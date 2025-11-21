"""ChangeExecutor agent for applying selected changes to the draft.

This agent applies a single change (rewrite or removal) to the draft,
producing a modified version.
"""

import logging
from typing import Dict, Any

from ..base_agent import BaseAgent


class ChangeExecutor(BaseAgent[Dict[str, Any], str]):
    """Agent that executes a single change on the draft.

    This agent applies one change (rewrite or removal) to the draft document,
    producing an updated draft with the change applied.

    Input Format:
        Dict with keys:
        {
            "draft": str,                    # Current draft content
            "change": dict                   # Single change to apply
        }

        Change dict contains either:
        - Rewrite: original_text, rewritten_text, ...
        - Removal: text_to_remove, ...

    Output Format:
        str: Modified draft with change applied

    Example:
        >>> state_mgr = StateManager(Path("./run_001"))
        >>> agent = ChangeExecutor(state_mgr, "pruning")
        >>> input_data = {
        ...     "draft": "# John Doe\\nResponsible for leading team...",
        ...     "change": {
        ...         "original_text": "Responsible for leading",
        ...         "rewritten_text": "Led",
        ...         "quality_delta": 0.05
        ...     }
        ... }
        >>> modified_draft = await agent.run(input_data)
    """

    @property
    def agent_name(self) -> str:
        """Unique identifier for this agent type.

        Returns:
            Agent name string
        """
        return "change_executor"

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
        2. Required keys exist: draft, change
        3. Draft is non-empty string
        4. Change is a dict with either rewrite or removal fields

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
        required_keys = ["draft", "change"]
        missing_keys = [k for k in required_keys if k not in input_data]
        if missing_keys:
            self.logger.error(f"Missing required keys: {missing_keys}")
            return False

        # Validate draft
        draft = input_data.get("draft", "")
        if not isinstance(draft, str) or len(draft.strip()) < 10:
            self.logger.error("draft must be non-empty string (min 10 chars)")
            return False

        # Validate change
        change = input_data.get("change", {})
        if not isinstance(change, dict):
            self.logger.error("change must be a dict")
            return False

        # Check if it's a rewrite or removal
        is_rewrite = "original_text" in change and "rewritten_text" in change
        is_removal = "text_to_remove" in change

        if not (is_rewrite or is_removal):
            self.logger.error(
                "change must have either (original_text, rewritten_text) or (text_to_remove)"
            )
            return False

        self.logger.info(
            f"Input validation passed: {'rewrite' if is_rewrite else 'removal'} change"
        )
        return True

    async def execute(self, input_data: Dict[str, Any]) -> str:
        """Apply the change to the draft.

        This is a simple string replacement operation, so we don't need
        the Task tool for this agent.

        Args:
            input_data: Validated input data with draft and change

        Returns:
            Modified draft string

        Raises:
            RuntimeError: If change application fails
        """
        draft = input_data["draft"]
        change = input_data["change"]

        # Determine change type
        is_rewrite = "original_text" in change and "rewritten_text" in change
        is_removal = "text_to_remove" in change

        if is_rewrite:
            original = change["original_text"]
            rewritten = change["rewritten_text"]

            self.logger.info(
                f"Applying rewrite: '{original[:50]}...' -> '{rewritten[:50]}...'"
            )

            # Check if original text exists in draft
            if original not in draft:
                self.logger.warning(
                    f"Original text not found in draft: '{original[:50]}...'"
                )
                # Return draft unchanged
                return draft

            # Apply rewrite (replace first occurrence)
            modified_draft = draft.replace(original, rewritten, 1)

            self.logger.info(
                f"Rewrite applied: draft length {len(draft)} -> {len(modified_draft)}"
            )

            return modified_draft

        elif is_removal:
            text_to_remove = change["text_to_remove"]

            self.logger.info(f"Applying removal: '{text_to_remove[:50]}...'")

            # Check if text exists in draft
            if text_to_remove not in draft:
                self.logger.warning(
                    f"Text to remove not found in draft: '{text_to_remove[:50]}...'"
                )
                # Return draft unchanged
                return draft

            # Apply removal (remove first occurrence)
            modified_draft = draft.replace(text_to_remove, "", 1)

            # Clean up any resulting double newlines or extra whitespace
            modified_draft = self._clean_whitespace(modified_draft)

            self.logger.info(
                f"Removal applied: draft length {len(draft)} -> {len(modified_draft)}"
            )

            return modified_draft

        else:
            # Should not reach here due to validation
            raise RuntimeError("Invalid change type")

    def _clean_whitespace(self, text: str) -> str:
        """Clean up excessive whitespace after removal.

        Args:
            text: Text to clean

        Returns:
            Cleaned text
        """
        # Replace multiple consecutive newlines with max 2
        while "\n\n\n" in text:
            text = text.replace("\n\n\n", "\n\n")

        # Remove trailing spaces from lines
        lines = text.split("\n")
        lines = [line.rstrip() for line in lines]
        text = "\n".join(lines)

        return text

    async def format_output(self, raw_output: Any) -> str:
        """Format the raw output (already a string from execute).

        Args:
            raw_output: Raw output from execute()

        Returns:
            Modified draft string
        """
        # Output is already a string from execute()
        if isinstance(raw_output, str):
            return raw_output
        else:
            # Shouldn't happen, but handle gracefully
            self.logger.warning(f"Unexpected output type: {type(raw_output)}")
            return str(raw_output)

    def _get_input_summary(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create summary of input data for logging.

        Args:
            input_data: Input data to summarize

        Returns:
            Dictionary with input summary information
        """
        change = input_data.get("change", {})
        is_rewrite = "original_text" in change and "rewritten_text" in change

        return {
            "draft_length": len(input_data.get("draft", "")),
            "change_type": "rewrite" if is_rewrite else "removal",
            "length_reduction": change.get("length_reduction", 0),
            "quality_delta": change.get("quality_delta", 0.0)
        }

    def _get_output_summary(self, output_data: str) -> Dict[str, Any]:
        """Create summary of output data for logging.

        Args:
            output_data: Modified draft

        Returns:
            Dictionary with output summary information
        """
        return {
            "type": "modified_draft",
            "draft_length": len(output_data) if isinstance(output_data, str) else 0,
            "word_count": len(output_data.split()) if isinstance(output_data, str) else 0
        }
