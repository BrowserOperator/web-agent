#!/bin/bash

set -o pipefail -o nounset

echo "[cloudrun-kernel] Starting kernel-images optimized for Cloud Run"

# Cloud Run specific environment setup
export WITHDOCKER=true
export RUN_AS_ROOT=false
export ENABLE_WEBRTC=true
export DISPLAY_NUM=1
export HEIGHT=768
export WIDTH=1024
export PORT=${PORT:-8080}

# Kernel-images environment
export DISPLAY=:1
export INTERNAL_PORT="${INTERNAL_PORT:-9223}"
export CHROME_PORT="${CHROME_PORT:-9222}"

# Setup directories for kernel-images (non-root compatible)
mkdir -p /tmp/nginx_client_temp /tmp/nginx_proxy_temp /tmp/nginx_fastcgi_temp \
         /tmp/nginx_uwsgi_temp /tmp/nginx_scgi_temp \
         /home/kernel/user-data /home/kernel/.config /home/kernel/.pki \
         /home/kernel/.cache /var/log/supervisord

# Test nginx configuration
echo "[cloudrun-kernel] Testing nginx configuration..."
if ! nginx -t; then
    echo "[cloudrun-kernel] ERROR: nginx configuration test failed"
    exit 1
fi

# Start supervisord in non-daemon mode in background
echo "[cloudrun-kernel] Starting supervisord..."
supervisord -c /etc/supervisor/supervisord-cloudrun.conf &
SUPERVISOR_PID=$!

# Wait for supervisord socket
echo "[cloudrun-kernel] Waiting for supervisord socket..."
for i in {1..30}; do
    if [ -S /tmp/supervisor.sock ]; then
        break
    fi
    sleep 0.2
done

# Start services in correct order (kernel-images sequence)
echo "[cloudrun-kernel] Starting Xorg..."
supervisorctl -c /etc/supervisor/supervisord-cloudrun.conf start xorg
echo "[cloudrun-kernel] Waiting for Xorg display $DISPLAY..."
for i in {1..50}; do
  if xdpyinfo -display "$DISPLAY" >/dev/null 2>&1; then
    break
  fi
  sleep 0.2
done

echo "[cloudrun-kernel] Starting Mutter..."
supervisorctl -c /etc/supervisor/supervisord-cloudrun.conf start mutter
echo "[cloudrun-kernel] Waiting for Mutter to be ready..."
timeout=30
while [ $timeout -gt 0 ]; do
  if xdotool search --class "mutter" >/dev/null 2>&1; then
    break
  fi
  sleep 1
  ((timeout--))
done

echo "[cloudrun-kernel] Starting D-Bus..."
supervisorctl -c /etc/supervisor/supervisord-cloudrun.conf start dbus
echo "[cloudrun-kernel] Waiting for D-Bus system bus..."
for i in {1..50}; do
  if [ -S /tmp/dbus/system_bus_socket ]; then
    break
  fi
  sleep 0.2
done
export DBUS_SESSION_BUS_ADDRESS="unix:path=/tmp/dbus/system_bus_socket"

# Start Squid proxy if enabled
PROXY_ENABLED="${PROXY_ENABLED:-true}"
if [[ "$PROXY_ENABLED" == "true" ]]; then
  echo "[cloudrun-kernel] Starting Squid proxy..."
  supervisorctl -c /etc/supervisor/supervisord-cloudrun.conf start squid
  echo "[cloudrun-kernel] Waiting for Squid proxy on port 3128..."
  for i in {1..30}; do
    if nc -z 127.0.0.1 3128 2>/dev/null; then
      break
    fi
    sleep 0.5
  done
  echo "[cloudrun-kernel] Squid proxy ready"
fi

echo "[cloudrun-kernel] Starting Chromium..."
supervisorctl -c /etc/supervisor/supervisord-cloudrun.conf start chromium
echo "[cloudrun-kernel] Waiting for Chromium on $INTERNAL_PORT..."
for i in {1..100}; do
  if nc -z 127.0.0.1 "$INTERNAL_PORT" 2>/dev/null; then
    break
  fi
  sleep 0.2
done

if [[ "${ENABLE_WEBRTC:-}" == "true" ]]; then
  echo "[cloudrun-kernel] Starting Neko (WebRTC)..."
  supervisorctl -c /etc/supervisor/supervisord-cloudrun.conf start neko
  echo "[cloudrun-kernel] Waiting for Neko on port 8080..."
  while ! nc -z 127.0.0.1 8080 2>/dev/null; do
    sleep 0.5
  done
fi

echo "[cloudrun-kernel] Starting kernel-images API..."
supervisorctl -c /etc/supervisor/supervisord-cloudrun.conf start kernel-images-api

# Wait for API to be ready
API_PORT="${KERNEL_IMAGES_API_PORT:-10001}"
echo "[cloudrun-kernel] Waiting for API on port $API_PORT..."
while ! nc -z 127.0.0.1 "$API_PORT" 2>/dev/null; do
  sleep 0.5
done

# Cleanup function
cleanup() {
    echo "[cloudrun-kernel] Cleaning up..."
    supervisorctl -c /etc/supervisor/supervisord-cloudrun.conf stop all 2>/dev/null || true
    kill $SUPERVISOR_PID 2>/dev/null || true
}
trap cleanup TERM INT

echo "[cloudrun-kernel] All services started successfully!"
echo "[cloudrun-kernel] Starting nginx proxy on port $PORT..."

# Start nginx in foreground (main process for Cloud Run)
nginx -g "daemon off;"