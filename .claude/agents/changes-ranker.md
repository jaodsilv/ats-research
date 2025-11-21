# Changes Ranker Agent

## Agent Name

`changes-ranker`

## Description

The Changes Ranker agent ranks all proposed changes (rewrites and removals) by their effectiveness - the quality-to-length ratio that represents how much quality is preserved or improved per character saved. It calculates an effectiveness score for each change, sorts them from most to least effective, applies decision logic to determine which changes should be recommended, and sets a selection threshold for quality delta.

## Agent Type

`general-purpose`

## Task Instructions

When invoked, this agent should:

1. Receive changes with quality_delta calculated
2. Calculate effectiveness score for each change:
   - Effectiveness = quality_delta / length_reduction
   - Higher is better (more quality per character saved)
3. Apply decision logic (`evaluate_change_impact`) to determine if each change should be recommended
4. Sort changes by effectiveness score (descending - best first)
5. Calculate selection threshold based on recommended changes
6. Return ranked changes with recommendation flags and threshold

**NOTE**: This agent uses decision logic functions rather than Task tool for deterministic ranking calculations.

## Input Schema

```yaml
type: object
required:
  - changes_with_delta
properties:
  changes_with_delta:
    type: array
    description: Changes with quality_delta from DeltaCalculator
    items:
      type: object
      required:
        - quality_delta
        - length_reduction
      properties:
        quality_delta:
          type: number
          minimum: -1.0
          maximum: 1.0
        length_reduction:
          type: integer
          minimum: 1
        # Other fields from rewrites or removals
        original_text:
          type: string
        rewritten_text:
          type: string
        text_to_remove:
          type: string
        impact_score:
          type: number
        rationale:
          type: string
```

## Output Schema

```yaml
type: object
required:
  - ranked_changes
  - selection_threshold
properties:
  ranked_changes:
    type: array
    description: Changes ranked by effectiveness (best first)
    items:
      type: object
      required:
        - effectiveness_score
        - recommended
      properties:
        effectiveness_score:
          type: number
          description: quality_delta / length_reduction (higher is better)
          example: 0.00217
        recommended:
          type: boolean
          description: Whether change is recommended for application
          example: true
        # All original fields preserved
        quality_delta:
          type: number
        length_reduction:
          type: integer
        original_text:
          type: string
        rewritten_text:
          type: string
        text_to_remove:
          type: string
        impact_score:
          type: number
        rationale:
          type: string
  selection_threshold:
    type: number
    description: Recommended quality_delta threshold for selection
    example: -0.15
```

## Example Usage

### Input Example

```json
{
  "changes_with_delta": [
    {
      "original_text": "Responsible for leading team",
      "rewritten_text": "Led team",
      "quality_delta": 0.05,
      "length_reduction": 23,
      "rationale": "Stronger verb"
    },
    {
      "text_to_remove": "Proficient in MS Office",
      "impact_score": 0.15,
      "quality_delta": -0.05,
      "length_reduction": 25,
      "rationale": "Generic skill"
    },
    {
      "text_to_remove": "Led AWS migration project",
      "impact_score": 0.85,
      "quality_delta": -0.5,
      "length_reduction": 27,
      "rationale": "High impact - should not remove"
    }
  ]
}
```

### Output Example

```json
{
  "ranked_changes": [
    {
      "original_text": "Responsible for leading team",
      "rewritten_text": "Led team",
      "quality_delta": 0.05,
      "length_reduction": 23,
      "rationale": "Stronger verb",
      "effectiveness_score": 0.00217,
      "recommended": true
    },
    {
      "text_to_remove": "Proficient in MS Office",
      "impact_score": 0.15,
      "quality_delta": -0.05,
      "length_reduction": 25,
      "rationale": "Generic skill",
      "effectiveness_score": -0.002,
      "recommended": true
    },
    {
      "text_to_remove": "Led AWS migration project",
      "impact_score": 0.85,
      "quality_delta": -0.5,
      "length_reduction": 27,
      "rationale": "High impact - should not remove",
      "effectiveness_score": -0.0185,
      "recommended": false
    }
  ],
  "selection_threshold": -0.06
}
```

## Special Instructions

1. **Effectiveness Score Calculation**:
   - Formula: `effectiveness = quality_delta / length_reduction`
   - Positive effectiveness: Quality improves or stays same per character saved (ideal)
   - Zero effectiveness: Neutral change
   - Negative effectiveness: Quality decreases per character saved (trade-off)
   - Higher scores are better (ranked first)

2. **Recommendation Logic** (uses `evaluate_change_impact` from decision_logic):
   - Apply change if:
     - (Low impact removal: impact_score < 0.3) AND (No quality loss: quality_delta ≥ 0), OR
     - Significant quality improvement: quality_delta > 0.1
   - Reject change if:
     - High impact removal: impact_score > 0.6
     - Large quality loss: quality_delta < -0.3

3. **Selection Threshold Calculation**:
   - Threshold = minimum quality_delta among recommended changes - 0.01
   - If no recommended changes: threshold = 0.0
   - Threshold helps identify the cutoff point for safe changes

4. **Ranking Strategy**:
   - Sort by effectiveness_score descending (best first)
   - Best changes: Positive effectiveness (quality improvement while reducing length)
   - Good changes: Near-zero effectiveness (minimal quality loss)
   - Poor changes: High negative effectiveness (significant quality loss per char)

5. **Examples of Effectiveness Scores**:

   | Change Type | Quality Delta | Length Reduction | Effectiveness | Interpretation |
   |-------------|---------------|------------------|---------------|----------------|
   | Rewrite (better verb) | +0.05 | 23 | +0.00217 | Excellent - quality improves |
   | Removal (low impact) | -0.05 | 25 | -0.002 | Good - minimal quality loss |
   | Removal (generic text) | -0.1 | 50 | -0.002 | Good - acceptable trade-off |
   | Removal (medium impact) | -0.2 | 30 | -0.00667 | Moderate - consider carefully |
   | Removal (high impact) | -0.5 | 27 | -0.0185 | Poor - avoid this change |

6. **Usage of Ranked Output**:
   - Apply all recommended changes (recommended=true)
   - Or apply top N changes by effectiveness score
   - Or apply changes until target length reached
   - Or apply changes above selection threshold

## Performance Considerations

- **Processing Time**: < 1 second (deterministic calculation)
- **No LLM Usage**: Pure Python logic using decision functions
- **Input Size**: Typically 10-50 changes
- **Output Size**: Same as input + effectiveness_score and recommended fields

## Quality Checklist

Before returning ranked changes, verify:

1. All changes have effectiveness_score calculated
2. All changes have recommended flag set
3. Changes sorted by effectiveness_score (descending)
4. Selection threshold calculated correctly
5. Recommended changes have acceptable quality_delta
6. High-impact removals marked as not recommended
7. All original fields preserved
8. No division by zero (length_reduction > 0)

## Related Agents

- **DeltaCalculator**: Provides changes with quality_delta (runs before ChangesRanker)
- **ChangeExecutor**: Applies selected changes from ranked list (runs after ChangesRanker)
- **DocumentEvaluator**: May evaluate final document after changes applied (runs after ChangeExecutor)

## Decision Logic Integration

This agent uses the following function from `decision_logic.py`:
- `evaluate_change_impact(change_type, impact_score, quality_delta)` → bool

This function determines if a change should be recommended based on its type, impact, and quality delta.
