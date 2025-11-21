"""RewritingEvaluator agent for evaluating rewriting options to reduce length.

This agent identifies text segments that can be rewritten more concisely
while maintaining or improving quality and impact.
"""

import logging
from typing import Dict, Any, List

from ..base_agent import BaseAgent


class RewritingEvaluator(BaseAgent[Dict[str, Any], Dict[str, Any]]):
    """Agent that evaluates rewriting options for length reduction.

    This agent analyzes the draft to identify text segments that can be
    rewritten more concisely. It proposes rewrites that maintain impact
    while reducing length.

    Input Format:
        Dict with keys:
        {
            "draft": str,                    # Draft content to analyze
            "parsed_jd": dict,               # Parsed job description
            "best_practices": str,           # Best practices guidelines
            "target_reduction": int          # Target length reduction (chars or lines)
        }

    Output Format:
        Dict with keys:
        {
            "rewrite_options": List[dict]    # List of rewrite options
        }

        Each rewrite option dict contains:
        {
            "original_text": str,            # Original text segment
            "rewritten_text": str,           # Proposed rewrite
            "impact_delta": float,           # Change in impact (-1.0 to +1.0)
            "length_reduction": int,         # Characters saved
            "rationale": str                 # Explanation of rewrite
        }

    Example:
        >>> state_mgr = StateManager(Path("./run_001"))
        >>> agent = RewritingEvaluator(state_mgr, "pruning")
        >>> input_data = {
        ...     "draft": "# John Doe\\n...",
        ...     "parsed_jd": {"job_title": "Senior Engineer", ...},
        ...     "best_practices": "Use action verbs...",
        ...     "target_reduction": 200
        ... }
        >>> result = await agent.run(input_data)
        >>> options = result["rewrite_options"]
    """

    @property
    def agent_name(self) -> str:
        """Unique identifier for this agent type.

        Returns:
            Agent name string
        """
        return "rewriting_evaluator"

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
        2. Required keys exist: draft, parsed_jd, target_reduction
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
        required_keys = ["draft", "parsed_jd", "target_reduction"]
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

        # Validate target_reduction
        target_reduction = input_data.get("target_reduction", 0)
        if not isinstance(target_reduction, (int, float)) or target_reduction < 0:
            self.logger.error("target_reduction must be non-negative number")
            return False

        self.logger.info(f"Input validation passed: target reduction = {target_reduction}")
        return True

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate rewriting options using Claude Code Task tool.

        Args:
            input_data: Validated input data with draft and context

        Returns:
            Dict with task instruction for rewrite evaluation

        Raises:
            RuntimeError: If evaluation fails
        """
        draft = input_data["draft"]
        target_reduction = input_data["target_reduction"]

        self.logger.info(
            f"Evaluating rewrite options for draft ({len(draft)} chars), "
            f"target reduction = {target_reduction}"
        )

        # Build prompt for Task tool
        prompt = self._build_rewrite_eval_prompt(input_data)

        # Task tool invocation structure
        task_instruction = {
            "instruction": "CALL_TASK_TOOL",
            "agent_type": self.agent_type,
            "prompt": prompt,
            "draft_length": len(draft),
            "target_reduction": target_reduction
        }

        self.logger.info("Generated rewrite evaluation instruction")

        return task_instruction

    async def format_output(self, raw_output: Any) -> Dict[str, Any]:
        """Format the raw output into structured rewrite options.

        Args:
            raw_output: Raw output from execute() or Task tool

        Returns:
            Dict with rewrite_options list
        """
        # If this is a task instruction (pre-execution), return as-is
        if isinstance(raw_output, dict) and raw_output.get("instruction") == "CALL_TASK_TOOL":
            self.logger.debug("Output is task instruction (pre-execution), passing through")
            return raw_output

        # Parse output into structured format
        if isinstance(raw_output, dict) and "rewrite_options" in raw_output:
            result = raw_output
        elif isinstance(raw_output, list):
            result = {"rewrite_options": raw_output}
        else:
            # Fallback
            self.logger.warning("Unexpected output format, using empty options")
            result = {"rewrite_options": []}

        # Validate options
        options = result.get("rewrite_options", [])
        if not isinstance(options, list):
            self.logger.error("rewrite_options must be a list")
            result["rewrite_options"] = []
        else:
            # Ensure each option has required fields
            validated_options = []
            for opt in options:
                if isinstance(opt, dict):
                    validated_options.append({
                        "original_text": opt.get("original_text", ""),
                        "rewritten_text": opt.get("rewritten_text", ""),
                        "impact_delta": float(opt.get("impact_delta", 0.0)),
                        "length_reduction": int(opt.get("length_reduction", 0)),
                        "rationale": opt.get("rationale", "")
                    })
            result["rewrite_options"] = validated_options

        self.logger.info(f"Formatted {len(result['rewrite_options'])} rewrite options")

        return result

    def _build_rewrite_eval_prompt(self, input_data: Dict[str, Any]) -> str:
        """Build prompt for Task tool to evaluate rewrite options.

        Args:
            input_data: Input data with draft and context

        Returns:
            Formatted prompt string for Task tool
        """
        draft = input_data["draft"]
        parsed_jd = input_data["parsed_jd"]
        best_practices = input_data.get("best_practices", "")
        target_reduction = input_data["target_reduction"]

        job_title = parsed_jd.get("job_title", "Unknown Position")
        company = parsed_jd.get("company", "Unknown Company")

        prompt = f"""Identify text segments in the draft that can be rewritten more concisely while maintaining or improving quality.

