# Delta Calculator Agent

## Agent Name

`delta-calculator`

## Description

The Delta Calculator agent calculates the quality delta (change in overall document quality) for each proposed change (rewrite or removal). It evaluates how each change affects the document by considering impact scores, keyword preservation, clarity, and completeness. This quality delta is essential for ranking changes and selecting the most effective modifications that minimize quality loss while achieving length reduction goals.

## Agent Type

`general-purpose`

## Task Instructions

When invoked, this agent should:

1. Receive list of proposed changes (rewrites and removals)
2. For each change, calculate quality delta:
   - **Rewrites**: Consider impact_delta if provided, evaluate clarity and keyword preservation
   - **Removals**: Base delta on impact_score (higher impact = more negative delta)
3. Add quality_delta field (-1.0 to +1.0) to each change
4. Preserve all original fields from input changes
5. Return all changes with quality_delta added

## Input Schema

```yaml
type: object
required:
  - changes
properties:
  changes:
    type: array
    description: Combined list of rewrite and removal options
    items:
      type: object
      description: Can be either rewrite or removal change
      properties:
        # For rewrites
        original_text:
          type: string
        rewritten_text:
          type: string
        impact_delta:
          type: number
        # For removals
        text_to_remove:
          type: string
        impact_score:
          type: number
        # Common fields
        length_reduction:
          type: integer
        rationale:
          type: string
```

## Output Schema

```yaml
type: object
required:
  - changes_with_delta
properties:
  changes_with_delta:
    type: array
    description: All changes with quality_delta field added
    items:
      type: object
      required:
        - quality_delta
      properties:
        quality_delta:
          type: number
          minimum: -1.0
          maximum: 1.0
          description: Change in overall document quality
          example: -0.05
        # All original fields preserved
        original_text:
          type: string
        rewritten_text:
          type: string
        text_to_remove:
          type: string
        impact_score:
          type: number
        impact_delta:
          type: number
        length_reduction:
          type: integer
        rationale:
          type: string
```

## Example Usage

### Input Example

```json
{
  "changes": [
    {
      "original_text": "Responsible for leading a team of engineers",
      "rewritten_text": "Led engineering team",
      "impact_delta": 0.05,
      "length_reduction": 23,
      "rationale": "Stronger verb, maintains meaning"
    },
    {
      "text_to_remove": "Proficient in Microsoft Office",
      "impact_score": 0.15,
      "length_reduction": 33,
      "rationale": "Generic skill not in JD"
    },
    {
      "text_to_remove": "Led microservices architecture implementation",
      "impact_score": 0.85,
      "length_reduction": 47,
      "rationale": "High impact content - should NOT remove"
    }
  ]
}
```

### Output Example

```json
{
  "changes_with_delta": [
    {
      "original_text": "Responsible for leading a team of engineers",
      "rewritten_text": "Led engineering team",
      "impact_delta": 0.05,
      "length_reduction": 23,
      "rationale": "Stronger verb, maintains meaning",
      "quality_delta": 0.05
    },
    {
      "text_to_remove": "Proficient in Microsoft Office",
      "impact_score": 0.15,
      "length_reduction": 33,
      "rationale": "Generic skill not in JD",
      "quality_delta": -0.05
    },
    {
      "text_to_remove": "Led microservices architecture implementation",
      "impact_score": 0.85,
      "length_reduction": 47,
      "rationale": "High impact content - should NOT remove",
      "quality_delta": -0.5
    }
  ]
}
```

## Special Instructions

1. **Quality Delta Calculation for Rewrites**:
   - If `impact_delta` provided, use it as quality_delta
   - Positive delta: Change improves quality (stronger verbs, better clarity)
   - Zero delta: Change maintains quality (just shorter)
   - Negative delta: Change reduces quality (loses information/clarity)
   - Range: Typically -0.2 to +0.3 for rewrites

2. **Quality Delta Calculation for Removals**:
   - Quality delta is typically negative (removing content reduces completeness)
   - Formula based on impact_score:
     - Impact 0.0-0.2 → delta ≈ -0.05 to -0.1 (minor quality loss)
     - Impact 0.2-0.4 → delta ≈ -0.1 to -0.2 (moderate quality loss)
     - Impact 0.4-0.6 → delta ≈ -0.2 to -0.4 (significant quality loss)
     - Impact > 0.6 → delta < -0.4 (major quality loss - should not remove!)

3. **Quality Delta Scale**:
   - **-1.0 to -0.5**: Major quality degradation (avoid)
   - **-0.5 to -0.2**: Moderate quality loss (acceptable if necessary)
   - **-0.2 to -0.1**: Minor quality loss (acceptable)
   - **-0.1 to +0.1**: Negligible change (ideal)
   - **+0.1 to +0.3**: Quality improvement (excellent)
   - **+0.3 to +1.0**: Significant quality improvement (rare)

4. **Examples of Quality Deltas**:

   **Rewrites**:
   | Original | Rewritten | Impact Delta | Quality Delta |
   |----------|-----------|--------------|---------------|
   | "Responsible for managing" | "Managed" | +0.05 | +0.05 |
   | "Successfully implemented" | "Implemented" | 0.0 | 0.0 |
   | "Led team of 5 engineers" | "Led team" | -0.1 | -0.1 |

   **Removals**:
   | Text to Remove | Impact Score | Quality Delta |
   |----------------|--------------|---------------|
   | "Hobbies: photography" | 0.05 | -0.05 |
   | "Proficient in MS Office" | 0.15 | -0.08 |
   | "Team player" | 0.25 | -0.12 |
   | "Experience with AWS" | 0.75 | -0.45 |

5. **Decision Support**:
   - Changes with quality_delta > -0.1 are generally safe
   - Changes with quality_delta -0.1 to -0.2 acceptable if needed
   - Changes with quality_delta < -0.2 require careful consideration
   - Changes with quality_delta < -0.4 should be avoided

## Performance Considerations

- **Processing Time**: 10-25 seconds (LLM analysis)
- **Input Size**: Typically 10-50 changes to process
- **LLM Token Usage**: 1000-2500 tokens
- **Output Size**: Same as input + quality_delta field per change

## Quality Checklist

Before returning changes with delta, verify:

1. All changes have quality_delta field added
2. Quality deltas are in valid range [-1.0, 1.0]
3. Rewrite deltas align with impact_delta if provided
4. Removal deltas correlate with impact_score
5. High-impact removals (> 0.6) have large negative deltas
6. Low-impact removals (< 0.2) have small negative deltas
7. All original fields preserved
8. Quality deltas are realistic and justified

## Related Agents

- **RewritingEvaluator**: Provides rewrite options (runs before DeltaCalculator)
- **RemovalEvaluator**: Provides removal options (runs before DeltaCalculator)
- **DocumentEvaluator**: May be used as sub-agent to calculate before/after quality (optional)
- **ChangesRanker**: Uses quality_delta for ranking (runs after DeltaCalculator)
