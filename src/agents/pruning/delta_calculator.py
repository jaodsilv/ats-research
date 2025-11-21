"""DeltaCalculator agent for calculating quality delta for changes.

This agent calculates the quality delta (change in document quality) for each
proposed change (rewrite or removal) by comparing before/after quality scores.
"""

import logging
from typing import Dict, Any, List

from ..base_agent import BaseAgent


class DeltaCalculator(BaseAgent[Dict[str, Any], Dict[str, Any]]):
    """Agent that calculates quality delta for proposed changes.

    This agent takes a list of proposed changes (rewrites and removals) and
    calculates the quality delta for each by evaluating the document quality
    before and after the change. It may use DocumentEvaluator as a sub-agent.

    Input Format:
        Dict with keys:
        {
            "changes": List[dict]            # Combined rewrite and removal options
        }

        Each change dict should contain either:
        - Rewrite: original_text, rewritten_text, impact_delta, length_reduction, rationale
        - Removal: text_to_remove, impact_score, length_reduction, rationale

    Output Format:
        Dict with keys:
        {
            "changes_with_delta": List[dict] # Changes with quality_delta added
        }

        Each output dict contains all original fields plus:
        {
            "quality_delta": float           # Change in overall quality (-1.0 to +1.0)
        }

    Example:
        >>> state_mgr = StateManager(Path("./run_001"))
        >>> agent = DeltaCalculator(state_mgr, "pruning")
        >>> input_data = {
        ...     "changes": [
        ...         {"original_text": "...", "rewritten_text": "...", ...},
        ...         {"text_to_remove": "...", "impact_score": 0.2, ...}
        ...     ]
        ... }
        >>> result = await agent.run(input_data)
        >>> changes = result["changes_with_delta"]
    """

    @property
    def agent_name(self) -> str:
        """Unique identifier for this agent type.

        Returns:
            Agent name string
        """
        return "delta_calculator"

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
        2. Required key exists: changes
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
        if "changes" not in input_data:
            self.logger.error("Missing required key: changes")
            return False

        # Validate changes
        changes = input_data.get("changes", [])
        if not isinstance(changes, list):
            self.logger.error("changes must be a list")
            return False

        if len(changes) == 0:
            self.logger.warning("Changes list is empty")
            # Not an error, just means no changes to process

        self.logger.info(f"Input validation passed: {len(changes)} changes to process")
        return True

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate quality delta for each change using Task tool.

        Args:
            input_data: Validated input data with changes

        Returns:
            Dict with task instruction for delta calculation

        Raises:
            RuntimeError: If calculation fails
        """
        changes = input_data["changes"]

        self.logger.info(f"Calculating quality delta for {len(changes)} changes")

        # Build prompt for Task tool
        prompt = self._build_delta_calc_prompt(input_data)

        # Task tool invocation structure
        task_instruction = {
            "instruction": "CALL_TASK_TOOL",
            "agent_type": self.agent_type,
            "prompt": prompt,
            "change_count": len(changes)
        }

        self.logger.info("Generated delta calculation instruction")

        return task_instruction

    async def format_output(self, raw_output: Any) -> Dict[str, Any]:
        """Format the raw output into changes with quality delta.

        Args:
            raw_output: Raw output from execute() or Task tool

        Returns:
            Dict with changes_with_delta list
        """
        # If this is a task instruction (pre-execution), return as-is
        if isinstance(raw_output, dict) and raw_output.get("instruction") == "CALL_TASK_TOOL":
            self.logger.debug("Output is task instruction (pre-execution), passing through")
            return raw_output

        # Parse output into structured format
        if isinstance(raw_output, dict) and "changes_with_delta" in raw_output:
            result = raw_output
        elif isinstance(raw_output, list):
            result = {"changes_with_delta": raw_output}
        else:
            # Fallback
            self.logger.warning("Unexpected output format, using empty changes")
            result = {"changes_with_delta": []}

        # Validate changes
        changes = result.get("changes_with_delta", [])
        if not isinstance(changes, list):
            self.logger.error("changes_with_delta must be a list")
            result["changes_with_delta"] = []
        else:
            # Ensure each change has quality_delta field
            validated_changes = []
            for change in changes:
                if isinstance(change, dict):
                    # Ensure quality_delta exists
                    if "quality_delta" not in change:
                        change["quality_delta"] = 0.0
                    else:
                        change["quality_delta"] = float(change["quality_delta"])
                    validated_changes.append(change)
            result["changes_with_delta"] = validated_changes

        self.logger.info(f"Formatted {len(result['changes_with_delta'])} changes with delta")

        return result

    def _build_delta_calc_prompt(self, input_data: Dict[str, Any]) -> str:
        """Build prompt for Task tool to calculate quality delta.

        Args:
            input_data: Input data with changes

        Returns:
            Formatted prompt string for Task tool
        """
        changes = input_data["changes"]

        # Serialize changes for prompt
        import json
        changes_json = json.dumps(changes, indent=2, ensure_ascii=False)

        prompt = f"""Calculate the quality delta (change in overall document quality) for each proposed change.

