"""Matching agents for job description and resume analysis.

This package contains agents responsible for matching resumes against job descriptions,
analyzing skills gaps, ranking multiple JDs, and selecting the best candidates for
tailoring.
"""

from .resume_jd_matcher import ResumeJDMatcher
from .jds_ranker_selector import JDsRankerSelector

__all__ = [
    "ResumeJDMatcher",
    "JDsRankerSelector",
]
