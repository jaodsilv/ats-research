"""
BaseOrchestra - Abstract base class for workflow orchestration.

This module provides the foundation for all orchestrators in the resume/cover letter
tailoring system. Each orchestra coordinates multiple agents to complete a specific
workflow stage with automatic checkpointing, error handling, and stage advancement.

Example:
    ```python
    from src.orchestrators.base_orchestra import BaseOrchestra
    from src.state.run_context import OrchestrationStage

    class MyCustomOrchestra(BaseOrchestra):
        @property
        def orchestra_name(self) -> str:
            return "my_custom_orchestra"

        @property
        def stage(self) -> OrchestrationStage:
            return OrchestrationStage.CUSTOM_STAGE

        async def execute(self) -> Dict[str, Any]:
            # Get input from previous stage
            previous_data = await self._get_context_data("previous_output")

            # Coordinate agents
            agent = await self.agent_pool.get_agent("research")
            result = await agent.execute(previous_data)

            # Checkpoint progress
            await self._checkpoint({"intermediate": result})

            # Store results for next stage
            await self._set_context_data("custom_output", result)

            return {
                "status": "success",
                "result": result,
                "metadata": {"agent_used": "research"}
            }

    # Usage
    orchestra = MyCustomOrchestra(run_context, agent_pool)
    results = await orchestra.run()
    ```
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging
from datetime import datetime

from ..state.state_manager import StateManager
from ..state.run_context import RunContext, OrchestrationStage
from ..agents.agent_pool import AgentPool
from ..utils.logging import log_checkpoint


class BaseOrchestra(ABC):
    """
    Abstract base class for workflow orchestration.

    Orchestras coordinate multiple agents to complete a workflow stage, providing:
    - Automatic stage advancement
    - Checkpoint management
    - Error handling with failure tracking
    - Shared context for inter-stage communication
    - Execution timing and logging

    Each concrete orchestra must implement:
    - orchestra_name: Unique identifier for the orchestra
    - stage: Associated OrchestrationStage
    - execute(): Main orchestration logic

    The run() method provides the complete orchestration pipeline with
    automatic error handling, checkpointing, and context management.
    """

    @property
    @abstractmethod
    def orchestra_name(self) -> str:
        """
        Unique orchestra identifier.

        Returns:
            str: Name of the orchestra (e.g., "research_orchestra", "matching_orchestra")
        """
        pass

    @property
    @abstractmethod
    def stage(self) -> OrchestrationStage:
        """
        Associated orchestration stage.

        Returns:
            OrchestrationStage: The stage this orchestra is responsible for
        """
        pass

    def __init__(self, run_context: RunContext, agent_pool: AgentPool):
        """
        Initialize the BaseOrchestra.

        Args:
            run_context: Shared context for tracking orchestration state
            agent_pool: Pool of agents for parallel execution
        """
        self.run_context = run_context
        self.agent_pool = agent_pool
        self.state_manager: StateManager = run_context.state_manager
        self.logger = logging.getLogger(f"{__name__}.{self.orchestra_name}")

    @abstractmethod
    async def execute(self) -> Dict[str, Any]:
        """
        Main orchestration logic - must be implemented by subclasses.

        This method contains the core workflow logic, coordinating agents
        to complete the orchestra's specific task.

        Returns:
            Dict[str, Any]: Execution results and metadata including:
                - status: "success" or "failure"
                - result: Primary output of the orchestration
                - metadata: Additional information about execution

        Raises:
            Exception: Any error during orchestration execution
        """
        pass

    async def run(self) -> Dict[str, Any]:
        """
        Execute the complete orchestration pipeline.

        This method provides the full orchestration lifecycle:
        1. Log orchestra start
        2. Advance run_context to current stage
        3. Execute orchestra logic with error handling
        4. Save checkpoint with results
        5. Add results to context data for next stage
        6. Log completion and timing

        Returns:
            Dict[str, Any]: Results from execute() with added timing metadata

        Raises:
            Exception: Re-raises any exception after logging and marking failure
        """
        self.logger.info(f"Starting orchestra: {self.orchestra_name}")

        # Advance to current stage
        self.run_context.advance_stage(self.stage)

        # Record start time
        start_time = datetime.now()

        try:
            # Execute orchestra logic
            self.logger.debug(f"Executing {self.orchestra_name} logic")
            results = await self.execute()

            # Calculate duration
            duration = (datetime.now() - start_time).total_seconds()

            # Add timing metadata
            results["execution_time_seconds"] = duration
            results["completed_at"] = datetime.now().isoformat()

            # Save checkpoint
            await self.run_context.save_checkpoint(
                checkpoint_data={
                    "orchestra": self.orchestra_name,
                    "stage": self.stage.value,
                    "results": results,
                    "duration_seconds": duration
                }
            )

            # Add results to context for next stage
            context_key = f"{self.orchestra_name}_output"
            self.run_context.add_context_data(context_key, results)

            # Log completion
            self.logger.info(
                f"Orchestra {self.orchestra_name} completed successfully "
                f"in {duration:.2f} seconds"
            )

            log_checkpoint(
                self.logger,
                f"{self.orchestra_name}_completed",
                {
                    "stage": self.stage.value,
                    "duration": duration,
                    "status": results.get("status", "success")
                }
            )

            return results

        except Exception as e:
            # Calculate duration even on failure
            duration = (datetime.now() - start_time).total_seconds()

            # Log error
            self.logger.error(
                f"Orchestra {self.orchestra_name} failed after {duration:.2f} seconds: {str(e)}",
                exc_info=True
            )

            # Mark run context as failed
            self.run_context.mark_failed(
                error_message=str(e),
                context={
                    "orchestra": self.orchestra_name,
                    "stage": self.stage.value,
                    "duration_seconds": duration
                }
            )

            # Re-raise for caller to handle
            raise

    async def _checkpoint(self, checkpoint_data: Dict[str, Any]) -> None:
        """
        Save an intermediate checkpoint during orchestration.

        This method allows orchestras to save progress at key points
        during execution, enabling recovery or debugging.

        Args:
            checkpoint_data: Data to save in the checkpoint
        """
        await self.run_context.save_checkpoint(checkpoint_data=checkpoint_data)

        log_checkpoint(
            self.logger,
            f"{self.orchestra_name}_checkpoint",
            checkpoint_data
        )

        self.logger.debug(f"Checkpoint saved for {self.orchestra_name}")

    async def _get_context_data(self, key: str, default: Any = None) -> Any:
        """
        Retrieve data from shared run context.

        This enables orchestras to access outputs from previous stages
        or other orchestras in the workflow.

        Args:
            key: Context data key
            default: Value to return if key doesn't exist

        Returns:
            Any: Context data value or default
        """
        value = self.run_context.context_data.get(key, default)

        if value is None and default is None:
            self.logger.warning(
                f"Context key '{key}' not found in run_context for {self.orchestra_name}"
            )

        return value

    async def _set_context_data(self, key: str, value: Any) -> None:
        """
        Store data in shared run context.

        This enables orchestras to make their outputs available to
        subsequent stages in the workflow.

        Args:
            key: Context data key
            value: Value to store
        """
        self.run_context.add_context_data(key, value)

        self.logger.debug(
            f"Context data set for {self.orchestra_name}: key='{key}'"
        )
