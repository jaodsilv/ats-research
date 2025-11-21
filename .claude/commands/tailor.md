# Tailor Command

Run the resume/cover letter tailoring orchestration system.

## Description

This command launches the interactive wizard and executes the complete tailoring workflow:

1. Input collection (job URLs, file paths, configuration)
2. Job description fetching and parsing
3. Resume matching and ranking
4. Resume/cover letter drafting and polishing
5. Document length optimization (with human feedback)
6. Release artifact generation

## Usage

```bash
/tailor
```

## Requirements

- All input files must exist:
  - Resume best practices guidelines
  - Cover letter best practices guidelines
  - Master resume
  - Company culture report (optional)
- Job posting URLs must be accessible
- LaTeX distribution installed (for PDF compilation)
- Python environment with all dependencies installed

## Parameters

None - the interactive wizard will collect all inputs interactively.

## Outputs

- Release-ready resume PDFs (one per selected JD)
- Release-ready cover letter PDFs (one per selected JD)
- All intermediate artifacts saved in `data/runs/run-{id}/`
- Comprehensive logs in `data/runs/run-{id}/logs/`

## Example

```
/tailor

→ Launches interactive wizard
→ Collects job URLs and file paths
→ Executes full tailoring workflow
→ Generates release artifacts
```

## Workflow Stages

The command executes five sequential orchestration stages:

1. **Input Preparation**: Loads and validates all input files and job descriptions
2. **JD Matching**: Matches job descriptions to master resume and selects best candidates
3. **Writing & Polishing**: Generates tailored resume and cover letter drafts (parallel)
4. **Fact Checking**: Verifies all claims against master resume
5. **Pruning**: Optimizes document length with human-in-the-loop feedback

## Technical Details

- **Execution**: `python D:\src\ats-research\src\main.py`
- **Runtime**: Async orchestration with configurable parallelism
- **Human-in-the-loop**: PDF review for length optimization
- **State Management**: Full checkpoint system for recovery
- **Logging**: Structured logs with Rich formatting

## Configuration Options

The wizard will prompt for:

- **Max Iterations** (default: 10): Maximum refinement cycles per document
- **Quality Threshold** (default: 0.8): Minimum quality score (0-1) for acceptance
- **Agent Pool Size** (default: 5): Max concurrent agents (0 = unlimited)
- **AI Detection Threshold** (default: 0.999): AI detection confidence threshold

## Output Structure

```
data/
└── runs/
    └── run-{uuid}/
        ├── logs/
        │   └── run-{uuid}.log
        ├── checkpoints/
        │   └── *.json
        ├── inputs/
        │   └── job_descriptions/
        ├── drafts/
        │   ├── resumes/
        │   └── cover_letters/
        └── release/
            ├── {jd_id}_resume.pdf
            └── {jd_id}_cover_letter.pdf
```

## Troubleshooting

### Common Issues

1. **"File not found"**
   - Solution: Check file paths provided in wizard
   - Ensure all input files exist at specified locations

2. **"LaTeX compilation failed"**
   - Solution: Ensure `pdflatex` is installed and in PATH
   - Check LaTeX syntax in master resume

3. **"API rate limit"**
   - Solution: Reduce agent_pool_size in wizard configuration
   - Add delays between API calls if needed

4. **"JD fetch failed"**
   - Solution: Verify job posting URLs are accessible
   - Check for rate limiting or authentication requirements

### Debug Mode

To run with debug logging, set environment variable before running:

```bash
export LOG_LEVEL=DEBUG
/tailor
```

### Recovery from Failure

The system automatically checkpoints progress. To resume from a failed run:

1. Note the run ID from the error output
2. Manually inspect `data/runs/run-{id}/checkpoints/`
3. Contact support for recovery assistance (feature in development)

## Exit Codes

- **0**: Success - all documents generated
- **1**: Error - fatal failure or user cancellation

## Notes

- The wizard can be cancelled at any time with Ctrl+C
- All intermediate files are preserved for debugging
- Release artifacts are production-ready PDFs
- The system supports unlimited parallel JD processing (limited only by agent_pool_size)
