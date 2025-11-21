# Usage Examples

This document provides practical examples of using the tailoring orchestration system.

## Quick Start

### Using the /tailor Slash Command (Recommended)

The simplest way to run the system:

```bash
/tailor
```

This launches the interactive wizard which will guide you through:
1. Entering job posting URLs
2. Providing input file paths
3. Configuring parameters
4. Starting the orchestration

### Using Python Directly

```bash
python -m src.main
# or
python src/main.py
```

## Interactive Wizard Walkthrough

When you run `/tailor` or `src/main.py`, you'll see:

```
================================================================================
RESUME & COVER LETTER TAILORING SYSTEM
================================================================================

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                                                                            ┃
┃  Resume & Cover Letter Tailoring System                                   ┃
┃  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                  ┃
┃                                                                            ┃
┃  This wizard will guide you through setting up a tailoring run.           ┃
┃  You'll need to provide:                                                  ┃
┃    • Job posting URLs                                                      ┃
┃    • Input file paths (resume, guidelines, company culture)               ┃
┃    • Configuration parameters                                             ┃
┃                                                                            ┃
┃  Press Ctrl+C at any time to cancel.                                      ┃
┃                                                                            ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

Step 1/4: Job Posting URLs
Enter the URLs of job postings you want to apply to.
(Enter each URL, then press Enter. Type 'done' when finished)

Job URL #1: https://example.com/job/senior-software-engineer
✓ Added: https://example.com/job/senior-software-engineer
Job URL #2 (or 'done'): https://example.com/job/backend-developer
✓ Added: https://example.com/job/backend-developer
Job URL #3 (or 'done'): done

Collected 2 job URL(s)

Step 2/4: Input File Paths
Provide paths to your input files.

Master Resume: Path to your master resume file (LaTeX or Markdown)
  Path [data/inputs/master_resume.tex]:
  ✓ Found: D:\src\ats-research\data\inputs\master_resume.tex

Resume Guidelines: Path to resume best practices guidelines
  Path [data/inputs/resume_best_practices.md]:
  ✓ Found: D:\src\ats-research\data\inputs\resume_best_practices.md

Cover Letter Guidelines: Path to cover letter best practices guidelines
  Path [data/inputs/cover_letter_best_practices.md]:
  ✓ Found: D:\src\ats-research\data\inputs\cover_letter_best_practices.md

Company Culture Report: Path to company culture research (optional)
  Path [data/inputs/company_culture.md]:
  ✓ Found: D:\src\ats-research\data\inputs\company_culture.md

All file paths collected

Step 3/4: Configuration Parameters
Configure orchestration behavior (press Enter for defaults).

Max Iterations (refinement cycles per document) [10]:
Quality Threshold (0.0-1.0, acceptance threshold) [0.8]:
Agent Pool Size (max concurrent agents, or 0 for unlimited)
  Pool size [5]: 3
AI Detection Threshold (0.0-1.0, for cover letters) [0.999]:

Configuration collected

Step 4/4: Output Directory
Where should outputs be saved?

Output directory [data]:
✓ Output directory: D:\src\ats-research\data

================================================================================
Configuration Summary
================================================================================

Job Posting URLs:
  1. https://example.com/job/senior-software-engineer
  2. https://example.com/job/backend-developer

Input Files:
  Master Resume           data/inputs/master_resume.tex
  Resume Guidelines       data/inputs/resume_best_practices.md
  Cover Letter Guidelines data/inputs/cover_letter_best_practices.md
  Company Culture         data/inputs/company_culture.md

Configuration:
  Max Iterations           10
  Quality Threshold        0.8
  Agent Pool Size          3
  AI Detection Threshold   0.999

Output Directory: data

================================================================================

Proceed with this configuration? [Y/n]: y

✓ Configuration complete!
```

## Programmatic Usage

### Basic Usage

```python
import asyncio
from src.main import main

# Run the full workflow
results = asyncio.run(main())

print(f"Processed {results['jds_processed']} job descriptions")
print(f"Release artifacts: {results['release_artifacts']}")
```