CHANGES TO EVALUATE:
{changes_json}

TASK:
For each change (rewrite or removal), calculate the quality_delta that represents how the change
affects the overall document quality.

QUALITY DELTA CALCULATION:

For **Rewrites**:
- If the change already has "impact_delta", use it as a starting point
- Consider: clarity improvement, conciseness, keyword preservation, professional tone
- Positive delta: Change improves quality (stronger verbs, better clarity)
- Zero delta: Change maintains quality (just shorter)
- Negative delta: Change reduces quality (loses information, clarity)

For **Removals**:
- Quality delta is typically negative (removing content reduces completeness)
- Low-impact content (score < 0.2): delta ≈ -0.05 to -0.1 (minor quality loss)
- Medium-low impact (score 0.2-0.4): delta ≈ -0.1 to -0.2 (moderate quality loss)
- Medium impact (score 0.4-0.6): delta ≈ -0.2 to -0.4 (significant quality loss)
- High impact (score > 0.6): delta < -0.4 (major quality loss - should not remove!)

QUALITY DELTA SCALE:
- -1.0 to -0.5: Major quality degradation
- -0.5 to -0.2: Moderate quality loss
- -0.2 to -0.1: Minor quality loss
- -0.1 to +0.1: Negligible change
- +0.1 to +0.3: Quality improvement
- +0.3 to +1.0: Significant quality improvement

EXAMPLES:

Rewrite Example 1:
{{
  "original_text": "Responsible for leading team of engineers",
  "rewritten_text": "Led engineering team",
  "impact_delta": 0.05,
  "length_reduction": 23,
  "quality_delta": 0.05  # Stronger verb, maintains meaning
}}

Rewrite Example 2:
{{
  "original_text": "Successfully implemented new features",
  "rewritten_text": "Implemented features",
  "impact_delta": 0.0,
  "length_reduction": 17,
  "quality_delta": 0.0  # Same meaning, just shorter
}}

Removal Example 1:
{{
  "text_to_remove": "Proficient in Microsoft Office",
  "impact_score": 0.15,
  "length_reduction": 33,
  "quality_delta": -0.05  # Low impact, minimal quality loss
}}

Removal Example 2:
{{
  "text_to_remove": "Led migration to microservices architecture",
  "impact_score": 0.85,
  "length_reduction": 45,
  "quality_delta": -0.5  # High impact, major quality loss!
}}

INSTRUCTIONS:
1. For each change in the input list, calculate quality_delta
2. For rewrites, consider impact_delta if provided
3. For removals, base delta on impact_score (higher impact = more negative delta)
4. Add quality_delta field to each change
5. Return all changes with quality_delta added

OUTPUT FORMAT:
Return a JSON object with this structure:
{{
  "changes_with_delta": [
    {{
      "original_text": "...",  # (for rewrites)
      "rewritten_text": "...",  # (for rewrites)
      "text_to_remove": "...",  # (for removals)
      "impact_score": 0.15,
      "length_reduction": 33,
      "rationale": "...",
      "quality_delta": -0.05  # NEWLY ADDED
    }},
    ...
  ]
}}

IMPORTANT:
- Preserve all original fields from input changes
- Add quality_delta field to each change
- Be realistic about quality impact
- Negative deltas are normal for removals
- Return ONLY the JSON object, no markdown formatting or code blocks
"""

        return prompt

    def _get_input_summary(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create summary of input data for logging.

        Args:
            input_data: Input data to summarize

        Returns:
            Dictionary with input summary information
        """
        changes = input_data.get("changes", [])
        rewrite_count = sum(1 for c in changes if "rewritten_text" in c)
        removal_count = sum(1 for c in changes if "text_to_remove" in c)

        return {
            "total_changes": len(changes),
            "rewrite_count": rewrite_count,
            "removal_count": removal_count
        }

    def _get_output_summary(self, output_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create summary of output data for logging.

        Args:
            output_data: Delta calculation result

        Returns:
            Dictionary with output summary information
        """
        if isinstance(output_data, dict):
            if output_data.get("instruction") == "CALL_TASK_TOOL":
                return {
                    "type": "task_instruction",
                    "change_count": output_data.get("change_count", 0),
                    "status": "pending_execution"
                }

            changes = output_data.get("changes_with_delta", [])
            if changes:
                deltas = [c.get("quality_delta", 0.0) for c in changes if isinstance(c, dict)]
                avg_delta = sum(deltas) / len(deltas) if deltas else 0.0

                return {
                    "type": "changes_with_delta",
                    "change_count": len(changes),
                    "average_quality_delta": round(avg_delta, 3),
                    "positive_delta_count": sum(1 for d in deltas if d > 0),
                    "negative_delta_count": sum(1 for d in deltas if d < 0)
                }

        return {"type": "unknown", "data": str(output_data)[:100]}
