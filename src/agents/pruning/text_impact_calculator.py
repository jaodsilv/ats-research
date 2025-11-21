"""TextImpactCalculator agent for calculating impact scores of text segments.

This agent analyzes a draft and assigns impact scores to each text segment
(sentences, bullet points, sections) based on relevance to job description
and best practices.
"""

import logging
from typing import Dict, Any, List

from ..base_agent import BaseAgent


class TextImpactCalculator(BaseAgent[Dict[str, Any], Dict[str, Any]]):
    """Agent that calculates impact scores for text segments in a draft.

    This agent analyzes each segment of the draft (sections, paragraphs, bullet
    points, sentences) and assigns impact scores from 0.0 (low impact) to 1.0
    (high impact) based on relevance to job requirements and best practices.

    Input Format:
        Dict with keys:
        {
            "draft": str,                    # Draft content to analyze
            "parsed_jd": dict,               # Parsed job description
            "best_practices": str            # Best practices guidelines
        }

    Output Format:
        Dict with keys:
        {
            "text_segments": List[dict]      # List of segments with impact scores
        }

        Each segment dict contains:
        {
            "segment": str,                  # Text segment
            "impact_score": float,           # 0.0 to 1.0
            "segment_type": str,             # "section", "bullet", "sentence"
            "line_count": int                # Number of lines in segment
        }

    Example:
        >>> state_mgr = StateManager(Path("./run_001"))
        >>> agent = TextImpactCalculator(state_mgr, "pruning")
        >>> input_data = {
        ...     "draft": "# John Doe\\n...",
        ...     "parsed_jd": {"job_title": "Senior Engineer", ...},
        ...     "best_practices": "Use action verbs..."
        ... }
        >>> result = await agent.run(input_data)
        >>> segments = result["text_segments"]
    """

    @property
    def agent_name(self) -> str:
        """Unique identifier for this agent type.

        Returns:
            Agent name string
        """
        return "text_impact_calculator"

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
        2. Required keys exist: draft, parsed_jd
        3. Draft is non-empty string
        4. Parsed JD is a dict

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
        required_keys = ["draft", "parsed_jd"]
        missing_keys = [k for k in required_keys if k not in input_data]
        if missing_keys:
            self.logger.error(f"Missing required keys: {missing_keys}")
            return False

        # Validate draft
        draft = input_data.get("draft", "")
        if not isinstance(draft, str) or len(draft.strip()) < 10:
            self.logger.error("draft must be non-empty string (min 10 chars)")
            return False

        # Validate parsed JD
        parsed_jd = input_data.get("parsed_jd", {})
        if not isinstance(parsed_jd, dict):
            self.logger.error("parsed_jd must be a dict")
            return False

        self.logger.info("Input validation passed")
        return True

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate impact scores using Claude Code Task tool.

        Args:
            input_data: Validated input data with draft and context

        Returns:
            Dict with task instruction for impact calculation

        Raises:
            RuntimeError: If calculation fails
        """
        draft = input_data["draft"]
        parsed_jd = input_data["parsed_jd"]

        self.logger.info(f"Calculating impact scores for draft ({len(draft)} chars)")

        # Build prompt for Task tool
        prompt = self._build_impact_calc_prompt(input_data)

        # Task tool invocation structure
        task_instruction = {
            "instruction": "CALL_TASK_TOOL",
            "agent_type": self.agent_type,
            "prompt": prompt,
            "draft_length": len(draft),
            "job_title": parsed_jd.get("job_title", "unknown")
        }

        self.logger.info("Generated impact calculation instruction")

        return task_instruction

    async def format_output(self, raw_output: Any) -> Dict[str, Any]:
        """Format the raw output into structured segments with scores.

        Args:
            raw_output: Raw output from execute() or Task tool

        Returns:
            Dict with text_segments list
        """
        # If this is a task instruction (pre-execution), return as-is
        if isinstance(raw_output, dict) and raw_output.get("instruction") == "CALL_TASK_TOOL":
            self.logger.debug("Output is task instruction (pre-execution), passing through")
            return raw_output

        # Parse output into structured format
        if isinstance(raw_output, dict) and "text_segments" in raw_output:
            result = raw_output
        elif isinstance(raw_output, list):
            result = {"text_segments": raw_output}
        else:
            # Fallback
            self.logger.warning("Unexpected output format, using empty segments")
            result = {"text_segments": []}

        # Validate segments
        segments = result.get("text_segments", [])
        if not isinstance(segments, list):
            self.logger.error("text_segments must be a list")
            result["text_segments"] = []
        else:
            # Ensure each segment has required fields
            validated_segments = []
            for seg in segments:
                if isinstance(seg, dict):
                    validated_segments.append({
                        "segment": seg.get("segment", ""),
                        "impact_score": float(seg.get("impact_score", 0.0)),
                        "segment_type": seg.get("segment_type", "unknown"),
                        "line_count": int(seg.get("line_count", 1))
                    })
            result["text_segments"] = validated_segments

        self.logger.info(f"Formatted {len(result['text_segments'])} text segments")

        return result

    def _build_impact_calc_prompt(self, input_data: Dict[str, Any]) -> str:
        """Build prompt for Task tool to calculate impact scores.

        Args:
            input_data: Input data with draft and context

        Returns:
            Formatted prompt string for Task tool
        """
        draft = input_data["draft"]
        parsed_jd = input_data["parsed_jd"]
        best_practices = input_data.get("best_practices", "")

        job_title = parsed_jd.get("job_title", "Unknown Position")
        company = parsed_jd.get("company", "Unknown Company")

        prompt = f"""Analyze the draft document and calculate impact scores for each text segment.

