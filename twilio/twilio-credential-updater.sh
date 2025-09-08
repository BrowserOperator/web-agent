#!/bin/bash

# Twilio TURN Credential Updater for Cloud Run
# This script is called from cloudrun-wrapper.sh to get fresh credentials on startup

set -e

# Check if we're using dynamic credentials mode (from Secret Manager)
if [ "$NEKO_ICESERVERS" = "DYNAMIC" ]; then
    echo "[twilio-updater] Dynamic credentials mode - will fetch fresh TURN credentials"
elif [ -n "$NEKO_ICESERVERS" ] && [ "$NEKO_ICESERVERS" != "DYNAMIC" ]; then
    # NEKO_ICESERVERS is already set with actual credentials
    echo "[twilio-updater] Using pre-configured TURN credentials"
    return 0 2>/dev/null || exit 0
fi

# Twilio credentials (passed as environment variables)
ACCOUNT_SID="${TWILIO_ACCOUNT_SID}"
AUTH_TOKEN="${TWILIO_AUTH_TOKEN}"

if [ -z "$ACCOUNT_SID" ] || [ -z "$AUTH_TOKEN" ]; then
    echo "[twilio-updater] Warning: Twilio credentials not set, using fallback TURN servers"
    # Export fallback servers
    export NEKO_ICESERVERS='[{"urls": ["turn:openrelay.metered.ca:80?transport=tcp"], "username": "openrelayproject", "credential": "openrelayproject"}]'
    return 0 2>/dev/null || exit 0
fi

echo "[twilio-updater] Fetching fresh TURN credentials from Twilio..."

# Get TURN credentials from Twilio API
response=$(curl -s -X POST \
  "https://api.twilio.com/2010-04-01/Accounts/${ACCOUNT_SID}/Tokens.json" \
  -u "${ACCOUNT_SID}:${AUTH_TOKEN}" 2>/dev/null)

# Check if request was successful
if echo "$response" | grep -q "ice_servers"; then
    # Format credentials for neko
    ice_servers=$(echo "$response" | python3 -c "
import json
import sys
try:
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
except:
    print('[]')
" 2>/dev/null)
    
    if [ -n "$ice_servers" ] && [ "$ice_servers" != "[]" ]; then
        echo "[twilio-updater] Successfully retrieved TURN credentials"
        export NEKO_ICESERVERS="$ice_servers"
    else
        echo "[twilio-updater] Failed to parse TURN credentials, using fallback"
        export NEKO_ICESERVERS='[{"urls": ["turn:openrelay.metered.ca:80?transport=tcp"], "username": "openrelayproject", "credential": "openrelayproject"}]'
    fi
else
    echo "[twilio-updater] Failed to get TURN credentials from Twilio, using fallback"
    echo "[twilio-updater] Response: ${response:0:100}..."
    export NEKO_ICESERVERS='[{"urls": ["turn:openrelay.metered.ca:80?transport=tcp"], "username": "openrelayproject", "credential": "openrelayproject"}]'
fi

echo "[twilio-updater] NEKO_ICESERVERS set to: ${NEKO_ICESERVERS:0:100}..."