"""Research agents for best practices research workflows.

This package contains agents that handle research and merging of best practices
for resumes and cover letters based on Region/Role/Level tuples.
"""

from .best_practices_merger import BestPracticesMerger

__all__ = [
    "BestPracticesMerger",
]
