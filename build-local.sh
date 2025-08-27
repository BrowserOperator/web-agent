#!/usr/bin/env bash

# Local build wrapper for kernel-images chromium-headful
set -e -o pipefail

echo "🔨 Building kernel-browser using kernel-images build system..."

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

# Change to kernel-images directory and build using their system
echo "📁 Changing to kernel-images directory..."
cd kernel-images/images/chromium-headful

# Make build script executable
chmod +x build-docker.sh

# Set image name for local use
export IMAGE="kernel-browser:local"
export NAME="kernel-browser-local"

# Set dummy UKC variables to bypass cloud requirements (we only need Docker)
export UKC_TOKEN="dummy-token-for-local-build"
export UKC_METRO="dummy-metro-for-local-build"

echo "🚀 Starting build with kernel-images build system..."
echo "   Image: $IMAGE"
echo "   Bypassing UKC requirements for local Docker build..."

# Run the official build script
./build-docker.sh

echo "✅ Build completed successfully!"
echo "   Image built: $IMAGE"
echo ""
echo "🏃 To run locally, use: ./run-local.sh"