# Evaluation Framework

Modular evaluation framework for testing browser automation agents using LLM-as-a-judge.

## Overview

This framework provides:
- **Shared Configuration**: Single `config.yml` for all evaluation runners
- **Modular Runner Scripts**: Separate scripts for different evaluation categories
- **LLM Judge**: Uses GPT-4 to assess response quality against criteria
- **Automatic Reporting**: Timestamped CSV reports with detailed results

## Directory Structure

```
evals/
├── config.yml              # Shared configuration
├── data/                   # Evaluation definitions (YAML)
│   ├── action-agent/
│   ├── research-agent/
│   ├── schema-extractor/
│   └── ...
├── lib/                    # Shared library code
│   ├── config_loader.py
│   ├── eval_loader.py
│   ├── api_client.py
│   └── judge.py
├── reports/                # Generated CSV reports
├── run_action_agent.py     # Action agent runner
├── pyproject.toml          # Project configuration and dependencies
└── requirements.txt        # Legacy pip requirements (optional)
```

## Setup

### 1. Install uv (if not already installed)

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or using pip
pip install uv
```

### 2. Install Dependencies

```bash
cd evals

# Install dependencies using uv
uv pip install -e .

# Or use uv sync for development
uv sync
```

**Alternative (using pip):**
```bash
pip install -r requirements.txt
```

### 3. Configure Environment

You have two options for setting API keys:

#### Option A: Using .env file (Recommended)

```bash
# Copy the example file
cp .env.example .env

# Edit .env and add your API keys
# The file will be automatically loaded when running evaluations
```

Example `.env` file:
```bash
OPENAI_API_KEY=sk-your-actual-key-here
GROQ_API_KEY=gsk-your-actual-key-here  # Optional
```

#### Option B: Using shell environment variables

```bash
export OPENAI_API_KEY="sk-..."      # Required for LLM judge
export GROQ_API_KEY="gsk-..."       # Optional, if using Groq models
```

### 4. Configure Models

Edit `config.yml` to set your model preferences:

```yaml
main_model:
  provider: "openai"
  model_name: "gpt-4"
  api_key: "${OPENAI_API_KEY}"

judge_model:
  provider: "openai"
  model_name: "gpt-4"
  api_key: "${OPENAI_API_KEY}"
```

The config supports environment variable substitution using `${VAR_NAME}` syntax.

### 5. Start Evaluation Server

Ensure the evaluation server is running:

```bash
# From the project root
make compose-dev
# OR
docker run -d --name kernel-browser-extended ... kernel-browser:extended
```

The server should be accessible at `http://localhost:8080` (or the URL specified in `config.yml`).

## Usage

### Running Action Agent Evaluations

```bash
# Run all enabled action-agent evaluations (up to default limit)
./run_action_agent.py

# Run first 10 evaluations
./run_action_agent.py --limit 10

# Run specific evaluations by ID
./run_action_agent.py --eval-ids action-agent-click-001 action-agent-form-001

# Use custom config file
./run_action_agent.py --config /path/to/config.yml
```

### Command-Line Options

```
--limit N           Maximum number of evaluations to run
--eval-ids ID...    Specific evaluation IDs to run
--config PATH       Path to config file (default: evals/config.yml)
```

## How It Works

### 1. Load Configuration

The runner automatically:
- Loads environment variables from `.env` file (if present)
- Loads model configurations from `config.yml`, including:
  - API endpoint for the evaluation server
  - Model tiers (main, mini, nano) for agent requests
  - Judge model for evaluation assessment
  - Execution settings (timeouts, delays, etc.)
- Substitutes environment variables using `${VAR_NAME}` syntax

### 2. Load Evaluations

Evaluation definitions are loaded from YAML files in `data/`:

```yaml
id: "action-agent-click-001"
name: "Search with Text Entry and Click"
tool: "action_agent"
input:
  objective: "Type 'DevTools automation' in search box and click search button"
validation:
  type: "llm-judge"
  llm_judge:
    model: "gpt-4.1-mini"
    criteria:
      - "Successfully located the search input field"
      - "Entered text correctly"
      - "Search was executed and results loaded"
```

### 3. Execute Evaluations

For each evaluation:

1. **Extract input** from the YAML definition
2. **Send API request** to `/v1/responses` with model config
3. **Receive response** from the agent
4. **Judge response** using LLM against validation criteria
5. **Record result** (pass/fail, score, reasoning)

### 4. Generate Reports

Results are saved to `reports/` as timestamped CSV files:

```
reports/action-agent_2025-01-17_14-30-45.csv
```

CSV columns:
- `timestamp`: When the evaluation was run
- `eval_id`: Evaluation identifier
- `eval_name`: Human-readable name
- `category`: Evaluation category
- `status`: PASS or FAIL
- `score`: Numerical score (0-1)
- `judge_reasoning`: LLM judge's explanation
- `execution_time_ms`: API request duration
- `error`: Error message (if any)

## Creating New Runners

To create a runner for a different category (e.g., `research-agent`):

1. Copy `run_action_agent.py` to `run_research_agent.py`
2. Update the category parameter in `run_evaluations()`:
   ```python
   runner.run_evaluations(
       category='research-agent',  # Change this
       limit=limit,
       eval_ids=args.eval_ids
   )
   ```
3. Update the script description and help text
4. Make it executable: `chmod +x run_research_agent.py`

All runners share the same configuration and library code.

## Adding New Evaluations

To add new evaluation definitions:

1. Create a YAML file in the appropriate `data/` subdirectory
2. Follow the existing evaluation format:
   ```yaml
   id: "unique-eval-id"
   name: "Human-readable name"
   enabled: true
   tool: "action_agent"  # or chat, research_agent, etc.
   input:
     objective: "Task description"
   validation:
     type: "llm-judge"
     llm_judge:
       criteria:
         - "Criterion 1"
         - "Criterion 2"
   ```
3. The evaluation will be automatically discovered and loaded

## Configuration Reference

### Model Configuration

```yaml
main_model:
  provider: "openai"         # Provider: openai, groq, etc.
  model_name: "gpt-4"       # Model identifier
  api_key: "${ENV_VAR}"     # API key (supports env vars)
```

### Execution Settings

```yaml
execution:
  default_limit: 20           # Default number of evals to run
  timeout: 300               # API request timeout (seconds)
  concurrent_requests: 1     # Concurrent execution (future)
  request_delay: 1           # Delay between requests (seconds)
```

### Reporting Settings

```yaml
reporting:
  reports_dir: "reports"          # Where to save CSV reports
  format: "csv"                   # Report format
  include_reasoning: true         # Include judge reasoning
```

## Troubleshooting

### API Server Connection Failed

```
ERROR: Cannot connect to API server at http://localhost:8080
```

**Solution**: Ensure the evaluation server is running and accessible:
```bash
curl http://localhost:8080/status
```

### Environment Variable Not Found

```
ValueError: Environment variable ${OPENAI_API_KEY} not found
```

**Solution**: Set the required environment variable using one of these methods:

1. **Using .env file (recommended)**:
   ```bash
   cp .env.example .env
   # Edit .env and add: OPENAI_API_KEY=sk-your-actual-key
   ```

2. **Using shell export**:
   ```bash
   export OPENAI_API_KEY="sk-..."
   ```

### No Evaluations Found

```
No evaluations found in category: action-agent
```

**Solution**: Verify that:
1. The `data/action-agent/` directory exists
2. It contains `.yaml` files
3. Evaluations have `enabled: true`

## Future Enhancements

- Additional runner scripts for other categories
- Parallel evaluation execution
- Web UI for viewing reports
- Integration with CI/CD pipelines
- Support for additional judge providers (Claude, local models)
