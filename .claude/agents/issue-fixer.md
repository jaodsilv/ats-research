# Issue Fixer Agent

## Agent Name

`issue-fixer`

## Description

The Issue Fixer agent addresses critical quality issues identified by the Document Evaluator. It focuses on fixing blocking problems that prevent the document from being acceptable, such as formatting errors, missing required sections, major grammatical mistakes, and severe ATS compatibility issues. This agent makes targeted corrections without extensive rewriting.

## Agent Type

`general-purpose`

## Task Instructions

When invoked, this agent should:

1. Review the document evaluation results to understand critical issues
2. Identify all blocking problems that must be fixed:
   - Missing or incorrect contact information
   - ATS-incompatible formatting (tables, columns, images)
   - Major grammatical errors
   - Missing required sections
   - Severe keyword gaps
3. Apply targeted fixes to address each critical issue
4. Preserve the overall structure and voice of the draft
5. Ensure fixes don't introduce new problems
6. Maintain factual accuracy (only fix presentation, not content)
7. Return the corrected draft with issues resolved

## Input Schema

```yaml
type: object
required:
  - draft
  - evaluation
  - parsed_jd
properties:
  draft:
    type: string
    description: Draft document with critical issues to fix
    minLength: 10
    example: |
      # JOHN DOE
      Senior Software Engineer

      ## SUMMARY
      Experienced engineer with cloud expertise

      ## SKILLS
      Python, AWS

      ## WORK HISTORY
      ### Tech Corp
      Did microservices work
  evaluation:
    type: object
    description: DocumentEvaluation results identifying issues
    required:
      - score
      - has_critical_issues
      - issue_count
      - quality_notes
    properties:
      score:
        type: number
        minimum: 0.0
        maximum: 1.0
      has_critical_issues:
        type: boolean
      has_false_facts:
        type: boolean
      issue_count:
        type: integer
        minimum: 0
      quality_notes:
        type: string
      metadata:
        type: object
    example:
      score: 0.62
      has_critical_issues: true
      has_false_facts: false
      issue_count: 5
      quality_notes: "Critical Issues:\n1. Missing contact info (email, phone)\n2. Weak section headers\n3. No quantified achievements\n4. Missing key technologies from JD\n5. Vague descriptions"
      metadata:
        evaluator: "DocumentEvaluator"
  parsed_jd:
    type: object
    description: Parsed job description for context
    required:
      - job_title
    properties:
      job_title:
        type: string
      company:
        type: string
      requirements:
        type: object
      technologies:
        type: array
        items:
          type: string
```

## Output Schema

```yaml
type: string
description: Fixed draft with critical issues addressed
minLength: 50
example: |
  # JOHN DOE
  Senior Software Engineer | john.doe@email.com | (555) 123-4567 | LinkedIn: linkedin.com/in/johndoe

  ## PROFESSIONAL SUMMARY
  Experienced Senior Software Engineer with proven expertise in cloud-based microservices architecture using Python and AWS

  ## TECHNICAL SKILLS
  **Languages**: Python, JavaScript, SQL
  **Cloud & Infrastructure**: AWS (EC2, S3, Lambda), Docker, Kubernetes
  **Frameworks**: Django, Flask
  **Databases**: PostgreSQL, Redis

  ## PROFESSIONAL EXPERIENCE

  ### Senior Software Engineer | Tech Corp | 2020 - Present
  - Designed and deployed microservices architecture serving 5M+ users
  - Reduced deployment time by 50% through automated CI/CD pipelines
  - Led migration to AWS cloud infrastructure, improving system reliability to 99.9% uptime
```

## Example Usage

### Input Example

```json
{
  "draft": "# JOHN DOE\nSenior Software Engineer\n\n## SUMMARY\nExperienced engineer with cloud expertise\n\n## SKILLS\nPython, AWS\n\n## WORK HISTORY\n### Tech Corp\n- Did microservices work\n- Used cloud services",
  "evaluation": {
    "score": 0.62,
    "has_critical_issues": true,
    "has_false_facts": false,
    "issue_count": 5,
    "quality_notes": "Critical Issues:\n1. Missing contact information (email, phone, LinkedIn)\n2. Professional summary too vague and brief\n3. Skills section missing many JD keywords (Docker, Kubernetes, PostgreSQL)\n4. Section header 'WORK HISTORY' should be 'PROFESSIONAL EXPERIENCE'\n5. Achievements lack quantifiable metrics\n6. Experience descriptions are extremely vague\n\nDocument needs significant improvement before acceptable.",
    "metadata": {
      "evaluator": "DocumentEvaluator",
      "keyword_match_percentage": 0.3
    }
  },
  "parsed_jd": {
    "job_title": "Senior Backend Engineer",
    "company": "Innovation Labs",
    "requirements": {
      "required": ["Python", "Microservices", "PostgreSQL", "Docker"],
      "preferred": ["AWS", "Kubernetes", "Redis"]
    },
    "technologies": ["Python", "Django", "PostgreSQL", "Docker", "Kubernetes", "AWS"]
  }
}
```

