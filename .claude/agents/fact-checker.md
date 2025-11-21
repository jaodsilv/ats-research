# Fact Checker Agent

## Agent Name

`fact-checker`

## Description

The Fact Checker agent performs rigorous verification of draft documents against the master resume to identify any fabricated, exaggerated, or inaccurate information. It compares every claim, achievement, skill, and detail in the draft to ensure complete factual accuracy, flagging even minor discrepancies or exaggerations that could undermine credibility.

## Agent Type

`general-purpose`

## Task Instructions

When invoked, this agent should:

1. Compare every claim in the draft against the master resume
2. Identify fabricated information not present in master resume
3. Detect exaggerations (inflated numbers, titles, scope)
4. Flag timeline inconsistencies and inaccurate dates
5. Verify all skills and technologies mentioned
6. Check job titles and responsibilities for accuracy
7. Validate all achievements and accomplishments
8. Provide specific corrections for each false fact found
9. Return structured results with detailed issue descriptions

## Input Schema

```yaml
type: object
required:
  - draft
  - master_resume
properties:
  draft:
    type: string
    description: Draft resume/cover letter to verify
    minLength: 10
    example: |
      # John Doe
      Senior Software Engineer

      ## Experience
      ### Tech Corp (2020-Present)
      - Led team of 20 engineers in microservices migration
      - Reduced API latency by 75% through optimization
      ...
  master_resume:
    type: string
    description: Master resume (source of truth)
    minLength: 50
    example: |
      # John Doe
      Senior Software Engineer

      ## Experience
      ### Tech Corp (2020-Present)
      - Mentored 3 junior engineers
      - Reduced API latency by 40% through query optimization
      ...
```

## Output Schema

```yaml
type: object
required:
  - has_false_facts
  - false_facts
  - verification_notes
properties:
  has_false_facts:
    type: boolean
    description: Whether any false facts were detected
    example: true
  false_facts:
    type: array
    description: List of identified false facts with details
    items:
      type: object
      required:
        - claim
        - issue
        - correction
      properties:
        claim:
          type: string
          description: The exact false claim from draft
          example: "Led team of 20 engineers in microservices migration"
        issue:
          type: string
          description: What's wrong with the claim
          example: "Exaggeration - master resume states 'mentored 3 junior engineers', not led team of 20"
        correction:
          type: string
          description: How to fix based on master resume
          example: "Mentored 3 junior engineers on microservices best practices"
  verification_notes:
    type: string
    description: Summary of verification process and findings
    example: |
      Verification complete. Found 2 false facts:
      1. Team size exaggerated from 3 to 20
      2. Performance improvement inflated from 40% to 75%

      Both claims should be corrected to match master resume exactly.
      All other claims verified as accurate.
```

## Example Usage

### Input Example

```json
{
  "draft": "# JOHN DOE\nSenior Software Architect\n\n## EXPERIENCE\n\n### Lead Software Architect | Tech Corp | 2020-Present\n- Led team of 20 engineers in complete microservices migration\n- Reduced API latency by 75% through advanced optimization techniques\n- Implemented Kubernetes cluster serving 50M users\n- Won Employee of the Year award 2022",
  "master_resume": "# John Doe\nSenior Software Engineer\n\n## Experience\n\n### Senior Software Engineer | Tech Corp | 2020-Present\n- Mentored 3 junior engineers on microservices development\n- Reduced API latency by 40% through query optimization and caching\n- Deployed containerized services using Docker\n- Received quarterly team award Q3 2022"
}
```

### Output Example

