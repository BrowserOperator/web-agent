# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

bo-eval-server is a thin WebSocket and REST API server for LLM agent evaluation. The server provides:
- WebSocket server for agent connections and RPC communication
- REST APIs for browser automation via Chrome DevTools Protocol (CDP)
- Screenshot capture and page content retrieval

**Evaluation orchestration and LLM-as-a-judge logic lives in the separate `evals/` Python project**, which calls these APIs.

## Commands

### Development
- `npm start` - Start the WebSocket server
- `npm run dev` - Start server with file watching for development
- `npm run cli` - Start interactive CLI for server management and testing
- `npm test` - Run example agent client for testing

### Installation
- `npm install` - Install dependencies
- Copy `.env.example` to `.env` and configure environment variables

### Required Environment Variables
- `OPENAI_API_KEY` - OpenAI API key for LLM judge functionality
- `PORT` - WebSocket server port (default: 8080)

### LLM Provider Configuration (Optional)
- `GROQ_API_KEY` - Groq API key for Groq provider support
- `OPENROUTER_API_KEY` - OpenRouter API key for OpenRouter provider support
- `LITELLM_ENDPOINT` - LiteLLM server endpoint URL
- `LITELLM_API_KEY` - LiteLLM API key for LiteLLM provider support
- `DEFAULT_PROVIDER` - Default LLM provider (openai, groq, openrouter, litellm)
- `DEFAULT_MAIN_MODEL` - Default main model name
- `DEFAULT_MINI_MODEL` - Default mini model name
- `DEFAULT_NANO_MODEL` - Default nano model name

## Architecture

### Core Components

**WebSocket Server** (`src/server.js`)
- Accepts connections from LLM agents
- Manages agent lifecycle (connect, ready, disconnect)
- Orchestrates evaluation sessions
- Handles bidirectional RPC communication

**RPC Client** (`src/rpc-client.js`)
- Implements JSON-RPC 2.0 protocol for bidirectional communication
- Manages request/response correlation with unique IDs
- Handles timeouts and error conditions
- Calls `Evaluate(request: String) -> String` method on connected agents
- Supports `configure_llm` method for dynamic LLM provider configuration

**CDP Integration** (`src/lib/EvalServer.js`)
- Direct Chrome DevTools Protocol communication
- Screenshot capture via `Page.captureScreenshot`
- Page content access via `Runtime.evaluate`
- Tab management via `Target.createTarget` / `Target.closeTarget`

**Logger** (`src/logger.js`)
- Structured logging using Winston
- Separate log files for different event types
- JSON format for easy parsing and analysis
- Logs all RPC calls, evaluations, and connection events

### Evaluation Flow

**WebSocket RPC Flow:**
1. Agent connects to WebSocket server
2. Agent sends "ready" signal
3. Server calls agent's `Evaluate` method with a task
4. Agent processes task and returns response
5. Response is returned to caller (evaluation orchestration happens externally in `evals/`)

**REST API Flow (for screenshot/content capture):**
1. External caller (e.g., Python evals runner) requests screenshot via `POST /page/screenshot`
2. Server uses CDP to capture screenshot
3. Returns base64-encoded image data
4. External caller uses screenshots for LLM-as-a-judge visual verification

### Project Structure

```
src/
├── server.js          # Main WebSocket server and evaluation orchestration
├── rpc-client.js      # JSON-RPC client for calling agent methods
├── evaluator.js       # LLM judge integration (OpenAI)
├── logger.js          # Structured logging and result storage
├── config.js          # Configuration management
└── cli.js             # Interactive CLI for testing and management

logs/                  # Log files (created automatically)
├── combined.log       # All log events
├── error.log          # Error events only
└── evaluations.jsonl  # Evaluation results in JSON Lines format
```

### Architecture: Separation of Concerns

**eval-server (Node.js)**: Thin API layer
- WebSocket server for agent connections
- JSON-RPC 2.0 bidirectional communication
- REST APIs for CDP operations (screenshots, page content, tab management)
- NO evaluation logic, NO judges, NO test orchestration

**evals (Python)**: Evaluation orchestration and judging
- LLM judges (LLMJudge, VisionJudge) in `lib/judge.py`
- Evaluation runners that call eval-server APIs
- Test case definitions (YAML files in `data/`)
- Result reporting and analysis

This separation keeps eval-server focused on infrastructure while evals/ handles business logic.

