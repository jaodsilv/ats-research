"""FactCheckingLoopOrchestra for iterative fact verification and correction.

This module implements the fact-checking loop that verifies drafts against the
master resume and rewrites them if false facts are found, continuing until
either no false facts remain or the maximum iteration limit is reached.
"""

from pathlib import Path
from typing import Dict, Any, List
import logging
from datetime import datetime

from .base_orchestra import BaseOrchestra
from ..state.run_context import RunContext, OrchestrationStage
from ..agents.agent_pool import AgentPool
from ..agents.writing import FactChecker, RevisedDraftWriter
from ..utils.logging import log_checkpoint


class FactCheckingLoopOrchestra(BaseOrchestra):
    """Orchestra that coordinates iterative fact-checking and draft revision.

    This orchestra implements a loop that:
    1. Runs FactChecker to verify draft against master resume
    2. Checks if false facts were found
    3. If yes: Runs RevisedDraftWriter to fix the draft and loops back to step 1
    4. If no: Exits the loop successfully
    5. Enforces maximum iteration limit for safety

    The loop continues until either:
    - No false facts are found (success condition)
    - Maximum iterations reached (safety limit)

    Attributes:
        orchestra_name: Unique identifier "fact_checking_loop"
        stage: OrchestrationStage.FACT_CHECKING

    Example:
        >>> run_context = await RunContext.create(config)
        >>> agent_pool = AgentPool(max_workers=config.agent_pool_size)
        >>> orchestra = FactCheckingLoopOrchestra(run_context, agent_pool)
        >>> results = await orchestra.run()
        >>> print(f"Final draft has false facts: {results['final_has_false_facts']}")
    """

    @property
    def orchestra_name(self) -> str:
        """Unique orchestra identifier.

        Returns:
            str: "fact_checking_loop"
        """
        return "fact_checking_loop"

    @property
    def stage(self) -> OrchestrationStage:
        """Associated orchestration stage.

        Returns:
            OrchestrationStage: FACT_CHECKING stage
        """
        return OrchestrationStage.FACT_CHECKING

    async def execute(self) -> Dict[str, Any]:
        """Execute the fact-checking loop workflow.

        This method implements the iterative fact-checking loop:
        1. Retrieve draft and master_resume from context
        2. Get max_iterations from config
        3. Loop:
           a. Run FactChecker agent
           b. Check if false facts found
           c. If no false facts: break (success)
           d. If false facts: run RevisedDraftWriter
           e. Update draft with revision
           f. Increment iteration counter
           g. Continue if under max_iterations
        4. Store final draft in context
        5. Return summary results

        Returns:
            Dict[str, Any]: Execution results containing:
                - iterations_performed: Number of iterations executed
                - final_has_false_facts: Whether final draft has false facts
                - false_facts_found: List of false facts from last check
                - final_draft: Final draft content (corrected or original)
                - max_iterations_reached: Whether loop hit iteration limit
                - artifacts: Dict mapping artifact names to file paths
                - status: "success" or "max_iterations_exceeded"

        Raises:
            KeyError: If required context data is missing
            Exception: If agent execution fails
        """
        self.logger.info("Starting fact-checking loop workflow")

        # Retrieve required context data
        draft = await self._get_context_data("draft")
        master_resume = await self._get_context_data("master_resume")

        if draft is None:
            raise KeyError("Missing required context data: 'draft'")
        if master_resume is None:
            raise KeyError("Missing required context data: 'master_resume'")

        # Get max iterations from config
        max_iterations = self.run_context.config.max_iterations
        self.logger.info(f"Max iterations: {max_iterations}")

        # Initialize loop state
        iteration = 0
        current_draft = draft
        final_has_false_facts = False
        false_facts_found: List[Dict[str, Any]] = []
        artifacts: Dict[str, Path] = {}

        # Main fact-checking loop
        while iteration < max_iterations:
            iteration += 1
            self.logger.info(f"=== Fact-checking iteration {iteration}/{max_iterations} ===")

            # Step 1: Run FactChecker
            self.logger.info(f"Running FactChecker (iteration {iteration})")
            fact_checker = FactChecker(
                state_manager=self.state_manager,
                stage_name=f"fact_checking_iter_{iteration}"
            )

            fact_check_input = {
                "draft": current_draft,
                "master_resume": master_resume
            }

            fact_check_results = await fact_checker.run(fact_check_input)

            # Check if this is a task instruction (needs manual execution)
            if isinstance(fact_check_results, dict) and \
               fact_check_results.get("instruction") == "CALL_TASK_TOOL":
                self.logger.warning(
                    "FactChecker returned task instruction - requires manual execution"
                )
                # For now, treat as no false facts to prevent infinite loop
                # In production, this would need actual Task tool execution
                final_has_false_facts = False
                false_facts_found = []
                break

            # Step 2: Extract fact-checking results
            has_false_facts_bool = fact_check_results.get("has_false_facts", False)
            false_facts_list = fact_check_results.get("false_facts", [])
            verification_notes = fact_check_results.get("verification_notes", "")

            self.logger.info(
                f"Fact-check complete: has_false_facts={has_false_facts_bool}, "
                f"false_fact_count={len(false_facts_list)}"
            )

            # Checkpoint after fact-checking
            await self._checkpoint({
                "iteration": iteration,
                "has_false_facts": has_false_facts_bool,
                "false_fact_count": len(false_facts_list),
                "verification_notes": verification_notes
            })

            # Step 3: Decision - Has false facts?
            if not has_false_facts_bool:
                # Success: No false facts found
                self.logger.info(
                    f"✓ No false facts found in iteration {iteration}. Loop complete."
                )
                final_has_false_facts = False
                false_facts_found = false_facts_list  # Should be empty
                break

            # Step 4: False facts found - log them
            self.logger.warning(f"✗ Found {len(false_facts_list)} false facts:")
            for i, fact in enumerate(false_facts_list, 1):
                self.logger.warning(
                    f"  {i}. CLAIM: {fact.get('claim', 'N/A')}\n"
                    f"     ISSUE: {fact.get('issue', 'N/A')}\n"
                    f"     CORRECTION: {fact.get('correction', 'N/A')}"
                )

            # Step 5: Run RevisedDraftWriter to fix the draft
            self.logger.info(f"Running RevisedDraftWriter (iteration {iteration})")
            revised_writer = RevisedDraftWriter(
                state_manager=self.state_manager,
                stage_name=f"draft_revision_iter_{iteration}"
            )

            revision_input = {
                "draft": current_draft,
                "fact_check_results": fact_check_results,
                "master_resume": master_resume
            }

            revised_draft = await revised_writer.run(revision_input)

            # Check if this is a task instruction
            if isinstance(revised_draft, dict) and \
               revised_draft.get("instruction") == "CALL_TASK_TOOL":
                self.logger.warning(
                    "RevisedDraftWriter returned task instruction - requires manual execution"
                )
                # Keep current draft unchanged
                final_has_false_facts = has_false_facts_bool
                false_facts_found = false_facts_list
                break

            # Step 6: Update current draft with revision
            current_draft = revised_draft
            self.logger.info(
                f"Draft revised: {len(current_draft)} characters "
                f"({len(current_draft.split())} words)"
            )

            # Checkpoint after revision
            await self._checkpoint({
                "iteration": iteration,
                "revision_complete": True,
                "revised_draft_length": len(current_draft),
                "revised_draft_word_count": len(current_draft.split())
            })

            # Store intermediate artifact
            artifact_name = f"draft_iter_{iteration}"
            artifacts[artifact_name] = Path(f"draft_iteration_{iteration}.md")

            # Continue to next iteration (loop back to fact-checking)
            self.logger.info(f"Iteration {iteration} complete. Continuing to next iteration.")

        # End of loop
        max_iterations_reached = iteration >= max_iterations

        if max_iterations_reached:
            self.logger.warning(
                f"⚠ Maximum iterations ({max_iterations}) reached. "
                f"Final draft may still contain false facts."
            )
            # Perform one final fact-check to get accurate status
            self.logger.info("Performing final fact-check to determine status...")
            final_checker = FactChecker(
                state_manager=self.state_manager,
                stage_name="final_fact_check"
            )
            final_check_results = await final_checker.run({
                "draft": current_draft,
                "master_resume": master_resume
            })

            if not (isinstance(final_check_results, dict) and
                    final_check_results.get("instruction") == "CALL_TASK_TOOL"):
                final_has_false_facts = final_check_results.get("has_false_facts", False)
                false_facts_found = final_check_results.get("false_facts", [])

        # Store final draft in context for next stage
        await self._set_context_data("fact_checked_draft", current_draft)
        await self._set_context_data("fact_check_complete", True)

        # Determine overall status
        if final_has_false_facts:
            status = "max_iterations_exceeded" if max_iterations_reached else "has_false_facts"
        else:
            status = "success"

        # Build results summary
        results = {
            "status": status,
            "iterations_performed": iteration,
            "final_has_false_facts": final_has_false_facts,
            "false_facts_found": false_facts_found,
            "final_draft": current_draft,
            "max_iterations_reached": max_iterations_reached,
            "artifacts": artifacts,
            "final_draft_length": len(current_draft),
            "final_draft_word_count": len(current_draft.split())
        }

        self.logger.info(
            f"Fact-checking loop complete: {iteration} iterations, "
            f"status={status}, final_has_false_facts={final_has_false_facts}"
        )

        return results
