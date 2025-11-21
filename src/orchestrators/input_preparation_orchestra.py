"""InputPreparationOrchestra - Orchestrates input file reading, JD fetching, and parsing.

This module provides the InputPreparationOrchestra class that coordinates the complete
input preparation workflow for the resume/cover letter tailoring system:
1. Reading local input files (best practices, master resume, company culture)
2. Fetching raw job descriptions from URLs
3. Parsing job descriptions into structured format

The orchestra manages parallel execution of multiple DocumentFetcher and JDParser agents
for efficient processing of multiple job descriptions simultaneously.
"""

import logging
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
import hashlib

from .base_orchestra import BaseOrchestra
from ..state.run_context import RunContext, OrchestrationStage
from ..agents.agent_pool import AgentPool
from ..agents.input_prep import InputReader, DocumentFetcher, JDParser


class InputPreparationOrchestra(BaseOrchestra):
    """Orchestrates input preparation stage of the tailoring workflow.

    This orchestra coordinates three types of agents:
    1. InputReader (single agent) - Reads all local input files
    2. DocumentFetcher (multiple agents in parallel) - Fetches job descriptions from URLs
    3. JDParser (multiple agents in parallel) - Parses raw JDs into structured format

    The workflow follows this sequence:
    1. Read local files: best practices, master resume, company culture
    2. Fetch raw job descriptions from URLs (parallel execution)
    3. Parse each raw JD into structured format (parallel execution)
    4. Generate unique IDs for each parsed JD
    5. Store all results in run_context for downstream orchestras

    Input Requirements (from run_context.context_data):
        - job_urls: List[str] - URLs to fetch job descriptions from
        - input_file_paths: Dict[str, str] - Paths to local input files:
            - resume_best_practices: Path to resume BP file
            - cover_letter_best_practices: Path to cover letter BP file
            - master_resume: Path to master resume file
            - company_culture: Path to company culture report

    Output (stored in run_context.context_data):
        - input_files: Dict[str, str] - Contents of all input files
        - raw_job_descriptions: List[Dict[str, str]] - Raw JD content from URLs
        - parsed_job_descriptions: Dict[str, Dict[str, Any]] - Parsed JDs keyed by jd_id
        - run_context.job_description_ids: List[str] - List of all JD IDs

    Example:
        >>> run_context = await RunContext.create(config)
        >>> agent_pool = AgentPool(pool_size=5)
        >>> orchestra = InputPreparationOrchestra(run_context, agent_pool)
        >>> results = await orchestra.run()
        >>> print(results["jd_ids"])
        ['jd_abc123', 'jd_def456', 'jd_ghi789']
    """

    @property
    def orchestra_name(self) -> str:
        """Unique identifier for this orchestra.

        Returns:
            Orchestra name string
        """
        return "input_preparation"

    @property
    def stage(self) -> OrchestrationStage:
        """Associated orchestration stage.

        Returns:
            OrchestrationStage.INPUT_PREPARATION
        """
        return OrchestrationStage.INPUT_PREPARATION

    async def execute(self) -> Dict[str, Any]:
        """Execute the input preparation workflow.

        This method orchestrates the complete input preparation process:
        1. Validates required inputs from run_context
        2. Reads local input files via InputReader
        3. Fetches raw JDs from URLs via DocumentFetcher agents (parallel)
        4. Parses raw JDs via JDParser agents (parallel)
        5. Generates unique IDs for each parsed JD
        6. Stores all results in run_context

        Returns:
            Dict containing execution summary:
                - status: "success" or "partial_success"
                - files_loaded: List[str] - Types of files loaded
                - jds_fetched: int - Count of successfully fetched JDs
                - jds_parsed: int - Count of successfully parsed JDs
                - jd_ids: List[str] - Generated JD IDs
                - artifacts: Dict[str, Path] - Paths to saved artifacts
                - errors: List[str] - Any non-fatal errors encountered

        Raises:
            ValueError: If required inputs are missing or invalid
            RuntimeError: If critical operations fail
        """
        self.logger.info("Starting input preparation execution")

        errors: List[str] = []
        artifacts: Dict[str, Path] = {}

        # Step 1: Validate required inputs
        self.logger.info("Step 1: Validating required inputs from run_context")
        job_urls = await self._get_context_data("job_urls", default=[])
        input_file_paths = await self._get_context_data("input_file_paths", default=None)

        if not job_urls:
            raise ValueError(
                "No job URLs found in run_context. "
                "Expected 'job_urls' list in context_data."
            )

        if not input_file_paths:
            raise ValueError(
                "No input file paths found in run_context. "
                "Expected 'input_file_paths' dict in context_data."
            )

        self.logger.info(
            f"Found {len(job_urls)} job URLs and input_file_paths with "
            f"{len(input_file_paths)} entries"
        )

        # Step 2: Read local input files
        self.logger.info("Step 2: Reading local input files")
        input_reader = InputReader(
            state_manager=self.state_manager,
            stage_name=self.stage.value
        )

        try:
            input_files = await input_reader.run(input_file_paths)
            await self._set_context_data("input_files", input_files)

            self.logger.info(
                f"Successfully read {len(input_files)} input files"
            )

            # Save checkpoint after reading files
            await self._checkpoint({
                "step": "input_files_read",
                "files_loaded": list(input_files.keys()),
                "total_chars": sum(len(content) for content in input_files.values())
            })

        except Exception as e:
            self.logger.error(f"Failed to read input files: {e}", exc_info=True)
            raise RuntimeError(f"Input file reading failed: {e}") from e

        # Step 3: Fetch raw job descriptions from URLs (parallel)
        self.logger.info(f"Step 3: Fetching {len(job_urls)} job descriptions in parallel")

        def create_document_fetcher(url: str) -> DocumentFetcher:
            """Factory function to create DocumentFetcher agents."""
            return DocumentFetcher(
                state_manager=self.state_manager,
                stage_name=self.stage.value
            )

        try:
            fetch_results = await self.agent_pool.execute_batches(
                agent_factory=create_document_fetcher,
                inputs=job_urls
            )

            # Separate successful fetches from failures
            raw_jds: List[Dict[str, Any]] = []
            for i, result in enumerate(fetch_results):
                if isinstance(result, Exception):
                    error_msg = f"Failed to fetch URL {job_urls[i]}: {result}"
                    self.logger.error(error_msg)
                    errors.append(error_msg)
                else:
                    raw_jds.append(result)

            if not raw_jds:
                raise RuntimeError(
                    f"Failed to fetch any job descriptions. "
                    f"All {len(job_urls)} fetch attempts failed."
                )

            await self._set_context_data("raw_job_descriptions", raw_jds)

            self.logger.info(
                f"Successfully fetched {len(raw_jds)}/{len(job_urls)} job descriptions"
            )

            # Save checkpoint after fetching
            await self._checkpoint({
                "step": "jds_fetched",
                "total_urls": len(job_urls),
                "successful_fetches": len(raw_jds),
                "failed_fetches": len(job_urls) - len(raw_jds)
            })

        except Exception as e:
            self.logger.error(f"Failed to fetch job descriptions: {e}", exc_info=True)
            raise RuntimeError(f"Job description fetching failed: {e}") from e

        # Step 4: Parse raw job descriptions (parallel)
        self.logger.info(f"Step 4: Parsing {len(raw_jds)} job descriptions in parallel")

        # Extract raw content from fetch results for parsing
        raw_contents: List[str] = []
        for raw_jd in raw_jds:
            # Handle both task instruction format and actual fetch result format
            if raw_jd.get("instruction") == "CALL_TASK_TOOL":
                # This is a task instruction - would need Task tool execution
                # For now, we'll use a placeholder
                self.logger.warning(
                    "DocumentFetcher returned task instruction - "
                    "actual execution not implemented yet"
                )
                raw_contents.append("")
            else:
                raw_contents.append(raw_jd.get("raw_content", ""))

        def create_jd_parser(raw_content: str) -> JDParser:
            """Factory function to create JDParser agents."""
            return JDParser(
                state_manager=self.state_manager,
                stage_name=self.stage.value
            )

        try:
            parse_results = await self.agent_pool.execute_batches(
                agent_factory=create_jd_parser,
                inputs=raw_contents
            )

            # Separate successful parses from failures
            parsed_jds: List[Dict[str, Any]] = []
            for i, result in enumerate(parse_results):
                if isinstance(result, Exception):
                    error_msg = f"Failed to parse JD {i}: {result}"
                    self.logger.error(error_msg)
                    errors.append(error_msg)
                else:
                    parsed_jds.append(result)

            if not parsed_jds:
                raise RuntimeError(
                    f"Failed to parse any job descriptions. "
                    f"All {len(raw_contents)} parse attempts failed."
                )

            self.logger.info(
                f"Successfully parsed {len(parsed_jds)}/{len(raw_contents)} job descriptions"
            )

        except Exception as e:
            self.logger.error(f"Failed to parse job descriptions: {e}", exc_info=True)
            raise RuntimeError(f"Job description parsing failed: {e}") from e

        # Step 5: Generate unique IDs for each parsed JD
        self.logger.info("Step 5: Generating unique IDs for parsed job descriptions")

        jd_ids: List[str] = []
        parsed_jds_dict: Dict[str, Dict[str, Any]] = {}

        for i, parsed_jd in enumerate(parsed_jds):
            # Generate ID based on job title and company
            jd_id = self._generate_jd_id(
                job_title=parsed_jd.get("job_title", f"unknown_{i}"),
                company=parsed_jd.get("company", "unknown"),
                index=i
            )

            jd_ids.append(jd_id)
            parsed_jds_dict[jd_id] = parsed_jd

            self.logger.debug(
                f"Generated ID '{jd_id}' for {parsed_jd.get('job_title')} "
                f"at {parsed_jd.get('company')}"
            )

        # Step 6: Store all results in run_context
        self.logger.info("Step 6: Storing results in run_context")

        await self._set_context_data("parsed_job_descriptions", parsed_jds_dict)

        # Update run_context.job_description_ids
        self.run_context.job_description_ids = jd_ids

        self.logger.info(
            f"Stored {len(parsed_jds_dict)} parsed JDs with IDs: {jd_ids}"
        )

        # Save final checkpoint
        await self._checkpoint({
            "step": "input_preparation_complete",
            "jd_ids": jd_ids,
            "total_jds": len(jd_ids),
            "files_loaded": list(input_files.keys())
        })

        # Step 7: Save artifacts to disk
        self.logger.info("Step 7: Saving artifacts to disk")

        # Save parsed JDs as JSON files
        artifacts_dir = self.run_context.config.runs_dir / "artifacts" / "parsed_jds"
        artifacts_dir.mkdir(parents=True, exist_ok=True)

        for jd_id, parsed_jd in parsed_jds_dict.items():
            artifact_path = artifacts_dir / f"{jd_id}.json"

            try:
                import json
                import aiofiles

                async with aiofiles.open(artifact_path, 'w', encoding='utf-8') as f:
                    await f.write(json.dumps(parsed_jd, indent=2))

                artifacts[jd_id] = artifact_path

                self.logger.debug(f"Saved artifact for {jd_id} to {artifact_path}")

            except Exception as e:
                error_msg = f"Failed to save artifact for {jd_id}: {e}"
                self.logger.error(error_msg)
                errors.append(error_msg)

        # Determine overall status
        status = "success"
        if errors:
            status = "partial_success"
            self.logger.warning(
                f"Input preparation completed with {len(errors)} errors"
            )

        # Build return summary
        summary = {
            "status": status,
            "files_loaded": list(input_files.keys()),
            "jds_fetched": len(raw_jds),
            "jds_parsed": len(parsed_jds),
            "jd_ids": jd_ids,
            "artifacts": {jd_id: str(path) for jd_id, path in artifacts.items()},
            "errors": errors if errors else []
        }

        self.logger.info(
            f"Input preparation complete: {len(jd_ids)} JDs ready for matching"
        )

        return summary

    def _generate_jd_id(
        self,
        job_title: str,
        company: str,
        index: int
    ) -> str:
        """Generate a unique ID for a job description.

        Creates a short, human-readable ID based on job title and company,
        with a hash suffix to ensure uniqueness.

        Args:
            job_title: Job title from parsed JD
            company: Company name from parsed JD
            index: Index of this JD in the batch (for ordering)

        Returns:
            Unique JD ID string (e.g., 'jd_senior_engineer_techcorp_a3f')

        Example:
            >>> orchestra._generate_jd_id("Senior Engineer", "TechCorp", 0)
            'jd_senior_engineer_techcorp_a3f'
        """
        # Normalize title and company for ID
        title_slug = self._slugify(job_title)[:30]  # Max 30 chars
        company_slug = self._slugify(company)[:20]  # Max 20 chars

        # Create hash from full title + company + index for uniqueness
        hash_input = f"{job_title}_{company}_{index}_{datetime.now().isoformat()}"
        hash_suffix = hashlib.md5(hash_input.encode()).hexdigest()[:3]

        # Build ID: jd_<title>_<company>_<hash>
        jd_id = f"jd_{title_slug}_{company_slug}_{hash_suffix}"

        return jd_id

    def _slugify(self, text: str) -> str:
        """Convert text to a URL-safe slug.

        Args:
            text: Text to slugify

        Returns:
            Slugified text (lowercase, alphanumeric + underscores)

        Example:
            >>> orchestra._slugify("Senior Software Engineer")
            'senior_software_engineer'
        """
        import re

        # Convert to lowercase
        slug = text.lower()

        # Replace non-alphanumeric chars with underscores
        slug = re.sub(r'[^a-z0-9]+', '_', slug)

        # Remove leading/trailing underscores
        slug = slug.strip('_')

        # Collapse multiple underscores
        slug = re.sub(r'_+', '_', slug)

        return slug
