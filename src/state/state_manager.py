"""State management for resume/cover letter tailoring orchestration system.

This module provides file-based persistence for artifacts, versions, checkpoints,
and run state throughout the tailoring workflow.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiofiles


class StateManager:
    """Manages file-based state persistence for orchestration runs.

    This class handles:
    - Artifact storage (JSON, Markdown, LaTeX, text)
    - Document versioning with metadata
    - Checkpoint management for workflow resumption
    - Current state persistence

    Attributes:
        run_dir: Root directory for this orchestration run
        artifacts_dir: Directory for stage artifacts
        checkpoints_dir: Directory for workflow checkpoints
        state_dir: Directory for current state
        logs_dir: Directory for logs
        logger: Logger instance for this class
    """

    def __init__(self, run_dir: Path) -> None:
        """Initialize StateManager with run directory.

        Args:
            run_dir: Root directory path for this orchestration run
        """
        self.run_dir = Path(run_dir)
        self.artifacts_dir = self.run_dir / "artifacts"
        self.checkpoints_dir = self.run_dir / "checkpoints"
        self.state_dir = self.run_dir / "state"
        self.logs_dir = self.run_dir / "logs"

        # Create all subdirectories
        for directory in [self.artifacts_dir, self.checkpoints_dir,
                         self.state_dir, self.logs_dir]:
            directory.mkdir(parents=True, exist_ok=True)

        # Initialize logger
        self.logger = logging.getLogger(f"{__name__}.{self.run_dir.name}")
        self.logger.setLevel(logging.INFO)

        # Add file handler if not already present
        if not self.logger.handlers:
            handler = logging.FileHandler(self.logs_dir / "state_manager.log")
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    # ============================================================================
    # Artifact Management Methods
    # ============================================================================

    async def save_artifact(
        self,
        stage: str,
        artifact_name: str,
        content: str | dict,
        format: str = "json"
    ) -> Path:
        """Save artifact to stage-specific directory.

        Args:
            stage: Workflow stage name (e.g., "jd_matching", "draft_writing")
            artifact_name: Name of the artifact (without extension)
            content: Artifact content (dict/list for JSON, str for others)
            format: File format (json, md, tex, txt)

        Returns:
            Path to saved artifact file

        Raises:
            ValueError: If format is unsupported
            IOError: If file write fails
        """
        supported_formats = {"json", "md", "tex", "txt"}
        if format not in supported_formats:
            raise ValueError(
                f"Unsupported format '{format}'. Must be one of {supported_formats}"
            )

        # Create stage directory
        stage_dir = self.artifacts_dir / stage
        stage_dir.mkdir(parents=True, exist_ok=True)

        # Construct artifact path
        artifact_path = stage_dir / f"{artifact_name}.{format}"

        try:
            async with aiofiles.open(artifact_path, 'w', encoding='utf-8') as f:
                if format == "json":
                    # Serialize dict/list to JSON
                    if not isinstance(content, (dict, list)):
                        raise ValueError(
                            f"JSON format requires dict or list, got {type(content)}"
                        )
                    await f.write(json.dumps(content, indent=2, ensure_ascii=False))
                else:
                    # Write string content as-is
                    if not isinstance(content, str):
                        raise ValueError(
                            f"Format '{format}' requires str content, got {type(content)}"
                        )
                    await f.write(content)

            self.logger.info(
                f"Saved artifact: {stage}/{artifact_name}.{format} "
                f"({artifact_path.stat().st_size} bytes)"
            )
            return artifact_path

        except Exception as e:
            self.logger.error(
                f"Failed to save artifact {stage}/{artifact_name}.{format}: {e}"
            )
            raise IOError(f"Failed to save artifact: {e}") from e

    async def load_artifact(
        self,
        stage: str,
        artifact_name: str,
        format: str = "json"
    ) -> str | dict:
        """Load artifact from stage directory.

        Args:
            stage: Workflow stage name
            artifact_name: Name of the artifact (without extension)
            format: File format (json, md, tex, txt)

        Returns:
            Parsed JSON (dict/list) for .json files, raw string for others

        Raises:
            FileNotFoundError: If artifact doesn't exist
            IOError: If file read fails
        """
        artifact_path = self.artifacts_dir / stage / f"{artifact_name}.{format}"

        if not artifact_path.exists():
            raise FileNotFoundError(
                f"Artifact not found: {stage}/{artifact_name}.{format}"
            )

        try:
            async with aiofiles.open(artifact_path, 'r', encoding='utf-8') as f:
                content = await f.read()

            if format == "json":
                result = json.loads(content)
            else:
                result = content

            self.logger.info(f"Loaded artifact: {stage}/{artifact_name}.{format}")
            return result

        except Exception as e:
            self.logger.error(
                f"Failed to load artifact {stage}/{artifact_name}.{format}: {e}"
            )
            raise IOError(f"Failed to load artifact: {e}") from e

    async def list_artifacts(self, stage: Optional[str] = None) -> List[Path]:
        """List all artifacts, optionally filtered by stage.

        Args:
            stage: Optional stage name to filter by

        Returns:
            List of Path objects for all matching artifacts
        """
        if stage:
            stage_dir = self.artifacts_dir / stage
            if not stage_dir.exists():
                return []
            paths = list(stage_dir.rglob("*"))
        else:
            paths = list(self.artifacts_dir.rglob("*"))

        # Filter to files only
        artifact_paths = [p for p in paths if p.is_file()]

        self.logger.debug(
            f"Listed {len(artifact_paths)} artifacts" +
            (f" for stage '{stage}'" if stage else "")
        )

        return sorted(artifact_paths)

    # ============================================================================
    # Version Management Methods
    # ============================================================================

    async def save_version(
        self,
        document_id: str,
        version_num: int,
        content: str,
        metadata: dict
    ) -> Path:
        """Save versioned document with metadata.

        Args:
            document_id: Unique identifier for the document
            version_num: Version number (incremental)
            content: Document content
            metadata: Version metadata (author, description, etc.)

        Returns:
            Path to saved version file

        Raises:
            IOError: If file write fails
        """
        # Create version directory for document
        version_dir = self.artifacts_dir / "versions" / document_id
        version_dir.mkdir(parents=True, exist_ok=True)

        # Construct version path
        version_path = version_dir / f"v{version_num}.json"

        # Prepare version data
        version_data = {
            "version": version_num,
            "content": content,
            "metadata": metadata,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

        try:
            async with aiofiles.open(version_path, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(version_data, indent=2, ensure_ascii=False))

            self.logger.info(
                f"Saved version {version_num} of document '{document_id}'"
            )
            return version_path

        except Exception as e:
            self.logger.error(
                f"Failed to save version {version_num} of '{document_id}': {e}"
            )
            raise IOError(f"Failed to save version: {e}") from e

    async def load_version(self, document_id: str, version_num: int) -> dict:
        """Load specific version of a document.

        Args:
            document_id: Unique identifier for the document
            version_num: Version number to load

        Returns:
            Dict with keys: version, content, metadata, timestamp

        Raises:
            FileNotFoundError: If version doesn't exist
            IOError: If file read fails
        """
        version_path = (
            self.artifacts_dir / "versions" / document_id / f"v{version_num}.json"
        )

        if not version_path.exists():
            raise FileNotFoundError(
                f"Version {version_num} of document '{document_id}' not found"
            )

        try:
            async with aiofiles.open(version_path, 'r', encoding='utf-8') as f:
                content = await f.read()

            version_data = json.loads(content)
            self.logger.info(
                f"Loaded version {version_num} of document '{document_id}'"
            )
            return version_data

        except Exception as e:
            self.logger.error(
                f"Failed to load version {version_num} of '{document_id}': {e}"
            )
            raise IOError(f"Failed to load version: {e}") from e

    async def get_latest_version(self, document_id: str) -> tuple[int, dict]:
        """Get the latest version of a document.

        Args:
            document_id: Unique identifier for the document

        Returns:
            Tuple of (version_number, version_data)

        Raises:
            FileNotFoundError: If no versions exist for this document
        """
        version_dir = self.artifacts_dir / "versions" / document_id

        if not version_dir.exists():
            raise FileNotFoundError(
                f"No versions found for document '{document_id}'"
            )

        # Find all version files
        version_files = list(version_dir.glob("v*.json"))

        if not version_files:
            raise FileNotFoundError(
                f"No versions found for document '{document_id}'"
            )

        # Extract version numbers and find max
        version_numbers = []
        for vf in version_files:
            try:
                # Extract number from "v123.json" -> 123
                num = int(vf.stem[1:])
                version_numbers.append(num)
            except (ValueError, IndexError):
                self.logger.warning(f"Skipping invalid version file: {vf.name}")
                continue

        if not version_numbers:
            raise FileNotFoundError(
                f"No valid version files found for document '{document_id}'"
            )

        latest_num = max(version_numbers)
        latest_data = await self.load_version(document_id, latest_num)

        self.logger.info(
            f"Found latest version {latest_num} for document '{document_id}'"
        )
        return (latest_num, latest_data)

    # ============================================================================
    # Checkpoint Management Methods
    # ============================================================================

    async def save_checkpoint(self, stage: str, state_data: dict) -> Path:
        """Save workflow checkpoint.

        Args:
            stage: Current workflow stage name
            state_data: State data to checkpoint

        Returns:
            Path to saved checkpoint file

        Raises:
            IOError: If file write fails
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        checkpoint_name = f"{stage}_{timestamp}.json"
        checkpoint_path = self.checkpoints_dir / checkpoint_name

        # Add timestamp to state data
        checkpoint_data = {
            **state_data,
            "stage": stage,
            "checkpoint_timestamp": datetime.utcnow().isoformat() + "Z"
        }

        try:
            async with aiofiles.open(checkpoint_path, 'w', encoding='utf-8') as f:
                await f.write(
                    json.dumps(checkpoint_data, indent=2, ensure_ascii=False)
                )

            self.logger.info(f"Saved checkpoint: {checkpoint_name}")
            return checkpoint_path

        except Exception as e:
            self.logger.error(f"Failed to save checkpoint for stage '{stage}': {e}")
            raise IOError(f"Failed to save checkpoint: {e}") from e

    async def load_latest_checkpoint(self) -> tuple[str, dict] | None:
        """Load the most recent checkpoint.

        Returns:
            Tuple of (stage_name, checkpoint_data) or None if no checkpoints exist

        Raises:
            IOError: If file read fails
        """
        checkpoints = await self.list_checkpoints()

        if not checkpoints:
            self.logger.info("No checkpoints found")
            return None

        # Checkpoints are sorted newest first by list_checkpoints
        latest_checkpoint = checkpoints[0]

        try:
            async with aiofiles.open(latest_checkpoint, 'r', encoding='utf-8') as f:
                content = await f.read()

            checkpoint_data = json.loads(content)
            stage_name = checkpoint_data.get("stage", "unknown")

            self.logger.info(
                f"Loaded latest checkpoint: {latest_checkpoint.name} (stage: {stage_name})"
            )
            return (stage_name, checkpoint_data)

        except Exception as e:
            self.logger.error(f"Failed to load checkpoint {latest_checkpoint}: {e}")
            raise IOError(f"Failed to load checkpoint: {e}") from e

    async def list_checkpoints(self) -> List[Path]:
        """List all checkpoint files sorted by timestamp (newest first).

        Returns:
            List of checkpoint Path objects, sorted newest to oldest
        """
        checkpoint_files = list(self.checkpoints_dir.glob("*.json"))

        # Sort by filename (which includes timestamp) in descending order
        sorted_checkpoints = sorted(checkpoint_files, reverse=True)

        self.logger.debug(f"Found {len(sorted_checkpoints)} checkpoints")
        return sorted_checkpoints

    # ============================================================================
    # State Persistence Methods
    # ============================================================================

    async def save_state(self, state_data: dict) -> Path:
        """Save current run state.

        Args:
            state_data: Current state data to persist

        Returns:
            Path to saved state file

        Raises:
            IOError: If file write fails
        """
        state_path = self.state_dir / "current_state.json"

        # Add timestamp to state
        state_with_timestamp = {
            **state_data,
            "last_updated": datetime.utcnow().isoformat() + "Z"
        }

        try:
            async with aiofiles.open(state_path, 'w', encoding='utf-8') as f:
                await f.write(
                    json.dumps(state_with_timestamp, indent=2, ensure_ascii=False)
                )

            self.logger.info("Saved current state")
            return state_path

        except Exception as e:
            self.logger.error(f"Failed to save current state: {e}")
            raise IOError(f"Failed to save state: {e}") from e

    async def load_state(self) -> dict | None:
        """Load current run state.

        Returns:
            State data dict or None if state file doesn't exist

        Raises:
            IOError: If file read fails (when file exists but can't be read)
        """
        state_path = self.state_dir / "current_state.json"

        if not state_path.exists():
            self.logger.info("No current state file found")
            return None

        try:
            async with aiofiles.open(state_path, 'r', encoding='utf-8') as f:
                content = await f.read()

            state_data = json.loads(content)
            self.logger.info("Loaded current state")
            return state_data

        except Exception as e:
            self.logger.error(f"Failed to load current state: {e}")
            raise IOError(f"Failed to load state: {e}") from e
