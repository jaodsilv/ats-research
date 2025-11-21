"""JDsRankerSelector agent for ranking and selecting top job descriptions.

This agent ranks multiple job description match results and selects the top N
candidates for resume tailoring. Runs conditionally only when multiple JDs exist.
"""

import logging
from typing import Dict, Any, List

from ..base_agent import BaseAgent
from ...decisions.decision_logic import MatchResult, select_top_jds


class JDsRankerSelector(BaseAgent[List[MatchResult], Dict[str, Any]]):
    """Agent that ranks job descriptions and selects top candidates.

    This agent takes match results from multiple ResumeJDMatcher runs, ranks them
    by match score, and selects the top N job descriptions for tailoring.
    Only runs when there are multiple JDs to compare (conditional execution).

    Uses the select_top_jds() function from decision_logic module for ranking logic.

    Input Format:
        List of MatchResult dataclasses:
        [
            MatchResult(jd_id="JD-001", match_score=0.85, ...),
            MatchResult(jd_id="JD-002", match_score=0.72, ...),
            MatchResult(jd_id="JD-003", match_score=0.91, ...)
        ]

    Output Format:
        Dict with:
        {
            "selected_jds": ["JD-003", "JD-001", "JD-002"],  # Top N jd_ids
            "rankings": [                                     # All JDs ranked
                {
                    "jd_id": "JD-003",
                    "match_score": 0.91,
                    "relevance_score": 0.88,
                    "rank": 1,
                    "selected": true
                },
                ...
            ],
            "selection_rationale": "Selected top 3 JDs based on match scores..."
        }

    Example:
        >>> state_mgr = StateManager(Path("./run_001"))
        >>> agent = JDsRankerSelector(state_mgr, "jd_matching")
        >>> matches = [
        ...     MatchResult("JD-001", 0.85, 0.82, [...], [...], "Strong match"),
        ...     MatchResult("JD-002", 0.72, 0.75, [...], [...], "Good match"),
        ...     MatchResult("JD-003", 0.91, 0.88, [...], [...], "Excellent match")
        ... ]
        >>> result = await agent.run(matches)
        >>> print(result["selected_jds"])
        ['JD-003', 'JD-001', 'JD-002']
    """

    def __init__(self, state_manager, stage: str, top_n: int = 3) -> None:
        """Initialize the JDsRankerSelector agent.

        Args:
            state_manager: StateManager instance for artifact persistence
            stage: Workflow stage name
            top_n: Number of top JDs to select (default: 3)
        """
        super().__init__(state_manager, stage)
        self.top_n = top_n
        self.logger.info(f"Initialized JDsRankerSelector with top_n={top_n}")

    @property
    def agent_name(self) -> str:
        """Unique identifier for this agent type.

        Returns:
            Agent name string
        """
        return "jds_ranker_selector"

    @property
    def agent_type(self) -> str:
        """Claude Code subagent type to use for this agent.

        Returns:
            Subagent type string
        """
        return "general-purpose"

    async def validate_input(self, input_data: List[MatchResult]) -> bool:
        """Validate input is a list of MatchResult objects.

        Checks that:
        1. Input is a list
        2. List is not empty
        3. All elements are MatchResult instances
        4. All MatchResults have valid scores (0.0-1.0)

        Args:
            input_data: List of MatchResult objects to validate

        Returns:
            True if input is valid, False otherwise
        """
        # Check type
        if not isinstance(input_data, list):
            self.logger.error(f"Input must be list, got {type(input_data)}")
            return False

        # Check non-empty
        if len(input_data) == 0:
            self.logger.error("Input list is empty")
            return False

        # Check all elements are MatchResult
        for i, item in enumerate(input_data):
            if not isinstance(item, MatchResult):
                self.logger.error(
                    f"Item {i} is not MatchResult, got {type(item)}"
                )
                return False

            # Validate score ranges
            if not (0.0 <= item.match_score <= 1.0):
                self.logger.error(
                    f"Invalid match_score for {item.jd_id}: {item.match_score}"
                )
                return False

            if not (0.0 <= item.relevance_score <= 1.0):
                self.logger.error(
                    f"Invalid relevance_score for {item.jd_id}: {item.relevance_score}"
                )
                return False

        self.logger.info(
            f"Input validation passed: {len(input_data)} MatchResult objects"
        )
        return True

    async def execute(self, input_data: List[MatchResult]) -> Dict[str, Any]:
        """Rank job descriptions and select top N candidates.

        Uses the select_top_jds() decision logic function to perform ranking.

        Args:
            input_data: List of MatchResult objects from ResumeJDMatcher

        Returns:
            Dict with selected_jds, rankings, and selection_rationale

        Raises:
            RuntimeError: If ranking/selection fails
        """
        matches = input_data

        self.logger.info(
            f"Ranking {len(matches)} job descriptions, selecting top {self.top_n}"
        )

        # Use decision logic to select top JDs
        selected_jd_ids = select_top_jds(matches, top_n=self.top_n)

        # Sort all matches by match_score descending for full rankings
        sorted_matches = sorted(
            matches,
            key=lambda m: m.match_score,
            reverse=True
        )

        # Build detailed rankings list
        rankings = []
        for rank, match in enumerate(sorted_matches, start=1):
            rankings.append({
                "jd_id": match.jd_id,
                "match_score": round(match.match_score, 3),
                "relevance_score": round(match.relevance_score, 3),
                "rank": rank,
                "selected": match.jd_id in selected_jd_ids,
                "matched_keywords_count": len(match.matched_keywords),
                "missing_skills_count": len(match.missing_skills),
                "recommendation": match.recommendation
            })

        # Generate selection rationale
        rationale = self._generate_rationale(
            selected_jd_ids,
            sorted_matches,
            self.top_n
        )

        result = {
            "selected_jds": selected_jd_ids,
            "rankings": rankings,
            "selection_rationale": rationale
        }

        self.logger.info(
            f"Ranked {len(matches)} JDs, selected top {len(selected_jd_ids)}: "
            f"{', '.join(selected_jd_ids)}"
        )

        return result

    async def format_output(self, raw_output: Dict[str, Any]) -> Dict[str, Any]:
        """Format the raw ranking output (pass-through in this case).

        Args:
            raw_output: Raw output from execute()

        Returns:
            Formatted output dict (same structure)
        """
        # Validate structure
        if not isinstance(raw_output, dict):
            self.logger.error(f"Raw output must be dict, got {type(raw_output)}")
            return {
                "selected_jds": [],
                "rankings": [],
                "selection_rationale": "Error: Invalid output format"
            }

        # Ensure all expected keys exist
        formatted = {
            "selected_jds": raw_output.get("selected_jds", []),
            "rankings": raw_output.get("rankings", []),
            "selection_rationale": raw_output.get(
                "selection_rationale",
                "No rationale provided"
            )
        }

        self.logger.info(
            f"Formatted ranking output: {len(formatted['selected_jds'])} selected, "
            f"{len(formatted['rankings'])} total rankings"
        )

        return formatted

    def _generate_rationale(
        self,
        selected_jd_ids: List[str],
        sorted_matches: List[MatchResult],
        top_n: int
    ) -> str:
        """Generate human-readable selection rationale.

        Args:
            selected_jd_ids: List of selected JD IDs
            sorted_matches: All matches sorted by score
            top_n: Number requested to select

        Returns:
            Human-readable rationale string
        """
        num_total = len(sorted_matches)
        num_selected = len(selected_jd_ids)

        # Get scores of selected JDs
        selected_matches = [
            m for m in sorted_matches if m.jd_id in selected_jd_ids
        ]
        if selected_matches:
            avg_match = sum(m.match_score for m in selected_matches) / len(selected_matches)
            min_match = min(m.match_score for m in selected_matches)
            max_match = max(m.match_score for m in selected_matches)

            rationale = (
                f"Selected top {num_selected} job descriptions out of {num_total} total. "
                f"Selected JDs have match scores ranging from {min_match:.2f} to {max_match:.2f} "
                f"(average: {avg_match:.2f}). "
            )

            # Add quality assessment
            if avg_match >= 0.8:
                rationale += "These are excellent matches with strong alignment to the resume."
            elif avg_match >= 0.7:
                rationale += "These are good matches with solid skill coverage."
            elif avg_match >= 0.6:
                rationale += "These are fair matches with some skill gaps to address."
            else:
                rationale += "These matches have notable gaps but represent the best available options."

            # Mention if we selected fewer than requested
            if num_selected < top_n:
                rationale += f" (Note: Only {num_selected} JDs available, requested {top_n}.)"

        else:
            rationale = f"No job descriptions selected from {num_total} available."

        return rationale

    def _get_input_summary(self, input_data: List[MatchResult]) -> Dict[str, Any]:
        """Create summary of input data for logging.

        Args:
            input_data: List of MatchResult objects

        Returns:
            Dictionary with input summary information
        """
        if not input_data:
            return {"match_count": 0}

        scores = [m.match_score for m in input_data]
        avg_score = sum(scores) / len(scores)

        return {
            "match_count": len(input_data),
            "avg_match_score": round(avg_score, 3),
            "min_match_score": round(min(scores), 3),
            "max_match_score": round(max(scores), 3),
            "jd_ids": [m.jd_id for m in input_data],
        }

    def _get_output_summary(self, output_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create summary of output data for logging.

        Args:
            output_data: Ranking output data

        Returns:
            Dictionary with output summary information
        """
        return {
            "total_jds": len(output_data.get("rankings", [])),
            "selected_count": len(output_data.get("selected_jds", [])),
            "selected_jds": output_data.get("selected_jds", []),
            "top_score": (
                output_data["rankings"][0]["match_score"]
                if output_data.get("rankings")
                else 0.0
            ),
        }
