"""DocumentEvaluator agent for evaluating draft quality.

This agent evaluates document quality, identifies issues, and assigns scores
to guide the polishing iteration process.
"""

import logging
from typing import Dict, Any

from ..base_agent import BaseAgent
from ...decisions.decision_logic import DocumentEvaluation


class DocumentEvaluator(BaseAgent[Dict[str, Any], DocumentEvaluation]):
    """Agent that evaluates document quality and identifies issues.

    This agent uses Claude Code's Task tool to perform comprehensive quality
    evaluation of drafts, checking for ATS optimization, clarity, formatting,
    keyword alignment, and overall effectiveness.

    Input Format:
        Dict with keys:
        {
            "draft": str,                # Draft to evaluate
            "parsed_jd": dict,           # Parsed job description
            "best_practices": str        # Best practices guidelines
        }

    Output Format:
        DocumentEvaluation dataclass with:
        {
            "score": float,                    # 0.0 to 1.0
            "has_critical_issues": bool,       # Blocking issues present
            "has_false_facts": bool,           # Factual inaccuracies detected
            "issue_count": int,                # Total issues found
            "quality_notes": str,              # Detailed quality analysis
            "metadata": dict                   # Additional evaluation data
        }

    Example:
        >>> state_mgr = StateManager(Path("./run_001"))
        >>> agent = DocumentEvaluator(state_mgr, "polishing")
        >>> input_data = {
        ...     "draft": "# John Doe Resume\\n...",
        ...     "parsed_jd": {"job_title": "Senior Engineer", ...},
        ...     "best_practices": "Use action verbs..."
        ... }
        >>> evaluation = await agent.run(input_data)
        >>> print(f"Score: {evaluation.score}, Issues: {evaluation.issue_count}")
    """

    @property
    def agent_name(self) -> str:
        """Unique identifier for this agent type.

        Returns:
            Agent name string
        """
        return "document_evaluator"

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
        2. Required keys exist: draft, parsed_jd
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
        """Evaluate document quality using Claude Code Task tool.

        Args:
            input_data: Validated input data with draft and context

        Returns:
            Dict with task instruction for evaluation

        Raises:
            RuntimeError: If evaluation fails
        """
        draft = input_data["draft"]
        parsed_jd = input_data["parsed_jd"]

        self.logger.info(f"Evaluating draft ({len(draft)} chars)")

        # Build prompt for Task tool
        prompt = self._build_evaluation_prompt(input_data)

        # Task tool invocation structure
        task_instruction = {
            "instruction": "CALL_TASK_TOOL",
            "agent_type": self.agent_type,
            "prompt": prompt,
            "draft_length": len(draft),
            "job_title": parsed_jd.get("job_title", "unknown")
        }

        self.logger.info("Generated evaluation instruction")

        return task_instruction

    async def format_output(self, raw_output: Any) -> DocumentEvaluation:
        """Format the raw evaluation output into DocumentEvaluation.

        Args:
            raw_output: Raw output from execute() or Task tool

        Returns:
            DocumentEvaluation dataclass instance
        """
        # If this is a task instruction (pre-execution), return as-is
        if isinstance(raw_output, dict) and raw_output.get("instruction") == "CALL_TASK_TOOL":
            self.logger.debug("Output is task instruction (pre-execution), passing through")
            return raw_output

        # Parse output into DocumentEvaluation
        if isinstance(raw_output, dict):
            evaluation = DocumentEvaluation(
                score=raw_output.get("score", 0.0),
                has_critical_issues=raw_output.get("has_critical_issues", False),
                has_false_facts=raw_output.get("has_false_facts", False),
                issue_count=raw_output.get("issue_count", 0),
                quality_notes=raw_output.get("quality_notes", ""),
                metadata=raw_output.get("metadata", {})
            )
        else:
            # Fallback if output format is unexpected
            self.logger.warning("Unexpected output format, using safe defaults")
            evaluation = DocumentEvaluation(
                score=0.0,
                has_critical_issues=True,
                has_false_facts=False,
                issue_count=1,
                quality_notes="Evaluation failed - unexpected output format",
                metadata={"error": str(raw_output)}
            )

        # Validate score is in range
        if not (0.0 <= evaluation.score <= 1.0):
            self.logger.warning(f"Score {evaluation.score} out of range, clamping to [0.0, 1.0]")
            evaluation.score = max(0.0, min(1.0, evaluation.score))

        self.logger.info(
            f"Evaluation complete: score={evaluation.score:.2f}, "
            f"issues={evaluation.issue_count}, critical={evaluation.has_critical_issues}"
        )

        return evaluation

    def _build_evaluation_prompt(self, input_data: Dict[str, Any]) -> str:
        """Build prompt for Task tool to evaluate document.

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

        prompt = f"""Evaluate the quality of the following draft document for a job application.

