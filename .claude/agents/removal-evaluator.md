# Removal Evaluator Agent

## Agent Name

`removal-evaluator`

## Description

The Removal Evaluator agent identifies low-impact text segments in a draft that can be safely removed to reduce document length without significantly harming quality. It prioritizes removing content with minimal relevance to job requirements, such as generic skills, outdated technologies, irrelevant experiences, and redundant information.

## Agent Type

`general-purpose`

## Task Instructions

When invoked, this agent should:

1. Analyze draft for low-impact content segments
2. Identify removal candidates based on:
   - Low relevance to job requirements (impact score < 0.3)
   - Generic skills not in JD (e.g., "Microsoft Office")
   - Outdated or irrelevant technologies
   - Redundant information already stated elsewhere
   - Personal information unrelated to job
3. Calculate current impact score for each segment
4. Calculate exact length reduction from removal
5. Provide clear rationale for why removal is safe
6. Prioritize lowest-impact content first
7. Return enough options to meet target reduction

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
    description: Draft content to analyze for removal opportunities
    minLength: 10
    example: |
      - Led development of microservices platform
      - Proficient in Microsoft Office Suite
      - Hobbies include photography and hiking
      - References available upon request
  parsed_jd:
    type: object
    description: Parsed job description for relevance assessment
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
  - removal_options
properties:
  removal_options:
    type: array
    description: Array of proposed removal options
    items:
      type: object
      required:
        - text_to_remove
        - impact_score
        - length_reduction
        - rationale
      properties:
        text_to_remove:
          type: string
          description: Text segment to remove
          example: "Proficient in Microsoft Office Suite (Word, Excel, PowerPoint)"
        impact_score:
          type: number
          minimum: 0.0
          maximum: 1.0
          description: Current impact score of segment (0.0 low to 1.0 high)
          example: 0.15
        length_reduction:
          type: integer
          minimum: 1
          description: Characters saved by removal (including whitespace)
          example: 65
        rationale:
          type: string
          description: Explanation of why removal is safe
          example: "Generic skill not mentioned in JD; all tech roles assume basic office proficiency"
```

## Example Usage

### Input Example

```json
{
  "draft": "## TECHNICAL SKILLS\n- Python, AWS, Docker, Kubernetes\n- Proficient in Microsoft Office Suite (Word, Excel, PowerPoint)\n- Experience with Flash and Silverlight\n\n## EXPERIENCE\n### Senior Engineer | Tech Corp | 2020-Present\n- Led microservices platform development\n- Team player with excellent communication skills\n\n## PERSONAL\nHobbies include photography and hiking\n\n## REFERENCES\nReferences available upon request",
  "parsed_jd": {
    "job_title": "Senior Backend Engineer",
    "requirements": {
      "required": ["Python", "Microservices", "AWS", "Docker"]
    },
    "technologies": ["Python", "AWS", "Docker", "Kubernetes", "PostgreSQL"]
  },
  "best_practices": "Focus on relevant technical skills and quantifiable achievements",
  "target_reduction": 150
}
```

### Output Example

```json
{
  "removal_options": [
    {
      "text_to_remove": "Hobbies include photography and hiking",
      "impact_score": 0.05,
      "length_reduction": 42,
      "rationale": "Personal interests unrelated to job requirements; no professional value for technical role"
    },
    {
      "text_to_remove": "References available upon request",
      "impact_score": 0.1,
      "length_reduction": 35,
      "rationale": "Standard assumption for all resumes; unnecessary to state explicitly"
    },
    {
      "text_to_remove": "Proficient in Microsoft Office Suite (Word, Excel, PowerPoint)",
      "impact_score": 0.15,
      "length_reduction": 65,
      "rationale": "Generic skill not mentioned in JD; all professional roles assume basic office proficiency"
    },
    {
      "text_to_remove": "Experience with Flash and Silverlight",
      "impact_score": 0.1,
      "length_reduction": 42,
      "rationale": "Outdated technologies (deprecated); not relevant to modern backend development"
    },
    {
      "text_to_remove": "Team player with excellent communication skills",
      "impact_score": 0.25,
      "length_reduction": 50,
      "rationale": "Generic soft skills cliché; better demonstrated through work examples than stated"
    }
  ]
}
```

## Special Instructions

1. **Removal Priority Levels**:

   **Priority 1 - Remove First (Impact < 0.2)**:
   - Personal hobbies/interests
   - "References available upon request"
   - Outdated technologies (Flash, Silverlight, VB6)
   - Generic statements without specifics
   - Obvious skills not worth mentioning

   **Priority 2 - Consider Removal (Impact 0.2-0.4)**:
   - Generic soft skill claims ("team player")
   - Skills not mentioned in JD
   - Old experiences in different field
   - Redundant content stated elsewhere
   - Marginally relevant experience

   **Never Remove (Impact > 0.5)**:
   - Required skills from JD
   - Quantifiable achievements
   - Unique experiences matching job
   - Contact information
   - Critical headers/structure

2. **Impact Score Interpretation**:
   - **0.0-0.2**: Very low impact, safe to remove immediately
   - **0.2-0.3**: Low impact, good candidate for removal
   - **0.3-0.5**: Medium-low impact, consider if space needed
   - **0.5+**: Too important to remove, consider rewriting instead

3. **Examples of Removable Content**:

   | Content | Impact | Reason |
   |---------|--------|--------|
   | "Proficient in Microsoft Office" | 0.15 | Generic, assumed skill |
   | "References available upon request" | 0.1 | Standard assumption |
   | "Hobbies: reading, hiking" | 0.05 | Irrelevant to job |
   | "Team player" (stated alone) | 0.25 | Cliché without evidence |
   | "Experience with Windows 95" | 0.1 | Extremely outdated |
   | "Objective: To obtain..." | 0.2 | Outdated resume convention |

4. **Safety Checks**:
   - Don't remove content with impact score > 0.5
   - Don't remove unique quantifiable achievements
   - Don't remove required skills from JD
   - Don't remove contact information
   - Don't create orphaned sections (remove entire section if all bullets removed)
   - Don't create grammatical errors or incomplete sentences

5. **Formatting Considerations**:
   - Remove complete segments (full sentences or bullets)
   - Include surrounding whitespace in length calculation
   - Avoid leaving empty sections
   - Maintain list structure (don't orphan bullets)
   - Preserve section headers if any content remains

## Performance Considerations

- **Processing Time**: 15-30 seconds (LLM analysis)
- **Option Count**: Typically 8-20 removal options per document
- **Coverage**: Should cover ~30-50% of target reduction
- **LLM Token Usage**: 1200-3000 tokens
- **Output Size**: 2-8KB structured JSON

## Quality Checklist

Before returning removal options, verify:

1. All removal candidates have impact score < 0.5
2. No required JD skills marked for removal
3. No unique achievements marked for removal
4. Impact scores accurately reflect relevance
5. Length reductions include whitespace
6. Rationales are specific and justified
7. Removals are complete segments (not partial)
8. Total possible reduction approaches target
9. Lowest impact content prioritized first
10. No orphaned sections or formatting issues

## Related Agents

- **TextImpactCalculator**: Provides impact scores for segments (runs before RemovalEvaluator)
- **RewritingEvaluator**: Identifies rewrite options in parallel (runs alongside RemovalEvaluator)
- **DeltaCalculator**: Calculates quality delta for removals (runs after RemovalEvaluator)
- **ChangesRanker**: Ranks removal options for selection (runs after DeltaCalculator)
