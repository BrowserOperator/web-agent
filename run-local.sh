#!/usr/bin/env bash

# Extended local run wrapper for kernel-images chromium-headful + DevTools
set -e -o pipefail

echo "🚀 Starting kernel-browser (EXTENDED) locally using kernel-images run system..."

# Ensure we're in the right directory
SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
cd "$SCRIPT_DIR"

# Check if kernel-images submodule exists
if [ ! -d "kernel-images" ] || [ ! -f "kernel-images/images/chromium-headful/run-docker.sh" ]; then
    echo "❌ Error: kernel-images submodule not found or incomplete"
    echo "   Run: git submodule update --init --recursive"
    exit 1
fi

# Create local recordings directory
mkdir -p "$SCRIPT_DIR/recordings"

# Change to kernel-images directory
cd kernel-images/images/chromium-headful

# Make run script executable
chmod +x run-docker.sh

# Set environment variables for extended local development
export IMAGE="kernel-browser:extended"
export NAME="kernel-browser-extended"
export ENABLE_WEBRTC="true"
export RUN_AS_ROOT="false"

# Set dummy UKC variables to satisfy kernel-images script requirements (not used in local Docker)
export UKC_TOKEN="dummy-token-for-local-run"
export UKC_METRO="dummy-metro-for-local-run"


# Local-friendly Chrome flags (less restrictive than cloud) + custom DevTools frontend
export CHROMIUM_FLAGS="--user-data-dir=/data/user-data --disable-dev-shm-usage --start-maximized --remote-allow-origins=* --no-sandbox --disable-setuid-sandbox --custom-devtools-frontend=http://localhost:8001/"

echo "🔧 Configuration:"
echo "   Image: $IMAGE"
echo "   Container: $NAME"
echo "   WebRTC: $ENABLE_WEBRTC"
echo "   DevTools UI: enabled"
echo "   Run as root: $RUN_AS_ROOT"
echo "   Recordings: $SCRIPT_DIR/recordings"
echo ""

echo "🏃 Starting extended container with kernel-images run system..."

# Execute the kernel-images script setup but override the final docker run command
# We'll replicate the essential parts here to avoid the sed hack

# Source common build vars
source ../../shared/ensure-common-build-run-vars.sh chromium-headful

# Directory on host where recordings will be saved
HOST_RECORDINGS_DIR="$SCRIPT_DIR/recordings"
mkdir -p "$HOST_RECORDINGS_DIR"

# Chromium data directory for persistence
# Set CHROMIUM_DATA_HOST to customize location (default: ./chromium-data)
# Set CHROMIUM_DATA_HOST="" to disable persistence (ephemeral mode)
if [[ "${CHROMIUM_DATA_HOST+set}" == "set" && -z "$CHROMIUM_DATA_HOST" ]]; then
  echo "🔄 Using ephemeral Chromium data (no persistence)"
  CHROMIUM_DATA_VOLUME=""
else
  # Default to ./chromium-data if not specified
  CHROMIUM_DATA_HOST="${CHROMIUM_DATA_HOST:-$SCRIPT_DIR/chromium-data}"
  echo "🗂️  Using persistent Chromium data directory: $CHROMIUM_DATA_HOST"
  CHROMIUM_DATA_REAL=$(realpath "$CHROMIUM_DATA_HOST" 2>/dev/null || echo "")
  if [[ -z "$CHROMIUM_DATA_REAL" ]]; then
    # Path doesn't exist yet, try to create it first
    mkdir -p "$CHROMIUM_DATA_HOST"
    CHROMIUM_DATA_REAL=$(realpath "$CHROMIUM_DATA_HOST" 2>/dev/null || echo "")
    if [[ -z "$CHROMIUM_DATA_REAL" ]]; then
      echo "❌ Error: Invalid path $CHROMIUM_DATA_HOST"
      exit 1
    fi
  fi

  # Clean up Chromium lock files from previous runs to prevent profile lock errors
  # These files prevent concurrent access but remain after container crashes
  echo "🧹 Cleaning Chromium lock files from previous runs..."
  rm -f "$CHROMIUM_DATA_REAL/user-data/SingletonLock" \
        "$CHROMIUM_DATA_REAL/user-data/SingletonSocket" \
        "$CHROMIUM_DATA_REAL/user-data/SingletonCookie" 2>/dev/null || true

  CHROMIUM_DATA_VOLUME="${CHROMIUM_DATA_REAL}:/data"
