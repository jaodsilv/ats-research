"""Prompt templates for best practices merger stages.

This module provides structured prompt templates for different stages of the
iterative merging process, requesting JSON output for easier parsing and validation.
"""

from typing import Dict, Any, List


def build_initial_merge_prompt(
    r1_content: str,
    r2_content: str,
    document_type: str,
    region: str,
    role: str,
    level: str
) -> str:
    """Build the initial comprehensive merge prompt.

    Args:
        r1_content: Theoretical best practices content
        r2_content: Real-world analysis content
        document_type: "resume" or "cover_letter"
        region: Geographic region
        role: Job role
        level: Seniority level

    Returns:
        Formatted prompt string requesting structured JSON output
    """
    doc_type_display = document_type.replace("_", " ").title()

    return f"""# {doc_type_display} Best Practices Comprehensive Merger

## Objective
Create a comprehensive, actionable best practices guide for {document_type}s by synthesizing theoretical research with real-world evidence.

## Target Audience
- **Region**: {region}
- **Role**: {role}
- **Seniority Level**: {level}

## Source Materials

### R1: Theoretical Best Practices
```
{r1_content}
```

### R2: Real-World Examples Analysis
```
{r2_content}
```

## Task Instructions

### 1. Analyze All R1 Principles
- Extract EVERY principle, recommendation, and guideline from R1
- Understand the theoretical foundations for each
- Note any region/role/level-specific advice
- Identify ATS optimization strategies

### 2. Extract All R2 Patterns
- Review the complete real-world analysis across all company categories:
  - FAANG/MAMAA companies
  - Startups and Unicorns
  - Enterprise organizations
- Identify successful patterns (what works and why)
- Extract specific examples and evidence
- Note formatting, structure, language, and tone patterns
- Identify quantification and metrics usage
- Document company-category-specific differences

### 3. Identify Anti-Patterns
- What causes {document_type}s to fail?
- Common mistakes from failed examples
- ATS rejection patterns
- Red flags and pitfalls

### 4. Synthesize Comprehensive Guidelines

Create a detailed, well-organized markdown document with these sections:

#### A. Executive Summary
- 2-3 paragraphs summarizing the merged insights
- Key philosophy and approach
- Critical success factors

#### B. Key Takeaways
- 7-10 bullet points with the most critical insights
- Prioritized by impact and frequency
- Actionable and specific
- Include evidence from R2 where applicable

#### C. Structure and Format
- Document structure and organization
- Section ordering and hierarchy
- Length guidelines (specific numbers)
- File format recommendations
- ATS-friendly formatting rules
- White space and readability
- Provide specific examples from R2

#### D. Content Strategy
- What to include and what to exclude
- How to prioritize content
- Quantification and metrics (with examples)
- Achievement framing
- Tailoring strategies
- Evidence-based recommendations from R2

#### E. Language and Tone
- Writing style guidelines
- Active vs passive voice
- Technical terminology usage
- Industry-specific language
- Tone for different company types (FAANG vs Startup vs Enterprise)
- Concrete examples from successful R2 cases

#### F. ATS Optimization
- Keyword strategies
- Formatting for ATS systems
- Common ATS pitfalls to avoid
- File format considerations
- Testing and validation approaches

#### G. Company Category Specifics
- FAANG/MAMAA: Specific strategies and expectations
- Startups/Unicorns: Unique considerations
- Enterprise: Key differences
- Use concrete examples from R2 analysis

#### H. Common Pitfalls and Anti-Patterns
- What to avoid (with reasons why)
- Failed patterns from R2 analysis
- ATS rejection causes
- Recovery strategies

#### I. Templates and Examples
- Provide 2-3 concrete example snippets
- Before/after comparisons if available from R2
- Annotated examples explaining why they work

### 5. Quality Requirements

- **Comprehensive**: Address EVERY principle from R1
- **Evidence-Based**: Cite specific patterns and examples from R2
- **Actionable**: Use specific, concrete directives (not vague suggestions)
- **Organized**: Clear hierarchy and logical flow
- **Specific**: Include numbers, formats, and concrete examples
- **Balanced**: Acknowledge trade-offs and different approaches for different contexts

## Output Format

Respond with a JSON object containing:

```json
{{
  "merged_guidelines": "<complete markdown document as described above>",
  "key_takeaways": [
    "<actionable insight 1>",
    "<actionable insight 2>",
    "... (7-10 total)"
  ],
  "patterns_identified": [
    "<key pattern 1 from synthesis>",
    "<key pattern 2 from synthesis>",
    "... (10-15 total)"
  ],
  "sources_count": <estimated number of examples/sources analyzed in R2>,
  "confidence_notes": "<brief note on confidence level and any limitations>"
}}
```

The `merged_guidelines` field should contain the complete, production-ready markdown document with all sections above.

Ensure your output:
- Is comprehensive (5000+ words for the merged_guidelines)
- References specific examples from R2
- Provides concrete, actionable advice
- Organizes information logically
- Maintains professional quality throughout
"""


