# TEX Template Filler Agent

## Agent Name

`tex-template-filler`

## Description

The TEX Template Filler agent converts draft content (typically in Markdown format) into a filled LaTeX (.tex) document by populating a LaTeX template. It handles the conversion of Markdown formatting to LaTeX syntax, ensures proper escaping of special LaTeX characters, and prepares the document for PDF compilation via pdflatex.

## Agent Type

`general-purpose`

## Task Instructions

When invoked, this agent should:

1. Read the specified LaTeX template file
2. Convert Markdown draft content to LaTeX formatting:
   - Headers (# -> \section{}, ## -> \subsection{}, etc.)
   - Bold text (**text** -> \textbf{text})
   - Italic text (*text* -> \textit{text})
   - Lists (- item -> \item in itemize environment)
3. Escape special LaTeX characters (%, $, &, #, _, {, })
4. Fill template placeholders with converted content
5. Ensure proper LaTeX document structure
6. Return complete filled LaTeX document ready for compilation

## Input Schema

```yaml
type: object
required:
  - draft
  - template_path
  - document_type
properties:
  draft:
    type: string
    description: Draft content in Markdown format to fill into template
    minLength: 10
    example: |
      # JOHN DOE
      Senior Software Engineer

      ## PROFESSIONAL SUMMARY
      Results-driven engineer with 5+ years experience...

      ## TECHNICAL SKILLS
      - Python, JavaScript, SQL
      - Docker, Kubernetes, AWS
  template_path:
    type: string
    description: Path to LaTeX template file to fill
    example: "./templates/resume.tex"
  document_type:
    type: string
    enum: ["resume", "cover_letter"]
    description: Type of document being generated
```

## Output Schema

```yaml
type: string
description: Complete filled LaTeX document content
minLength: 50
example: |
  \documentclass[11pt,a4paper]{article}
  \usepackage[utf8]{inputenc}
  \usepackage{geometry}
  \geometry{margin=1in}

  \begin{document}

  \begin{center}
  \textbf{\Large JOHN DOE}\\
  \textbf{Senior Software Engineer}
  \end{center}

  \section{PROFESSIONAL SUMMARY}
  Results-driven engineer with 5+ years experience...

  \section{TECHNICAL SKILLS}
  \begin{itemize}
    \item Python, JavaScript, SQL
    \item Docker, Kubernetes, AWS
  \end{itemize}

  \end{document}
```

## Example Usage

### Input Example

```json
{
  "draft": "# JOHN DOE\nSenior Software Engineer | john@email.com\n\n## PROFESSIONAL SUMMARY\nResults-driven Senior Software Engineer with 5+ years of experience in cloud architecture and microservices...\n\n## TECHNICAL SKILLS\n- **Languages**: Python, JavaScript, SQL\n- **Cloud**: AWS, Docker, Kubernetes\n\n## EXPERIENCE\n\n### Senior Engineer | Tech Corp | 2020-Present\n- Led development of microservices platform\n- Reduced API latency by 40%",
  "template_path": "./templates/resume_modern.tex",
  "document_type": "resume"
}
```

### Output Example

```latex
\documentclass[11pt,letterpaper]{moderncv}
\moderncvstyle{classic}
\moderncvcolor{blue}

\usepackage[utf8]{inputenc}
\usepackage[scale=0.85]{geometry}

\name{JOHN}{DOE}
\title{Senior Software Engineer}
\email{john@email.com}

\begin{document}
\makecvtitle

\section{PROFESSIONAL SUMMARY}
Results-driven Senior Software Engineer with 5+ years of experience in cloud architecture and microservices...

\section{TECHNICAL SKILLS}
\cvitem{Languages}{Python, JavaScript, SQL}
\cvitem{Cloud}{AWS, Docker, Kubernetes}

\section{EXPERIENCE}
\cventry{2020--Present}{Senior Engineer}{Tech Corp}{}{}{%
\begin{itemize}
  \item Led development of microservices platform
  \item Reduced API latency by 40\%
\end{itemize}}

\end{document}
```

## Special Instructions

1. **Markdown to LaTeX Conversion**:
   - Headers: # -> \section{}, ## -> \subsection{}, ### -> \subsubsection{}
   - Bold: **text** or __text__ -> \textbf{text}
   - Italic: *text* or _text_ -> \textit{text}
   - Unordered lists: - item or * item -> \item in \begin{itemize}
   - Ordered lists: 1. item -> \item in \begin{enumerate}

2. **Character Escaping**:
   - Percent: % -> \%
   - Dollar: $ -> \$
   - Ampersand: & -> \&
   - Hash: # (outside headers) -> \#
   - Underscore: _ (outside markdown) -> \_
   - Braces: { } -> \{ \}
   - Backslash: \ -> \textbackslash{}

3. **Template Placeholder Handling**:
   - Common placeholders: {{NAME}}, {{CONTENT}}, {{SKILLS}}, etc.
   - Replace placeholders with corresponding content from draft
   - Preserve template structure and styling commands

4. **Document Structure**:
   - Maintain proper \documentclass and preamble from template
   - Ensure \begin{document} and \end{document} are present
   - Keep all \usepackage commands from template
   - Preserve geometry and formatting settings

5. **Error Prevention**:
   - Validate that output is valid LaTeX syntax
   - Ensure all environments are properly closed
   - Check for unescaped special characters
   - Verify no unmatched braces or brackets

6. **Content Preservation**:
   - Maintain all draft content faithfully
   - Preserve spacing and paragraph breaks
   - Keep quantifiable metrics and achievements intact
   - Don't add or remove information

## Performance Considerations

- **Processing Time**: 5-15 seconds (LLM-based conversion)
- **Input Size**: Draft typically 2-10KB, Template 1-5KB
- **Output Size**: Filled .tex file typically 3-15KB
- **LLM Token Usage**: 500-2000 tokens

## Quality Checklist

Before returning filled LaTeX document, verify:

1. Valid LaTeX syntax (compilable)
2. All special characters properly escaped
3. All Markdown formatting converted to LaTeX
4. Template structure preserved
5. All draft content included
6. Proper document class and preamble
7. \begin{document} and \end{document} present
8. No unmatched braces or environments

## Related Agents

- **TEXCompiler**: Compiles the filled .tex file to PDF (runs after TEXTemplateFiller)
- **ChangeExecutor**: May modify draft before template filling (runs before TEXTemplateFiller)
