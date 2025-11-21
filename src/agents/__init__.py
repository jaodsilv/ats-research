"""Agent implementations for the orchestration system.

This package contains all agent classes that perform specific tasks in the
resume/cover letter tailoring workflow. All agents inherit from BaseAgent.
"""

from .base_agent import BaseAgent
from .agent_pool import AgentPool
from .input_prep import InputReader, DocumentFetcher, JDParser
from .writing import (
    DraftWriter,
    FactChecker,
    RevisedDraftWriter,
    VersionManager,
    DocumentEvaluator,
    IssueFixer,
    DocumentPolisher,
)

__all__ = [
    "BaseAgent",
    "AgentPool",
    "InputReader",
    "DocumentFetcher",
    "JDParser",
    "DraftWriter",
    "FactChecker",
    "RevisedDraftWriter",
    "VersionManager",
    "DocumentEvaluator",
    "IssueFixer",
    "DocumentPolisher",
]
