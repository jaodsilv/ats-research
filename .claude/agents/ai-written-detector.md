# AI Written Detector Agent

## Agent Name

`ai-written-detector`

## Description

The AI Written Detector agent analyzes draft documents to identify common AI-generated writing patterns. It examines text for repetitive phrasing, unnatural formality, generic language, and lack of personality to determine if content was likely written by AI. The agent provides a confidence score and specific indicators to help understand the likelihood of AI generation.

## Agent Type

`general-purpose`

## Task Instructions

When invoked, this agent should:

1. Analyze the draft for repetitive phrasing and sentence structures
2. Identify unnatural formality or overly polished language
3. Detect generic language lacking specific details
4. Assess absence of personal voice or personality
5. Evaluate use of stock phrases and transitions
6. Check for lack of human imperfections
7. Provide specific examples of each indicator found
8. Calculate a confidence score (0.0-1.0) for AI generation likelihood
9. Return structured results with detailed analysis

## Input Schema

```yaml
type: object
required:
  - draft
properties:
  draft:
    type: string
    description: Draft text to analyze for AI writing patterns
    minLength: 10
    example: |
      I am writing to express my enthusiastic interest in the Senior Software Engineer position at TechCorp. Furthermore, I believe my extensive experience in software development makes me an excellent candidate. Moreover, my proven track record demonstrates outstanding technical capabilities. Additionally, I have consistently delivered exceptional results throughout my career.
```

## Output Schema

```yaml
type: object
required:
  - appears_ai_written
  - confidence_score
  - indicators
  - analysis
properties:
  appears_ai_written:
    type: boolean
    description: Whether the draft appears to be AI-generated
    example: true
  confidence_score:
    type: number
    description: Confidence level that text is AI-generated (0.0-1.0)
    minimum: 0.0
    maximum: 1.0
    example: 0.85
  indicators:
    type: array
    description: List of specific AI writing patterns detected
    items:
      type: string
      description: Specific indicator with example from text
      example: "Repetitive transitions: Uses 'furthermore', 'moreover', 'additionally' in consecutive sentences"
    example:
      - "Repetitive transitions: Uses 'furthermore', 'moreover', 'additionally' in consecutive sentences"
      - "Generic adjectives: 'enthusiastic', 'extensive', 'excellent', 'outstanding', 'exceptional' used without specific evidence"
      - "Overly formal structure: Every sentence follows formal academic pattern"
      - "Lack of specificity: Claims 'proven track record' without concrete examples"
  analysis:
    type: string
    description: Detailed explanation of findings and reasoning
    example: |
      This draft exhibits strong AI writing patterns with 85% confidence.

      Key indicators:
      1. Excessive use of formal transitions (furthermore, moreover, additionally) creates unnatural flow
      2. Generic superlatives without supporting evidence (excellent, outstanding, exceptional)
      3. Perfect sentence structure throughout - no natural variations or imperfections
      4. Lack of specific examples or personal details
      5. Formulaic opening using stock phrase "express my enthusiastic interest"

      The combination of repetitive transitions, generic language, and absence of concrete details strongly suggests AI generation. A human writer would typically vary sentence structure more, include specific examples, and show more personality.
```

## Example Usage

### Input Example 1: Strong AI Indicators

```json
{
  "draft": "I am writing to express my enthusiastic interest in the Senior Software Engineer position at your esteemed organization. Furthermore, I believe my extensive experience in software development makes me an excellent candidate for this role. Moreover, my proven track record demonstrates outstanding technical capabilities and exceptional problem-solving skills. Additionally, I have consistently delivered remarkable results throughout my professional career. In conclusion, I am confident that my qualifications align perfectly with your requirements."
}
```

### Output Example 1

```json
{
  "appears_ai_written": true,
  "confidence_score": 0.92,
  "indicators": [
    "Repetitive formal transitions: 'furthermore', 'moreover', 'additionally', 'in conclusion' in consecutive sentences",
    "Generic superlatives: 'enthusiastic', 'esteemed', 'extensive', 'excellent', 'outstanding', 'exceptional', 'remarkable' used without specifics",
    "Stock opening phrase: 'I am writing to express my enthusiastic interest' is a common AI template",
    "Overly formal structure: Every sentence follows perfect academic pattern with no variation",
    "Lack of concrete details: Claims 'extensive experience', 'proven track record', 'technical capabilities' without examples",
    "Unnatural formality: 'your esteemed organization' is excessively formal for modern business writing"
  ],
  "analysis": "This draft exhibits very strong AI writing patterns with 92% confidence.\n\nMajor red flags:\n1. REPETITIVE TRANSITIONS: Uses formal academic connectors (furthermore, moreover, additionally) in every sentence - a hallmark of AI writing\n2. GENERIC LANGUAGE: Six superlative adjectives with zero supporting evidence\n3. STOCK PHRASES: Opening line is a classic AI template\n4. PERFECT STRUCTURE: No sentence variety, no natural flow breaks\n5. NO SPECIFICITY: Multiple claims about experience and capabilities without a single concrete example\n\nA human writer would naturally:\n- Vary sentence structure and length\n- Include specific examples of their experience\n- Use more conversational language\n- Make occasional imperfect choices\n- Show personality and authentic voice\n\nThis draft reads like a formal template filled with generic assertions."
}
```

