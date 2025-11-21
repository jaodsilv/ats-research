"""DocumentPolisher agent for improving draft quality.

This agent performs final polishing on drafts to improve grammar, tone,
ATS optimization, keyword density, and overall professional quality.
"""

import logging
from typing import Dict, Any

from ..base_agent import BaseAgent
from ...decisions.decision_logic import DocumentEvaluation


class DocumentPolisher(BaseAgent[Dict[str, Any], str]):
    """Agent that polishes and refines document drafts.

    This agent uses Claude Code's Task tool to improve draft quality through
    grammar refinement, tone adjustment, ATS keyword optimization, and
    professional writing enhancements.

    Input Format:
        Dict with keys:
        {
            "draft": str,                   # Draft to polish
            "evaluation": DocumentEvaluation, # Evaluation results
            "parsed_jd": dict,              # Parsed job description
            "best_practices": str           # Best practices guidelines
        }

    Output Format:
        str: Polished draft with quality improvements

    Example:
        >>> state_mgr = StateManager(Path("./run_001"))
        >>> agent = DocumentPolisher(state_mgr, "polishing")
        >>> evaluation = DocumentEvaluation(
        ...     score=0.75,
        ...     has_critical_issues=False,
        ...     has_false_facts=False,
        ...     issue_count=3,
        ...     quality_notes="Good but could use better keywords",
        ...     metadata={"improvement_areas": ["keyword optimization", "action verbs"]}
        ... )
        >>> input_data = {
        ...     "draft": "# John Doe Resume\\n...",
        ...     "evaluation": evaluation,
        ...     "parsed_jd": {"job_title": "Engineer", ...},
        ...     "best_practices": "Use strong action verbs..."
        ... }
        >>> polished = await agent.run(input_data)
    """

    @property
    def agent_name(self) -> str:
        """Unique identifier for this agent type.

        Returns:
            Agent name string
        """
        return "document_polisher"

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
        """Polish document using Claude Code Task tool.

        Args:
            input_data: Validated input data with draft, evaluation, and context

        Returns:
            Dict with task instruction for polishing

        Raises:
            RuntimeError: If polishing fails
        """
        draft = input_data["draft"]
        evaluation = input_data["evaluation"]
        parsed_jd = input_data["parsed_jd"]

        # Extract evaluation data
        if isinstance(evaluation, DocumentEvaluation):
            eval_dict = {
                "score": evaluation.score,
                "issue_count": evaluation.issue_count,
                "quality_notes": evaluation.quality_notes,
                "metadata": evaluation.metadata
            }
        else:
            eval_dict = evaluation

        current_score = eval_dict.get("score", 0.0)

        self.logger.info(f"Polishing draft (current score: {current_score:.2f})")

        # Build prompt for Task tool
        prompt = self._build_polish_prompt(input_data)

        # Task tool invocation structure
        task_instruction = {
            "instruction": "CALL_TASK_TOOL",
            "agent_type": self.agent_type,
            "prompt": prompt,
            "current_score": current_score,
            "draft_length": len(draft)
        }

        self.logger.info("Generated polishing instruction")

        return task_instruction

    async def format_output(self, raw_output: Any) -> str:
        """Format the raw polish output into final string.

        Args:
            raw_output: Raw output from execute() or Task tool

        Returns:
            Polished draft content as string
        """
        # If this is a task instruction (pre-execution), return as-is
        if isinstance(raw_output, dict) and raw_output.get("instruction") == "CALL_TASK_TOOL":
            self.logger.debug("Output is task instruction (pre-execution), passing through")
            return raw_output

        # Otherwise, ensure we have a string
        if isinstance(raw_output, str):
            polished = raw_output.strip()
        elif isinstance(raw_output, dict) and "polished_draft" in raw_output:
            polished = raw_output["polished_draft"].strip()
        else:
            polished = str(raw_output).strip()

        if len(polished) < 50:
            self.logger.warning(f"Polished draft seems too short: {len(polished)} characters")

        self.logger.info(f"Formatted polished draft: {len(polished)} characters")

        return polished

    def _build_polish_prompt(self, input_data: Dict[str, Any]) -> str:
        """Build prompt for Task tool to polish document.

        Args:
            input_data: Input data with draft, evaluation, and context

        Returns:
            Formatted prompt string for Task tool
        """
        draft = input_data["draft"]
        evaluation = input_data["evaluation"]
        parsed_jd = input_data["parsed_jd"]
        best_practices = input_data.get("best_practices", "")

        # Extract evaluation data
        if isinstance(evaluation, DocumentEvaluation):
            quality_notes = evaluation.quality_notes
            metadata = evaluation.metadata
            current_score = evaluation.score
        else:
            quality_notes = evaluation.get("quality_notes", "")
            metadata = evaluation.get("metadata", {})
            current_score = evaluation.get("score", 0.0)

        improvement_areas = metadata.get("improvement_areas", [])
        job_title = parsed_jd.get("job_title", "Unknown Position")

        # Format improvement areas
        improvements_text = ""
        if improvement_areas:
            improvements_text = "\n".join(f"  - {area}" for area in improvement_areas)
        else:
            improvements_text = "  (See quality notes for guidance)"

        prompt = f"""Polish and refine the following draft to improve its quality.

JOB TITLE: {job_title}

CURRENT DRAFT:
{draft}

CURRENT QUALITY SCORE: {current_score:.2f} / 1.0

AREAS FOR IMPROVEMENT:
{improvements_text}

QUALITY EVALUATION NOTES:
{quality_notes}

"""

        if best_practices:
            prompt += f"""BEST PRACTICES GUIDELINES:
{best_practices}

"""

        # Add job requirements for keyword optimization
        prompt += f"""JOB REQUIREMENTS (for keyword optimization):
{self._format_jd_requirements(parsed_jd)}

POLISHING INSTRUCTIONS:

1. **Grammar & Writing Quality**
   - Fix any grammar, spelling, or punctuation errors
   - Improve sentence structure and flow
   - Ensure consistent tense (past for previous roles, present for current)
   - Eliminate redundancy and wordiness

2. **Action Verbs & Impact**
   - Replace weak verbs with strong action verbs
   - Emphasize achievements and quantifiable results
   - Lead with impact, not responsibilities
   - Use active voice consistently

3. **ATS Optimization**
   - Incorporate keywords from job description naturally
   - Ensure proper formatting for ATS parsing
   - Use standard section headings
   - Avoid tables, columns, or complex layouts

4. **Professional Tone**
   - Maintain confident, professional language
   - Avoid informal language or clichés
   - Keep tone appropriate for industry
   - Ensure consistency throughout

5. **Clarity & Conciseness**
   - Make every word count
   - Remove filler and unnecessary details
   - Ensure clarity and easy readability
   - Maintain appropriate length

6. **Keyword Density**
   - Naturally integrate job-relevant keywords
   - Balance keyword usage with readability
   - Don't keyword-stuff
   - Prioritize required skills/technologies

IMPORTANT:
- Preserve all factual information (don't fabricate)
- Maintain the document structure
- Keep improvements subtle and natural
- Focus on quality over quantity
- The goal is incremental improvement, not complete rewrite

Return ONLY the polished draft in Markdown format.
Do not include explanations, comments, or metadata.
"""

        return prompt

    def _format_jd_requirements(self, parsed_jd: Dict[str, Any]) -> str:
        """Format JD requirements for keyword optimization.

        Args:
            parsed_jd: Parsed job description dict

        Returns:
            Formatted string with key requirements
        """
        lines = []

        if "requirements" in parsed_jd:
            reqs = parsed_jd["requirements"]
            if isinstance(reqs, dict):
                required = reqs.get("required", [])
                if required:
                    lines.append("Required Skills:")
                    for req in required[:8]:  # Top 8
                        lines.append(f"  - {req}")

        if "technologies" in parsed_jd and parsed_jd["technologies"]:
            tech_list = parsed_jd["technologies"][:12]  # Top 12
            lines.append(f"\nKey Technologies: {', '.join(tech_list)}")

        if "responsibilities" in parsed_jd and parsed_jd["responsibilities"]:
            resp_list = parsed_jd["responsibilities"][:5]  # Top 5
            lines.append("\nKey Responsibilities:")
            for resp in resp_list:
                lines.append(f"  - {resp}")

        return "\n".join(lines) if lines else "No specific requirements available"

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
        elif isinstance(evaluation, dict):
            score = evaluation.get("score", 0.0)
            issue_count = evaluation.get("issue_count", 0)
        else:
            score = 0.0
            issue_count = 0

        return {
            "draft_length": len(input_data.get("draft", "")),
            "job_title": parsed_jd.get("job_title", "unknown"),
            "current_score": score,
            "issue_count": issue_count,
            "has_best_practices": bool(input_data.get("best_practices"))
        }

    def _get_output_summary(self, output_data: str) -> Dict[str, Any]:
        """Create summary of output data for logging.

        Args:
            output_data: Polished draft content

        Returns:
            Dictionary with output summary information
        """
        if isinstance(output_data, dict) and output_data.get("instruction") == "CALL_TASK_TOOL":
            return {
                "type": "task_instruction",
                "current_score": output_data.get("current_score", 0.0),
                "draft_length": output_data.get("draft_length", 0),
                "status": "pending_execution"
            }

        draft_length = len(output_data) if isinstance(output_data, str) else 0
        word_count = len(output_data.split()) if isinstance(output_data, str) else 0

        return {
            "type": "polished_draft",
            "character_count": draft_length,
            "word_count": word_count,
            "line_count": output_data.count('\n') if isinstance(output_data, str) else 0
        }