### Output Example

```json
"# JOHN DOE\nSenior Software Engineer | john.doe@email.com | (555) 123-4567 | LinkedIn: linkedin.com/in/johndoe\n\n## PROFESSIONAL SUMMARY\nExperienced Senior Software Engineer with proven expertise in designing and deploying cloud-based microservices architectures. Strong background in Python, AWS, Docker, and Kubernetes with a focus on scalable, high-availability systems.\n\n## TECHNICAL SKILLS\n**Languages**: Python, JavaScript, SQL\n**Cloud & Infrastructure**: AWS (EC2, S3, Lambda, RDS), Docker, Kubernetes\n**Frameworks**: Django, Flask\n**Databases**: PostgreSQL, Redis, MongoDB\n**DevOps**: CI/CD, Git, Agile methodologies\n\n## PROFESSIONAL EXPERIENCE\n\n### Senior Software Engineer | Tech Corp | 2020 - Present\n- Designed and deployed microservices architecture serving 5M+ daily active users\n- Implemented containerized services using Docker and Kubernetes, improving deployment efficiency\n- Utilized AWS cloud infrastructure (EC2, S3, Lambda) for scalable application hosting\n- Developed RESTful APIs with Python and Django, integrated with PostgreSQL databases\n- Established CI/CD pipelines reducing deployment time and improving code quality"
```

## Special Instructions

1. **Critical Issue Priorities** (fix in order):
   1. **Contact Information**: Add missing email, phone, LinkedIn
   2. **Section Headers**: Use standard ATS-friendly headers
   3. **Required Sections**: Ensure all essential sections present
   4. **Major Grammar**: Fix glaring grammatical errors
   5. **Keyword Gaps**: Add critical missing keywords from JD
   6. **Formatting**: Fix ATS-incompatible formatting

2. **What to Fix**:
   - Missing contact details
   - Non-standard section headers
   - ATS-incompatible formatting (tables → lists)
   - Major grammatical errors (subject-verb, tense)
   - Critical keyword omissions
   - Extremely vague descriptions

3. **What NOT to Change**:
   - Factual content (dates, numbers, companies)
   - Overall structure if already reasonable
   - Voice and tone (unless completely unprofessional)
   - Non-critical wording choices
   - Minor stylistic preferences

4. **Adding Keywords**:
   - Only add keywords if they plausibly fit
   - Integrate naturally into existing content
   - Don't keyword-stuff or force unnatural phrasing
   - Prefer expanding existing descriptions

5. **Grammar Fixes**:
   - Focus on major errors only
   - Maintain consistent tense (past for previous roles, present for current)
   - Fix subject-verb agreement
   - Correct obvious typos

6. **Formatting Standards**:
   - Use Markdown with simple formatting (headers, bold, lists)
   - Avoid tables, columns, text boxes
   - Use consistent header hierarchy (# → ## → ###)
   - Ensure clean structure for ATS parsing

7. **Preservation Principle**:
   - Make minimal necessary changes
   - Preserve the author's voice
   - Keep good content unchanged
   - Only fix what's broken

## Performance Considerations

- **Processing Time**: 10-25 seconds per fix
- **Input Size**: 2-10KB typical drafts
- **LLM Token Usage**: 1500-3000 tokens per fix operation
- **Complexity**: Higher for drafts with many critical issues

## Quality Checklist

Before returning fixed draft, verify:

1. All critical issues from evaluation addressed
2. Contact information complete
3. Section headers are ATS-standard
4. No ATS-incompatible formatting remains
5. Major grammatical errors corrected
6. Critical keywords from JD incorporated
7. No new issues introduced by fixes
8. Factual content unchanged

## Related Agents

- **DocumentEvaluator**: Identifies critical issues (runs before IssueFixer)
- **DocumentPolisher**: Performs broader quality improvements (runs after IssueFixer)
- **FactChecker**: Verifies factual accuracy (separate concern)
