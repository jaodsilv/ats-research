"""PruningOrchestra for document length optimization with human feedback.

This module implements the pruning workflow that fits documents to target length
through iterative analysis, strategic rewriting/removal, and human-in-the-loop
feedback until the length is acceptable.
"""

from pathlib import Path
from typing import Dict, Any, List
import logging
from datetime import datetime

from .base_orchestra import BaseOrchestra
from ..state.run_context import RunContext, OrchestrationStage
from ..agents.agent_pool import AgentPool
from ..agents.pruning import (
    TEXTemplateFiller,
    TEXCompiler,
    TextImpactCalculator,
    RewritingEvaluator,
    RemovalEvaluator,
    DeltaCalculator,
    ChangesRanker,
    ChangeExecutor
)
from ..human.feedback import HumanFeedback
from ..utils.logging import log_checkpoint


class PruningOrchestra(BaseOrchestra):
    """Orchestra that prunes documents to target length with human-in-the-loop feedback.

    This orchestra implements an iterative pruning workflow:
    1. Compile initial PDF and get human feedback
    2. If acceptable: Promote to release version and exit
    3. If not acceptable: Enter pruning loop:
       a. Parallel analysis (TextImpactCalculator, RewritingEvaluator, RemovalEvaluator)
       b. Calculate quality delta scores for all proposed changes
       c. Rank changes by effectiveness
       d. Apply top-ranked change
       e. Re-compile PDF and get human feedback
       f. Repeat until acceptable or max iterations reached

    The loop continues until either:
    - Human accepts the length (success condition)
    - Maximum iterations reached (safety limit)

    Key Features:
    - Human-in-the-loop: Uses HumanFeedback for PDF review after each change
    - Parallel Analysis: Three evaluators run concurrently via agent_pool
    - Incremental Changes: Applies one change at a time, re-compiles, gets feedback
    - Change Tracking: Records all changes applied with rationale
    - Max Iterations Safety: Prevents infinite loops

    Attributes:
        orchestra_name: Unique identifier "pruning"
        stage: OrchestrationStage.PRUNING

    Example:
        >>> run_context = await RunContext.create(config)
        >>> agent_pool = AgentPool(max_workers=config.agent_pool_size)
        >>> orchestra = PruningOrchestra(run_context, agent_pool)
        >>> results = await orchestra.run()
        >>> print(f"Final PDF: {results['final_pdf_path']}")
        >>> print(f"Acceptable: {results['acceptable']}")
        >>> print(f"Changes applied: {len(results['changes_applied'])}")
    """

    @property
    def orchestra_name(self) -> str:
        """Unique orchestra identifier.

        Returns:
            str: "pruning"
        """
        return "pruning"

    @property
    def stage(self) -> OrchestrationStage:
        """Associated orchestration stage.

        Returns:
            OrchestrationStage: PRUNING stage
        """
        return OrchestrationStage.PRUNING

    async def execute(self) -> Dict[str, Any]:
        """Execute the pruning workflow with human feedback loop.

        This method implements the complete pruning workflow:
        1. Retrieve context: polished_draft, parsed_jd, best_practices, etc.
        2. Initialize HumanFeedback and iteration tracking
        3. Compile initial PDF
        4. Get initial human feedback
        5. If not acceptable, enter pruning loop:
           - Parallel analysis of rewriting/removal options
           - Calculate delta scores
           - Rank changes by effectiveness
           - Apply top change
           - Re-compile and get feedback
        6. Store final release version
        7. Return results summary

        Returns:
            Dict[str, Any]: Execution results containing:
                - status: "success" or "max_iterations_exceeded"
                - iterations: Number of pruning iterations performed
                - acceptable: Whether final length is acceptable
                - final_pdf_path: Path to final PDF
                - changes_applied: List of changes applied with details
                - artifacts: Dict mapping artifact names to file paths
                - feedback_log: List of all human feedback responses

        Raises:
            KeyError: If required context data is missing
            Exception: If agent execution fails
        """
        self.logger.info("Starting pruning workflow with human feedback loop")

        # Retrieve required context data
        polished_draft = await self._get_context_data("polished_draft")
        parsed_jd = await self._get_context_data("parsed_jd")
        best_practices = await self._get_context_data("best_practices")
        master_resume = await self._get_context_data("master_resume")
        company_culture = await self._get_context_data("company_culture")
        match_analysis = await self._get_context_data("match_analysis")

        if polished_draft is None:
            raise KeyError("Missing required context data: 'polished_draft'")
        if parsed_jd is None:
            raise KeyError("Missing required context data: 'parsed_jd'")

        # Get max iterations from config
        max_iterations = self.run_context.config.max_iterations
        self.logger.info(f"Max pruning iterations: {max_iterations}")

        # Initialize HumanFeedback collector
        human_feedback = HumanFeedback()

        # Initialize loop state
        iteration = 0
        current_draft = polished_draft
        acceptable = False
        changes_applied: List[Dict[str, Any]] = []
        feedback_log: List[Dict[str, Any]] = []
        artifacts: Dict[str, Path] = {}

        # Step 1: Initial compilation
        self.logger.info("=== Initial Compilation ===")
        initial_pdf_path = await self._compile_draft_to_pdf(
            draft=current_draft,
            iteration=0,
            artifacts=artifacts
        )

        # Step 2: Get initial human feedback
        self.logger.info("Getting initial human feedback...")
        initial_feedback = await human_feedback.get_length_feedback(initial_pdf_path)
        feedback_log.append(initial_feedback)

        acceptable = initial_feedback["acceptable"]
        self.logger.info(
            f"Initial feedback: acceptable={acceptable}, "
            f"comments='{initial_feedback.get('comments', '')}'"
        )

        # Checkpoint after initial feedback
        await self._checkpoint({
            "iteration": 0,
            "acceptable": acceptable,
            "initial_feedback": initial_feedback
        })

        # Decision: Is length acceptable?
        if acceptable:
            # Success - Promote to release version
            self.logger.info("✓ Initial length acceptable. Promoting to release version.")
            final_pdf_path = await self._promote_to_release(
                pdf_path=initial_pdf_path,
                draft=current_draft,
                artifacts=artifacts
            )

            results = {
                "status": "success",
                "iterations": 0,
                "acceptable": True,
                "final_pdf_path": final_pdf_path,
                "changes_applied": [],
                "artifacts": artifacts,
                "feedback_log": feedback_log
            }

            # Store final draft in context
            await self._set_context_data("pruned_draft", current_draft)
            await self._set_context_data("pruning_complete", True)

            self.logger.info("Pruning complete - no changes needed")
            return results

        # Step 3: Pruning loop (not acceptable)
        self.logger.info("✗ Initial length not acceptable. Entering pruning loop...")

        while not acceptable and iteration < max_iterations:
            iteration += 1
            self.logger.info(f"\n=== Pruning iteration {iteration}/{max_iterations} ===")

            # Step 3a: Parallel analysis
            self.logger.info(f"Running parallel analysis (iteration {iteration})")
            analysis_results = await self._run_parallel_analysis(
                current_draft=current_draft,
                iteration=iteration,
                parsed_jd=parsed_jd,
                best_practices=best_practices,
                master_resume=master_resume,
                company_culture=company_culture,
                match_analysis=match_analysis
            )

            # Step 3b: Calculate delta scores
            self.logger.info(f"Calculating delta scores (iteration {iteration})")
            delta_results = await self._calculate_delta_scores(
                analysis_results=analysis_results,
                iteration=iteration
            )

            # Step 3c: Rank changes
            self.logger.info(f"Ranking changes (iteration {iteration})")
            ranked_changes = await self._rank_changes(
                delta_results=delta_results,
                iteration=iteration
            )

            if not ranked_changes or len(ranked_changes) == 0:
                self.logger.warning(
                    f"No changes available in iteration {iteration}. Stopping loop."
                )
                break

            # Step 3d: Apply top-ranked change
            self.logger.info(f"Applying top-ranked change (iteration {iteration})")
            top_change = ranked_changes[0]
            execution_result = await self._apply_change(
                change=top_change,
                current_draft=current_draft,
                iteration=iteration
            )

            current_draft = execution_result["modified_draft"]
            changes_applied.append({
                "iteration": iteration,
                "change": top_change,
                "execution": execution_result
            })

            self.logger.info(
                f"Change applied: {execution_result.get('change_type', 'unknown')} - "
                f"{execution_result.get('description', 'no description')}"
            )

            # Checkpoint after change
            await self._checkpoint({
                "iteration": iteration,
                "change_applied": True,
                "change_type": execution_result.get("change_type"),
                "draft_length": len(current_draft)
            })

            # Step 3e: Re-compile and get feedback
            self.logger.info(f"Re-compiling PDF (iteration {iteration})")
            updated_pdf_path = await self._compile_draft_to_pdf(
                draft=current_draft,
                iteration=iteration,
                artifacts=artifacts
            )

            self.logger.info(f"Getting human feedback (iteration {iteration})")
            feedback = await human_feedback.get_length_feedback(updated_pdf_path)
            feedback_log.append(feedback)

            acceptable = feedback["acceptable"]
            self.logger.info(
                f"Feedback: acceptable={acceptable}, "
                f"comments='{feedback.get('comments', '')}'"
            )

            # Checkpoint after feedback
            await self._checkpoint({
                "iteration": iteration,
                "acceptable": acceptable,
                "feedback": feedback
            })

            # Decision: Is length acceptable now?
            if acceptable:
                self.logger.info(f"✓ Length acceptable after {iteration} iterations.")
                break

            # Continue loop
            self.logger.info(f"Iteration {iteration} complete. Continuing to next iteration.")

        # End of loop
        max_iterations_reached = iteration >= max_iterations

        if max_iterations_reached and not acceptable:
            self.logger.warning(
                f"⚠ Maximum iterations ({max_iterations}) reached. "
                f"Final document may not be at ideal length."
            )

        # Step 4: Finalization - Promote to release version
        self.logger.info("Promoting final version to release...")
        final_pdf_path = await self._promote_to_release(
            pdf_path=artifacts.get(f"pdf_iter_{iteration}", initial_pdf_path),
            draft=current_draft,
            artifacts=artifacts
        )

        # Store final draft in context for next stage
        await self._set_context_data("pruned_draft", current_draft)
        await self._set_context_data("pruning_complete", True)

        # Determine overall status
        if acceptable:
            status = "success"
        else:
            status = "max_iterations_exceeded"

        # Build results summary
        results = {
            "status": status,
            "iterations": iteration,
            "acceptable": acceptable,
            "final_pdf_path": final_pdf_path,
            "changes_applied": changes_applied,
            "artifacts": artifacts,
            "feedback_log": feedback_log,
            "final_draft_length": len(current_draft),
            "final_draft_word_count": len(current_draft.split())
        }

        self.logger.info(
            f"Pruning complete: {iteration} iterations, "
            f"status={status}, acceptable={acceptable}, "
            f"changes_applied={len(changes_applied)}"
        )

        return results

    async def _compile_draft_to_pdf(
        self,
        draft: str,
        iteration: int,
        artifacts: Dict[str, Path]
    ) -> Path:
        """Compile draft to PDF using TEXTemplateFiller and TEXCompiler.

        Args:
            draft: Draft content to compile
            iteration: Current iteration number (0 = initial)
            artifacts: Artifacts dict to update with paths

        Returns:
            Path to compiled PDF

        Raises:
            RuntimeError: If compilation fails
        """
        # Step 1: Fill TEX template
        self.logger.debug(f"Filling TEX template (iteration {iteration})")
        template_filler = TEXTemplateFiller(
            state_manager=self.state_manager,
            stage_name=f"template_fill_iter_{iteration}"
        )

        tex_content = await template_filler.run({"draft": draft})

        # Store TEX file
        tex_path = self.run_context.config.runs_dir / f"draft_iter_{iteration}.tex"
        tex_path.write_text(tex_content, encoding="utf-8")
        artifacts[f"tex_iter_{iteration}"] = tex_path

        # Step 2: Compile to PDF
        self.logger.debug(f"Compiling PDF (iteration {iteration})")
        compiler = TEXCompiler(
            state_manager=self.state_manager,
            stage_name=f"compile_iter_{iteration}"
        )

        pdf_path = self.run_context.config.runs_dir / f"draft_iter_{iteration}.pdf"
        compile_result = await compiler.run({
            "tex_content": tex_content,
            "output_path": str(pdf_path)
        })

        if not compile_result["success"]:
            error_msg = f"PDF compilation failed: {compile_result['errors']}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)

        artifacts[f"pdf_iter_{iteration}"] = Path(compile_result["pdf_path"])
        self.logger.info(f"PDF compiled successfully: {compile_result['pdf_path']}")

        return Path(compile_result["pdf_path"])

    async def _run_parallel_analysis(
        self,
        current_draft: str,
        iteration: int,
        parsed_jd: Any,
        best_practices: Any,
        master_resume: Any,
        company_culture: Any,
        match_analysis: Any
    ) -> Dict[str, Any]:
        """Run parallel analysis with TextImpactCalculator, RewritingEvaluator, and RemovalEvaluator.

        Args:
            current_draft: Current draft content
            iteration: Current iteration number
            parsed_jd: Parsed job description
            best_practices: Best practices data
            master_resume: Master resume content
            company_culture: Company culture data
            match_analysis: Match and skills gap analysis

        Returns:
            Dict with analysis results from all three agents
        """
        # Prepare common input data
        common_input = {
            "draft": current_draft,
            "parsed_jd": parsed_jd,
            "best_practices": best_practices,
            "master_resume": master_resume,
            "company_culture": company_culture,
            "match_analysis": match_analysis
        }

        # Create agents
        impact_calculator = TextImpactCalculator(
            state_manager=self.state_manager,
            stage_name=f"impact_calc_iter_{iteration}"
        )

        rewriting_evaluator = RewritingEvaluator(
            state_manager=self.state_manager,
            stage_name=f"rewriting_eval_iter_{iteration}"
        )

        removal_evaluator = RemovalEvaluator(
            state_manager=self.state_manager,
            stage_name=f"removal_eval_iter_{iteration}"
        )

        # Execute in parallel via agent_pool
        self.logger.debug("Executing parallel analysis agents")
        agents = [impact_calculator, rewriting_evaluator, removal_evaluator]
        inputs = [common_input, common_input, common_input]

        results = await self.agent_pool.execute_agents(agents, inputs)

        # Check for errors
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"Analysis agent {i} failed: {result}")
                raise result

        return {
            "impact_scores": results[0],
            "rewriting_options": results[1],
            "removal_options": results[2]
        }

    async def _calculate_delta_scores(
        self,
        analysis_results: Dict[str, Any],
        iteration: int
    ) -> Dict[str, Any]:
        """Calculate quality delta scores for all proposed changes.

        Args:
            analysis_results: Results from parallel analysis
            iteration: Current iteration number

        Returns:
            Dict with delta scores for all changes
        """
        delta_calculator = DeltaCalculator(
            state_manager=self.state_manager,
            stage_name=f"delta_calc_iter_{iteration}"
        )

        delta_results = await delta_calculator.run(analysis_results)

        self.logger.debug(
            f"Delta scores calculated: {len(delta_results.get('changes', []))} changes"
        )

        return delta_results

    async def _rank_changes(
        self,
        delta_results: Dict[str, Any],
        iteration: int
    ) -> List[Dict[str, Any]]:
        """Rank changes by effectiveness using ChangesRanker.

        Args:
            delta_results: Delta scores for all changes
            iteration: Current iteration number

        Returns:
            List of ranked changes (best first)
        """
        changes_ranker = ChangesRanker(
            state_manager=self.state_manager,
            stage_name=f"ranker_iter_{iteration}"
        )

        ranked_changes = await changes_ranker.run(delta_results)

        self.logger.debug(
            f"Changes ranked: {len(ranked_changes)} changes, "
            f"top change score: {ranked_changes[0].get('score', 'N/A') if ranked_changes else 'N/A'}"
        )

        return ranked_changes

    async def _apply_change(
        self,
        change: Dict[str, Any],
        current_draft: str,
        iteration: int
    ) -> Dict[str, Any]:
        """Apply the top-ranked change using ChangeExecutor.

        Args:
            change: Change specification to apply
            current_draft: Current draft content
            iteration: Current iteration number

        Returns:
            Dict with execution results including modified draft
        """
        change_executor = ChangeExecutor(
            state_manager=self.state_manager,
            stage_name=f"executor_iter_{iteration}"
        )

        execution_result = await change_executor.run({
            "change": change,
            "draft": current_draft
        })

        self.logger.debug(
            f"Change executed: {execution_result.get('change_type', 'unknown')}"
        )

        return execution_result

    async def _promote_to_release(
        self,
        pdf_path: Path,
        draft: str,
        artifacts: Dict[str, Path]
    ) -> Path:
        """Promote the final version to release.

        Args:
            pdf_path: Path to PDF to promote
            draft: Final draft content
            artifacts: Artifacts dict to update

        Returns:
            Path to release version PDF
        """
        import shutil

        # Copy PDF to release location
        release_pdf_path = self.run_context.config.runs_dir / "release_version.pdf"
        shutil.copy2(pdf_path, release_pdf_path)

        # Save release draft
        release_draft_path = self.run_context.config.runs_dir / "release_version.md"
        release_draft_path.write_text(draft, encoding="utf-8")

        artifacts["release_pdf"] = release_pdf_path
        artifacts["release_draft"] = release_draft_path

        self.logger.info(f"Release version promoted: {release_pdf_path}")

        return release_pdf_path
