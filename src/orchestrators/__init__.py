"""
Orchestrators package for workflow coordination.

This package provides abstract and concrete orchestrators that coordinate
multiple agents to complete specific workflow stages in the resume/cover
letter tailoring system.

Master Orchestrator:
- TailoringOrchestra: Top-level coordinator for the complete workflow

Writing/Polishing Orchestra Hierarchy:
- BaseWritingPolishingOrchestra: Abstract base class with shared workflow logic
- ResumeWritingPolishingOrchestra: Resume-specific implementation (no AI detection)
- CoverLetterWritingPolishingOrchestra: Cover letter implementation (with AI detection loop)

Pruning Orchestra:
- PruningOrchestra: Document length optimization with human-in-the-loop feedback
"""

from .base_orchestra import BaseOrchestra
from .input_preparation_orchestra import InputPreparationOrchestra
from .jd_matching_orchestra import JDMatchingOrchestra
from .fact_checking_loop_orchestra import FactCheckingLoopOrchestra
from .writing_polishing_orchestra import BaseWritingPolishingOrchestra
from .resume_writing_polishing_orchestra import ResumeWritingPolishingOrchestra
from .cover_letter_writing_polishing_orchestra import CoverLetterWritingPolishingOrchestra
from .pruning_orchestra import PruningOrchestra
from .tailoring_orchestra import TailoringOrchestra

__all__ = [
    "BaseOrchestra",
    "InputPreparationOrchestra",
    "JDMatchingOrchestra",
    "FactCheckingLoopOrchestra",
    "BaseWritingPolishingOrchestra",
    "ResumeWritingPolishingOrchestra",
    "CoverLetterWritingPolishingOrchestra",
    "PruningOrchestra",
    "TailoringOrchestra",
]
