# Resume-Job Description Matcher Agent

## Agent Name

`resume-jd-matcher`

## Description

The Resume-Job Description Matcher agent analyzes how well a resume matches a specific job description, performs comprehensive skills gap analysis, and provides actionable recommendations. It calculates match scores based on required/preferred skills alignment, identifies matched keywords, finds missing skills, and assesses cultural fit. Multiple instances run in parallel (one per job description) for efficient processing.

## Agent Type

`general-purpose`

## Task Instructions

When invoked, this agent should:

1. Receive a master resume, parsed job description, and company culture report
2. Analyze how well the resume aligns with required skills (highest weight)
3. Evaluate coverage of preferred skills and technology stack overlap
4. Assess relevance of past experience to job responsibilities
5. Identify specific keywords and skills present in both resume and JD
6. Detect critical skills gaps (required skills missing from resume)
7. Consider cultural fit based on company culture research
8. Calculate comprehensive match and relevance scores (0.0-1.0)
9. Generate actionable recommendations for tailoring strategy
10. Return structured MatchResult with all analysis data

## Input Schema

```yaml
type: object
required:
  - master_resume
  - parsed_jd
  - company_culture
properties:
  master_resume:
    type: string
    description: Full master resume content in text format
    minLength: 100
    example: |
      John Doe
      Senior Software Engineer

      EXPERIENCE
      TechCorp Inc. - Senior Python Developer (2020-Present)
      - Developed scalable microservices using Python, Django, PostgreSQL
      - Led team of 4 engineers, conducted code reviews
      - Implemented CI/CD pipelines with Docker and Kubernetes

      SKILLS
      Python, Django, Flask, PostgreSQL, Redis, Docker, Kubernetes, AWS
      Agile/Scrum, Team Leadership, Code Review

      EDUCATION
      BS Computer Science - University of Technology (2015)

  parsed_jd:
    type: object
    description: Structured job description from JDParser agent
    required:
      - job_title
      - company
      - requirements
    properties:
      job_title:
        type: string
        example: "Senior Python Engineer"
      company:
        type: string
        example: "InnovateTech Solutions"
      location:
        type: string
        example: "San Francisco, CA (Hybrid)"
      requirements:
        type: object
        properties:
          required:
            type: array
            items:
              type: string
            example:
              - "5+ years Python development"
              - "Experience with Django or Flask"
              - "Strong database skills (PostgreSQL, MySQL)"
              - "Docker and containerization experience"
          preferred:
            type: array
            items:
              type: string
            example:
              - "Kubernetes orchestration experience"
              - "AWS cloud platform experience"
              - "Team leadership experience"
      technologies:
        type: array
        items:
          type: string
        example: ["Python", "Django", "PostgreSQL", "Docker", "Kubernetes", "AWS"]
      responsibilities:
        type: array
        items:
          type: string
        example:
          - "Design and implement backend microservices"
          - "Mentor junior developers"
          - "Collaborate with DevOps on deployment"

  company_culture:
    type: string
    description: Company culture research report (can be empty)
    example: |
      InnovateTech Solutions Culture Report:

      Company values innovation, collaboration, and continuous learning.
      Strong emphasis on work-life balance and flexible work arrangements.
      Engineering-driven culture with focus on technical excellence.
      Open source contributions encouraged.
      Flat organizational structure with minimal hierarchy.
```

## Output Schema

```yaml
type: object
description: MatchResult dataclass with comprehensive match analysis
required:
  - jd_id
  - match_score
  - relevance_score
  - matched_keywords
  - missing_skills
  - recommendation
properties:
  jd_id:
    type: string
    description: Unique identifier for this job description
    example: "InnovateTech_Solutions_Senior_Python_Engineer"

  match_score:
    type: number
    format: float
    minimum: 0.0
    maximum: 1.0
    description: Overall match quality score (0.0 = poor, 1.0 = excellent)
    example: 0.85

  relevance_score:
    type: number
    format: float
    minimum: 0.0
    maximum: 1.0
    description: Relevance of candidate's background to the role
    example: 0.88

  matched_keywords:
    type: array
    items:
      type: string
    description: Keywords and skills found in BOTH resume and job description
    maxItems: 20
    example:
      - "Python"
      - "Django"
      - "PostgreSQL"
      - "Docker"
      - "Kubernetes"
      - "AWS"
      - "Microservices"
      - "Team Leadership"
      - "Code Review"
      - "Agile/Scrum"

  missing_skills:
    type: array
    items:
      type: string
    description: Required skills NOT found in resume (critical gaps)
    maxItems: 15
    example:
      - "MySQL"
      - "Terraform"

  recommendation:
    type: string
    description: Human-readable recommendation (2-4 sentences)
    example: |
      Strong match (0.85) - This candidate has excellent alignment with the role.
      Key strengths: 5+ years Python/Django experience, Docker/Kubernetes skills, team leadership.
      Minor gaps: MySQL experience (has PostgreSQL), Terraform (has general DevOps).
      Strong cultural fit based on innovation and engineering excellence values.
      Recommend applying with emphasis on microservices architecture and mentorship experience.
```

