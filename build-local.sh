#!/usr/bin/env bash

# Extended local build wrapper for kernel-browser with DevTools
set -e -o pipefail

echo "🔨 Building extended kernel-browser with DevTools frontend..."

# Ensure we're in the right directory
SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
cd "$SCRIPT_DIR"

# Check if kernel-images submodule exists and is initialized
if [ ! -d "kernel-images" ]; then
    echo "❌ Error: kernel-images submodule not found"
    echo "   Run: git submodule update --init --recursive"
    exit 1
fi

if [ ! -f "kernel-images/images/chromium-headful/build-docker.sh" ]; then
    echo "❌ Error: kernel-images submodule appears empty"
    echo "   Run: git submodule update --init --recursive"
    exit 1
fi

echo "🚀 Starting extended build with Docker..."
echo "   Using: Dockerfile.local"
echo "   Target image: kernel-browser:extended"

# Build using Docker with extended Dockerfile
docker build -f Dockerfile.local -t kernel-browser:extended .

echo "✅ Extended build completed successfully!"
echo "   Image built: kernel-browser:extended"
echo "   Includes: Chromium + DevTools frontend + WebRTC"
echo ""
echo "🏃 To run locally, use: ./run-local.sh"