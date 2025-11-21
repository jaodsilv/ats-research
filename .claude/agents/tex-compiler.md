# TEX Compiler Agent

## Agent Name

`tex-compiler`

## Description

The TEX Compiler agent compiles LaTeX (.tex) files to PDF format using the pdflatex command. It handles temporary file management, runs pdflatex compilation (potentially multiple passes for references), captures compilation errors, and returns the resulting PDF path or error information. This agent uses Bash tool directly rather than Task tool for compilation.

## Agent Type

`general-purpose`

## Task Instructions

When invoked, this agent should:

1. Create a temporary working directory for compilation
2. Write the LaTeX content to a temporary .tex file
3. Run pdflatex compilation (2 passes for references)
4. Check for successful PDF generation
5. If successful: Copy PDF to output path
6. If failed: Parse log file for error messages
7. Clean up temporary files
8. Return compilation results

**IMPORTANT**: This agent uses the Bash tool directly (via subprocess in Python) to run pdflatex, NOT the Task tool.

## Input Schema

```yaml
type: object
required:
  - tex_content
  - output_path
properties:
  tex_content:
    type: string
    description: Complete LaTeX document content to compile
    minLength: 50
    example: |
      \documentclass[11pt,a4paper]{article}
      \usepackage[utf8]{inputenc}
      \begin{document}
      \section{Test}
      This is a test document.
      \end{document}
  output_path:
    type: string
    description: Absolute path where compiled PDF should be saved
    pattern: ".*\\.pdf$"
    example: "D:/output/resume.pdf"
```

## Output Schema

```yaml
type: object
required:
  - pdf_path
  - success
  - errors
properties:
  pdf_path:
    type: string
    description: Absolute path to compiled PDF file (empty if compilation failed)
    example: "D:/output/resume.pdf"
  success:
    type: boolean
    description: Whether compilation succeeded
    example: true
  errors:
    type: array
    description: List of compilation error messages (empty if successful)
    items:
      type: string
    example: []
```

## Example Usage

### Input Example (Successful Compilation)

```json
{
  "tex_content": "\\documentclass[11pt,letterpaper]{article}\n\\usepackage[utf8]{inputenc}\n\\usepackage{geometry}\n\\geometry{margin=1in}\n\n\\begin{document}\n\n\\begin{center}\n\\textbf{\\Large JOHN DOE}\\\\\nSenior Software Engineer\n\\end{center}\n\n\\section{Experience}\n\\textbf{Tech Corp} | Senior Engineer | 2020-Present\n\\begin{itemize}\n  \\item Led microservices development\n  \\item Reduced latency by 40\\%\n\\end{itemize}\n\n\\end{document}",
  "output_path": "D:/documents/resume_v1.pdf"
}
```

### Output Example (Success)

```json
{
  "pdf_path": "D:/documents/resume_v1.pdf",
  "success": true,
  "errors": []
}
```

### Output Example (Failure)

```json
{
  "pdf_path": "",
  "success": false,
  "errors": [
    "! Undefined control sequence.",
    "l.15 \\invalidcommand",
    "! Missing $ inserted."
  ]
}
```

## Special Instructions

1. **Compilation Process**:
   - Run pdflatex with `-interaction=nonstopmode` to avoid hanging on errors
   - Use `-output-directory` to control where files are generated
   - Run compilation TWICE to resolve references (first pass generates aux files, second pass resolves)
   - Set 60-second timeout to prevent infinite loops

2. **Error Handling**:
   - Check if PDF file was created after compilation
   - If not created, parse the .log file for error messages
   - Extract lines starting with "!" or containing "Error:"
   - Return up to 10 most relevant error messages
   - Handle common errors: missing packages, syntax errors, encoding issues

3. **File Management**:
   - Create temporary directory for compilation artifacts
   - Write .tex content to temp directory
   - After successful compilation, copy PDF to final output path
   - Ensure output directory exists (create if needed)
   - Clean up temp directory after completion

4. **System Requirements**:
   - Requires pdflatex to be installed and in PATH
   - Handle FileNotFoundError if pdflatex not installed
   - Return helpful error message suggesting TeX distribution installation

5. **Output Path Handling**:
   - Convert output_path to absolute path
   - Create parent directories if they don't exist
   - Overwrite existing PDF at output_path if present
   - Return absolute path to compiled PDF

## Performance Considerations

- **Processing Time**: 2-10 seconds per document
- **First Compilation Pass**: 1-5 seconds
- **Second Compilation Pass**: 1-3 seconds (faster, uses cached data)
- **Timeout**: 60 seconds maximum
- **Temp Disk Space**: 1-5MB during compilation

## Quality Checklist

Before returning compilation results, verify:

1. PDF file exists at output_path (if success=true)
2. PDF file size > 0 bytes
3. Error list populated if compilation failed
4. Temporary files cleaned up
5. Output path is absolute
6. Parent directories created

## Common Errors and Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| `pdflatex command not found` | TeX not installed | Install MiKTeX or TeX Live |
| `Undefined control sequence` | Invalid LaTeX command | Check LaTeX syntax in input |
| `Missing $ inserted` | Unescaped math symbols | Escape %, $, &, #, _ properly |
| `File not found` | Missing package | Install required LaTeX packages |
| `Emergency stop` | Critical syntax error | Review log file for details |
| `Timeout` | Infinite loop or hanging | Check for circular references |

## Related Agents

- **TEXTemplateFiller**: Generates the .tex content (runs before TEXCompiler)
- **TextImpactCalculator**: May analyze compiled PDF length (runs after TEXCompiler)
