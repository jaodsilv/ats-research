"""Quality validation functions for best practices merger.

This module provides validation functions to ensure comprehensive merging of
theoretical practices (R1) with real-world analysis (R2). Each validator checks
a specific quality dimension and returns a validation result with score and details.
"""

from typing import Dict, Any, List, Set
from dataclasses import dataclass
import re
import logging

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of a validation check.

    Attributes:
        passed: Whether validation passed
        score: Numeric score 0-1 (1 = perfect)
        details: Human-readable details about the result
        issues: List of specific issues found (if any)
        coverage: Percentage of items covered (0-100)
    """

    passed: bool
    score: float
    details: str
    issues: List[str]
    coverage: float


def extract_principles_from_r1(r1_content: str) -> List[str]:
    """Extract key principles and recommendations from R1 theoretical content.

    Args:
        r1_content: Markdown content from R1 (theoretical best practices)

    Returns:
        List of identified principles/recommendations
    """
    principles = []

    # Extract headers as principles (## or ### level)
    header_pattern = r'^#{2,3}\s+(.+)$'
    for match in re.finditer(header_pattern, r1_content, re.MULTILINE):
        principle = match.group(1).strip()
        if principle and not principle.lower().startswith(('example', 'note', 'summary')):
            principles.append(principle)

    # Extract bullet points that look like recommendations
    bullet_pattern = r'^\s*[-*]\s+(.+)$'
    for match in re.finditer(bullet_pattern, r1_content, re.MULTILINE):
        item = match.group(1).strip()
        # Only include if it's a substantial recommendation (> 20 chars)
        if len(item) > 20 and ':' in item:
            principles.append(item.split(':')[0].strip())

    # Deduplicate while preserving order
    seen: Set[str] = set()
    unique_principles = []
    for p in principles:
        p_lower = p.lower()
        if p_lower not in seen:
            seen.add(p_lower)
            unique_principles.append(p)

    logger.debug(f"Extracted {len(unique_principles)} principles from R1")
    return unique_principles


def validate_r1_principles(
    r1_content: str,
    merged_guidelines: str,
    min_coverage: float = 0.80
) -> ValidationResult:
    """Validate that R1 theoretical principles are addressed in merged guidelines.

    Args:
        r1_content: Original R1 theoretical best practices
        merged_guidelines: Generated merged guidelines
        min_coverage: Minimum proportion of principles that must be covered (default 80%)

    Returns:
        ValidationResult with coverage details
    """
    principles = extract_principles_from_r1(r1_content)

    if not principles:
        return ValidationResult(
            passed=False,
            score=0.0,
            details="Could not extract principles from R1 content",
            issues=["R1 content appears to have no structured principles"],
            coverage=0.0
        )

    # Check coverage
    merged_lower = merged_guidelines.lower()
    covered = []
    not_covered = []

    for principle in principles:
        # Check if principle or key words from it appear in merged content
        principle_words = set(re.findall(r'\w{4,}', principle.lower()))
        # Require at least 50% of significant words to be present
        matches = sum(1 for word in principle_words if word in merged_lower)
        if principle_words and matches / len(principle_words) >= 0.5:
            covered.append(principle)
        else:
            not_covered.append(principle)

    coverage = len(covered) / len(principles) if principles else 0.0
    passed = coverage >= min_coverage

    issues = []
    if not_covered:
        issues.append(f"{len(not_covered)} principles not adequately addressed:")
        for p in not_covered[:5]:  # Show first 5
            issues.append(f"  - {p}")
        if len(not_covered) > 5:
            issues.append(f"  ... and {len(not_covered) - 5} more")

    details = f"Covered {len(covered)}/{len(principles)} principles ({coverage:.1%})"

    return ValidationResult(
        passed=passed,
        score=coverage,
        details=details,
        issues=issues,
        coverage=coverage * 100
    )


def extract_patterns_from_r2(r2_content: str) -> List[str]:
    """Extract key patterns and insights from R2 real-world analysis.

    Args:
        r2_content: Markdown content from R2 (real-world examples analysis)

    Returns:
        List of identified patterns/insights
    """
    patterns = []

    # Extract headers as patterns
    header_pattern = r'^#{2,4}\s+(.+)$'
    for match in re.finditer(header_pattern, r2_content, re.MULTILINE):
        pattern = match.group(1).strip()
        if pattern and not pattern.lower().startswith(('example', 'note', 'summary', 'conclusion')):
            patterns.append(pattern)

    # Extract list items that describe patterns
    list_pattern = r'^\s*\d+\.\s+(.+)$'
    for match in re.finditer(list_pattern, r2_content, re.MULTILINE):
        item = match.group(1).strip()
        if len(item) > 25:  # Substantial pattern description
            patterns.append(item[:100])  # Truncate long descriptions

    # Deduplicate
    seen: Set[str] = set()
    unique_patterns = []
    for p in patterns:
        p_lower = p.lower()
        if p_lower not in seen:
            seen.add(p_lower)
            unique_patterns.append(p)

    logger.debug(f"Extracted {len(unique_patterns)} patterns from R2")
    return unique_patterns


def validate_r2_examples(
    r2_content: str,
    merged_guidelines: str,
    min_utilization: float = 0.70
) -> ValidationResult:
    """Validate that R2 real-world patterns are utilized with examples.

    Args:
        r2_content: Original R2 real-world analysis
        merged_guidelines: Generated merged guidelines
        min_utilization: Minimum proportion of patterns to be cited (default 70%)

    Returns:
        ValidationResult with utilization details
    """
    patterns = extract_patterns_from_r2(r2_content)

    if not patterns:
        return ValidationResult(
            passed=False,
            score=0.0,
            details="Could not extract patterns from R2 content",
            issues=["R2 content appears to have no structured patterns"],
            coverage=0.0
        )

    # Check utilization
    merged_lower = merged_guidelines.lower()
    utilized = []
    not_utilized = []

    for pattern in patterns:
        # Check if pattern or key concepts appear in merged content
        pattern_words = set(re.findall(r'\w{5,}', pattern.lower()))
        matches = sum(1 for word in pattern_words if word in merged_lower)
        if pattern_words and matches / len(pattern_words) >= 0.4:
            utilized.append(pattern)
        else:
            not_utilized.append(pattern)

    utilization = len(utilized) / len(patterns) if patterns else 0.0
    passed = utilization >= min_utilization

    issues = []
    if not_utilized:
        issues.append(f"{len(not_utilized)} patterns not referenced:")
        for p in not_utilized[:5]:
            issues.append(f"  - {p[:80]}...")
        if len(not_utilized) > 5:
            issues.append(f"  ... and {len(not_utilized) - 5} more")

    # Also check for explicit examples/citations
    example_markers = ['for example', 'e.g.', 'such as', 'specifically', 'demonstrated by']
    example_count = sum(merged_lower.count(marker) for marker in example_markers)

    if example_count < 3:
        issues.append(f"Only {example_count} explicit example citations found (recommend 5+)")

    details = f"Utilized {len(utilized)}/{len(patterns)} patterns ({utilization:.1%}), {example_count} explicit examples"

    return ValidationResult(
        passed=passed,
        score=min(utilization, 1.0),
        details=details,
        issues=issues,
        coverage=utilization * 100
    )


def validate_section_completeness(
    merged_guidelines: str,
    required_sections: List[str] = None
) -> ValidationResult:
    """Validate that all required sections are present with substantial content.

    Args:
        merged_guidelines: Generated merged guidelines
        required_sections: List of required section names (uses defaults if None)

    Returns:
        ValidationResult with section completeness details
    """
    if required_sections is None:
        required_sections = [
            "Structure and Format",
            "Content Strategy",
            "Language and Tone",
            "ATS Optimization",
            "Company Category",  # Matches "Company Category Specific" or similar
            "Pitfalls",  # Matches "Common Pitfalls", "Anti-patterns", etc.
        ]

    merged_lower = merged_guidelines.lower()
    present = []
    missing = []
    insufficient = []

    for section in required_sections:
        section_lower = section.lower()

        # Check if section header exists
        # Match ## Section Name or ### Section Name or similar
        section_pattern = rf'^#{2,4}\s+.*{re.escape(section_lower)}.*$'
        section_match = re.search(section_pattern, merged_lower, re.MULTILINE | re.IGNORECASE)

        if section_match:
            # Extract content after this section (until next same-level header or end)
            start_pos = section_match.end()
            # Find next header at same or higher level
            next_header_pattern = r'\n#{2,4}\s+'
            next_match = re.search(next_header_pattern, merged_guidelines[start_pos:])

            if next_match:
                section_content = merged_guidelines[start_pos:start_pos + next_match.start()]
            else:
                section_content = merged_guidelines[start_pos:]

            # Check if section has substantial content (at least 200 chars, ignoring whitespace)
            content_length = len(section_content.strip())
            if content_length >= 200:
                present.append(section)
            else:
                insufficient.append(f"{section} (only {content_length} chars)")
        else:
            missing.append(section)

    total = len(required_sections)
    present_count = len(present)
    coverage = present_count / total if total else 0.0
    passed = coverage >= 0.85 and len(missing) == 0  # Allow some insufficient, but not missing

    issues = []
    if missing:
        issues.append(f"{len(missing)} required sections missing:")
        for s in missing:
            issues.append(f"  - {s}")

    if insufficient:
        issues.append(f"{len(insufficient)} sections have insufficient content:")
        for s in insufficient:
            issues.append(f"  - {s}")

    details = f"{present_count}/{total} sections present with substantial content ({coverage:.1%})"

    return ValidationResult(
        passed=passed,
        score=coverage,
        details=details,
        issues=issues,
        coverage=coverage * 100
    )


def validate_actionability(
    merged_guidelines: str,
    min_score: float = 0.75
) -> ValidationResult:
    """Validate that guidelines contain actionable, concrete recommendations.

    Args:
        merged_guidelines: Generated merged guidelines
        min_score: Minimum actionability score (default 75%)

    Returns:
        ValidationResult with actionability assessment
    """
    merged_lower = merged_guidelines.lower()

    # Positive indicators (concrete, actionable language)
    positive_indicators = [
        r'\buse\b', r'\bavoid\b', r'\binclude\b', r'\bexclude\b',
        r'\bensure\b', r'\bmust\b', r'\bshould\b', r'\brecommend\b',
        r'\bstart with\b', r'\bend with\b', r'\bplace\b', r'\bposition\b',
        r'\blimit to\b', r'\bkeep.*to\b', r'\bmaintain\b',
        r'\bspecific\b', r'\bconcrete\b', r'\bmeasurable\b',
        r'\bquantify\b', r'\bmetrics?\b', r'\bnumbers?\b',
    ]

    # Negative indicators (vague, non-actionable language)
    negative_indicators = [
        r'\bconsider\b', r'\bmaybe\b', r'\bmight\b', r'\bcould be\b',
        r'\bgenerally\b', r'\btypically\b', r'\boften\b', r'\busually\b',
        r'\bit depends\b', r'\bvaries\b', r'\bsubject to\b',
    ]

    # Count indicators
    positive_count = sum(len(re.findall(pattern, merged_lower)) for pattern in positive_indicators)
    negative_count = sum(len(re.findall(pattern, merged_lower)) for pattern in negative_indicators)

    # Check for concrete examples (numbers, specific tools, specific formats)
    concrete_examples = [
        r'\b\d+%?\b',  # Numbers/percentages
        r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b',  # Proper nouns (tools, companies)
        r'\.(pdf|docx|tex)\b',  # File formats
        r'\b\d+\s+(page|line|word|character)s?\b',  # Specific limits
    ]
    concrete_count = sum(len(re.findall(pattern, merged_guidelines)) for pattern in concrete_examples)

    # Calculate actionability score
    # Positive: each actionable term counts +1
    # Negative: each vague term counts -0.5
    # Concrete examples: each counts +2
    raw_score = positive_count - (negative_count * 0.5) + (concrete_count * 2)

    # Normalize to 0-1 scale (assume 100+ is excellent)
    normalized_score = min(raw_score / 100, 1.0)

    passed = normalized_score >= min_score

    issues = []
    if negative_count > positive_count * 0.3:
        issues.append(
            f"High ratio of vague language ({negative_count} vague terms vs {positive_count} actionable)"
        )

    if concrete_count < 10:
        issues.append(
            f"Insufficient concrete examples ({concrete_count} found, recommend 20+)"
        )

    if positive_count < 30:
        issues.append(
            f"Limited actionable directives ({positive_count} found, recommend 50+)"
        )

    details = (
        f"Actionability score: {normalized_score:.1%} "
        f"({positive_count} actionable terms, {concrete_count} concrete examples, "
        f"{negative_count} vague terms)"
    )

    return ValidationResult(
        passed=passed,
        score=normalized_score,
        details=details,
        issues=issues,
        coverage=normalized_score * 100
    )


def calculate_confidence_score(
    validation_results: Dict[str, ValidationResult],
    weights: Dict[str, float] = None
) -> float:
    """Calculate overall confidence score from validation results.

    Args:
        validation_results: Dict mapping validation names to ValidationResult
        weights: Optional custom weights for each validator (defaults to equal)

    Returns:
        Aggregate confidence score 0-1
    """
    if not validation_results:
        return 0.0

    if weights is None:
        # Default weights
        weights = {
            "r1_principles": 0.30,
            "r2_examples": 0.25,
            "section_completeness": 0.25,
            "actionability": 0.20,
        }

    total_score = 0.0
    total_weight = 0.0

    for name, result in validation_results.items():
        weight = weights.get(name, 1.0 / len(validation_results))
        total_score += result.score * weight
        total_weight += weight

    # Normalize
    confidence = total_score / total_weight if total_weight > 0 else 0.0

    return confidence
