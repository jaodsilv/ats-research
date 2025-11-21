"""VersionManager agent for storing and retrieving document versions.

This agent manages version history of documents throughout the polishing process,
allowing restoration of previous versions if quality degrades.
"""

import logging
from typing import Dict, Any

from ..base_agent import BaseAgent


class VersionManager(BaseAgent[Dict[str, Any], Dict[str, Any]]):
    """Agent that manages document version storage and retrieval.

    Unlike other agents, this agent directly uses StateManager methods
    rather than calling the Task tool, as version management is a
    straightforward file I/O operation.

    Input Format:
        Dict with keys:
        {
            "action": str,              # "store" or "restore"
            "document_id": str,         # Unique document identifier
            "content": str,             # Document content (for "store" action)
            "version_num": int,         # Version number (for "restore" action)
            "metadata": dict            # Optional metadata (for "store" action)
        }

    Output Format:
        Dict with keys:
        {
            "version_num": int,         # Version number stored/restored
            "content": str,             # Document content (for "restore")
            "metadata": dict,           # Version metadata
            "timestamp": str            # ISO timestamp
        }

    Example (Store):
        >>> state_mgr = StateManager(Path("./run_001"))
        >>> agent = VersionManager(state_mgr, "polishing")
        >>> result = await agent.run({
        ...     "action": "store",
        ...     "document_id": "resume_v1",
        ...     "content": "# John Doe Resume\\n...",
        ...     "metadata": {"score": 0.85, "iteration": 1}
        ... })
        >>> print(result["version_num"])
        1

    Example (Restore):
        >>> result = await agent.run({
        ...     "action": "restore",
        ...     "document_id": "resume_v1",
        ...     "version_num": 1
        ... })
        >>> print(result["content"])
        # John Doe Resume\n...
    """

    @property
    def agent_name(self) -> str:
        """Unique identifier for this agent type.

        Returns:
            Agent name string
        """
        return "version_manager"

    @property
    def agent_type(self) -> str:
        """Claude Code subagent type to use for this agent.

        Returns:
            Subagent type string
        """
        return "general-purpose"

    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input contains required fields based on action.

        Checks that:
        1. Input is a dictionary
        2. Required keys exist based on action type
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

        # Check action
        action = input_data.get("action", "")
        if action not in ["store", "restore"]:
            self.logger.error(f"action must be 'store' or 'restore', got '{action}'")
            return False

        # Check document_id
        document_id = input_data.get("document_id", "")
        if not isinstance(document_id, str) or not document_id.strip():
            self.logger.error("document_id must be non-empty string")
            return False

        # Validate based on action type
        if action == "store":
            # Must have content
            content = input_data.get("content", "")
            if not isinstance(content, str) or len(content.strip()) < 10:
                self.logger.error("content must be non-empty string (min 10 chars) for 'store'")
                return False

        elif action == "restore":
            # Must have version_num
            version_num = input_data.get("version_num")
            if not isinstance(version_num, int) or version_num < 1:
                self.logger.error("version_num must be positive integer for 'restore'")
                return False

        self.logger.info(f"Input validation passed: action={action}, document_id={document_id}")
        return True

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute version management operation (store or restore).

        This method directly uses StateManager's save_version() or load_version()
        methods rather than calling the Task tool.

        Args:
            input_data: Validated input data with action details

        Returns:
            Dict with version operation results

        Raises:
            RuntimeError: If version operation fails
        """
        action = input_data["action"]
        document_id = input_data["document_id"]

        if action == "store":
            # Store a new version
            content = input_data["content"]
            metadata = input_data.get("metadata", {})

            # Determine next version number
            try:
                latest_num, _ = await self.state_manager.get_latest_version(document_id)
                next_version = latest_num + 1
            except FileNotFoundError:
                # No versions exist yet, start at 1
                next_version = 1

            self.logger.info(f"Storing version {next_version} of document '{document_id}'")

            # Save version
            await self.state_manager.save_version(
                document_id=document_id,
                version_num=next_version,
                content=content,
                metadata=metadata
            )

            result = {
                "version_num": next_version,
                "content": content,
                "metadata": metadata,
                "timestamp": None  # Will be filled by format_output
            }

        else:  # restore
            # Restore an existing version
            version_num = input_data["version_num"]

            self.logger.info(f"Restoring version {version_num} of document '{document_id}'")

            # Load version
            version_data = await self.state_manager.load_version(document_id, version_num)

            result = {
                "version_num": version_data.get("version", version_num),
                "content": version_data.get("content", ""),
                "metadata": version_data.get("metadata", {}),
                "timestamp": version_data.get("timestamp", "")
            }

        self.logger.info(f"Version operation '{action}' completed successfully")

        return result

    async def format_output(self, raw_output: Dict[str, Any]) -> Dict[str, Any]:
        """Format the version operation output.

        Args:
            raw_output: Raw output from execute()

        Returns:
            Formatted dict with version information
        """
        # Ensure all expected keys exist
        formatted = {
            "version_num": raw_output.get("version_num", 0),
            "content": raw_output.get("content", ""),
            "metadata": raw_output.get("metadata", {}),
            "timestamp": raw_output.get("timestamp", "")
        }

        self.logger.info(f"Formatted version data: version={formatted['version_num']}")

        return formatted

    def _get_input_summary(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create summary of input data for logging.

        Args:
            input_data: Input data to summarize

        Returns:
            Dictionary with input summary information
        """
        summary = {
            "action": input_data.get("action", "unknown"),
            "document_id": input_data.get("document_id", "unknown")
        }

        if input_data.get("action") == "store":
            summary["content_length"] = len(input_data.get("content", ""))
            summary["has_metadata"] = bool(input_data.get("metadata"))
        elif input_data.get("action") == "restore":
            summary["version_num"] = input_data.get("version_num", 0)

        return summary

    def _get_output_summary(self, output_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create summary of output data for logging.

        Args:
            output_data: Version operation results

        Returns:
            Dictionary with output summary information
        """
        return {
            "version_num": output_data.get("version_num", 0),
            "content_length": len(output_data.get("content", "")),
            "has_metadata": bool(output_data.get("metadata")),
            "timestamp": output_data.get("timestamp", "")
        }
