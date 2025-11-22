# Claude Code - Technical Documentation

## Project Overview

This project extends the kernel-images Chromium browser environment with:
- **Browser Operator DevTools**: Custom DevTools frontend with AI chat panel
- **Eval Server**: HTTP/WebSocket API for browser automation and evaluation
- **Local Development**: Docker Compose setup for rapid iteration
- **Cloud Deployment**: Google Cloud Run deployment (legacy)

## Architecture

### Core Components

1. **Chromium Browser** (headful, GUI via WebRTC)
   - CDP (Chrome DevTools Protocol) on port 9223
   - Custom DevTools frontend at http://localhost:8001/
   - Auto-opens DevTools for all tabs

2. **Eval Server** (Node.js)
   - HTTP API on port 8080 (`/v1/responses`, `/page/content`, `/page/screenshot`)
   - WebSocket API on port 8082 (JSON-RPC 2.0)
   - Manages browser tabs and automation

3. **WebRTC Streaming** (Neko)
   - Live browser view on port 8000
   - WebRTC control interface on port 8081

4. **DevTools Frontend** (nginx)
   - Browser Operator custom DevTools on port 8001
   - Includes AI chat panel and automation features

5. **Recording API** (kernel-images)
   - Screen recording on port 444

### Service Dependencies

```
supervisord
├── xorg (X11 display :1)
├── mutter (window manager)
├── dbus (message bus)
├── chromium (browser + CDP port 9223)
├── neko (WebRTC on ports 8000, 8081)
├── kernel-images-api (recording on port 444)
├── eval-server (HTTP 8080, WS 8082)
└── nginx-devtools (DevTools UI on port 8001)
```

## Directory Structure

```
web-agent/
├── browser-operator-core/      # Submodule: DevTools frontend source
├── kernel-images/              # Submodule: Base browser environment
├── submodules/                 # Git submodules
│   └── webarena/               # WebArena benchmark (for webarena evals)
├── deployments/                # Deployment configurations
│   ├── cloudrun/               # Google Cloud Run deployment
│   │   ├── deploy.sh           # Cloud deployment script
│   │   ├── cloudbuild.yaml     # CI/CD pipeline config
│   │   ├── service.yaml        # Cloud Run service definition
│   │   ├── service-secrets.yaml # Service with Secret Manager
│   │   ├── cloudrun-wrapper.sh # Cloud Run entrypoint
│   │   ├── supervisord-cloudrun.conf # Supervisor for Cloud Run
│   │   ├── nginx.conf          # Reverse proxy config
│   │   ├── Dockerfile          # Cloud Run Docker build
│   │   └── scripts/            # Cloud Run specific scripts
│   ├── local/                  # Local deployment
│   │   ├── run-local.sh        # Interactive Docker run script
│   │   ├── docker-compose.yml  # Docker Compose config
│   │   ├── Dockerfile          # Local Docker build
│   │   ├── Makefile            # Local build commands
│   │   └── scripts/            # Local specific scripts
│   │       ├── init-container.sh   # Auto-cleanup of lock files
│   │       └── start-chromium.sh   # Chromium startup script
│   ├── local-webarena/         # Local deployment for WebArena evals
│   │   ├── run-local.sh        # WebArena-specific run script
│   │   ├── docker-compose.yml  # Docker Compose config
│   │   ├── Dockerfile          # WebArena Docker build
│   │   ├── Makefile            # WebArena build commands
│   │   └── scripts/            # WebArena specific scripts
│   └── commons/                # Shared configs across deployments
│       ├── nginx/              # Nginx configurations
│       │   └── nginx-devtools.conf # DevTools nginx config
│       └── supervisor/         # Supervisor configurations
│           ├── services/       # Service configs (local)
│           │   ├── chromium.conf           # Auto-open DevTools
│           │   ├── browser-agent-server.conf # Browser agent with CDP_PORT=9223
│           │   ├── neko.conf
│           │   └── nginx-devtools.conf
│           └── services-cloudrun/  # Service configs (cloud run)
│               └── browser-agent-server.conf
├── submodules/                 # Git submodules
│   ├── browser-operator-core/  # Browser Operator DevTools + Agent Server
│   │   ├── agent-server/       # Agent server (HTTP/WebSocket API)
│   │   │   └── nodejs/         # Node.js implementation
│   │   │       ├── src/
│   │   │       │   ├── api-server.js   # HTTP REST API
│   │   │       │   ├── client-manager.js  # Client management
│   │   │       │   └── lib/    # Core libraries
│   │   │       ├── start.js    # Server entrypoint
│   │   │       └── package.json
│   │   └── front_end/          # DevTools frontend source
│   ├── kernel-images/          # Base browser environment
│   └── webarena/               # WebArena benchmark (for webarena evals)
├── evals/                      # Evaluation framework
│   ├── .env                    # API keys (gitignored, copy from .env.example)
│   ├── config.yml              # Global eval configuration
│   ├── lib/                    # Shared evaluation library
│   │   ├── eval_loader.py      # YAML evaluation loader
│   │   ├── api_client.py       # HTTP client for agent server
│   │   ├── judge.py            # LLMJudge, VisionJudge, SimpleJudge
│   │   ├── webarena_adapter.py # WebArena task adapter
│   │   └── webarena_evaluators.py # WebArena evaluators
│   ├── native/                 # Native evaluation runner
│   │   ├── run.py              # Main runner script
│   │   └── data/               # Native evaluation YAML files
│   │       ├── test-simple/
│   │       ├── action-agent/
│   │       ├── web-task-agent/
│   │       └── ...
│   └── webarena/               # WebArena evaluation runner
│       ├── run_webarena.py     # WebArena runner script
│       ├── data/               # WebArena-specific data
│       └── webarena-local/     # Local WebArena environment setup
├── Dockerfile.devtools         # DevTools frontend build
├── Dockerfile.kernel-cloud     # Kernel cloud build
├── CLAUDE.md                   # This file
└── README.md                   # User documentation
```

