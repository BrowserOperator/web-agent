# Kernel Browser - Google Cloud Run Deployment

Deploy the [kernel-images](https://github.com/onkernel/kernel-images) Chrome browser environment to Google Cloud Run with WebRTC support, Chrome DevTools Protocol, and screen recording capabilities.

## 🏗️ Architecture

This deployment provides:
- **Headful Chrome** with GUI access via WebRTC
- **Chrome DevTools Protocol** for automation (Playwright, Puppeteer)
- **Screen Recording API** for session capture
- **nginx Reverse Proxy** for Cloud Run port requirements
- **Auto-scaling** from 0 to multiple instances

## 📋 Prerequisites

1. **Google Cloud Account** with billing enabled
2. **gcloud CLI** installed and authenticated
3. **Docker** installed locally (for local builds)
4. **Git** with submodule access

## 🚀 Quick Start

### 1. Clone and Setup

```bash
# The kernel-images submodule should already be initialized
cd /Users/tyson/codebase/blue-browser/web-agent

# Verify submodule
git submodule status
```

### 2. Configure Google Cloud

```bash
# Set your project ID
export PROJECT_ID="your-gcp-project-id"
gcloud config set project $PROJECT_ID

# Authenticate (if not already done)
gcloud auth login
gcloud auth application-default login
```

### 3. Deploy

```bash
# Automated deployment (recommended)
./deploy.sh

# Or with custom settings
./deploy.sh --project your-project-id --region us-central1
```

### 4. Access Your Service

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

## 📁 File Structure

```
web-agent/
├── kernel-images/          # Git submodule
├── Dockerfile.cloudrun     # Cloud Run optimized build
├── nginx.conf             # Reverse proxy config
├── cloudrun-wrapper.sh    # Cloud Run startup script
├── service.yaml           # Cloud Run service definition
├── cloudbuild.yaml        # CI/CD pipeline
├── deploy.sh              # Deployment script
├── .gcloudignore          # Build ignore rules
└── README.md              # This file
```

## 🐛 Troubleshooting

### Common Issues

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

### Debug Commands

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
2. Docker image build
3. Container Registry push
4. Cloud Run deployment
5. Traffic routing

Trigger builds via:
```bash
gcloud builds submit --config cloudbuild.yaml
```

## 📚 Additional Resources

- [kernel-images Documentation](https://github.com/onkernel/kernel-images)
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [WebRTC Documentation](https://webrtc.org/getting-started/)
- [Chrome DevTools Protocol](https://chromedevtools.github.io/devtools-protocol/)

---

**Need help?** Open an issue or check the kernel-images Discord community.