"""TEXTemplateFiller agent for filling LaTeX templates with draft content.

This agent takes a draft document and fills a LaTeX template with the content,
preparing it for PDF compilation.
"""

import logging
from typing import Dict, Any
from pathlib import Path

from ..base_agent import BaseAgent


class TEXTemplateFiller(BaseAgent[Dict[str, Any], str]):
    """Agent that fills LaTeX templates with draft content.

    This agent takes draft content (Markdown or plain text) and fills a LaTeX
    template to prepare for PDF rendering. It handles conversion from Markdown
    to LaTeX formatting and proper escaping of special characters.

    Input Format:
        Dict with keys:
        {
            "draft": str,                    # Draft content to fill into template
            "template_path": str,            # Path to LaTeX template file
            "document_type": str             # "resume" or "cover_letter"
        }

    Output Format:
        str: Filled LaTeX file content ready for compilation

    Example:
        >>> state_mgr = StateManager(Path("./run_001"))
        >>> agent = TEXTemplateFiller(state_mgr, "pruning")
        >>> input_data = {
        ...     "draft": "# John Doe\\nSenior Engineer\\n...",
        ...     "template_path": "./templates/resume.tex",
        ...     "document_type": "resume"
        ... }
        >>> tex_content = await agent.run(input_data)
    """

    @property
    def agent_name(self) -> str:
        """Unique identifier for this agent type.

        Returns:
            Agent name string
        """
        return "tex_template_filler"

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
        2. Required keys exist: draft, template_path, document_type
        3. Draft is non-empty string
        4. Template path is valid
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
        required_keys = ["draft", "template_path", "document_type"]
        missing_keys = [k for k in required_keys if k not in input_data]
        if missing_keys:
            self.logger.error(f"Missing required keys: {missing_keys}")
            return False

        # Validate draft
        draft = input_data.get("draft", "")
        if not isinstance(draft, str) or len(draft.strip()) < 10:
            self.logger.error("draft must be non-empty string (min 10 chars)")
            return False

        # Validate template path
        template_path = input_data.get("template_path", "")
        if not isinstance(template_path, str) or not template_path:
            self.logger.error("template_path must be non-empty string")
            return False

        # Validate document type
        doc_type = input_data.get("document_type", "")
        if doc_type not in ["resume", "cover_letter"]:
            self.logger.error(
                f"document_type must be 'resume' or 'cover_letter', got '{doc_type}'"
            )
            return False

        self.logger.info(f"Input validation passed: {doc_type} template filling")
        return True

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fill LaTeX template with draft content using Task tool.

        Args:
            input_data: Validated input data with draft and template path

        Returns:
            Dict with task instruction for template filling

        Raises:
            RuntimeError: If template filling fails
        """
        draft = input_data["draft"]
        template_path = input_data["template_path"]
        doc_type = input_data["document_type"]

        self.logger.info(
            f"Filling {doc_type} LaTeX template at {template_path} "
            f"with draft ({len(draft)} chars)"
        )

        # Build prompt for Task tool
        prompt = self._build_template_fill_prompt(input_data)

        # Task tool invocation structure
        task_instruction = {
            "instruction": "CALL_TASK_TOOL",
            "agent_type": self.agent_type,
            "prompt": prompt,
            "document_type": doc_type,
            "draft_length": len(draft),
            "template_path": template_path
        }

        self.logger.info("Generated template filling instruction")

        return task_instruction

    async def format_output(self, raw_output: Any) -> str:
        """Format the raw output into LaTeX content string.

        Args:
            raw_output: Raw output from execute() or Task tool

        Returns:
            LaTeX file content as string
        """
        # If this is a task instruction (pre-execution), return as-is
        if isinstance(raw_output, dict) and raw_output.get("instruction") == "CALL_TASK_TOOL":
            self.logger.debug("Output is task instruction (pre-execution), passing through")
            return raw_output

        # Otherwise, ensure we have a string
        if isinstance(raw_output, str):
            tex_content = raw_output.strip()
        elif isinstance(raw_output, dict) and "tex_content" in raw_output:
            tex_content = raw_output["tex_content"].strip()
        else:
            tex_content = str(raw_output).strip()

        # Basic validation: check for LaTeX document structure
        if "\\documentclass" not in tex_content and "\\begin{document}" not in tex_content:
            self.logger.warning("Output doesn't look like valid LaTeX (missing document markers)")

        self.logger.info(f"Formatted LaTeX content: {len(tex_content)} characters")

        return tex_content

    def _build_template_fill_prompt(self, input_data: Dict[str, Any]) -> str:
        """Build prompt for Task tool to fill LaTeX template.

        Args:
            input_data: Input data with draft and template info

        Returns:
            Formatted prompt string for Task tool
        """
        draft = input_data["draft"]
        template_path = input_data["template_path"]
        doc_type = input_data["document_type"]

        prompt = f"""Fill a LaTeX template with the provided draft content.

DOCUMENT TYPE: {doc_type}
TEMPLATE PATH: {template_path}

DRAFT CONTENT (Markdown format):
{draft}

TASK:
1. Read the LaTeX template from the specified path
2. Convert the Markdown draft content to LaTeX formatting:
   - Headers (# -> \\section, ## -> \\subsection, etc.)
   - Bold (**text** -> \\textbf{{text}})
   - Italic (*text* -> \\textit{{text}})
   - Lists (- item -> \\item in itemize environment)
   - Escape special LaTeX characters (%, $, &, #, _, {{, }})
3. Fill the template placeholders with the converted content
4. Ensure proper LaTeX structure and compilation readiness
5. Return ONLY the complete filled LaTeX document

IMPORTANT:
- Preserve all draft content faithfully
- Ensure proper LaTeX escaping to avoid compilation errors
- Maintain document structure from the template
- Do not add explanations or metadata
- Return ONLY the filled .tex file content

OUTPUT FORMAT:
Return the complete filled LaTeX document as plain text, starting with \\documentclass.
"""

        return prompt

    def _get_input_summary(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create summary of input data for logging.

        Args:
            input_data: Input data to summarize

        Returns:
            Dictionary with input summary information
        """
        return {
            "document_type": input_data.get("document_type", "unknown"),
            "draft_length": len(input_data.get("draft", "")),
            "template_path": input_data.get("template_path", "unknown"),
            "draft_word_count": len(input_data.get("draft", "").split())
        }

    def _get_output_summary(self, output_data: str) -> Dict[str, Any]:
        """Create summary of output data for logging.

        Args:
            output_data: LaTeX content

        Returns:
            Dictionary with output summary information
        """
        if isinstance(output_data, dict) and output_data.get("instruction") == "CALL_TASK_TOOL":
            return {
                "type": "task_instruction",
                "document_type": output_data.get("document_type", "unknown"),
                "draft_length": output_data.get("draft_length", 0),
                "status": "pending_execution"
            }

        has_document_class = "\\documentclass" in output_data if isinstance(output_data, str) else False
        has_begin_doc = "\\begin{document}" in output_data if isinstance(output_data, str) else False

        return {
            "type": "tex_content",
            "character_count": len(output_data) if isinstance(output_data, str) else 0,
            "has_document_class": has_document_class,
            "has_begin_document": has_begin_doc,
            "appears_valid": has_document_class and has_begin_doc
        }
