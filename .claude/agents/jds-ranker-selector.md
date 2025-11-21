# Job Descriptions Ranker and Selector Agent

## Agent Name

`jds-ranker-selector`

## Description

The JDs Ranker and Selector agent ranks multiple job description match results by their match scores and selects the top N candidates for resume tailoring. It provides comprehensive rankings with detailed metrics, generates selection rationale, and only runs conditionally when there are multiple job descriptions to compare (skipped for single JD scenarios).

Uses the `select_top_jds()` function from the decision_logic module for consistent ranking logic across the system.

## Agent Type

`general-purpose`

## Task Instructions

When invoked, this agent should:

1. Receive a list of MatchResult objects from multiple ResumeJDMatcher runs
2. Sort all matches by match_score in descending order (highest first)
3. Select the top N job descriptions for tailoring (default: 3)
4. Create detailed rankings with rank numbers and selection flags
5. Generate human-readable selection rationale explaining the choices
6. Include score statistics (average, min, max) for selected JDs
7. Provide quality assessment of selected matches
8. Return structured output with selected JD IDs and full rankings

## Conditional Execution

**IMPORTANT**: This agent should ONLY run when there are multiple job descriptions (2+).

For single JD scenarios:
- Skip this agent entirely
- Pass the single MatchResult directly to downstream agents
- No ranking or selection needed

## Input Schema

```yaml
type: array
description: List of MatchResult objects from ResumeJDMatcher agent
minItems: 1
items:
  type: object
  description: MatchResult dataclass with match analysis data
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
      description: Unique identifier for the job description
      example: "TechCorp_Senior_Python_Engineer"
    match_score:
      type: number
      format: float
      minimum: 0.0
      maximum: 1.0
      description: Overall match quality score
      example: 0.85
    relevance_score:
      type: number
      format: float
      minimum: 0.0
      maximum: 1.0
      description: Relevance of candidate's background
      example: 0.88
    matched_keywords:
      type: array
      items:
        type: string
      description: Keywords found in both resume and JD
      example: ["Python", "Django", "PostgreSQL", "Docker"]
    missing_skills:
      type: array
      items:
        type: string
      description: Required skills not in resume
      example: ["MySQL", "Terraform"]
    recommendation:
      type: string
      description: Human-readable recommendation text
      example: "Strong match - highlight microservices experience"

example:
  - jd_id: "TechCorp_Senior_Python_Engineer"
    match_score: 0.85
    relevance_score: 0.88
    matched_keywords: ["Python", "Django", "Docker", "AWS"]
    missing_skills: ["MySQL"]
    recommendation: "Strong match - emphasize microservices and leadership"
  - jd_id: "StartupCo_Backend_Developer"
    match_score: 0.72
    relevance_score: 0.75
    matched_keywords: ["Python", "Flask", "PostgreSQL"]
    missing_skills: ["Go", "GraphQL", "Redis"]
    recommendation: "Good match - some gaps in preferred technologies"
  - jd_id: "InnovateTech_Lead_Engineer"
    match_score: 0.91
    relevance_score: 0.89
    matched_keywords: ["Python", "Django", "Kubernetes", "AWS", "Leadership"]
    missing_skills: []
    recommendation: "Excellent match - perfect alignment with requirements"
```

## Output Schema

```yaml
type: object
required:
  - selected_jds
  - rankings
  - selection_rationale
properties:
  selected_jds:
    type: array
    items:
      type: string
    description: List of top N jd_ids selected for tailoring (ordered by rank)
    example:
      - "InnovateTech_Lead_Engineer"
      - "TechCorp_Senior_Python_Engineer"
      - "StartupCo_Backend_Developer"

  rankings:
    type: array
    description: Full rankings of all JDs with detailed metrics
    items:
      type: object
      required:
        - jd_id
        - match_score
        - relevance_score
        - rank
        - selected
      properties:
        jd_id:
          type: string
          description: Job description identifier
          example: "InnovateTech_Lead_Engineer"
        match_score:
          type: number
          format: float
          description: Match score (rounded to 3 decimals)
          example: 0.910
        relevance_score:
          type: number
          format: float
          description: Relevance score (rounded to 3 decimals)
          example: 0.890
        rank:
          type: integer
          description: Rank position (1 = highest)
          example: 1
        selected:
          type: boolean
          description: Whether this JD was selected for tailoring
          example: true
        matched_keywords_count:
          type: integer
          description: Number of matched keywords
          example: 15
        missing_skills_count:
          type: integer
          description: Number of missing skills
          example: 0
        recommendation:
          type: string
          description: Original recommendation from matcher
          example: "Excellent match - perfect alignment"

  selection_rationale:
    type: string
    description: Human-readable explanation of selection (2-4 sentences)
    example: |
      Selected top 3 job descriptions out of 5 total. Selected JDs have match scores
      ranging from 0.72 to 0.91 (average: 0.83). These are good to excellent matches
      with solid to strong skill coverage. Focus tailoring efforts on these positions
      for highest success probability.
```

