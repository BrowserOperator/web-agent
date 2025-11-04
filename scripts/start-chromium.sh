#!/bin/bash

set -o pipefail -o errexit -o nounset

# This script is launched by supervisord to start Chromium in the foreground.
# PATCHED VERSION: Properly quotes CHROMIUM_FLAGS to avoid word splitting

echo "Starting Chromium launcher (patched version with proper flag quoting)"

# Resolve internal port for the remote debugging interface
INTERNAL_PORT="${INTERNAL_PORT:-9223}"

# Load additional Chromium flags from env and optional file
CHROMIUM_FLAGS="${CHROMIUM_FLAGS:-}"
if [[ -f /chromium/flags ]]; then
  CHROMIUM_FLAGS="$CHROMIUM_FLAGS $(cat /chromium/flags)"
fi
echo "CHROMIUM_FLAGS: $CHROMIUM_FLAGS"

# Always use display :1 and point DBus to the system bus socket
export DISPLAY=":1"
export DBUS_SESSION_BUS_ADDRESS="unix:path=/run/dbus/system_bus_socket"

RUN_AS_ROOT="${RUN_AS_ROOT:-false}"

# Build chromium command with properly quoted flags
CHROMIUM_ARGS=(
  --remote-debugging-port="$INTERNAL_PORT"
  --user-data-dir=/home/kernel/user-data
  --password-store=basic
  --no-first-run
)

# Parse CHROMIUM_FLAGS properly using eval to handle quotes
if [[ -n "$CHROMIUM_FLAGS" ]]; then
  eval "CHROMIUM_ARGS+=($CHROMIUM_FLAGS)"
fi

if [[ "$RUN_AS_ROOT" == "true" ]]; then
  echo "Running chromium as root"
  exec chromium "${CHROMIUM_ARGS[@]}"
else
  echo "Running chromium as kernel user"
  exec runuser -u kernel -- env \
    DISPLAY=":1" \
    DBUS_SESSION_BUS_ADDRESS="unix:path=/run/dbus/system_bus_socket" \
    XDG_CONFIG_HOME=/home/kernel/.config \
    XDG_CACHE_HOME=/home/kernel/.cache \
    HOME=/home/kernel \
    chromium "${CHROMIUM_ARGS[@]}"
fi
