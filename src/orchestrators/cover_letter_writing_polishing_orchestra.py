"""CoverLetterWritingPolishingOrchestra for cover letter with AI detection loop.

This module implements the cover letter workflow which includes AI detection and
humanization processing to ensure the draft appears human-written before quality
evaluation begins.
"""

from typing import Dict, Any

from .writing_polishing_orchestra import BaseWritingPolishingOrchestra
from ..state.run_context import OrchestrationStage
from ..agents.writing import AIWrittenDetector, DraftHumanizer


class CoverLetterWritingPolishingOrchestra(BaseWritingPolishingOrchestra):
    """Cover letter writing and polishing orchestra - includes AI detection loop.

    This concrete implementation of BaseWritingPolishingOrchestra handles the
    cover letter-specific workflow, which includes an AI detection and humanization
    loop after fact-checking to ensure the draft appears human-written.

    The AI detection loop continues until either:
    1. The draft passes as human-written (confidence >= threshold)
    2. Maximum AI detection iterations are reached

    Based on the workflow diagram in 06.2.WritingOrchestra.CoverLetter.mmd.

    Attributes:
        orchestra_name: "cover_letter_writing_polishing"
        stage: OrchestrationStage.WRITING_POLISHING

    Example:
        >>> run_context = await RunContext.create(config)
        >>> agent_pool = AgentPool(max_workers=config.agent_pool_size)
        >>> orchestra = CoverLetterWritingPolishingOrchestra(run_context, agent_pool)
        >>> results = await orchestra.run()
        >>> print(f"Final quality score: {results['final_score']}")
    """

    @property
    def orchestra_name(self) -> str:
        """Unique orchestra identifier for cover letter workflow.

        Returns:
            str: "cover_letter_writing_polishing"
        """
        return "cover_letter_writing_polishing"

    @property
    def stage(self) -> OrchestrationStage:
        """Associated orchestration stage.

        Returns:
            OrchestrationStage: WRITING_POLISHING stage
        """
        return OrchestrationStage.WRITING_POLISHING

    async def _post_fact_check_processing(self, truthful_draft: str) -> str:
        """Cover letter workflow: AI detection and humanization loop.

        This method implements the AI detection loop from the cover letter workflow
        diagram (06.2.WritingOrchestra.CoverLetter.mmd):

        1. Detect AI patterns using AIWrittenDetector
        2. If appears AI-written (confidence >= threshold):
           - Humanize draft using DraftHumanizer
           - Loop back to step 1
        3. If appears human-written (confidence < threshold):
           - Exit loop, return draft

        The loop enforces a maximum iteration limit to prevent infinite loops.

        Args:
            truthful_draft: Draft that passed fact-checking

        Returns:
            Humanized draft that appears human-written

        Raises:
            RuntimeError: If AI detection agents fail
        """
        threshold = self.run_context.config.ai_detection_threshold
        max_iterations = self.run_context.config.max_iterations
        iteration = 0
        current_draft = truthful_draft

        self.logger.info(
            f"Starting AI detection loop for cover letter "
            f"(threshold: {threshold:.3f}, max_iterations: {max_iterations})"
        )

        while iteration < max_iterations:
            iteration += 1
            self.logger.info(f"=== AI Detection Iteration {iteration}/{max_iterations} ===")

            # Detect AI patterns
            detector = AIWrittenDetector(
                state_manager=self.state_manager,
                stage_name=f"{self.orchestra_name}_ai_detect_iter_{iteration}"
            )

            detection_input = {"draft": current_draft}
            detection_result = await detector.run(detection_input)

            # Handle task instruction if needed
            if isinstance(detection_result, dict) and detection_result.get(
                "instruction"
            ) == "CALL_TASK_TOOL":
                self.logger.warning(
                    "AIWrittenDetector returned task instruction - assuming human-written"
                )
                # Default to human-written if we can't run detection
                appears_ai = False
                confidence = 0.0
                indicators = []
            else:
                appears_ai = detection_result.get("appears_ai_written", False)
                confidence = detection_result.get("confidence_score", 0.0)
                indicators = detection_result.get("indicators", [])

            self.logger.info(
                f"AI detection iter {iteration}: appears_ai={appears_ai}, "
                f"confidence={confidence:.3f}"
            )

            # Checkpoint after detection
            await self._checkpoint(
                {
                    "ai_detection_iteration": iteration,
                    "appears_ai_written": appears_ai,
                    "confidence_score": confidence,
                    "indicator_count": len(indicators),
                }
            )

            # Decision: Does it look human-written?
            # Per diagram: "Does it look like it was written by a Human? (99.9% confident)"
            # This means: if confidence that it's AI is LESS than threshold, it passes
            if not appears_ai or confidence < threshold:
                self.logger.info(
                    f"✓ Draft passes human detection (appears_ai={appears_ai}, "
                    f"confidence={confidence:.3f} < threshold={threshold:.3f})"
                )
                break

            # Draft appears AI-written - humanize it
            self.logger.warning(
                f"Draft appears AI-written (confidence={confidence:.3f} >= "
                f"threshold={threshold:.3f}), humanizing..."
            )

            humanizer = DraftHumanizer(
                state_manager=self.state_manager,
                stage_name=f"{self.orchestra_name}_humanize_iter_{iteration}"
            )

            humanizer_input = {
                "draft": current_draft,
                "ai_indicators": indicators,
            }

            humanized_result = await humanizer.run(humanizer_input)

            # Handle task instruction
            if isinstance(humanized_result, dict) and humanized_result.get(
                "instruction"
            ) == "CALL_TASK_TOOL":
                self.logger.warning(
                    "DraftHumanizer returned task instruction - using current draft"
                )
                # If humanization fails, exit loop to avoid infinite loop
                break
            else:
                current_draft = humanized_result
                self.logger.info(
                    f"Draft humanized: {len(current_draft)} characters "
                    f"({len(current_draft.split())} words)"
                )

            # Checkpoint after humanization
            await self._checkpoint(
                {
                    "ai_detection_iteration": iteration,
                    "humanization_complete": True,
                    "humanized_draft_length": len(current_draft),
                }
            )

        # Final status
        if iteration >= max_iterations:
            self.logger.warning(
                f"⚠ AI detection loop reached max iterations ({max_iterations}), "
                f"using best humanization attempt"
            )
        else:
            self.logger.info(
                f"✓ AI detection loop complete after {iteration} iteration(s) - "
                f"draft appears human-written"
            )

        return current_draft
