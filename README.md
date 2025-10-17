# ATS Research

Public repository containing research on Applicant Tracking Systems (ATS), workflow diagrams for job application optimization, and best practices documentation.

## Overview

This repository contains:
1. Comprehensive ATS platform research (top 20 platforms for small and large companies)
2. Workflow orchestration diagrams (mermaid format)
3. Best practices research for resumes and cover letters

## Repository Structure

```
ats-research/
├── top20.md                                    # Comprehensive ATS platform research
├── 00.CompanyResearchDiagram.mmd               # Company research workflow
├── 01.MasterResumediagram.mmd                  # Master resume structure
├── 02.1.BestPracticesResearch.CoverLetter.mmd  # Cover letter best practices
├── 02.2.BestPracticesResearch.Resume.mmd       # Resume best practices
├── 03.TailoringOrchestra.mmd                   # Resume tailoring workflow
├── 04.JDMatchingOrchestra.mmd                  # Job description matching process
├── 05.DraftWritingOrchestra.mmd                # Draft writing process
├── 06.PolishingOrchestra.mmd                   # Document polishing workflow
└── 07.PruningOrchestra.mmd                     # Content pruning process
```

## ATS Platform Research

The `top20.md` file contains comprehensive research comparing top ATS platforms:
- Market share data
- Feature comparisons
- Small company vs large company recommendations
- Data aggregated from ChatGPT, Claude, and Gemini

## Workflow Diagrams

Mermaid diagrams document the complete job application workflow:

1. **Company Research**: Research target companies
2. **Master Resume**: Maintain comprehensive resume
3. **Best Practices Research**: Cover letter and resume best practices
4. **Tailoring**: Customize resume for specific roles
5. **JD Matching**: Match qualifications to job descriptions
6. **Draft Writing**: Create initial application documents
7. **Polishing**: Refine and optimize content
8. **Pruning**: Remove unnecessary content

## Rendering Diagrams

To render mermaid diagrams:

```bash
# Install mermaid-cli
npm install -g @mermaid-js/mermaid-cli

# Render single diagram
mmdc -i 00.CompanyResearchDiagram.mmd -o 00.CompanyResearchDiagram.png

# Render all diagrams
for file in *.mmd; do
  mmdc -i "$file" -o "rendered/${file%.mmd}.png"
done
```

## Related Repositories

1. **job-applications** (private): Actual application documents
2. **job-hunting-automation** (public): Python automation tools
3. **latex-templates** (public): Document templates

## Usage

This research informs:
- Resume and cover letter customization strategies
- ATS optimization techniques
- Job application workflow automation
- Platform selection for companies of different sizes

## Future Enhancements

1. Automated diagram rendering via GitHub Actions
2. Comparison table generator from research data
3. Claude Code slash commands for research updates
4. Integration with job-hunting-automation tools

## Contributing

This research is publicly shared to help job seekers optimize their applications. Contributions welcome:
- Additional ATS platform research
- Workflow diagram improvements
- Best practices updates
- Community feedback on effectiveness

## License

MIT License - See LICENSE file
