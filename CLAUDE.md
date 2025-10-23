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
├── deployment/                 # Deployment configurations
│   ├── cloudrun/               # Google Cloud Run deployment
│   │   ├── deploy.sh           # Cloud deployment script
│   │   ├── cloudbuild.yaml     # CI/CD pipeline config
│   │   ├── service.yaml        # Cloud Run service definition
│   │   ├── service-secrets.yaml # Service with Secret Manager
│   │   ├── cloudrun-wrapper.sh # Cloud Run entrypoint
│   │   ├── cloudrun-kernel-wrapper.sh # Alternative wrapper
│   │   ├── supervisord-cloudrun.conf # Supervisor for Cloud Run
│   │   └── nginx.conf          # Reverse proxy config
│   └── local/                  # Local deployment
│       └── run-local.sh        # Interactive Docker run script
├── nginx/                      # Nginx configurations
│   └── nginx-devtools.conf     # DevTools nginx config
├── scripts/                    # Utility scripts
│   ├── init-container.sh       # Auto-cleanup of lock files
│   └── test-eval-server.sh     # Eval server build test
├── supervisor/services/        # Service configs (override defaults)
│   ├── chromium.conf           # Auto-open DevTools
│   ├── eval-server.conf        # Eval server with CDP_PORT=9223
│   ├── neko.conf
│   └── nginx-devtools.conf
├── eval-server/
│   └── nodejs/                 # Eval server source (use this, NOT submodule)
│       ├── src/
│       │   ├── api-server.js   # HTTP REST API
│       │   ├── evaluation-server.js  # WebSocket + CDP
│       │   └── lib/            # EvaluationLoader, EvaluationStack, judges
│       ├── start.js            # Server entrypoint
│       └── package.json
├── evals/
│   ├── run.py                  # Python evaluation runner
│   ├── lib/judge.py            # LLMJudge, VisionJudge, SimpleJudge
│   └── data/                   # Evaluation YAML files
├── Dockerfile.local            # Main Docker build (local dev)
├── Dockerfile.devtools         # DevTools frontend build
├── Dockerfile.cloudrun         # Cloud Run build
├── docker-compose.yml          # Local deployment config
├── Makefile                    # Build/deployment commands
├── CLAUDE.md                   # This file
└── README.md                   # User documentation
```

## Key Files and What They Do

### Dockerfile.local
Multi-stage build that:
1. Copies pre-built DevTools from `browser-operator-devtools:latest`
2. Builds eval-server with `npm install`
3. Builds kernel-images Go API
4. Builds WebRTC client
5. Compiles custom Xorg drivers
6. Assembles final Ubuntu 22.04 image with all components
7. Adds init script for automatic lock cleanup

**Critical sections:**
- Line 284: Copies `scripts/init-container.sh` for lock cleanup
- Line 288-294: Creates `/entrypoint.sh` wrapper
- Line 299: Sets entrypoint to run init before main wrapper

### docker-compose.yml
Configures container with:
- Port mappings for all services (8000-8082, 9222, 444)
- Volume mounts: recordings, chromium-data, eval-server code
- tmpfs: `/dev/shm` and `/tmp` (prevents lock file persistence)
- Environment: `CHROMIUM_FLAGS` with custom DevTools frontend

**Recent fixes:**
- Added missing ports 8000, 8001, 8081, 8082
- Added `/tmp` tmpfs mount to prevent X11 lock persistence
- Added `--custom-devtools-frontend=http://localhost:8001/`

### scripts/init-container.sh
Runs on every container start to clean:
- Chromium lock files (`SingletonLock`, `SingletonSocket`, `SingletonCookie`)
- X11 lock files (`/tmp/.X*-lock`)

This prevents "profile in use" and "display already active" errors.

### eval-server/nodejs/src/api-server.js
HTTP REST API with endpoints:
- `POST /v1/responses` - Execute browser automation tasks
- `POST /page/content` - Get page HTML/text content
- `POST /page/screenshot` - Capture screenshots
- `GET /status` - Health check

### supervisor/services/eval-server.conf
**Critical environment variables:**
```ini
environment=NODE_ENV="production",PORT="8082",API_PORT="8080",HOST="0.0.0.0",CDP_PORT="9223"
```

Note: CDP_PORT must be 9223 (not 9222) to match Chromium configuration.

### Makefile
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

### deployment/local/run-local.sh
Interactive Docker run script that:
- Sources kernel-images common build variables
- Creates local recordings directory
- Configures Chromium data persistence (customizable with `CHROMIUM_DATA_HOST`)
- **Cleans lock files from host before starting** (lines 84-89)
- Builds docker run arguments with all port mappings
- Supports `URLS` environment variable to open URLs on startup
- Uses custom DevTools frontend flag
- Runs container with `docker run -d` (detached but logs visible via docker logs)

**Key difference from docker-compose:**
- Lock cleanup happens on HOST before container starts
- Eval server code is NOT volume-mounted (baked into image)
- More flexible for custom configurations via environment variables
- Better for seeing startup issues and debugging

