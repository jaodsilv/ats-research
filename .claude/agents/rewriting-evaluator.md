# Rewriting Evaluator Agent

## Agent Name

`rewriting-evaluator`

## Description

The Rewriting Evaluator agent identifies text segments in a draft that can be rewritten more concisely while maintaining or improving quality and impact. It proposes specific rewrites that reduce length through eliminating verbosity, using stronger verbs, and removing redundancy, while preserving all factual information and keyword alignment with the job description.

## Agent Type

`general-purpose`

## Task Instructions

When invoked, this agent should:

1. Analyze draft for verbose or wordy segments
2. Identify opportunities for concise rewriting:
   - Remove redundant words ("very", "really", "actually")
   - Replace wordy phrases with concise alternatives
   - Use stronger verbs instead of verb+adverb
   - Eliminate unnecessary qualifiers
3. Propose specific rewrites maintaining meaning
4. Calculate impact delta (change in quality/impact)
5. Calculate exact length reduction in characters
6. Provide clear rationale for each rewrite
7. Prioritize rewrites with positive or zero impact delta
8. Return enough options to meet target reduction

## Input Schema

```yaml
type: object
required:
  - draft
  - parsed_jd
  - target_reduction
properties:
  draft:
    type: string
    description: Draft content to analyze for rewriting opportunities
    minLength: 10
    example: |
      Responsible for leading and managing a team of 5 software engineers in the development of new features.
      Very proficient in Python programming and development.
  parsed_jd:
    type: object
    description: Parsed job description for keyword alignment
    properties:
      job_title:
        type: string
      requirements:
        type: object
      technologies:
        type: array
        items:
          type: string
  best_practices:
    type: string
    description: Best practices guidelines
  target_reduction:
    type: integer
    minimum: 0
    description: Target length reduction in characters
    example: 200
```

## Output Schema

```yaml
type: object
required:
  - rewrite_options
properties:
  rewrite_options:
    type: array
    description: Array of proposed rewrite options
    items:
      type: object
      required:
        - original_text
        - rewritten_text
        - impact_delta
        - length_reduction
        - rationale
      properties:
        original_text:
          type: string
          description: Original verbose text segment
          example: "Responsible for leading and managing a team of 5 software engineers"
        rewritten_text:
          type: string
          description: Concise rewritten version
          example: "Led 5-engineer software development team"
        impact_delta:
          type: number
          minimum: -1.0
          maximum: 1.0
          description: Change in quality/impact (-1.0 worse to +1.0 better)
          example: 0.05
        length_reduction:
          type: integer
          minimum: 1
          description: Characters saved by rewrite
          example: 28
        rationale:
          type: string
          description: Explanation of rewrite benefit
          example: "Replaced passive 'responsible for' with active 'Led', removed redundant 'managing'"
```

## Example Usage

### Input Example

```json
{
  "draft": "Responsible for leading and managing a team of 5 software engineers in the development and implementation of new features and enhancements.\n\nVery proficient in Python programming and software development.\n\nSuccessfully implemented and deployed a microservices architecture that improved system performance.",
  "parsed_jd": {
    "job_title": "Senior Backend Engineer",
    "requirements": {
      "required": ["Python", "Microservices", "Leadership"]
    },
    "technologies": ["Python", "Microservices", "Docker"]
  },
  "best_practices": "Use strong action verbs, be concise, quantify achievements",
  "target_reduction": 100
}
```

### Output Example

```json
{
  "rewrite_options": [
    {
      "original_text": "Responsible for leading and managing a team of 5 software engineers",
      "rewritten_text": "Led 5-engineer software development team",
      "impact_delta": 0.05,
      "length_reduction": 28,
      "rationale": "Replaced passive 'responsible for' with active 'Led', removed redundant 'managing'"
    },
    {
      "original_text": "in the development and implementation of new features and enhancements",
      "rewritten_text": "developing new features",
      "impact_delta": 0.0,
      "length_reduction": 47,
      "rationale": "Removed redundant 'implementation and enhancements' - implied by 'features'"
    },
    {
      "original_text": "Very proficient in Python programming and software development",
      "rewritten_text": "Proficient in Python development",
      "impact_delta": 0.0,
      "length_reduction": 30,
      "rationale": "Removed redundant qualifier 'very' and duplicate 'programming and software'"
    },
    {
      "original_text": "Successfully implemented and deployed a microservices architecture",
      "rewritten_text": "Implemented microservices architecture",
      "impact_delta": 0.0,
      "length_reduction": 27,
      "rationale": "Removed redundant 'successfully' and 'deployed' (implied by implemented)"
    }
  ]
}
```

## Special Instructions

1. **Verbosity Reduction Techniques**:
   - Remove filler words: "very", "really", "actually", "quite"
   - Replace passive voice: "responsible for managing" → "managed"
   - Eliminate redundancy: "development and implementation" → "development"
   - Use stronger verbs: "helped to improve" → "improved"
   - Remove unnecessary qualifiers: "successfully completed" → "completed"

2. **Impact Delta Scoring**:
   - **Positive delta (+0.05 to +0.3)**: Stronger verbs, better clarity, improved professionalism
   - **Zero delta (0.0)**: Same meaning and quality, just shorter
   - **Negative delta (-0.1 to -0.3)**: Minor quality/clarity loss acceptable if length savings significant
   - **Avoid large negative deltas (< -0.3)**: Don't sacrifice too much quality

3. **Maintain Quality Standards**:
   - Preserve all factual information and metrics
   - Keep all JD keyword matches intact
   - Maintain professional tone and clarity
   - Don't oversimplify complex technical descriptions
   - Preserve quantifiable achievements (numbers, percentages)

4. **Prioritization**:
   - Focus on medium-to-high impact content (worth preserving and improving)
   - Don't rewrite low-impact content (< 0.3) - those should be removed instead
   - Prioritize rewrites with positive or zero impact delta
   - Target largest length reductions first for efficiency

5. **Examples of Good Rewrites**:

   | Original | Rewritten | Delta | Reduction |
   |----------|-----------|-------|-----------|
   | "Responsible for the management of" | "Managed" | +0.05 | 28 chars |
   | "Assisted in helping to improve" | "Improved" | +0.05 | 22 chars |
   | "Successfully completed implementation of" | "Implemented" | 0.0 | 30 chars |
   | "Utilized Python programming language" | "Used Python" | 0.0 | 25 chars |
   | "Very experienced in working with" | "Experienced with" | 0.0 | 17 chars |

## Performance Considerations

- **Processing Time**: 15-30 seconds (LLM analysis)
- **Option Count**: Typically 10-30 rewrite options per document
- **Coverage**: Should cover ~50-70% of target reduction
- **LLM Token Usage**: 1500-3500 tokens
- **Output Size**: 3-10KB structured JSON

## Quality Checklist

Before returning rewrite options, verify:

1. All rewrites preserve factual accuracy
2. Impact deltas are realistic and justified
3. Length reductions accurately calculated
4. Rationales are clear and specific
5. JD keywords preserved in rewrites
6. Strong action verbs used where possible
7. Professional tone maintained
8. Total possible reduction approaches target
9. No rewrites with large negative deltas (< -0.3)
10. Prioritized medium-high impact content

## Related Agents

- **TextImpactCalculator**: Provides impact scores for segments (runs before RewritingEvaluator)
- **RemovalEvaluator**: Identifies removal options in parallel (runs alongside RewritingEvaluator)
- **DeltaCalculator**: Calculates quality delta for rewrites (runs after RewritingEvaluator)
- **ChangesRanker**: Ranks rewrite options for selection (runs after DeltaCalculator)