## Key Files and What They Do

### deployments/local/Dockerfile
Multi-stage build that:
1. Copies pre-built DevTools from `browser-operator-devtools:latest`
2. Builds agent server from `submodules/browser-operator-core/agent-server/nodejs` with `npm install`
3. Builds kernel-images Go API
4. Builds WebRTC client
5. Compiles custom Xorg drivers
6. Assembles final Ubuntu 22.04 image with all components
7. Adds init script for automatic lock cleanup

**Critical sections:**
- Copies `deployments/local/scripts/init-container.sh` for lock cleanup
- Creates `/entrypoint.sh` wrapper
- Sets entrypoint to run init before main wrapper

### deployments/local/docker-compose.yml
Configures container with:
- Port mappings for all services (8000-8082, 9222, 444)
- Volume mounts: recordings, chromium-data
- tmpfs: `/dev/shm` and `/tmp` (prevents lock file persistence)
- Environment: `CHROMIUM_FLAGS` with custom DevTools frontend
- Agent server code is baked into the image (not volume-mounted)

**Recent fixes:**
- Added missing ports 8000, 8001, 8081, 8082
- Added `/tmp` tmpfs mount to prevent X11 lock persistence
- Added `--custom-devtools-frontend=http://localhost:8001/`

### deployments/*/scripts/init-container.sh
Runs on every container start to clean:
- Chromium lock files (`SingletonLock`, `SingletonSocket`, `SingletonCookie`)
- X11 lock files (`/tmp/.X*-lock`)

This prevents "profile in use" and "display already active" errors.

Available in all deployment types: `local/`, `local-webarena/`, `cloudrun/`

### submodules/browser-operator-core/agent-server/nodejs/src/api-server.js
HTTP REST API with endpoints:
- `POST /v1/responses` - Execute browser automation tasks
- `POST /page/content` - Get page HTML/text content
- `POST /page/screenshot` - Capture screenshots
- `POST /page/execute` - Execute JavaScript in page context
- `GET /status` - Health check

### deployments/commons/supervisor/services/browser-agent-server.conf
**Critical environment variables:**
```ini
environment=NODE_ENV="production",PORT="8082",API_PORT="8080",HOST="0.0.0.0",CDP_PORT="9223"
```

Note: CDP_PORT must be 9223 (not 9222) to match Chromium configuration.

### deployments/local/Makefile (and deployments/local-webarena/Makefile)
Key targets:
- `make init` - Initialize git submodules
- `make build-devtools` - Build DevTools base (slow, ~30 min, cached)
- `make rebuild-devtools` - Fast rebuild with local changes
- `make build` - Build main image (auto-builds DevTools if missing)
- `make compose-up` - Start with docker-compose (background)
- `make run` - Start with run-local.sh (interactive)
- `make test` - Verify API and run simple eval
- `make stop` - Stop all containers
- `make clean` - Clean up everything

