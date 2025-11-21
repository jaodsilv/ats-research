"""Writing and polishing agents for resume/cover letter drafting.

This module provides agents for the draft writing and polishing stages:
- DraftWriter: Creates initial resume/cover letter drafts
- FactChecker: Verifies factual accuracy against master resume
- RevisedDraftWriter: Rewrites drafts to fix false facts
- VersionManager: Manages document versions
- DocumentEvaluator: Evaluates draft quality
- IssueFixer: Fixes critical issues in drafts
- DocumentPolisher: Improves draft quality
- AIWrittenDetector: Detects AI-generated writing patterns
- DraftHumanizer: Humanizes AI-detected content
"""

from .draft_writer import DraftWriter
from .fact_checker import FactChecker
from .revised_draft_writer import RevisedDraftWriter
from .version_manager import VersionManager
from .document_evaluator import DocumentEvaluator
from .issue_fixer import IssueFixer
from .document_polisher import DocumentPolisher
from .ai_written_detector import AIWrittenDetector
from .draft_humanizer import DraftHumanizer

__all__ = [
    "DraftWriter",
    "FactChecker",
    "RevisedDraftWriter",
    "VersionManager",
    "DocumentEvaluator",
    "IssueFixer",
    "DocumentPolisher",
    "AIWrittenDetector",
    "DraftHumanizer",
]
