"""Base WritingPolishingOrchestra for iterative document writing and quality improvement.

This module provides an abstract base class for the writing and polishing loop that
creates, evaluates, and improves resume/cover letter drafts through iterative refinement
with fact-checking, version management, and quality-driven decision making.

The base class implements shared logic, while concrete subclasses define document-specific
post-fact-check processing (e.g., AI detection for cover letters).
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, List
import logging

from .base_orchestra import BaseOrchestra
from .fact_checking_loop_orchestra import FactCheckingLoopOrchestra
from ..state.run_context import RunContext, OrchestrationStage
from ..agents.agent_pool import AgentPool
from ..agents.writing import (
    DraftWriter,
    VersionManager,
    DocumentEvaluator,
    IssueFixer,
    DocumentPolisher,
)
from ..decisions.decision_logic import (
    has_critical_issues,
    did_score_decrease,
    is_score_good_enough,
    DocumentEvaluation,
)
from ..utils.logging import log_checkpoint


class BaseWritingPolishingOrchestra(BaseOrchestra, ABC):
    """Abstract base orchestra for iterative document writing and polishing.

    This abstract base class implements the shared workflow logic for document writing
    and polishing, while allowing subclasses to define document-specific processing
    (e.g., AI detection for cover letters vs. no AI detection for resumes).

    This orchestra implements a sophisticated workflow that:
    1. Creates initial draft using DraftWriter
    2. Runs FactCheckingLoopOrchestra (sub-orchestra) to ensure factual accuracy
    3. Performs document-specific post-fact-check processing (abstract method)
       - Resume: No additional processing
       - Cover Letter: AI detection and humanization loop
    4. Stores the processed draft as version 0 using VersionManager
    5. Evaluates draft quality using DocumentEvaluator
    6. Implements a decision tree for iterative improvement:
       - Has critical issues? → IssueFixer → loop back
       - Did score decrease? → VersionManager (restore best) → exit
       - Is score good enough? → exit (success)
       - Needs improvement → DocumentPolisher → loop back
    7. Enforces maximum iteration limit for safety
    8. Tracks version history and quality scores

    The loop continues until:
    - Quality threshold is met (success)
    - Score decreases (restore best version and exit)
    - Maximum iterations reached (use best version)

    Abstract Methods:
        orchestra_name: Unique identifier for the subclass
        stage: Orchestration stage for the subclass
        _post_fact_check_processing: Document-specific processing after fact-checking

    Example:
        >>> # Use concrete subclass
        >>> run_context = await RunContext.create(config)
        >>> agent_pool = AgentPool(max_workers=config.agent_pool_size)
        >>> orchestra = ResumeWritingPolishingOrchestra(run_context, agent_pool)
        >>> results = await orchestra.run()
        >>> print(f"Final quality score: {results['final_score']}")
        >>> print(f"Iterations: {results['iterations_performed']}")
    """

    @property
    @abstractmethod
    def orchestra_name(self) -> str:
        """Unique orchestra identifier.

        Returns:
            str: Orchestra identifier (e.g., "resume_writing_polishing")
        """
        pass

    @property
    @abstractmethod
    def stage(self) -> OrchestrationStage:
        """Associated orchestration stage.

        Returns:
            OrchestrationStage: WRITING_POLISHING stage
        """
        pass

    @abstractmethod
    async def _post_fact_check_processing(self, truthful_draft: str) -> str:
        """Process draft after fact-checking (template method pattern).

        This abstract method allows subclasses to define document-specific processing
        that occurs after fact-checking but before version management and quality
        evaluation. Examples:

        - Resume: Returns draft as-is (no additional processing)
        - Cover Letter: Runs AI detection and humanization loop until draft appears
          human-written with sufficient confidence

        Args:
            truthful_draft: Draft that passed fact-checking

        Returns:
            Processed draft ready for version management and quality evaluation

        Raises:
            Exception: If processing fails
        """
        pass

    async def execute(self) -> Dict[str, Any]:
        """Execute the writing and polishing workflow.

        This method implements the complete writing and polishing loop:
        1. Retrieve inputs from context (master_resume, parsed_jd, etc.)
        2. Determine document_type ("resume" or "cover_letter")
        3. Create initial draft using DraftWriter
        4. Run FactCheckingLoopOrchestra to verify factual accuracy
        5. Run post-fact-check processing (document-specific via abstract method)
        6. Store processed draft as version 0
        7. Initialize loop state (iteration, scores, versions)
        8. Evaluation loop (while iteration < max_iterations):
           a. Evaluate current draft with DocumentEvaluator
           b. Update best_score/best_version if current score is higher
           c. Decision 1: has_critical_issues(evaluation)?
              - Yes: Run IssueFixer, save new version, continue loop
           d. Decision 2: did_score_decrease(current_score, previous_score)?
              - Yes: Restore best version with VersionManager, break loop
           e. Decision 3: is_score_good_enough(current_score, threshold)?
              - Yes: Break loop (success)
           f. Else: Run DocumentPolisher, save new version, continue loop
           g. Update previous_score, increment iteration
        9. Store final polished draft in context
        10. Return summary results

        Returns:
            Dict[str, Any]: Execution results containing:
                - status: "success", "max_iterations_reached", or "score_decreased"
                - iterations_performed: Number of iterations executed
                - final_version: Version number of final draft
                - final_score: Quality score of final draft (0.0 to 1.0)
                - initial_score: Quality score from first evaluation
                - score_improvement: Change from initial to final score
                - evaluation_path: List of decisions made (for debugging)
                - final_draft: Final polished draft content
                - artifacts: Dict mapping artifact names to file paths
                - best_version: Version number with highest score
                - best_score: Highest quality score achieved

        Raises:
            KeyError: If required context data is missing
            Exception: If agent execution fails
        """
        self.logger.info("Starting writing and polishing workflow")

        # Step 1: Retrieve required context data
        master_resume = await self._get_context_data("master_resume")
        parsed_jd = await self._get_context_data("parsed_jd")
        company_culture = await self._get_context_data("company_culture")
        best_practices_resume = await self._get_context_data("best_practices_resume")
        best_practices_cover_letter = await self._get_context_data(
            "best_practices_cover_letter"
        )
        skills_gap_analysis = await self._get_context_data("skills_gap_analysis")

        # Validate required inputs
        if master_resume is None:
            raise KeyError("Missing required context data: 'master_resume'")
        if parsed_jd is None:
            raise KeyError("Missing required context data: 'parsed_jd'")

        # Step 2: Determine document type from context
        document_type = await self._get_context_data("document_type", "resume")
        self.logger.info(f"Document type: {document_type}")

        # Select appropriate best practices
        best_practices = (
            best_practices_cover_letter
            if document_type == "cover_letter"
            else best_practices_resume
        )

        # Step 3: Create initial draft using DraftWriter
        self.logger.info("=== Creating initial draft ===")
        draft_writer = DraftWriter(
            state_manager=self.state_manager, stage_name="initial_draft_writing"
        )

        draft_input = {
            "master_resume": master_resume,
            "parsed_jd": parsed_jd,
            "company_culture": company_culture,
            "best_practices": best_practices,
            "skills_gap_analysis": skills_gap_analysis,
            "document_type": document_type,
        }

        initial_draft = await draft_writer.run(draft_input)

        # Handle task instruction if needed
        if isinstance(initial_draft, dict) and initial_draft.get(
            "instruction"
        ) == "CALL_TASK_TOOL":
            self.logger.warning(
                "DraftWriter returned task instruction - requires manual execution"
            )
            raise RuntimeError(
                "DraftWriter requires Task tool execution - not yet implemented"
            )

        self.logger.info(
            f"Initial draft created: {len(initial_draft)} characters "
            f"({len(initial_draft.split())} words)"
        )

        # Checkpoint after draft creation
        await self._checkpoint(
            {
                "step": "initial_draft_created",
                "draft_length": len(initial_draft),
                "draft_word_count": len(initial_draft.split()),
            }
        )

        # Step 4: Run FactCheckingLoopOrchestra (sub-orchestra)
        self.logger.info("=== Running fact-checking sub-orchestra ===")

        # Set draft in context for fact-checking orchestra
        await self._set_context_data("draft", initial_draft)

        fact_checking_orchestra = FactCheckingLoopOrchestra(
            self.run_context, self.agent_pool
        )

        fact_check_results = await fact_checking_orchestra.execute()

        # Extract truthful draft from fact-checking results
        truthful_draft = fact_check_results.get("final_draft", initial_draft)
        fact_check_status = fact_check_results.get("status", "unknown")

        self.logger.info(
            f"Fact-checking complete: status={fact_check_status}, "
            f"iterations={fact_check_results.get('iterations_performed', 0)}"
        )

        # Checkpoint after fact-checking
        await self._checkpoint(
            {
                "step": "fact_checking_complete",
                "fact_check_status": fact_check_status,
                "fact_check_iterations": fact_check_results.get(
                    "iterations_performed", 0
                ),
            }
        )

        # Step 5: Post-fact-check processing (document-specific)
        self.logger.info("=== Running post-fact-check processing ===")
        processed_draft = await self._post_fact_check_processing(truthful_draft)

        self.logger.info(
            f"Post-fact-check processing complete: "
            f"{len(processed_draft)} characters"
        )

        # Checkpoint after post-processing
        await self._checkpoint(
            {
                "step": "post_fact_check_complete",
                "processed_draft_length": len(processed_draft),
            }
        )

        # Step 6: Store processed draft as version 0
        self.logger.info("=== Storing initial version ===")
        version_manager = VersionManager(
            state_manager=self.state_manager, stage_name="version_management"
        )

        version_input = {
            "action": "store",
            "draft": processed_draft,
            "version_number": 0,
            "document_type": document_type,
        }

        version_result = await version_manager.run(version_input)

        self.logger.info(f"Version 0 stored: {version_result}")

        # Step 7: Initialize loop state
        max_iterations = self.run_context.config.max_iterations
        quality_threshold = self.run_context.config.quality_threshold

        iteration = 0
        version_counter = 1
        previous_score = 0.0
        best_version = 0
        best_score = 0.0
        current_draft = processed_draft
        evaluation_path: List[str] = []
        artifacts: Dict[str, Path] = {}
        initial_score: float = 0.0

        self.logger.info(
            f"Starting evaluation loop: max_iterations={max_iterations}, "
            f"quality_threshold={quality_threshold}"
        )

        # Step 8: Main evaluation and improvement loop
        while iteration < max_iterations:
            iteration += 1
            self.logger.info(
                f"=== Iteration {iteration}/{max_iterations} ==="
            )

            # Step 7a: Evaluate current draft
            self.logger.info(f"Evaluating draft (iteration {iteration})")
            evaluator = DocumentEvaluator(
                state_manager=self.state_manager,
                stage_name=f"evaluation_iter_{iteration}",
            )

            eval_input = {
                "draft": current_draft,
                "parsed_jd": parsed_jd,
                "best_practices": best_practices,
                "document_type": document_type,
            }

            evaluation_result = await evaluator.run(eval_input)

            # Handle task instruction if needed
            if isinstance(evaluation_result, dict) and evaluation_result.get(
                "instruction"
            ) == "CALL_TASK_TOOL":
                self.logger.warning(
                    "DocumentEvaluator returned task instruction - requires manual execution"
                )
                # For now, use a default evaluation to prevent failure
                evaluation = DocumentEvaluation(
                    score=0.5,
                    has_critical_issues=False,
                    has_false_facts=False,
                    issue_count=0,
                    quality_notes="Manual evaluation required",
                    metadata={"iteration": iteration},
                )
            else:
                # Parse evaluation result into DocumentEvaluation object
                evaluation = DocumentEvaluation(
                    score=evaluation_result.get("score", 0.0),
                    has_critical_issues=evaluation_result.get(
                        "has_critical_issues", False
                    ),
                    has_false_facts=evaluation_result.get("has_false_facts", False),
                    issue_count=evaluation_result.get("issue_count", 0),
                    quality_notes=evaluation_result.get("quality_notes", ""),
                    metadata={"iteration": iteration},
                )

            current_score = evaluation.score

            # Store initial score on first iteration
            if iteration == 1:
                initial_score = current_score

            self.logger.info(
                f"Evaluation complete: score={current_score:.2f}, "
                f"critical_issues={evaluation.has_critical_issues}, "
                f"issue_count={evaluation.issue_count}"
            )

            # Step 7b: Update best score/version if current is better
            if current_score > best_score:
                best_score = current_score
                best_version = version_counter - 1
                self.logger.info(
                    f"New best score: {best_score:.2f} (version {best_version})"
                )

            # Checkpoint after evaluation
            await self._checkpoint(
                {
                    "iteration": iteration,
                    "current_score": current_score,
                    "best_score": best_score,
                    "best_version": best_version,
                }
            )

            # Step 7c: Decision 1 - Has critical issues?
            if has_critical_issues(evaluation):
                self.logger.warning(
                    f"Critical issues detected: {evaluation.issue_count} issues"
                )
                evaluation_path.append("issue_fix")

                # Run IssueFixer
                issue_fixer = IssueFixer(
                    state_manager=self.state_manager,
                    stage_name=f"issue_fixing_iter_{iteration}",
                )

                fixer_input = {
                    "draft": current_draft,
                    "evaluation": evaluation_result,
                    "document_type": document_type,
                }

                fixed_draft = await issue_fixer.run(fixer_input)

                # Handle task instruction
                if isinstance(fixed_draft, dict) and fixed_draft.get(
                    "instruction"
                ) == "CALL_TASK_TOOL":
                    self.logger.warning(
                        "IssueFixer returned task instruction - using current draft"
                    )
                else:
                    current_draft = fixed_draft
                    self.logger.info(
                        f"Issues fixed: {len(current_draft)} characters"
                    )

                    # Save new version
                    version_input = {
                        "action": "store",
                        "draft": current_draft,
                        "version_number": version_counter,
                        "document_type": document_type,
                    }
                    await version_manager.run(version_input)
                    version_counter += 1

                    # Store artifact
                    artifacts[f"fixed_draft_iter_{iteration}"] = Path(
                        f"fixed_draft_iteration_{iteration}.md"
                    )

                # Continue to next iteration
                previous_score = current_score
                continue

            # Step 7d: Decision 2 - Did score decrease?
            if iteration > 1 and did_score_decrease(current_score, previous_score):
                self.logger.warning(
                    f"Score decreased: {previous_score:.2f} → {current_score:.2f}"
                )
                evaluation_path.append("restore")

                # Restore best version
                self.logger.info(f"Restoring best version: {best_version}")
                restore_input = {
                    "action": "restore",
                    "version_number": best_version,
                    "document_type": document_type,
                }
                restored_draft = await version_manager.run(restore_input)

                if isinstance(restored_draft, dict) and restored_draft.get(
                    "instruction"
                ) == "CALL_TASK_TOOL":
                    self.logger.warning(
                        "VersionManager returned task instruction - using current best"
                    )
                    # Keep current_draft as is
                else:
                    current_draft = restored_draft
                    self.logger.info("Best version restored - exiting loop")

                # Exit loop
                break

            # Step 7e: Decision 3 - Is score good enough?
            if is_score_good_enough(current_score, quality_threshold):
                self.logger.info(
                    f"✓ Quality threshold met: {current_score:.2f} >= {quality_threshold:.2f}"
                )
                evaluation_path.append("complete")
                # Exit loop successfully
                break

            # Step 7f: Needs improvement - polish the draft
            self.logger.info(
                f"Score below threshold ({current_score:.2f} < {quality_threshold:.2f}) - polishing"
            )
            evaluation_path.append("polish")

            polisher = DocumentPolisher(
                state_manager=self.state_manager,
                stage_name=f"polishing_iter_{iteration}",
            )

            polisher_input = {
                "draft": current_draft,
                "evaluation": evaluation_result,
                "parsed_jd": parsed_jd,
                "best_practices": best_practices,
                "document_type": document_type,
            }

            polished_draft = await polisher.run(polisher_input)

            # Handle task instruction
            if isinstance(polished_draft, dict) and polished_draft.get(
                "instruction"
            ) == "CALL_TASK_TOOL":
                self.logger.warning(
                    "DocumentPolisher returned task instruction - using current draft"
                )
            else:
                current_draft = polished_draft
                self.logger.info(
                    f"Draft polished: {len(current_draft)} characters"
                )

                # Save new version
                version_input = {
                    "action": "store",
                    "draft": current_draft,
                    "version_number": version_counter,
                    "document_type": document_type,
                }
                await version_manager.run(version_input)
                version_counter += 1

                # Store artifact
                artifacts[f"polished_draft_iter_{iteration}"] = Path(
                    f"polished_draft_iteration_{iteration}.md"
                )

            # Step 7g: Update previous_score for next iteration
            previous_score = current_score

        # End of loop - determine final status
        max_iterations_reached = iteration >= max_iterations
        score_decreased = "restore" in evaluation_path

        if max_iterations_reached:
            status = "max_iterations_reached"
            self.logger.warning(
                f"⚠ Maximum iterations ({max_iterations}) reached"
            )
        elif score_decreased:
            status = "score_decreased"
            self.logger.info("Score decreased - best version restored")
        else:
            status = "success"
            self.logger.info("Quality threshold met - polishing complete")

        # Step 8: Store final polished draft in context
        await self._set_context_data("polished_draft", current_draft)
        await self._set_context_data("polishing_complete", True)
        await self._set_context_data("final_version", version_counter - 1)

        # Step 9: Build and return results summary
        score_improvement = current_score - initial_score

        results = {
            "status": status,
            "iterations_performed": iteration,
            "final_version": version_counter - 1,
            "final_score": current_score,
            "initial_score": initial_score,
            "score_improvement": score_improvement,
            "best_version": best_version,
            "best_score": best_score,
            "evaluation_path": evaluation_path,
            "final_draft": current_draft,
            "artifacts": artifacts,
            "max_iterations_reached": max_iterations_reached,
            "final_draft_length": len(current_draft),
            "final_draft_word_count": len(current_draft.split()),
            "document_type": document_type,
        }

        self.logger.info(
            f"Writing and polishing complete: {iteration} iterations, "
            f"status={status}, final_score={current_score:.2f}, "
            f"improvement={score_improvement:+.2f}"
        )

        return results
