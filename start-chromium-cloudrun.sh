#!/bin/bash

set -o pipefail -o errexit -o nounset

# Cloud Run optimized Chromium launcher - no runuser needed since we're already kernel user

echo "Starting Chromium launcher (Cloud Run mode)"

# Resolve internal port for the remote debugging interface
INTERNAL_PORT="${INTERNAL_PORT:-9223}"

# Load additional Chromium flags from env and optional file
CHROMIUM_FLAGS="${CHROMIUM_FLAGS:-}"
if [[ -f /chromium/flags ]]; then
  CHROMIUM_FLAGS="$CHROMIUM_FLAGS $(cat /chromium/flags)"
fi

# Add proxy configuration if enabled
PROXY_ENABLED="${PROXY_ENABLED:-true}"
if [[ "$PROXY_ENABLED" == "true" ]]; then
  PROXY_SERVER="${PROXY_SERVER:-http://127.0.0.1:3128}"
  CHROMIUM_FLAGS="$CHROMIUM_FLAGS --proxy-server=$PROXY_SERVER"
  echo "Proxy enabled: $PROXY_SERVER"
fi

echo "CHROMIUM_FLAGS: $CHROMIUM_FLAGS"

# Always use display :1 and point DBus to the system bus socket
export DISPLAY=":1"
export DBUS_SESSION_BUS_ADDRESS="unix:path=/tmp/dbus/system_bus_socket"
export XDG_CONFIG_HOME=/home/kernel/.config
export XDG_CACHE_HOME=/home/kernel/.cache
export HOME=/home/kernel

echo "Running chromium as kernel user (Cloud Run mode)"
exec chromium \
  --remote-debugging-port="$INTERNAL_PORT" \
  --user-data-dir=/home/kernel/user-data \
  --password-store=basic \
  --no-first-run \
  ${CHROMIUM_FLAGS:-}