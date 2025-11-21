# Configuration Guide

This document describes all configuration options for the ATS research and resume tailoring orchestration system.

## Table of Contents

1. [Configuration Files](#configuration-files)
2. [Core Configuration](#core-configuration)
3. [Agent Configuration](#agent-configuration)
4. [LLM Provider Configuration](#llm-provider-configuration)
5. [Environment Variables](#environment-variables)
6. [Default Values](#default-values)
7. [Customization Examples](#customization-examples)
8. [Performance Tuning](#performance-tuning)

## Configuration Files

The system uses a hierarchical configuration system:

```
src/
├── config.py                    # Main configuration module
├── config/
│   ├── default_config.yaml     # Default system settings
│   ├── agents.yaml             # Agent-specific settings
│   └── llm_providers.yaml      # LLM provider settings
└── .env                        # Environment variables (not in git)
```

### Configuration Loading Priority

1. **Environment variables** (highest priority)
2. **User config file** (`~/.ats-research/config.yaml`)
3. **Project config file** (`./config/user_config.yaml`)
4. **Default config** (`./config/default_config.yaml`)

## Core Configuration

### Main Configuration Parameters

Located in `config/default_config.yaml`:

```yaml
# System-wide settings
system:
  version: "1.0.0"
  debug_mode: false
  log_level: "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
  log_file: "logs/ats-research.log"

  # State management
  state_dir: "data/states"
  auto_save_state: true
  state_retention_days: 30

# Workflow settings
workflow:
  # Default workflow stages (can be selectively disabled)
  enabled_stages:
    - company_research
    - master_resume_load
    - best_practices_research
    - tailoring
    - input_preparation
    - jd_matching
    - writing
    - fact_checking
    - pruning

  # Automatic vs. interactive mode
  interactive_mode: true
  auto_approve_decisions: false

  # Performance
  max_parallel_agents: 3
  timeout_seconds: 300

# Document settings
documents:
  master_resume_path: "data/master_resume.md"
  resume_best_practices_path: "data/resume_best_practices.md"
  cover_letter_best_practices_path: "data/cover_letter_best_practices.md"

  # Output settings
  output_dir: "data/output"
  output_format: "markdown"  # markdown, docx, pdf

  # Length targets
  resume_max_pages: 2
  cover_letter_max_words: 400

  # Quality settings
  min_match_score: 30  # Minimum score to include experience
  fact_check_strictness: "standard"  # strict, standard, lenient

# Research settings
research:
  company_research_depth: "standard"  # quick, standard, deep
  cache_research_results: true
  cache_ttl_days: 7

  # Sources for best practices research
  best_practices_sources:
    - "top20.md"
    - "external/ats_guides/*.md"
```

### Configuration Class Reference

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `system.debug_mode` | bool | `false` | Enable verbose debugging output |
| `system.log_level` | str | `"INFO"` | Logging level (DEBUG/INFO/WARNING/ERROR/CRITICAL) |
| `system.log_file` | str | `"logs/ats-research.log"` | Path to log file |
| `workflow.interactive_mode` | bool | `true` | Prompt user at decision points |
| `workflow.auto_approve_decisions` | bool | `false` | Auto-approve all decisions (non-interactive) |
| `workflow.max_parallel_agents` | int | `3` | Max concurrent agent executions |
| `workflow.timeout_seconds` | int | `300` | Agent timeout in seconds |
| `documents.resume_max_pages` | int | `2` | Target resume page count |
| `documents.cover_letter_max_words` | int | `400` | Target cover letter word count |
| `documents.min_match_score` | int | `30` | Minimum match score to include experience |
| `documents.fact_check_strictness` | str | `"standard"` | Fact checking strictness level |
| `research.company_research_depth` | str | `"standard"` | Research depth (quick/standard/deep) |
| `research.cache_research_results` | bool | `true` | Cache research results |
| `research.cache_ttl_days` | int | `7` | Cache time-to-live in days |

## Agent Configuration

Agent-specific settings in `config/agents.yaml`:

```yaml
# Company Research Agent
company_research:
  enabled: true
  timeout: 120
  max_sources: 5
  required_sections:
    - company_overview
    - culture_values
    - work_environment
    - candidate_values

  # Web scraping settings
  scraping:
    enabled: true
    max_depth: 2
    user_agent: "ATS-Research-Bot/1.0"
    respect_robots_txt: true

# JD Parser Agent
jd_parser:
  enabled: true
  timeout: 60

  # Section identification
  section_keywords:
    responsibilities: ["responsibilities", "duties", "you will", "what you'll do"]
    required_skills: ["required", "must have", "requirements", "qualifications"]
    preferred_skills: ["preferred", "nice to have", "bonus", "plus"]
    benefits: ["benefits", "perks", "we offer"]

  # Keyword extraction
  keyword_extraction:
    method: "tfidf"  # tfidf, rake, hybrid
    min_keyword_length: 3
    max_keywords: 50

# Requirement Matcher Agent
requirement_matcher:
  enabled: true
  timeout: 90

  # Scoring weights
  scoring:
    keyword_match_weight: 0.40
    skill_overlap_weight: 0.30
    achievement_relevance_weight: 0.20
    recency_weight: 0.10

  # Thresholds
  thresholds:
    strong_match: 70
    moderate_match: 50
    weak_match: 30

# Resume Tailoring Agent
resume_tailoring:
  enabled: true
  timeout: 120
  llm_provider: "claude"  # claude, gpt, gemini

  # Tailoring strategy
  aggressiveness: "moderate"  # conservative, moderate, aggressive
  preserve_voice: true
  max_keyword_density: 0.05  # Max 5% keyword density

  # Content prioritization
  prioritization:
    by_match_score: 0.60
    by_recency: 0.30
    by_achievement_impact: 0.10

# Cover Letter Writer Agent
cover_letter_writer:
  enabled: true
  timeout: 120
  llm_provider: "claude"

  # Writing style
  tone: "professional"  # professional, enthusiastic, formal
  personalization_level: "high"  # low, medium, high

  # Structure
  paragraph_count: 3  # Opening, body(s), closing
  include_company_research: true
  include_specific_examples: true

  # Length control
  min_words: 250
  max_words: 400
  target_words: 350

# Fact Checker Agent
fact_checker:
  enabled: true
  timeout: 60

  # Validation rules
  rules:
    check_dates: true
    check_metrics: true
    check_titles: true
    check_skills: true
    allow_rounding: true  # Allow conservative metric rounding
    rounding_threshold: 0.10  # Max 10% variance

  # Action on failure
  on_failure: "warn"  # error, warn, ignore

# Pruning Agent
pruning:
  enabled: true
  timeout: 60

  # Pruning strategy
  strategy: "score_based"  # score_based, recency_based, balanced
  preserve_top_n: 5  # Always keep top N experiences

  # Pruning thresholds
  min_score_to_keep: 40
  min_bullets_per_job: 2
  max_bullets_per_job: 5
```

## LLM Provider Configuration

Located in `config/llm_providers.yaml`:

```yaml
# Claude (Anthropic)
claude:
  enabled: true
  api_key_env: "ANTHROPIC_API_KEY"

  models:
    default: "claude-3-5-sonnet-20241022"
    fast: "claude-3-haiku-20240307"
    advanced: "claude-3-opus-20240229"

  # API settings
  max_tokens: 4096
  temperature: 0.7
  top_p: 0.9

  # Rate limiting
  requests_per_minute: 50
  retry_attempts: 3
  retry_delay: 2

# GPT (OpenAI)
gpt:
  enabled: true
  api_key_env: "OPENAI_API_KEY"

  models:
    default: "gpt-4-turbo-preview"
    fast: "gpt-3.5-turbo"
    advanced: "gpt-4"

  max_tokens: 4096
  temperature: 0.7

  requests_per_minute: 60
  retry_attempts: 3
  retry_delay: 2

# Gemini (Google)
gemini:
  enabled: false
  api_key_env: "GOOGLE_API_KEY"

  models:
    default: "gemini-pro"

  max_tokens: 4096
  temperature: 0.7

  requests_per_minute: 60
  retry_attempts: 3
  retry_delay: 2

# Model selection strategy
model_selection:
  # Agent-specific model preferences
  company_research: "fast"
  jd_parser: "fast"
  requirement_matcher: "default"
  resume_tailoring: "advanced"
  cover_letter_writer: "advanced"
  fact_checker: "default"
  pruning: "fast"
```

## Environment Variables

Create a `.env` file in the project root (this file is gitignored):

```bash
# LLM API Keys
ANTHROPIC_API_KEY=your_anthropic_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
GOOGLE_API_KEY=your_google_api_key_here

# Optional: Override config file location
ATS_CONFIG_FILE=/path/to/custom/config.yaml

# Optional: Override master resume location
MASTER_RESUME_PATH=/path/to/master_resume.md

# Optional: Debug settings
DEBUG=false
LOG_LEVEL=INFO

# Optional: Output directory
OUTPUT_DIR=./data/output
```

### Environment Variable Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | Yes* | - | Claude API key |
| `OPENAI_API_KEY` | Yes* | - | OpenAI API key |
| `GOOGLE_API_KEY` | No | - | Google Gemini API key |
| `ATS_CONFIG_FILE` | No | `config/default_config.yaml` | Custom config file path |
| `MASTER_RESUME_PATH` | No | `data/master_resume.md` | Master resume location |
| `DEBUG` | No | `false` | Enable debug mode |
| `LOG_LEVEL` | No | `INFO` | Logging level |
| `OUTPUT_DIR` | No | `data/output` | Output directory |

*At least one LLM provider API key is required

## Default Values

### Complete Default Configuration

```python
# src/config.py

DEFAULT_CONFIG = {
    "system": {
        "version": "1.0.0",
        "debug_mode": False,
        "log_level": "INFO",
        "log_file": "logs/ats-research.log",
        "state_dir": "data/states",
        "auto_save_state": True,
        "state_retention_days": 30,
    },
    "workflow": {
        "enabled_stages": [
            "company_research",
            "master_resume_load",
            "best_practices_research",
            "tailoring",
            "input_preparation",
            "jd_matching",
            "writing",
            "fact_checking",
            "pruning",
        ],
        "interactive_mode": True,
        "auto_approve_decisions": False,
        "max_parallel_agents": 3,
        "timeout_seconds": 300,
    },
    "documents": {
        "master_resume_path": "data/master_resume.md",
        "resume_best_practices_path": "data/resume_best_practices.md",
        "cover_letter_best_practices_path": "data/cover_letter_best_practices.md",
        "output_dir": "data/output",
        "output_format": "markdown",
        "resume_max_pages": 2,
        "cover_letter_max_words": 400,
        "min_match_score": 30,
        "fact_check_strictness": "standard",
    },
    "research": {
        "company_research_depth": "standard",
        "cache_research_results": True,
        "cache_ttl_days": 7,
        "best_practices_sources": ["top20.md", "external/ats_guides/*.md"],
    },
}
```

## Customization Examples

### Example 1: Fast, Non-Interactive Mode

```yaml
# config/fast_mode.yaml
workflow:
  interactive_mode: false
  auto_approve_decisions: true
  max_parallel_agents: 5

research:
  company_research_depth: "quick"
  cache_research_results: true

# Use fast models for all agents
llm_providers:
  claude:
    models:
      default: "claude-3-haiku-20240307"
```

**Usage**:
```bash
python src/main.py --config config/fast_mode.yaml --jd job.html
```

### Example 2: High-Quality, Deep Research Mode

```yaml
# config/deep_research.yaml
workflow:
  interactive_mode: true
  timeout_seconds: 600  # 10 minutes per agent

research:
  company_research_depth: "deep"

agents:
  requirement_matcher:
    thresholds:
      strong_match: 80  # Stricter matching
      moderate_match: 60
      weak_match: 40

  resume_tailoring:
    aggressiveness: "aggressive"
    llm_provider: "claude"

  cover_letter_writer:
    llm_provider: "claude"
    personalization_level: "high"

llm_providers:
  claude:
    models:
      default: "claude-3-opus-20240229"  # Most advanced model
```

### Example 3: Conservative, Fact-Focused Mode

```yaml
# config/conservative.yaml
agents:
  resume_tailoring:
    aggressiveness: "conservative"
    preserve_voice: true

  fact_checker:
    rules:
      allow_rounding: false
      check_dates: true
      check_metrics: true
      check_titles: true
      check_skills: true
    on_failure: "error"  # Strict enforcement

documents:
  fact_check_strictness: "strict"
  min_match_score: 50  # Higher threshold
```

### Example 4: Custom Agent Selection

```yaml
# config/custom_agents.yaml
workflow:
  enabled_stages:
    - master_resume_load
    - input_preparation
    - jd_matching
    - writing
    # Skip company research, best practices, fact checking, pruning

agents:
  company_research:
    enabled: false
  fact_checker:
    enabled: false
  pruning:
    enabled: false
```

## Performance Tuning

### For Faster Processing

1. **Use Fast Models**:
   ```yaml
   llm_providers:
     claude:
       models:
         default: "claude-3-haiku-20240307"
   ```

2. **Increase Parallelism**:
   ```yaml
   workflow:
     max_parallel_agents: 5
   ```

3. **Reduce Research Depth**:
   ```yaml
   research:
     company_research_depth: "quick"
   ```

4. **Enable Caching**:
   ```yaml
   research:
     cache_research_results: true
     cache_ttl_days: 30
   ```

5. **Skip Optional Stages**:
   ```yaml
   workflow:
     enabled_stages:
       - jd_matching
       - writing
       # Skip research and validation
   ```

### For Higher Quality

1. **Use Advanced Models**:
   ```yaml
   llm_providers:
     claude:
       models:
         default: "claude-3-opus-20240229"
   ```

2. **Enable All Validation**:
   ```yaml
   agents:
     fact_checker:
       enabled: true
       on_failure: "error"
   ```

3. **Deep Research**:
   ```yaml
   research:
     company_research_depth: "deep"
   ```

4. **Longer Timeouts**:
   ```yaml
   workflow:
     timeout_seconds: 600
   ```

### For Cost Optimization

1. **Strategic Model Selection**:
   ```yaml
   model_selection:
     company_research: "fast"
     jd_parser: "fast"
     requirement_matcher: "default"
     resume_tailoring: "advanced"  # Only use expensive model where it matters
     cover_letter_writer: "advanced"
     fact_checker: "default"
     pruning: "fast"
   ```

2. **Aggressive Caching**:
   ```yaml
   research:
     cache_research_results: true
     cache_ttl_days: 90
   ```

3. **Reduce Parallel Execution** (reduces simultaneous API calls):
   ```yaml
   workflow:
     max_parallel_agents: 1
   ```

## Loading Custom Configuration

### From File

```python
from src.config import Config

# Load custom config
config = Config.from_file("config/my_config.yaml")
orchestrator = MainOrchestrator(config)
```

### From Dictionary

```python
custom_config = {
    "workflow": {
        "interactive_mode": False
    },
    "research": {
        "company_research_depth": "quick"
    }
}

config = Config.from_dict(custom_config)
```

### Programmatic Override

```python
config = Config.load_default()
config.workflow.interactive_mode = False
config.research.company_research_depth = "deep"
config.save("config/runtime_config.yaml")
```

## Next Steps

- See [Architecture Guide](architecture.md) for component details
- Review [Usage Guide](usage.md) for practical configuration examples
- Check [Development Guide](development.md) for extending configuration options
