"""TEXCompiler agent for compiling LaTeX files to PDF.

This agent compiles .tex files to PDF using pdflatex command via Bash tool.
"""

import logging
import subprocess
from typing import Dict, Any, List
from pathlib import Path
import tempfile
import os

from ..base_agent import BaseAgent


class TEXCompiler(BaseAgent[Dict[str, Any], Dict[str, Any]]):
    """Agent that compiles LaTeX files to PDF using pdflatex.

    This agent uses the Bash tool directly (not Task tool) to run pdflatex
    compilation. It handles temporary file creation, compilation errors,
    and cleanup.

    Input Format:
        Dict with keys:
        {
            "tex_content": str,              # LaTeX file content to compile
            "output_path": str               # Path where PDF should be saved
        }

    Output Format:
        Dict with keys:
        {
            "pdf_path": str,                 # Path to compiled PDF file
            "success": bool,                 # Whether compilation succeeded
            "errors": List[str]              # List of compilation errors (if any)
        }

    Example:
        >>> state_mgr = StateManager(Path("./run_001"))
        >>> agent = TEXCompiler(state_mgr, "pruning")
        >>> input_data = {
        ...     "tex_content": "\\documentclass{article}\\n...",
        ...     "output_path": "./output/resume.pdf"
        ... }
        >>> result = await agent.run(input_data)
        >>> print(f"Success: {result['success']}, PDF: {result['pdf_path']}")
    """

    @property
    def agent_name(self) -> str:
        """Unique identifier for this agent type.

        Returns:
            Agent name string
        """
        return "tex_compiler"

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
        2. Required keys exist: tex_content, output_path
        3. tex_content is non-empty string with LaTeX markers
        4. output_path is valid

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
        required_keys = ["tex_content", "output_path"]
        missing_keys = [k for k in required_keys if k not in input_data]
        if missing_keys:
            self.logger.error(f"Missing required keys: {missing_keys}")
            return False

        # Validate tex_content
        tex_content = input_data.get("tex_content", "")
        if not isinstance(tex_content, str) or len(tex_content.strip()) < 50:
            self.logger.error("tex_content must be non-empty string (min 50 chars)")
            return False

        # Basic LaTeX validation
        if "\\documentclass" not in tex_content and "\\begin{document}" not in tex_content:
            self.logger.error("tex_content doesn't appear to be valid LaTeX")
            return False

        # Validate output_path
        output_path = input_data.get("output_path", "")
        if not isinstance(output_path, str) or not output_path:
            self.logger.error("output_path must be non-empty string")
            return False

        if not output_path.endswith(".pdf"):
            self.logger.error("output_path must end with .pdf extension")
            return False

        self.logger.info(f"Input validation passed: compiling to {output_path}")
        return True

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Compile LaTeX to PDF using pdflatex via subprocess.

        This method does NOT use the Task tool - it directly invokes pdflatex
        via subprocess for compilation.

        Args:
            input_data: Validated input data with LaTeX content

        Returns:
            Dict with compilation results

        Raises:
            RuntimeError: If compilation fails catastrophically
        """
        tex_content = input_data["tex_content"]
        output_path = input_data["output_path"]

        self.logger.info(f"Compiling LaTeX ({len(tex_content)} chars) to {output_path}")

        # Create temporary directory for compilation
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            tex_file_path = temp_dir_path / "document.tex"

            # Write LaTeX content to temporary file
            self.logger.debug(f"Writing LaTeX to {tex_file_path}")
            tex_file_path.write_text(tex_content, encoding="utf-8")

            # Run pdflatex compilation
            compile_result = self._compile_with_pdflatex(tex_file_path, temp_dir_path)

            if compile_result["success"]:
                # Move PDF to output path
                pdf_temp_path = temp_dir_path / "document.pdf"
                output_path_obj = Path(output_path)

                # Ensure output directory exists
                output_path_obj.parent.mkdir(parents=True, exist_ok=True)

                # Copy PDF to output location
                import shutil
                shutil.copy2(pdf_temp_path, output_path_obj)

                self.logger.info(f"PDF compiled successfully: {output_path}")

                return {
                    "pdf_path": str(output_path_obj.absolute()),
                    "success": True,
                    "errors": []
                }
            else:
                self.logger.error(f"Compilation failed: {compile_result['errors']}")

                return {
                    "pdf_path": "",
                    "success": False,
                    "errors": compile_result["errors"]
                }

    def _compile_with_pdflatex(
        self, tex_file: Path, work_dir: Path
    ) -> Dict[str, Any]:
        """Run pdflatex compilation.

        Args:
            tex_file: Path to .tex file to compile
            work_dir: Working directory for compilation

        Returns:
            Dict with success status and any errors
        """
        try:
            # Run pdflatex (may need to run twice for references)
            for run_num in [1, 2]:
                self.logger.debug(f"pdflatex run {run_num}/2")

                result = subprocess.run(
                    [
                        "pdflatex",
                        "-interaction=nonstopmode",
                        "-output-directory", str(work_dir),
                        str(tex_file)
                    ],
                    cwd=work_dir,
                    capture_output=True,
                    text=True,
                    timeout=60  # 60 second timeout
                )

            # Check if PDF was created
            pdf_path = work_dir / "document.pdf"
            if pdf_path.exists():
                return {
                    "success": True,
                    "errors": []
                }
            else:
                # Parse log file for errors
                log_path = work_dir / "document.log"
                errors = self._parse_latex_errors(log_path)

                return {
                    "success": False,
                    "errors": errors if errors else ["PDF not generated (unknown error)"]
                }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "errors": ["pdflatex compilation timed out (60s limit)"]
            }
        except FileNotFoundError:
            return {
                "success": False,
                "errors": ["pdflatex command not found - ensure TeX distribution is installed"]
            }
        except Exception as e:
            return {
                "success": False,
                "errors": [f"Compilation error: {str(e)}"]
            }

    def _parse_latex_errors(self, log_path: Path) -> List[str]:
        """Parse LaTeX log file for error messages.

        Args:
            log_path: Path to .log file

        Returns:
            List of error messages
        """
        if not log_path.exists():
            return ["Log file not found"]

        errors = []
        try:
            log_content = log_path.read_text(encoding="utf-8", errors="ignore")

            # Look for common error patterns
            for line in log_content.split("\n"):
                if line.startswith("!") or "Error:" in line:
                    errors.append(line.strip())

            # Limit to first 10 errors
            return errors[:10] if errors else ["Compilation failed (no specific errors found in log)"]

        except Exception as e:
            return [f"Error parsing log file: {str(e)}"]

    async def format_output(self, raw_output: Any) -> Dict[str, Any]:
        """Format the raw compilation output.

        Args:
            raw_output: Raw output from execute()

        Returns:
            Formatted output dict
        """
        # Output is already in correct format from execute()
        if isinstance(raw_output, dict):
            return raw_output
        else:
            # Shouldn't happen, but handle gracefully
            return {
                "pdf_path": "",
                "success": False,
                "errors": [f"Unexpected output type: {type(raw_output)}"]
            }

    def _get_input_summary(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create summary of input data for logging.

        Args:
            input_data: Input data to summarize

        Returns:
            Dictionary with input summary information
        """
        tex_content = input_data.get("tex_content", "")
        return {
            "tex_content_length": len(tex_content),
            "output_path": input_data.get("output_path", "unknown"),
            "has_documentclass": "\\documentclass" in tex_content,
            "has_begin_document": "\\begin{document}" in tex_content
        }

    def _get_output_summary(self, output_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create summary of output data for logging.

        Args:
            output_data: Compilation result

        Returns:
            Dictionary with output summary information
        """
        return {
            "type": "compilation_result",
            "success": output_data.get("success", False),
            "pdf_path": output_data.get("pdf_path", ""),
            "error_count": len(output_data.get("errors", []))
        }