### Advanced: Custom Configuration

```python
import asyncio
from src.config import Config
from src.state.run_context import RunContext
from src.agents.agent_pool import AgentPool
from src.orchestrators import TailoringOrchestra

async def custom_tailoring():
    # Create custom configuration
    config = Config(
        max_iterations=15,
        quality_threshold=0.85,
        agent_pool_size=10,
        ai_detection_threshold=0.995,
        base_data_dir=Path("custom_output")
    )

    # Create run context
    run_context = await RunContext.create(config)

    # Populate with inputs (skip wizard)
    await run_context.add_context_data("job_urls", [
        "https://example.com/job/1",
        "https://example.com/job/2"
    ])

    await run_context.add_context_data("input_file_paths", {
        "master_resume": "data/inputs/resume.tex",
        "resume_guidelines": "data/inputs/resume_guide.md",
        "cover_letter_guidelines": "data/inputs/cl_guide.md",
        "company_culture": "data/inputs/culture.md"
    })

    # Create agent pool
    agent_pool = AgentPool(pool_size=config.agent_pool_size)

    # Run orchestration
    orchestra = TailoringOrchestra(run_context, agent_pool)
    results = await orchestra.run()

    return results

# Run custom workflow
results = asyncio.run(custom_tailoring())
```

### Using Individual Orchestrators

```python
import asyncio
from pathlib import Path
from src.config import Config
from src.state.run_context import RunContext
from src.agents.agent_pool import AgentPool
from src.orchestrators import (
    InputPreparationOrchestra,
    JDMatchingOrchestra,
    ResumeWritingPolishingOrchestra
)

async def run_single_stage():
    # Setup
    config = Config()
    run_context = await RunContext.create(config)
    agent_pool = AgentPool(pool_size=5)

    # Populate inputs
    await run_context.add_context_data("job_urls", [
        "https://example.com/job/123"
    ])

    # Run only input preparation
    input_prep = InputPreparationOrchestra(run_context, agent_pool)
    prep_results = await input_prep.run()

    print(f"Loaded {len(prep_results['job_descriptions'])} JDs")

    # Run only JD matching
    jd_matching = JDMatchingOrchestra(run_context, agent_pool)
    match_results = await jd_matching.run()

    print(f"Selected {len(match_results['selected_jds'])} JDs")

    return match_results

results = asyncio.run(run_single_stage())
```

## Example Output

### Successful Run

```
================================================================================
TAILORING COMPLETE!
================================================================================

✓ Status: SUCCESS
  JDs Processed: 2

📦 Release Artifacts:

  job-senior-software-engineer:
    📄 Resume:       data/runs/run-123abc/release/job-senior-software-engineer_resume.pdf
    📄 Cover Letter: data/runs/run-123abc/release/job-senior-software-engineer_cover_letter.pdf

  job-backend-developer:
    📄 Resume:       data/runs/run-123abc/release/job-backend-developer_resume.pdf
    📄 Cover Letter: data/runs/run-123abc/release/job-backend-developer_cover_letter.pdf

📁 Run Directory: data/runs/run-123abc
📋 Log File: data/runs/run-123abc/logs/run-123abc.log

================================================================================
```

### Partial Success (Some JDs Failed)

```
================================================================================
TAILORING COMPLETE!
================================================================================

⚠ Status: PARTIAL
  JDs Processed: 1
  JDs Failed: 1

📦 Release Artifacts:

  job-senior-software-engineer:
    📄 Resume:       data/runs/run-123abc/release/job-senior-software-engineer_resume.pdf
    📄 Cover Letter: data/runs/run-123abc/release/job-senior-software-engineer_cover_letter.pdf

❌ Failed JDs:
    - job-backend-developer

📁 Run Directory: data/runs/run-123abc
📋 Log File: data/runs/run-123abc/logs/run-123abc.log

================================================================================
```

### Error

