#!/bin/bash
set -e

echo "🧪 Testing eval-server startup script..."

# Build only the eval-server stage
echo "📦 Building eval-server stage..."
docker build \
  --file Dockerfile.cloudrun \
  --target eval-server-builder \
  -t eval-server-test \
  .

echo "✅ Build successful!"
echo ""
echo "📂 Contents of /eval-server:"
docker run --rm eval-server-test ls -la /eval-server

echo ""
echo "📄 Checking package.json:"
docker run --rm eval-server-test cat /eval-server/package.json | grep '"type"'

echo ""
echo "🔍 Checking if node_modules exist:"
docker run --rm eval-server-test ls -la /eval-server/node_modules | head -5

echo ""
echo "✅ All checks passed! Eval-server build is working."
echo ""
echo "Next: Test the full image with 'docker build -f Dockerfile.cloudrun -t kernel-browser:cloudrun-test .'"
