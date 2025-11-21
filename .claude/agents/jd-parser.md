# Job Description Parser Agent

## Agent Name

`jd-parser`

## Description

The Job Description Parser agent intelligently parses raw job description HTML/text content into a structured format with extracted fields. It uses LLM capabilities to identify and extract job title, company, requirements, qualifications, technologies, and other key information. Multiple instances run in parallel to process multiple job descriptions simultaneously.

## Agent Type

`general-purpose`

## Task Instructions

When invoked, this agent should:

1. Receive raw job description content (HTML or plain text)
2. Use LLM capabilities to intelligently parse and extract key information
3. Distinguish between required and preferred qualifications
4. Extract specific technologies, tools, and frameworks mentioned
5. Clean HTML tags and format content into readable text
6. Return a comprehensive structured format with all extracted fields
7. Preserve original content in a "raw_text" field for reference

## Input Schema

```yaml
type: string
description: Raw job description content (HTML or plain text)
minLength: 100
example: |
  <html>
  <body>
    <h1>Senior Software Engineer</h1>
    <p>Company: TechCorp Inc.</p>
    <p>Location: San Francisco, CA (Remote)</p>
    <h2>About the Role</h2>
    <p>We are seeking an experienced software engineer...</p>
    <h2>Requirements</h2>
    <ul>
      <li>5+ years of Python development experience</li>
      <li>Experience with distributed systems</li>
    </ul>
  </body>
  </html>
```

## Output Schema

```yaml
type: object
required:
  - job_title
  - company
  - requirements
  - responsibilities
  - qualifications
  - technologies
properties:
  job_title:
    type: string
    description: The job position title
    example: "Senior Software Engineer"
  company:
    type: string
    description: Company or organization name
    example: "TechCorp Inc."
  location:
    type: string
    description: Job location including remote/hybrid information
    example: "San Francisco, CA (Remote)"
  job_type:
    type: string
    description: Employment type (Full-time, Part-time, Contract, etc.)
    example: "Full-time"
  salary_range:
    type: string
    description: Salary or compensation range if mentioned
    example: "$120,000 - $180,000"
  requirements:
    type: object
    description: Structured requirements split by priority
    properties:
      required:
        type: array
        items:
          type: string
        description: Must-have qualifications and skills
        example:
          - "5+ years Python development experience"
          - "Experience with distributed systems"
          - "Strong understanding of data structures and algorithms"
      preferred:
        type: array
        items:
          type: string
        description: Nice-to-have or preferred qualifications
        example:
          - "AWS or GCP experience"
          - "Open source contributions"
          - "Experience with microservices architecture"
  responsibilities:
    type: array
    items:
      type: string
    description: Main job duties and responsibilities
    example:
      - "Design and implement scalable backend services"
      - "Mentor junior engineers and conduct code reviews"
      - "Collaborate with product team on feature development"
  qualifications:
    type: array
    items:
      type: string
    description: Educational and experience qualifications
    example:
      - "Bachelor's degree in Computer Science or equivalent"
      - "5+ years professional software development"
      - "Strong communication and teamwork skills"
  technologies:
    type: array
    items:
      type: string
    description: Technologies, tools, frameworks, and languages mentioned
    example:
      - "Python"
      - "Django"
      - "PostgreSQL"
      - "Docker"
      - "Kubernetes"
      - "AWS"
  benefits:
    type: array
    items:
      type: string
    description: Benefits, perks, and compensation details
    example:
      - "Comprehensive health insurance"
      - "401(k) with company match"
      - "Flexible work hours"
      - "Professional development budget"
  company_description:
    type: string
    description: Brief company description or "About Us" section
    example: "TechCorp is a leading technology company specializing in cloud infrastructure solutions..."
  application_instructions:
    type: string
    description: How to apply or special application instructions
    example: "Apply via our careers page at techcorp.com/careers. Include links to GitHub portfolio."
  raw_text:
    type: string
    description: Clean text version of the JD without HTML tags, for reference
    example: "Senior Software Engineer\nTechCorp Inc.\n\nAbout the Role\nWe are seeking..."
```