## Selection Logic

The agent uses the `select_top_jds()` function from `decision_logic.py`:

```python
from decisions.decision_logic import select_top_jds

# Rank by match_score descending, select top N
selected_jd_ids = select_top_jds(matches, top_n=3)
```

**Default**: top_n = 3 (select top 3 JDs)

**Edge Cases**:
- If fewer JDs than top_n exist, select all available
- If tie scores at cutoff, include all tied JDs
- If all scores below threshold (0.5), still select top N but flag in rationale

## Example Usage

### Input Example

```json
[
  {
    "jd_id": "TechCorp_Senior_Python_Engineer",
    "match_score": 0.85,
    "relevance_score": 0.88,
    "matched_keywords": [
      "Python", "Django", "PostgreSQL", "Docker", "Kubernetes",
      "AWS", "Microservices", "Team Leadership", "Code Review"
    ],
    "missing_skills": ["MySQL"],
    "recommendation": "Strong match (0.85) - Excellent alignment. Key strengths: microservices architecture, Docker/Kubernetes, team leadership. Minor gap: MySQL (has PostgreSQL). Recommend applying."
  },
  {
    "jd_id": "StartupCo_Backend_Developer",
    "match_score": 0.72,
    "relevance_score": 0.75,
    "matched_keywords": [
      "Python", "Flask", "PostgreSQL", "REST API", "Agile"
    ],
    "missing_skills": ["Go", "GraphQL", "Redis", "Terraform"],
    "recommendation": "Good match (0.72) - Solid Python/Flask skills. Gaps: Go language, GraphQL, Redis caching. Consider applying if interested in startup environment."
  },
  {
    "jd_id": "InnovateTech_Lead_Engineer",
    "match_score": 0.91,
    "relevance_score": 0.89,
    "matched_keywords": [
      "Python", "Django", "Flask", "PostgreSQL", "Docker",
      "Kubernetes", "AWS", "Microservices", "Team Leadership",
      "Mentoring", "Code Review", "CI/CD", "TDD"
    ],
    "missing_skills": [],
    "recommendation": "Excellent match (0.91) - Outstanding alignment with all requirements. Perfect fit for leadership role. Strong cultural match. Highly recommend applying."
  },
  {
    "jd_id": "MegaCorp_Staff_Engineer",
    "match_score": 0.68,
    "relevance_score": 0.70,
    "matched_keywords": [
      "Python", "PostgreSQL", "AWS", "Team Leadership"
    ],
    "missing_skills": [
      "Java", "Spring Boot", "Kafka", "Cassandra", "Spark"
    ],
    "recommendation": "Fair match (0.68) - Python skills align but role requires significant Java/JVM experience. Major technology stack gaps. Apply only if willing to learn new stack."
  },
  {
    "jd_id": "CloudCo_Platform_Engineer",
    "match_score": 0.79,
    "relevance_score": 0.81,
    "matched_keywords": [
      "Python", "Docker", "Kubernetes", "AWS", "CI/CD",
      "Terraform", "Microservices"
    ],
    "missing_skills": ["GCP", "Azure"],
    "recommendation": "Good match (0.79) - Strong DevOps and platform engineering alignment. Minor gaps in multi-cloud (GCP/Azure). Recommend applying with focus on AWS expertise."
  }
]
```

### Output Example

```json
{
  "selected_jds": [
    "InnovateTech_Lead_Engineer",
    "TechCorp_Senior_Python_Engineer",
    "CloudCo_Platform_Engineer"
  ],
  "rankings": [
    {
      "jd_id": "InnovateTech_Lead_Engineer",
      "match_score": 0.910,
      "relevance_score": 0.890,
      "rank": 1,
      "selected": true,
      "matched_keywords_count": 13,
      "missing_skills_count": 0,
      "recommendation": "Excellent match (0.91) - Outstanding alignment with all requirements. Perfect fit for leadership role. Strong cultural match. Highly recommend applying."
    },
    {
      "jd_id": "TechCorp_Senior_Python_Engineer",
      "match_score": 0.850,
      "relevance_score": 0.880,
      "rank": 2,
      "selected": true,
      "matched_keywords_count": 9,
      "missing_skills_count": 1,
      "recommendation": "Strong match (0.85) - Excellent alignment. Key strengths: microservices architecture, Docker/Kubernetes, team leadership. Minor gap: MySQL (has PostgreSQL). Recommend applying."
    },
    {
      "jd_id": "CloudCo_Platform_Engineer",
      "match_score": 0.790,
      "relevance_score": 0.810,
      "rank": 3,
      "selected": true,
      "matched_keywords_count": 7,
      "missing_skills_count": 2,
      "recommendation": "Good match (0.79) - Strong DevOps and platform engineering alignment. Minor gaps in multi-cloud (GCP/Azure). Recommend applying with focus on AWS expertise."
    },
    {
      "jd_id": "StartupCo_Backend_Developer",
      "match_score": 0.720,
      "relevance_score": 0.750,
      "rank": 4,
      "selected": false,
      "matched_keywords_count": 5,
      "missing_skills_count": 4,
      "recommendation": "Good match (0.72) - Solid Python/Flask skills. Gaps: Go language, GraphQL, Redis caching. Consider applying if interested in startup environment."
    },
    {
      "jd_id": "MegaCorp_Staff_Engineer",
      "match_score": 0.680,
      "relevance_score": 0.700,
      "rank": 5,
      "selected": false,
      "matched_keywords_count": 4,
      "missing_skills_count": 5,
      "recommendation": "Fair match (0.68) - Python skills align but role requires significant Java/JVM experience. Major technology stack gaps. Apply only if willing to learn new stack."
    }
  ],
  "selection_rationale": "Selected top 3 job descriptions out of 5 total. Selected JDs have match scores ranging from 0.79 to 0.91 (average: 0.85). These are good to excellent matches with strong alignment to the resume. Focus tailoring efforts on these three positions for highest probability of success."
}
```

