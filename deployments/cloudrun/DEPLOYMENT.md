# Kernel Browser - Cloud Run Deployment Guide

This guide explains how to deploy the Kernel Browser to Google Cloud Run with secure Twilio credential management.

## Prerequisites

- Google Cloud SDK (`gcloud`) installed
- Docker installed
- Git installed
- A Google Cloud Project with billing enabled
- Twilio account with API credentials (for WebRTC TURN servers)

## Quick Start

### 1. Clone the repository
```bash
git clone <repository-url>
cd browser-web-agent
git submodule update --init --recursive
```

### 2. Set up Twilio credentials
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your Twilio credentials
# Get these from https://console.twilio.com/ > Account > API Keys & Tokens
```

Your `.env` file should contain:
```
TWILIO_ACCOUNT_SID=SK...your_api_key_sid_here
TWILIO_AUTH_TOKEN=your_api_key_secret_here
```

### 3. Deploy to Cloud Run
```bash
./deploy.sh
```

The script will:
- Load credentials from `.env`
- Create/update secrets in Google Secret Manager
- Build and deploy the container to Cloud Run
- Configure all necessary permissions

## Deployment Options

### Using Cloud Build (recommended)
```bash
./deploy.sh
```

### Using local Docker build
```bash
./deploy.sh --local
```

### Specify project and region
```bash
./deploy.sh --project YOUR_PROJECT_ID --region us-central1
```

## How It Works

### Credential Management

1. **Local Development**: Credentials are stored in `.env` file (gitignored)
2. **Secret Manager**: Deploy script automatically creates/updates secrets in Google Secret Manager
3. **Cloud Run**: Service uses `secretKeyRef` to securely access credentials at runtime
4. **Dynamic TURN**: Container fetches fresh TURN credentials from Twilio on startup

### Security Features

- Credentials never appear in code or logs
- Secrets are encrypted at rest and in transit
- Service account has minimal required permissions
- Automatic credential rotation support

### Files Overview

- `.env.example` - Template for environment variables
- `.env` - Your local credentials (gitignored)
- `deploy.sh` - Main deployment script with Secret Manager integration
- `service-secrets.yaml` - Cloud Run config with secret references
- `service.yaml` - Fallback config (for deployments without secrets)
- `cloudbuild.yaml` - Cloud Build configuration
- `twilio/` - Twilio credential management scripts

## Updating Credentials

To update Twilio credentials:

1. Update `.env` with new credentials
2. Run `./deploy.sh` again
3. Script will update secrets and redeploy

## Manual Secret Management

If you need to manage secrets manually:

```bash
# Create secrets
echo -n "YOUR_SID" | gcloud secrets create twilio-account-sid --data-file=-
echo -n "YOUR_TOKEN" | gcloud secrets create twilio-auth-token --data-file=-

# Update secrets
echo -n "NEW_SID" | gcloud secrets versions add twilio-account-sid --data-file=-
echo -n "NEW_TOKEN" | gcloud secrets versions add twilio-auth-token --data-file=-

# Grant access to service account
gcloud secrets add-iam-policy-binding twilio-account-sid \
  --member="serviceAccount:kernel-browser-sa@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

## Service Endpoints

After deployment, you'll have access to:

- **Main Interface**: `https://SERVICE_URL/`
- **WebRTC Client**: `https://SERVICE_URL/`
- **Chrome DevTools**: `https://SERVICE_URL/devtools/`
- **DevTools WebSocket**: `wss://SERVICE_URL/cdp/ws`
- **Recording API**: `https://SERVICE_URL/api`
- **Health Check**: `https://SERVICE_URL/health`

## Troubleshooting

### Deployment fails
- Check that all prerequisites are installed
- Ensure billing is enabled on your GCP project
- Verify you have sufficient quota in your region

### WebRTC not working
- Ensure Twilio credentials are correct
- Check Cloud Run logs: `gcloud run services logs read kernel-browser --region=us-central1`
- Verify TURN servers are accessible from your network

### Secrets not found
- Run `gcloud secrets list` to verify secrets exist
- Check service account permissions
- Ensure Secret Manager API is enabled

## Architecture

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Client    │────▶│   Cloud Run      │────▶│ Secret Manager  │
│  (Browser)  │     │   (Container)    │     │  (Credentials)  │
└─────────────┘     └──────────────────┘     └─────────────────┘
                            │
                            ▼
                    ┌──────────────────┐
                    │   Twilio API     │
                    │  (TURN Servers)  │
                    └──────────────────┘
```

## Support

For issues or questions:
- Check logs: `gcloud run services logs read kernel-browser --region=us-central1`
- Review service status: `gcloud run services describe kernel-browser --region=us-central1`
- File an issue on GitHub