## Example Usage

### Input Example

```html
<!DOCTYPE html>
<html>
<head><title>Software Engineer - TechCorp</title></head>
<body>
  <div class="job-posting">
    <h1>Senior Software Engineer</h1>
    <div class="company-info">
      <p><strong>Company:</strong> TechCorp Inc.</p>
      <p><strong>Location:</strong> San Francisco, CA (Remote)</p>
      <p><strong>Type:</strong> Full-time</p>
      <p><strong>Salary:</strong> $140,000 - $180,000</p>
    </div>
    <div class="description">
      <h2>About TechCorp</h2>
      <p>TechCorp is a leading cloud infrastructure company serving Fortune 500 clients.</p>

      <h2>Responsibilities</h2>
      <ul>
        <li>Design and develop scalable microservices using Python and Django</li>
        <li>Lead technical initiatives and mentor junior developers</li>
        <li>Collaborate with DevOps team on CI/CD pipelines</li>
      </ul>

      <h2>Required Qualifications</h2>
      <ul>
        <li>5+ years of professional Python development</li>
        <li>Strong experience with Django or Flask frameworks</li>
        <li>Experience with PostgreSQL and Redis</li>
        <li>Understanding of distributed systems and microservices</li>
      </ul>

      <h2>Preferred Qualifications</h2>
      <ul>
        <li>AWS or GCP cloud platform experience</li>
        <li>Experience with Docker and Kubernetes</li>
        <li>Open source contributions</li>
      </ul>

      <h2>Technologies We Use</h2>
      <p>Python, Django, PostgreSQL, Redis, Docker, Kubernetes, AWS, GitHub Actions</p>

      <h2>Benefits</h2>
      <ul>
        <li>Comprehensive health, dental, and vision insurance</li>
        <li>401(k) with 4% company match</li>
        <li>Unlimited PTO</li>
        <li>$2000/year professional development budget</li>
      </ul>
    </div>
  </div>
</body>
</html>
```

### Output Example

```json
{
  "job_title": "Senior Software Engineer",
  "company": "TechCorp Inc.",
  "location": "San Francisco, CA (Remote)",
  "job_type": "Full-time",
  "salary_range": "$140,000 - $180,000",
  "requirements": {
    "required": [
      "5+ years of professional Python development",
      "Strong experience with Django or Flask frameworks",
      "Experience with PostgreSQL and Redis",
      "Understanding of distributed systems and microservices"
    ],
    "preferred": [
      "AWS or GCP cloud platform experience",
      "Experience with Docker and Kubernetes",
      "Open source contributions"
    ]
  },
  "responsibilities": [
    "Design and develop scalable microservices using Python and Django",
    "Lead technical initiatives and mentor junior developers",
    "Collaborate with DevOps team on CI/CD pipelines"
  ],
  "qualifications": [
    "5+ years of professional Python development",
    "Strong experience with Django or Flask frameworks",
    "Experience with PostgreSQL and Redis",
    "Understanding of distributed systems and microservices"
  ],
  "technologies": [
    "Python",
    "Django",
    "PostgreSQL",
    "Redis",
    "Docker",
    "Kubernetes",
    "AWS",
    "GitHub Actions",
    "Flask"
  ],
  "benefits": [
    "Comprehensive health, dental, and vision insurance",
    "401(k) with 4% company match",
    "Unlimited PTO",
    "$2000/year professional development budget"
  ],
  "company_description": "TechCorp is a leading cloud infrastructure company serving Fortune 500 clients.",
  "application_instructions": "",
  "raw_text": "Senior Software Engineer\n\nCompany: TechCorp Inc.\nLocation: San Francisco, CA (Remote)\nType: Full-time\nSalary: $140,000 - $180,000\n\nAbout TechCorp\nTechCorp is a leading cloud infrastructure company serving Fortune 500 clients.\n\nResponsibilities\n- Design and develop scalable microservices using Python and Django\n- Lead technical initiatives and mentor junior developers\n- Collaborate with DevOps team on CI/CD pipelines\n\nRequired Qualifications\n- 5+ years of professional Python development\n- Strong experience with Django or Flask frameworks\n- Experience with PostgreSQL and Redis\n- Understanding of distributed systems and microservices\n\nPreferred Qualifications\n- AWS or GCP cloud platform experience\n- Experience with Docker and Kubernetes\n- Open source contributions\n\nTechnologies We Use\nPython, Django, PostgreSQL, Redis, Docker, Kubernetes, AWS, GitHub Actions\n\nBenefits\n- Comprehensive health, dental, and vision insurance\n- 401(k) with 4% company match\n- Unlimited PTO\n- $2000/year professional development budget"
}
```

