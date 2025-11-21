"""RemovalEvaluator agent for evaluating removal options to reduce length.

This agent identifies low-impact text segments that can be safely removed
to reduce document length without significantly harming quality.
"""

import logging
from typing import Dict, Any, List

from ..base_agent import BaseAgent


class RemovalEvaluator(BaseAgent[Dict[str, Any], Dict[str, Any]]):
    """Agent that evaluates removal options for length reduction.

    This agent analyzes the draft to identify low-impact text segments that
    can be removed to reduce length. It prioritizes removing content that
    has minimal relevance to the job requirements.

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
            "removal_options": List[dict]    # List of removal options
        }

        Each removal option dict contains:
        {
            "text_to_remove": str,           # Text segment to remove
            "impact_score": float,           # Current impact score (0.0 to 1.0)
            "length_reduction": int,         # Characters saved by removal
            "rationale": str                 # Explanation of why safe to remove
        }

    Example:
        >>> state_mgr = StateManager(Path("./run_001"))
        >>> agent = RemovalEvaluator(state_mgr, "pruning")
        >>> input_data = {
        ...     "draft": "# John Doe\\n...",
        ...     "parsed_jd": {"job_title": "Senior Engineer", ...},
        ...     "best_practices": "Use action verbs...",
        ...     "target_reduction": 200
        ... }
        >>> result = await agent.run(input_data)
        >>> options = result["removal_options"]
    """

    @property
    def agent_name(self) -> str:
        """Unique identifier for this agent type.

        Returns:
            Agent name string
        """
        return "removal_evaluator"

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
        """Evaluate removal options using Claude Code Task tool.

        Args:
            input_data: Validated input data with draft and context

        Returns:
            Dict with task instruction for removal evaluation

        Raises:
            RuntimeError: If evaluation fails
        """
        draft = input_data["draft"]
        target_reduction = input_data["target_reduction"]

        self.logger.info(
            f"Evaluating removal options for draft ({len(draft)} chars), "
            f"target reduction = {target_reduction}"
        )

        # Build prompt for Task tool
        prompt = self._build_removal_eval_prompt(input_data)

        # Task tool invocation structure
        task_instruction = {
            "instruction": "CALL_TASK_TOOL",
            "agent_type": self.agent_type,
            "prompt": prompt,
            "draft_length": len(draft),
            "target_reduction": target_reduction
        }

        self.logger.info("Generated removal evaluation instruction")

        return task_instruction

    async def format_output(self, raw_output: Any) -> Dict[str, Any]:
        """Format the raw output into structured removal options.

        Args:
            raw_output: Raw output from execute() or Task tool

        Returns:
            Dict with removal_options list
        """
        # If this is a task instruction (pre-execution), return as-is
        if isinstance(raw_output, dict) and raw_output.get("instruction") == "CALL_TASK_TOOL":
            self.logger.debug("Output is task instruction (pre-execution), passing through")
            return raw_output

        # Parse output into structured format
        if isinstance(raw_output, dict) and "removal_options" in raw_output:
            result = raw_output
        elif isinstance(raw_output, list):
            result = {"removal_options": raw_output}
        else:
            # Fallback
            self.logger.warning("Unexpected output format, using empty options")
            result = {"removal_options": []}

        # Validate options
        options = result.get("removal_options", [])
        if not isinstance(options, list):
            self.logger.error("removal_options must be a list")
            result["removal_options"] = []
        else:
            # Ensure each option has required fields
            validated_options = []
            for opt in options:
                if isinstance(opt, dict):
                    validated_options.append({
                        "text_to_remove": opt.get("text_to_remove", ""),
                        "impact_score": float(opt.get("impact_score", 0.0)),
                        "length_reduction": int(opt.get("length_reduction", 0)),
                        "rationale": opt.get("rationale", "")
                    })
            result["removal_options"] = validated_options

        self.logger.info(f"Formatted {len(result['removal_options'])} removal options")

        return result

    def _build_removal_eval_prompt(self, input_data: Dict[str, Any]) -> str:
        """Build prompt for Task tool to evaluate removal options.

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

        prompt = f"""Identify low-impact text segments in the draft that can be safely removed to reduce length.

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
Analyze the draft and identify text segments that have low relevance to the job and can be removed.

