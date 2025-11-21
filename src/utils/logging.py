"""Structured logging utilities for the orchestration system.

This module provides logging setup and helper functions for tracking agent execution,
decisions, and checkpoints throughout the workflow.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from rich.logging import RichHandler


def setup_logging(run_id: str, log_dir: Path, level: str = "INFO") -> logging.Logger:
    """Configure structured logging with both console and file output.

    Sets up the root logger with:
    - RichHandler for formatted console output
    - FileHandler for persistent log storage

    Args:
        run_id: Unique run identifier for log file naming
        log_dir: Directory where log files should be stored
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Configured root logger instance
    """
    # Create log directory if it doesn't exist
    log_dir.mkdir(parents=True, exist_ok=True)

    # Create log file path
    log_file = log_dir / f"run-{run_id}.log"

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Console handler with rich formatting
    console_handler = RichHandler(
        rich_tracebacks=True,
        markup=True,
        show_time=True,
        show_path=True
    )
    console_handler.setLevel(getattr(logging, level.upper()))
    console_formatter = logging.Formatter(
        "%(message)s",
        datefmt="[%X]"
    )
    console_handler.setFormatter(console_formatter)

    # File handler with detailed formatting
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)  # Always log DEBUG to file
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_formatter)

    # Add handlers to root logger
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    root_logger.info(f"Logging initialized for run {run_id}")
    root_logger.info(f"Log file: {log_file}")

    return root_logger


def log_agent_start(agent_name: str, inputs: dict[str, Any]) -> None:
    """Log the start of an agent's execution.

    Args:
        agent_name: Name/identifier of the agent starting
        inputs: Dictionary of input parameters for the agent
    """
    logger = logging.getLogger(__name__)
    logger.info(f"[bold blue]Agent START[/bold blue]: {agent_name}", extra={"markup": True})
    logger.debug(f"Agent inputs: {inputs}")


def log_agent_complete(agent_name: str, outputs: dict[str, Any], duration: float) -> None:
    """Log the completion of an agent's execution.

    Args:
        agent_name: Name/identifier of the completed agent
        outputs: Dictionary of output values from the agent
        duration: Execution time in seconds
    """
    logger = logging.getLogger(__name__)
    logger.info(
        f"[bold green]Agent COMPLETE[/bold green]: {agent_name} "
        f"(duration: {duration:.2f}s)",
        extra={"markup": True}
    )
    logger.debug(f"Agent outputs: {outputs}")


def log_decision(decision_name: str, result: bool, details: dict[str, Any]) -> None:
    """Log a decision point in the workflow.

    Args:
        decision_name: Name/description of the decision being made
        result: Boolean result of the decision
        details: Additional context about the decision
    """
    logger = logging.getLogger(__name__)
    result_str = "[bold green]TRUE[/bold green]" if result else "[bold red]FALSE[/bold red]"
    logger.info(
        f"[bold yellow]DECISION[/bold yellow]: {decision_name} = {result_str}",
        extra={"markup": True}
    )
    logger.debug(f"Decision details: {details}")


def log_checkpoint(stage: str, data: dict[str, Any]) -> None:
    """Log a checkpoint in the workflow for state persistence.

    Args:
        stage: Name of the workflow stage being checkpointed
        data: State data to be persisted
    """
    logger = logging.getLogger(__name__)
    logger.info(f"[bold magenta]CHECKPOINT[/bold magenta]: {stage}", extra={"markup": True})
    logger.debug(f"Checkpoint data: {data}")
