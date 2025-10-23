#!/bin/bash
set -e

echo "🧪 Testing browser-agent-server startup script..."

# Build only the browser-agent-server stage
echo "📦 Building browser-agent-server stage..."
docker build \
  --file Dockerfile.cloudrun \
  --target browser-agent-server-builder \
  -t browser-agent-server-test \
  .

echo "✅ Build successful!"
echo ""
echo "📂 Contents of /browser-agent-server:"
docker run --rm browser-agent-server-test ls -la /browser-agent-server

echo ""
echo "📄 Checking package.json:"
docker run --rm browser-agent-server-test cat /browser-agent-server/package.json | grep '"type"'

echo ""
echo "🔍 Checking if node_modules exist:"
docker run --rm browser-agent-server-test ls -la /browser-agent-server/node_modules | head -5

echo ""
echo "✅ All checks passed! Eval-server build is working."
echo ""
echo "Next: Test the full image with 'docker build -f Dockerfile.cloudrun -t kernel-browser:cloudrun-test .'"
