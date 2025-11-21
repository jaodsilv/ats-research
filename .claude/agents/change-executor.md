# Change Executor Agent

## Agent Name

`change-executor`

## Description

The Change Executor agent applies a single change (rewrite or removal) to a draft document, producing a modified version. It performs string replacement for rewrites, removal for deletions, and cleans up excessive whitespace after removals to maintain proper formatting. This agent operates deterministically without LLM involvement, making it fast and reliable.

## Agent Type

`general-purpose`

## Task Instructions

When invoked, this agent should:

1. Receive draft content and a single change to apply
2. Determine change type (rewrite or removal)
3. For rewrites:
   - Locate original_text in draft
   - Replace first occurrence with rewritten_text
   - Return modified draft
4. For removals:
   - Locate text_to_remove in draft
   - Remove first occurrence
   - Clean up excessive whitespace (multiple newlines)
   - Return modified draft
5. If text not found, return draft unchanged with warning

**NOTE**: This agent does NOT use Task tool - it performs simple string operations in Python.

## Input Schema

```yaml
type: object
required:
  - draft
  - change
properties:
  draft:
    type: string
    description: Current draft content to modify
    minLength: 10
    example: |
      # JOHN DOE
      Senior Engineer

      Responsible for leading a team of 5 engineers.
      Proficient in Microsoft Office.
  change:
    type: object
    description: Single change to apply (rewrite OR removal)
    oneOf:
      - required: [original_text, rewritten_text]
      - required: [text_to_remove]
    properties:
      # For rewrites
      original_text:
        type: string
        description: Text to find and replace
        example: "Responsible for leading"
      rewritten_text:
        type: string
        description: Replacement text
        example: "Led"
      # For removals
      text_to_remove:
        type: string
        description: Text to remove
        example: "Proficient in Microsoft Office."
      # Optional metadata
      quality_delta:
        type: number
      length_reduction:
        type: integer
      rationale:
        type: string
```

## Output Schema

```yaml
type: string
description: Modified draft with change applied
minLength: 10
example: |
  # JOHN DOE
  Senior Engineer

  Led a team of 5 engineers.
```

## Example Usage

### Input Example (Rewrite)

```json
{
  "draft": "Responsible for leading and managing a team of 5 software engineers in developing new features.\n\nVery proficient in Python programming.",
  "change": {
    "original_text": "Responsible for leading and managing",
    "rewritten_text": "Led",
    "quality_delta": 0.05,
    "length_reduction": 28,
    "rationale": "Stronger verb, removed redundancy"
  }
}
```

### Output Example (Rewrite)

```text
Led a team of 5 software engineers in developing new features.

Very proficient in Python programming.
```

### Input Example (Removal)

```json
{
  "draft": "## TECHNICAL SKILLS\n- Python, AWS, Docker\n- Proficient in Microsoft Office Suite\n- PostgreSQL, Redis\n\n## EXPERIENCE\nLed development...",
  "change": {
    "text_to_remove": "- Proficient in Microsoft Office Suite\n",
    "impact_score": 0.15,
    "quality_delta": -0.05,
    "length_reduction": 41,
    "rationale": "Generic skill not in JD"
  }
}
```

### Output Example (Removal)

```text
## TECHNICAL SKILLS
- Python, AWS, Docker
- PostgreSQL, Redis

## EXPERIENCE
Led development...
```

## Special Instructions

1. **String Replacement for Rewrites**:
   - Use `str.replace(original_text, rewritten_text, 1)` to replace first occurrence only
   - Preserve all surrounding text and formatting
   - If original_text not found, log warning and return draft unchanged
   - Do not modify case, whitespace, or formatting around replacement

2. **String Removal for Deletions**:
   - Use `str.replace(text_to_remove, "", 1)` to remove first occurrence only
   - Clean up resulting whitespace issues:
     - Replace 3+ consecutive newlines with 2 newlines
     - Remove trailing whitespace from lines
   - If text_to_remove not found, log warning and return draft unchanged
   - Avoid creating orphaned bullets or empty sections

3. **Whitespace Cleanup Algorithm**:
   ```python
   # Remove excessive blank lines (3+ → 2)
   while "\n\n\n" in text:
       text = text.replace("\n\n\n", "\n\n")

   # Remove trailing spaces from lines
   lines = [line.rstrip() for line in text.split("\n")]
   text = "\n".join(lines)
   ```

4. **Error Handling**:
   - If text not found: Return original draft unchanged
   - Log warning with preview of missing text (first 50 chars)
   - Do not raise exception - gracefully degrade
   - Return valid draft in all cases

5. **Performance**:
   - No LLM usage - pure string operations
   - Processing time: < 0.1 seconds
   - Deterministic results
   - No API calls or network operations

6. **Validation**:
   - Verify draft is non-empty after change
   - Ensure no malformed structure created
   - Check that change actually modified the draft (if text was found)
   - Log before/after length for tracking

## Performance Considerations

- **Processing Time**: < 0.1 seconds (string operations only)
- **No LLM Usage**: Pure Python string manipulation
- **Memory**: Minimal (2x draft size during operation)
- **Deterministic**: Same input always produces same output

## Quality Checklist

Before returning modified draft, verify:

1. Draft is non-empty string
2. If rewrite: original text was found and replaced
3. If removal: text was found and removed
4. Whitespace cleaned up (no 3+ consecutive newlines)
5. No trailing spaces on lines
6. No orphaned sections or formatting issues
7. Draft length decreased as expected (for removals)
8. Draft structure still valid (headers, sections intact)

## Common Issues and Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| Text not found | Text was already modified | Log warning, return draft unchanged |
| Multiple occurrences | Text appears multiple times | Only replace/remove first occurrence |
| Orphaned bullets | Removed last bullet in section | Clean up empty sections manually |
| Excessive whitespace | Removal left gaps | Apply whitespace cleanup algorithm |
| Case mismatch | Text case differs | Ensure exact match including case |

## Related Agents

- **ChangesRanker**: Ranks changes and selects which to apply (runs before ChangeExecutor)
- **TEXTemplateFiller**: May process modified draft into LaTeX (runs after ChangeExecutor)
- **DocumentEvaluator**: May evaluate modified draft quality (runs after ChangeExecutor)

## Usage Pattern

Typically used in a loop:
1. Get ranked changes from ChangesRanker
2. Select next change to apply
3. Call ChangeExecutor with current draft + change
4. Check if target length reached
5. If not, repeat with next change

Example:
```python
draft = original_draft
for change in ranked_changes:
    if change["recommended"]:
        draft = await change_executor.run({
            "draft": draft,
            "change": change
        })
        if len(draft) <= target_length:
            break
```
