#!/bin/bash

set -o pipefail -o nounset

echo "[cloudrun-wrapper] Starting Cloud Run optimized kernel-images"

# Cloud Run specific environment setup
export WITHDOCKER=true
export RUN_AS_ROOT=false
export ENABLE_WEBRTC=true
export DISPLAY_NUM=1
export HEIGHT=768
export WIDTH=1024

# Port configuration for Cloud Run
export PORT=${PORT:-8080}
export CHROMIUM_FLAGS="${CHROMIUM_FLAGS:---user-data-dir=/home/kernel/user-data --disable-dev-shm-usage --disable-gpu --start-maximized --disable-software-rasterizer --remote-allow-origins=* --no-sandbox --disable-setuid-sandbox --disable-features=VizDisplayCompositor}"

# Setup directories with proper permissions
mkdir -p /tmp/nginx_client_temp /tmp/nginx_proxy_temp /tmp/nginx_fastcgi_temp \
         /tmp/nginx_uwsgi_temp /tmp/nginx_scgi_temp \
         /home/kernel/user-data /home/kernel/.config /home/kernel/.cache \
         /tmp/runtime-kernel /var/log/neko /tmp/recordings

# Test nginx configuration
echo "[cloudrun-wrapper] Testing nginx configuration..."
if ! nginx -t; then
    echo "[cloudrun-wrapper] ERROR: nginx configuration test failed"
    exit 1
fi

# Start supervisor for kernel-images services in background
echo "[cloudrun-wrapper] Starting kernel-images services..."
supervisord -c /etc/supervisor/supervisord-cloudrun.conf -n &
SUPERVISOR_PID=$!

# Wait a moment for services to start
sleep 5

# Cleanup function
cleanup() {
    echo "[cloudrun-wrapper] Cleaning up..."
    kill $SUPERVISOR_PID 2>/dev/null || true
    supervisorctl -c /etc/supervisor/supervisord-cloudrun.conf stop all 2>/dev/null || true
}
trap cleanup TERM INT

# Start nginx in foreground (main process for Cloud Run)
echo "[cloudrun-wrapper] Starting nginx proxy on port $PORT"
nginx -g "daemon off;"