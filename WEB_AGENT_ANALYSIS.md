# Web Agent Architecture Analysis

## Executive Summary

This web agent is a sophisticated browser automation system that combines:
- **Chromium Browser** with Chrome DevTools Protocol (CDP) for low-level browser control
- **Custom DevTools Frontend** with AI capabilities for interactive agent control
- **Browser Agent Server** providing HTTP/WebSocket APIs for programmatic automation
- **Evaluation Framework** for testing and validating agent performance

The system enables both interactive (via DevTools UI) and programmatic (via API) browser automation with AI-powered decision making.

---

## System Architecture

### High-Level Component Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Docker Container                         │
│                                                                  │
│  ┌──────────────┐    ┌──────────────────┐   ┌───────────────┐  │
│  │   Chromium   │◄───┤ Browser Agent    │◄──┤ HTTP Clients  │  │
│  │  (w/ CDP)    │    │     Server       │   │  (Evals)      │  │
│  │  Port 9223   │    │  HTTP: 8080      │   └───────────────┘  │
│  └──────┬───────┘    │  WS: 8082        │                       │
│         │            └──────────────────┘                       │
│         │                                                        │
│  ┌──────▼───────┐    ┌──────────────────┐                       │
│  │   Custom     │    │  WebRTC Neko     │                       │
│  │  DevTools    │    │  (Port 8000,     │                       │
│  │  (Port 8001) │    │   8081)          │                       │
│  └──────────────┘    └──────────────────┘                       │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Supervisor (manages all services)                         │ │
│  │  - Xorg, Mutter, DBus, Chromium, Neko, Eval Server, nginx │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Core Components

#### 1. **Chromium Browser**
- **Location**: Runs as headful browser in X11 display `:1`
- **CDP Endpoint**: `http://localhost:9223/json/version`
- **Purpose**: Actual web browsing and page rendering
- **Configuration**:
  - Custom DevTools frontend at `http://localhost:8001/`
  - Auto-opens DevTools for all tabs
  - Remote debugging enabled on port 9223

#### 2. **Browser Agent Server** (`browser-agent-server/nodejs/`)
- **Main Entry**: `start.js`
- **Dual API**:
  - **WebSocket** (port 8082): JSON-RPC 2.0 for bidirectional DevTools communication
  - **HTTP** (port 8080): REST API for evaluations and automation
- **Key Responsibilities**:
  - Manage DevTools client connections
  - Execute browser automation requests
  - Control tabs via CDP
  - Coordinate AI model interactions

**Architecture**:
```javascript
start.js
├── BrowserAgentServer (WebSocket Server on 8082)
│   ├── Manages DevTools client connections
│   ├── ClientManager (tracks clients and tabs)
│   └── RpcClient (JSON-RPC 2.0 communication)
└── HTTPWrapper (HTTP Server on 8080)
    └── APIServer (REST endpoints)
        ├── /v1/responses (main automation endpoint)
        ├── /page/content (get page HTML/text)
        ├── /page/screenshot (capture screenshots)
        └── /tabs/* (tab management)
```

#### 3. **Custom DevTools Frontend**
- **Location**: `submodules/browser-operator-core/`
- **Build**: Multi-stage Docker build creates `browser-operator-devtools:latest` image
- **Served by**: nginx on port 8001
- **Features**:
  - Standard Chrome DevTools panels (Elements, Console, Network, etc.)
  - Custom AI Chat panel for interactive agent control
  - WebSocket connection to Browser Agent Server
  - Registers with server as a client (per-tab connections)

#### 4. **Evaluation Framework** (`evals/`)
- **Native Evaluations**: YAML-based test definitions
- **WebArena Support**: 812-task benchmark suite
- **Components**:
  - `APIClient`: HTTP client for `/v1/responses` endpoint
  - `EvalLoader`: YAML evaluation file parser
  - `LLMJudge`: AI-powered response validation
  - `VisionJudge`: Screenshot-based validation
  - Evaluation runners (native, WebArena)

---

## Data Flow: Complete Request Lifecycle

### Scenario: Running an Evaluation

Let's trace how the system executes a simple evaluation like `math-001.yaml`:

```yaml
id: "math-001"
name: "Simple Math 5x7"
input:
  message: "How much is 5x7? Just respond with the number."
target:
  url: "about:blank"
validation:
  type: "llm-judge"
  llm_judge:
    criteria:
      - "Response contains the number 35"
```

### Step-by-Step Flow

#### **Step 1: Evaluation Runner Initialization**
```python
# evals/native/run.py
runner = EvaluationRunner(config)
runner.run_from_path("data/test-simple/math-001.yaml")
```

