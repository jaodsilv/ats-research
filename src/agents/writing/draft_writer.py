"""DraftWriter agent for creating initial resume/cover letter drafts.

This agent generates the first draft of a tailored resume or cover letter based on
master resume content, parsed job description, company culture research, best practices,
and skills gap analysis.
"""

import logging
from typing import Dict, Any

from ..base_agent import BaseAgent


class DraftWriter(BaseAgent[Dict[str, Any], str]):
    """Agent that writes initial resume/cover letter drafts.

    This agent leverages Claude Code's Task tool to generate high-quality initial
    drafts that are tailored to the specific job description while maintaining
    factual accuracy based on the master resume.

    Input Format:
        Dict with keys:
        {
            "master_resume": str,              # Master resume content
            "parsed_jd": dict,                 # Parsed job description structure
            "company_culture": str,            # Company culture research
            "best_practices": str,             # Resume/cover letter best practices
            "skills_gap_analysis": dict,       # Skills gap analysis results
            "document_type": str               # "resume" or "cover_letter"
        }

    Output Format:
        str: Draft document content (Markdown or LaTeX format)

    Example:
        >>> state_mgr = StateManager(Path("./run_001"))
        >>> agent = DraftWriter(state_mgr, "draft_writing")
        >>> input_data = {
        ...     "master_resume": "# John Doe\\n...",
        ...     "parsed_jd": {"job_title": "Senior Engineer", ...},
        ...     "company_culture": "Tech-forward, collaborative...",
        ...     "best_practices": "Use action verbs...",
        ...     "skills_gap_analysis": {"matched": [...], "missing": [...]},
        ...     "document_type": "resume"
        ... }
        >>> draft = await agent.run(input_data)
    """

    @property
    def agent_name(self) -> str:
        """Unique identifier for this agent type.

        Returns:
            Agent name string
        """
        return "draft_writer"

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
        2. Required keys exist: master_resume, parsed_jd, document_type
        3. Master resume is non-empty string
        4. Parsed JD is a dict with job_title
        5. Document type is valid

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
        required_keys = ["master_resume", "parsed_jd", "document_type"]
        missing_keys = [k for k in required_keys if k not in input_data]
        if missing_keys:
            self.logger.error(f"Missing required keys: {missing_keys}")
            return False

        # Validate master resume
        master_resume = input_data.get("master_resume", "")
        if not isinstance(master_resume, str) or len(master_resume.strip()) < 100:
            self.logger.error("master_resume must be non-empty string (min 100 chars)")
            return False

        # Validate parsed JD
        parsed_jd = input_data.get("parsed_jd", {})
        if not isinstance(parsed_jd, dict) or "job_title" not in parsed_jd:
            self.logger.error("parsed_jd must be dict with 'job_title' key")
            return False

        # Validate document type
        doc_type = input_data.get("document_type", "")
        if doc_type not in ["resume", "cover_letter"]:
            self.logger.error(f"document_type must be 'resume' or 'cover_letter', got '{doc_type}'")
            return False

        self.logger.info(
            f"Input validation passed: {doc_type} for {parsed_jd.get('job_title', 'unknown')}"
        )
        return True

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate initial draft using Claude Code Task tool.

        Args:
            input_data: Validated input data with all context

        Returns:
            Dict with task instruction for draft generation

        Raises:
            RuntimeError: If draft generation fails
        """
        doc_type = input_data["document_type"]
        job_title = input_data["parsed_jd"].get("job_title", "Unknown Position")

        self.logger.info(f"Generating {doc_type} draft for {job_title}")

        # Build prompt for Task tool
        prompt = self._build_draft_prompt(input_data)

        # Task tool invocation structure
        task_instruction = {
            "instruction": "CALL_TASK_TOOL",
            "agent_type": self.agent_type,
            "prompt": prompt,
            "document_type": doc_type,
            "job_title": job_title
        }

        self.logger.info(f"Generated draft writing instruction for {doc_type}")

        return task_instruction

    async def format_output(self, raw_output: Any) -> str:
        """Format the raw draft output into final string.

        Args:
            raw_output: Raw output from execute() or Task tool

        Returns:
            Draft content as string
        """
        # If this is a task instruction (pre-execution), return as-is
        if isinstance(raw_output, dict) and raw_output.get("instruction") == "CALL_TASK_TOOL":
            self.logger.debug("Output is task instruction (pre-execution), passing through")
            return raw_output

        # Otherwise, ensure we have a string
        if isinstance(raw_output, str):
            draft = raw_output.strip()
        elif isinstance(raw_output, dict) and "draft" in raw_output:
            draft = raw_output["draft"].strip()
        else:
            draft = str(raw_output).strip()

        if len(draft) < 50:
            self.logger.warning(f"Draft seems too short: {len(draft)} characters")

        self.logger.info(f"Formatted draft: {len(draft)} characters")

        return draft

    def _build_draft_prompt(self, input_data: Dict[str, Any]) -> str:
        """Build prompt for Task tool to generate draft.

        Args:
            input_data: Input data with all context

        Returns:
            Formatted prompt string for Task tool
        """
        doc_type = input_data["document_type"]
        master_resume = input_data["master_resume"]
        parsed_jd = input_data["parsed_jd"]
        company_culture = input_data.get("company_culture", "")
        best_practices = input_data.get("best_practices", "")
        skills_gap = input_data.get("skills_gap_analysis", {})

        job_title = parsed_jd.get("job_title", "Unknown Position")
        company = parsed_jd.get("company", "Unknown Company")

        prompt = f"""Write an initial draft {doc_type} tailored for the following job posting.

