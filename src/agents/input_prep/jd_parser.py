"""JDParser agent for parsing raw job descriptions into structured format.

This agent parses raw job description HTML/text into a structured format
containing extracted fields like job title, company, requirements, qualifications,
responsibilities, etc. Multiple instances can run in parallel.
"""

import logging
from typing import Dict, Any, List, Optional

from ..base_agent import BaseAgent


class JDParser(BaseAgent[str, Dict[str, Any]]):
    """Agent that parses raw job descriptions into structured format.

    This agent uses Claude Code's Task tool with LLM capabilities to intelligently
    parse job description content and extract key information into a structured
    format suitable for downstream matching and tailoring agents.

    Input Format:
        Raw job description text/HTML string:
        "<html><body><h1>Software Engineer</h1>...</body></html>"

    Output Format:
        Dict with parsed and structured fields:
        {
            "job_title": "Senior Software Engineer",
            "company": "TechCorp Inc.",
            "location": "San Francisco, CA (Remote)",
            "job_type": "Full-time",
            "salary_range": "$120k - $180k",
            "requirements": {
                "required": [
                    "5+ years Python development",
                    "Experience with distributed systems"
                ],
                "preferred": [
                    "AWS/GCP experience",
                    "Open source contributions"
                ]
            },
            "responsibilities": [
                "Design and implement scalable backend services",
                "Mentor junior engineers"
            ],
            "qualifications": [
                "BS in Computer Science or equivalent",
                "Strong communication skills"
            ],
            "technologies": [
                "Python", "Django", "PostgreSQL", "Docker", "Kubernetes"
            ],
            "benefits": [
                "Health insurance",
                "401k matching",
                "Flexible work hours"
            ],
            "company_description": "TechCorp is a leading...",
            "application_instructions": "Apply via our careers page...",
            "raw_text": "... original text for reference ..."
        }

    Example:
        >>> state_mgr = StateManager(Path("./run_001"))
        >>> agent = JDParser(state_mgr, "input_preparation")
        >>> raw_jd = "<html>... job description HTML ...</html>"
        >>> result = await agent.run(raw_jd)
        >>> print(result["job_title"])
        Senior Software Engineer
    """

    @property
    def agent_name(self) -> str:
        """Unique identifier for this agent type.

        Returns:
            Agent name string
        """
        return "jd_parser"

    @property
    def agent_type(self) -> str:
        """Claude Code subagent type to use for this agent.

        Returns:
            Subagent type string
        """
        return "general-purpose"

    async def validate_input(self, input_data: str) -> bool:
        """Validate input is a non-empty string.

        Checks that:
        1. Input is a string
        2. Input has sufficient content (at least 100 characters)

        Args:
            input_data: Raw job description text to validate

        Returns:
            True if input is valid, False otherwise
        """
        # Check type
        if not isinstance(input_data, str):
            self.logger.error(f"Input must be string, got {type(input_data)}")
            return False

        # Check non-empty and minimum length
        content = input_data.strip()
        if len(content) < 100:
            self.logger.error(
                f"Input content too short ({len(content)} chars). "
                "Expected at least 100 characters for a valid job description."
            )
            return False

        self.logger.info(
            f"Input validation passed: {len(content)} characters of JD content"
        )
        return True

    async def execute(self, input_data: str) -> Dict[str, Any]:
        """Parse raw job description into structured format.

        This method uses Claude Code's Task tool to leverage LLM capabilities
        for intelligent parsing and extraction of job description fields.

        Args:
            input_data: Raw job description text/HTML

        Returns:
            Dict containing task instruction for parsing

        Raises:
            RuntimeError: If parsing fails
        """
        raw_content = input_data.strip()

        self.logger.info(
            f"Parsing job description ({len(raw_content)} characters)"
        )

        # Build prompt for Task tool to parse JD
        prompt = self._build_parsing_prompt(raw_content)

        # Task tool invocation structure (for documentation):
        # The actual Task tool call would be made by the orchestrator
        task_instruction = {
            "instruction": "CALL_TASK_TOOL",
            "agent_type": self.agent_type,
            "prompt": prompt,
            "raw_content_length": len(raw_content)
        }

        self.logger.info(
            f"Generated parsing instruction for {len(raw_content)} chars of content"
        )

        return task_instruction

    async def format_output(self, raw_output: Dict[str, Any]) -> Dict[str, Any]:
        """Format the raw parsing output into final structured result.

        Args:
            raw_output: Raw output from execute() or Task tool

        Returns:
            Formatted dict with parsed JD fields
        """
        # If this is a task instruction (pre-execution), pass it through
        if raw_output.get("instruction") == "CALL_TASK_TOOL":
            self.logger.debug(
                "Output is task instruction (pre-execution), passing through"
            )
            return raw_output

        # Otherwise, validate and format the parsed structure
        # Expected structure from Task tool should already match our output schema

        # Ensure all expected top-level keys exist with defaults
        formatted = {
            "job_title": raw_output.get("job_title", "Unknown Position"),
            "company": raw_output.get("company", "Unknown Company"),
            "location": raw_output.get("location", ""),
            "job_type": raw_output.get("job_type", ""),
            "salary_range": raw_output.get("salary_range", ""),
            "requirements": raw_output.get("requirements", {
                "required": [],
                "preferred": []
            }),
            "responsibilities": raw_output.get("responsibilities", []),
            "qualifications": raw_output.get("qualifications", []),
            "technologies": raw_output.get("technologies", []),
            "benefits": raw_output.get("benefits", []),
            "company_description": raw_output.get("company_description", ""),
            "application_instructions": raw_output.get("application_instructions", ""),
            "raw_text": raw_output.get("raw_text", "")
        }

        # Validate requirements structure
        if not isinstance(formatted["requirements"], dict):
            formatted["requirements"] = {"required": [], "preferred": []}
        if "required" not in formatted["requirements"]:
            formatted["requirements"]["required"] = []
        if "preferred" not in formatted["requirements"]:
            formatted["requirements"]["preferred"] = []

        self.logger.info(
            f"Formatted parsed JD: {formatted['job_title']} at {formatted['company']}"
        )

        return formatted

    def _build_parsing_prompt(self, raw_content: str) -> str:
        """Build prompt for Task tool to parse job description.

        Args:
            raw_content: Raw job description content

        Returns:
            Formatted prompt string for Task tool
        """
        # Truncate very long content for prompt (keep first 20k chars)
        content_for_prompt = raw_content[:20000]
        if len(raw_content) > 20000:
            content_for_prompt += "\n\n[... content truncated ...]"

        prompt = f"""Parse the following job description and extract key information into a structured JSON format.

JOB DESCRIPTION CONTENT:
{content_for_prompt}

INSTRUCTIONS:
Parse the above job description and extract the following information:

1. **job_title**: The job position title (string)
2. **company**: Company name (string)
3. **location**: Job location including remote/hybrid info (string)
4. **job_type**: Employment type (Full-time, Part-time, Contract, etc.) (string)
5. **salary_range**: Salary or compensation range if mentioned (string)
6. **requirements**: Object with two arrays:
   - required: List of required qualifications/skills (array of strings)
   - preferred: List of preferred/nice-to-have qualifications (array of strings)
7. **responsibilities**: Main job duties and responsibilities (array of strings)
8. **qualifications**: Educational and experience qualifications (array of strings)
9. **technologies**: Technologies, tools, frameworks mentioned (array of strings)
10. **benefits**: Benefits and perks offered (array of strings)
11. **company_description**: Brief company description if provided (string)
12. **application_instructions**: How to apply or special instructions (string)
13. **raw_text**: Clean text version of the JD without HTML tags (string)

IMPORTANT:
- Extract as much information as possible from the content
- If a field is not found, use appropriate empty value (empty string or empty array)
- For requirements, distinguish between "required" and "preferred/nice-to-have"
- Extract specific technologies and tools mentioned
- Clean up HTML tags from text content
- Be thorough and capture all relevant details

Return ONLY a valid JSON object with the structure described above. Do not include any markdown formatting or code blocks.
"""

        return prompt

    def _get_input_summary(self, input_data: str) -> Dict[str, Any]:
        """Create summary of input data for logging.

        Args:
            input_data: Raw JD content

        Returns:
            Dictionary with input summary information
        """
        content = input_data.strip()

        # Count common indicators to assess content type
        has_html = "<html" in content.lower() or "<body" in content.lower()
        line_count = len(content.split('\n'))

        return {
            "content_length": len(content),
            "line_count": line_count,
            "is_html": has_html,
            "first_100_chars": content[:100] + "..." if len(content) > 100 else content
        }

    def _get_output_summary(self, output_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create summary of output data for logging.

        Args:
            output_data: Parsed JD data

        Returns:
            Dictionary with output summary information
        """
        # Check if this is a task instruction or actual result
        if output_data.get("instruction") == "CALL_TASK_TOOL":
            return {
                "type": "task_instruction",
                "content_length": output_data.get("raw_content_length", 0),
                "status": "pending_execution"
            }

        # Summarize parsed fields
        requirements = output_data.get("requirements", {})
        required_count = len(requirements.get("required", []))
        preferred_count = len(requirements.get("preferred", []))

        return {
            "type": "parsed_result",
            "job_title": output_data.get("job_title", "unknown"),
            "company": output_data.get("company", "unknown"),
            "location": output_data.get("location", "unknown"),
            "required_skills_count": required_count,
            "preferred_skills_count": preferred_count,
            "responsibilities_count": len(output_data.get("responsibilities", [])),
            "technologies_count": len(output_data.get("technologies", [])),
            "has_salary": bool(output_data.get("salary_range", "").strip())
        }