**What happens**:
1. Loads global config from `evals/config.yml` (API endpoint, model config, judge config)
2. Creates `APIClient` pointing to `http://localhost:8080`
3. Initializes `LLMJudge` with GPT-4 for validation
4. Checks API server health via `GET /status`

#### **Step 2: Load and Parse Evaluation**
```python
evaluation = Evaluation(eval_file, yaml_data)
input_message = evaluation.get_input_message()
# Returns: "How much is 5x7? Just respond with the number."
```

#### **Step 3: Send HTTP Request to Browser Agent Server**
```python
api_response = api_client.send_request(
    input_message="How much is 5x7?",
    model_config={
        "main_model": {"provider": "openai", "model": "gpt-4", "api_key": "sk-..."},
        "mini_model": {...},
        "nano_model": {...}
    },
    url="about:blank",
    wait_timeout=1000
)
```

**HTTP Request**:
```http
POST http://localhost:8080/v1/responses
Content-Type: application/json

{
  "input": "How much is 5x7? Just respond with the number.",
  "url": "about:blank",
  "wait_timeout": 1000,
  "model": {
    "main_model": {"provider": "openai", "model": "gpt-4", "api_key": "sk-..."},
    ...
  }
}
```

#### **Step 4: API Server Handles Request**
**File**: `browser-agent-server/nodejs/src/api-server.js`

```javascript
async handleResponsesRequest(requestBody) {
  // 1. Find a base client ID (e.g., "default")
  const baseClientId = this.findClientWithTabs();

  // 2. Open new tab via CDP
  const tabResult = await this.browserAgentServer.openTab(baseClientId, {
    url: "about:blank",
    background: false
  });
  // Returns: { tabId: "E1A2B3C4...", compositeClientId: "default:E1A2B3C4..." }

  // 3. Wait for DevTools client to connect
  const tabClient = await this.waitForClientConnection("default:E1A2B3C4...");

  // 4. Create request object
  const request = {
    id: "req-1234567890",
    name: "Dynamic Request",
    tool: "chat",
    input: { message: "How much is 5x7?" },
    model: { main_model: {...}, mini_model: {...}, nano_model: {...} }
  };

  // 5. Execute request via WebSocket RPC
  const result = await this.browserAgentServer.executeRequest(tabClient, request);

  // 6. Format response in OpenAI-compatible format
  return this.formatResponse(result);
}
```

#### **Step 5: Open Tab via CDP**
**File**: `browser-agent-server/nodejs/src/lib/BrowserAgentServer.js`

```javascript
async openTab(baseClientId, options) {
  // 1. Get CDP WebSocket endpoint
  const cdpUrl = "http://localhost:9223/json/version";
  const response = await fetch(cdpUrl);
  const data = await response.json();
  const wsUrl = data.webSocketDebuggerUrl; // "ws://localhost:9223/devtools/browser/..."

  // 2. Send CDP command to create new target
  const result = await this.sendCDPCommand('Target.createTarget', {
    url: "about:blank",
    newWindow: false,
    background: false
  });

  // 3. Return tab info
  return {
    tabId: result.targetId,  // e.g., "E1A2B3C4D5E6F7G8"
    compositeClientId: "default:E1A2B3C4D5E6F7G8",
    url: "about:blank"
  };
}
```

**CDP WebSocket Communication**:
```javascript
// Open WebSocket to CDP
const ws = new WebSocket("ws://localhost:9223/devtools/browser/...");

// Send command
ws.send(JSON.stringify({
  id: 123456,
  method: "Target.createTarget",
  params: { url: "about:blank", newWindow: false, background: false }
}));

// Receive response
// {"id": 123456, "result": {"targetId": "E1A2B3C4D5E6F7G8"}}
```

**What happens in Chromium**:
- New tab is created with target ID `E1A2B3C4D5E6F7G8`
- Chromium loads `about:blank`
- Custom DevTools frontend auto-opens for this tab
- DevTools connects to `ws://localhost:8082` (Browser Agent Server)

#### **Step 6: DevTools Client Connection**
**DevTools Frontend** (running in the new tab):
```javascript
// DevTools connects to Browser Agent Server
const ws = new WebSocket("ws://localhost:8082");

// Send registration message
ws.send(JSON.stringify({
  type: "register",
  clientId: "default:E1A2B3C4D5E6F7G8",
  capabilities: {
    chat: true,
    screenshot: true,
    search: true
  },
  version: "1.0.0"
}));

// Server responds with auth challenge
// Client verifies secret key, server acknowledges registration

// Client signals ready
ws.send(JSON.stringify({ type: "ready" }));
```

