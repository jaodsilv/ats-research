# Text Impact Calculator Agent

## Agent Name

`text-impact-calculator`

## Description

The Text Impact Calculator agent analyzes a draft document and calculates impact scores for each text segment (sections, paragraphs, bullet points, sentences). Impact scores range from 0.0 (low impact/relevance) to 1.0 (high impact/critical content) based on relevance to job requirements, quantifiable achievements, keyword density, and best practices alignment. This scoring guides pruning decisions by identifying which content is most valuable to preserve.

## Agent Type

`general-purpose`

## Task Instructions

When invoked, this agent should:

1. Break the draft into meaningful text segments (sections, bullets, sentences)
2. For each segment, calculate impact score (0.0 to 1.0) based on:
   - Relevance to job requirements (40% weight)
   - Quantifiable achievements (30% weight)
   - Keyword density from JD (20% weight)
   - Best practices alignment (10% weight)
3. Identify segment type (header, summary, section, bullet, sentence, paragraph)
4. Count lines in each segment
5. Return structured array of all segments with scores

## Input Schema

```yaml
type: object
required:
  - draft
  - parsed_jd
properties:
  draft:
    type: string
    description: Draft content to analyze for impact scores
    minLength: 10
    example: |
      # JOHN DOE
      Senior Software Engineer

      ## PROFESSIONAL SUMMARY
      Results-driven engineer with 5+ years in Python and AWS...

      ## EXPERIENCE
      ### Senior Engineer | Tech Corp | 2020-Present
      - Led microservices platform serving 10M users
      - Reduced API latency by 40% through optimization
      - Proficient in Microsoft Office
  parsed_jd:
    type: object
    description: Parsed job description with requirements
    properties:
      job_title:
        type: string
      company:
        type: string
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
    description: Best practices guidelines for evaluation
```

## Output Schema

```yaml
type: object
required:
  - text_segments
properties:
  text_segments:
    type: array
    description: Array of text segments with impact scores
    items:
      type: object
      required:
        - segment
        - impact_score
        - segment_type
        - line_count
      properties:
        segment:
          type: string
          description: The text content of the segment
          example: "Led microservices platform serving 10M users"
        impact_score:
          type: number
          minimum: 0.0
          maximum: 1.0
          description: Impact score from 0.0 (low) to 1.0 (high)
          example: 0.92
        segment_type:
          type: string
          enum: ["header", "summary", "section", "bullet", "sentence", "paragraph"]
          description: Type of text segment
          example: "bullet"
        line_count:
          type: integer
          minimum: 1
          description: Number of lines in the segment
          example: 1
```

## Example Usage

### Input Example

```json
{
  "draft": "# JOHN DOE\nSenior Software Engineer\n\n## PROFESSIONAL SUMMARY\nResults-driven Senior Software Engineer with 5+ years experience architecting microservices in Python and AWS.\n\n## EXPERIENCE\n### Senior Engineer | Tech Corp | 2020-Present\n- Led development of microservices platform serving 10M users\n- Reduced API latency by 40% through caching and optimization\n- Proficient in Microsoft Office Suite\n- Hobbies include photography",
  "parsed_jd": {
    "job_title": "Senior Backend Engineer",
    "company": "TechStart Inc.",
    "requirements": {
      "required": ["Python", "Microservices", "AWS", "5+ years experience"],
      "preferred": ["Docker", "Kubernetes"]
    },
    "technologies": ["Python", "AWS", "Docker", "Microservices", "PostgreSQL"]
  },
  "best_practices": "Use strong action verbs, quantify achievements, align with job requirements"
}
```

### Output Example

