# Master Orchestration System

Complete documentation for the master TailoringOrchestra, InteractiveWizard, and entry points.

## Overview

This system provides the top-level coordination for the resume/cover letter tailoring workflow. It integrates all sub-orchestras and provides a user-friendly interface for input collection and execution.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     InteractiveWizard                        │
│  • Collect job URLs                                         │
│  • Validate file paths                                      │
│  • Configure parameters                                     │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│                        main.py                               │
│  • Create Config and RunContext                             │
│  • Setup logging                                            │
│  • Initialize AgentPool                                     │
│  • Run TailoringOrchestra                                   │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│                  TailoringOrchestra                          │
│                                                              │
│  ┌────────────────────────────────────────────────────┐   │
│  │  Stage 1: InputPreparationOrchestra                │   │
│  │  • Load job descriptions from URLs                 │   │
│  │  • Validate input files                            │   │
│  │  • Parse and structure data                        │   │
│  └────────────────────────────────────────────────────┘   │
│                       │                                     │
│                       ▼                                     │
│  ┌────────────────────────────────────────────────────┐   │
│  │  Stage 2: JDMatchingOrchestra                      │   │
│  │  • Match JDs to master resume                      │   │
│  │  • Rank by relevance                               │   │
│  │  • Select best candidates                          │   │
│  └────────────────────────────────────────────────────┘   │
│                       │                                     │
│                       ▼                                     │
│  ┌────────────────────────────────────────────────────┐   │
│  │  Stage 3-4: Writing (Parallel per JD)             │   │
│  │                                                     │   │
│  │  ┌──────────────────────────────────────────┐    │   │
│  │  │ ResumeWritingPolishingOrchestra          │    │   │
│  │  │  • Generate tailored resume              │    │   │
│  │  │  • Polish and refine                     │    │   │
│  │  │  • Fact check                            │    │   │
│  │  └──────────────────────────────────────────┘    │   │
│  │                                                     │   │
│  │  ┌──────────────────────────────────────────┐    │   │
│  │  │ CoverLetterWritingPolishingOrchestra     │    │   │
│  │  │  • Generate tailored cover letter        │    │   │
│  │  │  • Polish and refine                     │    │   │
│  │  │  • AI detection check                    │    │   │
│  │  └──────────────────────────────────────────┘    │   │
│  └────────────────────────────────────────────────────┘   │
│                       │                                     │
│                       ▼                                     │
│  ┌────────────────────────────────────────────────────┐   │
│  │  Stage 5: PruningOrchestra (per document)         │   │
│  │  • Optimize document length                        │   │
│  │  • Human review of PDFs                            │   │
│  │  • Generate release artifacts                      │   │
│  └────────────────────────────────────────────────────┘   │
│                       │                                     │
│                       ▼                                     │
│                  Release Artifacts                         │
│  • Resume PDFs (one per JD)                                │
│  • Cover Letter PDFs (one per JD)                          │
└─────────────────────────────────────────────────────────────┘
```

## Components

### 1. TailoringOrchestra

**File**: `src/orchestrators/tailoring_orchestra.py`

**Purpose**: Master coordinator that orchestrates the complete end-to-end workflow.

**Key Methods**:
- `execute()`: Main orchestration logic (called by `run()`)
- Returns comprehensive results with status and artifacts

**Orchestration Flow**:
1. **Sequential Stage Execution**: Runs 5 sub-orchestras in order
2. **Parallel Document Generation**: Processes multiple JDs concurrently
3. **Error Resilience**: Continues processing even if some JDs fail
4. **Artifact Collection**: Gathers all release PDFs and paths

**Configuration**:
- Inherits from `BaseOrchestra`
- Uses `OrchestrationStage.INITIALIZATION`
- Requires `RunContext` and `AgentPool`

### 2. InteractiveWizard

**File**: `src/human/wizard.py`

**Purpose**: Terminal-based wizard for collecting all user inputs.

**Features**:
- Rich terminal formatting with colors and panels
- Input validation with retry logic
- File existence checking
- Sensible defaults for all parameters
- Comprehensive summary with confirmation

**Collected Data**:
```python
{
    "job_urls": List[str],                    # Job posting URLs
    "input_file_paths": {                     # Validated file paths
        "master_resume": str,
        "resume_guidelines": str,
        "cover_letter_guidelines": str,
        "company_culture": str                # Optional
    },
    "config_params": {                        # Configuration
        "max_iterations": int,
        "quality_threshold": float,
        "agent_pool_size": int | None,
        "ai_detection_threshold": float
    },
    "output_dir": Path                        # Base output directory
}
```

**Key Methods**:
- `run()`: Main wizard flow (async)
- `_collect_job_urls()`: Collect and validate URLs
- `_collect_file_paths()`: Collect and validate file paths
- `_collect_config()`: Collect configuration parameters
- `_display_summary()`: Show summary and request confirmation

### 3. main.py

**File**: `src/main.py`

**Purpose**: Main entry point for the entire system.

**Execution Flow**:
1. Display welcome banner
2. Run `InteractiveWizard` to collect inputs
3. Create `Config` from wizard inputs
4. Create `RunContext` for state management
5. Setup structured logging
6. Populate context with inputs
7. Create `AgentPool` with configured size
8. Execute `TailoringOrchestra`
9. Display final summary
10. Mark run as completed

**Usage**:
```bash
python -m src.main
# or
python src/main.py
```

**Exit Codes**:
- `0`: Success
- `1`: Error or user cancellation

### 4. /tailor Slash Command

**File**: `.claude/commands/tailor.md`

**Purpose**: Quick execution via Claude Code slash command.

**Usage**:
```
/tailor
```

This is equivalent to running `python src/main.py` but provides integrated Claude Code experience.

## Input Requirements

### Required Files

1. **Master Resume** (`.tex` or `.md`)
   - Your comprehensive resume with all experience
   - Location: `data/inputs/master_resume.tex`

2. **Resume Best Practices** (`.md`)
   - Guidelines for resume optimization
   - Location: `data/inputs/resume_best_practices.md`

3. **Cover Letter Best Practices** (`.md`)
   - Guidelines for cover letter writing
   - Location: `data/inputs/cover_letter_best_practices.md`

### Optional Files

4. **Company Culture Report** (`.md`)
   - Research about target companies
   - Location: `data/inputs/company_culture.md`

### Job Posting URLs

- At least one valid job posting URL
- Format: `https://example.com/job/...`
- Must be publicly accessible