**Browser Agent Server**:
```javascript
handleConnection(ws) {
  // Creates connection object
  const connection = {
    id: "conn-abc123",
    ws: ws,
    clientId: null,  // Set after registration
    registered: false,
    ready: false,
    rpcClient: new RpcClient()  // For JSON-RPC calls
  };

  this.connectedClients.set("conn-abc123", connection);
}

handleRegistration(connection, data) {
  // After auth verification...
  connection.clientId = "default:E1A2B3C4D5E6F7G8";
  connection.registered = true;

  // Move to composite clientId key
  this.connectedClients.delete("conn-abc123");
  this.connectedClients.set("default:E1A2B3C4D5E6F7G8", connection);
}
```

#### **Step 7: Execute Request via JSON-RPC**
**File**: `browser-agent-server/nodejs/src/lib/BrowserAgentServer.js`

```javascript
async executeRequest(connection, request) {
  // Prepare RPC request
  const rpcRequest = {
    jsonrpc: "2.0",
    method: "evaluate",
    params: {
      requestId: "req-1234567890",
      name: "Dynamic Request",
      url: "about:blank",
      tool: "chat",
      input: { message: "How much is 5x7? Just respond with the number." },
      model: {
        main_model: { provider: "openai", model: "gpt-4", api_key: "sk-..." },
        mini_model: {...},
        nano_model: {...}
      },
      timeout: 30000
    },
    id: "rpc-abc123"
  };

  // Send via WebSocket to DevTools client
  const response = await connection.rpcClient.callMethod(
    connection.ws,
    "evaluate",
    rpcRequest.params,
    45000  // timeout
  );

  return response;
}
```

**RpcClient** (`browser-agent-server/nodejs/src/rpc-client.js`):
```javascript
async callMethod(ws, method, params, timeout) {
  return new Promise((resolve, reject) => {
    const id = uuidv4();

    // Store pending request
    this.pendingRequests.set(id, { resolve, reject, timeoutId });

    // Send JSON-RPC request
    ws.send(JSON.stringify({
      jsonrpc: "2.0",
      method: "evaluate",
      params: {...},
      id: id
    }));

    // Wait for response via handleResponse()
  });
}

handleResponse(message) {
  const response = JSON.parse(message);
  // {"jsonrpc": "2.0", "result": {...}, "id": "..."}

  const pending = this.pendingRequests.get(response.id);
  pending.resolve(response.result);
}
```

#### **Step 8: DevTools Frontend Executes Request**
**DevTools AI Chat Panel** (in browser):
```javascript
// Receives JSON-RPC request via WebSocket
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  if (data.jsonrpc === "2.0" && data.method === "evaluate") {
    // Execute the request
    handleEvaluateRequest(data.params, data.id);
  }
};

async handleEvaluateRequest(params, rpcId) {
  // 1. Extract parameters
  const { tool, input, model, timeout } = params;

  // 2. Based on tool type, execute appropriate action
  if (tool === "chat") {
    // Send message to AI model (GPT-4)
    const response = await callLLM({
      model: model.main_model.model,
      messages: [
        { role: "user", content: input.message }
      ]
    });

    // 3. Return result via JSON-RPC response
    ws.send(JSON.stringify({
      jsonrpc: "2.0",
      result: {
        success: true,
        response: response.choices[0].message.content,  // "35"
        tool: "chat",
        timestamp: Date.now()
      },
      id: rpcId
    }));
  }
}
```

#### **Step 9: Response Propagation**
The response flows back through the layers:

1. **DevTools** → sends JSON-RPC response via WebSocket
2. **RpcClient** → resolves pending promise with result
3. **executeRequest()** → returns result to API server
4. **handleResponsesRequest()** → formats response
5. **HTTP Response** → sent back to evaluation runner

**HTTP Response**:
```json
{
  "id": "chatcmpl-xyz789",
  "object": "response.object",
  "created": 1699564800,
  "model": "gpt-4",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "35"
      }
    }
  ],
  "metadata": {
    "client_id": "default",
    "tab_id": "E1A2B3C4D5E6F7G8"
  }
}
```

#### **Step 10: Validation with LLM Judge**
**File**: `evals/native/run.py`

```python
# Extract response text
response_text = api_response['response']  # "35"

# Validate using LLM Judge
judge_result = self.judge.judge(
    input_prompt="How much is 5x7? Just respond with the number.",
    response="35",
    criteria=[
        "Response contains the number 35",
        "Response is mathematically correct"
    ]
)

# Judge calls GPT-4 mini with structured prompt
# Returns: JudgeResult(passed=True, score=1.0, reasoning="...")
```