JOB DETAILS:
- Title: {job_title}
- Company: {company}
- Target Length Reduction: {target_reduction} characters

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
Analyze the draft and propose rewriting options that reduce length while maintaining impact.

REWRITING CRITERIA:
1. **Verbosity Reduction**:
   - Remove redundant words ("very", "really", "actually")
   - Replace wordy phrases with concise alternatives
   - Eliminate unnecessary qualifiers
   - Use stronger verbs instead of verb+adverb combinations

2. **Maintain/Improve Impact**:
   - Preserve all key information and achievements
   - Keep quantifiable metrics
   - Maintain keyword alignment with job description
   - Use stronger action verbs where possible

3. **Length Reduction**:
   - Aim for 10-30% reduction per segment
   - Prioritize segments with high verbosity
   - Focus on medium-to-high impact content (worth rewriting)

4. **Quality Standards**:
   - Preserve professional tone
   - Maintain clarity and readability
   - Keep all factual information accurate
   - Follow ATS optimization principles

EXAMPLES OF GOOD REWRITES:
Original: "Responsible for leading a team of 5 engineers in the development of new features"
Rewritten: "Led 5-engineer team developing new features"
Impact Delta: +0.05 (stronger verb)
Length Reduction: 31 characters

Original: "Successfully implemented and deployed a microservices architecture"
Rewritten: "Implemented microservices architecture"
Impact Delta: 0.0 (no loss)
Length Reduction: 25 characters

IMPACT DELTA SCORING:
- Negative delta (-0.1 to -0.5): Quality/impact decreased
- Zero delta (0.0): Same quality/impact
- Positive delta (+0.1 to +0.3): Improved quality/impact (stronger verbs, better clarity)

INSTRUCTIONS:
1. Identify verbose or wordy segments (paragraphs, sentences, bullets)
2. Propose concise rewrites that maintain meaning
3. Calculate impact delta (change in quality/impact)
4. Calculate exact length reduction in characters
5. Provide clear rationale for each rewrite
6. Prioritize rewrites with positive or zero impact delta
7. Aim to achieve target reduction of {target_reduction} characters total

OUTPUT FORMAT:
Return a JSON object with this structure:
{{
  "rewrite_options": [
    {{
      "original_text": "Responsible for leading and managing a team of 5 software engineers",
      "rewritten_text": "Led 5-engineer software development team",
      "impact_delta": 0.05,
      "length_reduction": 28,
      "rationale": "Replaced passive 'responsible for' with active 'Led', removed redundant 'managing'"
    }},
    {{
      "original_text": "Very proficient in Python programming and development",
      "rewritten_text": "Proficient in Python development",
      "impact_delta": 0.0,
      "length_reduction": 21,
      "rationale": "Removed redundant qualifier 'very' and duplicate 'programming and'"
    }}
  ]
}}

IMPORTANT:
- Focus on medium-to-high impact segments (worth preserving)
- Don't rewrite low-impact segments (those should be removed instead)
- Ensure rewrites maintain factual accuracy
- Provide enough options to meet target reduction
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

        if "requirements" in parsed_jd:
            reqs = parsed_jd["requirements"]
            if isinstance(reqs, dict) and reqs.get("required"):
                skills = reqs["required"][:5]
                lines.append(f"Required Skills: {', '.join(skills)}")

        if "technologies" in parsed_jd and parsed_jd["technologies"]:
            tech_list = parsed_jd["technologies"][:8]
            lines.append(f"Technologies: {', '.join(tech_list)}")

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
            "target_reduction": input_data.get("target_reduction", 0),
            "job_title": parsed_jd.get("job_title", "unknown"),
            "has_best_practices": bool(input_data.get("best_practices"))
        }

    def _get_output_summary(self, output_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create summary of output data for logging.

        Args:
            output_data: Rewrite options result

        Returns:
            Dictionary with output summary information
        """
        if isinstance(output_data, dict):
            if output_data.get("instruction") == "CALL_TASK_TOOL":
                return {
                    "type": "task_instruction",
                    "draft_length": output_data.get("draft_length", 0),
                    "target_reduction": output_data.get("target_reduction", 0),
                    "status": "pending_execution"
                }

            options = output_data.get("rewrite_options", [])
            if options:
                total_reduction = sum(opt.get("length_reduction", 0) for opt in options)
                avg_delta = sum(opt.get("impact_delta", 0.0) for opt in options) / len(options)

                return {
                    "type": "rewrite_options",
                    "option_count": len(options),
                    "total_length_reduction": total_reduction,
                    "average_impact_delta": round(avg_delta, 3),
                    "positive_impact_count": sum(1 for opt in options if opt.get("impact_delta", 0) > 0)
                }

        return {"type": "unknown", "data": str(output_data)[:100]}