## Special Instructions

1. **Intelligent Parsing**:
   - Use LLM capabilities to understand context and extract information semantically
   - Don't rely solely on HTML structure - parse based on content meaning
   - Handle various job description formats and layouts gracefully
   - Infer missing fields from context when possible

2. **Requirements Classification**:
   - Distinguish between "required" and "preferred/nice-to-have" qualifications
   - Common indicators for required: "must have", "required", "essential"
   - Common indicators for preferred: "preferred", "nice to have", "bonus", "plus"
   - If unclear, default to "required" for safety

3. **Technology Extraction**:
   - Extract ALL technologies mentioned: languages, frameworks, databases, tools, platforms
   - Normalize technology names (e.g., "K8s" -> "Kubernetes", "Postgres" -> "PostgreSQL")
   - Include version numbers if specified (e.g., "Python 3.9+")
   - Deduplicate similar technologies

4. **HTML Cleaning**:
   - Remove all HTML tags from the raw_text output
   - Preserve logical structure with newlines and basic formatting
   - Convert HTML lists to bulleted lists with "-" or numbered lists
   - Remove navigation, headers, footers, and irrelevant content

5. **Missing Information**:
   - If a field cannot be found, use appropriate empty value:
     - Strings: empty string ""
     - Arrays: empty array []
     - Objects: empty object with expected structure
   - Do NOT use "Unknown", "N/A", or placeholder text
   - Log when important fields (job_title, company) are missing

6. **Edge Cases**:
   - Handle job descriptions without clear section headers
   - Parse combined requirement sections (not split into required/preferred)
   - Handle job descriptions in different languages (attempt English extraction)
   - Deal with heavily formatted or poorly structured HTML

## Performance Considerations

- **Parallel Execution**: This agent runs in parallel with multiple instances
- **Typical Parse Time**: 3-10 seconds per job description (LLM processing)
- **Input Size Range**: 100 characters - 100KB per job description
- **Output Size**: 2KB - 20KB structured JSON per job
- **LLM Token Usage**: ~500-2000 tokens per job description

## Parallel Execution Pattern

When parsing multiple job descriptions:

```
Raw JDs: [jd1, jd2, jd3, jd4, jd5]

Launch in parallel:
  - JDParser(jd1) -> structured1
  - JDParser(jd2) -> structured2
  - JDParser(jd3) -> structured3
  - JDParser(jd4) -> structured4
  - JDParser(jd5) -> structured5

Wait for all to complete, collect structured results
```

## Related Agents

- **DocumentFetcher**: Fetches raw job descriptions from URLs (runs before JDParser)
- **JDMatcher**: Matches parsed JDs against resume/qualifications (runs after JDParser)

## Dependencies

- LLM capabilities for intelligent parsing
- HTML parsing utilities (for tag removal)
- Text cleaning and normalization functions
- JSON schema validation

## Quality Assurance

1. **Validation**: Verify output matches the schema before returning
2. **Completeness Check**: Warn if critical fields (job_title, company) are empty
3. **Deduplication**: Remove duplicate entries in arrays (technologies, requirements)
4. **Normalization**: Standardize technology names and terminology
5. **Logging**: Log parsing quality metrics (fields found, confidence level)
