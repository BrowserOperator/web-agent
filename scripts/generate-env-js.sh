#!/bin/bash
# Generate env.js file for browser-side environment variable access

ENV_JS_PATH="/usr/share/nginx/devtools/env.js"

cat > "$ENV_JS_PATH" << EOF
// Auto-generated environment variables for browser-side config substitution
// Generated at container startup
window.__ENV__ = {
  LITELLM_API_KEY: "${LITELLM_API_KEY:-}",
  OPENROUTER_API_KEY: "${OPENROUTER_API_KEY:-}",
  GROQ_API_KEY: "${GROQ_API_KEY:-}",
  LANGFUSE_PUBLIC_KEY: "${LANGFUSE_PUBLIC_KEY:-}",
  LANGFUSE_SECRET_KEY: "${LANGFUSE_SECRET_KEY:-}",
  MCP_SERVER1_TOKEN: "${MCP_SERVER1_TOKEN:-}",
  MILVUS_PASSWORD: "${MILVUS_PASSWORD:-}",
  MILVUS_OPENAI_KEY: "${MILVUS_OPENAI_KEY:-}"
};
EOF

echo "✅ Generated $ENV_JS_PATH with environment variables"
