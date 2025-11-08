#!/bin/bash
# Container initialization script
# Runs before services start to clean up stale lock files and configure WebArena routing

set +e  # Don't exit on errors

echo "🔧 [init] Running container initialization..."

# Generate Chromium flags dynamically based on WebArena configuration
# If WEBARENA_HOST_IP is set, add DNS mapping for WebArena domains
if [ -n "$WEBARENA_HOST_IP" ]; then
  echo "🌐 [init] Configuring WebArena DNS mapping to $WEBARENA_HOST_IP..."
  cat > /chromium/flags << EOF
--host-resolver-rules="MAP wikipedia.com $WEBARENA_HOST_IP,MAP www.wikipedia.com $WEBARENA_HOST_IP,MAP en.wikipedia.org $WEBARENA_HOST_IP,MAP wikipedia.org $WEBARENA_HOST_IP,MAP www.wikipedia.org $WEBARENA_HOST_IP,MAP gitlab.com $WEBARENA_HOST_IP,MAP www.gitlab.com $WEBARENA_HOST_IP,MAP reddit.com $WEBARENA_HOST_IP,MAP www.reddit.com $WEBARENA_HOST_IP,MAP onestopshop.com $WEBARENA_HOST_IP,MAP www.onestopshop.com $WEBARENA_HOST_IP,MAP onestopmarket.com $WEBARENA_HOST_IP,EXCLUDE localhost"
--disable-features=HttpsUpgrades,TransportSecurity
--ignore-certificate-errors
--test-type
--auto-open-devtools-for-tabs
EOF
else
  echo "ℹ️  [init] WEBARENA_HOST_IP not configured, using standard Chromium flags (no DNS mapping)..."
  cat > /chromium/flags << EOF
--disable-features=HttpsUpgrades,TransportSecurity
--ignore-certificate-errors
--test-type
--auto-open-devtools-for-tabs
EOF
fi

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

# Add route to WebArena network via Docker host gateway (if configured)
# This allows the container to reach hosts on the WebArena network
# Only runs if WEBARENA_NETWORK environment variable is set
if [ -n "$WEBARENA_NETWORK" ] && command -v ip >/dev/null 2>&1; then
  GATEWAY=$(ip route | grep default | awk '{print $3}')
  if [ -n "$GATEWAY" ]; then
    echo "🌐 [init] Adding route to $WEBARENA_NETWORK via $GATEWAY..."
    ip route add $WEBARENA_NETWORK via $GATEWAY 2>/dev/null || echo "⚠️  [init] Route already exists or failed to add"
  else
    echo "⚠️  [init] WEBARENA_NETWORK is set but no default gateway found"
  fi
else
  if [ -z "$WEBARENA_NETWORK" ]; then
    echo "ℹ️  [init] WEBARENA_NETWORK not configured, skipping WebArena routing"
  fi
fi

echo "✅ [init] Container initialization complete"
exit 0