**LLM Judge** (`evals/lib/judge.py`):
```python
def judge(self, input_prompt, response, criteria):
    # Build judgment prompt
    prompt = f"""
    Evaluate this response:

    Input: {input_prompt}
    Response: {response}

    Criteria:
    - {criteria[0]}
    - {criteria[1]}

    Return JSON: {{"passed": true/false, "score": 0-1, "reasoning": "..."}}
    """

    # Call OpenAI
    result = self.client.chat.completions.create(
        model="gpt-4-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )

    # Parse and return
    judgment = json.loads(result.choices[0].message.content)
    return JudgeResult(
        passed=judgment["passed"],
        score=judgment["score"],
        reasoning=judgment["reasoning"]
    )
```

#### **Step 11: Report Results**
```python
# Print result
print(f"Status: PASS")
print(f"Score: 1.0")
print(f"Time: 2543ms")

# Save to CSV
with open('reports/test-simple.csv', 'w') as f:
    writer = csv.writer(f)
    writer.writerow(['eval_id', 'passed', 'score', 'execution_time_ms', ...])
    writer.writerow(['math-001', True, 1.0, 2543, ...])
```

---

## Key Technical Details

### 1. **Client ID System**

The system uses composite client IDs to track DevTools instances per tab:

- **Base Client ID**: `"default"` (or custom UUID from YAML config)
- **Tab ID**: Chrome target ID (e.g., `"E1A2B3C4D5E6F7G8"`)
- **Composite Client ID**: `"default:E1A2B3C4D5E6F7G8"`

**Why?**
- Each browser tab has its own DevTools instance
- Each DevTools connects as a separate WebSocket client
- Server needs to route requests to the correct tab

### 2. **Chrome DevTools Protocol (CDP) Integration**

**CDP Endpoint Discovery**:
```javascript
// Get browser-level CDP WebSocket URL
GET http://localhost:9223/json/version
// Returns: {"webSocketDebuggerUrl": "ws://localhost:9223/devtools/browser/..."}

// Get all targets (tabs)
GET http://localhost:9223/json
// Returns: [{"id": "E1A2B3C4...", "type": "page", "url": "...", ...}, ...]
```

**CDP Commands Used**:
- `Target.createTarget` - Create new tab
- `Target.closeTarget` - Close tab
- `Target.attachToTarget` - Attach to target for session
- `Page.navigate` - Navigate to URL
- `Page.captureScreenshot` - Take screenshot
- `Runtime.evaluate` - Execute JavaScript

**Example: Get Page HTML**:
```javascript
async getPageHTML(tabId) {
  // Attach to target and get session ID
  await this.sendCDPCommand('Target.attachToTarget', {
    targetId: tabId,
    flatten: true
  });

  // Execute JavaScript in page context
  const result = await this.sendCDPCommandToTarget(tabId, 'Runtime.evaluate', {
    expression: 'document.documentElement.outerHTML',
    returnByValue: true
  });

  return result.result.value;
}
```

### 3. **Model Configuration Hierarchy**

The system supports a three-tier model configuration:

- **main_model**: Primary model for complex reasoning (e.g., GPT-4)
- **mini_model**: Lighter model for simpler tasks (e.g., GPT-4-mini)
- **nano_model**: Smallest model for basic operations (e.g., GPT-3.5-turbo)

**Configuration Sources** (priority order):
1. Request-specific config (passed in API call)
2. Client connection config (configured via DevTools)
3. Global defaults (from `evals/config.yml`)
4. Hardcoded fallbacks

**Example Configuration**:
```yaml
# evals/config.yml
model:
  provider: openai
  main_model: gpt-4
  mini_model: gpt-4-mini
  nano_model: gpt-3.5-turbo
  api_key: ${OPENAI_API_KEY}
```

### 4. **Tool System**

The agent supports different tools for different task types:

**Tool: `chat`**
- Simple message-based interaction
- No browser manipulation
- Good for: Q&A, simple reasoning

**Tool: `search`** (implied)
- Web search capabilities
- Result extraction
- Good for: Information gathering

**Tool: `action`** (implied)
- Browser interaction (click, type, scroll)
- Element selection
- Good for: Task automation

**Tool: `screenshot`**
- Visual validation
- Element highlighting
- Good for: Visual regression testing

### 5. **Evaluation Types**

**Simple Judge**:
```yaml
validation:
  type: simple
  simple:
    expected_contains: "35"
```

