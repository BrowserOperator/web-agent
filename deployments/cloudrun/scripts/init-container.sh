#!/bin/bash
# Container initialization script
# Runs before services start to clean up stale lock files

set +e  # Don't exit on errors

echo "🔧 [init] Running container initialization..."

# Clean up Chromium lock files from persistent data directory
# These prevent "profile in use" errors after container restarts
if [ -d "/data/user-data" ]; then
  echo "🧹 [init] Cleaning Chromium profile locks..."
  rm -f /data/user-data/SingletonLock \
        /data/user-data/SingletonSocket \
        /data/user-data/SingletonCookie \
        2>/dev/null || true
fi

# Clean up X11 lock files
# These prevent "Server is already active for display" errors
if [ -d "/tmp" ]; then
  echo "🧹 [init] Cleaning X11 lock files..."
  rm -f /tmp/.X*-lock 2>/dev/null || true
fi

# Add route to 172.16.55.0/24 network via Docker host gateway
# This allows the container to reach hosts on the 172.16.55.x network
if command -v ip >/dev/null 2>&1; then
  GATEWAY=$(ip route | grep default | awk '{print $3}')
  if [ -n "$GATEWAY" ]; then
    echo "🌐 [init] Adding route to 172.16.55.0/24 via $GATEWAY..."
    ip route add 172.16.55.0/24 via $GATEWAY 2>/dev/null || echo "⚠️  [init] Route already exists or failed to add"
  fi
fi

echo "✅ [init] Container initialization complete"
exit 0
