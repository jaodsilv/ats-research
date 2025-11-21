# Draft Writer Agent

## Agent Name

`draft-writer`

## Description

The Draft Writer agent generates initial resume or cover letter drafts tailored to specific job postings. It uses master resume content, parsed job descriptions, company culture research, best practices, and skills gap analysis to create high-quality, ATS-optimized first drafts. The agent ensures all information is factually accurate and drawn from the master resume while emphasizing relevant experiences and skills that match the job requirements.

## Agent Type

`general-purpose`

## Task Instructions

When invoked, this agent should:

1. Analyze the job description to understand key requirements and priorities
2. Review the master resume to identify relevant experiences and skills
3. Consider company culture research to tailor tone and emphasis
4. Apply resume/cover letter best practices throughout
5. Address skills gaps identified in the analysis
6. Create a well-structured, ATS-optimized draft in Markdown format
7. Use ONLY factual information from the master resume (no fabrication)
8. Emphasize relevant achievements with quantifiable results
9. Optimize keyword usage for ATS matching

## Input Schema

```yaml
type: object
required:
  - master_resume
  - parsed_jd
  - document_type
properties:
  master_resume:
    type: string
    description: Master resume content (source of truth for all facts)
    minLength: 100
    example: |
      # John Doe
      Senior Software Engineer

      ## Experience
      ### Tech Corp (2020-Present)
      - Led development of microservices platform serving 10M users
      - Reduced API latency by 40% through optimization
      ...
  parsed_jd:
    type: object
    description: Structured job description with extracted fields
    required:
      - job_title
    properties:
      job_title:
        type: string
        example: "Senior Software Engineer"
      company:
        type: string
        example: "Innovation Labs"
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
      responsibilities:
        type: array
        items:
          type: string
      technologies:
        type: array
        items:
          type: string
  company_culture:
    type: string
    description: Research about company culture and values
    example: "Tech-forward startup culture emphasizing innovation and collaboration..."
  best_practices:
    type: string
    description: Resume/cover letter best practices guidelines
    example: "Use strong action verbs, quantify achievements, optimize for ATS..."
  skills_gap_analysis:
    type: object
    description: Analysis of matched vs missing skills
    properties:
      matched:
        type: array
        items:
          type: string
      missing:
        type: array
        items:
          type: string
  document_type:
    type: string
    enum: ["resume", "cover_letter"]
    description: Type of document to generate
```

## Output Schema

```yaml
type: string
description: Draft document content in Markdown format
minLength: 50
example: |
  # JOHN DOE
  Senior Software Engineer | john.doe@email.com | (555) 123-4567

  ## PROFESSIONAL SUMMARY
  Results-driven Senior Software Engineer with 5+ years of experience designing and implementing scalable microservices architectures. Proven track record of optimizing system performance and leading cross-functional teams. Expertise in Python, Django, PostgreSQL, and cloud infrastructure.

  ## TECHNICAL SKILLS
  **Languages**: Python, JavaScript, SQL
  **Frameworks**: Django, Flask, React
  **Cloud & DevOps**: AWS, Docker, Kubernetes, CI/CD
  **Databases**: PostgreSQL, Redis, MongoDB

  ## PROFESSIONAL EXPERIENCE

  ### Senior Software Engineer | Tech Corp | 2020 - Present
  - Architected and deployed microservices platform serving 10M+ daily active users, reducing API latency by 40%
  - Led team of 3 engineers in migrating legacy monolith to containerized architecture, improving deployment frequency by 10x
  - Implemented automated testing and CI/CD pipelines, reducing production bugs by 60%

  ...
```

## Example Usage

### Input Example (Resume)

```json
{
  "master_resume": "# John Doe\nSenior Software Engineer...",
  "parsed_jd": {
    "job_title": "Senior Backend Engineer",
    "company": "TechStart Inc.",
    "requirements": {
      "required": [
        "5+ years Python development",
        "Experience with microservices",
        "PostgreSQL expertise"
      ],
      "preferred": [
        "AWS experience",
        "Docker/Kubernetes knowledge"
      ]
    },
    "technologies": ["Python", "Django", "PostgreSQL", "Docker", "AWS"]
  },
  "company_culture": "Fast-paced startup focusing on innovation and ownership",
  "best_practices": "Use action verbs, quantify results, optimize for ATS",
  "skills_gap_analysis": {
    "matched": ["Python", "PostgreSQL", "Docker", "AWS"],
    "missing": ["Kubernetes", "Terraform"]
  },
  "document_type": "resume"
}
```

