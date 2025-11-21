"""RevisedDraftWriter agent for rewriting drafts to fix false facts.

This agent rewrites drafts to correct any factual inaccuracies identified
by the FactChecker while maintaining document quality and structure.
"""

import logging
from typing import Dict, Any

from ..base_agent import BaseAgent


class RevisedDraftWriter(BaseAgent[Dict[str, Any], str]):
    """Agent that rewrites drafts to correct factual inaccuracies.

    This agent uses Claude Code's Task tool to intelligently rewrite drafts,
    removing or correcting false facts while preserving the overall structure,
    tone, and quality of the document.

    Input Format:
        Dict with keys:
        {
            "draft": str,                    # Original draft with false facts
            "fact_check_results": dict,      # Results from FactChecker
            "master_resume": str             # Master resume (source of truth)
        }

    Output Format:
        str: Revised draft with corrections applied

    Example:
        >>> state_mgr = StateManager(Path("./run_001"))
        >>> agent = RevisedDraftWriter(state_mgr, "fact_checking")
        >>> input_data = {
        ...     "draft": "Led team of 20 engineers...",
        ...     "fact_check_results": {
        ...         "has_false_facts": True,
        ...         "false_facts": [{"claim": "team of 20", "issue": "exaggeration", ...}]
        ...     },
        ...     "master_resume": "Mentored 3 junior developers..."
        ... }
        >>> revised = await agent.run(input_data)
    """

    @property
    def agent_name(self) -> str:
        """Unique identifier for this agent type.

        Returns:
            Agent name string
        """
        return "revised_draft_writer"

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
        2. Required keys exist: draft, fact_check_results, master_resume
        3. All are valid types

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
        required_keys = ["draft", "fact_check_results", "master_resume"]
        missing_keys = [k for k in required_keys if k not in input_data]
        if missing_keys:
            self.logger.error(f"Missing required keys: {missing_keys}")
            return False

        # Validate draft
        draft = input_data.get("draft", "")
        if not isinstance(draft, str) or len(draft.strip()) < 10:
            self.logger.error("draft must be non-empty string (min 10 chars)")
            return False

        # Validate fact_check_results
        fact_check = input_data.get("fact_check_results", {})
        if not isinstance(fact_check, dict):
            self.logger.error("fact_check_results must be a dict")
            return False

        # Validate master resume
        master_resume = input_data.get("master_resume", "")
        if not isinstance(master_resume, str) or len(master_resume.strip()) < 50:
            self.logger.error("master_resume must be non-empty string (min 50 chars)")
            return False

        self.logger.info("Input validation passed")
        return True

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Rewrite draft to fix false facts using Claude Code Task tool.

        Args:
            input_data: Validated input data with draft, fact_check, and master

        Returns:
            Dict with task instruction for revision

        Raises:
            RuntimeError: If revision fails
        """
        draft = input_data["draft"]
        fact_check = input_data["fact_check_results"]
        master_resume = input_data["master_resume"]

        false_facts = fact_check.get("false_facts", [])

        self.logger.info(f"Revising draft to fix {len(false_facts)} false facts")

        # Build prompt for Task tool
        prompt = self._build_revision_prompt(draft, fact_check, master_resume)

        # Task tool invocation structure
        task_instruction = {
            "instruction": "CALL_TASK_TOOL",
            "agent_type": self.agent_type,
            "prompt": prompt,
            "false_fact_count": len(false_facts),
            "draft_length": len(draft)
        }

        self.logger.info(f"Generated revision instruction for {len(false_facts)} issues")

        return task_instruction

    async def format_output(self, raw_output: Any) -> str:
        """Format the raw revision output into final string.

        Args:
            raw_output: Raw output from execute() or Task tool

        Returns:
            Revised draft content as string
        """
        # If this is a task instruction (pre-execution), return as-is
        if isinstance(raw_output, dict) and raw_output.get("instruction") == "CALL_TASK_TOOL":
            self.logger.debug("Output is task instruction (pre-execution), passing through")
            return raw_output

        # Otherwise, ensure we have a string
        if isinstance(raw_output, str):
            revised = raw_output.strip()
        elif isinstance(raw_output, dict) and "revised_draft" in raw_output:
            revised = raw_output["revised_draft"].strip()
        else:
            revised = str(raw_output).strip()

        if len(revised) < 50:
            self.logger.warning(f"Revised draft seems too short: {len(revised)} characters")

        self.logger.info(f"Formatted revised draft: {len(revised)} characters")

        return revised

    def _build_revision_prompt(
        self,
        draft: str,
        fact_check: Dict[str, Any],
        master_resume: str
    ) -> str:
        """Build prompt for Task tool to revise draft.

        Args:
            draft: Original draft with false facts
            fact_check: Fact-checking results
            master_resume: Master resume (source of truth)

        Returns:
            Formatted prompt string for Task tool
        """
        false_facts = fact_check.get("false_facts", [])
        verification_notes = fact_check.get("verification_notes", "")

        # Format false facts for prompt
        false_facts_text = ""
        for i, fact in enumerate(false_facts, 1):
            false_facts_text += f"\n{i}. CLAIM: {fact.get('claim', '')}\n"
            false_facts_text += f"   ISSUE: {fact.get('issue', '')}\n"
            false_facts_text += f"   CORRECTION: {fact.get('correction', '')}\n"

        prompt = f"""Rewrite the draft to fix all identified factual inaccuracies.

