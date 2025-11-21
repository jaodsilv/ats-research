"""Abstract base class for all agents in the orchestration system.

This module provides the foundational BaseAgent class that all specific agent
implementations inherit from. It handles common concerns like validation,
execution pipeline, error handling, logging, and state persistence.

Key Design Decisions:
- Agents use Claude Code's Task tool rather than direct Anthropic API calls
- Generic types (InputT, OutputT) enable type-safe input/output handling
- Async/await throughout for non-blocking I/O operations
- Automatic artifact persistence for audit trail and debugging
- Comprehensive error handling with structured logging
"""

import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Generic, Optional, TypeVar

from ..state.state_manager import StateManager
from ..utils.logging import log_agent_complete, log_agent_start

# Type variables for generic input/output types
InputT = TypeVar('InputT')
OutputT = TypeVar('OutputT')


class BaseAgent(ABC, Generic[InputT, OutputT]):
    """Abstract base class for all orchestration agents.

    This class provides the execution pipeline and common functionality for
    agents that leverage Claude Code's Task tool to perform work. Subclasses
    implement the specific logic for validation, execution, and output formatting.

    The agent execution pipeline:
    1. Validate input data
    2. Log execution start
    3. Execute agent logic (typically calling Task tool)
    4. Format raw output into structured result
    5. Save output as artifact for persistence
    6. Log execution completion
    7. Return formatted output

    Attributes:
        state_manager: StateManager instance for artifact persistence
        stage: Workflow stage this agent belongs to (e.g., "jd_matching")
        logger: Logger instance for this agent

    Example:
        >>> class MyAgent(BaseAgent[dict, str]):
        ...     agent_name = "my_agent"
        ...     agent_type = "code_analysis"
        ...
        ...     async def validate_input(self, input_data: dict) -> bool:
        ...         return "required_field" in input_data
        ...
        ...     async def execute(self, input_data: dict) -> str:
        ...         # Use Claude Code Task tool to perform work
        ...         prompt = self._build_task_prompt(input_data)
        ...         # Task tool execution would happen here
        ...         return "result from task"
        ...
        ...     async def format_output(self, raw_output: Any) -> str:
        ...         return str(raw_output)
        >>>
        >>> state_mgr = StateManager(Path("./run_001"))
        >>> agent = MyAgent(state_mgr, "processing")
        >>> result = await agent.run({"required_field": "value"})
    """

    @property
    @abstractmethod
    def agent_name(self) -> str:
        """Unique identifier for this agent type.

        Returns:
            Agent name string (e.g., "jd_matcher", "style_polisher")
        """
        pass

    @property
    @abstractmethod
    def agent_type(self) -> str:
        """Claude Code subagent type to use for this agent.

        Returns:
            Subagent type string (e.g., "code_analysis", "documentation")
        """
        pass

    def __init__(self, state_manager: StateManager, stage: str) -> None:
        """Initialize the base agent.

        Args:
            state_manager: StateManager instance for artifact persistence
            stage: Workflow stage name (e.g., "jd_matching", "draft_writing")
        """
        self.state_manager = state_manager
        self.stage = stage

        # Initialize logger with agent-specific name
        logger_name = f"{__name__}.{self.agent_name}"
        self.logger = logging.getLogger(logger_name)

        self.logger.debug(
            f"Initialized {self.agent_name} agent for stage '{stage}'"
        )

    @abstractmethod
    async def validate_input(self, input_data: InputT) -> bool:
        """Validate input data before execution.

        Subclasses implement this to check that input_data contains all
        required fields and meets any constraints.

        Args:
            input_data: Input data to validate

        Returns:
            True if input is valid, False otherwise
        """
        pass

    @abstractmethod
    async def execute(self, input_data: InputT) -> OutputT:
        """Execute the main agent logic.

        Subclasses implement this to perform the actual agent work, typically
        by calling Claude Code's Task tool with a constructed prompt.

        Args:
            input_data: Validated input data

        Returns:
            Raw output from agent execution (to be formatted by format_output)
        """
        pass

    @abstractmethod
    async def format_output(self, raw_output: Any) -> OutputT:
        """Format raw agent output into structured result.

        Subclasses implement this to parse and structure the raw output
        from execute() into the expected OutputT type.

        Args:
            raw_output: Raw output from execute()

        Returns:
            Formatted output of type OutputT
        """
        pass

    async def run(self, input_data: InputT) -> OutputT:
        """Execute the full agent pipeline.

        This is the main entry point for agent execution. It orchestrates
        validation, execution, formatting, persistence, and logging.

        Pipeline stages:
        1. Validate input data
        2. Log start with input summary
        3. Record start time
        4. Execute agent logic with error handling
        5. Format raw output
        6. Calculate execution duration
        7. Save output as artifact
        8. Log completion with duration
        9. Return formatted output

        Args:
            input_data: Input data for the agent

        Returns:
            Formatted output from the agent

        Raises:
            ValueError: If input validation fails
            Exception: If agent execution fails (re-raised with context)
        """
        # Step 1: Validate input
        is_valid = await self.validate_input(input_data)
        if not is_valid:
            self.logger.error(f"Input validation failed for {self.agent_name}")
            raise ValueError(
                f"Invalid input data for {self.agent_name}. "
                "Check logs for validation details."
            )

        # Step 2: Log start
        input_summary = self._get_input_summary(input_data)
        log_agent_start(self.agent_name, input_summary)

        # Step 3: Record start time
        start_time = datetime.utcnow()

        try:
            # Step 4: Execute agent logic
            self.logger.info(f"Executing {self.agent_name}...")
            raw_output = await self.execute(input_data)

            # Step 5: Format output
            formatted_output = await self.format_output(raw_output)

            # Step 6: Calculate duration
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()

            # Step 7: Save output as artifact
            metadata = {
                "agent_name": self.agent_name,
                "agent_type": self.agent_type,
                "stage": self.stage,
                "duration_seconds": duration,
                "start_time": start_time.isoformat() + "Z",
                "end_time": end_time.isoformat() + "Z",
            }

            await self._save_output(formatted_output, metadata)

            # Step 8: Log completion
            output_summary = self._get_output_summary(formatted_output)
            log_agent_complete(self.agent_name, output_summary, duration)

            # Step 9: Return formatted output
            return formatted_output

        except Exception as e:
            # Calculate duration even on failure
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()

            self.logger.error(
                f"Agent {self.agent_name} failed after {duration:.2f}s: {e}",
                exc_info=True
            )

            # Re-raise with context
            raise RuntimeError(
                f"Agent {self.agent_name} execution failed: {e}"
            ) from e

    def _build_task_prompt(self, input_data: InputT) -> str:
        """Build prompt string for Claude Code Task tool.

        This helper converts input_data into a string prompt that can be
        passed to the Task tool. Override in subclasses for custom formatting.

        Args:
            input_data: Input data to convert to prompt

        Returns:
            Formatted prompt string
        """
        # Default implementation: JSON serialization if dict/list, str otherwise
        if isinstance(input_data, (dict, list)):
            return json.dumps(input_data, indent=2, ensure_ascii=False)
        else:
            return str(input_data)

    async def _save_output(
        self,
        output_data: OutputT,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Path:
        """Save agent output as artifact via state manager.

        Args:
            output_data: Formatted output to save
            metadata: Optional metadata dict (duration, timestamps, etc.)

        Returns:
            Path to saved artifact file
        """
        # Generate timestamped artifact name
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        artifact_name = f"{self.agent_name}_{timestamp}"

        # Prepare artifact content with metadata
        artifact_content = {
            "output": self._serialize_output(output_data),
            "metadata": metadata or {}
        }

        # Save via state manager
        artifact_path = await self.state_manager.save_artifact(
            stage=self.stage,
            artifact_name=artifact_name,
            content=artifact_content,
            format="json"
        )

        self.logger.debug(f"Saved output artifact: {artifact_path}")
        return artifact_path

    def _serialize_output(self, output_data: OutputT) -> Any:
        """Convert output data to JSON-serializable format.

        Override this in subclasses if OutputT needs custom serialization.

        Args:
            output_data: Output to serialize

        Returns:
            JSON-serializable representation
        """
        # Default: return as-is if already serializable, convert to str otherwise
        if isinstance(output_data, (dict, list, str, int, float, bool, type(None))):
            return output_data
        else:
            return str(output_data)

    def _get_input_summary(self, input_data: InputT) -> Dict[str, Any]:
        """Create summary of input data for logging.

        Override this in subclasses for custom input summaries.

        Args:
            input_data: Input data to summarize

        Returns:
            Dictionary with input summary information
        """
        if isinstance(input_data, dict):
            return {
                "input_keys": list(input_data.keys()),
                "input_size": len(input_data)
            }
        elif isinstance(input_data, (list, str)):
            return {
                "input_type": type(input_data).__name__,
                "input_size": len(input_data)
            }
        else:
            return {
                "input_type": type(input_data).__name__
            }

    def _get_output_summary(self, output_data: OutputT) -> Dict[str, Any]:
        """Create summary of output data for logging.

        Override this in subclasses for custom output summaries.

        Args:
            output_data: Output data to summarize

        Returns:
            Dictionary with output summary information
        """
        if isinstance(output_data, dict):
            return {
                "output_keys": list(output_data.keys()),
                "output_size": len(output_data)
            }
        elif isinstance(output_data, (list, str)):
            return {
                "output_type": type(output_data).__name__,
                "output_size": len(output_data)
            }
        else:
            return {
                "output_type": type(output_data).__name__
            }
