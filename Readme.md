# Web Agent - Browser Automation & Evaluation Platform

Extended [kernel-images](https://github.com/onkernel/kernel-images) Chromium environment with Browser Operator DevTools and eval server for browser automation, testing, and AI agent evaluation.

## 🏗️ Architecture

This platform provides:
- **Browser Operator DevTools** - Custom DevTools frontend with AI chat panel
- **Eval Server API** - HTTP/WebSocket API for browser automation and evaluation
- **Headful Chrome** with GUI access via WebRTC
- **Chrome DevTools Protocol** for automation (Playwright, Puppeteer)
- **Screen Recording API** for session capture
- **Local Docker Compose** for development
- **Google Cloud Run** deployment option

## 📋 Prerequisites

### For Local Development
1. **Docker** and **Docker Compose** installed
2. **Make** utility
3. **Git** with submodule access
4. **Python 3** (for running evals)

### For Cloud Run Deployment
1. **Google Cloud Account** with billing enabled
2. **gcloud CLI** installed and authenticated
3. All of the above

---

## 🚀 Local Development - Two Deployment Options

### Option 1: Docker Compose (Recommended for Development)

**Best for:** Background services, docker-compose workflows, persistent containers

```bash
# 1. Initialize submodules
make init

# 2. Build Docker images (takes ~30 minutes first time)
make build

# 3. Start all services in background
make compose-up

# 4. Verify everything works
make test
```

### Option 2: Direct Docker Run (Interactive Mode)

**Best for:** Interactive debugging, seeing live logs, quick testing

```bash
# 1. Initialize submodules
make init

# 2. Build Docker images (takes ~30 minutes first time)
make build

# 3. Start in interactive mode (logs to terminal)
make run

# In another terminal, verify
make test
```

### Access Points

After starting with either `make compose-up` or `make run`, access:

| Service | URL | Purpose |
|---------|-----|---------|
| **WebRTC Client** | http://localhost:8000 | Live browser view with control |
| **DevTools UI** | http://localhost:8001 | Enhanced DevTools with AI chat |
| **Eval Server API** | http://localhost:8080 | HTTP REST API for automation |
| **WebRTC Neko** | http://localhost:8081 | WebRTC control interface |
| **Eval Server WS** | ws://localhost:8082 | WebSocket JSON-RPC API |
| **CDP Endpoint** | http://localhost:9222/json | Chrome DevTools Protocol |
| **Recording API** | http://localhost:444/api | Screen recording controls |

### Available Make Commands

```bash
make help              # Show all available commands
make init              # Initialize git submodules
make build             # Build images (smart caching)
make rebuild           # Force complete rebuild
make build-devtools    # Build DevTools base (~30 min)
make rebuild-devtools  # Fast rebuild with local changes
make compose-up        # Start in background
make run               # Start in interactive mode
make stop              # Stop all containers
make restart           # Restart containers
make logs              # View container logs
make test              # Run API verification test
make clean             # Clean up everything
```

### Comparison: `make run` vs `make compose-up`

| Feature | `make run` | `make compose-up` |
|---------|------------|-------------------|
| **Log visibility** | Live logs in terminal | Background, use `make logs` |
| **Stopping** | Ctrl+C or `docker stop` | `make stop` or `docker-compose down` |
| **Restarting** | Stop and run again | `docker-compose restart` |
| **Use case** | Interactive debugging | Background development |
| **Startup script** | `run-local.sh` | `docker-compose.yml` |
| **Lock cleanup** | Script cleans before start | Container cleans on start |
| **Volume mounts** | Defined in script | Defined in compose file |

### Development Workflow

**With Docker Compose (make compose-up):**

*Editing Eval Server Code:*
```bash
# 1. Make changes in eval-server/nodejs/
vim eval-server/nodejs/src/api-server.js

# 2. Restart container (no rebuild needed, volume-mounted)
docker-compose restart

# 3. Test changes
make test
```

*Editing DevTools:*
```bash
# 1. Make changes in browser-operator-core/front_end/
vim browser-operator-core/front_end/panels/ai_chat/...

# 2. Rebuild DevTools only
make rebuild-devtools

# 3. Restart containers
docker-compose down && docker-compose up -d
```

*Full Rebuild:*
```bash
make rebuild        # Rebuild everything from scratch
make compose-up     # Start containers
```

**With Direct Docker Run (make run):**

*Editing Eval Server Code:*
```bash
# 1. Make changes in eval-server/nodejs/
vim eval-server/nodejs/src/api-server.js

# 2. Since eval-server is NOT volume-mounted in run mode, rebuild
make rebuild

# 3. Stop and restart
# Press Ctrl+C in the terminal running 'make run'
make run
```

*Editing DevTools:*
```bash
# 1. Make changes in browser-operator-core/front_end/
vim browser-operator-core/front_end/panels/ai_chat/...

# 2. Rebuild DevTools only
make rebuild-devtools

# 3. Stop and restart
# Press Ctrl+C in the terminal running 'make run'
make run
```

*Full Rebuild:*
```bash
make rebuild        # Rebuild everything from scratch
# Press Ctrl+C in the terminal running 'make run'
make run           # Start in interactive mode
```

### Customizing Browser Data Location

**With `make run`:**
```bash
# Default: ./chromium-data
make run

# Custom location
CHROMIUM_DATA_HOST=/path/to/data make run

# Ephemeral (no persistence)
CHROMIUM_DATA_HOST="" make run
```

**With `make compose-up`:**
```bash
# Edit docker-compose.yml to change CHROMIUM_DATA_HOST
# Or set environment variable:
CHROMIUM_DATA_HOST=/path/to/data make compose-up
```

### Opening URLs on Startup

**With `make run`:**
```bash
# Open specific URLs when browser starts
URLS="https://google.com https://github.com" make run
```

**With `make compose-up`:**
```bash
# Add URLS to docker-compose.yml environment section
```

### Running Evaluations

```bash
# Simple test
make test

# Specific evaluation
cd evals
python3 run.py --path data/web-task-agent/flight-001.yaml --verbose

# All evaluations in a directory
python3 run.py --path data/web-task-agent/ --verbose
```

### Troubleshooting

**Container won't start (docker-compose):**
```bash
# Check logs
docker logs kernel-browser-extended

# Clean restart
make stop
make clean
make build
make compose-up
```

**Container won't start (make run):**
```bash
# Stop existing container
docker stop kernel-browser-extended
docker rm kernel-browser-extended

# Clean rebuild
make clean
make rebuild
make run
```

**Port conflicts:**
```bash
# Remove existing container
docker rm -f kernel-browser-extended

# Then start with your preferred method
make compose-up  # OR make run
```

**Lock file errors (should be automatic now):**
The system now automatically cleans lock files on startup. If you still see errors:

*With docker-compose:*
```bash
docker-compose down
rm -f ./chromium-data/user-data/Singleton*
make compose-up
```

*With make run:*
```bash
# Press Ctrl+C to stop
rm -f ./chromium-data/user-data/Singleton*
make run
```

**Seeing stale code after changes (make run):**
```bash
# Eval server code is NOT volume-mounted in run mode
# You must rebuild after code changes
make rebuild
# Press Ctrl+C in terminal running 'make run'
make run
```

**Want to see live logs (docker-compose):**
```bash
# Option 1: Follow logs
make logs

# Option 2: Switch to interactive mode
make stop
make run
```

---

## 🚀 Google Cloud Run Deployment

### Configure Google Cloud

```bash
# Set your project ID
export PROJECT_ID="your-gcp-project-id"
gcloud config set project $PROJECT_ID

# Authenticate (if not already done)
gcloud auth login
gcloud auth application-default login
```

### Deploy to Cloud Run

```bash
# Automated deployment (recommended)
./deployment/cloudrun/deploy.sh

# Or with custom settings
./deployment/cloudrun/deploy.sh --project your-project-id --region us-central1
```

### Access Cloud Run Service

After deployment, you'll get URLs like:
```
🌐 Service Endpoints:
   Main Interface:    https://kernel-browser-xxx-uc.a.run.app
   WebRTC Client:     https://kernel-browser-xxx-uc.a.run.app/
   Chrome DevTools:   https://kernel-browser-xxx-uc.a.run.app/ws  
   Recording API:     https://kernel-browser-xxx-uc.a.run.app/api
   Health Check:      https://kernel-browser-xxx-uc.a.run.app/health
```

## 📖 Detailed Usage

### WebRTC Live View

Access the main URL in your browser to get real-time Chrome access:
- Full mouse/keyboard control
- Copy/paste support
- Window resizing
- Audio streaming (experimental)

### Chrome DevTools Protocol

Connect automation tools to the `/ws` endpoint:

```javascript
// Playwright
const browser = await chromium.connectOverCDP('wss://your-service-url/ws');

// Puppeteer  
const browser = await puppeteer.connect({
  browserWSEndpoint: 'wss://your-service-url/ws',
});
```

### Recording API

Capture screen recordings via REST API:

```bash
# Start recording
curl -X POST https://your-service-url/api/recording/start -d '{}'

# Stop recording  
curl -X POST https://your-service-url/api/recording/stop -d '{}'

# Download recording
curl https://your-service-url/api/recording/download --output recording.mp4
```

## ⚙️ Configuration

### Environment Variables

Key configuration options in `service.yaml`:

```yaml
env:
- name: ENABLE_WEBRTC
  value: "true"               # Enable WebRTC streaming
- name: WIDTH  
  value: "1024"              # Browser width
- name: HEIGHT
  value: "768"               # Browser height
- name: CHROMIUM_FLAGS
  value: "--no-sandbox..."   # Chrome launch flags
- name: NEKO_ICESERVERS
  value: '[{"urls": [...]}]' # TURN/STUN servers
```

### Resource Limits

Default Cloud Run settings:
- **CPU**: 4 cores
- **Memory**: 8GB
- **Timeout**: 1 hour
- **Concurrency**: 1 (one browser per container)

### Scaling

- **Min instances**: 0 (scales to zero when unused)
- **Max instances**: 10 (adjustable)
- **Cold start**: ~30-60 seconds

## 🔧 Advanced Configuration

### Custom Chrome Flags

Edit `service.yaml` to modify Chrome behavior:

```yaml
- name: CHROMIUM_FLAGS
  value: "--user-data-dir=/home/kernel/user-data --disable-dev-shm-usage --custom-flag"
```

### TURN Server for WebRTC

For production WebRTC, configure a TURN server:

```yaml
- name: NEKO_ICESERVERS  
  value: '[{"urls": ["turn:turn.example.com:3478"], "username": "user", "credential": "pass"}]'
```

## 📁 Project Structure

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
├── supervisor/services/        # Service configs (overrides)
├── eval-server/
│   └── nodejs/                 # Eval server (use this, NOT submodule)
│       ├── src/                # API server, evaluation server, lib
│       ├── start.js            # Server entrypoint
│       └── package.json
├── evals/
│   ├── run.py                  # Python evaluation runner
│   ├── lib/judge.py            # Judge implementations
│   └── data/                   # Evaluation YAML files
├── Dockerfile.local            # Main Docker build (local dev)
├── Dockerfile.devtools         # DevTools frontend build
├── Dockerfile.cloudrun         # Cloud Run build
├── docker-compose.yml          # Local deployment config
├── Makefile                    # Build commands
├── CLAUDE.md                   # Technical documentation
└── README.md                   # This file
```

## 🐛 Troubleshooting

### Local Development Issues

See the detailed troubleshooting section under **Local Docker Compose Deployment** above.

Common quick fixes:
```bash
# Clean restart
make stop && make clean && make build && make compose-up

# Check logs
docker logs kernel-browser-extended

# Verify services
docker exec kernel-browser-extended supervisorctl status
```

### Cloud Run Issues

1. **Build Timeout**
   ```bash
   # Use local build for testing
   ./deploy.sh --local
   ```

2. **Port Binding Errors**
   - Cloud Run requires port 8080
   - nginx proxies internal services
   - Check `nginx.conf` for port mappings

3. **Chrome Crashes**
   - Ensure `--no-sandbox` flag is set
   - Check memory limits (8GB minimum)
   - Verify non-root user execution

### Cloud Run Debug Commands

```bash
# View service logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=kernel-browser" --project=$PROJECT_ID --limit=50

# Check service status
gcloud run services describe kernel-browser --region=us-central1

# Test endpoints
curl https://your-service-url/health
curl https://your-service-url/json/version
```

## 🔒 Security Considerations

- Service runs as non-root user
- Chrome uses `--no-sandbox` (required for containers)
- WebRTC streams are not encrypted by default
- Consider VPC/firewall rules for production
- Use Cloud IAM for API access control

## 💰 Cost Estimation

Approximate Cloud Run costs:
- **CPU**: $0.00002400 per vCPU-second
- **Memory**: $0.00000250 per GiB-second  
- **Requests**: $0.40 per million requests

Example: 1 hour session ≈ $0.50-1.00

## 🔄 CI/CD Pipeline

The `cloudbuild.yaml` provides:
1. Submodule initialization
2. Docker image build with caching
3. Container Registry push
4. Cloud Run deployment
5. Traffic routing

### Build Commands

```bash
# Normal build (with cache) - recommended for development
gcloud builds submit --config deployment/cloudrun/cloudbuild.yaml

# Force rebuild without cache - use when dependencies change
gcloud builds submit --config deployment/cloudrun/cloudbuild.yaml --substitutions=_NO_CACHE=true

# Automated deployment with Twilio TURN server setup
./deployment/cloudrun/deploy.sh
```

### Cache Control

The build system uses Docker layer caching by default to reduce build times and costs:
- **With cache**: ~5-10 minutes, lower cost
- **Without cache**: ~30+ minutes, higher cost (~$3-5 per build)

Use `_NO_CACHE=true` only when:
- Dependencies have changed significantly
- Base images need updating
- Debugging build issues

## 📚 Additional Resources

- [CLAUDE.md](./CLAUDE.md) - Detailed technical documentation for Claude Code
- [kernel-images Documentation](https://github.com/onkernel/kernel-images)
- [Browser Operator DevTools](https://github.com/BrowserOperator/browser-operator-core)
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [WebRTC Documentation](https://webrtc.org/getting-started/)
- [Chrome DevTools Protocol](https://chromedevtools.github.io/devtools-protocol/)

## 🎯 API Examples

### Eval Server HTTP API

```bash
# Execute browser task
curl -X POST http://localhost:8080/v1/responses \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Navigate to google.com and search for puppies",
    "url": "about:blank",
    "wait_timeout": 5000,
    "model": {
      "main_model": {
        "provider": "openai",
        "model": "gpt-4",
        "api_key": "your-api-key"
      }
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

### WebSocket JSON-RPC API

```javascript
const WebSocket = require('ws');
const ws = new WebSocket('ws://localhost:8082');

ws.on('open', () => {
  // Subscribe to evaluations
  ws.send(JSON.stringify({
    jsonrpc: '2.0',
    method: 'subscribe',
    params: { clientId: 'my-client' },
    id: 1
  }));
});

ws.on('message', (data) => {
  const response = JSON.parse(data);
  console.log('Received:', response);
});
```

---

**Need help?** Check [CLAUDE.md](./CLAUDE.md) for detailed technical docs or open an issue.