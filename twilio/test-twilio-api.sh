#!/bin/bash

# Test Twilio Network Traversal Service API
# This generates temporary TURN credentials

ACCOUNT_SID="${TWILIO_ACCOUNT_SID:-YOUR_ACCOUNT_SID}"
AUTH_TOKEN="${TWILIO_AUTH_TOKEN:-YOUR_AUTH_TOKEN}"

echo "Testing Twilio Network Traversal Service API"
echo "============================================"
echo "Account SID: $ACCOUNT_SID"
echo ""

# Make API call to get TURN credentials
echo "Requesting TURN credentials from Twilio..."
echo ""

response=$(curl -s -X POST \
  "https://api.twilio.com/2010-04-01/Accounts/${ACCOUNT_SID}/Tokens.json" \
  -u "${ACCOUNT_SID}:${AUTH_TOKEN}")

# Check if request was successful
if echo "$response" | grep -q "ice_servers"; then
    echo "✅ Success! Received TURN credentials:"
    echo "$response" | python3 -m json.tool
    
    # Extract and format for service.yaml
    echo ""
    echo "Formatted for NEKO_ICESERVERS:"
    echo "$response" | python3 -c "
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
"
else
    echo "❌ Failed to get TURN credentials"
    echo "Response: $response"
    echo ""
    echo "Make sure you have:"
    echo "1. Valid Twilio Account SID and Auth Token"
    echo "2. Network Traversal Service enabled on your Twilio account"
fi