```
================================================================================
TAILORING COMPLETE!
================================================================================

❌ ERROR: File not found: data/inputs/master_resume.tex

📁 Run Directory: data/runs/run-123abc
📋 Log File: data/runs/run-123abc/logs/run-123abc.log

================================================================================
```

## Output Directory Structure

After a successful run, you'll find:

```
data/
└── runs/
    └── run-123abc/
        ├── logs/
        │   └── run-123abc.log                    # Detailed execution log
        ├── checkpoints/
        │   ├── initialization.json               # Initial state
        │   ├── input_preparation.json            # After input prep
        │   ├── jd_matching.json                  # After JD matching
        │   └── completed.json                    # Final state
        ├── inputs/
        │   └── job_descriptions/
        │       ├── job-123.json                  # Fetched JD
        │       └── job-456.json
        ├── drafts/
        │   ├── resumes/
        │   │   ├── job-123_resume_draft_v1.tex
        │   │   ├── job-123_resume_draft_v2.tex
        │   │   └── job-123_resume_final.tex
        │   └── cover_letters/
        │       ├── job-123_cl_draft_v1.tex
        │       ├── job-123_cl_draft_v2.tex
        │       └── job-123_cl_final.tex
        └── release/
            ├── job-123_resume.pdf                # ✓ Final resume
            ├── job-123_cover_letter.pdf          # ✓ Final cover letter
            ├── job-456_resume.pdf
            └── job-456_cover_letter.pdf
```

## Tips and Best Practices

### 1. File Organization

Keep your input files organized:

```
data/
├── inputs/
│   ├── master_resume.tex
│   ├── resume_best_practices.md
│   ├── cover_letter_best_practices.md
│   └── company_culture.md
└── templates/
    ├── resume_template.tex
    └── cover_letter_template.tex
```

### 2. Concurrency Configuration

**For speed** (high-end machine with good API limits):
```
Agent Pool Size: 10 or unlimited (0)
```

**For stability** (limited API rate limits):
```
Agent Pool Size: 3
```

**For debugging** (sequential execution):
```
Agent Pool Size: 1
```

### 3. Quality Thresholds

**Strict quality** (more iterations):
```
Quality Threshold: 0.9
Max Iterations: 15
```

**Balanced** (recommended):
```
Quality Threshold: 0.8
Max Iterations: 10
```

**Fast turnaround** (fewer iterations):
```
Quality Threshold: 0.7
Max Iterations: 5
```

### 4. Cancellation

If you need to cancel during execution:
1. Press `Ctrl+C` once (graceful shutdown)
2. Wait for current agents to finish
3. Check `data/runs/run-{id}/checkpoints/` for partial results

### 5. Recovery

If a run fails partway through:
1. Note the run ID from the error message
2. Check logs: `data/runs/run-{id}/logs/run-{id}.log`
3. Review checkpoints: `data/runs/run-{id}/checkpoints/`
4. Contact support for recovery assistance (feature in development)

## Environment Variables

Set these before running:

```bash
# Required
export ANTHROPIC_API_KEY="your-api-key"

# Optional
export LOG_LEVEL="DEBUG"  # For detailed logging
```

## Common Scenarios

### Scenario 1: Single Job Application

```bash
/tailor
# Enter 1 job URL
# Use default settings
# Get 1 resume + 1 cover letter
```

### Scenario 2: Batch Applications

```bash
/tailor
# Enter 10 job URLs
# Set Agent Pool Size: 5 (process 5 in parallel)
# Get 10 resumes + 10 cover letters
```

### Scenario 3: High-Quality Output

```bash
/tailor
# Enter job URLs
# Set Max Iterations: 20
# Set Quality Threshold: 0.95
# Set AI Detection Threshold: 0.9995
# Thorough refinement with multiple rounds
```

### Scenario 4: Quick Draft

```bash
/tailor
# Enter job URLs
# Set Max Iterations: 3
# Set Quality Threshold: 0.6
# Fast turnaround with minimal refinement
```