JOB DETAILS:
- Title: {job_title}
- Company: {company}

DRAFT TO EVALUATE:
{draft}

PARSED JOB DESCRIPTION:
{self._format_jd_for_prompt(parsed_jd)}

"""

        if best_practices:
            prompt += f"""BEST PRACTICES GUIDELINES:
{best_practices}

"""

        prompt += """EVALUATION CRITERIA:

1. **ATS Optimization** (Weight: 25%)
   - Keyword alignment with job description
   - Proper formatting for ATS parsing
   - No tables, columns, or complex formatting
   - Standard section headings

2. **Content Quality** (Weight: 30%)
   - Strong action verbs and quantifiable achievements
   - Relevance to job requirements
   - Clear and concise writing
   - Professional tone

3. **Completeness** (Weight: 20%)
   - All critical sections present
   - Sufficient detail in each section
   - Contact information included (if applicable)
   - Proper length for document type

4. **Formatting & Structure** (Weight: 15%)
   - Clean, professional layout
   - Consistent formatting
   - Good use of whitespace
   - Easy to scan and read

5. **Alignment** (Weight: 10%)
   - Addresses job requirements
   - Highlights relevant skills
   - Shows fit for company culture

CRITICAL ISSUES (must be flagged):
- Missing contact information
- Obvious formatting problems
- Length significantly off-target
- Major keyword gaps for required skills
- Poor overall structure

INSTRUCTIONS:
Provide a comprehensive evaluation with:

1. **Overall Score**: 0.0 (unacceptable) to 1.0 (excellent)
   - 0.0-0.4: Major problems, needs substantial rework
   - 0.4-0.6: Acceptable but needs improvement
   - 0.6-0.8: Good quality, minor improvements needed
   - 0.8-1.0: Excellent quality, ready or near-ready

2. **Critical Issues**: Identify any blocking issues that must be fixed

3. **Issue Count**: Total number of issues found (critical + non-critical)

4. **Quality Notes**: Detailed analysis including:
   - Strengths of the draft
   - Areas for improvement
   - Specific issues identified
   - Recommendations for next iteration

Return a JSON object with this structure:
{
  "score": 0.85,
  "has_critical_issues": false,
  "has_false_facts": false,
  "issue_count": 3,
  "quality_notes": "Detailed evaluation text...",
  "metadata": {
    "ats_score": 0.9,
    "content_score": 0.85,
    "completeness_score": 0.8,
    "formatting_score": 0.9,
    "alignment_score": 0.8,
    "word_count": 450,
    "critical_issues_list": [],
    "improvement_areas": ["minor keyword gaps", "add more quantification"]
  }
}

IMPORTANT:
- Be thorough but fair in evaluation
- Provide actionable feedback in quality_notes
- Flag critical issues honestly
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
                    for req in reqs["required"][:5]:  # Top 5
                        lines.append(f"  - {req}")
                if reqs.get("preferred"):
                    lines.append("\nPreferred Skills:")
                    for pref in reqs["preferred"][:3]:  # Top 3
                        lines.append(f"  - {pref}")

        if "technologies" in parsed_jd and parsed_jd["technologies"]:
            tech_list = parsed_jd["technologies"][:10]  # Top 10
            lines.append(f"\nKey Technologies: {', '.join(tech_list)}")

        return "\n".join(lines)

    def _serialize_output(self, output_data: DocumentEvaluation) -> Any:
        """Convert DocumentEvaluation to JSON-serializable format.

        Args:
            output_data: DocumentEvaluation instance

        Returns:
            JSON-serializable dict
        """
        if isinstance(output_data, dict):
            # Already serializable
            return output_data

        if hasattr(output_data, "__dict__"):
            # Convert dataclass to dict
            return {
                "score": output_data.score,
                "has_critical_issues": output_data.has_critical_issues,
                "has_false_facts": output_data.has_false_facts,
                "issue_count": output_data.issue_count,
                "quality_notes": output_data.quality_notes,
                "metadata": output_data.metadata
            }

        return str(output_data)

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

    def _get_output_summary(self, output_data: DocumentEvaluation) -> Dict[str, Any]:
        """Create summary of output data for logging.

        Args:
            output_data: DocumentEvaluation instance

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
            # Pre-formatted dict
            return {
                "type": "evaluation",
                "score": output_data.get("score", 0.0),
                "has_critical_issues": output_data.get("has_critical_issues", False),
                "issue_count": output_data.get("issue_count", 0)
            }

        # DocumentEvaluation instance
        return {
            "type": "evaluation",
            "score": getattr(output_data, "score", 0.0),
            "has_critical_issues": getattr(output_data, "has_critical_issues", False),
            "issue_count": getattr(output_data, "issue_count", 0),
            "has_false_facts": getattr(output_data, "has_false_facts", False)
        }