**LLM Judge**:
```yaml
validation:
  type: llm-judge
  llm_judge:
    model: gpt-4-mini
    criteria:
      - "Response is factually correct"
      - "Response is concise"
```

**Vision Judge**:
```yaml
validation:
  type: vision-judge
  vision_judge:
    model: gpt-4-vision
    criteria:
      - "Element is visible on screen"
      - "Color is red (#FF0000)"
```

**WebArena Evaluators**:
- URL matching
- Element presence
- Text content validation
- Functional checks (e.g., item in cart)

---

## Deployment Configurations

### Local Development (`deployments/local/`)

**Characteristics**:
- Full GUI stack (Xorg, Mutter, WebRTC)
- Volume-mounted code for live development
- Persistent Chromium profile
- All debug ports exposed

**Key Files**:
- `Dockerfile` - Multi-stage build
- `docker-compose.yml` - Service orchestration
- `run-local.sh` - Alternative direct Docker run
- `scripts/init-container.sh` - Lock cleanup on startup

**Build & Run**:
```bash
cd deployments/local
make init          # Initialize submodules
make build         # Build images (~30 min first time)
make compose-up    # Start services in background
make test          # Run simple eval test
make logs          # View logs
make stop          # Stop services
```

### Cloud Run (`deployments/cloudrun/`)

**Characteristics**:
- No persistent storage (ephemeral containers)
- nginx reverse proxy (port 8080 required by Cloud Run)
- Twilio TURN server for WebRTC NAT traversal
- Cloud Build CI/CD pipeline

**Key Differences**:
- `nginx.conf` - Proxies all services through port 8080
- `cloudrun-wrapper.sh` - Custom entrypoint
- `deploy.sh` - Automated deployment with secrets
- `service-secrets.yaml` - Secret Manager integration

### WebArena Local (`deployments/local-webarena/`)

**Characteristics**:
- Extends local deployment
- DNS mapping for WebArena domains
- Network routing to WebArena infrastructure
- Custom domain resolution in Chromium

**Configuration** (`evals/.env`):
```bash
WEBARENA_HOST_IP=172.16.55.59
WEBARENA_NETWORK=172.16.55.0/24
```

**How it works**:
```bash
# init-container.sh generates Chromium flags
echo '--host-resolver-rules="MAP gitlab.com 172.16.55.59, MAP reddit.com 172.16.55.59, ..."' \
  > /mount/chromium-flags/flags

# Adds route to WebArena network
ip route add 172.16.55.0/24 via 172.17.0.1
```

---

## Supervisor Service Management

All services are managed by `supervisord`:

**Service Startup Order**:
```
1. dbus          (message bus)
2. xorg          (X11 display :1)
3. mutter        (window manager)
4. chromium      (browser with CDP on 9223)
5. neko          (WebRTC server)
6. nginx-devtools (DevTools UI on 8001)
7. browser-agent-server (API server)
8. kernel-images-api (recording on 444)
```

**Key Configuration**:
```ini
# deployments/commons/supervisor/services/chromium.conf
[program:chromium]
command=/path/to/chrome --remote-debugging-port=9223 \
  --custom-devtools-frontend=http://localhost:8001/ \
  --auto-open-devtools-for-tabs \
  --flag-switches-begin @/mount/chromium-flags/flags --flag-switches-end
environment=DISPLAY=":1"
autostart=true
autorestart=true
```

```ini
# deployments/commons/supervisor/services/browser-agent-server.conf
[program:browser-agent-server]
command=node /app/browser-agent-server/nodejs/start.js
environment=NODE_ENV="production",PORT="8082",API_PORT="8080",HOST="0.0.0.0",CDP_PORT="9223"
autostart=true
autorestart=true
```

---

## Communication Protocols

### 1. **HTTP REST API** (Port 8080)

**Endpoints**:
```
GET  /status              → Server health
GET  /clients             → List all clients and tabs
GET  /clients/{id}/tabs   → List client's tabs
POST /tabs/open           → Open new tab
POST /tabs/close          → Close tab
POST /v1/responses        → Execute automation request (OpenAI-compatible)
POST /page/content        → Get page HTML/text
POST /page/screenshot     → Capture screenshot
```

**Example `/v1/responses` request**:
```bash
curl -X POST http://localhost:8080/v1/responses \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Navigate to google.com and search for \"web automation\"",
    "url": "https://google.com",
    "wait_timeout": 5000,
    "model": {
      "main_model": {"provider": "openai", "model": "gpt-4", "api_key": "sk-..."}
    }
  }'
```

