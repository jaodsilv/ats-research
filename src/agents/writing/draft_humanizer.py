"""DraftHumanizer agent for rewriting AI-detected content to sound more human.

This agent takes drafts that appear AI-generated and rewrites them to sound more
natural and human-like while preserving the core content and quality.
"""

import logging
from typing import Dict, Any, List

from ..base_agent import BaseAgent


class DraftHumanizer(BaseAgent[Dict[str, Any], str]):
    """Agent that humanizes AI-generated drafts.

    This agent uses Claude Code's Task tool to rewrite drafts that appear
    AI-generated, making them sound more natural and human-like through:
    - Varying sentence structure and length
    - Adding personality and conversational elements
    - Using contractions where appropriate
    - Reducing excessive formality
    - Adding specific details and examples

    Input Format:
        Dict with keys:
        {
            "draft": str,                   # Draft text to humanize
            "ai_indicators": List[str]      # AI patterns to address
        }

    Output Format:
        str - The humanized draft text

    Example:
        >>> state_mgr = StateManager(Path("./run_001"))
        >>> agent = DraftHumanizer(state_mgr, "draft_writing")
        >>> input_data = {
        ...     "draft": "I am writing to express my enthusiastic interest...",
        ...     "ai_indicators": ["Overly formal language", "Generic phrases"]
        ... }
        >>> humanized = await agent.run(input_data)
        >>> print(humanized)
    """

    @property
    def agent_name(self) -> str:
        """Unique identifier for this agent type.

        Returns:
            Agent name string
        """
        return "draft_humanizer"

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
        2. Required keys exist: draft, ai_indicators
        3. Draft is a non-empty string
        4. ai_indicators is a list

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
        required_keys = ["draft", "ai_indicators"]
        missing_keys = [k for k in required_keys if k not in input_data]
        if missing_keys:
            self.logger.error(f"Missing required keys: {missing_keys}")
            return False

        # Validate draft
        draft = input_data.get("draft", "")
        if not isinstance(draft, str) or len(draft.strip()) < 10:
            self.logger.error("draft must be non-empty string (min 10 chars)")
            return False

        # Validate ai_indicators
        ai_indicators = input_data.get("ai_indicators", [])
        if not isinstance(ai_indicators, list):
            self.logger.error(f"ai_indicators must be list, got {type(ai_indicators)}")
            return False

        self.logger.info(
            f"Input validation passed: draft={len(draft)} chars, "
            f"indicators={len(ai_indicators)}"
        )
        return True

    async def execute(self, input_data: Dict[str, Any]) -> str:
        """Perform draft humanization using Claude Code Task tool.

        Args:
            input_data: Validated input data with draft and indicators

        Returns:
            Task instruction dict for humanization

        Raises:
            RuntimeError: If humanization fails
        """
        draft = input_data["draft"]
        ai_indicators = input_data["ai_indicators"]

        self.logger.info(
            f"Humanizing draft ({len(draft)} chars) with "
            f"{len(ai_indicators)} indicators to address"
        )

        # Build prompt for Task tool
        prompt = self._build_humanization_prompt(draft, ai_indicators)

        # Task tool invocation structure
        task_instruction = {
            "instruction": "CALL_TASK_TOOL",
            "agent_type": self.agent_type,
            "prompt": prompt,
            "draft_length": len(draft),
            "indicator_count": len(ai_indicators)
        }

        self.logger.info("Generated humanization instruction")

        return task_instruction

    async def format_output(self, raw_output: Any) -> str:
        """Format the raw humanization output into final string.

        Args:
            raw_output: Raw output from execute() or Task tool

        Returns:
            Humanized draft as string
        """
        # If this is a task instruction (pre-execution), return as-is
        if isinstance(raw_output, dict) and raw_output.get("instruction") == "CALL_TASK_TOOL":
            self.logger.debug("Output is task instruction (pre-execution), passing through")
            return raw_output

        # Convert to string
        if isinstance(raw_output, str):
            humanized_draft = raw_output.strip()
        elif isinstance(raw_output, dict):
            # If output is dict, try to extract the humanized text
            humanized_draft = raw_output.get("humanized_draft", str(raw_output))
        else:
            humanized_draft = str(raw_output)

        # Validate output is not empty
        if not humanized_draft or len(humanized_draft.strip()) < 10:
            self.logger.warning("Humanized output appears empty or too short")
            humanized_draft = str(raw_output)

        self.logger.info(f"Humanization complete: output={len(humanized_draft)} chars")

        return humanized_draft

    def _build_humanization_prompt(self, draft: str, ai_indicators: List[str]) -> str:
        """Build prompt for Task tool to perform humanization.

        Args:
            draft: Draft content to humanize
            ai_indicators: List of AI patterns to address

        Returns:
            Formatted prompt string for Task tool
        """
        indicators_text = "\n".join(f"- {indicator}" for indicator in ai_indicators)

        prompt = f"""Rewrite this draft to sound more natural and human-like while preserving its core content and quality.

ORIGINAL DRAFT:
{draft}

AI PATTERNS IDENTIFIED:
{indicators_text if ai_indicators else "- General AI writing patterns detected"}

HUMANIZATION INSTRUCTIONS:

1. **Vary Sentence Structure**:
   - Mix short and long sentences
   - Use different sentence patterns (simple, compound, complex)
   - Break up overly long or complex sentences
   - Add natural rhythm and flow

2. **Add Personality**:
   - Include conversational elements where appropriate
   - Use active voice more frequently
   - Add personal touches without being unprofessional
   - Make it sound like a real person wrote it

3. **Use Contractions**:
   - Replace formal constructions with contractions (I am → I'm, I have → I've)
   - Use contractions naturally, not everywhere
   - Maintain professionalism while being conversational

4. **Reduce Formality**:
   - Replace overly formal words with simpler alternatives
   - Cut unnecessary transition words (furthermore, moreover, etc.)
   - Simplify complex phrasing
   - Make language more direct and accessible

5. **Add Specific Details**:
   - Where generic statements exist, make them more concrete
   - Add specific examples or context where appropriate
   - Use industry-specific terminology naturally
   - Include relevant details that show genuine understanding

QUALITY PRESERVATION:
- Maintain all factual information from the original
- Keep the same overall structure and key points
- Preserve the professional tone appropriate for the context
- Ensure grammar and spelling remain correct
- Do not remove important details or qualifications

OUTPUT FORMAT:
Return ONLY the rewritten draft text. Do not include:
- Explanations or meta-commentary
- Markdown formatting or code blocks
- Section headers or labels
- Comparison with the original

IMPORTANT:
- The goal is to make it sound like a real person wrote it
- Balance natural language with professionalism
- Don't oversimplify or dumb down the content
- Maintain the draft's purpose and effectiveness
- The result should pass as genuinely human-written
"""

        return prompt

    def _serialize_output(self, output_data: str) -> Any:
        """Convert output data to JSON-serializable format.

        Args:
            output_data: Humanized draft string

        Returns:
            JSON-serializable representation
        """
        # For string output, return as-is (strings are JSON-serializable)
        return output_data

    def _get_input_summary(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create summary of input data for logging.

        Args:
            input_data: Input data to summarize

        Returns:
            Dictionary with input summary information
        """
        return {
            "draft_length": len(input_data.get("draft", "")),
            "draft_word_count": len(input_data.get("draft", "").split()),
            "indicator_count": len(input_data.get("ai_indicators", []))
        }

    def _get_output_summary(self, output_data: str | Dict[str, Any]) -> Dict[str, Any]:
        """Create summary of output data for logging.

        Args:
            output_data: Humanized draft or task instruction

        Returns:
            Dictionary with output summary information
        """
        if isinstance(output_data, dict) and output_data.get("instruction") == "CALL_TASK_TOOL":
            return {
                "type": "task_instruction",
                "draft_length": output_data.get("draft_length", 0),
                "indicator_count": output_data.get("indicator_count", 0),
                "status": "pending_execution"
            }

        if isinstance(output_data, str):
            return {
                "type": "humanized_draft",
                "output_length": len(output_data),
                "output_word_count": len(output_data.split())
            }

        return {
            "type": "unknown",
            "output_type": type(output_data).__name__
        }