## Configuration Parameters

### max_iterations
- **Type**: `int`
- **Default**: `10`
- **Description**: Maximum number of refinement cycles per document
- **Recommendation**:
  - 5 for quick drafts
  - 10 for balanced quality
  - 15-20 for high-quality output

### quality_threshold
- **Type**: `float`
- **Range**: `0.0 - 1.0`
- **Default**: `0.8`
- **Description**: Minimum quality score for document acceptance
- **Recommendation**:
  - 0.7 for fast turnaround
  - 0.8 for balanced quality (recommended)
  - 0.9+ for strict quality

### agent_pool_size
- **Type**: `int | None`
- **Default**: `5`
- **Description**: Maximum concurrent agents (None = unlimited)
- **Recommendation**:
  - 1 for debugging (sequential)
  - 3-5 for balanced (recommended)
  - 10+ for speed (requires good API limits)
  - None for maximum parallelism

### ai_detection_threshold
- **Type**: `float`
- **Range**: `0.0 - 1.0`
- **Default**: `0.999`
- **Description**: AI detection confidence threshold for cover letters
- **Recommendation**:
  - 0.999 for very high confidence (recommended)
  - 0.995 for balanced
  - 0.99 for more lenient

## Output Structure

```
data/
└── runs/
    └── run-{uuid}/
        ├── logs/
        │   └── run-{uuid}.log              # Execution log
        ├── checkpoints/
        │   ├── initialization.json
        │   ├── input_preparation.json
        │   ├── jd_matching.json
        │   ├── writing_polishing.json
        │   ├── pruning.json
        │   └── completed.json
        ├── inputs/
        │   └── job_descriptions/
        │       ├── jd-{id}.json            # Fetched JDs
        │       └── ...
        ├── drafts/
        │   ├── resumes/
        │   │   ├── {jd_id}_v1.tex
        │   │   ├── {jd_id}_v2.tex
        │   │   └── {jd_id}_final.tex
        │   └── cover_letters/
        │       ├── {jd_id}_v1.tex
        │       ├── {jd_id}_v2.tex
        │       └── {jd_id}_final.tex
        └── release/                         # ★ FINAL OUTPUTS ★
            ├── {jd_id}_resume.pdf           # Ready to submit
            └── {jd_id}_cover_letter.pdf     # Ready to submit
```

## Error Handling

### Partial Success
If some JDs fail but others succeed, the orchestration continues:
```python
{
    "status": "partial",
    "jds_processed": 2,
    "jds_failed": 1,
    "release_artifacts": {
        "job-123": {
            "resume": Path(...),
            "cover_letter": Path(...)
        },
        "job-456": {
            "resume": Path(...),
            "cover_letter": Path(...)
        }
    },
    "failed_jds": ["job-789"]
}
```

### Complete Failure
If critical stages fail, the entire orchestration stops:
- Input preparation failure → Stops immediately
- JD matching failure → Stops immediately
- All JDs fail → Returns empty artifacts

