# Evaluation Framework

Comprehensive evaluation framework for testing browser automation agents using LLM-as-a-judge with visual verification support.

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Directory Structure](#directory-structure)
- [Running Evaluations](#running-evaluations)
- [YAML Configuration](#yaml-configuration)
- [Judge Types](#judge-types)
- [Visual Verification](#visual-verification)
- [Results and Reports](#results-and-reports)
- [Configuration Reference](#configuration-reference)
- [Troubleshooting](#troubleshooting)

---

## Overview

This framework provides:
- **Universal Runner**: Single `run.py` script for all evaluation types
- **Visual Verification**: VisionJudge with screenshot analysis for UI tests
- **LLM Judge**: Text-based evaluation using GPT models
- **Modular Architecture**: Shared configuration and library code
- **Automatic Reporting**: Timestamped CSV reports with detailed results
- **Screenshot Capture**: Automatic screenshot capture via Chrome DevTools Protocol

---

## Quick Start

### 1. Install Dependencies

```bash
cd evals

# Using uv (recommended)
uv pip install -e .

# Or using pip
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your API keys
# OPENAI_API_KEY=sk-...
```

### 3. Configure Models

Edit `config.yml` to set your model preferences:

```yaml
main_model:
  provider: "openai"
  model_name: "gpt-5-mini"
  api_key: "${OPENAI_API_KEY}"

judge_model:
  provider: "openai"
  model_name: "gpt-5"
  api_key: "${OPENAI_API_KEY}"
```

### 4. Start Evaluation Server

```bash
# From project root
make compose-dev
```

Verify server is running at `http://localhost:8080`

### 5. Run Your First Evaluation

```bash
# Simple math test
python3 run.py --path test-simple/math-001.yaml

# With verbose output
python3 run.py --path test-simple/math-001.yaml --verbose

# UI test with visual verification
python3 run.py --path action-agent/accordion-001.yaml --verbose
```

---

## Directory Structure

```
evals/
├── run.py                    # Universal evaluation runner
├── config.yml                # Global configuration
├── .env                      # API keys and secrets
├── .env.example              # Example environment file
├── requirements.txt          # Python dependencies
├── pyproject.toml            # Project configuration
│
├── data/                     # Evaluation definitions (YAML)
│   ├── test-simple/          # Simple sanity tests
│   ├── action-agent/         # UI interaction tests
│   ├── web-task-agent/       # Multi-step web tasks
│   ├── research-agent/       # Research and information gathering
│   ├── schema-extractor/     # Data extraction tests
│   ├── screenshot-verification/  # Visual verification tests
│   └── end-to-end/           # Complex multi-step scenarios
│
├── lib/                      # Framework library
│   ├── __init__.py           # Library exports
│   ├── config_loader.py      # Configuration management
│   ├── eval_loader.py        # YAML evaluation loader
│   ├── api_client.py         # API client for eval-server
│   └── judge.py              # LLMJudge and VisionJudge
│
├── screenshots/              # Captured screenshots (auto-generated)
└── reports/                  # CSV evaluation reports (auto-generated)
```

---

## Running Evaluations

### Command-Line Interface

The `run.py` script provides three execution modes:

#### 1. Run Specific Evaluation

```bash
python3 run.py --path <path-to-yaml>
```

Examples:
```bash
# Relative to data/ directory
python3 run.py --path test-simple/math-001.yaml
python3 run.py --path action-agent/accordion-001.yaml

# Absolute path also supported
python3 run.py --path /absolute/path/to/eval.yaml
```

#### 2. Run All Evals in a Category

```bash
python3 run.py --category <category-name>
```

Examples:
```bash
python3 run.py --category action-agent
python3 run.py --category test-simple
python3 run.py --category web-task-agent
```

#### 3. Run All Evaluations

```bash
python3 run.py --all
```

### Verbose Mode

Add `--verbose` flag for detailed execution information:

```bash
python3 run.py --path action-agent/accordion-001.yaml --verbose
```

Verbose output includes:
- Input prompt sent to the agent
- Response received from the agent
- Whether VisionJudge is being used
- Judge reasoning and criteria evaluation
- Screenshot paths (if captured)

Example verbose output:
```
  Input: Click to expand the "Section 2" accordion panel
  Response: Done — I expanded "Section 2" for you.
  Using Vision Judge with screenshot
  Judge Reasoning: The AFTER screenshot shows Section 2 highlighted in blue...
  Screenshot: /path/to/screenshots/accordion-001_20251020_170412.png
[1/1] Running: Expand Accordion Section
  ID: accordion-001
  Status: PASS
  Score: 0.80
  Time: 167222ms
```

---

## YAML Configuration

### Basic Structure

Every evaluation YAML file follows this structure:

```yaml
# Unique identifier
id: "example-001"

# Human-readable name
name: "Example Test"

# Description of what this test does
description: "Test description here"

# Enable/disable the test
enabled: true

# Target configuration
target:
  url: "https://example.com"
  wait_for: "networkidle"  # or "domcontentloaded", "load"
  wait_timeout: 5000

# Tool/agent type to use
tool: "action_agent"

# Timeout for the entire evaluation (milliseconds)
timeout: 60000

# Input for the agent (varies by tool)
input:
  objective: "Task description"  # For action_agent
  # OR
  message: "Prompt"              # For chat
  # OR
  task: "Multi-step task"        # For web_task_agent

# Validation configuration
validation:
  type: "llm-judge"
  llm_judge:
    model: "gpt-4.1-mini"
    temperature: 0.3  # Optional
    criteria:
      - "Criterion 1"
      - "Criterion 2"
    visual_verification:
      enabled: false  # Set to true for UI tests

# Metadata
metadata:
  tags: ["tag1", "tag2"]
  priority: "high"  # high, medium, low
  owner: "team-name"
```

### Tool Types

Different tools have different input fields:

**chat** - Simple text response:
```yaml
tool: "chat"
input:
  message: "Your question or prompt here"
```

**action_agent** - UI interactions:
```yaml
tool: "action_agent"
input:
  objective: "Click the submit button"
  reasoning: "Testing form submission"  # Optional
```

**web_task_agent** - Multi-step web tasks:
```yaml
tool: "web_task_agent"
input:
  task: "Search for flights from NYC to LAX on June 15"
```

**research_agent** - Research tasks:
```yaml
tool: "research_agent"
input:
  query: "What are the latest developments in quantum computing?"
```

### Target Configuration

```yaml
target:
  url: "https://example.com"        # URL to navigate to
  wait_for: "networkidle"           # Wait condition
  wait_timeout: 5000                # Timeout in milliseconds
```

For simple tests without web navigation:
```yaml
target:
  url: "about:blank"
  wait_timeout: 1000
```

---

## Judge Types

### LLM Judge (Text-only)

Standard text-based evaluation:

```yaml
validation:
  type: "llm-judge"
  llm_judge:
    model: "gpt-4.1-mini"  # or "gpt-5", "gpt-4.1"
    temperature: 0.3       # Optional
    criteria:
      - "Response is accurate"
      - "Response is complete"
      - "Response follows instructions"
```

The LLM judge:
- Evaluates text responses against criteria
- Provides pass/fail result
- Returns score (0.0 to 1.0)
- Includes reasoning for the judgment

### Vision Judge (Visual Verification)

For UI interaction tests requiring visual validation:

```yaml
validation:
  type: "llm-judge"
  llm_judge:
    model: "gpt-4.1-mini"
    criteria:
      - "Located the correct UI element"
      - "Successfully clicked the element"
      - "UI state changed as expected"
    visual_verification:
      enabled: true
      capture_before: true   # Future feature
      capture_after: true    # Currently implemented
      prompts:
        - "Verify the button is now in active state"
        - "Check if the modal dialog is visible"
```

The Vision judge:
- Automatically captures screenshots after agent actions
- Uses vision-capable models (GPT-4o, GPT-4.1, etc.)
- Analyzes visual state of the page
- Provides more accurate scoring for UI tests

**When to use Vision Judge:**
- Testing UI interactions (clicks, form fills, navigation)
- Verifying visual state changes
- Checking element visibility and styling
- Validating layout and positioning

---

## Visual Verification

### How It Works

1. **Screenshot Capture**: Framework automatically captures screenshot after agent completes action
2. **Metadata Extraction**: API client extracts `client_id` and `tab_id` from response
3. **CDP Screenshot**: Uses Chrome DevTools Protocol to capture viewport screenshot
4. **Image Loading**: Screenshot is loaded and converted to base64 data URL
5. **Vision Model**: Screenshot sent to vision-capable LLM with criteria
6. **Visual Analysis**: Model analyzes visual state and evaluates criteria

### Configuration

```yaml
visual_verification:
  enabled: true                    # Enable visual verification
  capture_before: true             # Future: before action screenshot
  capture_after: true              # Capture after action
  prompts:                         # Guide vision model
    - "Verify Section 2 is expanded"
    - "Check if other sections are collapsed"
    - "Ensure proper visual styling is applied"
```

### Screenshots Directory

Screenshots are saved to `screenshots/` with naming pattern:
```
<eval-id>_<timestamp>.png
```

Example: `screenshots/accordion-001_20251020_170412.png`

### Example: Accordion Test with Vision

```yaml
id: "accordion-001"
name: "Expand Accordion Section"
tool: "action_agent"

target:
  url: "https://jqueryui.com/accordion/"
  wait_for: "networkidle"
  wait_timeout: 5000

input:
  objective: "Click to expand the \"Section 2\" accordion panel"

validation:
  type: "llm-judge"
  llm_judge:
    model: "gpt-4.1-mini"
    criteria:
      - "Located the Section 2 accordion header"
      - "Successfully clicked to expand the section"
      - "Section 2 content became visible"
      - "Other sections collapsed appropriately"
    visual_verification:
      enabled: true
      prompts:
        - "Verify Section 2 is now expanded and content visible"
        - "Check if other accordion sections collapsed"
```

**Result:**
- Score: 0.80 (4/5 criteria met)
- Vision model confirms Section 2 is expanded (blue highlight)
- Vision model verifies content is visible
- Vision model checks other sections are collapsed
- Animation smoothness cannot be verified from static screenshot

---

## Results and Reports

### Console Output

Standard output:
```
[1/1] Running: Expand Accordion Section
  ID: accordion-001
  Status: PASS
  Score: 0.80
  Time: 167222ms
```

### Summary Statistics

```
======================================================================
Summary
======================================================================
Total: 10
Passed: 8 (80.0%)
Failed: 2
Average Score: 0.85
Average Time: 145234ms
======================================================================
```

### CSV Reports

Reports saved to `reports/` directory:
```
reports/action-agent_2025-10-20_17-04-43.csv
```

CSV columns:
- `eval_id` - Evaluation identifier
- `eval_name` - Human-readable name
- `category` - Category/subdirectory
- `passed` - Boolean pass/fail
- `score` - Numeric score 0.0-1.0
- `reasoning` - Judge's detailed reasoning
- `execution_time_ms` - Time taken in milliseconds
- `error` - Error message if failed
- `screenshot_path` - Path to captured screenshot (if any)

---

## Configuration Reference

### config.yml Structure

```yaml
# API endpoint for eval-server
api_endpoint: "http://localhost:8080"

# Models for the agent under test
main_model:
  provider: "openai"
  model_name: "gpt-5-mini"
  api_key: "${OPENAI_API_KEY}"

mini_model:
  provider: "openai"
  model_name: "gpt-5-nano"
  api_key: "${OPENAI_API_KEY}"

nano_model:
  provider: "openai"
  model_name: "gpt-5-nano"
  api_key: "${OPENAI_API_KEY}"

# Model for judging evaluations
judge_model:
  provider: "openai"
  model_name: "gpt-5"
  api_key: "${OPENAI_API_KEY}"

# Execution settings
execution:
  default_limit: 20           # Default number of evals to run
  timeout: 3600              # API request timeout (seconds)
  concurrent_requests: 1     # Concurrent execution
  request_delay: 1           # Delay between requests (seconds)

# Reporting settings
reporting:
  reports_dir: "reports"
  format: "csv"
  include_reasoning: true
```

### Environment Variables (.env)

```bash
# Required: OpenAI API key
OPENAI_API_KEY=sk-...

# Optional: Alternative providers
OPENROUTER_API_KEY=sk-or-...
ANTHROPIC_API_KEY=sk-ant-...
```

---

## Framework Architecture

### Components

**run.py (EvaluationRunner)**
- Entry point for running evaluations
- Handles CLI arguments and execution flow
- Coordinates between components
- Manages screenshot capture

**lib/eval_loader.py (EvalLoader, Evaluation)**
- Loads YAML evaluation definitions
- Parses configuration and metadata
- Provides evaluation objects to runner
- Handles visual verification config

**lib/api_client.py (APIClient)**
- Communicates with eval-server API
- Sends requests with model configs
- Captures screenshots via Chrome DevTools Protocol
- Extracts metadata (client_id, tab_id) from responses

**lib/judge.py (LLMJudge, VisionJudge)**
- LLMJudge: Text-based evaluation
- VisionJudge: Visual verification with screenshots
- Returns JudgeResult with pass/fail, score, reasoning

**lib/config_loader.py (ConfigLoader)**
- Loads global configuration from config.yml
- Handles environment variable substitution
- Provides model configs to components

### Data Flow

```
1. User: python3 run.py --path test.yaml --verbose

2. EvaluationRunner:
   - Loads config.yml
   - Initializes APIClient, LLMJudge, VisionJudge

3. EvalLoader:
   - Loads YAML evaluation
   - Parses configuration
   - Checks if visual_verification.enabled

4. APIClient:
   - Sends request to eval-server with input + models
   - Receives response + metadata (client_id, tab_id)

5. Screenshot Capture:
   - Uses client_id/tab_id to capture screenshot via CDP
   - Saves PNG to screenshots/ directory

6. Judging:
   - If visual_verification.enabled:
     - Use VisionJudge
     - Load screenshot as base64 data URL
     - Send to vision model with criteria and image
   - Else:
     - Use LLMJudge for text-only evaluation

7. Results:
   - Print to console (with verbose details)
   - Save CSV report
   - Include screenshot path
```

---

## Examples

### Simple Math Test

**File:** `data/test-simple/math-001.yaml`

```yaml
id: "math-001"
name: "Simple Math 5x7"
enabled: true

target:
  url: "about:blank"
  wait_timeout: 1000

tool: "chat"
timeout: 10000

input:
  message: "How much is 5x7? Just respond with the number."

validation:
  type: "llm-judge"
  llm_judge:
    model: "gpt-4.1-mini"
    criteria:
      - "Response contains the number 35"
      - "Response is mathematically correct"

metadata:
  tags: ["test", "simple", "math"]
  priority: "high"
```

**Run:**
```bash
python3 run.py --path test-simple/math-001.yaml --verbose
```

### UI Interaction Test with Vision

**File:** `data/action-agent/accordion-001.yaml`

```yaml
id: "accordion-001"
name: "Expand Accordion Section"
enabled: true

target:
  url: "https://jqueryui.com/accordion/"
  wait_for: "networkidle"
  wait_timeout: 5000

tool: "action_agent"
timeout: 60000

input:
  objective: "Click to expand the \"Section 2\" accordion panel"

validation:
  type: "llm-judge"
  llm_judge:
    model: "gpt-4.1-mini"
    criteria:
      - "Located the Section 2 accordion header"
      - "Successfully clicked to expand the section"
      - "Section 2 content became visible"
      - "Other sections collapsed appropriately"
    visual_verification:
      enabled: true
      prompts:
        - "Verify Section 2 is now expanded and content visible"
        - "Check if other accordion sections collapsed"

metadata:
  tags: ["action", "accordion", "ui"]
  priority: "high"
```

**Run:**
```bash
python3 run.py --path action-agent/accordion-001.yaml --verbose
```

---

## Troubleshooting

### API Server Connection Failed

**Error:** `API server is not reachable`

**Solution:**
1. Check if eval-server is running:
   ```bash
   docker-compose ps
   ```
2. Verify API endpoint in `config.yml`
3. Test connection:
   ```bash
   curl http://localhost:8080/health
   ```

### API Key Not Configured

**Error:** `API key not configured for provider: openai`

**Solution:**
1. Check `.env` file has `OPENAI_API_KEY=sk-...`
2. Verify `config.yml` references: `api_key: "${OPENAI_API_KEY}"`
3. Ensure `.env` file is in the `evals/` directory

### Screenshot Not Captured

**Issue:** Visual verification enabled but no screenshot

**Solution:**
1. Check that agent returned `client_id` and `tab_id` metadata
2. Verify eval-server is running with volume mount:
   ```yaml
   volumes:
     - "./eval-server/nodejs:/opt/eval-server"
   ```
3. Enable verbose mode to see capture attempts
4. Check `screenshots/` directory permissions

### Low Scores

**Issue:** Evaluations scoring lower than expected

**Solution:**
1. Review criteria - make them specific and measurable
2. Use verbose mode to see judge reasoning
3. Enable visual verification for UI tests
4. Check screenshots to verify agent behavior
5. Adjust criteria based on actual capabilities

### Environment Variable Not Found

**Error:** `Environment variable ${OPENAI_API_KEY} not found`

**Solution:**
1. Create `.env` file from `.env.example`
2. Add API key: `OPENAI_API_KEY=sk-your-key`
3. Or export in shell: `export OPENAI_API_KEY="sk-..."`

---

## Best Practices

### Writing Criteria

**Good criteria:**
- Specific and measurable
- Focus on observable outcomes
- One assertion per criterion
- Clear pass/fail conditions

Example:
```yaml
criteria:
  - "Response contains the number 35"
  - "Section 2 accordion is expanded"
  - "Search results show at least 5 flights"
```

**Bad criteria:**
- Vague or subjective ("Response is good")
- Multiple assertions ("Located and clicked button")
- Impossible to verify ("Animation was smooth")

### Using Visual Verification

**When to enable:**
- UI interaction tests
- Visual state verification
- Layout/styling checks

**When NOT to enable:**
- Simple text responses
- Logic/computation tests
- Research/information gathering

---

## Quick Reference

### Command Cheat Sheet

```bash
# Run single eval
python3 run.py --path <category>/<eval>.yaml

# Run with verbose output
python3 run.py --path <eval>.yaml --verbose

# Run all in category
python3 run.py --category <category>

# Run all evaluations
python3 run.py --all

# View results
cat reports/<category>_<timestamp>.csv

# View screenshot
open screenshots/<eval-id>_<timestamp>.png
```

### Evaluation Categories

- `test-simple/` - Simple sanity tests
- `action-agent/` - UI interaction tests
- `web-task-agent/` - Multi-step web tasks
- `research-agent/` - Research tasks
- `schema-extractor/` - Data extraction
- `screenshot-verification/` - Visual tests
- `end-to-end/` - Complex scenarios

---

## Contributing

To add new evaluations:

1. Create YAML file in appropriate `data/` category
2. Follow existing evaluation format
3. Test with verbose mode first
4. Adjust criteria based on results

To add new categories:

1. Create new directory under `data/`
2. Add YAML evaluation files
3. Run with `--category <new-category>`

---

## Version Information

- **Framework Version:** 2.0
- **Features:** Universal runner, VisionJudge, screenshot capture
- **Last Updated:** October 2025