### Output Example (Resume)

```markdown
# JOHN DOE
Senior Software Engineer | john.doe@email.com | (555) 123-4567 | LinkedIn: linkedin.com/in/johndoe

## PROFESSIONAL SUMMARY
Results-oriented Senior Software Engineer with 5+ years of experience architecting and deploying scalable microservices solutions. Proven expertise in Python, Django, and PostgreSQL with a track record of optimizing system performance and leading technical initiatives. Passionate about building robust, high-availability systems in fast-paced environments.

## TECHNICAL SKILLS
**Languages & Frameworks**: Python, Django, Flask, JavaScript, SQL
**Databases**: PostgreSQL, Redis, MongoDB
**Cloud & Infrastructure**: AWS (EC2, S3, Lambda, RDS), Docker, CI/CD
**Tools & Practices**: Git, Agile, TDD, REST APIs, Microservices Architecture

## PROFESSIONAL EXPERIENCE

### Senior Software Engineer | Tech Corp | San Francisco, CA | 2020 - Present
- Architected and deployed microservices platform serving 10M+ daily active users, reducing API latency by 40% through query optimization and caching strategies
- Led migration of legacy monolith to containerized Docker-based architecture, improving deployment frequency from weekly to daily releases
- Designed and implemented PostgreSQL database schemas supporting complex multi-tenant applications with 99.9% uptime
- Mentored team of 3 junior engineers on Python best practices and microservices design patterns

### Software Engineer | StartupXYZ | San Francisco, CA | 2018 - 2020
- Developed RESTful APIs using Django and PostgreSQL, processing 1M+ requests daily with sub-100ms response times
- Implemented automated testing suite with 85% code coverage, reducing production bugs by 60%
- Collaborated with product team to design and launch 3 major features, increasing user engagement by 25%
...
```

## Special Instructions

1. **Factual Accuracy**:
   - Use ONLY information from the master resume
   - Never fabricate job titles, dates, achievements, or skills
   - If a skill is missing from master resume, do not include it
   - Preserve all timeline accuracy (dates, durations)

2. **ATS Optimization**:
   - Use standard section headings (EXPERIENCE, EDUCATION, SKILLS)
   - Include keywords from job description naturally throughout
   - Avoid tables, columns, text boxes, or complex formatting
   - Use simple Markdown formatting (headers, bold, lists)
   - Put most important keywords in first third of document

3. **Content Strategy for Resumes**:
   - Lead with strong professional summary highlighting match
   - Technical skills section should mirror JD requirements
   - Prioritize experiences most relevant to job posting
   - Use action verbs (Led, Architected, Implemented, Optimized)
   - Quantify achievements with metrics and percentages
   - Keep to 1-2 pages equivalent length

4. **Content Strategy for Cover Letters**:
   - Opening: Express enthusiasm and reference specific role
   - Body paragraphs: 2-3 key experiences that match requirements
   - Show understanding of company culture and values
   - Demonstrate how background solves their specific needs
   - Closing: Call to action and eagerness to discuss
   - Keep to 300-400 words (3-4 paragraphs)

5. **Tone and Style**:
   - Professional and confident (not arrogant)
   - Active voice throughout
   - Industry-appropriate language
   - Avoid clichés ("team player", "detail-oriented")
   - Be specific and concrete

6. **Skills Gap Handling**:
   - Emphasize matched skills prominently
   - For missing skills: find related/transferable skills if available
   - Focus on demonstrated abilities rather than gaps
   - Never claim skills not in master resume

## Performance Considerations

- **Processing Time**: 10-30 seconds per draft (LLM generation)
- **Input Size**: Master resume typically 2-10KB
- **Output Size**: Resume ~2-5KB, Cover letter ~1-2KB
- **LLM Token Usage**: 1000-3000 tokens per draft

## Quality Checklist

Before returning draft, verify:

1. All facts match master resume
2. Keywords from JD incorporated naturally
3. Strong action verbs used throughout
4. Achievements quantified where possible
5. ATS-friendly formatting (simple Markdown)
6. Appropriate length for document type
7. Professional tone maintained
8. No fabricated information

## Related Agents

- **FactChecker**: Verifies draft accuracy (runs after DraftWriter)
- **DocumentEvaluator**: Evaluates draft quality (runs after DraftWriter)
- **DocumentPolisher**: Refines draft quality (runs in iteration loop)