### Key Features

- **Bidirectional RPC**: Server can call methods on connected clients
- **Multi-Provider LLM Support**: Support for OpenAI, Groq, OpenRouter, and LiteLLM providers (configured by clients)
- **Dynamic LLM Configuration**: Runtime configuration via `configure_llm` JSON-RPC method
- **Per-Client Configuration**: Each connected client can have different LLM settings
- **CDP Browser Automation**: Screenshot capture, page content access, tab management
- **Concurrent Evaluations**: Support for multiple agents and parallel evaluations
- **Structured Logging**: All interactions logged as JSON for analysis
- **Interactive CLI**: Built-in CLI for testing and server management
- **Connection Management**: Robust handling of agent connections and disconnections
- **Timeout Handling**: Configurable timeouts for RPC calls and evaluations

### Agent Protocol

Agents must implement:
- WebSocket connection to server
- JSON-RPC 2.0 protocol support
- `Evaluate(task: string) -> string` method
- "ready" message to signal availability for evaluations

### Model Configuration Schema

The server uses a canonical nested model configuration format that allows per-tier provider and API key settings:

#### Model Configuration Structure

```typescript
interface ModelTierConfig {
  provider: string;  // "openai" | "groq" | "openrouter" | "litellm"
  model: string;     // Model name (e.g., "gpt-4", "llama-3.1-8b-instant")
  api_key: string;   // API key for this tier
}

interface ModelConfig {
  main_model: ModelTierConfig;  // Primary model for complex tasks
  mini_model: ModelTierConfig;  // Secondary model for simpler tasks
  nano_model: ModelTierConfig;  // Tertiary model for basic tasks
}
```

#### Example: Evaluation with Model Configuration

```json
{
  "jsonrpc": "2.0",
  "method": "evaluate",
  "params": {
    "tool": "chat",
    "input": {"message": "Hello"},
    "model": {
      "main_model": {
        "provider": "openai",
        "model": "gpt-4",
        "api_key": "sk-main-key"
      },
      "mini_model": {
        "provider": "openai",
        "model": "gpt-4-mini",
        "api_key": "sk-mini-key"
      },
      "nano_model": {
        "provider": "groq",
        "model": "llama-3.1-8b-instant",
        "api_key": "gsk-nano-key"
      }
    }
  }
}
```

### Dynamic LLM Configuration

The server supports runtime LLM configuration via the `configure_llm` JSON-RPC method:

```json
{
  "jsonrpc": "2.0",
  "method": "configure_llm",
  "params": {
    "provider": "openai|groq|openrouter|litellm",
    "apiKey": "your-api-key",
    "endpoint": "endpoint-url-for-litellm",
    "models": {
      "main": "main-model-name",
      "mini": "mini-model-name",
      "nano": "nano-model-name"
    },
    "partial": false
  },
  "id": "config-request-id"
}
```

### Tab Management

The evaluation server supports managing browser tabs via REST API endpoints and Chrome DevTools Protocol (CDP).

#### Tab Identification

Each browser tab is identified by a **composite client ID** in the format: `baseClientId:tabId`

- `baseClientId`: The persistent identifier for the DevTools client (e.g., `9907fd8d-92a8-4a6a-bce9-458ec8c57306`)
- `tabId`: The Chrome target ID for the specific tab (e.g., `482D56EE57B1931A3B9D1BFDAF935429`)

#### API Endpoints

**List All Clients and Tabs**
```bash
GET /clients
```

Returns all registered clients with their active tabs, connection status, and readiness state.

Response format:
```json
[
  {
    "id": "baseClientId",
    "name": "Client Name",
    "description": "Client Description",
    "tabCount": 3,
    "tabs": [
      {
        "tabId": "482D56EE57B1931A3B9D1BFDAF935429",
        "compositeClientId": "baseClientId:tabId",
        "connected": true,
        "ready": true,
        "connectedAt": "2025-01-15T10:30:00.000Z",
        "remoteAddress": "::ffff:172.18.0.1"
      }
    ]
  }
]
```

**List Tabs for Specific Client**
```bash
GET /clients/{clientId}/tabs
```

Returns all tabs for a specific client identified by `baseClientId`.

**Open New Tab**
```bash
POST /tabs/open
Content-Type: application/json

{
  "clientId": "baseClientId:tabId",
  "url": "https://example.com",
  "background": false
}
```

