"""
JDMatchingOrchestra - Coordinates job description matching and selection workflow.

This orchestrator manages the JD matching stage of the resume/cover letter tailoring
system. It runs ResumeJDMatcher agents in parallel (one per JD), analyzes match
results, and conditionally ranks/selects the top job descriptions when multiple JDs
are provided.

Workflow:
1. Retrieve master_resume, company_culture, parsed_jds from context
2. Execute ResumeJDMatcher agents in parallel (one per JD)
3. Collect all match results
4. Decision: Are there multiple JDs?
   - If yes: Run JDsRankerSelector to rank and select top JDs
   - If no: Use the single JD as selected
5. Update run_context.selected_jd_ids
6. Return summary with match statistics and artifacts

Author: ATS Research Project
"""

import logging
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

from .base_orchestra import BaseOrchestra
from ..state.run_context import OrchestrationStage
from ..agents.agent_pool import AgentPool
from ..agents.matching import ResumeJDMatcher, JDsRankerSelector
from ..decisions.decision_logic import should_rank_jds, MatchResult


class JDMatchingOrchestra(BaseOrchestra):
    """
    Orchestrates job description matching and selection workflow.

    This orchestra coordinates the JD_MATCHING stage, which involves:
    - Parallel execution of ResumeJDMatcher agents (one per job description)
    - Skills gap analysis for each JD
    - Conditional ranking/selection when multiple JDs exist
    - Context data preparation for next stage

    The orchestra uses decision logic from decision_logic.py to determine
    whether ranking is needed (multiple JDs) or can be skipped (single JD).

    Attributes:
        orchestra_name: "jd_matching"
        stage: OrchestrationStage.JD_MATCHING
        top_n: Number of top JDs to select when ranking (default: 3)

    Example:
        >>> config = Config(...)
        >>> run_context = await RunContext.create(config)
        >>> agent_pool = AgentPool(pool_size=5)
        >>> orchestra = JDMatchingOrchestra(run_context, agent_pool, top_n=3)
        >>> results = await orchestra.run()
        >>> print(f"Selected JDs: {results['selected_jd_ids']}")
        Selected JDs: ['JD-003', 'JD-001']
    """

    @property
    def orchestra_name(self) -> str:
        """
        Unique orchestra identifier.

        Returns:
            str: "jd_matching"
        """
        return "jd_matching"

    @property
    def stage(self) -> OrchestrationStage:
        """
        Associated orchestration stage.

        Returns:
            OrchestrationStage: JD_MATCHING stage
        """
        return OrchestrationStage.JD_MATCHING

    def __init__(
        self,
        run_context,
        agent_pool: AgentPool,
        top_n: int = 3
    ):
        """
        Initialize the JDMatchingOrchestra.

        Args:
            run_context: Shared context for tracking orchestration state
            agent_pool: Pool of agents for parallel execution
            top_n: Number of top JDs to select when ranking (default: 3)
        """
        super().__init__(run_context, agent_pool)
        self.top_n = top_n
        self.logger.info(
            f"Initialized JDMatchingOrchestra with top_n={top_n}"
        )

    async def execute(self) -> Dict[str, Any]:
        """
        Execute the JD matching and selection workflow.

        This method:
        1. Retrieves inputs from context (master_resume, company_culture, parsed_jds)
        2. Creates and executes ResumeJDMatcher agents in parallel (one per JD)
        3. Collects all match results
        4. Decides whether to rank JDs (uses should_rank_jds decision logic)
        5. If ranking needed: Runs JDsRankerSelector to select top N JDs
        6. If no ranking: Uses the single JD as selected
        7. Updates run_context.selected_jd_ids
        8. Saves artifacts and returns summary

        Returns:
            Dict[str, Any]: Execution results including:
                - total_jds: Number of JDs processed
                - matches_completed: Number of successful matches
                - ranking_performed: Whether ranking was performed
                - selected_jd_ids: List of selected JD IDs
                - top_match_score: Highest match score achieved
                - artifacts: Dict mapping artifact names to file paths
                - match_results: List of all MatchResult objects
                - selection_data: Ranking/selection data (if applicable)

        Raises:
            ValueError: If required context data is missing or invalid
            RuntimeError: If matching or ranking fails
        """
        self.logger.info("Starting JD matching workflow")

        # Step 1: Retrieve inputs from context
        master_resume = await self._get_context_data("master_resume")
        company_culture = await self._get_context_data("company_culture", default="")
        parsed_jds = await self._get_context_data("parsed_jds")

        # Validate inputs
        if not master_resume:
            raise ValueError("master_resume not found in context data")
        if not parsed_jds or not isinstance(parsed_jds, dict):
            raise ValueError(
                "parsed_jds not found or invalid format in context data "
                "(expected dict keyed by jd_id)"
            )

        jd_count = len(parsed_jds)
        self.logger.info(
            f"Retrieved inputs: resume_length={len(master_resume)}, "
            f"jd_count={jd_count}, "
            f"has_culture={len(company_culture) > 0}"
        )

        # Step 2: Prepare inputs for ResumeJDMatcher agents (one per JD)
        matcher_inputs = []
        jd_ids_list = []

        for jd_id, parsed_jd in parsed_jds.items():
            matcher_inputs.append({
                "master_resume": master_resume,
                "parsed_jd": parsed_jd,
                "company_culture": company_culture
            })
            jd_ids_list.append(jd_id)

        self.logger.info(
            f"Prepared {len(matcher_inputs)} ResumeJDMatcher inputs for JDs: "
            f"{', '.join(jd_ids_list)}"
        )

        # Step 3: Create and execute ResumeJDMatcher agents in parallel
        self.logger.info("Executing ResumeJDMatcher agents in parallel...")

        def create_matcher(input_data: Dict[str, Any]) -> ResumeJDMatcher:
            """Factory function to create ResumeJDMatcher instances."""
            return ResumeJDMatcher(
                state_manager=self.state_manager,
                stage=self.stage.value
            )

        # Execute all matchers in parallel via agent pool
        raw_results = await self.agent_pool.execute_batches(
            agent_factory=create_matcher,
            inputs=matcher_inputs
        )

        # Step 4: Collect match results and handle any failures
        match_results: List[MatchResult] = []
        failed_indices = []

        for i, result in enumerate(raw_results):
            if isinstance(result, Exception):
                self.logger.error(
                    f"ResumeJDMatcher {i} ({jd_ids_list[i]}) failed: {result}"
                )
                failed_indices.append(i)
            else:
                # Result should be a MatchResult from agent's run() method
                if isinstance(result, MatchResult):
                    match_results.append(result)
                else:
                    self.logger.warning(
                        f"Unexpected result type from matcher {i}: {type(result)}"
                    )

        matches_completed = len(match_results)
        self.logger.info(
            f"ResumeJDMatcher execution complete: "
            f"{matches_completed} succeeded, {len(failed_indices)} failed"
        )

        if matches_completed == 0:
            raise RuntimeError(
                "All ResumeJDMatcher agents failed - no match results available"
            )

        # Checkpoint intermediate results
        await self._checkpoint({
            "stage": "matching_completed",
            "matches_completed": matches_completed,
            "match_results": [
                {
                    "jd_id": m.jd_id,
                    "match_score": m.match_score,
                    "relevance_score": m.relevance_score
                }
                for m in match_results
            ]
        })

        # Step 5: Store all match results in context
        await self._set_context_data("match_results", match_results)

        # Step 6: Decision - should we rank JDs?
        ranking_performed = should_rank_jds(matches_completed)

        selected_jd_ids: List[str] = []
        selection_data: Dict[str, Any] = {}

        if ranking_performed:
            # Step 7a: Multiple JDs - run JDsRankerSelector
            self.logger.info(
                f"Multiple JDs detected ({matches_completed}), "
                f"running JDsRankerSelector to select top {self.top_n}"
            )

            ranker_selector = JDsRankerSelector(
                state_manager=self.state_manager,
                stage=self.stage.value,
                top_n=self.top_n
            )

            # Run ranker/selector agent
            selection_data = await ranker_selector.run(match_results)

            # Extract selected JD IDs from selection data
            selected_jd_ids = selection_data.get("selected_jds", [])

            self.logger.info(
                f"JDsRankerSelector complete: selected {len(selected_jd_ids)} JDs - "
                f"{', '.join(selected_jd_ids)}"
            )

            # Checkpoint ranking results
            await self._checkpoint({
                "stage": "ranking_completed",
                "selected_jd_ids": selected_jd_ids,
                "rankings": selection_data.get("rankings", [])
            })

        else:
            # Step 7b: Single JD - skip ranking, use as selected
            self.logger.info(
                "Single JD detected - skipping ranking, using as selected"
            )

            if match_results:
                selected_jd_ids = [match_results[0].jd_id]
                selection_data = {
                    "selected_jds": selected_jd_ids,
                    "rankings": [{
                        "jd_id": match_results[0].jd_id,
                        "match_score": match_results[0].match_score,
                        "relevance_score": match_results[0].relevance_score,
                        "rank": 1,
                        "selected": True,
                        "matched_keywords_count": len(match_results[0].matched_keywords),
                        "missing_skills_count": len(match_results[0].missing_skills),
                        "recommendation": match_results[0].recommendation
                    }],
                    "selection_rationale": (
                        f"Single JD provided - automatically selected: "
                        f"{match_results[0].jd_id} "
                        f"(match_score: {match_results[0].match_score:.2f})"
                    )
                }

            self.logger.info(
                f"Selected single JD: {selected_jd_ids[0] if selected_jd_ids else 'none'}"
            )

        # Step 8: Update run_context.selected_jd_ids
        self.run_context.selected_jd_ids = selected_jd_ids.copy()

        # Store selection data in context for next stage
        await self._set_context_data("jd_selection", selection_data)

        # Step 9: Calculate summary statistics
        top_match_score = 0.0
        if match_results:
            top_match_score = max(m.match_score for m in match_results)

        # Step 10: Save artifacts
        artifacts = await self._save_artifacts(
            match_results=match_results,
            selection_data=selection_data
        )

        # Step 11: Build and return summary
        summary = {
            "total_jds": jd_count,
            "matches_completed": matches_completed,
            "matches_failed": len(failed_indices),
            "ranking_performed": ranking_performed,
            "selected_jd_ids": selected_jd_ids,
            "selected_count": len(selected_jd_ids),
            "top_match_score": round(top_match_score, 3),
            "artifacts": artifacts,
            "match_results": match_results,
            "selection_data": selection_data,
        }

        self.logger.info(
            f"JD matching workflow complete: "
            f"{matches_completed}/{jd_count} matches successful, "
            f"{len(selected_jd_ids)} JDs selected, "
            f"top_score={top_match_score:.3f}"
        )

        return summary

    async def _save_artifacts(
        self,
        match_results: List[MatchResult],
        selection_data: Dict[str, Any]
    ) -> Dict[str, Path]:
        """
        Save match and selection artifacts to disk.

        Args:
            match_results: List of all MatchResult objects
            selection_data: Selection/ranking data from JDsRankerSelector

        Returns:
            Dict mapping artifact names to file paths
        """
        artifacts = {}

        try:
            # Save match results artifact
            match_results_data = [
                {
                    "jd_id": m.jd_id,
                    "match_score": m.match_score,
                    "relevance_score": m.relevance_score,
                    "matched_keywords": m.matched_keywords,
                    "missing_skills": m.missing_skills,
                    "recommendation": m.recommendation
                }
                for m in match_results
            ]

            match_artifact_path = await self.state_manager.save_artifact(
                stage=self.stage.value,
                artifact_name="match_results",
                data=match_results_data
            )
            artifacts["match_results"] = match_artifact_path

            self.logger.info(f"Saved match results artifact: {match_artifact_path}")

            # Save selection artifact if ranking was performed
            if selection_data.get("rankings"):
                selection_artifact_path = await self.state_manager.save_artifact(
                    stage=self.stage.value,
                    artifact_name="jd_selection",
                    data=selection_data
                )
                artifacts["jd_selection"] = selection_artifact_path

                self.logger.info(
                    f"Saved selection artifact: {selection_artifact_path}"
                )

        except Exception as e:
            self.logger.error(
                f"Failed to save artifacts: {e}",
                exc_info=True
            )
            # Don't raise - artifacts are supplementary

        return artifacts
