#!/bin/bash

# Update Cloud Run service with fresh Twilio TURN credentials
# This script should be run periodically (e.g., every hour via cron)
# Run from the root directory: ./twilio/update-twilio-credentials.sh

set -e

# Load environment variables from .env file if it exists
if [ -f ../.env ]; then
    set -a
    . ../.env
    set +a
elif [ -f .env ]; then
    set -a
    . .env
    set +a
fi

# Configuration
PROJECT_ID="${PROJECT_ID}"
SERVICE_NAME="kernel-browser"
REGION="${REGION:-us-central1}"

# Twilio credentials (from environment or .env file)
TWILIO_ACCOUNT_SID="${TWILIO_ACCOUNT_SID}"
TWILIO_AUTH_TOKEN="${TWILIO_AUTH_TOKEN}"

if [ -z "$PROJECT_ID" ]; then
    echo "❌ Error: PROJECT_ID must be set"
    echo "   Set it in your .env file or export as environment variable:"
    echo "   export PROJECT_ID=your-project-id"
    exit 1
fi

if [ -z "$TWILIO_ACCOUNT_SID" ] || [ -z "$TWILIO_AUTH_TOKEN" ]; then
    echo "❌ Error: TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN must be set"
    echo "   Set them in your .env file or export as environment variables:"
    echo "   export TWILIO_ACCOUNT_SID=your_account_sid"
    echo "   export TWILIO_AUTH_TOKEN=your_auth_token"
    exit 1
fi

echo "🔄 Fetching fresh TURN credentials from Twilio..."

# Get TURN credentials from Twilio API
response=$(curl -s -X POST \
  "https://api.twilio.com/2010-04-01/Accounts/${TWILIO_ACCOUNT_SID}/Tokens.json" \
  -u "${TWILIO_ACCOUNT_SID}:${TWILIO_AUTH_TOKEN}")

# Check if request was successful
if ! echo "$response" | grep -q "ice_servers"; then
    echo "❌ Failed to get TURN credentials from Twilio"
    echo "Response: $response"
    exit 1
fi

# Format credentials for neko
ice_servers=$(echo "$response" | python3 -c "
import json
import sys
data = json.load(sys.stdin)
servers = []
for server in data.get('ice_servers', []):
    if server.get('url', '').startswith('turn'):
        url = server['url']
        if 'transport=' not in url:
            url += '?transport=tcp'
        servers.append({
            'urls': [url],
            'username': server.get('username', ''),
            'credential': server.get('credential', '')
        })
print(json.dumps(servers))
")

echo "✅ Received fresh TURN credentials"
echo "   ICE Servers: $ice_servers"

# Update Cloud Run service with new credentials
echo "🚀 Updating Cloud Run service..."

# Create a temporary service.yaml with updated credentials
cat > /tmp/service-update.yaml <<EOF
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: ${SERVICE_NAME}
spec:
  template:
    spec:
      containers:
      - name: kernel-browser
        env:
        - name: NEKO_ICESERVERS
          value: '${ice_servers}'
        - name: CREDENTIAL_UPDATE_TIME
          value: "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
EOF

# Apply the update
gcloud run services replace /tmp/service-update.yaml \
  --region=${REGION} \
  --project=${PROJECT_ID} \
  --platform=managed

echo "✅ Cloud Run service updated with fresh TURN credentials"
echo "   Service URL: https://${SERVICE_NAME}-759404826657.us-central1.run.app"
echo ""
echo "📝 Note: These credentials will expire in ~24 hours"
echo "   Run this script periodically to refresh them"

# Clean up
rm -f /tmp/service-update.yaml