### deployments/local/run-local.sh
Interactive Docker run script that:
- Sources kernel-images common build variables
- Creates local recordings directory
- Configures Chromium data persistence (customizable with `CHROMIUM_DATA_HOST`)
- **Cleans lock files from host before starting**
- Builds docker run arguments with all port mappings
- Supports `URLS` environment variable to open URLs on startup
- Uses custom DevTools frontend flag
- Runs container with `docker run -d` (detached but logs visible via docker logs)

**Key difference from docker-compose:**
- Lock cleanup happens on HOST before container starts
- Browser-agent-server code is NOT volume-mounted (baked into image)
- More flexible for custom configurations via environment variables
- Better for seeing startup issues and debugging

### deployments/cloudrun/
Contains all Google Cloud Run deployment files:
- `deploy.sh` - Automated deployment script with Twilio TURN setup
- `cloudbuild.yaml` - CI/CD pipeline for Cloud Build
- `service.yaml` / `service-secrets.yaml` - Cloud Run service definitions
- `cloudrun-wrapper.sh` - Cloud Run container entrypoint
- `supervisord-cloudrun.conf` - Supervisor configuration for Cloud Run
- `nginx.conf` - Reverse proxy for Cloud Run port requirements
- `Dockerfile` - Cloud Run specific Docker build
- `scripts/` - Cloud Run specific scripts

### deployments/commons/nginx/
Nginx configuration files:
- `nginx-devtools.conf` - DevTools UI server config (used by all deployments)

### deployments/commons/supervisor/
Supervisor configuration files:
- `services/` - Service configs for local deployments
- `services-cloudrun/` - Service configs for cloud run deployments

## Common Issues and Solutions

### 1. Chromium Profile Lock Errors
**Symptom:** "The profile appears to be in use by another Chromium process"

**Solution:** Now handled automatically by `deployments/*/scripts/init-container.sh`
- Runs on every container start
- Cleans lock files before services start
- No manual intervention needed

### 2. X11 Display Lock Errors
**Symptom:** "Server is already active for display 1"

**Solution:** Fixed by adding `/tmp` to tmpfs in `deployments/local/docker-compose.yml`
- `- /tmp` in tmpfs section
- Prevents lock files from persisting across restarts

### 3. CDP Connection Failures
**Symptom:** "Failed to connect to Chrome DevTools Protocol"

**Solution:** Ensure CDP_PORT=9223 in `deployments/commons/supervisor/services/browser-agent-server.conf`
- Chromium runs on port 9223 (not 9222)
- Check logs: `docker logs kernel-browser-extended | grep CDP`

### 4. Module Not Found Errors
**Symptom:** "Cannot find module 'js-yaml'" or missing dependencies

**Solution:**
- Agent server code comes from `submodules/browser-operator-core/agent-server/nodejs/`
- Dependencies are installed during Docker build via `npm install`
- Rebuild the image if dependencies are missing: `make rebuild`

### 5. Docker Volume Caching on macOS
**Symptom:** File changes not visible in running container with docker-compose

**Solution:** Completely recreate container
```bash
cd deployments/local
docker-compose down
docker-compose up -d
```
macOS Docker has aggressive volume caching.

**Note:** This only affects `make compose-up`. With `make run`, code is baked into the image, so you must rebuild to see changes.

### 6. Port Already in Use
**Symptom:** "Ports are not available: UDP 56065 already in use"

**Solution:**
```bash
# Remove existing container
docker rm -f kernel-browser-extended

# Then start with your preferred method
make compose-up  # OR make run
```

## Deployment Workflows

### Two Local Deployment Options

#### Option 1: Docker Compose (Recommended for Development)

**Advantages:**
- Background operation
- Easy restart without rebuilding
- Managed by docker-compose
- Better for long-running development

**Note:** Agent server code is baked into the image, so rebuilds are needed for code changes

**Usage:**
```bash
# First time setup
make init                    # Initialize submodules
make build                   # Build images (~30 min first time)

# Start services in background
make compose-up

# Verify
make test                    # Run simple eval test

# View logs
make logs                    # Follow all logs

# Iterate on agent server code (REQUIRES REBUILD)
vim submodules/browser-operator-core/agent-server/nodejs/src/api-server.js
make rebuild
docker-compose down
docker-compose up -d

# Stop
make stop                    # OR docker-compose down
```