Opens a new tab in the browser associated with the specified client.

Response format:
```json
{
  "clientId": "baseClientId:tabId",
  "tabId": "newTabId",
  "compositeClientId": "baseClientId:newTabId",
  "url": "https://example.com",
  "status": "opened"
}
```

**Close Tab**
```bash
POST /tabs/close
Content-Type: application/json

{
  "clientId": "baseClientId:tabId",
  "tabId": "targetTabId"
}
```

Closes the specified tab.

Response format:
```json
{
  "clientId": "baseClientId:tabId",
  "tabId": "targetTabId",
  "status": "closed",
  "success": true
}
```

**Get Page Content**
```bash
POST /page/content
Content-Type: application/json

{
  "clientId": "baseClientId",
  "tabId": "targetTabId",
  "format": "html"  // or "text"
}
```

Retrieves the HTML or text content of a specific tab.

Response format:
```json
{
  "clientId": "baseClientId",
  "tabId": "targetTabId",
  "content": "<html>...</html>",
  "format": "html",
  "length": 12345,
  "timestamp": 1234567890
}
```

**Capture Screenshot**
```bash
POST /page/screenshot
Content-Type: application/json

{
  "clientId": "baseClientId",
  "tabId": "targetTabId",
  "fullPage": false
}
```

Captures a screenshot of a specific tab.

Response format:
```json
{
  "clientId": "baseClientId",
  "tabId": "targetTabId",
  "imageData": "data:image/png;base64,iVBORw0KG...",
  "format": "png",
  "fullPage": false,
  "timestamp": 1234567890
}
```

#### Implementation Architecture

**Direct CDP Approach (Current)**

Tab management and page content access are implemented using direct Chrome DevTools Protocol (CDP) communication:

1. Server discovers the CDP WebSocket endpoint via `http://localhost:9223/json/version`
2. For each command, a new WebSocket connection is established to the CDP endpoint
3. Commands are sent using JSON-RPC 2.0 format:
   - **Browser-level operations** (use `sendCDPCommand`):
     - `Target.createTarget` - Opens new tab
     - `Target.closeTarget` - Closes existing tab
   - **Tab-level operations** (use `sendCDPCommandToTarget`):
     - `Runtime.evaluate` - Execute JavaScript to get page content
     - `Page.captureScreenshot` - Capture screenshot of tab
4. For tab-level operations, the server first attaches to the target, executes the command, then detaches
5. WebSocket connection is closed after receiving the response

Key implementation files:
- `src/lib/EvalServer.js` - Contains CDP methods:
  - `sendCDPCommand()` - Browser-level CDP commands
  - `sendCDPCommandToTarget()` - Tab-level CDP commands (with attach/detach)
  - `openTab()`, `closeTab()` - Tab management
  - `getPageHTML()`, `getPageText()` - Page content access
  - `captureScreenshot()` - Screenshot capture
- `src/api-server.js` - REST API endpoints that delegate to EvalServer methods

**Alternative Approach Considered**

An RPC-based approach was initially considered where:
- API server sends JSON-RPC request to DevTools client via WebSocket
- DevTools client executes CDP commands locally
- Response is sent back via JSON-RPC

This was rejected in favor of direct CDP communication for simplicity and reduced latency.

#### Chrome Setup

The browser must be started with remote debugging enabled:
```bash
chromium --remote-debugging-port=9223
```

The CDP endpoint is accessible at:
- HTTP: `http://localhost:9223/json/version`
- WebSocket: `ws://localhost:9223/devtools/browser/{browserId}`

#### Usage Examples

**Complete workflow: Open tab, get content, take screenshot, close tab**

