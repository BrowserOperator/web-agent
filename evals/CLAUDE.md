# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is the **Evaluation Framework** for testing browser automation agents. It uses **LLM-as-a-judge** to evaluate agent responses against defined criteria, with support for **visual verification** through screenshots.

The framework is completely independent of the main browser-agent server and operates as a standalone Python application that communicates with the browser-agent-server API at http://localhost:8080.

## Framework Structure

The evals directory contains two types of evaluation runners:

1. **native/** - Native evaluation runner using YAML-based test definitions
   - Custom test suite for browser automation features
   - LLM-as-a-judge evaluation
   - Visual verification support

2. **webarena/** - WebArena benchmark runner
   - 812 standardized benchmark tasks
   - Deterministic evaluation (string/URL/HTML matching)
   - Self-hosted environment support

Both runners share the common library in `lib/` which includes judges, API clients, and adapters.

## Quick Start Commands

### Installation

```bash
# Install dependencies using pip
pip install -r requirements.txt

# OR install as editable package with uv (recommended)
uv pip install -e .
```

### Configuration

```bash
# 1. Copy environment template
cp .env.example .env

# 2. Edit .env and add your API keys
#    OPENAI_API_KEY=sk-...
#    OPENROUTER_API_KEY=...

# 3. Edit config.yml to set model preferences
#    - main_model: The model under test (sent to eval-server)
#    - judge_model: The model used to evaluate responses (local)
```

### Running Evaluations

**Native evaluations:**
```bash
# Navigate to native runner directory
cd native

# Run a specific evaluation by path (relative to data/)
python3 run.py --path test-simple/math-001.yaml

# Run with verbose output (shows input, response, reasoning, screenshots)
python3 run.py --path action-agent/accordion-001.yaml --verbose

# Run all evaluations in a category
python3 run.py --category action-agent

# Run all evaluations across all categories
python3 run.py --all

# Run with a limit
python3 run.py --category action-agent --limit 5

# Run specific evals by ID within a category
python3 run.py --category action-agent --eval-ids accordion-001 modal-001
```

**WebArena evaluations:**
```bash
# Navigate to webarena runner directory
cd webarena

# Run a specific task by ID
python3 run_webarena.py --task-id 1

# Run with verbose output
python3 run_webarena.py --task-id 1 --verbose

# Run multiple tasks
python3 run_webarena.py --all --limit 10
```

### Viewing Results

```bash
# Reports are saved to reports/ directory as CSV files
cat reports/action-agent_2025-10-29_14-30-45.csv

# Screenshots are saved to screenshots/ directory
ls -lh screenshots/
```

## Architecture

### Core Components

1. **run.py (EvaluationRunner)** - Main entry point
   - Coordinates evaluation execution
   - Handles CLI arguments and execution modes
   - Manages screenshot capture via CDP
   - Generates CSV reports

2. **lib/eval_loader.py (EvalLoader, Evaluation)** - YAML evaluation parser
   - Loads and parses YAML evaluation definitions
   - Provides structured access to eval configuration
   - Handles different tool types (chat, action_agent, web_task_agent, etc.)

3. **lib/api_client.py (APIClient)** - HTTP client for eval-server
   - Sends requests to `/v1/responses` endpoint
   - Captures screenshots via `/page/screenshot` endpoint
   - Extracts metadata (client_id, tab_id) from responses
   - Handles errors and timeouts

4. **lib/judge.py (LLMJudge, VisionJudge, SimpleJudge)** - Evaluation judges
   - **LLMJudge**: Text-based evaluation using OpenAI API
   - **VisionJudge**: Visual verification with screenshots (uses vision-capable models)
   - **SimpleJudge**: Fallback keyword-based evaluation

5. **lib/config_loader.py (ConfigLoader)** - Configuration management
   - Loads config.yml
   - Handles environment variable substitution (e.g., `${OPENAI_API_KEY}`)
   - Provides model configs to components

### Data Flow

```
1. CLI (run.py --path test.yaml --verbose)
   ↓
2. ConfigLoader loads config.yml + .env
   ↓
3. EvalLoader parses YAML evaluation definition
   ↓
4. APIClient sends request to eval-server at localhost:8080
   ↓
5. eval-server executes agent action and returns response + metadata
   ↓
6. APIClient extracts client_id/tab_id from response metadata
   ↓
7. APIClient captures screenshot via CDP (if metadata present)
   ↓
8. VisionJudge or LLMJudge evaluates response against criteria
   (VisionJudge uses screenshot for visual verification)
   ↓
9. EvaluationRunner saves results to CSV and prints summary
```

## Directory Structure

```
evals/
├── config.yml                      # Global configuration (models, API endpoint)
├── .env                            # API keys (gitignored, copy from .env.example)
├── .env.example                    # Environment template
├── requirements.txt                # Python dependencies
├── pyproject.toml                  # Package metadata for uv/pip
├── CLAUDE.md                       # This file
├── README.md                       # User documentation
│
├── lib/                            # Shared framework library
│   ├── __init__.py                 # Library exports
│   ├── config_loader.py            # Configuration management
│   ├── eval_loader.py              # YAML evaluation loader
│   ├── api_client.py               # HTTP client for browser-agent-server
│   ├── judge.py                    # LLMJudge, VisionJudge, SimpleJudge
│   ├── webarena_adapter.py         # WebArena task adapter
│   └── webarena_evaluators.py      # WebArena evaluators
│
├── native/                         # Native evaluation runner
│   ├── run.py                      # Main runner (entry point)
│   ├── test_vision_judge.py        # Vision judge tests
│   └── data/                       # Native evaluation YAML files
│       ├── test-simple/            # Simple sanity tests (math, chat)
│       ├── action-agent/           # UI interaction tests (clicks, forms)
│       ├── web-task-agent/         # Multi-step web tasks (flights, shopping)
│       ├── research-agent/         # Research and information gathering
│       ├── schema-extractor/       # Data extraction tests
│       ├── screenshot-verification/ # Visual verification tests
│       └── end-to-end/             # Complex multi-step scenarios
│
├── webarena/                       # WebArena benchmark runner
│   ├── run_webarena.py             # WebArena runner (entry point)
│   ├── run_gitlab_tasks.py         # GitLab-specific tasks
│   ├── run_shopping_tasks.py       # Shopping-specific tasks
│   ├── login_webarena_sites.py     # Site login utilities
│   ├── test_webarena_integration.py # Integration tests
│   ├── data/                       # WebArena-specific data
│   │   └── login/                  # Login credentials and configs
│   └── webarena-local/             # Local WebArena environment
│       ├── docker-compose.yml      # Local services setup
│       ├── setup-webarena.sh       # Setup script
│       └── README.md               # WebArena setup guide
│
├── screenshots/                    # Auto-generated screenshots (gitignored)
└── reports/                        # CSV evaluation reports (gitignored)
```

## YAML Evaluation Format

Every evaluation is defined in a YAML file with this structure:

```yaml
id: "unique-identifier"             # Unique eval ID
name: "Human Readable Name"         # Display name
description: "What this test does"  # Description
enabled: true                       # Enable/disable

target:                             # Where to navigate
  url: "https://example.com"
  wait_for: "networkidle"          # or "domcontentloaded", "load"
  wait_timeout: 5000               # milliseconds

tool: "action_agent"               # Tool type (see below)
timeout: 60000                     # Eval timeout (ms)

input:                             # Input varies by tool type
  objective: "Click the submit button"  # For action_agent
  # OR message: "..."               # For chat
  # OR task: "..."                  # For web_task_agent
  # OR query: "..."                 # For research_agent

validation:                        # How to evaluate
  type: "llm-judge"
  llm_judge:
    model: "gpt-4.1-mini"          # Model for judging
    temperature: 0.3               # Optional
    criteria:                      # What to check
      - "Criterion 1"
      - "Criterion 2"
    visual_verification:           # Optional visual check
      enabled: true                # Use VisionJudge with screenshots
      prompts:                     # Guide vision model
        - "Verify X is visible"
        - "Check Y has changed"

metadata:                          # Optional metadata
  tags: ["tag1", "tag2"]
  priority: "high"                 # high, medium, low
  owner: "team-name"
```

### Tool Types

Different tools have different input fields:

- **chat**: `input.message` - Simple text prompt
- **action_agent**: `input.objective` - UI interaction objective
- **web_task_agent**: `input.task` - Multi-step web task
- **research_agent**: `input.query` - Research query
- **extract_data**: `input.instruction` - Data extraction instruction
- **take_screenshot**: Uses `target.url` and `input.fullPage`

## Visual Verification (VisionJudge)

When an evaluation has `visual_verification.enabled: true`:

1. **Screenshot is captured** after agent completes action
2. **VisionJudge is used** instead of LLMJudge
3. **Vision model** (e.g., gpt-4.1-mini with vision) analyzes the screenshot
4. **More accurate scores** for UI tests (can verify visual state changes)

**When to use VisionJudge:**
- UI interaction tests (clicks, form fills, navigation)
- Verifying visual state changes (modals, accordions, tooltips)
- Checking element visibility, styling, layout

**When NOT to use VisionJudge:**
- Simple text responses (chat, math)
- Logic/computation tests
- Research/information gathering

## Important Implementation Details

### Screenshot Capture Flow

The framework uses a two-step process:

1. **Agent executes action** via `/v1/responses` endpoint
2. **Response includes metadata** with `clientId` and `tabId`
3. **APIClient extracts metadata** in `_extract_metadata()` (api_client.py:200-217)
4. **APIClient captures screenshot** via `/page/screenshot` endpoint (api_client.py:219-291)
5. **Screenshot saved** to `screenshots/` with pattern: `{eval_id}_{timestamp}.png`
6. **VisionJudge loads screenshot** as base64 data URL for vision model

### Model Configuration

The framework uses a **nested model config** format for API requests:

```python
{
    "main_model": {
        "provider": "openai",
        "model": "gpt-5-mini",
        "api_key": "sk-..."
    },
    "mini_model": {...},
    "nano_model": {...}
}
```

This is constructed by `ConfigLoader.get_nested_model_config()` and sent to eval-server in the request payload.

### Judge Selection Logic

In run.py:287-386 (`_run_single_evaluation`):

1. Check if `evaluation.requires_vision_judge()` (eval_loader.py:109-121)
2. If yes AND screenshot captured → use **VisionJudge** with screenshot
3. If no → use **LLMJudge** for text-only evaluation

### Environment Variable Substitution

In config.yml, use `${VAR_NAME}` syntax:

```yaml
judge_model:
  api_key: "${OPENAI_API_KEY}"
```

ConfigLoader automatically substitutes from `.env` file using python-dotenv.

## Common Development Tasks

### Adding a New Evaluation

1. Create YAML file in appropriate `data/` category:
   ```bash
   vim data/action-agent/my-new-test.yaml
   ```

2. Follow the YAML format (see above)

3. Test with verbose mode:
   ```bash
   python3 run.py --path action-agent/my-new-test.yaml --verbose
   ```

4. Review judge reasoning and adjust criteria if needed

### Adding a New Judge Type

1. Create new class in `lib/judge.py` that implements:
   - `judge(input_prompt, response, criteria) -> JudgeResult`

2. Initialize in `run.py` EvaluationRunner.__init__()

3. Add selection logic in `_run_single_evaluation()`

### Adding a New Tool Type

1. Add tool name to `lib/eval_loader.py` in `get_input_message()` (line 59-92)

2. Define how to extract input message from YAML

3. Test with a sample evaluation

### Debugging Failed Evaluations

1. **Use verbose mode** to see input, response, and reasoning:
   ```bash
   python3 run.py --path path/to/eval.yaml --verbose
   ```

2. **Check screenshots** if visual verification is enabled:
   ```bash
   ls -lh screenshots/
   open screenshots/eval-id_timestamp.png
   ```

3. **Review CSV reports** for detailed results:
   ```bash
   cat reports/category_timestamp.csv
   ```

4. **Test API endpoint directly**:
   ```bash
   curl http://localhost:8080/status
   ```

5. **Check eval-server logs** (in parent directory):
   ```bash
   docker logs kernel-browser-extended | tail -50
   ```

### WebArena Integration

The `webarena/` subdirectory contains a separate evaluation runner for the WebArena benchmark:

- **Different architecture**: WebArena uses its own agent implementations and evaluation harness
- **Separate runner**: `webarena/run.py` (not the main `run.py`)
- **Not covered by this framework**: WebArena evals don't use the LLM-as-a-judge approach

## Dependencies

- **PyYAML**: YAML parsing for evaluation definitions
- **requests**: HTTP client for API communication
- **openai**: OpenAI API client for LLMJudge and VisionJudge
- **python-dotenv**: Environment variable management

Install with: `pip install -r requirements.txt` or `uv pip install -e .`

## Configuration Files

### config.yml

Global configuration loaded by every evaluation run:

- **api_endpoint**: URL of eval-server (default: http://localhost:8080)
- **main_model, mini_model, nano_model**: Models sent to eval-server for agent execution
- **judge_model**: Model used locally to evaluate responses
- **execution**: Timeout, concurrency, request delay settings
- **reporting**: Reports directory, format, options

### .env

API keys and secrets (gitignored):

- **OPENAI_API_KEY**: Required for LLMJudge and VisionJudge
- **OPENROUTER_API_KEY**: Optional, if using OpenRouter models
- **GROQ_API_KEY**: Optional, if using Groq models

Copy from `.env.example` and fill in your actual keys.

## Testing

### Quick API Test

```bash
# Check if eval-server is running
curl http://localhost:8080/status

# Run simple math test
python3 run.py --path test-simple/math-001.yaml --verbose
```

### Test Tracing Configuration

```bash
# Run test script to verify tracing setup
./test-tracing.sh
```

## Report Format

CSV reports are saved to `reports/` with columns:

- **timestamp**: When the eval was run
- **eval_id**: Unique identifier
- **eval_name**: Human-readable name
- **category**: Category/subdirectory
- **status**: PASS or FAIL
- **score**: Numeric score 0.0-1.0
- **judge_reasoning**: Detailed explanation from judge
- **execution_time_ms**: Time taken in milliseconds
- **error**: Error message if failed

## WebArena Integration

The framework now supports running **WebArena benchmark tasks** (812 tasks) alongside the custom YAML evaluations.

### What is WebArena?

WebArena is a comprehensive research benchmark for web agents featuring:
- **812 tasks** across 7 self-hosted websites
- **Realistic environments**: E-commerce, forums, GitLab, Wikipedia, maps
- **Deterministic evaluation**: String matching, URL matching, HTML content verification
- **Multi-step agent trajectories**: Complex tasks requiring multiple actions

### Quick Start with WebArena

```bash
# Run a specific WebArena task
python3 run_webarena.py --task-id 1

# Run all public site tasks (no self-hosted environment needed)
python3 run_webarena.py --all --public-only --limit 10

# Run with verbose output
python3 run_webarena.py --task-id 2 --verbose

# Run first 20 example tasks
python3 run_webarena.py --all --limit 20
```

### WebArena Architecture

**Task Format:** JSON configuration files in `webarena/config_files/`

```json
{
  "task_id": 1,
  "sites": ["reddit"],
  "intent": "tell me all subreddits starting with character 'a'",
  "start_url": "http://localhost:9999/",
  "eval": {
    "eval_types": ["string_match"],
    "reference_answers": ["announcements Art AskReddit"]
  }
}
```

**Evaluation Types:**
- **string_match**: Exact match, must include phrases, fuzzy match (LLM-based)
- **url_match**: URL and query parameter matching
- **program_html**: JavaScript-based page content verification

### WebArena Components

1. **run_webarena.py (WebArenaRunner)** - Main runner for WebArena tasks
   - Loads JSON task configurations
   - Uses existing eval-server API infrastructure
   - Applies WebArena evaluators for scoring

2. **lib/webarena_adapter.py** - Adapts WebArena to eval-server
   - **WebArenaTask**: Parses JSON task configs
   - **WebArenaExecutor**: Executes tasks via APIClient
   - **WebArenaTaskLoader**: Loads tasks from config files

3. **lib/webarena_evaluators.py** - WebArena evaluation logic
   - **StringEvaluator**: Text matching (exact, must_include, fuzzy)
   - **URLEvaluator**: URL and query parameter validation
   - **HTMLContentEvaluator**: Page content verification via CDP

### Local Environment Setup

WebArena tasks require self-hosted websites. Two options:

**Option 1: Public Sites Only (Quick)**
```bash
# Run tasks that work on public websites
python3 run_webarena.py --all --public-only
```

**Option 2: Full Local Setup (Complete)**
```bash
# See webarena-local/README.md for detailed instructions
cd webarena-local
docker-compose up -d
```

Services:
- Shopping (OneStopShop): localhost:7770
- Shopping Admin: localhost:7780
- Forum (Reddit clone): localhost:9999
- GitLab: localhost:8023
- Wikipedia: localhost:8888
- Map: localhost:3000
- Homepage: localhost:4399

### Task Configuration Files

- `webarena/config_files/examples/*.json` - Example tasks (4-5 samples)
- `webarena/config_files/test.raw.json` - Full benchmark (812 tasks)

### Comparison: YAML Evals vs WebArena

| Aspect | YAML Evals | WebArena |
|--------|-----------|----------|
| **Format** | YAML (human-readable) | JSON (auto-generated) |
| **Tasks** | ~100 hand-crafted | 812 benchmark tasks |
| **Evaluation** | LLM judge + Vision | Deterministic (string/URL/HTML) |
| **Sites** | Public internet | Self-hosted (7 websites) |
| **Use Case** | Feature testing, DevTools | Research benchmark, agent comparison |
| **Runner** | `run.py` | `run_webarena.py` |

### Adding WebArena Tasks

WebArena tasks are predefined in JSON. To add new tasks:

1. Create JSON config in `webarena/config_files/examples/`
2. Follow WebArena task format
3. Run with: `python3 run_webarena.py --task-id <new-id>`

### WebArena Results

Reports saved to `reports/webarena-*.csv`:

```csv
task_id,site,intent,eval_types,status,score,response,execution_time_ms
1,reddit,"List subreddits starting with 'a'","string_match",PASS,1.00,"announcements Art...",12450
2,misc,"Check classification section","url_match",PASS,1.00,"Done",8320
```

### Troubleshooting WebArena

**"Task requires self-hosted WebArena sites" error:**
- Use `--public-only` flag or set up local environment (see webarena-local/README.md)

**Task execution failures:**
- Verify eval-server is running: `curl http://localhost:8080/status`
- Check task config exists: `ls webarena/config_files/examples/<id>.json`
- Run with `--verbose` to see detailed errors

**Low scores:**
- WebArena uses deterministic evaluation (must match exactly)
- Check response format matches expected reference answers
- Review task requirements in JSON config

### Documentation

- **Local setup guide**: `webarena-local/README.md`
- **WebArena README**: `webarena/README.md`
- **Docker environment**: `webarena/environment_docker/README.md`
- **Runner help**: `python3 run_webarena.py --help`

## Code Navigation

### Key Entry Points

- **native/run.py:523-628** - `main()` function with CLI argument parsing
- **native/run.py:287-386** - `_run_single_evaluation()` where the magic happens
- **webarena/run_webarena.py:280-380** - WebArena main() and runner
- **lib/api_client.py:24-153** - `send_request()` for API communication
- **lib/judge.py:73-143** - LLMJudge implementation
- **lib/judge.py:222-325** - VisionJudge implementation
- **lib/eval_loader.py:59-92** - Tool type input extraction logic
- **lib/webarena_adapter.py:80-170** - WebArena task execution
- **lib/webarena_evaluators.py:70-230** - WebArena evaluation logic

### Important Classes

- **EvaluationRunner** (native/run.py:33-521) - Orchestrates native evals
- **WebArenaRunner** (webarena/run_webarena.py:21-277) - Orchestrates WebArena evals
- **Evaluation** (lib/eval_loader.py:10-174) - Represents single eval definition
- **WebArenaTask** (lib/webarena_adapter.py:19-79) - Represents WebArena task
- **EvalLoader** (lib/eval_loader.py:176-315) - Loads evals from YAML files
- **WebArenaTaskLoader** (lib/webarena_adapter.py:172-330) - Loads WebArena tasks
- **APIClient** (lib/api_client.py:10-382) - Communicates with browser-agent-server
- **LLMJudge** (lib/judge.py:44-191) - Text-based evaluation
- **VisionJudge** (lib/judge.py:193-386) - Visual verification
- **StringEvaluator** (lib/webarena_evaluators.py:38-210) - String matching evaluation
- **URLEvaluator** (lib/webarena_evaluators.py:213-290) - URL matching evaluation
- **HTMLContentEvaluator** (lib/webarena_evaluators.py:293-385) - HTML content evaluation
- **JudgeResult** (lib/judge.py:10-42) - Evaluation result data structure
