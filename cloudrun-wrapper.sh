#!/bin/bash

set -o pipefail -o nounset

echo "[cloudrun-wrapper] Starting Cloud Run optimized kernel-images"

# Cloud Run specific environment setup
export WITHDOCKER=true
export RUN_AS_ROOT=false
export ENABLE_WEBRTC=true
export DISPLAY_NUM=1
export HEIGHT=768
export WIDTH=1024
export NEKO_BIND=:8081

# Get fresh Twilio TURN credentials if available
if [ -f /twilio-credential-updater.sh ]; then
    echo "[cloudrun-wrapper] Getting fresh Twilio TURN credentials..."
    source /twilio-credential-updater.sh
else
    echo "[cloudrun-wrapper] Twilio updater not found, using credentials from environment"
fi

# Port configuration for Cloud Run
export PORT=${PORT:-8080}
export CHROMIUM_FLAGS="${CHROMIUM_FLAGS:---user-data-dir=/home/kernel/user-data --disable-dev-shm-usage --disable-gpu --start-maximized --disable-software-rasterizer --remote-allow-origins=* --no-sandbox --disable-setuid-sandbox --disable-features=VizDisplayCompositor --custom-devtools-frontend=http://localhost:8001/ https://www.google.com}"

# Setup directories with proper permissions
mkdir -p /tmp/nginx_client_temp /tmp/nginx_proxy_temp /tmp/nginx_fastcgi_temp \
         /tmp/nginx_uwsgi_temp /tmp/nginx_scgi_temp \
         /tmp/nginx_devtools_client_temp /tmp/nginx_devtools_proxy_temp /tmp/nginx_devtools_fastcgi_temp \
         /tmp/nginx_devtools_uwsgi_temp /tmp/nginx_devtools_scgi_temp \
         /home/kernel/user-data /home/kernel/.config /home/kernel/.cache \
         /tmp/runtime-kernel /var/log/neko /tmp/recordings \
         /tmp/supervisord /tmp/dbus

# Start nginx immediately in background to respond to CloudRun health checks
echo "[cloudrun-wrapper] Starting nginx proxy on port $PORT (background)"

# Create nginx config file
cat > /tmp/nginx.conf <<EOF
worker_processes 1;
pid /tmp/cloudrun-nginx.pid;
error_log /tmp/cloudrun-nginx-error.log;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    
    # Create temp directories for nginx (non-root execution)
    client_body_temp_path /tmp/nginx_client_temp;
    proxy_temp_path /tmp/nginx_proxy_temp;
    fastcgi_temp_path /tmp/nginx_fastcgi_temp;
    uwsgi_temp_path /tmp/nginx_uwsgi_temp;
    scgi_temp_path /tmp/nginx_scgi_temp;
    
    # WebSocket support
    map \$http_upgrade \$connection_upgrade {
        default upgrade;
        "" close;
    }

    server {
        listen $PORT;
        server_name _;

        # Health check endpoint (required by Cloud Run)
        location /health {
            access_log off;
            add_header Content-Type text/plain;
            return 200 "OK\n";
        }

        # WebSocket connection for neko WebRTC
        location /ws {
            proxy_pass http://127.0.0.1:8081/ws;
            proxy_http_version 1.1;
            proxy_set_header Upgrade \$http_upgrade;
            proxy_set_header Connection \$connection_upgrade;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
            proxy_read_timeout 86400;
            proxy_send_timeout 86400;
        }

        # WebRTC client (main interface)
        location / {
            proxy_pass http://127.0.0.1:8081;
            proxy_http_version 1.1;
            proxy_set_header Upgrade \$http_upgrade;
            proxy_set_header Connection \$connection_upgrade;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
            proxy_read_timeout 86400;
            proxy_send_timeout 86400;
        }

        # Chrome DevTools Protocol WebSocket (use different path to avoid conflict)
        location /cdp/ws {
            proxy_pass http://127.0.0.1:9223;
            proxy_http_version 1.1;
            proxy_set_header Upgrade \$http_upgrade;
            proxy_set_header Connection \$connection_upgrade;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
            proxy_read_timeout 86400;
            proxy_send_timeout 86400;
        }

        # Chrome DevTools Protocol HTTP endpoints
        location /json {
            proxy_pass http://127.0.0.1:9223/json;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
        }
        
        # Chrome DevTools Protocol HTTP endpoints (with trailing slash)
        location /json/ {
            proxy_pass http://127.0.0.1:9223/json/;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
        }

        # Recording API
        location /api {
            proxy_pass http://127.0.0.1:10001;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
            proxy_read_timeout 86400;
            proxy_send_timeout 86400;
        }

        # Recording API direct (alternative path)
        location /recording {
            proxy_pass http://127.0.0.1:10001;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
            proxy_read_timeout 86400;
            proxy_send_timeout 86400;
        }

        # Enhanced DevTools Frontend
        location /devtools/ {
            proxy_pass http://127.0.0.1:8001/;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
            proxy_set_header Accept-Encoding gzip;
            proxy_read_timeout 86400;
            proxy_send_timeout 86400;
        }
    }
}
EOF

# Start supervisor for kernel-images services in background first
echo "[cloudrun-wrapper] Starting kernel-images services..."
supervisord -c /etc/supervisor/supervisord-cloudrun.conf &
SUPERVISOR_PID=$!

# Wait for key services to be ready before starting nginx
echo "[cloudrun-wrapper] Waiting for backend services to start..."

# Wait for neko service (port 8081) to be ready
for i in {1..60}; do
    if curl -s http://127.0.0.1:8081/ > /dev/null 2>&1; then
        echo "[cloudrun-wrapper] Neko service is ready"
        break
    fi
    if [ $i -eq 60 ]; then
        echo "[cloudrun-wrapper] Warning: Neko service not ready after 60 seconds, starting nginx anyway"
    fi
    sleep 1
done

# Start nginx in foreground (required for Cloud Run)
echo "[cloudrun-wrapper] Starting nginx proxy on port $PORT"
exec nginx -g "daemon off;" -c /tmp/nginx.conf