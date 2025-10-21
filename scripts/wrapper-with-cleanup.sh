#!/bin/bash
# Wrapper script extension that adds Chromium lock cleanup
# This script will be injected into the Docker image

# Add this right after supervisord starts
cleanup_chromium_locks() {
  echo "[wrapper] 🧹 Cleaning up Chromium lock files..."

  # Remove Chromium profile locks from persistent data directory
  rm -f /data/user-data/SingletonLock \
        /data/user-data/SingletonSocket \
        /data/user-data/SingletonCookie \
        2>/dev/null || true

  # Remove X11 lock files from /tmp
  rm -f /tmp/.X*-lock 2>/dev/null || true

  echo "[wrapper] ✅ Chromium lock cleanup complete"
}

# Export the function so it can be called from the main wrapper
export -f cleanup_chromium_locks