fi

# Build Chromium flags file and mount
CHROMIUM_FLAGS_DEFAULT="--user-data-dir=/data/user-data --disable-dev-shm-usage --disable-gpu --start-maximized --disable-software-rasterizer --remote-allow-origins=*"
if [[ "$RUN_AS_ROOT" == "true" ]]; then
  CHROMIUM_FLAGS_DEFAULT="$CHROMIUM_FLAGS_DEFAULT --no-sandbox --no-zygote"
fi
CHROMIUM_FLAGS="${CHROMIUM_FLAGS:-$CHROMIUM_FLAGS_DEFAULT}"
rm -rf .tmp/chromium
mkdir -p .tmp/chromium
FLAGS_FILE="$(pwd)/.tmp/chromium/flags"
echo "$CHROMIUM_FLAGS" > "$FLAGS_FILE"

# Build docker run argument list
RUN_ARGS=(
  --name "$NAME"
  --privileged
  --tmpfs /dev/shm:size=2g
  -v "$HOST_RECORDINGS_DIR:/recordings"
  --memory 8192m
  -p 9222:9222
  -p 444:10001
  -p 8000:8000 \
  -p 8001:8001 \
  -p 8080:8080 \
  -p 8081:8081 \
  -p 8082:8082
  -e DISPLAY_NUM=1
  -e HEIGHT=768
  -e WIDTH=1024
  -e RUN_AS_ROOT="$RUN_AS_ROOT"
  --mount type=bind,src="$FLAGS_FILE",dst=/chromium/flags,ro
)

# Add Chromium data volume if specified
if [[ -n "$CHROMIUM_DATA_VOLUME" ]]; then
  RUN_ARGS+=( -v "${CHROMIUM_DATA_VOLUME}" )
fi

# Add URLS environment variable if provided
if [[ -n "${URLS:-}" ]]; then
  echo "   URLs: $URLS"
  RUN_ARGS+=( -e URLS="$URLS" )
fi

# WebRTC port mapping
if [[ "${ENABLE_WEBRTC:-}" == "true" ]]; then
  echo "Running container with WebRTC"
  RUN_ARGS+=( -e ENABLE_WEBRTC=true )
  if [[ -n "${NEKO_ICESERVERS:-}" ]]; then
    RUN_ARGS+=( -e NEKO_ICESERVERS="$NEKO_ICESERVERS" )
  else
    RUN_ARGS+=( -e NEKO_WEBRTC_EPR=57000-57100 )
    RUN_ARGS+=( -e NEKO_WEBRTC_NAT1TO1=127.0.0.1 )
    RUN_ARGS+=( -p 57000-57100:57000-57100/udp )
  fi
fi

# Run with our additional DevTools port mapping
docker rm -f "$NAME" 2>/dev/null || true
docker run -d "${RUN_ARGS[@]}" "$IMAGE"

echo ""
echo "🌐 Extended service should be accessible at:"
echo "   WebRTC Client:        http://localhost:8000"
echo "   Eval Server HTTP API: http://localhost:8080"
echo "   WebRTC (Neko):        http://localhost:8081"
echo "   Eval Server WS:       ws://localhost:8082"
echo "   Chrome DevTools:      http://localhost:9222"
echo "   Recording API:        http://localhost:444"
echo "   Enhanced DevTools UI: http://localhost:8001"