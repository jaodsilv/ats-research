"""ResumeJDMatcher agent for matching resumes against job descriptions.

This agent analyzes how well a resume matches a job description, performs skills gap
analysis, and provides recommendations. Multiple instances run in parallel, one per JD.
"""

import logging
from typing import Dict, Any

from ..base_agent import BaseAgent
from ...decisions.decision_logic import MatchResult


class ResumeJDMatcher(BaseAgent[Dict[str, Any], MatchResult]):
    """Agent that matches a resume against a job description with skills gap analysis.

    This agent uses Claude Code's Task tool with LLM capabilities to intelligently
    compare a resume against a parsed job description, identify matched keywords,
    find missing skills, calculate match scores, and provide recommendations.

    Multiple instances run in parallel (one per job description) to efficiently
    process multiple JD matching tasks.

    Input Format:
        Dict with the following keys:
        {
            "master_resume": str,           # Full resume content
            "parsed_jd": dict,              # Parsed job description from JDParser
            "company_culture": str          # Company culture research report
        }

    Output Format:
        MatchResult dataclass with:
        {
            "jd_id": str,                   # Unique identifier for the JD
            "match_score": float,           # Overall match score (0.0-1.0)
            "relevance_score": float,       # Relevance score (0.0-1.0)
            "matched_keywords": List[str],  # Keywords found in both
            "missing_skills": List[str],    # Required skills not in resume
            "recommendation": str           # Human-readable recommendation
        }

    Example:
        >>> state_mgr = StateManager(Path("./run_001"))
        >>> agent = ResumeJDMatcher(state_mgr, "jd_matching")
        >>> input_data = {
        ...     "master_resume": "John Doe\\nSoftware Engineer\\n...",
        ...     "parsed_jd": {
        ...         "job_title": "Senior Python Engineer",
        ...         "requirements": {"required": [...], "preferred": [...]},
        ...         ...
        ...     },
        ...     "company_culture": "Company values innovation..."
        ... }
        >>> result = await agent.run(input_data)
        >>> print(f"Match score: {result.match_score:.2f}")
        Match score: 0.78
    """

    @property
    def agent_name(self) -> str:
        """Unique identifier for this agent type.

        Returns:
            Agent name string
        """
        return "resume_jd_matcher"

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
        2. Contains 'master_resume' (non-empty string)
        3. Contains 'parsed_jd' (dict with required structure)
        4. Contains 'company_culture' (string, can be empty)

        Args:
            input_data: Input dict to validate

        Returns:
            True if input is valid, False otherwise
        """
        # Check type
        if not isinstance(input_data, dict):
            self.logger.error(f"Input must be dict, got {type(input_data)}")
            return False

        # Check required keys
        required_keys = ["master_resume", "parsed_jd", "company_culture"]
        for key in required_keys:
            if key not in input_data:
                self.logger.error(f"Missing required key: {key}")
                return False

        # Validate master_resume
        resume = input_data.get("master_resume", "")
        if not isinstance(resume, str) or len(resume.strip()) < 100:
            self.logger.error(
                f"master_resume must be non-empty string (at least 100 chars), "
                f"got {len(resume.strip())} chars"
            )
            return False

        # Validate parsed_jd
        parsed_jd = input_data.get("parsed_jd", {})
        if not isinstance(parsed_jd, dict):
            self.logger.error(f"parsed_jd must be dict, got {type(parsed_jd)}")
            return False

        # Check for essential parsed_jd fields
        if "job_title" not in parsed_jd or "requirements" not in parsed_jd:
            self.logger.error(
                "parsed_jd missing essential fields (job_title, requirements)"
            )
            return False

        # Validate company_culture
        culture = input_data.get("company_culture", "")
        if not isinstance(culture, str):
            self.logger.error(
                f"company_culture must be string, got {type(culture)}"
            )
            return False

        self.logger.info(
            f"Input validation passed: resume={len(resume)} chars, "
            f"JD={parsed_jd.get('job_title', 'unknown')}"
        )
        return True

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Match resume against job description with skills gap analysis.

        This method uses Claude Code's Task tool to leverage LLM capabilities
        for intelligent resume-JD matching and gap analysis.

        Args:
            input_data: Dict with master_resume, parsed_jd, company_culture

        Returns:
            Dict containing task instruction for matching

        Raises:
            RuntimeError: If matching fails
        """
        resume = input_data["master_resume"].strip()
        parsed_jd = input_data["parsed_jd"]
        company_culture = input_data["company_culture"].strip()

        jd_title = parsed_jd.get("job_title", "Unknown Position")
        jd_company = parsed_jd.get("company", "Unknown Company")

        self.logger.info(
            f"Matching resume against: {jd_title} at {jd_company}"
        )

        # Build prompt for Task tool to perform matching
        prompt = self._build_matching_prompt(resume, parsed_jd, company_culture)

        # Task tool invocation structure (for documentation):
        # The actual Task tool call would be made by the orchestrator
        task_instruction = {
            "instruction": "CALL_TASK_TOOL",
            "agent_type": self.agent_type,
            "prompt": prompt,
            "jd_id": f"{jd_company}_{jd_title}".replace(" ", "_"),
            "resume_length": len(resume),
        }

        self.logger.info(
            f"Generated matching instruction for {jd_title}"
        )

        return task_instruction

    async def format_output(self, raw_output: Any) -> MatchResult:
        """Format the raw matching output into MatchResult dataclass.

        Args:
            raw_output: Raw output from execute() or Task tool

        Returns:
            MatchResult dataclass with match analysis
        """
        # If this is a task instruction (pre-execution), convert to placeholder result
        if isinstance(raw_output, dict) and raw_output.get("instruction") == "CALL_TASK_TOOL":
            self.logger.debug(
                "Output is task instruction (pre-execution), creating placeholder"
            )
            return MatchResult(
                jd_id=raw_output.get("jd_id", "unknown"),
                match_score=0.0,
                relevance_score=0.0,
                matched_keywords=[],
                missing_skills=[],
                recommendation="Pending execution"
            )

        # Otherwise, parse the actual matching result
        # Expected structure from Task tool should contain match data

        # Extract MatchResult fields with defaults
        jd_id = raw_output.get("jd_id", "unknown")
        match_score = float(raw_output.get("match_score", 0.0))
        relevance_score = float(raw_output.get("relevance_score", 0.0))
        matched_keywords = raw_output.get("matched_keywords", [])
        missing_skills = raw_output.get("missing_skills", [])
        recommendation = raw_output.get("recommendation", "No recommendation provided")

        # Validate score ranges
        match_score = max(0.0, min(1.0, match_score))
        relevance_score = max(0.0, min(1.0, relevance_score))

        # Ensure lists are actually lists
        if not isinstance(matched_keywords, list):
            matched_keywords = []
        if not isinstance(missing_skills, list):
            missing_skills = []

        result = MatchResult(
            jd_id=jd_id,
            match_score=match_score,
            relevance_score=relevance_score,
            matched_keywords=matched_keywords,
            missing_skills=missing_skills,
            recommendation=recommendation
        )

        self.logger.info(
            f"Formatted match result: {jd_id} - "
            f"match={match_score:.2f}, relevance={relevance_score:.2f}, "
            f"matched={len(matched_keywords)}, missing={len(missing_skills)}"
        )

        return result

    def _build_matching_prompt(
        self,
        resume: str,
        parsed_jd: Dict[str, Any],
        company_culture: str
    ) -> str:
        """Build prompt for Task tool to perform resume-JD matching.

        Args:
            resume: Master resume content
            parsed_jd: Parsed job description dict
            company_culture: Company culture research report

        Returns:
            Formatted prompt string for Task tool
        """
        # Extract key JD information
        jd_title = parsed_jd.get("job_title", "Unknown Position")
        jd_company = parsed_jd.get("company", "Unknown Company")
        jd_location = parsed_jd.get("location", "")

        required_skills = parsed_jd.get("requirements", {}).get("required", [])
        preferred_skills = parsed_jd.get("requirements", {}).get("preferred", [])
        technologies = parsed_jd.get("technologies", [])
        responsibilities = parsed_jd.get("responsibilities", [])

        # Format JD details for prompt
        required_skills_text = "\n".join(f"  - {skill}" for skill in required_skills)
        preferred_skills_text = "\n".join(f"  - {skill}" for skill in preferred_skills)
        technologies_text = ", ".join(technologies) if technologies else "Not specified"
        responsibilities_text = "\n".join(f"  - {resp}" for resp in responsibilities)

        # Truncate resume if very long (keep first 15k chars)
        resume_for_prompt = resume[:15000]
        if len(resume) > 15000:
            resume_for_prompt += "\n\n[... resume truncated ...]"

        # Truncate culture report if very long (keep first 5k chars)
        culture_for_prompt = company_culture[:5000] if company_culture else "No culture information provided"
        if len(company_culture) > 5000:
            culture_for_prompt += "\n\n[... culture report truncated ...]"

        prompt = f"""Analyze how well the following resume matches the job description and perform a skills gap analysis.

JOB DESCRIPTION DETAILS:
Position: {jd_title}
Company: {jd_company}
Location: {jd_location}

Required Skills:
{required_skills_text if required_skills_text else "  - Not specified"}

Preferred Skills:
{preferred_skills_text if preferred_skills_text else "  - Not specified"}

Technologies: {technologies_text}

Responsibilities:
{responsibilities_text if responsibilities_text else "  - Not specified"}

COMPANY CULTURE:
{culture_for_prompt}

RESUME CONTENT:
{resume_for_prompt}

INSTRUCTIONS:
Analyze the match between this resume and the job description. Provide:

1. **match_score** (float 0.0-1.0): Overall match quality considering:
   - How well resume skills align with required skills (weighted highest)
   - Coverage of preferred skills
   - Relevance of past experience to responsibilities
   - Cultural fit based on company culture report

2. **relevance_score** (float 0.0-1.0): How relevant the candidate's background is:
   - Industry/domain alignment
   - Role/position level match
   - Technology stack overlap
   - Career trajectory alignment

3. **matched_keywords** (array of strings): Keywords/skills found in BOTH resume and JD:
   - Include technologies, frameworks, methodologies
   - Include soft skills that match
   - Be specific (e.g., "Python 3.x" not just "Python")
   - Limit to top 20 most important matches

4. **missing_skills** (array of strings): Required skills NOT found in resume:
   - Focus on REQUIRED skills only (not preferred)
   - List specific technologies/skills that are gaps
   - Prioritize by importance to the role
   - Limit to top 15 most critical gaps

5. **recommendation** (string): Human-readable recommendation (2-4 sentences):
   - Should candidate apply? (Strong match / Good match / Fair match / Weak match)
   - Key strengths to highlight in tailored resume
   - Main gaps to address or downplay
   - Cultural fit assessment

SCORING GUIDELINES:
- 0.9-1.0: Excellent match - nearly all required skills, strong experience alignment
- 0.8-0.9: Strong match - most required skills, good experience fit
- 0.7-0.8: Good match - solid coverage of requirements, some gaps
- 0.6-0.7: Fair match - partial coverage, notable gaps but viable candidate
- 0.5-0.6: Weak match - many gaps, questionable fit
- Below 0.5: Poor match - major misalignment, not recommended

IMPORTANT:
- Be objective and thorough in your analysis
- Consider both technical skills AND soft skills/culture fit
- Focus on substance over keywords (e.g., "5 years Python" beats "mentioned Python once")
- Required skills should weigh more heavily than preferred skills
- Return ONLY a valid JSON object with this exact structure:

{{
  "jd_id": "{jd_company}_{jd_title}",
  "match_score": 0.0,
  "relevance_score": 0.0,
  "matched_keywords": [],
  "missing_skills": [],
  "recommendation": ""
}}

Do not include any markdown formatting or code blocks. Return only the JSON object.
"""

        return prompt

    def _serialize_output(self, output_data: MatchResult) -> Dict[str, Any]:
        """Convert MatchResult dataclass to JSON-serializable dict.

        Args:
            output_data: MatchResult to serialize

        Returns:
            JSON-serializable dictionary
        """
        return {
            "jd_id": output_data.jd_id,
            "match_score": output_data.match_score,
            "relevance_score": output_data.relevance_score,
            "matched_keywords": output_data.matched_keywords,
            "missing_skills": output_data.missing_skills,
            "recommendation": output_data.recommendation,
        }

    def _get_input_summary(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create summary of input data for logging.

        Args:
            input_data: Input data to summarize

        Returns:
            Dictionary with input summary information
        """
        resume = input_data.get("master_resume", "")
        parsed_jd = input_data.get("parsed_jd", {})
        culture = input_data.get("company_culture", "")

        return {
            "resume_length": len(resume),
            "jd_title": parsed_jd.get("job_title", "unknown"),
            "jd_company": parsed_jd.get("company", "unknown"),
            "required_skills_count": len(
                parsed_jd.get("requirements", {}).get("required", [])
            ),
            "preferred_skills_count": len(
                parsed_jd.get("requirements", {}).get("preferred", [])
            ),
            "has_culture_report": len(culture.strip()) > 0,
        }

    def _get_output_summary(self, output_data: MatchResult) -> Dict[str, Any]:
        """Create summary of output data for logging.

        Args:
            output_data: MatchResult to summarize

        Returns:
            Dictionary with output summary information
        """
        return {
            "jd_id": output_data.jd_id,
            "match_score": round(output_data.match_score, 3),
            "relevance_score": round(output_data.relevance_score, 3),
            "matched_keywords_count": len(output_data.matched_keywords),
            "missing_skills_count": len(output_data.missing_skills),
            "recommendation_length": len(output_data.recommendation),
        }
