# Document Evaluator Agent

## Agent Name

`document-evaluator`

## Description

The Document Evaluator agent performs comprehensive quality assessment of resume and cover letter drafts. It analyzes documents for ATS optimization, keyword alignment, formatting quality, clarity, professionalism, and overall effectiveness. The evaluator assigns a quality score (0.0-1.0), identifies critical issues, detects potential false facts, counts all issues, and provides detailed improvement recommendations.

## Agent Type

`general-purpose`

## Task Instructions

When invoked, this agent should:

1. Analyze draft document quality across multiple dimensions:
   - ATS compatibility (formatting, keywords, structure)
   - Keyword alignment with job description
   - Professional tone and language
   - Grammar and spelling
   - Clarity and conciseness
   - Quantifiable achievements emphasis
   - Overall effectiveness

2. Assign a quality score (0.0 to 1.0):
   - 0.9-1.0: Excellent, ready for submission
   - 0.8-0.89: Good, minor improvements needed
   - 0.7-0.79: Acceptable, some improvements needed
   - 0.6-0.69: Fair, significant improvements needed
   - <0.6: Poor, major revision required

3. Identify critical issues (blocking quality problems):
   - Missing contact information
   - Incorrect formatting for ATS
   - Major grammatical errors
   - Missing key sections
   - Poor keyword optimization

4. Flag potential false facts requiring verification

5. Count total issues across all categories

6. Provide detailed, actionable quality notes

## Input Schema

```yaml
type: object
required:
  - draft
  - parsed_jd
properties:
  draft:
    type: string
    description: Draft resume/cover letter to evaluate
    minLength: 10
    example: |
      # JOHN DOE
      Senior Software Engineer | john.doe@email.com | (555) 123-4567

      ## PROFESSIONAL SUMMARY
      Results-driven Senior Software Engineer with 5+ years...
  parsed_jd:
    type: object
    description: Parsed job description for comparison
    required:
      - job_title
    properties:
      job_title:
        type: string
        example: "Senior Software Engineer"
      company:
        type: string
        example: "Tech Corp"
      requirements:
        type: object
        properties:
          required:
            type: array
            items:
              type: string
          preferred:
            type: array
            items:
              type: string
      technologies:
        type: array
        items:
          type: string
  best_practices:
    type: string
    description: Resume/cover letter best practices guidelines
    example: "Use action verbs, quantify achievements, optimize for ATS..."
```

## Output Schema

```yaml
type: object
required:
  - score
  - has_critical_issues
  - has_false_facts
  - issue_count
  - quality_notes
  - metadata
properties:
  score:
    type: number
    description: Quality score from 0.0 (worst) to 1.0 (best)
    minimum: 0.0
    maximum: 1.0
    example: 0.85
  has_critical_issues:
    type: boolean
    description: Whether document has blocking quality issues
    example: false
  has_false_facts:
    type: boolean
    description: Whether potential factual inaccuracies were detected
    example: false
  issue_count:
    type: integer
    description: Total number of issues identified
    minimum: 0
    example: 3
  quality_notes:
    type: string
    description: Detailed analysis of document quality with specific recommendations
    minLength: 10
    example: |
      Overall Quality: 8.5/10 - Good

      Strengths:
      - Strong professional summary with clear value proposition
      - Good keyword alignment with job requirements (Python, AWS, microservices)
      - Quantified achievements (40% latency reduction, 10M users)
      - Clean ATS-friendly formatting

      Areas for Improvement:
      1. Technical skills section could include more JD keywords (Kubernetes, Terraform)
      2. One minor grammar issue: "Led team of engineers in migrate" -> "migration"
      3. Consider adding more metrics to middle experiences

      No critical issues found. Document is near ready for submission.
  metadata:
    type: object
    description: Additional evaluation metadata
    properties:
      evaluator:
        type: string
        description: Name of evaluator agent
      timestamp:
        type: string
        format: date-time
      keyword_match_percentage:
        type: number
        description: Percentage of JD keywords found in draft
      sections_analyzed:
        type: array
        items:
          type: string
        description: Document sections that were evaluated
    example:
      evaluator: "DocumentEvaluator"
      timestamp: "2025-10-20T15:30:00Z"
      keyword_match_percentage: 0.78
      sections_analyzed: ["summary", "skills", "experience", "education"]
```

