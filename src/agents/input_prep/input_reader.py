"""InputReader agent for reading input files from the file system.

This agent reads all required input files for the resume/cover letter tailoring
workflow, including best practices guidelines, master resume, and company culture
reports.
"""

import logging
from pathlib import Path
from typing import Dict, List

import aiofiles

from ..base_agent import BaseAgent


class InputReader(BaseAgent[Dict[str, str], Dict[str, str]]):
    """Agent that reads all input files required for the tailoring workflow.

    This agent reads multiple input documents from specified file paths and
    returns their contents organized by file type/category. It handles:
    - Resume best practices guidelines
    - Cover letter best practices guidelines
    - Master resume document
    - Company culture research reports

    Input Format:
        Dict with keys as file type identifiers and values as file paths:
        {
            "resume_best_practices": "/path/to/resume_bp.md",
            "cover_letter_best_practices": "/path/to/cl_bp.md",
            "master_resume": "/path/to/master_resume.tex",
            "company_culture": "/path/to/culture_report.md"
        }

    Output Format:
        Dict with same keys but values as file contents:
        {
            "resume_best_practices": "# Resume Best Practices\n...",
            "cover_letter_best_practices": "# Cover Letter Tips\n...",
            "master_resume": "\\documentclass{article}\n...",
            "company_culture": "# Company Culture Report\n..."
        }

    Example:
        >>> state_mgr = StateManager(Path("./run_001"))
        >>> agent = InputReader(state_mgr, "input_preparation")
        >>> input_paths = {
        ...     "resume_best_practices": "./data/resume_bp.md",
        ...     "master_resume": "./data/resume.tex"
        ... }
        >>> result = await agent.run(input_paths)
        >>> print(result["resume_best_practices"][:50])
        # Resume Best Practices for ATS Optimization...
    """

    # Required file type keys
    REQUIRED_KEYS = {
        "resume_best_practices",
        "cover_letter_best_practices",
        "master_resume",
        "company_culture"
    }

    @property
    def agent_name(self) -> str:
        """Unique identifier for this agent type.

        Returns:
            Agent name string
        """
        return "input_reader"

    @property
    def agent_type(self) -> str:
        """Claude Code subagent type to use for this agent.

        Returns:
            Subagent type string
        """
        return "general-purpose"

    async def validate_input(self, input_data: Dict[str, str]) -> bool:
        """Validate input data contains all required file paths.

        Checks that:
        1. Input is a dictionary
        2. All required keys are present
        3. All values are non-empty strings
        4. All paths point to existing files

        Args:
            input_data: Dict mapping file types to file paths

        Returns:
            True if input is valid, False otherwise
        """
        # Check type
        if not isinstance(input_data, dict):
            self.logger.error(f"Input must be dict, got {type(input_data)}")
            return False

        # Check required keys
        missing_keys = self.REQUIRED_KEYS - set(input_data.keys())
        if missing_keys:
            self.logger.error(
                f"Missing required keys: {missing_keys}. "
                f"Required: {self.REQUIRED_KEYS}"
            )
            return False

        # Check all values are non-empty strings
        for key, value in input_data.items():
            if not isinstance(value, str) or not value.strip():
                self.logger.error(
                    f"Value for key '{key}' must be non-empty string, got: {value}"
                )
                return False

        # Check all paths exist
        for key, path_str in input_data.items():
            path = Path(path_str)
            if not path.exists():
                self.logger.error(f"File not found for '{key}': {path}")
                return False
            if not path.is_file():
                self.logger.error(f"Path for '{key}' is not a file: {path}")
                return False

        self.logger.info(
            f"Input validation passed: {len(input_data)} files to read"
        )
        return True

    async def execute(self, input_data: Dict[str, str]) -> Dict[str, str]:
        """Read all input files from the file system.

        Reads each file specified in input_data and stores its contents
        in the output dictionary with the same key.

        Args:
            input_data: Dict mapping file types to file paths

        Returns:
            Dict mapping file types to file contents

        Raises:
            IOError: If any file read operation fails
        """
        results: Dict[str, str] = {}

        for key, path_str in input_data.items():
            path = Path(path_str)

            try:
                self.logger.debug(f"Reading file for '{key}': {path}")

                async with aiofiles.open(path, 'r', encoding='utf-8') as f:
                    content = await f.read()

                results[key] = content

                # Log file size for debugging
                file_size = len(content)
                self.logger.info(
                    f"Successfully read '{key}': {file_size} characters from {path.name}"
                )

            except Exception as e:
                self.logger.error(
                    f"Failed to read file for '{key}' at {path}: {e}",
                    exc_info=True
                )
                raise IOError(
                    f"Failed to read {key} from {path}: {e}"
                ) from e

        self.logger.info(
            f"Successfully read all {len(results)} input files"
        )
        return results

    async def format_output(self, raw_output: Dict[str, str]) -> Dict[str, str]:
        """Format the raw file contents output.

        For InputReader, the raw output is already in the desired format
        (dict of file contents), so this is a pass-through operation.
        We just add some summary metadata to logs.

        Args:
            raw_output: Dict mapping file types to file contents

        Returns:
            Same dict as raw_output
        """
        # Calculate total content size
        total_chars = sum(len(content) for content in raw_output.values())

        self.logger.info(
            f"Formatted output: {len(raw_output)} documents, "
            f"{total_chars:,} total characters"
        )

        # Log individual document sizes
        for key, content in raw_output.items():
            self.logger.debug(
                f"  - {key}: {len(content):,} characters"
            )

        return raw_output

    def _get_input_summary(self, input_data: Dict[str, str]) -> Dict[str, any]:
        """Create summary of input data for logging.

        Args:
            input_data: Input data to summarize

        Returns:
            Dictionary with input summary information
        """
        return {
            "file_types": list(input_data.keys()),
            "file_count": len(input_data),
            "file_paths": [Path(p).name for p in input_data.values()]
        }

    def _get_output_summary(self, output_data: Dict[str, str]) -> Dict[str, any]:
        """Create summary of output data for logging.

        Args:
            output_data: Output data to summarize

        Returns:
            Dictionary with output summary information
        """
        total_chars = sum(len(content) for content in output_data.values())

        return {
            "file_types": list(output_data.keys()),
            "file_count": len(output_data),
            "total_characters": total_chars,
            "individual_sizes": {
                key: len(content) for key, content in output_data.items()
            }
        }
