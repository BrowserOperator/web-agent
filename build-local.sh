#!/usr/bin/env bash

# Extended local build wrapper for kernel-browser with DevTools
set -e -o pipefail

echo "🔨 Building extended kernel-browser with DevTools frontend..."

# Ensure we're in the right directory
SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
cd "$SCRIPT_DIR"

# Initialize submodules if needed
if [ ! -d "kernel-images/.git" ]; then
    echo "📦 Initializing kernel-images submodule..."
    git submodule update --init --depth 1 kernel-images
fi

if [ ! -d "browser-operator-core/.git" ]; then
    echo "📦 Initializing browser-operator-core submodule..."
    git submodule update --init --depth 1 browser-operator-core
fi

# Check if DevTools image exists
if ! docker images | grep -q "browser-operator-devtools.*latest"; then
    echo "📦 DevTools image not found, building it first..."
    echo "   This is a one-time operation and will take ~30 minutes..."
    make build-devtools
else
    echo "✅ Using existing DevTools image"
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