#### Option 2: Direct Docker Run (Interactive Mode)

**Advantages:**
- Live logs in terminal
- Better for debugging
- See all output immediately
- Good for quick testing
- Chromium data location customizable

**Disadvantages:**
- Requires rebuild for code changes
- Runs in foreground (blocks terminal)
- No volume mount for eval-server

**Usage:**
```bash
# First time setup
make init                    # Initialize submodules
make build                   # Build images (~30 min first time)

# Start in interactive mode (logs to stdout)
make run

# In another terminal, verify
make test

# Stop
# Press Ctrl+C in terminal running 'make run'
# OR: docker stop kernel-browser-extended

# Iterate on eval-server code (REQUIRES REBUILD)
vim eval-server/nodejs/src/api-server.js
make rebuild
make run                     # Restart after rebuild
```

### Comparison: `make run` vs `make compose-up`

| Aspect | `make run` | `make compose-up` |
|--------|-----------|-------------------|
| **Logs** | Live in terminal | Background, use `make logs` |
| **Stopping** | Ctrl+C or docker stop | `make stop` |
| **Agent server code** | Baked into image, rebuild needed | Baked into image, rebuild needed |
| **DevTools code** | Baked into image, rebuild needed | Baked into image, rebuild needed |
| **Best for** | Debugging, seeing startup issues | Development iteration |
| **Script** | `run-local.sh` | `docker-compose.yml` |
| **Data location** | Easy to customize with env vars | Set in compose file or env var |
| **Lock cleanup** | Script cleans host before start | Container init cleans on start |
| **URLs on startup** | `URLS="..." make run` | Edit compose file |

### Rebuild After Changes

#### With Docker Compose:

```bash
cd deployments/local

# Agent server changes (REQUIRES REBUILD)
vim ../../submodules/browser-operator-core/agent-server/nodejs/src/api-server.js
make rebuild
docker-compose down
docker-compose up -d

# DevTools changes
vim ../../browser-operator-core/front_end/panels/ai_chat/...
make rebuild-devtools        # Fast rebuild
docker-compose down
docker-compose up -d

# Dockerfile changes
make rebuild                 # Full rebuild
make compose-up
```

#### With Direct Docker Run:

```bash
cd deployments/local

# ANY code changes (browser-agent-server OR DevTools)
make rebuild                 # Must rebuild
# Press Ctrl+C in terminal running 'make run'
make run                     # Restart

# DevTools only changes (faster)
make rebuild-devtools        # Fast rebuild
# Press Ctrl+C
make run

# Dockerfile changes
make rebuild                 # Full rebuild
make run
```

### Advanced run-local.sh Options

```bash
# Custom Chromium data directory
CHROMIUM_DATA_HOST=/custom/path make run

# Ephemeral mode (no data persistence)
CHROMIUM_DATA_HOST="" make run

# Open URLs on startup
URLS="https://google.com https://github.com" make run

# Combine options
CHROMIUM_DATA_HOST=/tmp/browser URLS="https://example.com" make run
```

## Important Notes

### Agent Server Location
The agent server code is in: `submodules/browser-operator-core/agent-server/nodejs/`

This is the main server that handles browser automation requests via HTTP/WebSocket APIs.

**Note:** The submodule must be on the `feat/js-eval-endpoint` branch to have the `/page/execute` endpoint.

### CDP Port is 9223, Not 9222
The default Chrome DevTools port is 9222, but this project uses 9223.

Check these files:
- `deployments/commons/supervisor/services/browser-agent-server.conf` - Must have `CDP_PORT="9223"`
- Chromium startup config uses port 9223

### Dependencies in submodules/browser-operator-core/agent-server/nodejs/
Required packages:
- ws (WebSocket server)
- uuid (ID generation)
- winston (logging)
- js-yaml (YAML parsing)
- dotenv (environment variables)

All managed by `package.json` and `npm install` during Docker build.

### Lock File Cleanup is Automatic
After implementing `deployments/*/scripts/init-container.sh`, you should never need to manually clean lock files again. The script runs on every container start.

## WebArena Configuration

The system supports running **WebArena benchmark evaluations** (812 tasks across 7 self-hosted websites). WebArena requires special network configuration to route specific domains to a custom IP address.

### Configuration Overview

WebArena configuration is **completely optional** and **pluggable**:
- **Without configuration**: System works normally with standard DNS resolution
- **With configuration**: Domains like `gitlab.com`, `reddit.com`, `wikipedia.org` route to your WebArena deployment IP

