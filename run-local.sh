#!/usr/bin/env bash

# Local run wrapper for kernel-images chromium-headful
set -e -o pipefail

echo "🚀 Starting kernel-browser locally using kernel-images run system..."

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

# Set environment variables for local development
export IMAGE="kernel-browser:local"
export NAME="kernel-browser-local"
export ENABLE_WEBRTC="true"
export RUN_AS_ROOT="false"

# Set dummy UKC variables to bypass cloud requirements (we only need Docker)
export UKC_TOKEN="dummy-token-for-local-run"
export UKC_METRO="dummy-metro-for-local-run"

# Local-friendly Chrome flags (less restrictive than cloud)
export CHROMIUM_FLAGS="--user-data-dir=/home/kernel/user-data --disable-dev-shm-usage --start-maximized --remote-allow-origins=* --no-sandbox --disable-setuid-sandbox"

echo "🔧 Configuration:"
echo "   Image: $IMAGE"
echo "   Container: $NAME"
echo "   WebRTC: $ENABLE_WEBRTC"
echo "   Run as root: $RUN_AS_ROOT"
echo "   Recordings: $SCRIPT_DIR/recordings"
echo ""

echo "🏃 Starting container with kernel-images run system..."

# Run using the official run script
./run-docker.sh

echo ""
echo "🌐 Service should be accessible at:"
echo "   WebRTC Client:     http://localhost:8080"
echo "   Chrome DevTools:   http://localhost:9222"
echo "   Recording API:     http://localhost:444"