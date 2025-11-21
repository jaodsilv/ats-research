"""FactChecker agent for verifying factual accuracy against master resume.

This agent compares draft content against the master resume to identify any
fabricated or inaccurate information.
"""

import logging
from typing import Dict, Any, List

from ..base_agent import BaseAgent


class FactChecker(BaseAgent[Dict[str, Any], Dict[str, Any]]):
    """Agent that verifies factual accuracy of drafts against master resume.

    This agent uses Claude Code's Task tool to perform detailed fact-checking,
    comparing every claim in the draft against the master resume to detect
    any fabrications, exaggerations, or inaccuracies.

    Input Format:
        Dict with keys:
        {
            "draft": str,           # Draft resume/cover letter to check
            "master_resume": str    # Master resume (source of truth)
        }

    Output Format:
        Dict with keys:
        {
            "has_false_facts": bool,              # Whether false facts were found
            "false_facts": List[dict],            # List of false fact details
            "verification_notes": str             # Summary of verification
        }

        Each item in false_facts:
        {
            "claim": str,                         # The false claim from draft
            "issue": str,                         # What's wrong with it
            "correction": str                     # How to fix it (if applicable)
        }

    Example:
        >>> state_mgr = StateManager(Path("./run_001"))
        >>> agent = FactChecker(state_mgr, "fact_checking")
        >>> input_data = {
        ...     "draft": "Led team of 20 engineers...",
        ...     "master_resume": "Mentored 3 junior developers..."
        ... }
        >>> result = await agent.run(input_data)
        >>> if result["has_false_facts"]:
        ...     print("False facts detected!")
    """

    @property
    def agent_name(self) -> str:
        """Unique identifier for this agent type.

        Returns:
            Agent name string
        """
        return "fact_checker"

    @property
    def agent_type(self) -> str:
        """Claude Code subagent type to use for this agent.

        Returns:
            Subagent type string
        """
        return "general-purpose"

    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input contains required fields.

        Checks that:
        1. Input is a dictionary
        2. Required keys exist: draft, master_resume
        3. Both are non-empty strings

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
        required_keys = ["draft", "master_resume"]
        missing_keys = [k for k in required_keys if k not in input_data]
        if missing_keys:
            self.logger.error(f"Missing required keys: {missing_keys}")
            return False

        # Validate draft
        draft = input_data.get("draft", "")
        if not isinstance(draft, str) or len(draft.strip()) < 10:
            self.logger.error("draft must be non-empty string (min 10 chars)")
            return False

        # Validate master resume
        master_resume = input_data.get("master_resume", "")
        if not isinstance(master_resume, str) or len(master_resume.strip()) < 50:
            self.logger.error("master_resume must be non-empty string (min 50 chars)")
            return False

        self.logger.info(
            f"Input validation passed: draft={len(draft)} chars, master={len(master_resume)} chars"
        )
        return True

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform fact-checking using Claude Code Task tool.

        Args:
            input_data: Validated input data with draft and master resume

        Returns:
            Dict with task instruction for fact-checking

        Raises:
            RuntimeError: If fact-checking fails
        """
        draft = input_data["draft"]
        master_resume = input_data["master_resume"]

        self.logger.info(f"Fact-checking draft ({len(draft)} chars) against master resume")

        # Build prompt for Task tool
        prompt = self._build_fact_check_prompt(draft, master_resume)

        # Task tool invocation structure
        task_instruction = {
            "instruction": "CALL_TASK_TOOL",
            "agent_type": self.agent_type,
            "prompt": prompt,
            "draft_length": len(draft),
            "master_length": len(master_resume)
        }

        self.logger.info("Generated fact-checking instruction")

        return task_instruction

    async def format_output(self, raw_output: Any) -> Dict[str, Any]:
        """Format the raw fact-check output into final structure.

        Args:
            raw_output: Raw output from execute() or Task tool

        Returns:
            Dict with fact-checking results
        """
        # If this is a task instruction (pre-execution), return as-is
        if isinstance(raw_output, dict) and raw_output.get("instruction") == "CALL_TASK_TOOL":
            self.logger.debug("Output is task instruction (pre-execution), passing through")
            return raw_output

        # Ensure we have the expected structure
        if isinstance(raw_output, dict):
            formatted = {
                "has_false_facts": raw_output.get("has_false_facts", False),
                "false_facts": raw_output.get("false_facts", []),
                "verification_notes": raw_output.get("verification_notes", "")
            }
        else:
            # Fallback if output is not structured as expected
            self.logger.warning("Unexpected output format, using safe defaults")
            formatted = {
                "has_false_facts": False,
                "false_facts": [],
                "verification_notes": str(raw_output)
            }

        # Ensure false_facts is a list
        if not isinstance(formatted["false_facts"], list):
            formatted["false_facts"] = []

        # Validate each false fact entry
        validated_facts = []
        for fact in formatted["false_facts"]:
            if isinstance(fact, dict):
                validated_fact = {
                    "claim": fact.get("claim", ""),
                    "issue": fact.get("issue", ""),
                    "correction": fact.get("correction", "")
                }
                validated_facts.append(validated_fact)

        formatted["false_facts"] = validated_facts

        # Ensure has_false_facts is consistent with list
        if formatted["false_facts"]:
            formatted["has_false_facts"] = True
        else:
            formatted["has_false_facts"] = False

        self.logger.info(
            f"Fact-check complete: {len(formatted['false_facts'])} false facts found"
        )

        return formatted

    def _build_fact_check_prompt(self, draft: str, master_resume: str) -> str:
        """Build prompt for Task tool to perform fact-checking.

        Args:
            draft: Draft content to verify
            master_resume: Master resume (source of truth)

        Returns:
            Formatted prompt string for Task tool
        """
        prompt = f"""Perform rigorous fact-checking on the draft document against the master resume.