### 2. **WebSocket JSON-RPC 2.0** (Port 8082)

**Connection Flow**:
```
1. Client → Server: WebSocket connection
2. Server → Client: {"type": "welcome", "serverId": "...", ...}
3. Client → Server: {"type": "register", "clientId": "default:tab123", ...}
4. Server → Client: {"type": "registration_ack", "status": "auth_required", ...}
5. Client → Server: {"type": "auth_verify", "verified": true}
6. Server → Client: {"type": "registration_ack", "status": "accepted"}
7. Client → Server: {"type": "ready"}
```

**RPC Methods**:

**Server → Client**:
- `evaluate` - Execute automation request
- `navigate` - Navigate to URL
- `screenshot` - Capture screenshot
- `page_content` - Get page content

**Client → Server**:
- `configure_llm` - Configure LLM settings

**Example RPC Call**:
```json
// Server → Client
{
  "jsonrpc": "2.0",
  "method": "evaluate",
  "params": {
    "requestId": "req-123",
    "tool": "chat",
    "input": {"message": "What is 2+2?"},
    "model": {...},
    "timeout": 30000
  },
  "id": "rpc-abc"
}

// Client → Server (response)
{
  "jsonrpc": "2.0",
  "result": {
    "success": true,
    "response": "4",
    "tool": "chat"
  },
  "id": "rpc-abc"
}
```

### 3. **Chrome DevTools Protocol** (Port 9223)

**WebSocket-based protocol** for low-level browser control.

**Example Session**:
```javascript
// Connect
const ws = new WebSocket("ws://localhost:9223/devtools/browser/...");

// Create tab
ws.send(JSON.stringify({
  id: 1,
  method: "Target.createTarget",
  params: {url: "https://example.com", newWindow: false}
}));
// Response: {"id": 1, "result": {"targetId": "E1A2B3C4..."}}

// Navigate (requires session)
ws.send(JSON.stringify({
  id: 2,
  method: "Target.attachToTarget",
  params: {targetId: "E1A2B3C4...", flatten: true}
}));
// Response: {"id": 2, "result": {"sessionId": "F5G6H7I8..."}}

ws.send(JSON.stringify({
  id: 3,
  method: "Page.navigate",
  params: {url: "https://google.com"},
  sessionId: "F5G6H7I8..."
}));
```

---

## Security & Authentication

### Client Authentication

**Client Configuration** (`browser-agent-server/nodejs/clients/{uuid}.yaml`):
```yaml
client:
  id: 9907fd8d-92a8-4a6a-bce9-458ec8c57306
  name: DevTools Client
  secret_key: your-secret-key-here
  description: Browser Operator DevTools client
```

**Authentication Flow**:
1. Client sends registration with `clientId`
2. Server looks up client config from `clients/{clientId}.yaml`
3. Server sends `secret_key` to client for verification
4. Client verifies secret key matches (local storage or environment)
5. Client sends `auth_verify` with `verified: true`
6. Server accepts connection and marks as `registered: true`

**Why this design?**
- DevTools clients don't have server-side storage
- Secret verification happens client-side
- Prevents unauthorized clients from connecting
- Each tab gets its own authenticated connection

### API Key Management

**Model API Keys**:
- Passed in request config or global config
- Never logged (redacted in logs)
- Environment variable fallback: `OPENAI_API_KEY`

**Example Redaction**:
```javascript
const redact = (mk) => ({
  ...mk,
  api_key: mk?.api_key ? `${String(mk.api_key).slice(0, 4)}...` : undefined
});

logger.info('Model config:', {
  main_model: redact(config.main_model)
});
// Logs: {main_model: {provider: "openai", model: "gpt-4", api_key: "sk-p..."}}
```

---

## Performance Characteristics

### Build Times

**First Build** (cold cache):
- DevTools frontend: ~25-30 minutes
- Main container: ~15-20 minutes
- Total: ~40-50 minutes

**Rebuild** (warm cache):
- DevTools changes only: ~5-10 minutes
- Code changes only: ~2-5 minutes
- Dockerfile changes: ~10-15 minutes

### Container Resource Usage

**Typical**:
- CPU: 2-4 cores (Chromium + Node.js)
- Memory: 4-6 GB (Chromium is memory-intensive)
- Disk: ~2 GB (base images + cache)

**With WebRTC streaming**:
- CPU: +20% (video encoding)
- Network: ~2-5 Mbps (video stream)

### Request Latency

**Simple Chat Request** (math question):
- Tab creation: ~100-200ms
- DevTools connection: ~50-100ms
- LLM call (GPT-4): ~1000-3000ms
- Total: ~1500-3500ms