## Scoring Guidelines

**Match Score (0.0-1.0):**

1. **0.9-1.0 (Excellent)**: Nearly all required skills present, strong experience alignment, excellent culture fit
2. **0.8-0.9 (Strong)**: Most required skills covered, good experience fit, minor gaps only
3. **0.7-0.8 (Good)**: Solid coverage of requirements, some notable gaps but addressable
4. **0.6-0.7 (Fair)**: Partial coverage, notable gaps but still viable candidate
5. **0.5-0.6 (Weak)**: Many gaps, questionable fit, major skill deficiencies
6. **Below 0.5 (Poor)**: Major misalignment, not recommended

**Relevance Score (0.0-1.0):**

Consider:
- Industry/domain alignment (same sector vs. different)
- Role/position level match (senior to senior vs. junior to senior)
- Technology stack overlap (modern stack vs. legacy stack)
- Career trajectory alignment (progressive growth vs. lateral moves)

## Example Usage

### Input Example

```json
{
  "master_resume": "John Doe\nSenior Software Engineer\n\nEXPERIENCE\nTechCorp Inc. - Senior Python Developer (2020-Present)\n- Developed scalable microservices using Python, Django, PostgreSQL\n- Led team of 4 engineers, conducted code reviews\n- Implemented CI/CD pipelines with Docker and Kubernetes\n- Deployed services on AWS EC2, RDS, and Lambda\n\nStartup Inc. - Python Developer (2017-2020)\n- Built REST APIs with Flask and SQLAlchemy\n- Worked with PostgreSQL and Redis\n- Collaborated in Agile/Scrum teams\n\nSKILLS\nLanguages: Python, SQL, JavaScript\nFrameworks: Django, Flask, FastAPI\nDatabases: PostgreSQL, Redis, MongoDB\nDevOps: Docker, Kubernetes, AWS, CI/CD\nMethodologies: Agile, Scrum, TDD\nSoft Skills: Team Leadership, Code Review, Mentoring\n\nEDUCATION\nBS Computer Science - University of Technology (2015)",

  "parsed_jd": {
    "job_title": "Senior Python Engineer",
    "company": "InnovateTech Solutions",
    "location": "San Francisco, CA (Hybrid)",
    "requirements": {
      "required": [
        "5+ years Python development experience",
        "Experience with Django or Flask frameworks",
        "Strong database skills (PostgreSQL, MySQL)",
        "Docker and containerization experience",
        "RESTful API design experience"
      ],
      "preferred": [
        "Kubernetes orchestration experience",
        "AWS cloud platform experience",
        "Team leadership and mentoring experience",
        "Open source contributions",
        "Microservices architecture experience"
      ]
    },
    "technologies": [
      "Python",
      "Django",
      "PostgreSQL",
      "MySQL",
      "Docker",
      "Kubernetes",
      "AWS",
      "Redis"
    ],
    "responsibilities": [
      "Design and implement scalable backend microservices",
      "Mentor junior and mid-level developers",
      "Collaborate with DevOps on deployment and infrastructure",
      "Conduct code reviews and establish best practices"
    ]
  },

  "company_culture": "InnovateTech Solutions Culture Report:\n\nCompany values innovation, collaboration, and continuous learning. Strong emphasis on work-life balance with flexible hybrid work arrangements. Engineering-driven culture with focus on technical excellence and code quality. Open source contributions encouraged and supported with dedicated time. Flat organizational structure with minimal hierarchy - engineers have high autonomy. Regular tech talks, hackathons, and learning sessions."
}
```

### Output Example

