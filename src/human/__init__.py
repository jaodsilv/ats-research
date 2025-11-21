"""Human interaction module for human-in-the-loop workflows.

This module provides classes for collecting human feedback during orchestration
workflows, particularly for document review and approval processes.

Components:
- HumanFeedback: Collect feedback on document quality and revisions
- InteractiveWizard: Terminal wizard for initial input collection
"""

from .feedback import HumanFeedback
from .wizard import InteractiveWizard

__all__ = [
    "HumanFeedback",
    "InteractiveWizard",
]