**Web Navigation** (open google.com):
- Tab creation: ~100-200ms
- Page load: ~500-2000ms (depends on site)
- DOM interaction: ~50-200ms
- Total: ~1000-3000ms

**Screenshot Capture**:
- CDP screenshot command: ~200-500ms
- Base64 encoding: ~50-100ms
- Total: ~300-700ms

---

## Common Development Workflows

### 1. **Modify Browser Agent Server Code**

**With Docker Compose** (code is volume-mounted):
```bash
# Edit code
vim browser-agent-server/nodejs/src/api-server.js

# Restart service
cd deployments/local
docker-compose restart browser-agent-server

# Test
make test
```

**With Direct Docker Run** (code is baked in):
```bash
# Edit code
vim browser-agent-server/nodejs/src/api-server.js

# Rebuild and restart
cd deployments/local
make rebuild
make run
```

### 2. **Modify DevTools Frontend**

```bash
# Edit DevTools code
vim submodules/browser-operator-core/front_end/panels/ai_chat/ChatPanel.ts

# Rebuild DevTools image
cd deployments/local
make rebuild-devtools

# Restart container
docker-compose down
docker-compose up -d

# OR with run-local.sh
make run
```

### 3. **Create New Evaluation**

```bash
# Create YAML file
vim evals/native/data/my-category/my-eval-001.yaml
```

```yaml
id: "my-eval-001"
name: "My Test Evaluation"
enabled: true

target:
  url: "https://example.com"
  wait_for: "networkidle"
  wait_timeout: 3000

tool: "chat"
timeout: 30000

input:
  message: "Describe what you see on this page"

validation:
  type: "llm-judge"
  llm_judge:
    model: "gpt-4-mini"
    criteria:
      - "Response mentions the page content"
      - "Response is coherent and detailed"
```

```bash
# Run evaluation
cd evals/native
python3 run.py --path my-category/my-eval-001.yaml --verbose
```

### 4. **Debug WebSocket Communication**

```bash
# View browser-agent-server logs
docker logs -f kernel-browser-extended | grep -E "RPC|WebSocket"

# View all logs
docker logs -f kernel-browser-extended

# Connect to container
docker exec -it kernel-browser-extended bash

# Check services
supervisorctl status

# Restart service
supervisorctl restart browser-agent-server
```

### 5. **Test CDP Commands Directly**

```bash
# Get CDP endpoint
curl http://localhost:9223/json/version

# List all targets
curl http://localhost:9223/json

# Use websocat to send CDP commands
websocat ws://localhost:9223/devtools/browser/...
> {"id":1,"method":"Target.createTarget","params":{"url":"https://example.com"}}
```

---

## Troubleshooting Guide

### Problem: "Profile appears to be in use"

**Cause**: Chromium lock files persisting across restarts

**Solution**: Automatic cleanup via `init-container.sh`
- Cleans `SingletonLock`, `SingletonSocket`, `SingletonCookie`
- Runs on every container start
- No manual intervention needed

### Problem: "Server is already active for display 1"

**Cause**: X11 lock files persisting in `/tmp`

**Solution**: `/tmp` mounted as tmpfs in docker-compose
```yaml
tmpfs:
  - /tmp
  - /dev/shm
```

### Problem: "Failed to connect to CDP"

**Cause**: CDP port mismatch

**Solution**: Ensure `CDP_PORT=9223` in all configs
- Check `deployments/commons/supervisor/services/browser-agent-server.conf`
- Check Chromium startup args: `--remote-debugging-port=9223`
- Verify: `curl http://localhost:9223/json/version`

### Problem: "Module not found: js-yaml"

**Cause**: Missing Node.js dependencies

**Solution**:
```bash
cd browser-agent-server/nodejs
npm install
```

### Problem: "Cannot connect to API server"

**Cause**: Server not running or wrong port

**Solution**:
```bash
# Check if server is running
docker ps | grep kernel-browser

# Check browser-agent-server logs
docker logs kernel-browser-extended | grep "API server started"

# Verify port mapping
docker port kernel-browser-extended

# Test endpoint
curl http://localhost:8080/status
```

### Problem: Evaluation fails with timeout

**Cause**: LLM request takes too long

**Solution**: Increase timeout in YAML
```yaml
timeout: 60000  # 60 seconds instead of 30
```

Or in code:
```javascript
const result = await executeRequest(connection, {
  ...request,
  timeout: 60000
});
```

---

## Architecture Insights

### Design Decisions

