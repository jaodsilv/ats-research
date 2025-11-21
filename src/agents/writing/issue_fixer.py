"""IssueFixer agent for fixing critical issues in drafts.

This agent addresses critical quality issues identified by DocumentEvaluator,
such as missing sections, formatting problems, or major content gaps.
"""

import logging
from typing import Dict, Any

from ..base_agent import BaseAgent
from ...decisions.decision_logic import DocumentEvaluation


class IssueFixer(BaseAgent[Dict[str, Any], str]):
    """Agent that fixes critical issues in document drafts.

    This agent uses Claude Code's Task tool to address blocking quality issues
    that prevent the document from being acceptable, such as missing contact info,
    major formatting problems, or critical content gaps.

    Input Format:
        Dict with keys:
        {
            "draft": str,                   # Draft with critical issues
            "evaluation": DocumentEvaluation, # Evaluation results
            "parsed_jd": dict               # Parsed job description
        }

    Output Format:
        str: Fixed draft with critical issues resolved

    Example:
        >>> state_mgr = StateManager(Path("./run_001"))
        >>> agent = IssueFixer(state_mgr, "polishing")
        >>> evaluation = DocumentEvaluation(
        ...     score=0.45,
        ...     has_critical_issues=True,
        ...     has_false_facts=False,
        ...     issue_count=5,
        ...     quality_notes="Missing contact info, poor formatting",
        ...     metadata={"critical_issues_list": ["no contact", "bad structure"]}
        ... )
        >>> input_data = {
        ...     "draft": "# Resume\\n...",
        ...     "evaluation": evaluation,
        ...     "parsed_jd": {"job_title": "Engineer", ...}
        ... }
        >>> fixed = await agent.run(input_data)
    """

    @property
    def agent_name(self) -> str:
        """Unique identifier for this agent type.

        Returns:
            Agent name string
        """
        return "issue_fixer"

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
        2. Required keys exist: draft, evaluation, parsed_jd
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
        required_keys = ["draft", "evaluation", "parsed_jd"]
        missing_keys = [k for k in required_keys if k not in input_data]
        if missing_keys:
            self.logger.error(f"Missing required keys: {missing_keys}")
            return False

        # Validate draft
        draft = input_data.get("draft", "")
        if not isinstance(draft, str) or len(draft.strip()) < 10:
            self.logger.error("draft must be non-empty string (min 10 chars)")
            return False

        # Validate evaluation (can be dict or DocumentEvaluation)
        evaluation = input_data.get("evaluation")
        if not isinstance(evaluation, (dict, DocumentEvaluation)):
            self.logger.error("evaluation must be dict or DocumentEvaluation")
            return False

        # Validate parsed JD
        parsed_jd = input_data.get("parsed_jd", {})
        if not isinstance(parsed_jd, dict):
            self.logger.error("parsed_jd must be a dict")
            return False

        self.logger.info("Input validation passed")
        return True

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fix critical issues using Claude Code Task tool.

        Args:
            input_data: Validated input data with draft, evaluation, and context

        Returns:
            Dict with task instruction for issue fixing

        Raises:
            RuntimeError: If issue fixing fails
        """
        draft = input_data["draft"]
        evaluation = input_data["evaluation"]
        parsed_jd = input_data["parsed_jd"]

        # Extract evaluation data
        if isinstance(evaluation, DocumentEvaluation):
            eval_dict = {
                "score": evaluation.score,
                "has_critical_issues": evaluation.has_critical_issues,
                "issue_count": evaluation.issue_count,
                "quality_notes": evaluation.quality_notes,
                "metadata": evaluation.metadata
            }
        else:
            eval_dict = evaluation

        issue_count = eval_dict.get("issue_count", 0)

        self.logger.info(f"Fixing critical issues in draft ({issue_count} total issues)")

        # Build prompt for Task tool
        prompt = self._build_fix_prompt(draft, eval_dict, parsed_jd)

        # Task tool invocation structure
        task_instruction = {
            "instruction": "CALL_TASK_TOOL",
            "agent_type": self.agent_type,
            "prompt": prompt,
            "issue_count": issue_count,
            "draft_length": len(draft)
        }

        self.logger.info(f"Generated issue-fixing instruction for {issue_count} issues")

        return task_instruction

    async def format_output(self, raw_output: Any) -> str:
        """Format the raw fix output into final string.

        Args:
            raw_output: Raw output from execute() or Task tool

        Returns:
            Fixed draft content as string
        """
        # If this is a task instruction (pre-execution), return as-is
        if isinstance(raw_output, dict) and raw_output.get("instruction") == "CALL_TASK_TOOL":
            self.logger.debug("Output is task instruction (pre-execution), passing through")
            return raw_output

        # Otherwise, ensure we have a string
        if isinstance(raw_output, str):
            fixed = raw_output.strip()
        elif isinstance(raw_output, dict) and "fixed_draft" in raw_output:
            fixed = raw_output["fixed_draft"].strip()
        else:
            fixed = str(raw_output).strip()

        if len(fixed) < 50:
            self.logger.warning(f"Fixed draft seems too short: {len(fixed)} characters")

        self.logger.info(f"Formatted fixed draft: {len(fixed)} characters")

        return fixed

    def _build_fix_prompt(
        self,
        draft: str,
        evaluation: Dict[str, Any],
        parsed_jd: Dict[str, Any]
    ) -> str:
        """Build prompt for Task tool to fix critical issues.

        Args:
            draft: Draft with critical issues
            evaluation: Evaluation results dict
            parsed_jd: Parsed job description

        Returns:
            Formatted prompt string for Task tool
        """
        quality_notes = evaluation.get("quality_notes", "")
        metadata = evaluation.get("metadata", {})
        critical_issues = metadata.get("critical_issues_list", [])

        job_title = parsed_jd.get("job_title", "Unknown Position")

        # Format critical issues
        issues_text = ""
        if critical_issues:
            issues_text = "\n".join(f"  - {issue}" for issue in critical_issues)
        else:
            issues_text = "  (See quality notes for details)"

        prompt = f"""Fix the critical issues in the following draft document.

