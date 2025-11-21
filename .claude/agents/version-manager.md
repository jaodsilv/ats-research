# Version Manager Agent

## Agent Name

`version-manager`

## Description

The Version Manager agent handles document version storage and retrieval throughout the polishing workflow. It maintains a history of document versions, allowing the workflow to restore previous versions if quality degrades during polishing iterations. Unlike other agents, this agent performs direct file I/O operations rather than complex AI processing.

## Agent Type

`general-purpose`

## Task Instructions

When invoked, this agent should:

1. **For "store" action**:
   - Accept document content and metadata
   - Determine next version number (auto-increment)
   - Save version to versioned storage with metadata
   - Return version number and confirmation

2. **For "restore" action**:
   - Accept document ID and version number
   - Retrieve specified version from storage
   - Return version content and metadata

3. Maintain version metadata (timestamps, scores, iteration numbers)
4. Support version history queries
5. Handle storage errors gracefully

## Input Schema

```yaml
type: object
required:
  - action
  - document_id
properties:
  action:
    type: string
    enum: ["store", "restore"]
    description: Whether to store a new version or restore an existing one
    example: "store"
  document_id:
    type: string
    description: Unique identifier for the document being versioned
    minLength: 1
    example: "resume_tech_corp_senior_engineer"
  content:
    type: string
    description: Document content (required for "store" action)
    minLength: 10
    example: |
      # JOHN DOE
      Senior Software Engineer

      ## PROFESSIONAL SUMMARY
      Results-driven engineer with 5+ years...
  version_num:
    type: integer
    description: Version number to restore (required for "restore" action)
    minimum: 1
    example: 3
  metadata:
    type: object
    description: Optional metadata to store with version (for "store" action)
    properties:
      score:
        type: number
        description: Quality score for this version
        minimum: 0.0
        maximum: 1.0
      iteration:
        type: integer
        description: Polishing iteration number
      notes:
        type: string
        description: Notes about this version
    example:
      score: 0.85
      iteration: 2
      notes: "After fixing grammar issues"
```

## Output Schema

```yaml
type: object
required:
  - version_num
  - timestamp
properties:
  version_num:
    type: integer
    description: Version number stored or restored
    minimum: 1
    example: 3
  content:
    type: string
    description: Document content (returned for "restore" action)
    example: |
      # JOHN DOE
      Senior Software Engineer...
  metadata:
    type: object
    description: Version metadata
    properties:
      score:
        type: number
      iteration:
        type: integer
      notes:
        type: string
    example:
      score: 0.85
      iteration: 2
      notes: "After fixing grammar issues"
  timestamp:
    type: string
    format: date-time
    description: ISO 8601 timestamp of when version was created
    example: "2025-10-20T14:30:00Z"
```

## Example Usage

### Input Example (Store)

```json
{
  "action": "store",
  "document_id": "resume_tech_corp_senior_engineer",
  "content": "# JOHN DOE\nSenior Software Engineer | john.doe@email.com\n\n## PROFESSIONAL SUMMARY\nResults-driven Senior Software Engineer with 5+ years...",
  "metadata": {
    "score": 0.85,
    "iteration": 2,
    "notes": "Fixed grammar and improved keyword density"
  }
}
```

### Output Example (Store)

```json
{
  "version_num": 3,
  "timestamp": "2025-10-20T14:30:45Z",
  "metadata": {
    "score": 0.85,
    "iteration": 2,
    "notes": "Fixed grammar and improved keyword density"
  }
}
```

### Input Example (Restore)

```json
{
  "action": "restore",
  "document_id": "resume_tech_corp_senior_engineer",
  "version_num": 2
}
```

### Output Example (Restore)

```json
{
  "version_num": 2,
  "content": "# JOHN DOE\nSenior Software Engineer | john.doe@email.com\n\n## PROFESSIONAL SUMMARY\nResults-oriented Senior Software Engineer...",
  "metadata": {
    "score": 0.82,
    "iteration": 1,
    "notes": "After initial polishing"
  },
  "timestamp": "2025-10-20T14:15:23Z"
}
```

## Special Instructions

1. **Version Numbering**:
   - Versions are numbered sequentially starting from 1
   - Auto-increment on each store operation
   - Version numbers are unique per document_id

2. **Storage Location**:
   - Versions stored in `artifacts/versions/{document_id}/v{num}.json`
   - Each version includes content, metadata, and timestamp
   - Storage managed via StateManager.save_version() and load_version()

3. **Error Handling**:
   - If restore requested for non-existent version, return clear error
   - If storage fails, provide actionable error message
   - Validate document_id format before operations

4. **Metadata Management**:
   - Always include timestamp when storing
   - Preserve all metadata fields when restoring
   - Support arbitrary metadata fields for extensibility

5. **Performance Considerations**:
   - Operations should be fast (<1 second)
   - No AI processing needed for this agent
   - Direct file system operations via StateManager

## Performance Considerations

- **Processing Time**: <1 second per operation (file I/O only)
- **Storage Size**: Typically 2-10KB per version
- **No LLM Usage**: This agent performs direct file operations

## Quality Checklist

Before returning result, verify:

1. Version number is correct and sequential
2. Content matches what was stored (for restore)
3. Metadata is preserved accurately
4. Timestamp is in ISO 8601 format
5. File was successfully written/read from storage

## Related Agents

- **DocumentEvaluator**: Generates scores stored in version metadata
- **DocumentPolisher**: Creates new versions after polishing
- **IssueFixer**: Creates new versions after fixing issues