### deployment/cloudrun/
Contains all Google Cloud Run deployment files:
- `deploy.sh` - Automated deployment script with Twilio TURN setup
- `cloudbuild.yaml` - CI/CD pipeline for Cloud Build
- `service.yaml` / `service-secrets.yaml` - Cloud Run service definitions
- `cloudrun-wrapper.sh` - Cloud Run container entrypoint
- `supervisord-cloudrun.conf` - Supervisor configuration for Cloud Run
- `nginx.conf` - Reverse proxy for Cloud Run port requirements

### nginx/
Nginx configuration files:
- `nginx-devtools.conf` - DevTools UI server config (used by Dockerfile.local)

### scripts/
Utility scripts:
- `init-container.sh` - Automatic lock file cleanup on container start
- `test-eval-server.sh` - Test eval-server Docker build stage

## Common Issues and Solutions

### 1. Chromium Profile Lock Errors
**Symptom:** "The profile appears to be in use by another Chromium process"

**Solution:** Now handled automatically by `scripts/init-container.sh`
- Runs on every container start
- Cleans lock files before services start
- No manual intervention needed

### 2. X11 Display Lock Errors
**Symptom:** "Server is already active for display 1"

**Solution:** Fixed by adding `/tmp` to tmpfs in docker-compose.yml
- Line 54: `- /tmp` in tmpfs section
- Prevents lock files from persisting across restarts

### 3. CDP Connection Failures
**Symptom:** "Failed to connect to Chrome DevTools Protocol"

**Solution:** Ensure CDP_PORT=9223 in `supervisor/services/eval-server.conf`
- Chromium runs on port 9223 (not 9222)
- Check logs: `docker logs kernel-browser-extended | grep CDP`

### 4. Module Not Found Errors
**Symptom:** "Cannot find module 'js-yaml'" or "Cannot find module 'EvaluationLoader.js'"

**Solution:**
- Ensure `eval-server/nodejs/` has all dependencies
- Run `cd eval-server/nodejs && npm install`
- Copy missing files from `browser-operator-core/eval-server/` if needed
- **Always use local `eval-server/`, NOT the submodule version**

### 5. Docker Volume Caching on macOS
**Symptom:** File changes not visible in running container with docker-compose

**Solution:** Completely recreate container
```bash
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
- Volume-mounted eval-server code (live reload)
- Managed by docker-compose
- Better for long-running development

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

# Iterate on eval-server code (NO REBUILD NEEDED)
vim eval-server/nodejs/src/api-server.js
docker-compose restart       # Picks up changes immediately

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
| **Eval server code** | Baked into image, rebuild needed | Volume-mounted, restart only |
| **DevTools code** | Baked into image, rebuild needed | Baked into image, rebuild needed |
| **Best for** | Debugging, seeing startup issues | Development iteration |
| **Script** | `run-local.sh` | `docker-compose.yml` |
| **Data location** | Easy to customize with env vars | Set in compose file or env var |
| **Lock cleanup** | Script cleans host before start | Container init cleans on start |
| **URLs on startup** | `URLS="..." make run` | Edit compose file |

### Rebuild After Changes

#### With Docker Compose:

```bash
# Eval server changes (NO REBUILD)
vim eval-server/nodejs/src/api-server.js
docker-compose restart       # Volume-mounted, picks up changes

# DevTools changes
vim browser-operator-core/front_end/panels/ai_chat/...
make rebuild-devtools        # Fast rebuild
docker-compose down
docker-compose up -d

# Dockerfile changes
make rebuild                 # Full rebuild
make compose-up
```

#### With Direct Docker Run:

```bash
# ANY code changes (eval-server OR DevTools)
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

### Always Use Local eval-server/
**DO NOT** use files from `browser-operator-core/eval-server/`

The correct path is: `eval-server/nodejs/`

Dockerfile.devtools has been updated to copy from local directory.

### CDP Port is 9223, Not 9222
The default Chrome DevTools port is 9222, but this project uses 9223.

Check these files:
- `supervisor/services/eval-server.conf` - Must have `CDP_PORT="9223"`
- Chromium startup config uses port 9223

### Dependencies in eval-server/nodejs/
Required packages:
- js-yaml (for parsing YAML eval files)
- express (HTTP server)
- ws (WebSocket server)
- chrome-remote-interface (CDP client)

All managed by `package.json` and `npm install`.

### Lock File Cleanup is Automatic
After implementing `scripts/init-container.sh`, you should never need to manually clean lock files again. The script runs on every container start.

## Testing

### Quick API Test
```bash
make test
```

Runs `evals/data/test-simple/math-001.yaml` which:
1. Checks API endpoint health
2. Sends simple math question via `/v1/responses`
3. Validates response using SimpleJudge
4. Reports PASS/FAIL

### Running Specific Evals
```bash
cd evals
python3 run.py --path data/web-task-agent/flight-001.yaml --verbose
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

1. **Fixed docker-compose.yml** - Added missing port mappings (8000, 8001, 8081, 8082)
2. **Fixed tmpfs mounts** - Added `/tmp` to prevent X11 lock persistence
3. **Added automatic lock cleanup** - `scripts/init-container.sh` runs on every start
4. **Updated Chromium flags** - Added `--custom-devtools-frontend=http://localhost:8001/`
5. **Fixed CDP port** - Set `CDP_PORT="9223"` in eval-server supervisor config
6. **Created make test** - Quick verification of eval API functionality
7. **Fixed eval-server source** - Always use local `eval-server/`, not submodule
