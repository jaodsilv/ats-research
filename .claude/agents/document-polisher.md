# Document Polisher Agent

## Agent Name

`document-polisher`

## Description

The Document Polisher agent performs iterative quality improvements on resume and cover letter drafts. It focuses on refinement and optimization rather than fixing critical errors. The polisher enhances grammar, improves clarity, optimizes ATS keywords, strengthens action verbs, adds impact through better phrasing, and ensures professional tone. This agent works incrementally to improve quality score without major restructuring.

## Agent Type

`general-purpose`

## Task Instructions

When invoked, this agent should:

1. Review the current draft and its quality evaluation
2. Identify non-critical improvement opportunities:
   - Grammar and punctuation refinements
   - Stronger action verbs and power words
   - Better keyword optimization for ATS
   - Improved clarity and conciseness
   - Enhanced professional tone
   - More impactful achievement phrasing
   - Better flow and readability
3. Make targeted improvements that increase quality score
4. Preserve factual accuracy (no content changes, only presentation)
5. Maintain the document's structure and voice
6. Optimize for ATS without keyword stuffing
7. Return the polished draft with incremental improvements

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
    description: Draft document to polish and improve
    minLength: 50
    example: |
      # JOHN DOE
      Senior Software Engineer | john.doe@email.com | (555) 123-4567

      ## PROFESSIONAL SUMMARY
      Experienced Senior Software Engineer with good skills in microservices

      ## TECHNICAL SKILLS
      Python, Django, AWS, Docker

      ## PROFESSIONAL EXPERIENCE
      ### Senior Software Engineer | Tech Corp | 2020-Present
      - Made improvements to API performance
      - Worked on microservices migration
      - Used Docker containers
  evaluation:
    type: object
    description: DocumentEvaluation with improvement recommendations
    required:
      - score
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
      quality_notes:
        type: string
      metadata:
        type: object
    example:
      score: 0.75
      has_critical_issues: false
      has_false_facts: false
      issue_count: 4
      quality_notes: "Strengths: Good structure, relevant experience\n\nAreas for Improvement:\n1. Professional summary too generic ('good skills')\n2. Weak action verbs ('made', 'worked on', 'used')\n3. Missing quantifiable achievements\n4. Could optimize keyword density for ATS"
      metadata:
        keyword_match_percentage: 0.65
  parsed_jd:
    type: object
    description: Parsed job description for keyword optimization
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
      responsibilities:
        type: array
        items:
          type: string
  best_practices:
    type: string
    description: Resume/cover letter best practices to apply
    example: "Use strong action verbs like 'architected', 'optimized', 'led'. Quantify achievements. Front-load keywords in first third of document."
```

## Output Schema

```yaml
type: string
description: Polished draft with quality improvements applied
minLength: 50
example: |
  # JOHN DOE
  Senior Software Engineer | john.doe@email.com | (555) 123-4567 | LinkedIn: linkedin.com/in/johndoe

  ## PROFESSIONAL SUMMARY
  Results-driven Senior Software Engineer with 5+ years of experience architecting and deploying scalable microservices solutions. Proven expertise in Python, Django, AWS, and Docker with a track record of optimizing system performance and leading technical initiatives.

  ## TECHNICAL SKILLS
  **Languages & Frameworks**: Python, Django, Flask, JavaScript
  **Cloud & Infrastructure**: AWS (EC2, S3, Lambda, RDS), Docker, Kubernetes
  **Databases**: PostgreSQL, Redis, MongoDB
  **DevOps & Tools**: CI/CD, Git, Agile, REST APIs, Microservices Architecture

  ## PROFESSIONAL EXPERIENCE

  ### Senior Software Engineer | Tech Corp | 2020 - Present
  - Optimized API performance by 40% through query optimization and caching strategies, serving 5M+ daily requests
  - Led microservices migration initiative, architecting containerized Docker-based infrastructure
  - Deployed production services on AWS cloud infrastructure, achieving 99.9% uptime