```json
{
  "text_segments": [
    {
      "segment": "# JOHN DOE",
      "impact_score": 0.5,
      "segment_type": "header",
      "line_count": 1
    },
    {
      "segment": "Results-driven Senior Software Engineer with 5+ years experience architecting microservices in Python and AWS.",
      "impact_score": 0.88,
      "segment_type": "summary",
      "line_count": 1
    },
    {
      "segment": "Led development of microservices platform serving 10M users",
      "impact_score": 0.92,
      "segment_type": "bullet",
      "line_count": 1
    },
    {
      "segment": "Reduced API latency by 40% through caching and optimization",
      "impact_score": 0.85,
      "segment_type": "bullet",
      "line_count": 1
    },
    {
      "segment": "Proficient in Microsoft Office Suite",
      "impact_score": 0.15,
      "segment_type": "bullet",
      "line_count": 1
    },
    {
      "segment": "Hobbies include photography",
      "impact_score": 0.05,
      "segment_type": "bullet",
      "line_count": 1
    }
  ]
}
```

## Special Instructions

1. **Impact Score Calculation** (Total: 100%):

   **Relevance to Job Requirements (40%)**:
   - Direct match with required skills/tech: 0.8-1.0
   - Indirect relevance to job duties: 0.4-0.7
   - Unrelated to job posting: 0.0-0.3

   **Quantifiable Achievements (30%)**:
   - Specific metrics/percentages: +0.2 to +0.3
   - Measurable impact shown: +0.1 to +0.2
   - Generic statements: No bonus

   **Keyword Density (20%)**:
   - High density of JD keywords: +0.1 to +0.2
   - Some JD keywords: +0.05 to +0.1
   - No JD keywords: No bonus

   **Best Practices Alignment (10%)**:
   - Strong action verbs: +0.05
   - Clear, concise writing: +0.05

2. **Segment Type Classification**:
   - **header**: Document title, name, contact headers
   - **summary**: Professional summary or objective section
   - **section**: Major section headers (Experience, Skills, Education)
   - **bullet**: Individual bullet points in lists
   - **sentence**: Individual sentences in paragraphs
   - **paragraph**: Multi-sentence text blocks

3. **Segmentation Strategy**:
   - Break document at natural boundaries (sections, bullets, sentences)
   - Preserve complete thoughts (don't split mid-sentence)
   - Maintain context (include section headers as separate segments)
   - Count each bullet point as individual segment
   - Split long paragraphs into sentences

4. **Impact Score Interpretation**:
   - **0.0-0.2**: Very low impact, safe to remove
   - **0.2-0.4**: Low-medium impact, consider for removal
   - **0.4-0.6**: Medium impact, consider for rewriting
   - **0.6-0.8**: High impact, preserve and maybe enhance
   - **0.8-1.0**: Critical content, must preserve

5. **Examples of Scoring**:
   - "Led 10-person team implementing AWS microservices" → 0.92 (relevant tech + quantified + action verb)
   - "Experience with programming" → 0.3 (too generic, no specifics)
   - "Proficient in Microsoft Office" → 0.15 (common skill, likely not in JD)
   - "Hobbies include reading" → 0.05 (irrelevant to job)

## Performance Considerations

- **Processing Time**: 10-30 seconds (LLM analysis)
- **Segment Count**: Typically 20-100 segments per resume
- **Input Size**: 2-10KB draft content
- **LLM Token Usage**: 1000-3000 tokens
- **Output Size**: 5-20KB structured JSON

## Quality Checklist

Before returning impact scores, verify:

1. All draft content segmented (no missing text)
2. Impact scores are in range [0.0, 1.0]
3. Segment types are valid enum values
4. Line counts are positive integers
5. High relevance content scored appropriately (> 0.6)
6. Low relevance content scored appropriately (< 0.3)
7. Quantified achievements receive score boost
8. JD keyword matches reflected in scores

## Related Agents

- **RewritingEvaluator**: Uses impact scores to identify rewrite candidates (runs after TextImpactCalculator)
- **RemovalEvaluator**: Uses impact scores to identify removal candidates (runs after TextImpactCalculator)
- **DeltaCalculator**: May reference impact scores when calculating quality delta (runs after evaluators)