```bash
# 1. Get list of clients
curl -X GET http://localhost:8081/clients

# 2. Open a new tab
curl -X POST http://localhost:8081/tabs/open \
  -H "Content-Type: application/json" \
  -d '{"clientId":"9907fd8d-92a8-4a6a-bce9-458ec8c57306","url":"https://example.com"}'

# Response: {"tabId":"ABC123DEF456",...}

# 3. Get page HTML content
curl -X POST http://localhost:8081/page/content \
  -H "Content-Type: application/json" \
  -d '{"clientId":"9907fd8d-92a8-4a6a-bce9-458ec8c57306","tabId":"ABC123DEF456","format":"html"}'

# 4. Get page text content
curl -X POST http://localhost:8081/page/content \
  -H "Content-Type: application/json" \
  -d '{"clientId":"9907fd8d-92a8-4a6a-bce9-458ec8c57306","tabId":"ABC123DEF456","format":"text"}'

# 5. Capture screenshot
curl -X POST http://localhost:8081/page/screenshot \
  -H "Content-Type: application/json" \
  -d '{"clientId":"9907fd8d-92a8-4a6a-bce9-458ec8c57306","tabId":"ABC123DEF456","fullPage":false}'

# 6. Close the tab
curl -X POST http://localhost:8081/tabs/close \
  -H "Content-Type: application/json" \
  -d '{"clientId":"9907fd8d-92a8-4a6a-bce9-458ec8c57306","tabId":"ABC123DEF456"}'
```

**LLM-as-a-Judge evaluation pattern**

This workflow replicates the DevTools evaluation pattern using the eval-server:

```bash
# 1. Open tab and navigate to test URL
TAB_RESPONSE=$(curl -X POST http://localhost:8081/tabs/open \
  -H "Content-Type: application/json" \
  -d '{"clientId":"CLIENT_ID","url":"https://www.w3.org/WAI/ARIA/apg/patterns/button/examples/button/"}')

TAB_ID=$(echo $TAB_RESPONSE | jq -r '.tabId')

# 2. Capture BEFORE screenshot
BEFORE_SCREENSHOT=$(curl -X POST http://localhost:8081/page/screenshot \
  -H "Content-Type: application/json" \
  -d "{\"clientId\":\"CLIENT_ID\",\"tabId\":\"$TAB_ID\",\"fullPage\":false}")

# 3. Execute agent action (via /v1/responses or custom endpoint)
# ... agent performs action ...

# 4. Capture AFTER screenshot
AFTER_SCREENSHOT=$(curl -X POST http://localhost:8081/page/screenshot \
  -H "Content-Type: application/json" \
  -d "{\"clientId\":\"CLIENT_ID\",\"tabId\":\"$TAB_ID\",\"fullPage\":false}")

# 5. Get page content for verification
PAGE_CONTENT=$(curl -X POST http://localhost:8081/page/content \
  -H "Content-Type: application/json" \
  -d "{\"clientId\":\"CLIENT_ID\",\"tabId\":\"$TAB_ID\",\"format\":\"text\"}")

# 6. Send to LLM judge with screenshots and content
# (Use OpenAI Vision API or similar with before/after screenshots)

# 7. Clean up
curl -X POST http://localhost:8081/tabs/close \
  -H "Content-Type: application/json" \
  -d "{\"clientId\":\"CLIENT_ID\",\"tabId\":\"$TAB_ID\"}"
```

#### Current Limitations

**⚠️ Known Issue: WebSocket Timeout**

Tab opening and closing functionality is currently experiencing a WebSocket timeout issue:

- Symptom: `sendCDPCommand()` times out after 10 seconds with no response
- Error: `CDP command timeout: Target.createTarget`
- Status: Under investigation
- Debugging approach: Added extensive logging to track WebSocket lifecycle events

The CDP endpoint is correctly discovered and accessible, but WebSocket messages are not being received. This may be related to:
- WebSocket handshake issues
- CDP protocol version mismatch
- Network/proxy configuration
- Chrome process state

**Workaround**: Until this issue is resolved, tab management via the API is not functional. Manual CDP testing is required to diagnose the root cause.

#### Features Implemented

- ✅ Page HTML/text content access via CDP
- ✅ Screenshot capture via CDP
- ✅ Direct CDP communication for tab management
- ✅ Tab-level CDP command execution with attach/detach

#### Future Enhancements

- Automatic tab registration in ClientManager when DevTools connects
- Tab lifecycle events (opened, closed, navigated)
- Bulk tab operations
- Tab metadata (title, URL, favicon)
- Tab grouping and organization
- Additional CDP methods:
  - JavaScript execution with custom expressions
  - DOM tree access (`DOM.getDocument`)
  - MHTML snapshots (`Page.captureSnapshot`)
  - PDF generation (`Page.printToPDF`)

### Configuration

All configuration is managed through environment variables and `src/config.js`. Key settings:
- Server port and host
- OpenAI API configuration
- RPC timeouts
- Logging levels and directories
- Maximum concurrent evaluations
- CDP endpoint (default: localhost:9223)