### Logging
All errors are logged with full stack traces to:
- Console (via Rich handler)
- Log file: `data/runs/run-{id}/logs/run-{id}.log`

### Recovery
Checkpoints are saved at each stage:
- Review checkpoints: `data/runs/run-{id}/checkpoints/*.json`
- Manual recovery feature in development

## Examples

### Example 1: Single Job Application

```bash
$ /tailor
Step 1/4: Job Posting URLs
Job URL #1: https://example.com/job/senior-engineer
Job URL #2 (or 'done'): done

Step 2/4: Input File Paths
[Use defaults by pressing Enter]

Step 3/4: Configuration Parameters
[Use defaults by pressing Enter]

Step 4/4: Output Directory
[Use default: data]

Proceed with this configuration? [Y/n]: y

[... orchestration runs ...]

✓ Status: SUCCESS
  JDs Processed: 1

📦 Release Artifacts:
  job-senior-engineer:
    📄 Resume:       data/runs/run-abc/release/job-senior-engineer_resume.pdf
    📄 Cover Letter: data/runs/run-abc/release/job-senior-engineer_cover_letter.pdf
```

### Example 2: Batch Processing with Custom Config

```bash
$ /tailor
Step 1/4: Job Posting URLs
Job URL #1: https://example.com/job/1
Job URL #2 (or 'done'): https://example.com/job/2
Job URL #3 (or 'done'): https://example.com/job/3
Job URL #4 (or 'done'): done

Step 2/4: Input File Paths
[Use defaults]

Step 3/4: Configuration Parameters
Max Iterations [10]: 15
Quality Threshold [0.8]: 0.9
Agent Pool Size [5]: 3
AI Detection Threshold [0.999]: [Enter]

Step 4/4: Output Directory
[Use default: data]

Proceed with this configuration? [Y/n]: y

[... orchestration runs ...]

✓ Status: SUCCESS
  JDs Processed: 3

📦 Release Artifacts:
  [3 complete application sets]
```

## Performance Considerations

### Concurrency
- **Agent pool size** controls parallelism
- Each JD gets its own resume + cover letter generation (parallel)
- Pruning runs sequentially per document

### API Rate Limits
- Higher `agent_pool_size` = more concurrent API calls
- Monitor API usage in logs
- Reduce pool size if hitting rate limits

### Execution Time
Estimated time per JD (with `agent_pool_size=5`):
- Input prep: 30s (one-time)
- JD matching: 1-2 minutes (one-time)
- Resume writing: 5-10 minutes per JD (parallel)
- Cover letter writing: 5-10 minutes per JD (parallel)
- Pruning: 2-5 minutes per document (sequential)

**Total for 3 JDs**: ~20-30 minutes

### Memory Usage
- Checkpoint data accumulates in memory
- Large runs (10+ JDs) may need more RAM
- Consider running in batches for 20+ JDs

## Troubleshooting

### Issue: "File not found"
**Solution**: Check file paths in wizard, ensure files exist

### Issue: "API rate limit exceeded"
**Solution**: Reduce `agent_pool_size` or wait before retrying

### Issue: "LaTeX compilation failed"
**Solution**:
1. Check LaTeX syntax in master resume
2. Ensure `pdflatex` is installed and in PATH
3. Review logs for specific LaTeX errors

### Issue: "No JDs selected after matching"
**Solution**:
1. Review matching criteria in logs
2. Lower `quality_threshold`
3. Improve master resume content

### Issue: "Wizard cancelled unexpectedly"
**Solution**:
1. Check terminal encoding (Windows: use UTF-8)
2. Run with Python 3.9+ for full Rich support

## Best Practices

1. **Organize Input Files**: Keep all inputs in `data/inputs/`
2. **Use Version Control**: Track master resume and guidelines in git
3. **Start Small**: Test with 1-2 JDs before batch processing
4. **Monitor Logs**: Watch `logs/run-{id}.log` for issues
5. **Review Drafts**: Check intermediate drafts before final release
6. **Preserve Runs**: Don't delete run directories (useful for debugging)
7. **Iterate Configuration**: Adjust thresholds based on output quality

## Future Enhancements

Planned features:
1. **Checkpoint Recovery**: Resume from failed runs
2. **Web Interface**: GUI alternative to wizard
3. **Batch Templates**: Save and reuse wizard configurations
4. **Quality Reports**: Detailed analysis of generated documents
5. **A/B Testing**: Compare different configuration strategies

## Support

For issues or questions:
1. Check logs: `data/runs/run-{id}/logs/run-{id}.log`
2. Review checkpoints: `data/runs/run-{id}/checkpoints/*.json`
3. Consult documentation: `USAGE_EXAMPLES.md`
4. File an issue with run ID and logs