def build_refinement_prompt(
    r1_content: str,
    r2_content: str,
    previous_merge: str,
    validation_issues: List[str],
    document_type: str,
    region: str,
    role: str,
    level: str
) -> str:
    """Build a refinement prompt to address specific validation gaps.

    Args:
        r1_content: Original theoretical best practices
        r2_content: Original real-world analysis
        previous_merge: The previous merge attempt
        validation_issues: List of specific issues to address
        document_type: "resume" or "cover_letter"
        region: Geographic region
        role: Job role
        level: Seniority level

    Returns:
        Formatted refinement prompt
    """
    doc_type_display = document_type.replace("_", " ").title()
    issues_formatted = "\n".join(f"- {issue}" for issue in validation_issues)

    return f"""# {doc_type_display} Best Practices Refinement

## Context
You previously generated a merged best practices guide, but validation identified specific gaps that need to be addressed.

## Target Audience
- **Region**: {region}
- **Role**: {role}
- **Level**: {level}

## Validation Issues Identified
{issues_formatted}

## Source Materials (for reference)

### R1: Theoretical Best Practices
```
{r1_content}
```

### R2: Real-World Analysis
```
{r2_content}
```

### Previous Merge Attempt
```markdown
{previous_merge}
```

## Refinement Task

Your task is to **improve the previous merge** by:

1. **Addressing Each Issue**: For every validation issue listed above, make specific improvements
2. **Preserving Quality**: Keep the good parts of the previous merge
3. **Adding Missing Content**: If principles from R1 or patterns from R2 were not addressed, add them
4. **Enhancing Examples**: Add more concrete examples and citations from R2
5. **Improving Actionability**: Replace any vague language with specific directives
6. **Completing Sections**: Expand any sections that were insufficient

## Specific Focus Areas

Based on the validation issues:
- If R1 principles are missing: Explicitly incorporate them with explanations
- If R2 examples are underutilized: Add specific citations and examples
- If sections are incomplete: Expand with substantial, high-quality content (200+ chars per section)
- If language is vague: Use concrete terms, specific numbers, actionable directives

## Output Format

Respond with a JSON object:

```json
{{
  "merged_guidelines": "<improved complete markdown document>",
  "key_takeaways": ["<updated list of 7-10 key insights>"],
  "patterns_identified": ["<updated list of 10-15 key patterns>"],
  "sources_count": <number>,
  "confidence_notes": "<note on improvements made>",
  "changes_made": [
    "<specific change 1>",
    "<specific change 2>",
    "... (list major improvements)"
  ]
}}
```

The improved `merged_guidelines` should:
- Address all validation issues
- Maintain or improve the quality of good existing content
- Be comprehensive and production-ready
- Include 7-10 key takeaways that are highly actionable
"""


def build_validation_prompt(
    merged_guidelines: str,
    r1_content: str,
    r2_content: str
) -> str:
    """Build a self-validation prompt for Claude to assess the merge quality.

    Args:
        merged_guidelines: The merged guidelines to validate
        r1_content: Original R1 content for comparison
        r2_content: Original R2 content for comparison

    Returns:
        Validation assessment prompt
    """
    return f"""# Self-Validation Assessment

## Task
Assess the quality and completeness of the following merged best practices guidelines.

## Merged Guidelines to Assess
```markdown
{merged_guidelines}
```

## Source Materials (for reference)

### R1: Theoretical Principles
```
{r1_content}
```

### R2: Real-World Analysis
```
{r2_content}
```

## Validation Criteria

Assess the merged guidelines against these criteria:

### 1. R1 Coverage
- Are all major principles from R1 addressed?
- List any R1 principles that are missing or underrepresented

### 2. R2 Utilization
- Are real-world patterns from R2 cited with examples?
- Is there evidence of incorporating R2 insights?
- List any R2 patterns that should be referenced but aren't

### 3. Section Completeness
Required sections:
- Executive Summary
- Key Takeaways (7-10 items)
- Structure and Format
- Content Strategy
- Language and Tone
- ATS Optimization
- Company Category Specifics
- Common Pitfalls
- Templates/Examples

Assess: Which sections are missing or have insufficient content (<200 chars)?

### 4. Actionability
- Are recommendations specific and concrete?
- Are there measurable guidelines (numbers, formats, etc.)?
- Is vague language minimized?
- List any areas that are too vague

## Output Format

```json
{{
  "r1_coverage": {{
    "score": <0-1>,
    "missing_principles": ["<principle 1>", "..."],
    "assessment": "<brief assessment>"
  }},
  "r2_utilization": {{
    "score": <0-1>,
    "missing_patterns": ["<pattern 1>", "..."],
    "example_count": <number of explicit R2 citations>,
    "assessment": "<brief assessment>"
  }},
  "section_completeness": {{
    "score": <0-1>,
    "missing_sections": ["<section 1>", "..."],
    "insufficient_sections": ["<section 1>", "..."],
    "assessment": "<brief assessment>"
  }},
  "actionability": {{
    "score": <0-1>,
    "vague_areas": ["<area 1>", "..."],
    "concrete_examples_count": <number>,
    "assessment": "<brief assessment>"
  }},
  "overall_confidence": <0-1>,
  "overall_assessment": "<2-3 sentence summary>",
  "recommended_improvements": [
    "<improvement 1>",
    "<improvement 2>",
    "... (3-5 most important improvements)"
  ]
}}
```

Be honest and critical in your assessment. The goal is to produce the highest quality guidelines possible.
"""


def build_metadata_header(
    document_type: str,
    region: str,
    role: str,
    level: str,
    confidence_score: float,
    validation_summary: Dict[str, Any]
) -> str:
    """Build metadata header for merged guidelines.

    Args:
        document_type: Type of document
        region: Geographic region
        role: Job role
        level: Seniority level
        confidence_score: Overall confidence score
        validation_summary: Summary of validation results

    Returns:
        Formatted metadata header
    """
    from datetime import datetime

    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")

    return f"""---
title: Best Practices for {document_type.replace('_', ' ').title()}s
region: {region}
role: {role}
level: {level}
generated: {date_str}
confidence_score: {confidence_score:.2f}
validation:
  r1_coverage: {validation_summary.get('r1_principles', {}).get('score', 0):.2f}
  r2_utilization: {validation_summary.get('r2_examples', {}).get('score', 0):.2f}
  section_completeness: {validation_summary.get('section_completeness', {}).get('score', 0):.2f}
  actionability: {validation_summary.get('actionability', {}).get('score', 0):.2f}
---

"""