```json
{
  "jd_id": "InnovateTech_Solutions_Senior_Python_Engineer",
  "match_score": 0.87,
  "relevance_score": 0.90,
  "matched_keywords": [
    "Python",
    "Django",
    "Flask",
    "PostgreSQL",
    "Docker",
    "Kubernetes",
    "AWS",
    "Redis",
    "Microservices",
    "RESTful API",
    "Team Leadership",
    "Mentoring",
    "Code Review",
    "Agile/Scrum",
    "CI/CD",
    "TDD"
  ],
  "missing_skills": [
    "MySQL"
  ],
  "recommendation": "Excellent match (0.87) - This candidate has outstanding alignment with the role requirements. Key strengths to highlight: 8+ years Python experience with Django/Flask, proven microservices architecture expertise, Docker/Kubernetes deployment experience, AWS cloud platform skills, and demonstrated team leadership with mentoring. Only minor gap: MySQL (candidate has extensive PostgreSQL experience which is highly transferable). Strong cultural fit based on innovation focus, engineering excellence values, and open source encouragement. Highly recommend applying with emphasis on microservices projects, team leadership achievements, and technical mentoring experience."
}
```

## Special Instructions

1. **Scoring Philosophy**:
   - Required skills should weigh MORE heavily than preferred skills
   - Substance over keywords: "5 years Python" beats "mentioned Python once"
   - Consider transferable skills (PostgreSQL → MySQL, Docker → Podman)
   - Technical skills AND soft skills both matter
   - Cultural alignment can boost scores for close matches

2. **Matched Keywords**:
   - Be specific: "Python 3.x" not just "Python" if version specified
   - Include technologies, frameworks, methodologies, soft skills
   - Focus on meaningful matches, not trivial word overlap
   - Deduplicate similar technologies (count "K8s" and "Kubernetes" once)
   - Limit to top 20 most important/relevant matches

3. **Missing Skills**:
   - Focus ONLY on REQUIRED skills (ignore preferred skills for this list)
   - Prioritize by importance to the role
   - Don't list skills that are easily transferable
   - Be specific about gaps (e.g., "Terraform" not "DevOps tools")
   - Limit to top 15 most critical gaps

4. **Recommendation Quality**:
   - Start with match level: Excellent/Strong/Good/Fair/Weak/Poor
   - Include match score for transparency
   - List 2-4 key strengths to highlight in tailoring
   - Mention critical gaps and how to address/mitigate them
   - Assess cultural fit based on company culture report
   - End with clear apply/don't apply recommendation
   - Keep to 2-4 sentences (concise but informative)

5. **Cultural Fit Assessment**:
   - If company culture report provided, incorporate it
   - Look for alignment in values, work style, company size
   - Consider startup vs. enterprise culture differences
   - Flag major culture mismatches (can override high technical score)
   - If no culture report, focus only on technical/experience fit

6. **Edge Cases**:
   - Career changers: Lower match score but note transferable skills
   - Overqualified candidates: High match score, flag in recommendation
   - Junior applying for senior: Low score, note experience gap
   - Different industry: Adjust relevance score, note domain switch

## Performance Considerations

- **Parallel Execution**: Multiple instances run in parallel (one per JD)
- **Typical Processing Time**: 5-15 seconds per match (LLM analysis)
- **Input Size Range**:
  - Resume: 1KB - 50KB
  - Parsed JD: 2KB - 20KB
  - Culture report: 0KB - 10KB
- **Output Size**: ~2KB per MatchResult
- **LLM Token Usage**: ~1000-3000 tokens per match

## Parallel Execution Pattern

When matching against multiple job descriptions:

```
Inputs:
  - 1 master resume
  - 1 company culture report
  - N parsed job descriptions

Launch in parallel:
  - ResumeJDMatcher(resume, jd1, culture) -> match1
  - ResumeJDMatcher(resume, jd2, culture) -> match2
  - ResumeJDMatcher(resume, jd3, culture) -> match3
  - ...
  - ResumeJDMatcher(resume, jdN, culture) -> matchN

Wait for all to complete, collect MatchResult objects
```

## Related Agents

- **JDParser**: Parses raw JDs into structured format (runs before this agent)
- **JDsRankerSelector**: Ranks and selects top matches (runs after this agent)
- **DraftWriter**: Uses MatchResult to tailor resume content (downstream consumer)

## Quality Assurance

1. **Score Validation**: Ensure scores are within 0.0-1.0 range
2. **Consistency Check**: Match score should align with recommendation tone
3. **Gap Analysis**: Verify missing_skills are truly absent from resume
4. **Keyword Accuracy**: Validate matched_keywords appear in both documents
5. **Recommendation Quality**: Check for specific, actionable insights
6. **Deduplication**: Remove duplicate keywords and skills
