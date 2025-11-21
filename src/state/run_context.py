"""RunContext for execution state tracking in the resume/cover letter tailoring orchestration system.

This module provides the RunContext class that encapsulates the entire run state,
including current stage, timing, job description tracking, and error logging.
"""

from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

from ..config import Config
from .state_manager import StateManager


class OrchestrationStage(Enum):
    """Enumeration of orchestration workflow stages.

    Attributes:
        INITIALIZATION: Initial setup and configuration
        INPUT_PREPARATION: Input file loading and validation
        JD_MATCHING: Job description matching and selection
        WRITING_POLISHING: Document writing and polishing
        FACT_CHECKING: Fact verification loop
        PRUNING: Content pruning and optimization
        COMPLETED: Successful completion
        FAILED: Execution failed
    """
    INITIALIZATION = "initialization"
    INPUT_PREPARATION = "input_preparation"
    JD_MATCHING = "jd_matching"
    WRITING_POLISHING = "writing_polishing"
    FACT_CHECKING = "fact_checking"
    PRUNING = "pruning"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class RunContext:
    """Encapsulates the entire run state for orchestration execution.

    This class tracks the current execution state including:
    - Configuration and state management
    - Current orchestration stage
    - Execution timing
    - Job description processing state
    - Arbitrary context data storage
    - Error tracking

    Attributes:
        config: Configuration object
        state_manager: State manager instance for persistence
        current_stage: Current orchestration stage
        start_time: Execution start timestamp
        end_time: Execution end timestamp (None if running)
        job_description_ids: List of all JD IDs being processed
        selected_jd_ids: List of JD IDs selected after matching
        context_data: Dictionary for arbitrary context storage
        error_log: List of error records with timestamps
    """

    config: Config
    state_manager: StateManager
    current_stage: OrchestrationStage = OrchestrationStage.INITIALIZATION
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    job_description_ids: List[str] = field(default_factory=list)
    selected_jd_ids: List[str] = field(default_factory=list)
    context_data: Dict[str, Any] = field(default_factory=dict)
    error_log: List[Dict[str, Any]] = field(default_factory=list)

    @classmethod
    async def create(cls, config: Config) -> "RunContext":
        """Create a new RunContext with initialized StateManager.

        This factory method:
        1. Creates the run directory structure
        2. Initializes the StateManager
        3. Saves the initial state
        4. Returns the RunContext instance

        Args:
            config: Configuration object with run settings

        Returns:
            Initialized RunContext instance

        Raises:
            OSError: If directory creation fails
            Exception: If state initialization fails
        """
        # Create run directory structure
        config.runs_dir.mkdir(parents=True, exist_ok=True)

        # Initialize state manager
        state_manager = StateManager(config.runs_dir)

        # Create the run context
        run_context = cls(config=config, state_manager=state_manager)

        # Save initial state
        await run_context.save_checkpoint()

        return run_context

    async def advance_stage(self, new_stage: OrchestrationStage) -> None:
        """Advance to a new orchestration stage.

        Updates the current stage, saves a checkpoint, and logs the stage transition.

        Args:
            new_stage: The new stage to transition to

        Raises:
            Exception: If checkpoint save fails
        """
        old_stage = self.current_stage
        self.current_stage = new_stage

        # Save checkpoint with stage transition
        checkpoint_path = await self.save_checkpoint()

        # Log stage change (could be enhanced with actual logging)
        print(f"Stage transition: {old_stage.value} -> {new_stage.value}")
        print(f"Checkpoint saved: {checkpoint_path}")

    async def add_context_data(self, key: str, value: Any) -> None:
        """Add data to the context storage.

        Args:
            key: Key for the context data
            value: Value to store (must be JSON-serializable)

        Raises:
            Exception: If state save fails
        """
        self.context_data[key] = value
        await self.save_checkpoint()

    async def log_error(
        self,
        error_type: str,
        message: str,
        details: Optional[dict] = None
    ) -> None:
        """Log an error to the error log.

        Args:
            error_type: Category or type of error
            message: Error message
            details: Optional additional error details

        Raises:
            Exception: If state save fails
        """
        error_record = {
            "timestamp": datetime.now().isoformat(),
            "error_type": error_type,
            "message": message,
            "details": details or {},
            "stage": self.current_stage.value
        }

        self.error_log.append(error_record)
        await self.save_checkpoint()

    async def mark_completed(self) -> None:
        """Mark the execution as completed.

        Sets the end time, advances to COMPLETED stage, and saves final state.

        Raises:
            Exception: If state save fails
        """
        self.end_time = datetime.now()
        await self.advance_stage(OrchestrationStage.COMPLETED)

    async def mark_failed(self, reason: str) -> None:
        """Mark the execution as failed.

        Sets the end time, logs the failure reason, advances to FAILED stage,
        and saves final state.

        Args:
            reason: Description of the failure reason

        Raises:
            Exception: If error logging or state save fails
        """
        self.end_time = datetime.now()
        await self.log_error(
            error_type="execution_failure",
            message=reason,
            details={"final_stage": self.current_stage.value}
        )
        await self.advance_stage(OrchestrationStage.FAILED)

    def get_duration(self) -> float | None:
        """Get the execution duration in seconds.

        Returns:
            Duration in seconds if execution has ended, None otherwise
        """
        if self.end_time is None:
            return None

        return (self.end_time - self.start_time).total_seconds()

    async def save_checkpoint(self) -> Path:
        """Save the current context state as a checkpoint.

        Serializes the entire RunContext state and saves it via the state manager.

        Returns:
            Path to the saved checkpoint file

        Raises:
            Exception: If serialization or save fails
        """
        # Convert to serializable dictionary
        state_dict = await self.to_dict()

        # Save via state manager
        checkpoint_path = await self.state_manager.save_checkpoint(
            stage=self.current_stage.value,
            data=state_dict
        )

        return checkpoint_path

    async def to_dict(self) -> dict:
        """Serialize RunContext to a dictionary.

        Converts all fields to JSON-serializable format, including:
        - Config serialization
        - Enum values as strings
        - Datetime objects as ISO format strings

        Returns:
            Dictionary representation of the RunContext
        """
        return {
            "config": self.config.model_dump(),
            "current_stage": self.current_stage.value,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "job_description_ids": self.job_description_ids.copy(),
            "selected_jd_ids": self.selected_jd_ids.copy(),
            "context_data": self.context_data.copy(),
            "error_log": self.error_log.copy(),
            "duration_seconds": self.get_duration()
        }
