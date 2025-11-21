"""DocumentFetcher agent for fetching job descriptions from URLs.

This agent fetches raw job description content from job posting URLs using
web scraping capabilities. Multiple instances can run in parallel to fetch
multiple job descriptions concurrently.
"""

import logging
from typing import Dict, Any
from urllib.parse import urlparse

from ..base_agent import BaseAgent


class DocumentFetcher(BaseAgent[str, Dict[str, str]]):
    """Agent that fetches raw job description content from a URL.

    This agent uses Claude Code's WebFetch tool (or similar capabilities) to
    retrieve the HTML/text content of a job posting from a URL. It's designed
    to be instantiated multiple times in parallel for fetching multiple job
    descriptions simultaneously.

    Input Format:
        Single URL string:
        "https://jobs.example.com/posting/12345"

    Output Format:
        Dict with URL and fetched content:
        {
            "url": "https://jobs.example.com/posting/12345",
            "raw_content": "<html>...</html>",
            "fetch_timestamp": "2025-10-20T14:30:00Z",
            "content_length": 15234
        }

    Example:
        >>> state_mgr = StateManager(Path("./run_001"))
        >>> agent = DocumentFetcher(state_mgr, "input_preparation")
        >>> url = "https://jobs.company.com/software-engineer"
        >>> result = await agent.run(url)
        >>> print(result["content_length"])
        15234
    """

    @property
    def agent_name(self) -> str:
        """Unique identifier for this agent type.

        Returns:
            Agent name string
        """
        return "document_fetcher"

    @property
    def agent_type(self) -> str:
        """Claude Code subagent type to use for this agent.

        Returns:
            Subagent type string
        """
        return "general-purpose"

    async def validate_input(self, input_data: str) -> bool:
        """Validate input is a valid URL string.

        Checks that:
        1. Input is a string
        2. Input is non-empty
        3. Input has valid URL format with scheme and netloc

        Args:
            input_data: URL string to validate

        Returns:
            True if input is valid, False otherwise
        """
        # Check type
        if not isinstance(input_data, str):
            self.logger.error(f"Input must be string, got {type(input_data)}")
            return False

        # Check non-empty
        if not input_data.strip():
            self.logger.error("Input URL string is empty")
            return False

        # Check URL format
        try:
            parsed = urlparse(input_data.strip())

            # Must have scheme (http/https) and network location
            if not parsed.scheme:
                self.logger.error(f"URL missing scheme: {input_data}")
                return False

            if not parsed.netloc:
                self.logger.error(f"URL missing network location: {input_data}")
                return False

            # Prefer https but allow http
            if parsed.scheme not in ('http', 'https'):
                self.logger.error(
                    f"URL scheme must be http or https, got: {parsed.scheme}"
                )
                return False

            self.logger.info(f"Input validation passed for URL: {input_data}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to parse URL '{input_data}': {e}")
            return False

    async def execute(self, input_data: str) -> Dict[str, Any]:
        """Fetch raw job description content from URL.

        This method uses Claude Code's Task tool to leverage the WebFetch
        capability for retrieving web content. The Task tool is invoked
        with a prompt that instructs it to fetch the URL content.

        Args:
            input_data: URL string to fetch

        Returns:
            Dict containing URL, raw content, timestamp, and metadata

        Raises:
            RuntimeError: If web fetch fails
        """
        url = input_data.strip()

        self.logger.info(f"Fetching job description from: {url}")

        # Build prompt for Task tool to use WebFetch
        prompt = self._build_fetch_prompt(url)

        # NOTE: In actual implementation, this would call Claude Code's Task tool
        # For now, we'll create a placeholder that documents the expected behavior
        # The actual Task tool invocation would be handled by the orchestrator
        # that calls this agent through Claude Code's environment

        # Simulated Task tool invocation structure (for documentation):
        # task_result = await self.invoke_task_tool(
        #     agent_type=self.agent_type,
        #     prompt=prompt
        # )

        # For this implementation, we'll return a structure that indicates
        # this agent expects the Task tool to be called with the prompt
        task_instruction = {
            "instruction": "CALL_TASK_TOOL",
            "agent_type": self.agent_type,
            "prompt": prompt,
            "url": url
        }

        self.logger.info(
            f"Generated fetch instruction for URL: {url}"
        )

        return task_instruction

    async def format_output(self, raw_output: Dict[str, Any]) -> Dict[str, str]:
        """Format the raw fetch output into structured result.

        When the Task tool actually executes, it will return the fetched content.
        This method structures that content with metadata.

        Args:
            raw_output: Raw output from execute() or Task tool

        Returns:
            Formatted dict with URL, content, and metadata
        """
        from datetime import datetime

        # If this is a task instruction (pre-execution), pass it through
        if raw_output.get("instruction") == "CALL_TASK_TOOL":
            self.logger.debug(
                "Output is task instruction (pre-execution), passing through"
            )
            return raw_output

        # Otherwise, format actual fetched content
        # Expected structure from Task tool:
        # {
        #     "url": "...",
        #     "content": "...",
        #     "status_code": 200,
        #     ...
        # }

        url = raw_output.get("url", "unknown")
        content = raw_output.get("content", "")

        formatted = {
            "url": url,
            "raw_content": content,
            "fetch_timestamp": datetime.utcnow().isoformat() + "Z",
            "content_length": len(content),
            "status_code": raw_output.get("status_code", 0)
        }

        self.logger.info(
            f"Formatted fetch result: {formatted['content_length']} bytes from {url}"
        )

        return formatted

    def _build_fetch_prompt(self, url: str) -> str:
        """Build prompt for Task tool to fetch URL content.

        Args:
            url: URL to fetch

        Returns:
            Formatted prompt string for Task tool
        """
        prompt = f"""Fetch the job description from the following URL and return the raw HTML/text content.

URL: {url}

Instructions:
1. Use the WebFetch tool to retrieve the content from this URL
2. Extract the complete HTML content
3. Return the raw content without any modifications
4. Include any error messages if the fetch fails

Expected output format:
{{
    "url": "{url}",
    "content": "... raw HTML/text content ...",
    "status_code": 200,
    "error": null
}}
"""

        return prompt

    def _get_input_summary(self, input_data: str) -> Dict[str, Any]:
        """Create summary of input data for logging.

        Args:
            input_data: URL string

        Returns:
            Dictionary with input summary information
        """
        parsed = urlparse(input_data)

        return {
            "url": input_data,
            "domain": parsed.netloc,
            "scheme": parsed.scheme,
            "path": parsed.path
        }

    def _get_output_summary(self, output_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create summary of output data for logging.

        Args:
            output_data: Output data to summarize

        Returns:
            Dictionary with output summary information
        """
        # Check if this is a task instruction or actual result
        if output_data.get("instruction") == "CALL_TASK_TOOL":
            return {
                "type": "task_instruction",
                "url": output_data.get("url", "unknown"),
                "status": "pending_execution"
            }

        return {
            "type": "fetch_result",
            "url": output_data.get("url", "unknown"),
            "content_length": output_data.get("content_length", 0),
            "status_code": output_data.get("status_code", 0),
            "timestamp": output_data.get("fetch_timestamp", "unknown")
        }
