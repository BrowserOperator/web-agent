#!/bin/bash
# Test script to verify tracing configuration

echo "==================================================================="
echo "Testing Langfuse Tracing Configuration"
echo "==================================================================="

# 1. Check environment variables in container
echo ""
echo "1. Checking container environment variables..."
docker exec kernel-browser-extended printenv | grep -E "LANGFUSE|OPENROUTER|GROQ|LITELLM" || echo "  ⚠️  No env vars found"

# 2. Check env.js file
echo ""
echo "2. Checking /usr/share/nginx/devtools/env.js file..."
docker exec kernel-browser-extended cat /usr/share/nginx/devtools/env.js | grep -A2 "LANGFUSE" || echo "  ⚠️  No Langfuse keys in env.js"

# 3. Check config file
echo ""
echo "3. Checking config YAML file..."
docker exec kernel-browser-extended cat /config/browser-operator-config.yaml 2>/dev/null | grep -A5 "tracing:" || echo "  ⚠️  No config file or no tracing section"

# 4. Check if env.js is accessible via HTTP
echo ""
echo "4. Checking env.js via HTTP..."
curl -s http://localhost:8001/env.js | grep -o "LANGFUSE_PUBLIC_KEY:" || echo "  ⚠️  env.js not accessible or no Langfuse keys"

# 5. Run a simple eval test
echo ""
echo "5. Running math-001 eval test..."
echo "   (Tracing should be initialized when EvaluationRunner loads)"
cd /Users/olehluchkiv/Work/browser/web-agent/evals
python3 run.py --path data/test-simple/math-001.yaml 2>&1 | head -20

echo ""
echo "==================================================================="
echo "Test Complete"
echo "==================================================================="
echo ""
echo "To manually check tracing in the browser:"
echo "1. Open http://localhost:8000 in your browser"
echo "2. Open DevTools (F12) and go to the Console tab"
echo "3. Look for [TracingInit] and [ConfigLoader] messages"
echo "4. Run: window.isTracingEnabled()"
echo "5. Run: window.getTracingConfig()"
echo ""