JOB DETAILS:
- Title: {job_title}
- Company: {company}
- Location: {parsed_jd.get('location', 'N/A')}

MASTER RESUME (SOURCE OF TRUTH - USE ONLY FACTUAL INFORMATION FROM HERE):
{master_resume}

PARSED JOB DESCRIPTION:
{self._format_jd_for_prompt(parsed_jd)}

"""

        if company_culture:
            prompt += f"""COMPANY CULTURE RESEARCH:
{company_culture}

"""

        if best_practices:
            prompt += f"""BEST PRACTICES:
{best_practices}

"""

        if skills_gap:
            prompt += f"""SKILLS GAP ANALYSIS:
Matched Skills: {', '.join(skills_gap.get('matched', []))}
Missing Skills: {', '.join(skills_gap.get('missing', []))}

"""

        if doc_type == "resume":
            prompt += """INSTRUCTIONS FOR RESUME DRAFT:
1. Create a tailored resume in Markdown format
2. Highlight experiences and skills that match the job requirements
3. Use ONLY factual information from the master resume - DO NOT fabricate
4. Emphasize relevant technologies and accomplishments
5. Structure sections to align with job posting priorities
6. Use strong action verbs and quantifiable achievements
7. Optimize for ATS keyword matching based on the job description
8. Keep the resume concise and targeted (1-2 pages equivalent)

Return ONLY the resume draft in Markdown format. Do not include explanations or metadata.
"""
        else:  # cover_letter
            prompt += """INSTRUCTIONS FOR COVER LETTER DRAFT:
1. Create a professional cover letter in Markdown format
2. Opening: Express enthusiasm and explain why you're interested in the role
3. Body: Highlight 2-3 key experiences/achievements that match job requirements
4. Use ONLY factual information from the master resume - DO NOT fabricate
5. Show understanding of company culture and values
6. Demonstrate how your background solves their needs
7. Closing: Call to action and express eagerness to discuss further
8. Keep concise (3-4 paragraphs, ~300-400 words)

Return ONLY the cover letter draft in Markdown format. Do not include explanations or metadata.
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
            lines.append(f"Job Title: {parsed_jd['job_title']}")
        if "company" in parsed_jd:
            lines.append(f"Company: {parsed_jd['company']}")

        if "requirements" in parsed_jd:
            reqs = parsed_jd["requirements"]
            if isinstance(reqs, dict):
                if reqs.get("required"):
                    lines.append("\nRequired Qualifications:")
                    for req in reqs["required"]:
                        lines.append(f"  - {req}")
                if reqs.get("preferred"):
                    lines.append("\nPreferred Qualifications:")
                    for pref in reqs["preferred"]:
                        lines.append(f"  - {pref}")

        if "responsibilities" in parsed_jd and parsed_jd["responsibilities"]:
            lines.append("\nKey Responsibilities:")
            for resp in parsed_jd["responsibilities"]:
                lines.append(f"  - {resp}")

        if "technologies" in parsed_jd and parsed_jd["technologies"]:
            lines.append(f"\nTechnologies: {', '.join(parsed_jd['technologies'])}")

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
            "document_type": input_data.get("document_type", "unknown"),
            "job_title": parsed_jd.get("job_title", "unknown"),
            "company": parsed_jd.get("company", "unknown"),
            "master_resume_length": len(input_data.get("master_resume", "")),
            "has_company_culture": bool(input_data.get("company_culture")),
            "has_best_practices": bool(input_data.get("best_practices")),
            "has_skills_gap": bool(input_data.get("skills_gap_analysis"))
        }

    def _get_output_summary(self, output_data: str) -> Dict[str, Any]:
        """Create summary of output data for logging.

        Args:
            output_data: Draft content

        Returns:
            Dictionary with output summary information
        """
        if isinstance(output_data, dict) and output_data.get("instruction") == "CALL_TASK_TOOL":
            return {
                "type": "task_instruction",
                "document_type": output_data.get("document_type", "unknown"),
                "job_title": output_data.get("job_title", "unknown"),
                "status": "pending_execution"
            }

        draft_length = len(output_data) if isinstance(output_data, str) else 0
        word_count = len(output_data.split()) if isinstance(output_data, str) else 0

        return {
            "type": "draft",
            "character_count": draft_length,
            "word_count": word_count,
            "line_count": output_data.count('\n') if isinstance(output_data, str) else 0
        }
