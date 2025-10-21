#!/bin/bash
# Cleanup Chromium lock files before starting services
# This prevents "profile in use" errors after container restarts

set -e

echo "🧹 Cleaning up Chromium lock files..."

# Remove lock files from persistent data directory
rm -f /data/user-data/SingletonLock \
      /data/user-data/SingletonSocket \
      /data/user-data/SingletonCookie \
      2>/dev/null || true

# Remove X11 lock files
rm -f /tmp/.X*-lock 2>/dev/null || true

echo "✅ Chromium lock cleanup complete"