## Special Instructions

1. **Ranking Criteria**:
   - Primary: Sort by `match_score` descending (highest first)
   - Secondary: If tie scores, use `relevance_score` as tiebreaker
   - Tertiary: If still tied, maintain original order

2. **Selection Count**:
   - Default `top_n = 3` (select top 3 JDs)
   - Can be configured via agent initialization parameter
   - If fewer JDs available than top_n, select all
   - Example: 2 JDs with top_n=3 → select both

3. **Rationale Generation**:
   - State total JDs and number selected
   - Provide score range (min to max) of selected JDs
   - Calculate and mention average score of selected JDs
   - Include quality assessment:
     - avg >= 0.8: "excellent matches"
     - avg >= 0.7: "good matches"
     - avg >= 0.6: "fair matches"
     - avg < 0.6: "weak matches, best available"
   - If selected count < top_n, note in rationale
   - Keep to 2-4 sentences

4. **Rankings List**:
   - Include ALL JDs (selected and not selected)
   - Sort by rank (1, 2, 3, ...)
   - Round scores to 3 decimal places
   - Set `selected: true` for top N, `false` for rest
   - Include counts (matched keywords, missing skills)
   - Preserve original recommendation text

5. **Edge Cases**:
   - Empty input list: Return empty results with error rationale
   - Single JD: Technically works but should be skipped by orchestrator
   - All low scores (<0.5): Still select top N but flag in rationale
   - Tie scores at cutoff: Include all tied JDs (may exceed top_n)

6. **Decision Logic Integration**:
   - Use `select_top_jds()` function from `decision_logic.py`
   - This ensures consistency with decision framework
   - Function handles sorting and selection automatically
   - Agent focuses on formatting and rationale generation

## Performance Considerations

- **Execution**: Single agent (NOT parallel - runs after all matchers complete)
- **Typical Processing Time**: <1 second (simple sorting and selection)
- **Input Size Range**: 1-50 MatchResult objects typical, up to 100 supported
- **Output Size**: ~2KB + (N_jds × 500 bytes) for rankings
- **No LLM Usage**: Pure computational logic, no LLM calls needed

## Execution Flow

```
Sequential execution after all ResumeJDMatcher instances complete:

Wait for parallel matchers:
  MatchResult1 ----┐
  MatchResult2 ----┤
  MatchResult3 ----┼--→ [All complete]
  MatchResult4 ----┤
  MatchResult5 ----┘
                   ↓
          JDsRankerSelector
         (rank and select top N)
                   ↓
         Output: selected_jds + rankings
```

## Related Agents

- **ResumeJDMatcher**: Produces MatchResult inputs (runs in parallel before this agent)
- **DraftWriter**: Consumes selected_jds for tailoring (runs after this agent)
- **TailoringOrchestrator**: Orchestrates the full workflow including conditional execution

## Conditional Execution Logic

The orchestrator should check before running this agent:

```python
from decisions.decision_logic import should_rank_jds

jd_count = len(parsed_jds)

if should_rank_jds(jd_count):
    # Run JDsRankerSelector
    result = await jds_ranker_selector.run(all_match_results)
    selected_jds = result["selected_jds"]
else:
    # Single JD - skip ranking, use directly
    selected_jds = [all_match_results[0].jd_id]
```

## Quality Assurance

1. **Ranking Correctness**: Verify JDs sorted by match_score descending
2. **Selection Count**: Ensure exactly top_n JDs selected (or fewer if not available)
3. **Score Statistics**: Validate avg/min/max calculations in rationale
4. **Selection Flags**: Check `selected: true` for exactly top N entries
5. **Rank Numbering**: Verify ranks are sequential 1, 2, 3, ...
6. **Completeness**: Confirm all input JDs appear in rankings output