MASTER RESUME (SOURCE OF TRUTH):
{master_resume}

ORIGINAL DRAFT (WITH FALSE FACTS):
{draft}

IDENTIFIED FALSE FACTS:
{false_facts_text}

VERIFICATION NOTES:
{verification_notes}

INSTRUCTIONS:
1. Rewrite the draft to correct all false facts listed above
2. Use ONLY factual information from the master resume
3. Maintain the overall structure and tone of the original draft
4. Preserve high-quality writing, action verbs, and strong phrasing
5. Keep all accurate content unchanged
6. Ensure corrections flow naturally within the document
7. Do not introduce new false facts or exaggerations
8. Maintain similar length and detail level to original draft

IMPORTANT:
- The revised draft should read naturally, not appear patched or choppy
- Preserve the document's professional tone and formatting
- Only change what needs to be changed to fix the false facts
- All claims must be verifiable against the master resume

Return ONLY the revised draft in the same format as the original (Markdown).
Do not include explanations, comments, or metadata.
"""

        return prompt

    def _get_input_summary(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create summary of input data for logging.

        Args:
            input_data: Input data to summarize

        Returns:
            Dictionary with input summary information
        """
        fact_check = input_data.get("fact_check_results", {})
        false_facts = fact_check.get("false_facts", [])

        return {
            "draft_length": len(input_data.get("draft", "")),
            "master_resume_length": len(input_data.get("master_resume", "")),
            "false_fact_count": len(false_facts),
            "has_false_facts": fact_check.get("has_false_facts", False)
        }

    def _get_output_summary(self, output_data: str) -> Dict[str, Any]:
        """Create summary of output data for logging.

        Args:
            output_data: Revised draft content

        Returns:
            Dictionary with output summary information
        """
        if isinstance(output_data, dict) and output_data.get("instruction") == "CALL_TASK_TOOL":
            return {
                "type": "task_instruction",
                "false_fact_count": output_data.get("false_fact_count", 0),
                "draft_length": output_data.get("draft_length", 0),
                "status": "pending_execution"
            }

        draft_length = len(output_data) if isinstance(output_data, str) else 0
        word_count = len(output_data.split()) if isinstance(output_data, str) else 0

        return {
            "type": "revised_draft",
            "character_count": draft_length,
            "word_count": word_count,
            "line_count": output_data.count('\n') if isinstance(output_data, str) else 0
        }