### Environment Variables

All WebArena configuration is done via environment variables in `evals/.env`:

```bash
# WebArena Infrastructure Configuration (Optional)
# Leave empty to disable WebArena routing

# IP address where WebArena sites are hosted (e.g., 172.16.55.59)
WEBARENA_HOST_IP=

# Network CIDR for routing to WebArena infrastructure (e.g., 172.16.55.0/24)
WEBARENA_NETWORK=

# WebArena Site URLs (Optional - for custom deployments)
SHOPPING=http://onestopmarket.com
SHOPPING_ADMIN=http://onestopmarket.com/admin
REDDIT=http://reddit.com
GITLAB=http://gitlab.com
WIKIPEDIA=http://wikipedia.org
MAP=http://openstreetmap.org
HOMEPAGE=http://homepage.com
```

### How It Works

When `WEBARENA_HOST_IP` and `WEBARENA_NETWORK` are set:

1. **DNS Mapping** (`scripts/init-container.sh`):
   - Generates Chromium `--host-resolver-rules` flag dynamically
   - Maps WebArena domains to specified IP address
   - File: `@mount/chromium-flags/flags` (auto-generated on container start)

2. **Network Routing** (`scripts/init-container.sh`):
   - Adds route to WebArena network via Docker host gateway
   - Enables container to reach hosts on the specified network
   - Example: `ip route add 172.16.55.0/24 via <gateway>`

3. **Environment Propagation**:
   - Variables passed from `evals/.env` to container
   - Available in both `docker-compose.yml` and `run-local.sh`
   - Python scripts use `os.environ.get()` for site URLs

### Setting Up WebArena

**Step 1: Configure environment variables**

```bash
# Copy example file
cd evals
cp .env.example .env

# Edit .env and set WebArena configuration
vim .env
```

Add:
```bash
WEBARENA_HOST_IP=172.16.55.59
WEBARENA_NETWORK=172.16.55.0/24
```

**Step 2: Start container with configuration**

The configuration is automatically loaded:

```bash
# With docker-compose (reads .env automatically)
make compose-up

# With run-local.sh (sources evals/.env)
make run
```

**Step 3: Verify configuration**

Check container logs to confirm WebArena routing is enabled:

```bash
docker logs kernel-browser-extended | grep -i webarena
```

You should see:
```
🌐 [init] Configuring WebArena DNS mapping to 172.16.55.59...
🌐 [init] Adding route to 172.16.55.0/24 via 172.17.0.1...
```

**Step 4: Run WebArena evaluations**

```bash
cd evals
python3 run_webarena.py --task-id 1 --verbose
```

### Disabling WebArena (Default Behavior)

To disable WebArena routing, simply leave the variables empty in `evals/.env`:

```bash
WEBARENA_HOST_IP=
WEBARENA_NETWORK=
```

Or remove them entirely. The system will:
- Skip DNS mapping in Chromium flags
- Skip network route addition
- Use normal DNS resolution for all domains
- Log: `ℹ️ [init] WEBARENA_HOST_IP not configured, skipping WebArena routing`

### Deployment-Specific Configuration

When deploying to different environments (local, cloud, staging), you can use different IP addresses:

**Local WebArena (Docker network)**
```bash
WEBARENA_HOST_IP=172.16.55.59
WEBARENA_NETWORK=172.16.55.0/24
```

**Cloud WebArena (external IP)**
```bash
WEBARENA_HOST_IP=34.123.45.67
WEBARENA_NETWORK=34.123.45.0/24
```

**Public sites only (no routing)**
```bash
WEBARENA_HOST_IP=
WEBARENA_NETWORK=
```

### Files Affected by WebArena Configuration