JOB DETAILS:
- Title: {job_title}
- Company: {company}

DRAFT TO ANALYZE:
{draft}

PARSED JOB DESCRIPTION:
{self._format_jd_for_prompt(parsed_jd)}

"""

        if best_practices:
            prompt += f"""BEST PRACTICES:
{best_practices}

"""

        prompt += """TASK:
Analyze the draft and break it down into text segments (sections, paragraphs, bullet points, sentences).
For each segment, calculate an impact score from 0.0 to 1.0 based on:

IMPACT SCORE CRITERIA:
1. **Relevance to Job Requirements** (40%):
   - Direct match with required skills/technologies: High impact (0.8-1.0)
   - Indirect relevance to job duties: Medium impact (0.4-0.7)
   - Unrelated to job posting: Low impact (0.0-0.3)

2. **Quantifiable Achievements** (30%):
   - Contains specific metrics/percentages: +0.2 to +0.3
   - Demonstrates measurable impact: +0.1 to +0.2
   - Generic statements without metrics: No bonus

3. **Keyword Density** (20%):
   - High density of JD keywords: +0.1 to +0.2
   - Some JD keywords present: +0.05 to +0.1
   - No JD keywords: No bonus

4. **Best Practices Alignment** (10%):
   - Strong action verbs: +0.05
   - Clear, concise writing: +0.05
   - Follows ATS optimization: +0.05

SEGMENT TYPES:
- "header": Document headers and titles
- "summary": Professional summary or objective
- "section": Major sections (Experience, Skills, Education)
- "bullet": Individual bullet points or list items
- "sentence": Individual sentences within paragraphs
- "paragraph": Multi-sentence text blocks

INSTRUCTIONS:
1. Break the draft into meaningful segments
2. Calculate impact score for each segment
3. Identify segment type
4. Count lines in each segment
5. Return a JSON array with all segments

OUTPUT FORMAT:
Return a JSON object with this structure:
{
  "text_segments": [
    {
      "segment": "Led development of microservices platform serving 10M users",
      "impact_score": 0.92,
      "segment_type": "bullet",
      "line_count": 1
    },
    {
      "segment": "Proficient in Microsoft Office",
      "impact_score": 0.15,
      "segment_type": "bullet",
      "line_count": 1
    }
  ]
}

IMPORTANT:
- Be precise with impact scores based on job relevance
- Low-impact segments (< 0.3) are candidates for removal
- Medium-impact segments (0.3-0.6) may be rewritten
- High-impact segments (> 0.6) should be preserved
- Return ONLY the JSON object, no markdown formatting or code blocks
"""

        return prompt

    def _format_jd_for_prompt(self, parsed_jd: Dict[str, Any]) -> str:
        """Format parsed JD for inclusion in prompt.

        Args:
            parsed_jd: Parsed job description dict

        Returns:
            Formatted string representation
        """
        lines = []

        if "job_title" in parsed_jd:
            lines.append(f"Title: {parsed_jd['job_title']}")
        if "company" in parsed_jd:
            lines.append(f"Company: {parsed_jd['company']}")

        if "requirements" in parsed_jd:
            reqs = parsed_jd["requirements"]
            if isinstance(reqs, dict):
                if reqs.get("required"):
                    lines.append("\nRequired Skills:")
                    for req in reqs["required"]:
                        lines.append(f"  - {req}")
                if reqs.get("preferred"):
                    lines.append("\nPreferred Skills:")
                    for pref in reqs["preferred"]:
                        lines.append(f"  - {pref}")

        if "technologies" in parsed_jd and parsed_jd["technologies"]:
            tech_list = parsed_jd["technologies"]
            lines.append(f"\nKey Technologies: {', '.join(tech_list)}")

        return "\n".join(lines)

    def _get_input_summary(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create summary of input data for logging.

        Args:
            input_data: Input data to summarize

        Returns:
            Dictionary with input summary information
        """
        parsed_jd = input_data.get("parsed_jd", {})
        return {
            "draft_length": len(input_data.get("draft", "")),
            "job_title": parsed_jd.get("job_title", "unknown"),
            "company": parsed_jd.get("company", "unknown"),
            "has_best_practices": bool(input_data.get("best_practices"))
        }

    def _get_output_summary(self, output_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create summary of output data for logging.

        Args:
            output_data: Impact calculation result

        Returns:
            Dictionary with output summary information
        """
        if isinstance(output_data, dict):
            if output_data.get("instruction") == "CALL_TASK_TOOL":
                return {
                    "type": "task_instruction",
                    "draft_length": output_data.get("draft_length", 0),
                    "job_title": output_data.get("job_title", "unknown"),
                    "status": "pending_execution"
                }

            segments = output_data.get("text_segments", [])
            if segments:
                scores = [s.get("impact_score", 0.0) for s in segments if isinstance(s, dict)]
                avg_score = sum(scores) / len(scores) if scores else 0.0

                return {
                    "type": "impact_scores",
                    "segment_count": len(segments),
                    "average_score": round(avg_score, 2),
                    "low_impact_count": sum(1 for s in scores if s < 0.3),
                    "high_impact_count": sum(1 for s in scores if s > 0.6)
                }

        return {"type": "unknown", "data": str(output_data)[:100]}
