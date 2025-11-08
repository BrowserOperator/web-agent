# Twilio TURN Server Integration

This folder contains scripts for integrating Twilio's Network Traversal Service to provide TURN server credentials for WebRTC in Cloud Run.

## Scripts

### `twilio-credential-updater.sh`
- **Purpose**: Called by `cloudrun-wrapper.sh` on container startup
- **Function**: Fetches fresh TURN credentials from Twilio API
- **Fallback**: Uses free TURN servers if Twilio fails
- **Environment Variables Required**:
  - `TWILIO_ACCOUNT_SID` (API Key SID)
  - `TWILIO_AUTH_TOKEN` (API Key Secret)

### `twilio-token-service.js` 
- **Purpose**: Node.js service for TURN credential generation
- **Features**: 
  - HTTP server mode (`--server` flag)
  - One-time credential generation (default)
  - Credential caching (1 hour)
- **Dependencies**: Express.js (for server mode)

### `test-twilio-api.sh`
- **Purpose**: Test Twilio Network Traversal Service API
- **Usage**: `TWILIO_ACCOUNT_SID=xxx TWILIO_AUTH_TOKEN=xxx ./test-twilio-api.sh`
- **Output**: Formatted credentials for `NEKO_ICESERVERS`

### `test-twilio-node.js`
- **Purpose**: Simple Node.js test for Twilio API
- **Usage**: Node.js version of the API test
- **Dependencies**: Only Node.js built-ins

### `update-twilio-credentials.sh`
- **Purpose**: Update running Cloud Run service with fresh credentials
- **Usage**: Run periodically to refresh credentials
- **Features**: Direct Cloud Run service update

## Integration

The main integration point is in `../cloudrun-wrapper.sh`:

```bash
# Get fresh Twilio TURN credentials if available
if [ -f /twilio-credential-updater.sh ]; then
    echo "[cloudrun-wrapper] Getting fresh Twilio TURN credentials..."
    source /twilio-credential-updater.sh
else
    echo "[cloudrun-wrapper] Twilio updater not found, using credentials from environment"
fi
```

## Credentials Format

Twilio Network Traversal Service returns credentials in this format:

```json
{
  "ice_servers": [
    {
      "url": "turn:global.turn.twilio.com:3478?transport=tcp",
      "username": "long-generated-username",
      "credential": "base64-encoded-credential"
    }
  ],
  "ttl": "86400"
}
```

These are converted to neko format:

```json
[
  {
    "urls": ["turn:global.turn.twilio.com:3478?transport=tcp"],
    "username": "long-generated-username", 
    "credential": "base64-encoded-credential"
  }
]
```