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

echo "✅ [init] Container initialization complete"
exit 0
