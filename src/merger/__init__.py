"""Best Practices Merger package for iterative merging with quality validation.

This package provides the core merging engine and validation infrastructure for
synthesizing theoretical best practices (R1) with real-world analysis (R2) into
comprehensive, actionable guidelines.

Modules:
    merger_engine: Iterative merge orchestration with Claude API
    validators: Quality validation functions for merge completeness
    prompts: Structured prompt templates for different merge stages
"""

from .merger_engine import MergerEngine
from .validators import (
    validate_r1_principles,
    validate_r2_examples,
    validate_section_completeness,
    validate_actionability,
    calculate_confidence_score,
)

__all__ = [
    "MergerEngine",
    "validate_r1_principles",
    "validate_r2_examples",
    "validate_section_completeness",
    "validate_actionability",
    "calculate_confidence_score",
]
