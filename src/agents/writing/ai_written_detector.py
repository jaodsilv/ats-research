"""AIWrittenDetector agent for detecting AI-generated writing patterns.

This agent analyzes draft content to identify common AI writing patterns such as
repetitive phrasing, unnatural formality, generic language, and lack of personality.
"""

import logging
from typing import Dict, Any, List

from ..base_agent import BaseAgent


class AIWrittenDetector(BaseAgent[Dict[str, Any], Dict[str, Any]]):
    """Agent that detects AI-generated writing patterns in drafts.

    This agent uses Claude Code's Task tool to analyze writing style and identify
    indicators that suggest content was AI-generated, including:
    - Repetitive phrasing and sentence structures
    - Unnatural formality or overly polished language
    - Generic language lacking specific details
    - Absence of personal voice or personality

    Input Format:
        Dict with keys:
        {
            "draft": str    # Draft text to analyze for AI patterns
        }

    Output Format:
        Dict with keys:
        {
            "appears_ai_written": bool,       # Whether draft appears AI-generated
            "confidence_score": float,        # Confidence level (0.0-1.0)
            "indicators": List[str],          # List of AI writing patterns found
            "analysis": str                   # Detailed explanation of findings
        }

    Example:
        >>> state_mgr = StateManager(Path("./run_001"))
        >>> agent = AIWrittenDetector(state_mgr, "draft_writing")
        >>> input_data = {
        ...     "draft": "I am writing to express my enthusiastic interest..."
        ... }
        >>> result = await agent.run(input_data)
        >>> if result["appears_ai_written"]:
        ...     print(f"AI detected with {result['confidence_score']:.1%} confidence")
    """

    @property
    def agent_name(self) -> str:
        """Unique identifier for this agent type.

        Returns:
            Agent name string
        """
        return "ai_written_detector"

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
        2. Required key exists: draft
        3. Draft is a non-empty string

        Args:
            input_data: Input data to validate

        Returns:
            True if input is valid, False otherwise
        """
        # Check type
        if not isinstance(input_data, dict):
            self.logger.error(f"Input must be dict, got {type(input_data)}")
            return False

        # Check required key
        if "draft" not in input_data:
            self.logger.error("Missing required key: draft")
            return False

        # Validate draft
        draft = input_data.get("draft", "")
        if not isinstance(draft, str) or len(draft.strip()) < 10:
            self.logger.error("draft must be non-empty string (min 10 chars)")
            return False

        self.logger.info(f"Input validation passed: draft={len(draft)} chars")
        return True

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform AI detection using Claude Code Task tool.

        Args:
            input_data: Validated input data with draft

        Returns:
            Dict with task instruction for AI detection

        Raises:
            RuntimeError: If AI detection fails
        """
        draft = input_data["draft"]

        self.logger.info(f"Analyzing draft for AI writing patterns ({len(draft)} chars)")

        # Build prompt for Task tool
        prompt = self._build_ai_detection_prompt(draft)

        # Task tool invocation structure
        task_instruction = {
            "instruction": "CALL_TASK_TOOL",
            "agent_type": self.agent_type,
            "prompt": prompt,
            "draft_length": len(draft)
        }

        self.logger.info("Generated AI detection instruction")

        return task_instruction

    async def format_output(self, raw_output: Any) -> Dict[str, Any]:
        """Format the raw AI detection output into final structure.

        Args:
            raw_output: Raw output from execute() or Task tool

        Returns:
            Dict with AI detection results
        """
        # If this is a task instruction (pre-execution), return as-is
        if isinstance(raw_output, dict) and raw_output.get("instruction") == "CALL_TASK_TOOL":
            self.logger.debug("Output is task instruction (pre-execution), passing through")
            return raw_output

        # Ensure we have the expected structure
        if isinstance(raw_output, dict):
            formatted = {
                "appears_ai_written": raw_output.get("appears_ai_written", False),
                "confidence_score": raw_output.get("confidence_score", 0.0),
                "indicators": raw_output.get("indicators", []),
                "analysis": raw_output.get("analysis", "")
            }
        else:
            # Fallback if output is not structured as expected
            self.logger.warning("Unexpected output format, using safe defaults")
            formatted = {
                "appears_ai_written": False,
                "confidence_score": 0.0,
                "indicators": [],
                "analysis": str(raw_output)
            }

        # Ensure indicators is a list of strings
        if not isinstance(formatted["indicators"], list):
            formatted["indicators"] = []
        else:
            formatted["indicators"] = [str(ind) for ind in formatted["indicators"]]

        # Ensure confidence_score is a float between 0 and 1
        try:
            confidence = float(formatted["confidence_score"])
            formatted["confidence_score"] = max(0.0, min(1.0, confidence))
        except (TypeError, ValueError):
            self.logger.warning("Invalid confidence_score, defaulting to 0.0")
            formatted["confidence_score"] = 0.0

        # Ensure appears_ai_written is consistent with confidence
        if formatted["confidence_score"] >= 0.7:
            formatted["appears_ai_written"] = True
        elif formatted["confidence_score"] < 0.3:
            formatted["appears_ai_written"] = False

        self.logger.info(
            f"AI detection complete: appears_ai_written={formatted['appears_ai_written']}, "
            f"confidence={formatted['confidence_score']:.2f}, "
            f"indicators={len(formatted['indicators'])}"
        )

        return formatted

    def _build_ai_detection_prompt(self, draft: str) -> str:
        """Build prompt for Task tool to perform AI detection.

        Args:
            draft: Draft content to analyze

        Returns:
            Formatted prompt string for Task tool
        """
        prompt = f"""Analyze this draft document to detect AI-generated writing patterns.

DRAFT TO ANALYZE:
{draft}

INSTRUCTIONS:
Carefully examine the draft for common AI writing indicators:

1. **Repetitive Phrasing**:
   - Overuse of transition words (furthermore, moreover, additionally)
   - Repeated sentence structures or patterns
   - Stock phrases repeated multiple times

2. **Unnatural Formality**:
   - Overly polished or academic tone
   - Excessive use of formal connectors
   - Lack of contractions where natural
   - Unnatural word choices for the context

3. **Generic Language**:
   - Vague or non-specific statements
   - Lack of concrete examples or details
   - Generic adjectives (excellent, outstanding, remarkable)
   - Absence of industry-specific terminology

4. **Lack of Personality**:
   - Missing personal voice or unique perspective
   - No conversational elements or natural flow
   - Absence of human imperfections (all sentences perfect)
   - No personal anecdotes or specific experiences

For each indicator found, note the specific pattern and provide examples from the text.

Return a JSON object with this structure:
{{
  "appears_ai_written": true/false,
  "confidence_score": 0.0-1.0,
  "indicators": [
    "Specific indicator 1: example from text",
    "Specific indicator 2: example from text"
  ],
  "analysis": "Detailed explanation of findings, including reasoning for confidence score and overall assessment"
}}

CONFIDENCE SCORING GUIDELINES:
- 0.9-1.0: Very strong AI indicators, multiple patterns across categories
- 0.7-0.89: Strong AI indicators, clear patterns in 2+ categories
- 0.5-0.69: Moderate AI indicators, some patterns detected
- 0.3-0.49: Weak AI indicators, borderline patterns
- 0.0-0.29: Minimal AI indicators, appears human-written

IMPORTANT:
- Be thorough in analysis
- Provide specific quotes from the draft as evidence
- Consider context (formal business writing may naturally be more polished)
- Balance multiple factors in determining confidence score
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
            "draft_word_count": len(input_data.get("draft", "").split()),
        }

    def _get_output_summary(self, output_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create summary of output data for logging.

        Args:
            output_data: AI detection results

        Returns:
            Dictionary with output summary information
        """
        if output_data.get("instruction") == "CALL_TASK_TOOL":
            return {
                "type": "task_instruction",
                "draft_length": output_data.get("draft_length", 0),
                "status": "pending_execution"
            }

        return {
            "type": "ai_detection_result",
            "appears_ai_written": output_data.get("appears_ai_written", False),
            "confidence_score": output_data.get("confidence_score", 0.0),
            "indicator_count": len(output_data.get("indicators", [])),
            "analysis_length": len(output_data.get("analysis", ""))
        }