REMOVAL CRITERIA:
1. **Low Impact Content** (Priority 1 - Remove First):
   - Impact score < 0.3
   - No relevant keywords from job description
   - Generic skills/experiences not mentioned in JD
   - Outdated technologies or irrelevant experience
   - Redundant information already stated elsewhere

2. **Medium-Low Impact** (Priority 2 - Consider for Removal):
   - Impact score 0.3-0.5
   - Marginally relevant to job requirements
   - Can be inferred from other content
   - Nice-to-have but not essential

3. **Do NOT Remove**:
   - High impact content (score > 0.6)
   - Unique quantifiable achievements
   - Required skills/technologies from JD
   - Contact information or critical headers
   - Content that cannot be recovered if removed

EXAMPLES OF REMOVABLE CONTENT:
1. Generic skills: "Proficient in Microsoft Office" (if not in JD)
   Impact: 0.15, Removal: 35 chars

2. Irrelevant old experience: "Worked with Visual Basic in 2005"
   Impact: 0.2, Removal: 34 chars

3. Redundant statement: "Team player with excellent communication skills"
   Impact: 0.25, Removal: 50 chars

4. Outdated technology: "Experience with Flash and Silverlight"
   Impact: 0.1, Removal: 42 chars

IMPACT SCORE INTERPRETATION:
- 0.0-0.2: Very low impact, safe to remove
- 0.2-0.3: Low impact, good candidate for removal
- 0.3-0.5: Medium-low impact, consider if needed
- 0.5+: Too important to remove, consider rewriting instead

INSTRUCTIONS:
1. Identify segments with low relevance to job requirements
2. Calculate current impact score for each segment
3. Calculate exact length reduction (characters including whitespace)
4. Provide clear rationale for why removal is safe
5. Prioritize low-impact content first
6. Aim to achieve target reduction of {target_reduction} characters total
7. Ensure removal doesn't create orphaned sections or formatting issues

OUTPUT FORMAT:
Return a JSON object with this structure:
{{
  "removal_options": [
    {{
      "text_to_remove": "Proficient in Microsoft Office Suite (Word, Excel, PowerPoint)",
      "impact_score": 0.15,
      "length_reduction": 65,
      "rationale": "Generic skill not mentioned in JD; all tech roles assume basic office proficiency"
    }},
    {{
      "text_to_remove": "Hobbies include photography and hiking",
      "impact_score": 0.05,
      "length_reduction": 42,
      "rationale": "Personal interests unrelated to job requirements; no professional value"
    }},
    {{
      "text_to_remove": "References available upon request",
      "impact_score": 0.1,
      "length_reduction": 35,
      "rationale": "Standard assumption; unnecessary to state explicitly"
    }}
  ]
}}

IMPORTANT:
- Prioritize lowest impact content first (score < 0.2)
- Be conservative: when in doubt, don't remove
- Ensure removals are complete segments (full sentences/bullets)
- Avoid creating grammatical issues or orphaned text
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
            output_data: Removal options result

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

            options = output_data.get("removal_options", [])
            if options:
                total_reduction = sum(opt.get("length_reduction", 0) for opt in options)
                avg_impact = sum(opt.get("impact_score", 0.0) for opt in options) / len(options)

                return {
                    "type": "removal_options",
                    "option_count": len(options),
                    "total_length_reduction": total_reduction,
                    "average_impact_score": round(avg_impact, 3),
                    "very_low_impact_count": sum(1 for opt in options if opt.get("impact_score", 0) < 0.2)
                }

        return {"type": "unknown", "data": str(output_data)[:100]}