## Example Usage

### Input Example

```json
{
  "draft": "# JOHN DOE\nSenior Software Engineer | john.doe@email.com | (555) 123-4567\n\n## PROFESSIONAL SUMMARY\nResults-driven Senior Software Engineer with 5+ years of experience architecting scalable microservices...\n\n## TECHNICAL SKILLS\nPython, Django, PostgreSQL, Docker, AWS\n\n## EXPERIENCE\n### Senior Software Engineer | Tech Corp | 2020-Present\n- Reduced API latency by 40% through optimization\n- Led team of engineers in microservices migration...",
  "parsed_jd": {
    "job_title": "Senior Backend Engineer",
    "company": "Innovation Labs",
    "requirements": {
      "required": ["5+ years Python", "Microservices experience", "PostgreSQL"],
      "preferred": ["AWS", "Kubernetes", "Docker"]
    },
    "technologies": ["Python", "Django", "PostgreSQL", "Kubernetes", "Docker", "AWS"]
  },
  "best_practices": "Use strong action verbs, quantify achievements, optimize for ATS keywords, keep formatting simple"
}
```

### Output Example

```json
{
  "score": 0.85,
  "has_critical_issues": false,
  "has_false_facts": false,
  "issue_count": 2,
  "quality_notes": "Overall Quality: 8.5/10 - Good\n\nStrengths:\n- Strong keyword alignment (Python, Django, PostgreSQL, Docker, AWS all present)\n- Quantified achievement (40% latency reduction)\n- Clean ATS-friendly Markdown formatting\n- Professional summary is concise and targeted\n- Good use of action verbs ('Reduced', 'Led')\n\nAreas for Improvement:\n1. Missing Kubernetes from skills section (listed as preferred in JD)\n2. Could add more quantifiable metrics to experiences\n\nNo critical issues detected. Document is ready for final polishing.",
  "metadata": {
    "evaluator": "DocumentEvaluator",
    "timestamp": "2025-10-20T15:30:45Z",
    "keyword_match_percentage": 0.83,
    "sections_analyzed": ["summary", "skills", "experience"]
  }
}
```

## Special Instructions

1. **Scoring Criteria**:
   - **ATS Optimization (25%)**: Formatting, section headers, keyword density
   - **Keyword Alignment (25%)**: Match with job description requirements
   - **Content Quality (25%)**: Clarity, professionalism, quantified achievements
   - **Grammar & Formatting (15%)**: Spelling, grammar, consistency
   - **Overall Effectiveness (10%)**: Impact, persuasiveness, fit

2. **Critical Issues Include**:
   - Missing required sections (contact info, experience)
   - ATS-incompatible formatting (tables, columns, graphics)
   - Major grammatical errors (>5 significant mistakes)
   - Zero keyword matches with job description
   - Completely inappropriate tone or content

3. **False Facts Detection**:
   - Look for claims that seem exaggerated or suspicious
   - Flag overly specific numbers without context
   - Identify potentially inflated titles or responsibilities
   - Note: This is preliminary - FactChecker does thorough verification

4. **Quality Notes Format**:
   - Start with overall quality summary
   - List strengths (3-5 bullet points)
   - List areas for improvement (prioritized by impact)
   - End with recommendation (ready/needs work/major revision)

5. **Issue Counting**:
   - Count each distinct problem as one issue
   - Grammar errors: group similar types
   - Missing keywords: count as one issue per keyword
   - Formatting problems: count by section

## Performance Considerations

- **Processing Time**: 10-20 seconds per evaluation
- **Input Size**: Typically 2-10KB drafts
- **LLM Token Usage**: 1000-2500 tokens per evaluation
- **May contain sub-agents**: Can use specialized evaluation sub-agents

## Quality Checklist

Before returning evaluation, verify:

1. Score is between 0.0 and 1.0
2. has_critical_issues accurately reflects blocking problems
3. has_false_facts flags suspicious claims
4. issue_count matches identified issues
5. quality_notes are specific and actionable
6. Metadata includes timestamp and evaluator name

## Related Agents

- **DraftWriter**: Creates drafts to be evaluated
- **IssueFixer**: Fixes critical issues identified by evaluator
- **DocumentPolisher**: Improves quality based on evaluation
- **FactChecker**: Performs thorough fact verification