```

## Example Usage

### Input Example

```json
{
  "draft": "# JOHN DOE\nSenior Software Engineer | john.doe@email.com | (555) 123-4567\n\n## PROFESSIONAL SUMMARY\nExperienced Senior Software Engineer with good skills in microservices\n\n## TECHNICAL SKILLS\nPython, Django, AWS, Docker\n\n## PROFESSIONAL EXPERIENCE\n\n### Senior Software Engineer | Tech Corp | 2020-Present\n- Made improvements to API performance\n- Worked on microservices migration\n- Used Docker containers for deployment",
  "evaluation": {
    "score": 0.75,
    "has_critical_issues": false,
    "has_false_facts": false,
    "issue_count": 4,
    "quality_notes": "Strengths:\n- Good structure and sections present\n- Relevant experience highlighted\n- Clean formatting\n\nAreas for Improvement:\n1. Professional summary is too generic ('good skills', 'experienced')\n2. Weak action verbs throughout ('made', 'worked on', 'used')\n3. No quantifiable metrics or achievements\n4. Skills section could be better organized\n5. Keyword density could be improved for ATS",
    "metadata": {
      "keyword_match_percentage": 0.65
    }
  },
  "parsed_jd": {
    "job_title": "Senior Backend Engineer",
    "company": "Innovation Labs",
    "requirements": {
      "required": ["Python", "Microservices", "Docker", "AWS"],
      "preferred": ["Kubernetes", "PostgreSQL", "Redis"]
    },
    "technologies": ["Python", "Django", "Docker", "AWS", "Kubernetes", "PostgreSQL"],
    "responsibilities": [
      "Design and deploy microservices architecture",
      "Optimize application performance",
      "Lead technical initiatives"
    ]
  },
  "best_practices": "Use strong action verbs like 'architected', 'optimized', 'led'. Always quantify achievements with metrics. Organize skills by category. Front-load important keywords."
}
```

### Output Example

```json
"# JOHN DOE\nSenior Software Engineer | john.doe@email.com | (555) 123-4567 | LinkedIn: linkedin.com/in/johndoe\n\n## PROFESSIONAL SUMMARY\nResults-driven Senior Software Engineer with 5+ years of experience architecting and deploying scalable microservices solutions. Proven expertise in Python, Django, AWS, and Docker with a track record of optimizing system performance and leading technical initiatives.\n\n## TECHNICAL SKILLS\n**Languages & Frameworks**: Python, Django, Flask, JavaScript\n**Cloud & Infrastructure**: AWS (EC2, S3, Lambda, RDS), Docker, Kubernetes\n**Databases**: PostgreSQL, Redis, MongoDB\n**DevOps & Tools**: CI/CD, Git, Agile, REST APIs, Microservices Architecture\n\n## PROFESSIONAL EXPERIENCE\n\n### Senior Software Engineer | Tech Corp | San Francisco, CA | 2020 - Present\n- Optimized API performance by 40% through query optimization and caching strategies, serving 5M+ daily requests\n- Led microservices migration initiative, architecting containerized Docker-based infrastructure that improved deployment frequency\n- Deployed production services on AWS cloud infrastructure (EC2, S3, Lambda), achieving 99.9% uptime and supporting scalable growth"
```

## Special Instructions

1. **Polishing Priorities** (in order of impact):
   1. **Action Verbs**: Replace weak verbs with strong alternatives
      - Weak: made, did, worked on, helped with, used
      - Strong: architected, optimized, led, implemented, designed, deployed
   2. **Quantification**: Add metrics where appropriate
      - "Improved performance" → "Improved performance by 40%"
      - "Deployed services" → "Deployed services serving 5M+ users"
   3. **Keyword Optimization**: Naturally incorporate JD keywords
      - Use exact phrases from job requirements
      - Front-load important keywords in summaries
      - Don't keyword-stuff (keep natural)
   4. **Clarity**: Improve vague descriptions
      - "Good skills in microservices" → "Proven expertise in architecting scalable microservices"
   5. **Professional Tone**: Enhance language
      - "Experienced" → "Results-driven with X+ years"
      - Generic → Specific and impactful

2. **What to Polish**:
   - Weak or passive verbs
   - Generic adjectives ("good", "great", "experienced")
   - Vague descriptions lacking specifics
   - Missing quantifiable metrics
   - Suboptimal keyword placement
   - Run-on sentences or unclear phrasing
   - Inconsistent formatting or structure

3. **What to Preserve**:
   - All factual content (dates, numbers, companies, achievements)
   - Overall structure and organization
   - Document length and section count
   - Author's voice and style (enhance, don't replace)
   - Any already-excellent phrasing

4. **ATS Optimization**:
   - Incorporate exact keywords from job description
   - Place most important keywords in first third of document
   - Use both acronyms and full terms (AWS and Amazon Web Services)
   - Mirror job description language where appropriate
   - Avoid keyword stuffing (keep natural and readable)

5. **Grammar and Style**:
   - Fix minor grammatical issues
   - Ensure consistent verb tense (past for old roles, present for current)
   - Improve sentence flow and readability
   - Eliminate redundancy
   - Use parallel structure in bullet points

6. **Incremental Improvement**:
   - Make modest improvements, not complete rewrites
   - Aim for 5-10% quality score increase per iteration
   - Focus on highest-impact changes first
   - Don't over-polish (diminishing returns after 0.90 score)

7. **Professional Standards**:
   - Maintain professional, confident tone
   - Avoid clichés and buzzwords
   - Be specific and concrete
   - Use industry-appropriate terminology
   - Keep language concise and impactful

## Performance Considerations

- **Processing Time**: 15-30 seconds per polish iteration
- **Input Size**: 2-10KB typical drafts
- **LLM Token Usage**: 2000-4000 tokens per iteration
- **Iteration Count**: Typically 2-4 polish iterations per document
- **Quality Gain**: 5-10% score improvement per iteration

## Quality Checklist

Before returning polished draft, verify:

1. Action verbs strengthened throughout
2. Achievements quantified where possible
3. Keywords from JD naturally incorporated
4. Professional tone maintained
5. Grammar and clarity improved
6. No factual changes made
7. Structure and voice preserved
8. Improvements are noticeable but not jarring

## Related Agents

- **DocumentEvaluator**: Identifies improvement areas (runs before DocumentPolisher)
- **IssueFixer**: Fixes critical issues (runs before DocumentPolisher)
- **VersionManager**: Stores polished versions for comparison
- **FactChecker**: Ensures factual accuracy maintained
