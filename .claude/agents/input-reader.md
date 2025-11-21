# Input Reader Agent

## Agent Name

`input-reader`

## Description

The Input Reader agent is responsible for reading all required input files from the file system for the resume/cover letter tailoring workflow. This includes best practices guidelines, master resume, and company culture research reports.

## Agent Type

`general-purpose`

## Task Instructions

When invoked, this agent should:

1. Receive a dictionary mapping file type identifiers to file paths
2. Validate that all required files exist and are accessible
3. Read the contents of each file
4. Return a dictionary with the same keys but file contents as values
5. Handle any file reading errors gracefully with clear error messages

## Input Schema

```yaml
type: object
required:
  - resume_best_practices
  - cover_letter_best_practices
  - master_resume
  - company_culture
properties:
  resume_best_practices:
    type: string
    description: Path to resume best practices guidelines file (typically .md)
    example: "./data/best_practices/resume_bp.md"
  cover_letter_best_practices:
    type: string
    description: Path to cover letter best practices guidelines file (typically .md)
    example: "./data/best_practices/cover_letter_bp.md"
  master_resume:
    type: string
    description: Path to master resume document file (typically .tex or .md)
    example: "./data/resumes/master_resume.tex"
  company_culture:
    type: string
    description: Path to company culture research report file (typically .md)
    example: "./data/research/company_culture_report.md"
```

## Output Schema

```yaml
type: object
required:
  - resume_best_practices
  - cover_letter_best_practices
  - master_resume
  - company_culture
properties:
  resume_best_practices:
    type: string
    description: Complete content of the resume best practices file
  cover_letter_best_practices:
    type: string
    description: Complete content of the cover letter best practices file
  master_resume:
    type: string
    description: Complete content of the master resume file
  company_culture:
    type: string
    description: Complete content of the company culture report file
```

## Example Usage

### Input Example

```json
{
  "resume_best_practices": "D:/projects/job-search/data/best_practices/resume_bp.md",
  "cover_letter_best_practices": "D:/projects/job-search/data/best_practices/cl_bp.md",
  "master_resume": "D:/projects/job-search/data/resumes/master_resume.tex",
  "company_culture": "D:/projects/job-search/data/research/techcorp_culture.md"
}
```

### Output Example

```json
{
  "resume_best_practices": "# Resume Best Practices for ATS Optimization\n\n## Overview\nThis document contains...",
  "cover_letter_best_practices": "# Cover Letter Best Practices\n\n## Key Principles\n1. Personalization...",
  "master_resume": "\\documentclass{article}\n\\usepackage{moderncv}\n...",
  "company_culture": "# TechCorp Culture Research\n\n## Company Overview\nTechCorp is a leading..."
}
```

## Special Instructions

1. **File Format Handling**: The agent should handle various text file formats including:
   - Markdown (.md)
   - LaTeX (.tex)
   - Plain text (.txt)
   - Any UTF-8 encoded text file

2. **Error Handling**: If any file is missing or unreadable:
   - Log the specific file that failed
   - Include the file path in the error message
   - Do NOT attempt to continue with partial data
   - Return a clear error indicating which file(s) failed

3. **Encoding**: All files should be read with UTF-8 encoding to support international characters

4. **File Size**: Log the size of each file read for debugging purposes

5. **Validation**: Before reading:
   - Verify each path points to an existing file (not a directory)
   - Check that the file is readable
   - Validate that all required keys are present in the input

6. **Output Integrity**: The returned content should be:
   - Exactly as stored in the file (no modifications)
   - Preserving all whitespace and formatting
   - Including all special characters

## Performance Considerations

- Files are read sequentially (not in parallel) to maintain order and simplify error handling
- Typical file sizes: 10KB - 500KB per file
- Expected total execution time: < 2 seconds for all files
- Memory usage: Approximately 2-4MB for all files combined

## Related Agents

- **DocumentFetcher**: Fetches job descriptions from URLs (runs in parallel with InputReader)
- **JDParser**: Parses fetched job descriptions (runs after DocumentFetcher)

## Dependencies

- File system access (Read tool)
- UTF-8 text encoding support
- Path validation utilities
