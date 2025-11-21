"""Best Practices Merger agent for synthesizing research into comprehensive guidelines.

This agent takes theoretical best practices and real-world examples (both successful
and failed) and merges them into comprehensive, actionable guidelines for either
resumes or cover letters.

This agent now integrates with the MergerEngine for iterative refinement with
quality validation.
"""

from typing import Dict, Any, List
import logging

from ..base_agent import BaseAgent
from ...merger.merger_engine import MergerEngine


class BestPracticesMerger(BaseAgent[Dict[str, Any], Dict[str, Any]]):
    """Agent that merges theoretical research with real-world examples.

    This agent (A1 in the diagrams) synthesizes:
    - Theoretical best practices from research (R1 output)
    - Real-world successful and failed examples (R2 output)

    Into a comprehensive best practices document.

    Input format:
        {
            "theoretical_practices": str,  # Output from R1 (Best Practices Researcher)
            "real_world_analysis": str,  # Output from R2 (Real World Examples Analysis)
            "document_type": str,  # "resume" or "cover_letter"
            "region": str,  # Geographic region
            "role": str,  # Job role
            "level": str  # Seniority level
        }

    Output format:
        {
            "merged_guidelines": str,  # Comprehensive markdown guidelines
            "key_takeaways": List[str],  # Top actionable insights
            "confidence_score": float,  # 0-1 confidence in guidelines
            "sources_count": int,  # Number of sources analyzed
            "patterns_identified": List[str]  # Key patterns found
        }
    """

    @property
    def agent_name(self) -> str:
        """Agent identifier."""
        return "best_practices_merger"

    def validate_input(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate input data has all required fields.

        Args:
            input_data: Input dictionary to validate

        Returns:
            Validated input data

        Raises:
            ValueError: If required fields are missing or invalid
        """
        required_fields = {
            "theoretical_practices",
            "real_world_analysis",
            "document_type",
            "region",
            "role",
            "level"
        }

        missing = required_fields - set(input_data.keys())
        if missing:
            raise ValueError(f"Missing required fields: {missing}")

        if input_data["document_type"] not in {"resume", "cover_letter"}:
            raise ValueError(
                f"Invalid document_type: {input_data['document_type']}"
            )

        return input_data

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute best practices merging using the MergerEngine.

        This agent now uses the MergerEngine for iterative merging with validation:
        1. Initial comprehensive merge
        2. Quality validation across 4 dimensions
        3. Iterative refinement until quality threshold met
        4. Final formatted output with metadata

        Args:
            input_data: Validated input data containing:
                - theoretical_practices: R1 content
                - real_world_analysis: R2 content
                - document_type: "resume" or "cover_letter"
                - region: Geographic region
                - role: Job role
                - level: Seniority level

        Returns:
            Dict with merged guidelines and metadata:
                - merged_guidelines: Final markdown with metadata header
                - key_takeaways: List of actionable insights
                - patterns_identified: Key patterns found
                - confidence_score: Overall quality score 0-1
                - validation_summary: Validation results summary
                - iterations_performed: Number of refinement iterations

        Raises:
            Exception: If merge execution fails
        """
        self.logger.info(
            f"Merging {input_data['document_type']} best practices for "
            f"{input_data['region']}/{input_data['role']}/{input_data['level']}"
        )

        # Create merger engine with quality settings
        engine = MergerEngine(
            max_iterations=3,
            quality_threshold=0.85
        )

        # Execute the merge
        result = await engine.merge(
            r1_content=input_data['theoretical_practices'],
            r2_content=input_data['real_world_analysis'],
            document_type=input_data['document_type'],
            region=input_data['region'],
            role=input_data['role'],
            level=input_data['level'],
            verbose=False
        )

        self.logger.info(
            f"Merge complete: confidence={result.confidence_score:.2f}, "
            f"iterations={result.iterations_performed}"
        )

        # Return in the format expected by orchestrators
        return {
            "merged_guidelines": result.merged_guidelines,
            "key_takeaways": result.key_takeaways,
            "patterns_identified": result.patterns_identified,
            "confidence_score": result.confidence_score,
            "validation_summary": {
                name: {
                    "score": vr.score,
                    "passed": vr.passed,
                    "coverage": vr.coverage
                }
                for name, vr in result.validation_results.items()
            },
            "iterations_performed": result.iterations_performed,
            "metadata": result.metadata
        }

    # Note: _build_task_prompt removed as we now use MergerEngine with its own prompts

    def format_output(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Format the output from MergerEngine execution.

        Args:
            result: Result from MergerEngine.merge()

        Returns:
            Formatted output matching the expected schema
        """
        return {
            "merged_guidelines": result.get("merged_guidelines", ""),
            "key_takeaways": result.get("key_takeaways", []),
            "confidence_score": result.get("confidence_score", 0.0),
            "patterns_identified": result.get("patterns_identified", []),
            "validation_summary": result.get("validation_summary", {}),
            "iterations_performed": result.get("iterations_performed", 0),
            "metadata": result.get("metadata", {})
        }