MASTER RESUME (SOURCE OF TRUTH):
{master_resume}

DRAFT TO VERIFY:
{draft}

INSTRUCTIONS:
Carefully compare every claim, achievement, skill, and detail in the DRAFT against the MASTER RESUME.

Identify any discrepancies including:
1. **Fabricated Information**: Claims not present in master resume
2. **Exaggerations**: Numbers, titles, or scope inflated beyond master resume
3. **Inaccurate Dates**: Timeline inconsistencies
4. **Wrong Technologies**: Skills or tools not mentioned in master resume
5. **Misrepresented Roles**: Job titles or responsibilities changed
6. **False Achievements**: Accomplishments not backed by master resume

For each false fact found, provide:
- claim: The exact text from the draft that is false
- issue: What's wrong with it (fabrication, exaggeration, etc.)
- correction: How to fix it based on master resume (if applicable)

Return a JSON object with this structure:
{{
  "has_false_facts": true/false,
  "false_facts": [
    {{
      "claim": "exact quote from draft",
      "issue": "description of the problem",
      "correction": "suggested fix based on master resume"
    }}
  ],
  "verification_notes": "Summary of verification process and findings"
}}

IMPORTANT:
- Be thorough and strict in verification
- Even minor exaggerations should be flagged
- Only information explicitly stated or strongly implied in master resume is acceptable
- If the draft is accurate, return has_false_facts: false with empty false_facts array
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
        return {
            "draft_length": len(input_data.get("draft", "")),
            "master_resume_length": len(input_data.get("master_resume", "")),
            "draft_word_count": len(input_data.get("draft", "").split()),
            "master_word_count": len(input_data.get("master_resume", "").split())
        }

    def _get_output_summary(self, output_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create summary of output data for logging.

        Args:
            output_data: Fact-check results

        Returns:
            Dictionary with output summary information
        """
        if output_data.get("instruction") == "CALL_TASK_TOOL":
            return {
                "type": "task_instruction",
                "draft_length": output_data.get("draft_length", 0),
                "master_length": output_data.get("master_length", 0),
                "status": "pending_execution"
            }

        return {
            "type": "fact_check_result",
            "has_false_facts": output_data.get("has_false_facts", False),
            "false_fact_count": len(output_data.get("false_facts", [])),
            "verification_notes_length": len(output_data.get("verification_notes", ""))
        }
