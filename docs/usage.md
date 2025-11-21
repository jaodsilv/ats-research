# Usage Guide

This guide provides practical examples and tutorials for using the ATS research and resume tailoring orchestration system.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Interactive Wizard Walkthrough](#interactive-wizard-walkthrough)
3. [Command-Line Usage](#command-line-usage)
4. [Slash Command Usage](#slash-command-usage)
5. [Programmatic Usage](#programmatic-usage)
6. [Interpreting Results](#interpreting-results)
7. [Troubleshooting](#troubleshooting)
8. [Best Practices](#best-practices)

## Getting Started

### Prerequisites

1. **Python Installation**: Python 3.8 or higher
2. **API Keys**: At least one LLM provider API key (Claude or GPT recommended)
3. **Master Resume**: Your complete resume in markdown format

### Initial Setup

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/ats-research.git
cd ats-research

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create .env file with your API keys
cat > .env << EOF
ANTHROPIC_API_KEY=your_api_key_here
OPENAI_API_KEY=your_openai_key_here
EOF

# 4. Create your master resume
cp data/test/sample_master_resume.md data/master_resume.md
# Edit data/master_resume.md with your actual experience

# 5. Test the installation
python src/main.py --help
```

### Quick Start Tutorial

Let's tailor a resume for a sample job posting:

```bash
# Use the test fixtures for a quick demo
python src/main.py \
  --jd data/test/sample_jd.html \
  --master-resume data/test/sample_master_resume.md \
  --output-dir data/output/demo
```

This will:
1. Parse the job description
2. Match your experience to requirements
3. Generate a tailored resume
4. Create a cover letter
5. Validate accuracy
6. Save outputs to `data/output/demo/`

## Interactive Wizard Walkthrough

The interactive wizard guides you through the entire process step-by-step.

### Starting the Wizard

```bash
python src/main.py
```

### Step 1: Job Information

```
ATS Resume Tailoring System
============================

Welcome! This wizard will help you create a tailored resume and cover letter.

Step 1: Job Information
-----------------------

How would you like to provide the job description?
  1. Paste URL to job posting
  2. Load from HTML file
  3. Paste job description text

Your choice [1-3]: 1

Enter job posting URL: https://techcorp.com/careers/senior-backend-engineer

Fetching job description... ✓

Company detected: TechCorp
Position: Senior Backend Engineer
Location: San Francisco, CA
```

### Step 2: Company Research

```
Step 2: Company Research
------------------------

How much company research would you like to perform?
  1. Quick - Use job posting info only (~2 min)
  2. Standard - Basic web research (~5 min) [Recommended]
  3. Deep - Comprehensive research (~15 min)
  4. Skip - No additional research

Your choice [1-4]: 2

Researching TechCorp...
  ✓ Fetching company website
  ✓ Analyzing culture and values
  ✓ Extracting candidate preferences

Company Research Summary:
  - Founded: 2015
  - Size: 500+ employees
  - Industry: SaaS - Workflow Automation
  - Culture: Innovation-first, collaborative, remote-friendly
```

### Step 3: Master Resume Selection

```
Step 3: Master Resume
---------------------

Which master resume should we use?
  1. Default (data/master_resume.md) [Recommended]
  2. Backend-focused (data/master_resume_backend.md)
  3. Custom path

Your choice [1-3]: 1

Loading master resume... ✓

Resume Summary:
  - Name: John Doe
  - Experience: 8 years
  - Positions: 2
  - Skills: 25
  - Education: Bachelor's in Computer Science
```

### Step 4: Requirements Matching

```
Step 4: Job Requirements Analysis
----------------------------------

Analyzing job requirements...
  ✓ Extracting required skills
  ✓ Identifying preferred qualifications
  ✓ Parsing responsibilities

Matching your experience to requirements...

Match Analysis:
  Strong Matches (70-100%): 8 requirements
  Moderate Matches (50-69%): 4 requirements
  Weak Matches (30-49%): 2 requirements
  Gaps: 1 requirement

Top Matched Experiences:
  1. Microservices development at Tech Corp (95% match)
  2. API development at StartupXYZ (88% match)
  3. Cloud architecture at Tech Corp (85% match)

Skill Gaps:
  - Kafka/RabbitMQ (preferred but not required)

Continue with these matches? [Y/n]: Y
```

### Step 5: Tailoring Strategy

```
Step 5: Tailoring Strategy
--------------------------

How aggressive should the resume tailoring be?
  1. Conservative - Reorder and emphasize only (safer, authentic)
  2. Moderate - Reword for keywords (balanced) [Recommended]
  3. Aggressive - Rewrite to match JD language (ATS-optimized, less authentic)

Your choice [1-3]: 2

Tailoring Configuration:
  - Strategy: Moderate keyword optimization
  - Preserve voice: Yes
  - Max keyword density: 5%
  - Target length: 2 pages
```

### Step 6: Document Generation

```
Step 6: Document Generation
---------------------------

Generating tailored resume...
  ✓ Prioritizing relevant experiences
  ✓ Optimizing keywords
  ✓ Formatting for ATS compatibility

Generating cover letter...
  ✓ Incorporating company research
  ✓ Highlighting top matches
  ✓ Personalizing tone

Documents Generated:
  Resume: 475 words, 2 pages
  Cover Letter: 342 words
```

### Step 7: Quality Validation

```
Step 7: Quality Validation
--------------------------

Fact-checking tailored documents...
  ✓ Verifying employment dates
  ✓ Checking achievement metrics
  ✓ Validating skills claimed

Fact Check Results: PASSED
  ✓ All dates accurate
  ✓ All metrics verified
  ✓ No fabricated claims
  ⚠ 1 metric conservatively rounded (10% → 15%)

Length Check:
  Resume: 2.0 pages ✓
  Cover Letter: 342 words ✓

Documents meet quality standards!
```

### Step 8: Output

```
Step 8: Save Results
--------------------

Where should we save the results?
  Default: data/output/techcorp-senior-backend-engineer/

Output directory [or press Enter for default]:

Saving results...
  ✓ tailored_resume.md
  ✓ cover_letter.md
  ✓ match_analysis.json
  ✓ workflow_state.json

Success! Your tailored application materials are ready.

Output location: D:\src\ats-research\data\output\techcorp-senior-backend-engineer\

Next steps:
  1. Review the tailored resume and cover letter
  2. Convert to PDF using your preferred tool
  3. Submit your application!

View match analysis for insights on your application strength.
```

## Command-Line Usage

For power users, the CLI supports direct execution without the wizard.

### Basic Command Structure

```bash
python src/main.py [OPTIONS]
```

### Common Options

| Option | Short | Description | Example |
|--------|-------|-------------|---------|
| `--jd` | `-j` | Job description file path | `--jd job.html` |
| `--jd-url` | `-u` | Job posting URL | `--jd-url https://...` |
| `--master-resume` | `-m` | Master resume path | `--master-resume data/resume.md` |
| `--output-dir` | `-o` | Output directory | `--output-dir data/output/job1` |
| `--config` | `-c` | Custom config file | `--config config/fast.yaml` |
| `--no-interactive` | `-n` | Non-interactive mode | `--no-interactive` |
| `--research-depth` | `-r` | Research depth | `--research-depth deep` |
| `--skip-company-research` | | Skip company research | `--skip-company-research` |
| `--skip-fact-check` | | Skip fact checking | `--skip-fact-check` |
| `--skip-pruning` | | Skip content pruning | `--skip-pruning` |
| `--verbose` | `-v` | Verbose output | `--verbose` |
| `--help` | `-h` | Show help | `--help` |

### Example Commands

#### Basic Usage with URL

```bash
python src/main.py \
  --jd-url "https://company.com/careers/job123" \
  --output-dir data/output/company-job123
```

#### Fast Mode (Non-Interactive)

```bash
python src/main.py \
  --jd job_description.html \
  --no-interactive \
  --research-depth quick \
  --output-dir data/output/quick-application
```

#### High-Quality Mode

```bash
python src/main.py \
  --jd job.html \
  --research-depth deep \
  --config config/deep_research.yaml \
  --output-dir data/output/important-application
```

#### Resume-Only (Skip Cover Letter)

```bash
python src/main.py \
  --jd job.html \
  --skip-cover-letter \
  --output-dir data/output/resume-only
```

#### Using Custom Master Resume

```bash
python src/main.py \
  --jd job.html \
  --master-resume data/backend_focused_resume.md \
  --output-dir data/output/backend-role
```

#### Batch Processing Multiple Jobs

```bash
# Process multiple job descriptions
for jd in data/jobs/*.html; do
  job_name=$(basename "$jd" .html)
  python src/main.py \
    --jd "$jd" \
    --no-interactive \
    --output-dir "data/output/$job_name"
done
```

## Slash Command Usage

When using the system within Claude Code, you can use custom slash commands.

### Available Commands

#### `/docs:download`

Download documentation from a URL for research:

```
/docs:download url: https://company.com/engineering-blog output-path: data/research/company
```

**Parameters**:
- `url`: URL to download (required)
- `output-path`: Destination folder (required)
- `filename`: Custom filename (optional)
- `file-existing-mode`: What to do if file exists - `overwrite`, `skip`, `rename` (optional)

#### `/tailor-resume`

Quick resume tailoring command:

```
/tailor-resume jd: data/jobs/job1.html output: data/output/job1
```

**Parameters**:
- `jd`: Job description file path or URL (required)
- `output`: Output directory (required)
- `research-depth`: `quick`, `standard`, or `deep` (optional, default: standard)
- `interactive`: `true` or `false` (optional, default: true)

#### `/analyze-match`

Analyze match quality without generating documents:

```
/analyze-match jd: data/jobs/job1.html
```

**Output**: JSON match analysis with scores and recommendations

## Programmatic Usage

For integration into other tools or custom workflows:

### Python API

```python
from src.orchestrator import MainOrchestrator
from src.config import Config

# Load configuration
config = Config.from_file("config/default_config.yaml")

# Initialize orchestrator
orchestrator = MainOrchestrator(config)

# Load job description
jd_data = orchestrator.load_job_description(
    jd_path="data/jobs/job1.html"
)

# Run company research
company_data = orchestrator.run_company_research(
    company_name=jd_data["company_name"],
    depth="standard"
)

# Load master resume
master_resume = orchestrator.load_master_resume(
    path="data/master_resume.md"
)

# Match requirements
match_results = orchestrator.match_requirements(
    master_resume=master_resume,
    jd_data=jd_data,
    company_data=company_data
)

# Generate tailored resume
tailored_resume = orchestrator.tailor_resume(
    master_resume=master_resume,
    match_results=match_results,
    aggressiveness="moderate"
)

# Generate cover letter
cover_letter = orchestrator.write_cover_letter(
    company_data=company_data,
    jd_data=jd_data,
    match_results=match_results
)

# Validate
validation = orchestrator.fact_check(
    master_resume=master_resume,
    tailored_resume=tailored_resume,
    cover_letter=cover_letter
)

# Save results
orchestrator.save_results(
    output_dir="data/output/job1",
    resume=tailored_resume,
    cover_letter=cover_letter,
    match_analysis=match_results,
    validation=validation
)
```

### Custom Agent Usage

```python
from src.agents.jd_parser import JDParserAgent
from src.agents.requirement_matcher import RequirementMatcherAgent

# Initialize agents
jd_parser = JDParserAgent(config)
matcher = RequirementMatcherAgent(config)

# Parse JD
with open("data/jobs/job1.html", "r") as f:
    jd_html = f.read()

parsed_jd = jd_parser.parse(jd_html)

# Match requirements
match_results = matcher.match(
    master_resume=master_resume_data,
    job_requirements=parsed_jd
)

# Access results
print(f"Strong matches: {len(match_results['strong_matches'])}")
print(f"Skill gaps: {match_results['skill_gaps']}")
```

## Interpreting Results

### Output Files

After running the orchestrator, you'll find the following files in your output directory:

```
data/output/techcorp-senior-backend/
├── tailored_resume.md          # Tailored resume in markdown
├── cover_letter.md             # Cover letter in markdown
├── match_analysis.json         # Detailed match analysis
├── workflow_state.json         # Complete workflow state
├── company_research.md         # Company research notes
└── logs/                       # Detailed execution logs
```

### Match Analysis Structure

The `match_analysis.json` file contains:

```json
{
  "overall_match_score": 78,
  "match_grade": "Strong",
  "strong_matches": [
    {
      "requirement": "5+ years backend development",
      "matching_experience": "8 years at Tech Corp and StartupXYZ",
      "score": 95,
      "evidence": "Senior Software Engineer role with microservices..."
    }
  ],
  "moderate_matches": [...],
  "weak_matches": [...],
  "skill_gaps": [
    {
      "skill": "Kafka",
      "type": "preferred",
      "transferable_skills": ["RabbitMQ experience mentioned"]
    }
  ],
  "recommendations": [
    "Emphasize microservices architecture experience",
    "Highlight cloud migration project",
    "Mention willingness to learn Kafka"
  ]
}
```

### Match Score Interpretation

| Score Range | Grade | Interpretation | Action |
|-------------|-------|----------------|--------|
| 90-100 | Excellent | Perfect match, highly qualified | Apply with confidence |
| 75-89 | Strong | Good match, well-qualified | Apply, emphasize strengths |
| 60-74 | Moderate | Decent match with some gaps | Apply, address gaps in cover letter |
| 45-59 | Weak | Significant gaps | Consider if you can bridge gaps |
| 0-44 | Poor | Not a good fit | Reconsider application |

### Resume Quality Indicators

Check these quality metrics in the validation output:

1. **ATS Compatibility**:
   - ✓ Standard section headings
   - ✓ No tables or graphics
   - ✓ Keyword density 3-5%

2. **Content Quality**:
   - ✓ Quantified achievements
   - ✓ Action verbs
   - ✓ Results-focused

3. **Accuracy**:
   - ✓ Dates match master resume
   - ✓ Metrics verified
   - ✓ No fabrications

4. **Length**:
   - ✓ Resume: 1-2 pages
   - ✓ Cover letter: 250-400 words

## Troubleshooting

### Common Issues

#### Issue: "API key not found"

**Symptoms**: Error message about missing API key

**Solution**:
```bash
# Check .env file exists
ls -la .env

# Verify API key is set
cat .env | grep ANTHROPIC_API_KEY

# Make sure .env is in the project root
# Restart the application after setting the key
```

#### Issue: "Master resume not found"

**Symptoms**: FileNotFoundError for master resume

**Solution**:
```bash
# Check file exists
ls -la data/master_resume.md

# Or specify custom path
python src/main.py --master-resume /path/to/your/resume.md
```

#### Issue: "JD parsing failed"

**Symptoms**: Unable to extract requirements from job description

**Solution**:
1. Check if HTML file is valid: `file data/jobs/job.html`
2. Try converting to plain text first
3. Use `--verbose` to see parsing details
4. Check if job description has standard sections

#### Issue: "Low match scores across the board"

**Symptoms**: All experiences show match scores < 30%

**Possible causes**:
1. Wrong master resume for this role (e.g., frontend resume for backend job)
2. JD parsing extracted wrong requirements
3. Missing keywords in master resume

**Solution**:
```bash
# Review match analysis
cat data/output/job/match_analysis.json

# Try with different master resume
python src/main.py --master-resume data/specialized_resume.md

# Manually review parsed requirements
cat data/output/job/workflow_state.json | jq '.parsed_jd'
```

#### Issue: "Fact check failures"

**Symptoms**: Validation finds discrepancies

**Solution**:
1. Review specific failures in validation output
2. Check if master resume has accurate data
3. If failures are due to rounding, adjust strictness:
   ```yaml
   # config/custom.yaml
   agents:
     fact_checker:
       rules:
         allow_rounding: true
         rounding_threshold: 0.15  # Allow 15% variance
   ```

#### Issue: "Timeout errors"

**Symptoms**: Agent execution times out

**Solution**:
```yaml
# Increase timeout in config
workflow:
  timeout_seconds: 600  # 10 minutes

# Or use faster models
llm_providers:
  claude:
    models:
      default: "claude-3-haiku-20240307"
```

### Debug Mode

Enable detailed logging for troubleshooting:

```bash
python src/main.py --verbose --jd job.html 2>&1 | tee debug.log
```

Or in config:
```yaml
system:
  debug_mode: true
  log_level: "DEBUG"
```

### Getting Help

1. Check logs: `cat logs/ats-research.log`
2. Review workflow state: `cat data/output/job/workflow_state.json`
3. Enable debug mode and re-run
4. Open an issue on GitHub with logs

## Best Practices

### 1. Maintain Your Master Resume

- Update master resume after each new achievement
- Include metrics for all accomplishments
- Keep detailed notes even if you prune later
- Use consistent formatting

### 2. Customize Per Application Type

Create role-specific master resumes:

```bash
data/
├── master_resume.md              # Complete resume
├── master_resume_backend.md      # Backend-focused
├── master_resume_frontend.md     # Frontend-focused
└── master_resume_leadership.md   # Leadership roles
```

### 3. Review Generated Content

Always review and edit:
- Generated documents are starting points
- Add personal touches to cover letters
- Verify technical accuracy
- Ensure authentic voice

### 4. Track Your Applications

Keep organized:

```bash
data/output/
├── 2024-01-15-techcorp-backend/
├── 2024-01-16-startup-fullstack/
└── 2024-01-17-bigco-senior/
```

### 5. Iterate and Improve

- Review match scores to understand strengths
- Add missing skills to master resume
- Refine best practices based on feedback
- Track which applications get responses

### 6. Balance ATS and Human Readers

- Don't over-optimize for ATS at expense of readability
- Use "moderate" tailoring aggressiveness by default
- Keep authentic voice and examples
- Remember: ATS gets you past the filter, but humans make decisions

## Next Steps

- Review [Architecture Guide](architecture.md) for system understanding
- Check [Configuration Guide](configuration.md) for customization
- See [Development Guide](development.md) to extend functionality
