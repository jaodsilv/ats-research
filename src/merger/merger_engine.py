"""Merger engine for iterative best practices merging with quality validation.

This module provides the MergerEngine class that orchestrates the multi-stage
merge process using the Anthropic API with validation and refinement cycles.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import logging
import json
import os
from pathlib import Path

import anthropic

from .validators import (
    validate_r1_principles,
    validate_r2_examples,
    validate_section_completeness,
    validate_actionability,
    calculate_confidence_score,
    ValidationResult,
)
from .prompts import (
    build_initial_merge_prompt,
    build_refinement_prompt,
    build_metadata_header,
)


logger = logging.getLogger(__name__)


@dataclass
class MergeResult:
    """Result of the merge operation.

    Attributes:
        merged_guidelines: Final merged guidelines markdown
        key_takeaways: List of key insights
        patterns_identified: List of key patterns found
        confidence_score: Overall confidence 0-1
        validation_results: Dict of ValidationResult by validator name
        iterations_performed: Number of refinement iterations
        metadata: Additional metadata about the merge
    """

    merged_guidelines: str
    key_takeaways: List[str]
    patterns_identified: List[str]
    confidence_score: float
    validation_results: Dict[str, ValidationResult]
    iterations_performed: int
    metadata: Dict[str, Any]


class MergerEngine:
    """Engine for iterative merging of R1 and R2 with quality validation.

    This engine implements a multi-stage process:
    1. Initial merge with comprehensive prompt
    2. Quality validation across 4 dimensions
    3. Iterative refinement until quality threshold met or max iterations
    4. Final formatting with metadata

    Example:
        ```python
        engine = MergerEngine(
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            max_iterations=3,
            quality_threshold=0.85
        )

        result = await engine.merge(
            r1_content=r1_text,
            r2_content=r2_text,
            document_type="resume",
            region="North America",
            role="Software Engineer",
            level="Senior"
        )

        print(f"Confidence: {result.confidence_score:.2f}")
        print(f"Iterations: {result.iterations_performed}")
        ```
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-5-20250929",
        max_iterations: int = 3,
        quality_threshold: float = 0.85,
        max_tokens: int = 16000,
    ):
        """Initialize the merger engine.

        Args:
            api_key: Anthropic API key (loads from ANTHROPIC_API_KEY env if None)
            model: Claude model to use
            max_iterations: Maximum refinement iterations
            quality_threshold: Minimum confidence score to accept (0-1)
            max_tokens: Maximum tokens per API call
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key required. Set ANTHROPIC_API_KEY environment variable "
                "or pass api_key parameter"
            )

        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = model
        self.max_iterations = max_iterations
        self.quality_threshold = quality_threshold
        self.max_tokens = max_tokens

        logger.info(f"MergerEngine initialized with model {model}")

    async def merge(
        self,
        r1_content: str,
        r2_content: str,
        document_type: str,
        region: str = "Global",
        role: str = "General",
        level: str = "All Levels",
        verbose: bool = False
    ) -> MergeResult:
        """Execute the complete iterative merge process.

        Args:
            r1_content: Theoretical best practices content
            r2_content: Real-world analysis content
            document_type: "resume" or "cover_letter"
            region: Geographic region
            role: Job role
            level: Seniority level
            verbose: Enable verbose logging

        Returns:
            MergeResult with final merged content and metadata

        Raises:
            ValueError: If inputs are invalid
            anthropic.APIError: If API calls fail
        """
        logger.info(f"Starting merge for {document_type} - {region}/{role}/{level}")

        # Validate inputs
        if not r1_content or not r2_content:
            raise ValueError("Both R1 and R2 content required")

        if document_type not in {"resume", "cover_letter"}:
            raise ValueError(f"Invalid document_type: {document_type}")

        # Stage 1: Initial merge
        logger.info("Stage 1: Initial comprehensive merge")
        merge_data = await self._execute_initial_merge(
            r1_content, r2_content, document_type, region, role, level, verbose
        )

        current_guidelines = merge_data["merged_guidelines"]
        current_metadata = {
            "key_takeaways": merge_data.get("key_takeaways", []),
            "patterns_identified": merge_data.get("patterns_identified", []),
            "sources_count": merge_data.get("sources_count", 0),
        }

        # Stage 2-4: Iterative validation and refinement
        iteration = 0
        validation_results = {}

        while iteration < self.max_iterations:
            iteration += 1
            logger.info(f"Stage {iteration + 1}: Validation (iteration {iteration})")

            # Run all validators
            validation_results = self._run_validators(
                r1_content, r2_content, current_guidelines
            )

            # Calculate confidence
            confidence = calculate_confidence_score(validation_results)
            logger.info(f"Confidence score: {confidence:.2f} (threshold: {self.quality_threshold})")

            if verbose:
                self._log_validation_details(validation_results)

            # Check if we meet quality threshold
            if confidence >= self.quality_threshold:
                logger.info(f"✓ Quality threshold met after {iteration} iteration(s)")
                break

            # Check if we've hit max iterations
            if iteration >= self.max_iterations:
                logger.warning(
                    f"⚠ Max iterations ({self.max_iterations}) reached. "
                    f"Final confidence: {confidence:.2f}"
                )
                break

            # Refinement needed
            logger.info(f"Refinement needed (confidence: {confidence:.2f}). Running refinement...")
            issues = self._extract_validation_issues(validation_results)

            refined_data = await self._execute_refinement(
                r1_content,
                r2_content,
                current_guidelines,
                issues,
                document_type,
                region,
                role,
                level,
                verbose
            )

            current_guidelines = refined_data["merged_guidelines"]
            current_metadata = {
                "key_takeaways": refined_data.get("key_takeaways", []),
                "patterns_identified": refined_data.get("patterns_identified", []),
                "sources_count": refined_data.get("sources_count", 0),
                "changes_made": refined_data.get("changes_made", []),
            }

        # Final validation
        final_validation = self._run_validators(r1_content, r2_content, current_guidelines)
        final_confidence = calculate_confidence_score(final_validation)

        logger.info(f"Merge complete: {iteration} iterations, confidence: {final_confidence:.2f}")

        # Add metadata header
        validation_summary = {
            name: {"score": result.score, "coverage": result.coverage}
            for name, result in final_validation.items()
        }

        metadata_header = build_metadata_header(
            document_type, region, role, level, final_confidence, final_validation
        )

        final_guidelines = metadata_header + current_guidelines

        return MergeResult(
            merged_guidelines=final_guidelines,
            key_takeaways=current_metadata.get("key_takeaways", []),
            patterns_identified=current_metadata.get("patterns_identified", []),
            confidence_score=final_confidence,
            validation_results=final_validation,
            iterations_performed=iteration,
            metadata={
                **current_metadata,
                "validation_summary": validation_summary,
                "quality_threshold": self.quality_threshold,
                "max_iterations": self.max_iterations,
            }
        )

    async def _execute_initial_merge(
        self,
        r1_content: str,
        r2_content: str,
        document_type: str,
        region: str,
        role: str,
        level: str,
        verbose: bool
    ) -> Dict[str, Any]:
        """Execute the initial merge API call.

        Args:
            r1_content: R1 theoretical content
            r2_content: R2 real-world content
            document_type: Document type
            region: Region
            role: Role
            level: Level
            verbose: Verbose logging

        Returns:
            Parsed JSON response from Claude
        """
        prompt = build_initial_merge_prompt(
            r1_content, r2_content, document_type, region, role, level
        )

        if verbose:
            logger.debug(f"Initial merge prompt length: {len(prompt)} chars")

        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = response.content[0].text

        # Parse JSON response
        try:
            # Extract JSON from markdown code blocks if present
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_str = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                json_str = response_text[json_start:json_end].strip()
            else:
                json_str = response_text.strip()

            merge_data = json.loads(json_str)
            return merge_data

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Response text: {response_text[:500]}...")
            # Fallback: treat entire response as markdown
            return {
                "merged_guidelines": response_text,
                "key_takeaways": [],
                "patterns_identified": [],
                "sources_count": 0,
            }

    async def _execute_refinement(
        self,
        r1_content: str,
        r2_content: str,
        previous_merge: str,
        issues: List[str],
        document_type: str,
        region: str,
        role: str,
        level: str,
        verbose: bool
    ) -> Dict[str, Any]:
        """Execute a refinement API call.

        Args:
            r1_content: R1 content
            r2_content: R2 content
            previous_merge: Previous merge attempt
            issues: Validation issues to address
            document_type: Document type
            region: Region
            role: Role
            level: Level
            verbose: Verbose logging

        Returns:
            Parsed JSON response from Claude
        """
        prompt = build_refinement_prompt(
            r1_content, r2_content, previous_merge, issues,
            document_type, region, role, level
        )

        if verbose:
            logger.debug(f"Refinement prompt length: {len(prompt)} chars")
            logger.debug(f"Addressing {len(issues)} issues")

        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = response.content[0].text

        # Parse JSON
        try:
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_str = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                json_str = response_text[json_start:json_end].strip()
            else:
                json_str = response_text.strip()

            refined_data = json.loads(json_str)
            return refined_data

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse refinement JSON: {e}")
            return {
                "merged_guidelines": response_text,
                "key_takeaways": [],
                "patterns_identified": [],
                "sources_count": 0,
                "changes_made": [],
            }

    def _run_validators(
        self,
        r1_content: str,
        r2_content: str,
        merged_guidelines: str
    ) -> Dict[str, ValidationResult]:
        """Run all validators on the merged guidelines.

        Args:
            r1_content: Original R1 content
            r2_content: Original R2 content
            merged_guidelines: Current merged guidelines

        Returns:
            Dict mapping validator names to ValidationResult
        """
        return {
            "r1_principles": validate_r1_principles(r1_content, merged_guidelines),
            "r2_examples": validate_r2_examples(r2_content, merged_guidelines),
            "section_completeness": validate_section_completeness(merged_guidelines),
            "actionability": validate_actionability(merged_guidelines),
        }

    def _extract_validation_issues(
        self,
        validation_results: Dict[str, ValidationResult]
    ) -> List[str]:
        """Extract specific issues from validation results.

        Args:
            validation_results: Dict of validation results

        Returns:
            List of issue descriptions
        """
        issues = []
        for name, result in validation_results.items():
            if not result.passed:
                issues.append(f"[{name.upper()}] {result.details}")
                issues.extend(f"  {issue}" for issue in result.issues)

        return issues

    def _log_validation_details(self, validation_results: Dict[str, ValidationResult]):
        """Log detailed validation results.

        Args:
            validation_results: Dict of validation results
        """
        logger.info("Validation Details:")
        for name, result in validation_results.items():
            status = "✓ PASS" if result.passed else "✗ FAIL"
            logger.info(f"  {name}: {status} (score: {result.score:.2f})")
            logger.info(f"    {result.details}")
            if result.issues:
                for issue in result.issues[:3]:  # Show first 3 issues
                    logger.info(f"    - {issue}")
                if len(result.issues) > 3:
                    logger.info(f"    ... and {len(result.issues) - 3} more issues")
