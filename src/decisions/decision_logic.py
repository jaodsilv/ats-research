"""
Centralized decision logic framework for workflow control.

This module provides pure decision functions for orchestrating the resume/cover letter
tailoring workflow. All functions are stateless and side-effect-free (except logging).

Author: ATS Research Project
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ============================================================================
# Data Classes
# ============================================================================


@dataclass
class DocumentEvaluation:
    """
    Represents the evaluation results of a document (resume or cover letter).

    Attributes:
        score: Quality score from 0.0 (worst) to 1.0 (best)
        has_critical_issues: Whether the document has blocking quality issues
        has_false_facts: Whether the document contains factual inaccuracies
        issue_count: Total number of identified issues
        quality_notes: Human-readable notes about document quality
        metadata: Additional evaluation metadata (e.g., evaluator, timestamp)

    Example:
        >>> eval = DocumentEvaluation(
        ...     score=0.85,
        ...     has_critical_issues=False,
        ...     has_false_facts=False,
        ...     issue_count=2,
        ...     quality_notes="Minor formatting improvements needed",
        ...     metadata={"evaluator": "QualityAgent", "timestamp": "2025-10-20T10:00:00"}
        ... )
    """

    score: float
    has_critical_issues: bool
    has_false_facts: bool
    issue_count: int
    quality_notes: str
    metadata: Dict[str, Any]


@dataclass
class MatchResult:
    """
    Represents the matching result between a resume and a job description.

    Attributes:
        jd_id: Unique identifier for the job description
        match_score: Overall match score from 0.0 (no match) to 1.0 (perfect match)
        relevance_score: Relevance score from 0.0 to 1.0
        matched_keywords: List of keywords found in both resume and JD
        missing_skills: List of required skills not present in resume
        recommendation: Human-readable recommendation text

    Example:
        >>> match = MatchResult(
        ...     jd_id="JD-2025-001",
        ...     match_score=0.78,
        ...     relevance_score=0.82,
        ...     matched_keywords=["Python", "AWS", "Machine Learning"],
        ...     missing_skills=["Kubernetes", "Terraform"],
        ...     recommendation="Strong match - highlight cloud experience"
        ... )
    """

    jd_id: str
    match_score: float
    relevance_score: float
    matched_keywords: List[str]
    missing_skills: List[str]
    recommendation: str


# ============================================================================
# Quality Decisions
# ============================================================================


def has_critical_issues(evaluation: DocumentEvaluation) -> bool:
    """
    Determine if the document has critical quality issues.

    Args:
        evaluation: Document evaluation containing quality metrics

    Returns:
        True if critical issues exist, False otherwise

    Example:
        >>> eval = DocumentEvaluation(
        ...     score=0.6, has_critical_issues=True, has_false_facts=False,
        ...     issue_count=5, quality_notes="Missing contact info",
        ...     metadata={}
        ... )
        >>> has_critical_issues(eval)
        True
    """
    result = evaluation.has_critical_issues
    log_decision(
        decision_name="has_critical_issues",
        result=result,
        details={
            "score": evaluation.score,
            "issue_count": evaluation.issue_count,
            "quality_notes": evaluation.quality_notes,
        },
    )
    return result


def did_score_decrease(current_score: float, previous_score: float) -> bool:
    """
    Determine if the quality score decreased from previous iteration.

    Args:
        current_score: Current quality score (0.0 to 1.0)
        previous_score: Previous quality score (0.0 to 1.0)

    Returns:
        True if score decreased, False otherwise

    Example:
        >>> did_score_decrease(current_score=0.75, previous_score=0.80)
        True
        >>> did_score_decrease(current_score=0.85, previous_score=0.80)
        False
    """
    result = current_score < previous_score
    log_decision(
        decision_name="did_score_decrease",
        result=result,
        details={
            "current_score": current_score,
            "previous_score": previous_score,
            "delta": current_score - previous_score,
        },
    )
    return result


def is_score_good_enough(score: float, threshold: float) -> bool:
    """
    Determine if the quality score meets or exceeds the threshold.

    Args:
        score: Quality score to evaluate (0.0 to 1.0)
        threshold: Minimum acceptable score (0.0 to 1.0)

    Returns:
        True if score >= threshold, False otherwise

    Example:
        >>> is_score_good_enough(score=0.85, threshold=0.80)
        True
        >>> is_score_good_enough(score=0.75, threshold=0.80)
        False
    """
    result = score >= threshold
    log_decision(
        decision_name="is_score_good_enough",
        result=result,
        details={"score": score, "threshold": threshold, "margin": score - threshold},
    )
    return result


def has_false_facts(evaluation: DocumentEvaluation) -> bool:
    """
    Determine if the document contains factual inaccuracies.

    Args:
        evaluation: Document evaluation containing fact-check results

    Returns:
        True if false facts detected, False otherwise

    Example:
        >>> eval = DocumentEvaluation(
        ...     score=0.7, has_critical_issues=False, has_false_facts=True,
        ...     issue_count=1, quality_notes="Inflated job title detected",
        ...     metadata={}
        ... )
        >>> has_false_facts(eval)
        True
    """
    result = evaluation.has_false_facts
    log_decision(
        decision_name="has_false_facts",
        result=result,
        details={
            "score": evaluation.score,
            "quality_notes": evaluation.quality_notes,
        },
    )
    return result


# ============================================================================
# Matching Decisions
# ============================================================================


def should_rank_jds(jd_count: int) -> bool:
    """
    Determine if job descriptions need to be ranked by match score.

    Ranking is only necessary when there are multiple JDs to compare.

    Args:
        jd_count: Number of job descriptions to process

    Returns:
        True if jd_count > 1 (ranking needed), False if jd_count <= 1

    Example:
        >>> should_rank_jds(jd_count=3)
        True
        >>> should_rank_jds(jd_count=1)
        False
        >>> should_rank_jds(jd_count=0)
        False
    """
    result = jd_count > 1
    log_decision(
        decision_name="should_rank_jds",
        result=result,
        details={"jd_count": jd_count},
    )
    return result


def select_top_jds(matches: List[MatchResult], top_n: int = 3) -> List[str]:
    """
    Select the top N job descriptions based on match score.

    Sorts matches by match_score in descending order and returns the IDs
    of the top N matches. If fewer than top_n matches exist, returns all.

    Args:
        matches: List of MatchResult objects to rank
        top_n: Number of top matches to select (default: 3)

    Returns:
        List of jd_ids for the top N matches

    Example:
        >>> matches = [
        ...     MatchResult("JD-001", 0.75, 0.8, [], [], "Good"),
        ...     MatchResult("JD-002", 0.90, 0.85, [], [], "Excellent"),
        ...     MatchResult("JD-003", 0.65, 0.7, [], [], "Fair"),
        ... ]
        >>> select_top_jds(matches, top_n=2)
        ['JD-002', 'JD-001']
    """
    sorted_matches = sorted(matches, key=lambda m: m.match_score, reverse=True)
    top_jd_ids = [match.jd_id for match in sorted_matches[:top_n]]

    log_decision(
        decision_name="select_top_jds",
        result=len(top_jd_ids) > 0,
        details={
            "total_matches": len(matches),
            "top_n": top_n,
            "selected_jd_ids": top_jd_ids,
            "top_scores": [m.match_score for m in sorted_matches[:top_n]],
        },
    )
    return top_jd_ids


# ============================================================================
# Length Decisions
# ============================================================================


def is_length_acceptable(
    actual_length: int, target_length: int, tolerance: float = 0.1
) -> bool:
    """
    Determine if document length is within acceptable range of target.

    Args:
        actual_length: Actual document length (e.g., word count, character count)
        target_length: Target document length
        tolerance: Acceptable deviation as fraction of target (default: 0.1 = 10%)

    Returns:
        True if actual length within target ± (target * tolerance), False otherwise

    Example:
        >>> is_length_acceptable(actual_length=950, target_length=1000, tolerance=0.1)
        True  # 950 is within 900-1100 range
        >>> is_length_acceptable(actual_length=850, target_length=1000, tolerance=0.1)
        False  # 850 is below 900-1100 range
    """
    lower_bound = target_length * (1 - tolerance)
    upper_bound = target_length * (1 + tolerance)
    result = lower_bound <= actual_length <= upper_bound

    log_decision(
        decision_name="is_length_acceptable",
        result=result,
        details={
            "actual_length": actual_length,
            "target_length": target_length,
            "tolerance": tolerance,
            "acceptable_range": f"{lower_bound:.0f}-{upper_bound:.0f}",
        },
    )
    return result


def calculate_length_score(actual_length: int, target_length: int) -> float:
    """
    Calculate a score representing how close actual length is to target.

    Score calculation:
    - 1.0 for exact match
    - Decreases linearly as difference increases
    - Formula: max(0, 1 - abs(actual - target) / target)
    - Minimum score: 0.0

    Args:
        actual_length: Actual document length
        target_length: Target document length

    Returns:
        Score from 0.0 (far from target) to 1.0 (exact match)

    Example:
        >>> calculate_length_score(actual_length=1000, target_length=1000)
        1.0
        >>> calculate_length_score(actual_length=900, target_length=1000)
        0.9
        >>> calculate_length_score(actual_length=500, target_length=1000)
        0.5
    """
    if target_length == 0:
        return 0.0

    score = max(0.0, 1.0 - abs(actual_length - target_length) / target_length)

    log_decision(
        decision_name="calculate_length_score",
        result=score > 0.0,
        details={
            "actual_length": actual_length,
            "target_length": target_length,
            "score": score,
            "difference": abs(actual_length - target_length),
        },
    )
    return score


# ============================================================================
# Iteration Decisions
# ============================================================================


def should_continue_iteration(
    current_iteration: int, max_iterations: int, current_score: float, threshold: float
) -> Tuple[bool, str]:
    """
    Determine if the workflow should continue iterating or stop.

    Stop conditions (in priority order):
    1. Reached max iterations → Stop
    2. Score meets threshold → Stop
    3. Otherwise → Continue

    Args:
        current_iteration: Current iteration number (0-indexed or 1-indexed)
        max_iterations: Maximum allowed iterations
        current_score: Current quality score (0.0 to 1.0)
        threshold: Quality threshold to meet (0.0 to 1.0)

    Returns:
        Tuple of (should_continue, reason):
        - (False, "max_iterations_reached") if max iterations hit
        - (False, "quality_threshold_met") if score >= threshold
        - (True, "needs_improvement") if should continue

    Example:
        >>> should_continue_iteration(5, 5, 0.75, 0.80)
        (False, 'max_iterations_reached')
        >>> should_continue_iteration(3, 5, 0.85, 0.80)
        (False, 'quality_threshold_met')
        >>> should_continue_iteration(3, 5, 0.75, 0.80)
        (True, 'needs_improvement')
    """
    if current_iteration >= max_iterations:
        reason = "max_iterations_reached"
        should_continue = False
    elif current_score >= threshold:
        reason = "quality_threshold_met"
        should_continue = False
    else:
        reason = "needs_improvement"
        should_continue = True

    log_decision(
        decision_name="should_continue_iteration",
        result=should_continue,
        details={
            "current_iteration": current_iteration,
            "max_iterations": max_iterations,
            "current_score": current_score,
            "threshold": threshold,
            "reason": reason,
        },
    )
    return should_continue, reason


# ============================================================================
# Change Evaluation
# ============================================================================


def evaluate_change_impact(
    change_type: str, impact_score: float, quality_delta: float
) -> bool:
    """
    Determine if a pruning/editing change should be applied.

    Apply change if:
    1. Low impact (impact_score < 0.3) AND no quality loss (quality_delta >= 0)
    2. OR significant quality improvement (quality_delta > 0.1)

    Args:
        change_type: Type of change ("removal" or "rewrite")
        impact_score: Impact score from 0.0 (negligible) to 1.0 (critical)
        quality_delta: Quality change from -1.0 (worse) to 1.0 (better)

    Returns:
        True if change should be applied, False if it should be rejected

    Example:
        >>> evaluate_change_impact("removal", impact_score=0.2, quality_delta=0.05)
        True  # Low impact, no quality loss
        >>> evaluate_change_impact("rewrite", impact_score=0.5, quality_delta=0.15)
        True  # Significant quality improvement
        >>> evaluate_change_impact("removal", impact_score=0.5, quality_delta=-0.1)
        False  # Medium impact with quality loss
    """
    # Condition 1: Low impact with no quality loss
    condition_1 = impact_score < 0.3 and quality_delta >= 0

    # Condition 2: Significant quality improvement
    condition_2 = quality_delta > 0.1

    result = condition_1 or condition_2

    log_decision(
        decision_name="evaluate_change_impact",
        result=result,
        details={
            "change_type": change_type,
            "impact_score": impact_score,
            "quality_delta": quality_delta,
            "condition_low_impact": condition_1,
            "condition_quality_improvement": condition_2,
        },
    )
    return result


# ============================================================================
# Logging Helpers
# ============================================================================


def log_decision(decision_name: str, result: bool, details: Dict[str, Any]) -> None:
    """
    Log a decision with its name, result, and supporting details.

    This function provides consistent logging format for all decision functions.
    Logs at INFO level for audit trail and debugging purposes.

    Args:
        decision_name: Name of the decision function
        result: Boolean result of the decision
        details: Dictionary of supporting information (scores, thresholds, etc.)

    Example:
        >>> log_decision(
        ...     decision_name="is_score_good_enough",
        ...     result=True,
        ...     details={"score": 0.85, "threshold": 0.80}
        ... )
        # Logs: "Decision [is_score_good_enough]: True - {'score': 0.85, 'threshold': 0.80}"
    """
    logger.info(f"Decision [{decision_name}]: {result} - {details}")