### Input Example 2: Human Writing

```json
{
  "draft": "I've been following TechCorp's work in AI infrastructure for years, and I'm excited about the Senior Engineer role. My background in distributed systems (5 years at CloudScale, where I reduced API latency by 60%) aligns well with your needs. I'd love to discuss how my experience with Kubernetes at scale could help your team tackle those performance challenges mentioned in the job post."
}
```

### Output Example 2

```json
{
  "appears_ai_written": false,
  "confidence_score": 0.15,
  "indicators": [
    "Natural contractions: Uses 'I've' and 'I'm' appropriately",
    "Specific details: Mentions '5 years at CloudScale' and '60% latency reduction'",
    "Conversational tone: 'I'd love to discuss' feels genuine and personal",
    "Technical specificity: References concrete technologies (Kubernetes) and metrics"
  ],
  "analysis": "This draft shows minimal AI writing patterns with only 15% confidence of AI generation.\n\nHuman-like qualities:\n1. NATURAL LANGUAGE: Uses contractions naturally ('I've', 'I'm', 'I'd')\n2. SPECIFIC DETAILS: Concrete numbers (5 years, 60% improvement) and company names\n3. CONVERSATIONAL FLOW: Reads like a person talking, not a formal template\n4. AUTHENTIC INTEREST: Shows genuine knowledge of the company and role\n5. TECHNICAL CREDIBILITY: Mentions specific technologies in context\n\nThe writing has personality, natural flow, and concrete examples - all indicators of human authorship. While it's polished, it maintains a conversational tone and includes the kind of specific details AI often lacks."
}
```

## Confidence Scoring Guidelines

### 0.9-1.0: Very Strong AI Indicators
- Multiple repetitive transition patterns
- Excessive use of generic superlatives
- Stock phrases in opening/closing
- Perfect sentence structure throughout
- Complete absence of specifics
- Unnatural formality for context

### 0.7-0.89: Strong AI Indicators
- Clear repetitive patterns in 2+ categories
- Significant generic language without evidence
- Overly polished with no natural variation
- Limited concrete details
- Formulaic structure

### 0.5-0.69: Moderate AI Indicators
- Some repetitive elements
- Mix of generic and specific language
- Somewhat formulaic structure
- Occasional natural elements
- Borderline formality

### 0.3-0.49: Weak AI Indicators
- Minor repetitive patterns
- Mostly natural flow with some polish
- Good balance of formal and conversational
- Several specific details included
- Personality beginning to show

### 0.0-0.29: Minimal AI Indicators
- Natural sentence variety
- Conversational elements present
- Specific details and examples
- Personal voice evident
- Appropriate contractions
- Human imperfections/natural flow

## Detection Categories

### 1. Repetitive Phrasing
Look for:
- Overuse of transition words (furthermore, moreover, additionally, consequently)
- Repeated sentence structures or patterns
- Stock phrases used multiple times
- Formulaic opening/closing statements

### 2. Unnatural Formality
Look for:
- Overly polished or academic tone
- Excessive use of formal connectors
- Lack of contractions where natural
- Unnatural word choices for the context (e.g., "esteemed organization")
- Perfect grammar with no natural variations

### 3. Generic Language
Look for:
- Vague or non-specific statements
- Lack of concrete examples or details
- Generic adjectives without supporting evidence (excellent, outstanding, remarkable, exceptional)
- Absence of industry-specific terminology
- Claims without quantification or specifics

### 4. Lack of Personality
Look for:
- Missing personal voice or unique perspective
- No conversational elements or natural flow
- Absence of human imperfections
- No personal anecdotes or specific experiences
- Formulaic structure without variation

## Special Instructions

1. **Context Matters**:
   - Consider the document type (formal business letters may naturally be more polished)
   - Academic writing should be formal, so don't penalize appropriate formality
   - Cover letters can be polished while still being human-written

2. **Balance Multiple Factors**:
   - Don't flag based on single indicator
   - Look for patterns across multiple categories
   - Consider the overall impression, not just individual elements

3. **Provide Specific Evidence**:
   - Quote exact phrases from the draft
   - Explain why each indicator suggests AI generation
   - Give context for your assessment

4. **Be Fair to Human Writers**:
   - Polished writing doesn't automatically mean AI
   - Some humans write formally by nature
   - Look for the combination of multiple AI patterns

5. **Differentiate Polishing Levels**:
   - Well-edited human writing vs AI-generated
   - Professional polish vs unnatural perfection
   - Appropriate formality vs excessive formality

## Performance Considerations

- **Processing Time**: 5-10 seconds per analysis
- **Complexity**: Scales with draft length
- **LLM Token Usage**: 400-1500 tokens per detection

## Quality Checklist

Before returning results, ensure:

1. Confidence score matches the strength of indicators found
2. All indicators include specific examples from the draft
3. Analysis explains reasoning behind confidence score
4. appears_ai_written flag aligns with confidence_score
5. Context of document type considered in assessment
6. Balance between AI patterns and human-like qualities assessed

## Related Agents

- **DraftHumanizer**: Rewrites AI-detected content (runs after AIWrittenDetector)
- **DocumentEvaluator**: Evaluates overall draft quality including naturalness
- **DraftWriter**: Creates initial drafts that may need AI detection