**1. Why WebSocket + HTTP dual API?**
- **WebSocket**: Real-time bidirectional communication with DevTools
- **HTTP**: Simple request/response for evaluations and external tools
- Separation of concerns: DevTools clients vs. automation clients

**2. Why composite client IDs?**
- Each tab has independent DevTools instance
- Server needs to route requests to specific tabs
- Format: `{baseClientId}:{tabId}` enables hierarchy
- Example: `default:E1A2B3C4` = base client "default", tab "E1A2B3C4"

**3. Why use CDP instead of Puppeteer/Playwright?**
- Direct control without extra abstraction layer
- Integration with custom DevTools frontend
- Lower overhead (no separate browser launch)
- More flexibility for custom automation

**4. Why three-tier model configuration?**
- Cost optimization: Use expensive models only when needed
- Latency optimization: Fast models for simple tasks
- Flexibility: Override per-request or use defaults

**5. Why LLM-as-a-Judge validation?**
- Flexible evaluation criteria (not just string matching)
- Natural language criteria specification
- Handles nuanced correctness (e.g., "answer is polite and accurate")
- Scales to complex evaluations (e.g., "UI matches design mockup")

### Scalability Considerations

**Current Architecture**:
- Single Chromium instance per container
- Multiple tabs per instance
- Each tab = separate DevTools client connection

**Scaling Options**:

**Horizontal** (multiple containers):
```
Load Balancer
├─ Container 1 (Chromium + Agent Server)
├─ Container 2 (Chromium + Agent Server)
└─ Container N (Chromium + Agent Server)
```

**Vertical** (more tabs per instance):
- Current limit: ~10-20 tabs per Chromium instance
- Limited by memory (each tab ~100-300 MB)
- Limited by CDP connection overhead

**Hybrid** (container pool + queue):
```
Request Queue
   ↓
Container Pool Manager
   ├─ Container 1 (idle)
   ├─ Container 2 (busy: 3 tabs)
   └─ Container 3 (busy: 5 tabs)
```

---

## Future Enhancements

Based on architecture analysis, potential improvements:

### 1. **Request Queueing**
Current: Requests are synchronous (one at a time per tab)
Enhanced: Queue system with priority and parallel execution

```javascript
class RequestQueue {
  async enqueue(request, priority) {
    // Add to priority queue
    // Allocate to available tab
    // Execute when ready
  }
}
```

### 2. **Tab Pooling**
Current: Create new tab for each request
Enhanced: Reuse tabs from pool

```javascript
class TabPool {
  async acquireTab() {
    // Get idle tab or create new
  }

  async releaseTab(tabId) {
    // Reset state and return to pool
  }
}
```

### 3. **Persistent Sessions**
Current: Each request is independent
Enhanced: Support for multi-turn conversations

```javascript
POST /v1/sessions
POST /v1/sessions/{sessionId}/messages
GET  /v1/sessions/{sessionId}/history
```

### 4. **Streaming Responses**
Current: Complete response returned at end
Enhanced: SSE or WebSocket streaming

```javascript
const stream = await client.sendRequest({
  input: "Long task...",
  stream: true
});

for await (const chunk of stream) {
  console.log(chunk.delta);
}
```

### 5. **Multi-Model Orchestration**
Current: Single model per request
Enhanced: Automatic model selection based on task

```javascript
{
  "input": "Complex reasoning task",
  "auto_model_selection": true,
  "model_preferences": {
    "reasoning": "gpt-4",
    "classification": "gpt-4-mini",
    "extraction": "gpt-3.5-turbo"
  }
}
```

---

## Conclusion

This web agent system is a well-architected browser automation platform that combines:

✅ **Low-level browser control** (CDP for precise automation)
✅ **High-level AI integration** (LLM-powered decision making)
✅ **Dual interaction modes** (Interactive UI + Programmatic API)
✅ **Comprehensive evaluation framework** (YAML-based tests + LLM judges)
✅ **Production-ready deployment** (Local development + Cloud Run)

**Key Strengths**:
- Clean separation of concerns (browser, server, evals)
- Flexible model configuration (three-tier system)
- Robust communication (WebSocket + HTTP + CDP)
- Excellent developer experience (Docker Compose + make targets)
- Strong evaluation capabilities (LLM/Vision judges + WebArena)

**Ideal Use Cases**:
- Automated browser testing with AI assistance
- Web scraping with intelligent navigation
- UI/UX evaluation and regression testing
- Research on web agent capabilities (WebArena benchmarks)
- Interactive debugging with AI copilot (DevTools chat panel)

The architecture is modular, extensible, and well-documented, making it suitable for both research and production use.