1. **evals/.env.example** - Environment variable template
2. **deployments/*/scripts/init-container.sh** - Dynamic flag generation and routing
3. **deployments/local-webarena/docker-compose.yml** - Environment variable propagation
4. **deployments/local-webarena/run-local.sh** - Environment loading for direct Docker run
5. **evals/webarena/login_webarena_sites.py** - Uses env vars for site URLs
6. **@mount/chromium-flags/flags** - Auto-generated based on `WEBARENA_HOST_IP`

### Troubleshooting

**WebArena domains not resolving to custom IP:**
- Check `WEBARENA_HOST_IP` is set in `evals/.env`
- Restart container to regenerate flags file
- Verify flags file: `cat @mount/chromium-flags/flags | grep host-resolver-rules`

**Container cannot reach WebArena network:**
- Check `WEBARENA_NETWORK` is set correctly
- Ensure Docker has network access to that subnet
- Verify route: `docker exec kernel-browser-extended ip route | grep 172.16.55`

**Evaluations failing with network errors:**
- Confirm WebArena infrastructure is running and accessible
- Test connectivity: `docker exec kernel-browser-extended ping 172.16.55.59`
- Check firewall rules between Docker host and WebArena network

## Testing

### Quick API Test
```bash
cd deployments/local
make test
```

Runs `evals/native/data/test-simple/math-001.yaml` which:
1. Checks API endpoint health
2. Sends simple math question via `/v1/responses`
3. Validates response using SimpleJudge
4. Reports PASS/FAIL

### Running Specific Evals

**Native evals:**
```bash
cd evals/native
python3 run.py --path data/web-task-agent/flight-001.yaml --verbose
```

**WebArena evals:**
```bash
cd evals/webarena
python3 run_webarena.py --task-id 1 --verbose
```

### Manual API Testing
```bash
# Health check
curl http://localhost:8080/status

# Execute task
curl -X POST http://localhost:8080/v1/responses \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Navigate to google.com",
    "url": "about:blank",
    "wait_timeout": 5000,
    "model": {
      "main_model": {"provider": "openai", "model": "gpt-4", "api_key": "..."}
    }
  }'

# Get page content
curl -X POST http://localhost:8080/page/content \
  -H "Content-Type: application/json" \
  -d '{"clientId": "test", "tabId": "tab-001", "format": "html"}'

# Capture screenshot
curl -X POST http://localhost:8080/page/screenshot \
  -H "Content-Type: application/json" \
  -d '{"clientId": "test", "tabId": "tab-001", "fullPage": false}'
```

## Access Points

### Local Docker Compose Deployment

| Service | URL | Purpose |
|---------|-----|---------|
| WebRTC Client | http://localhost:8000 | Live browser view with mouse/keyboard control |
| Enhanced DevTools UI | http://localhost:8001 | Custom DevTools with AI chat panel |
| Eval Server HTTP API | http://localhost:8080 | REST API for automation |
| WebRTC Neko | http://localhost:8081 | WebRTC control interface |
| Eval Server WebSocket | ws://localhost:8082 | JSON-RPC 2.0 bidirectional API |
| Chrome DevTools Protocol | http://localhost:9222/json | CDP endpoint list |
| Recording API | http://localhost:444/api | Screen recording controls |

## Recent Changes Summary

### Repository Restructuring
1. **Reorganized deployments** - Moved to `deployments/` with separate configs for:
   - `cloudrun/` - Google Cloud Run deployment
   - `local/` - Local development deployment
   - `local-webarena/` - WebArena-specific deployment
   - `commons/` - Shared configs (nginx, supervisor)

2. **Reorganized evaluations** - Moved to `evals/` with separate runners:
   - `native/` - Native evaluation runner with YAML-based tests
   - `webarena/` - WebArena benchmark runner
   - `lib/` - Shared evaluation library (judges, adapters, loaders)

3. **Consolidated agent server** - Now using `submodules/browser-operator-core/agent-server/` directly (removed duplicate `browser-agent-server/` directory)

4. **Moved WebArena config files** - Task configurations moved to in-repo location:
   - New location: `evals/webarena/config_files/` (preferred)
   - Legacy location: `submodules/webarena/config_files/` (fallback)
   - `WebArenaTaskLoader` now tries new location first

### Technical Fixes
1. **Fixed docker-compose.yml** - Added missing port mappings (8000, 8001, 8081, 8082)
2. **Fixed tmpfs mounts** - Added `/tmp` to prevent X11 lock persistence
3. **Added automatic lock cleanup** - `deployments/*/scripts/init-container.sh` runs on every start
4. **Updated Chromium flags** - Added `--custom-devtools-frontend=http://localhost:8001/`
5. **Fixed CDP port** - Set `CDP_PORT="9223"` in agent server supervisor config
6. **Added /page/execute endpoint** - JavaScript execution endpoint available in `feat/js-eval-endpoint` branch
6. **Created make test** - Quick verification of API functionality
7. **Fixed path resolution** - `eval_loader.py` now supports new `evals/native/data/` structure
