"""ChangesRanker agent for ranking changes by quality-to-length ratio.

This agent ranks all proposed changes by their quality-to-length ratio,
helping select the best changes to apply for optimal length reduction
with minimal quality loss.
"""

import logging
from typing import Dict, Any, List

from ..base_agent import BaseAgent
from ...decisions.decision_logic import evaluate_change_impact


class ChangesRanker(BaseAgent[Dict[str, Any], Dict[str, Any]]):
    """Agent that ranks changes by quality-to-length ratio.

    This agent takes changes with quality delta and ranks them to identify
    the best changes to apply. It uses decision logic functions to determine
    which changes should be applied.

    Input Format:
        Dict with keys:
        {
            "changes_with_delta": List[dict]  # Changes with quality_delta
        }

    Output Format:
        Dict with keys:
        {
            "ranked_changes": List[dict],     # Changes ranked by effectiveness
            "selection_threshold": float      # Recommended quality delta threshold
        }

    Example:
        >>> state_mgr = StateManager(Path("./run_001"))
        >>> agent = ChangesRanker(state_mgr, "pruning")
        >>> input_data = {
        ...     "changes_with_delta": [
        ...         {"quality_delta": -0.05, "length_reduction": 50, ...},
        ...         {"quality_delta": 0.1, "length_reduction": 30, ...}
        ...     ]
        ... }
        >>> result = await agent.run(input_data)
        >>> ranked = result["ranked_changes"]
    """

    @property
    def agent_name(self) -> str:
        """Unique identifier for this agent type.

        Returns:
            Agent name string
        """
        return "changes_ranker"

    @property
    def agent_type(self) -> str:
        """Claude Code subagent type to use for this agent.

        Returns:
            Subagent type string
        """
        return "general-purpose"

    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input contains all required fields.

        Checks that:
        1. Input is a dictionary
        2. Required key exists: changes_with_delta
        3. Changes is a list

        Args:
            input_data: Input data to validate

        Returns:
            True if input is valid, False otherwise
        """
        # Check type
        if not isinstance(input_data, dict):
            self.logger.error(f"Input must be dict, got {type(input_data)}")
            return False

        # Check required keys
        if "changes_with_delta" not in input_data:
            self.logger.error("Missing required key: changes_with_delta")
            return False

        # Validate changes
        changes = input_data.get("changes_with_delta", [])
        if not isinstance(changes, list):
            self.logger.error("changes_with_delta must be a list")
            return False

        if len(changes) == 0:
            self.logger.warning("Changes list is empty")
            # Not an error, just means no changes to rank

        self.logger.info(f"Input validation passed: {len(changes)} changes to rank")
        return True

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Rank changes by quality-to-length ratio.

        This uses decision logic rather than Task tool for ranking,
        as it's a deterministic calculation.

        Args:
            input_data: Validated input data with changes

        Returns:
            Dict with ranked changes and selection threshold

        Raises:
            RuntimeError: If ranking fails
        """
        changes = input_data["changes_with_delta"]

        self.logger.info(f"Ranking {len(changes)} changes by effectiveness")

        if len(changes) == 0:
            return {
                "ranked_changes": [],
                "selection_threshold": 0.0
            }

        # Calculate effectiveness score for each change
        scored_changes = []
        for change in changes:
            if not isinstance(change, dict):
                continue

            quality_delta = float(change.get("quality_delta", 0.0))
            length_reduction = int(change.get("length_reduction", 0))

            if length_reduction <= 0:
                # Skip changes with no length benefit
                continue

            # Effectiveness = quality_delta / length_reduction
            # Higher is better (more quality per character saved)
            # Positive effectiveness = quality improvement or minimal loss per char
            # Negative effectiveness = quality loss per char
            effectiveness = quality_delta / length_reduction if length_reduction > 0 else -999.0

            scored_change = {
                **change,  # Preserve all original fields
                "effectiveness_score": effectiveness
            }

            # Apply decision logic to evaluate if change should be applied
            change_type = "rewrite" if "rewritten_text" in change else "removal"
            impact_score = change.get("impact_score", 0.5)  # For removals
            should_apply = evaluate_change_impact(change_type, impact_score, quality_delta)

            scored_change["recommended"] = should_apply

            scored_changes.append(scored_change)

        # Sort by effectiveness (descending - best first)
        ranked_changes = sorted(
            scored_changes,
            key=lambda x: x["effectiveness_score"],
            reverse=True
        )

        # Calculate selection threshold based on ranked changes
        # Threshold is the quality_delta where we transition from recommended to not recommended
        recommended_deltas = [
            c["quality_delta"] for c in ranked_changes if c.get("recommended", False)
        ]

        if recommended_deltas:
            # Threshold is slightly below the worst recommended change
            selection_threshold = min(recommended_deltas) - 0.01
        else:
            # No recommended changes
            selection_threshold = 0.0

        self.logger.info(
            f"Ranked {len(ranked_changes)} changes, "
            f"threshold = {selection_threshold:.3f}"
        )

        return {
            "ranked_changes": ranked_changes,
            "selection_threshold": selection_threshold
        }

    async def format_output(self, raw_output: Any) -> Dict[str, Any]:
        """Format the raw output (already formatted in execute).

        Args:
            raw_output: Raw output from execute()

        Returns:
            Formatted output dict
        """
        # Output is already in correct format from execute()
        if isinstance(raw_output, dict):
            return raw_output
        else:
            # Shouldn't happen, but handle gracefully
            return {
                "ranked_changes": [],
                "selection_threshold": 0.0
            }

    def _get_input_summary(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create summary of input data for logging.

        Args:
            input_data: Input data to summarize

        Returns:
            Dictionary with input summary information
        """
        changes = input_data.get("changes_with_delta", [])
        if changes:
            deltas = [c.get("quality_delta", 0.0) for c in changes if isinstance(c, dict)]
            avg_delta = sum(deltas) / len(deltas) if deltas else 0.0

            return {
                "change_count": len(changes),
                "average_quality_delta": round(avg_delta, 3),
                "positive_delta_count": sum(1 for d in deltas if d > 0)
            }

        return {"change_count": 0}

    def _get_output_summary(self, output_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create summary of output data for logging.

        Args:
            output_data: Ranking result

        Returns:
            Dictionary with output summary information
        """
        ranked = output_data.get("ranked_changes", [])
        threshold = output_data.get("selection_threshold", 0.0)

        if ranked:
            recommended_count = sum(1 for c in ranked if c.get("recommended", False))
            total_reduction = sum(c.get("length_reduction", 0) for c in ranked)

            return {
                "type": "ranked_changes",
                "total_changes": len(ranked),
                "recommended_count": recommended_count,
                "selection_threshold": round(threshold, 3),
                "total_possible_reduction": total_reduction
            }

        return {
            "type": "ranked_changes",
            "total_changes": 0,
            "recommended_count": 0,
            "selection_threshold": round(threshold, 3)
        }