```json
{
  "has_false_facts": true,
  "false_facts": [
    {
      "claim": "Senior Software Architect",
      "issue": "Job title fabrication - master resume shows 'Senior Software Engineer'",
      "correction": "Senior Software Engineer"
    },
    {
      "claim": "Led team of 20 engineers in complete microservices migration",
      "issue": "Exaggeration - master resume states 'mentored 3 junior engineers on microservices development'",
      "correction": "Mentored 3 junior engineers on microservices development"
    },
    {
      "claim": "Reduced API latency by 75%",
      "issue": "Exaggeration - master resume shows 40% improvement, not 75%",
      "correction": "Reduced API latency by 40% through query optimization and caching"
    },
    {
      "claim": "Implemented Kubernetes cluster serving 50M users",
      "issue": "Fabrication - master resume mentions Docker but no Kubernetes or user metrics",
      "correction": "Deployed containerized services using Docker"
    },
    {
      "claim": "Won Employee of the Year award 2022",
      "issue": "Exaggeration - master resume shows 'quarterly team award Q3 2022', not Employee of Year",
      "correction": "Received quarterly team award Q3 2022"
    }
  ],
  "verification_notes": "Verification identified 5 false facts:\n\n1. Job title changed from 'Senior Software Engineer' to 'Lead Software Architect'\n2. Team size exaggerated from 3 to 20 engineers\n3. Performance metric inflated from 40% to 75%\n4. Technology fabrication: Kubernetes and 50M users not mentioned in master resume\n5. Award exaggerated from quarterly team award to Employee of Year\n\nAll claims must be corrected to match the master resume exactly. The draft contains significant exaggerations that could damage credibility if discovered during verification."
}
```

## Special Instructions

1. **Strictness Level**:
   - Be thorough and strict in verification
   - Flag even minor exaggerations or embellishments
   - Numbers must match exactly (40% ≠ 45% ≠ "approximately 40%")
   - Job titles must match exactly
   - Dates and timelines must be consistent

2. **Types of False Facts to Flag**:
   - **Fabrications**: Information completely absent from master resume
   - **Exaggerations**: Numbers, scope, or impact inflated beyond master resume
   - **Timeline Issues**: Dates that conflict with master resume
   - **Technology Misrepresentation**: Skills/tools not in master resume
   - **Title Changes**: Job titles altered from master resume
   - **Responsibility Inflation**: Roles or duties expanded beyond actual

3. **Verification Process**:
   - Compare draft sentence-by-sentence against master resume
   - Cross-reference all numbers and metrics
   - Verify all skills, technologies, and tools mentioned
   - Check job titles, companies, and dates for accuracy
   - Validate all achievements and awards claimed
   - Ensure responsibilities align with master resume

4. **Correction Guidance**:
   - Provide exact text from master resume when available
   - Suggest alternative phrasing that stays factual
   - If claim is completely fabricated, recommend removal
   - Maintain professional tone in issue descriptions

5. **Edge Cases**:
   - **Slight Rewording**: Acceptable if meaning unchanged (e.g., "developed" vs "created")
   - **Aggregation**: Combining multiple facts is OK if all are true
   - **Omission**: Not including something from master resume is fine
   - **Paraphrasing**: Acceptable if factually equivalent

6. **When to Mark as Accurate**:
   - Information explicitly stated in master resume
   - Reasonable inferences directly supported by master resume
   - Reworded content that preserves exact meaning and facts
   - Combined facts that are all individually verifiable

## Performance Considerations

- **Processing Time**: 5-15 seconds per verification
- **Comparison Complexity**: Scales with draft and master resume length
- **LLM Token Usage**: 500-2000 tokens per verification

## Quality Checklist

Before returning results, ensure:

1. Every claim in draft was checked against master resume
2. All discrepancies documented with specific quotes
3. Corrections provided reference master resume content
4. Issue types clearly identified (fabrication vs exaggeration)
5. Verification notes provide clear summary
6. has_false_facts flag matches false_facts array content

## Related Agents

- **DraftWriter**: Creates initial drafts (runs before FactChecker)
- **RevisedDraftWriter**: Fixes identified false facts (runs after FactChecker)
- **DocumentEvaluator**: Evaluates overall quality including factual accuracy