JOB TITLE: {job_title}

DRAFT WITH CRITICAL ISSUES:
{draft}

EVALUATION SCORE: {evaluation.get('score', 0.0):.2f} / 1.0

CRITICAL ISSUES IDENTIFIED:
{issues_text}

QUALITY EVALUATION NOTES:
{quality_notes}

INSTRUCTIONS:
Fix all critical issues while preserving the overall content and structure. Focus on:

1. **Missing Content**: Add any required sections (contact info, summary, etc.)
2. **Formatting Problems**: Fix structure, headings, spacing, ATS compatibility
3. **Major Gaps**: Address significant content deficiencies
4. **Critical Errors**: Fix any blocking problems

IMPORTANT:
- Preserve all good content from the original draft
- Only fix what's broken - don't rewrite unnecessarily
- Maintain professional tone and formatting
- Ensure ATS compatibility (no tables, columns, complex formatting)
- Keep the document length appropriate
- Use proper Markdown formatting

The goal is to resolve ONLY the critical issues that are blocking acceptance.
Polish and minor improvements will happen in a later step.

Return ONLY the fixed draft in Markdown format.
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
        evaluation = input_data.get("evaluation")
        parsed_jd = input_data.get("parsed_jd", {})

        # Extract evaluation data
        if isinstance(evaluation, DocumentEvaluation):
            score = evaluation.score
            issue_count = evaluation.issue_count
            has_critical = evaluation.has_critical_issues
        elif isinstance(evaluation, dict):
            score = evaluation.get("score", 0.0)
            issue_count = evaluation.get("issue_count", 0)
            has_critical = evaluation.get("has_critical_issues", False)
        else:
            score = 0.0
            issue_count = 0
            has_critical = False

        return {
            "draft_length": len(input_data.get("draft", "")),
            "job_title": parsed_jd.get("job_title", "unknown"),
            "evaluation_score": score,
            "issue_count": issue_count,
            "has_critical_issues": has_critical
        }

    def _get_output_summary(self, output_data: str) -> Dict[str, Any]:
        """Create summary of output data for logging.

        Args:
            output_data: Fixed draft content

        Returns:
            Dictionary with output summary information
        """
        if isinstance(output_data, dict) and output_data.get("instruction") == "CALL_TASK_TOOL":
            return {
                "type": "task_instruction",
                "issue_count": output_data.get("issue_count", 0),
                "draft_length": output_data.get("draft_length", 0),
                "status": "pending_execution"
            }

        draft_length = len(output_data) if isinstance(output_data, str) else 0
        word_count = len(output_data.split()) if isinstance(output_data, str) else 0

        return {
            "type": "fixed_draft",
            "character_count": draft_length,
            "word_count": word_count,
            "line_count": output_data.count('\n') if isinstance(output_data, str) else 0
        }
