"""
TailoringOrchestra - Master coordinator for the complete tailoring workflow.

This module provides the top-level orchestrator that coordinates all sub-orchestras
to complete the end-to-end resume and cover letter tailoring process. It manages:
- Input preparation and validation
- Job description matching and selection
- Parallel resume and cover letter generation
- Document length optimization
- Release artifact collection

The TailoringOrchestra follows the workflow defined in 03.TailoringOrchestra.mmd.
"""

from pathlib import Path
from typing import Dict, Any, List
import logging
import asyncio

from .base_orchestra import BaseOrchestra
from ..state.run_context import RunContext, OrchestrationStage
from ..agents.agent_pool import AgentPool
from .input_preparation_orchestra import InputPreparationOrchestra
from .jd_matching_orchestra import JDMatchingOrchestra
from .resume_writing_polishing_orchestra import ResumeWritingPolishingOrchestra
from .cover_letter_writing_polishing_orchestra import CoverLetterWritingPolishingOrchestra
from .pruning_orchestra import PruningOrchestra


class TailoringOrchestra(BaseOrchestra):
    """
    Master orchestrator coordinating the entire tailoring workflow.

    This orchestra coordinates five sub-orchestras:
    1. InputPreparationOrchestra - Load and validate all input files
    2. JDMatchingOrchestra - Match JDs to resume and select best candidates
    3. ResumeWritingPolishingOrchestra - Generate resume drafts (parallel per JD)
    4. CoverLetterWritingPolishingOrchestra - Generate cover letter drafts (parallel per JD)
    5. PruningOrchestra - Optimize document length and produce release versions

    The workflow executes sequentially at the top level, with parallelization
    for document generation (one resume + cover letter per selected JD).

    Example:
        ```python
        # Create run context
        config = Config()
        run_context = await RunContext.create(config)

        # Populate with wizard inputs
        await run_context.add_context_data("job_urls", job_urls)
        await run_context.add_context_data("input_file_paths", file_paths)

        # Create agent pool
        agent_pool = AgentPool(pool_size=5)

        # Run tailoring
        orchestra = TailoringOrchestra(run_context, agent_pool)
        results = await orchestra.run()

        print(f"Generated {results['jds_processed']} complete applications")
        print(f"Release artifacts: {results['release_artifacts']}")
        ```
    """

    @property
    def orchestra_name(self) -> str:
        """Unique orchestra identifier.

        Returns:
            str: "tailoring"
        """
        return "tailoring"

    @property
    def stage(self) -> OrchestrationStage:
        """Associated orchestration stage.

        Returns:
            OrchestrationStage.INITIALIZATION: Master coordinator stage
        """
        return OrchestrationStage.INITIALIZATION

    async def execute(self) -> Dict[str, Any]:
        """
        Execute the complete end-to-end tailoring workflow.

        Workflow stages:
        1. InputPreparationOrchestra → Prepare and validate inputs
        2. JDMatchingOrchestra → Match and select JDs
        3. For each selected JD (parallel with agent_pool):
           a. ResumeWritingPolishingOrchestra
           b. CoverLetterWritingPolishingOrchestra
        4. For each document (resume + cover letter per JD):
           a. PruningOrchestra → Release version
        5. Collect all artifacts and return summary

        Returns:
            Dict[str, Any]: Complete workflow summary containing:
                - status: "success" or "partial" (if any JD failed)
                - jds_processed: Number of JDs successfully processed
                - jds_failed: Number of JDs that failed
                - release_artifacts: Dict mapping jd_id to artifact paths
                    - resume: Path to final resume PDF
                    - cover_letter: Path to final cover letter PDF
                - failed_jds: List of JD IDs that failed (if any)

        Raises:
            Exception: If any critical orchestration step fails
        """
        self.logger.info("Starting master tailoring orchestration workflow")

        # Track results
        jds_processed = 0
        jds_failed = 0
        release_artifacts: Dict[str, Dict[str, Path]] = {}
        failed_jds: List[str] = []

        try:
            # ===================================================================
            # STAGE 1: Input Preparation
            # ===================================================================
            self.logger.info("STAGE 1/4: Input Preparation")
            input_prep = InputPreparationOrchestra(self.run_context, self.agent_pool)
            input_results = await input_prep.run()

            if input_results.get("status") != "success":
                raise RuntimeError(
                    f"Input preparation failed: {input_results.get('error', 'Unknown error')}"
                )

            self.logger.info(
                f"Input preparation complete: {len(input_results.get('job_descriptions', []))} JDs loaded"
            )

            # ===================================================================
            # STAGE 2: JD Matching
            # ===================================================================
            self.logger.info("STAGE 2/4: Job Description Matching")
            jd_matching = JDMatchingOrchestra(self.run_context, self.agent_pool)
            matching_results = await jd_matching.run()

            if matching_results.get("status") != "success":
                raise RuntimeError(
                    f"JD matching failed: {matching_results.get('error', 'Unknown error')}"
                )

            selected_jds = matching_results.get("selected_jds", [])
            if not selected_jds:
                self.logger.warning("No JDs selected after matching")
                return {
                    "status": "success",
                    "jds_processed": 0,
                    "jds_failed": 0,
                    "release_artifacts": {},
                    "message": "No job descriptions met the matching criteria"
                }

            self.logger.info(f"JD matching complete: {len(selected_jds)} JDs selected")

            # ===================================================================
            # STAGE 3 & 4: Parallel Resume and Cover Letter Generation
            # ===================================================================
            self.logger.info(
                f"STAGE 3/4: Generating resumes and cover letters for {len(selected_jds)} JDs"
            )

            # Create writing tasks for each JD
            async def generate_documents_for_jd(jd_id: str) -> Dict[str, Any]:
                """Generate both resume and cover letter for a single JD."""
                try:
                    self.logger.info(f"Starting document generation for JD: {jd_id}")

                    # Generate resume
                    resume_orchestra = ResumeWritingPolishingOrchestra(
                        self.run_context,
                        self.agent_pool
                    )
                    resume_results = await resume_orchestra.run()

                    # Generate cover letter
                    cover_letter_orchestra = CoverLetterWritingPolishingOrchestra(
                        self.run_context,
                        self.agent_pool
                    )
                    cover_letter_results = await cover_letter_orchestra.run()

                    return {
                        "jd_id": jd_id,
                        "status": "success",
                        "resume": resume_results,
                        "cover_letter": cover_letter_results
                    }

                except Exception as e:
                    self.logger.error(f"Document generation failed for JD {jd_id}: {e}")
                    return {
                        "jd_id": jd_id,
                        "status": "failed",
                        "error": str(e)
                    }

            # Execute document generation in parallel (controlled by agent pool)
            writing_tasks = [generate_documents_for_jd(jd["id"]) for jd in selected_jds]
            writing_results = await asyncio.gather(*writing_tasks, return_exceptions=True)

            # Process writing results
            for result in writing_results:
                if isinstance(result, Exception):
                    self.logger.error(f"Document generation exception: {result}")
                    jds_failed += 1
                    continue

                jd_id = result["jd_id"]

                if result["status"] != "success":
                    self.logger.warning(f"Document generation failed for JD {jd_id}")
                    failed_jds.append(jd_id)
                    jds_failed += 1
                    continue

                # Store intermediate results for pruning stage
                await self.run_context.add_context_data(
                    f"resume_candidate_{jd_id}",
                    result["resume"]
                )
                await self.run_context.add_context_data(
                    f"cover_letter_candidate_{jd_id}",
                    result["cover_letter"]
                )

            self.logger.info(
                f"Document generation complete: "
                f"{len(selected_jds) - jds_failed} succeeded, {jds_failed} failed"
            )

            # ===================================================================
            # STAGE 5: Pruning and Final Release
            # ===================================================================
            self.logger.info("STAGE 5/5: Document length optimization (pruning)")

            for jd in selected_jds:
                jd_id = jd["id"]

                # Skip failed JDs
                if jd_id in failed_jds:
                    continue

                try:
                    self.logger.info(f"Pruning documents for JD: {jd_id}")

                    # Prune resume
                    resume_pruning = PruningOrchestra(
                        self.run_context,
                        self.agent_pool,
                        document_type="resume",
                        jd_id=jd_id
                    )
                    resume_release = await resume_pruning.run()

                    # Prune cover letter
                    cover_letter_pruning = PruningOrchestra(
                        self.run_context,
                        self.agent_pool,
                        document_type="cover_letter",
                        jd_id=jd_id
                    )
                    cover_letter_release = await cover_letter_pruning.run()

                    # Store release artifacts
                    release_artifacts[jd_id] = {
                        "resume": resume_release.get("release_pdf_path"),
                        "cover_letter": cover_letter_release.get("release_pdf_path")
                    }

                    jds_processed += 1
                    self.logger.info(f"JD {jd_id} complete: all artifacts generated")

                except Exception as e:
                    self.logger.error(f"Pruning failed for JD {jd_id}: {e}", exc_info=True)
                    failed_jds.append(jd_id)
                    jds_failed += 1

            # ===================================================================
            # Final Summary
            # ===================================================================
            self.logger.info(
                f"Tailoring workflow complete: {jds_processed} JDs succeeded, {jds_failed} failed"
            )

            status = "success" if jds_failed == 0 else "partial"

            results = {
                "status": status,
                "jds_processed": jds_processed,
                "jds_failed": jds_failed,
                "release_artifacts": release_artifacts,
            }

            if failed_jds:
                results["failed_jds"] = failed_jds

            return results

        except Exception as e:
            self.logger.error(f"Fatal error in tailoring orchestration: {e}", exc_info=True)
            raise
