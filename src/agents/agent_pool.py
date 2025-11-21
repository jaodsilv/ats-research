"""
AgentPool - Configurable async parallelism for agent execution.

This module provides the AgentPool class for managing concurrent execution of agents
with configurable concurrency limits. Supports unlimited, sequential, or bounded
parallel execution patterns.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Awaitable, Callable, Generic, List, Optional, TypeVar, TYPE_CHECKING

if TYPE_CHECKING:
    from .base_agent import BaseAgent

# Type variable for generic agent outputs
T = TypeVar('T')


class AgentPool:
    """Manages concurrent execution of agents with configurable parallelism.

    The AgentPool controls how many agents can run concurrently:
    - pool_size=None: Unlimited concurrency (all agents run in parallel)
    - pool_size=1: Sequential execution (one agent at a time)
    - pool_size=N: Max N agents running concurrently

    Examples:
        >>> # Unlimited concurrency
        >>> pool = AgentPool(pool_size=None)
        >>> results = await pool.execute_agents(agents, inputs)

        >>> # Sequential execution
        >>> pool = AgentPool(pool_size=1)
        >>> results = await pool.execute_agents(agents, inputs)

        >>> # Max 5 concurrent agents
        >>> pool = AgentPool(pool_size=5)
        >>> results = await pool.execute_agents(agents, inputs)

        >>> # Batch execution with agent factory
        >>> pool = AgentPool(pool_size=3)
        >>> results = await pool.execute_batches(
        ...     agent_factory=lambda input_data: MyAgent(config),
        ...     inputs=job_descriptions
        ... )
    """

    def __init__(self, pool_size: Optional[int] = None):
        """Initialize the AgentPool.

        Args:
            pool_size: Maximum number of concurrent agents.
                      None = unlimited concurrency
                      1 = sequential execution
                      N = max N concurrent agents
        """
        self._pool_size = pool_size
        self._semaphore: Optional[asyncio.Semaphore] = None

        if pool_size is not None:
            if pool_size < 1:
                raise ValueError(f"pool_size must be >= 1 or None, got {pool_size}")
            self._semaphore = asyncio.Semaphore(pool_size)

        self._logger = logging.getLogger(__name__)
        self._logger.info(
            f"AgentPool initialized with pool_size={pool_size} "
            f"({'unlimited' if pool_size is None else f'max {pool_size}'} concurrency)"
        )

    @property
    def pool_size(self) -> Optional[int]:
        """Return the configured pool size.

        Returns:
            Pool size (None means unlimited concurrency)
        """
        return self._pool_size

    def get_effective_concurrency(self) -> Optional[int]:
        """Get the effective concurrency limit.

        Returns:
            Current pool size (None means unlimited)
        """
        return self._pool_size

    async def _execute_one(
        self,
        agent: "BaseAgent",
        input_data: Any,
        index: int
    ) -> tuple[int, Any]:
        """Execute a single agent with semaphore control.

        Args:
            agent: Agent to execute
            input_data: Input data for the agent
            index: Index of this agent in the batch (for output ordering)

        Returns:
            Tuple of (index, result) where result is either the agent output
            or an Exception if the agent failed
        """
        start_time = datetime.now()
        agent_name = getattr(agent, '__class__', type(agent)).__name__

        try:
            if self._semaphore is not None:
                # Bounded concurrency - acquire semaphore
                async with self._semaphore:
                    self._logger.debug(
                        f"Agent {index} ({agent_name}) started "
                        f"(pool utilization: {self._pool_size - self._semaphore._value}/{self._pool_size})"
                    )
                    result = await agent.run(input_data)
            else:
                # Unlimited concurrency - no semaphore
                self._logger.debug(f"Agent {index} ({agent_name}) started (unlimited pool)")
                result = await agent.run(input_data)

            duration = (datetime.now() - start_time).total_seconds()
            self._logger.debug(
                f"Agent {index} ({agent_name}) completed successfully in {duration:.2f}s"
            )
            return (index, result)

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            self._logger.error(
                f"Agent {index} ({agent_name}) failed after {duration:.2f}s: {e}",
                exc_info=True
            )
            return (index, e)

    async def execute_agents(
        self,
        agents: List["BaseAgent"],
        inputs: List[Any]
    ) -> List[Any]:
        """Execute multiple agents in parallel with concurrency control.

        Executes agents concurrently (subject to pool_size limits) and returns
        results in the same order as the input lists. If an agent fails, the
        exception is included in the results list at the corresponding position.

        Args:
            agents: List of agent instances to execute
            inputs: List of input data (one per agent, must match length)

        Returns:
            List of results in the same order as inputs. Each result is either
            the agent's output or an Exception if the agent failed.

        Raises:
            ValueError: If agents and inputs lists have different lengths

        Example:
            >>> pool = AgentPool(pool_size=3)
            >>> agents = [Agent1(), Agent2(), Agent3()]
            >>> inputs = [input1, input2, input3]
            >>> results = await pool.execute_agents(agents, inputs)
            >>> for i, result in enumerate(results):
            ...     if isinstance(result, Exception):
            ...         print(f"Agent {i} failed: {result}")
            ...     else:
            ...         print(f"Agent {i} succeeded: {result}")
        """
        if len(agents) != len(inputs):
            raise ValueError(
                f"agents and inputs must have same length "
                f"(got {len(agents)} agents and {len(inputs)} inputs)"
            )

        if not agents:
            self._logger.warning("execute_agents called with empty agent list")
            return []

        self._logger.info(
            f"Executing {len(agents)} agents with "
            f"{'unlimited' if self._pool_size is None else f'pool_size={self._pool_size}'} concurrency"
        )

        start_time = datetime.now()

        # Execute all agents concurrently (with semaphore limiting if pool_size set)
        tasks = [
            self._execute_one(agent, input_data, index)
            for index, (agent, input_data) in enumerate(zip(agents, inputs))
        ]

        # Gather results (index, result) tuples
        index_results = await asyncio.gather(*tasks, return_exceptions=False)

        # Sort by index to preserve input order
        sorted_results = sorted(index_results, key=lambda x: x[0])

        # Extract just the results (drop indices)
        results = [result for _, result in sorted_results]

        duration = (datetime.now() - start_time).total_seconds()

        # Count successes and failures
        failures = sum(1 for r in results if isinstance(r, Exception))
        successes = len(results) - failures

        self._logger.info(
            f"Completed {len(agents)} agents in {duration:.2f}s "
            f"({successes} succeeded, {failures} failed)"
        )

        return results

    async def execute_batches(
        self,
        agent_factory: Callable[[Any], "BaseAgent"],
        inputs: List[Any]
    ) -> List[Any]:
        """Execute a batch of agents created from a factory function.

        Creates one agent instance per input using the factory function,
        then executes all agents in parallel with concurrency control.
        This is useful for "one agent per item" patterns, such as creating
        one tailoring agent per job description.

        Args:
            agent_factory: Function that takes an input and returns an agent instance
            inputs: List of input data (one agent will be created per input)

        Returns:
            List of results in the same order as inputs

        Example:
            >>> pool = AgentPool(pool_size=5)
            >>>
            >>> def create_tailoring_agent(job_description):
            ...     return TailoringAgent(config=config, job_desc=job_description)
            >>>
            >>> job_descriptions = [jd1, jd2, jd3, jd4, jd5]
            >>> results = await pool.execute_batches(
            ...     agent_factory=create_tailoring_agent,
            ...     inputs=job_descriptions
            ... )
        """
        self._logger.info(f"Creating {len(inputs)} agents from factory")

        # Create one agent per input
        agents = [agent_factory(input_data) for input_data in inputs]

        # Execute all agents using the main execute_agents method
        return await self.execute_agents(agents, inputs)


# Example usage
if __name__ == "__main__":
    import asyncio

    # Mock agent for demonstration
    class MockAgent:
        def __init__(self, name: str, delay: float = 0.1):
            self.name = name
            self.delay = delay

        async def run(self, input_data: Any) -> str:
            await asyncio.sleep(self.delay)
            return f"{self.name} processed: {input_data}"

    async def demo_unlimited():
        """Demo: Unlimited concurrency"""
        print("\n=== Unlimited Concurrency ===")
        pool = AgentPool(pool_size=None)

        agents = [MockAgent(f"Agent{i}") for i in range(5)]
        inputs = [f"input{i}" for i in range(5)]

        results = await pool.execute_agents(agents, inputs)
        for i, result in enumerate(results):
            print(f"Result {i}: {result}")

    async def demo_sequential():
        """Demo: Sequential execution"""
        print("\n=== Sequential Execution (pool_size=1) ===")
        pool = AgentPool(pool_size=1)

        agents = [MockAgent(f"Agent{i}") for i in range(5)]
        inputs = [f"input{i}" for i in range(5)]

        results = await pool.execute_agents(agents, inputs)
        for i, result in enumerate(results):
            print(f"Result {i}: {result}")

    async def demo_bounded():
        """Demo: Bounded concurrency"""
        print("\n=== Bounded Concurrency (pool_size=3) ===")
        pool = AgentPool(pool_size=3)

        agents = [MockAgent(f"Agent{i}") for i in range(5)]
        inputs = [f"input{i}" for i in range(5)]

        results = await pool.execute_agents(agents, inputs)
        for i, result in enumerate(results):
            print(f"Result {i}: {result}")

    async def demo_batch():
        """Demo: Batch execution with factory"""
        print("\n=== Batch Execution with Factory ===")
        pool = AgentPool(pool_size=2)

        def agent_factory(input_data):
            return MockAgent(f"BatchAgent-{input_data}")

        inputs = [f"job{i}" for i in range(4)]

        results = await pool.execute_batches(agent_factory, inputs)
        for i, result in enumerate(results):
            print(f"Result {i}: {result}")

    async def demo_error_handling():
        """Demo: Error handling"""
        print("\n=== Error Handling ===")

        class FailingAgent:
            def __init__(self, should_fail: bool):
                self.should_fail = should_fail

            async def run(self, input_data: Any) -> str:
                await asyncio.sleep(0.05)
                if self.should_fail:
                    raise ValueError(f"Agent failed on {input_data}")
                return f"Success: {input_data}"

        pool = AgentPool(pool_size=3)
        agents = [FailingAgent(i % 2 == 0) for i in range(5)]
        inputs = [f"input{i}" for i in range(5)]

        results = await pool.execute_agents(agents, inputs)
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"Result {i}: ERROR - {result}")
            else:
                print(f"Result {i}: {result}")

    async def main():
        """Run all demos"""
        logging.basicConfig(level=logging.INFO)

        await demo_unlimited()
        await demo_sequential()
        await demo_bounded()
        await demo_batch()
        await demo_error_handling()

    asyncio.run(main())
