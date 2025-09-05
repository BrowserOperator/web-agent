# Makefile for kernel-browser local development
# Using kernel-images native build system

.PHONY: help build run stop logs clean dev status shell test

# Default target
help: ## Show this help message
	@echo "Kernel Browser - Local Development (using kernel-images build system)"
	@echo "=================================================================="
	@echo ""
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

init: ## Initialize submodules (run this first)
	git submodule update --init --recursive
	@echo "✅ Submodules initialized"

build: init ## Build extended image with DevTools frontend
	@echo "🔨 Building extended kernel-browser with DevTools frontend..."
	docker build -f Dockerfile.local -t kernel-browser:extended .
	@echo "✅ Extended build complete"

run: ## Run extended container with DevTools (interactive)
	@echo "🚀 Starting extended kernel-browser with DevTools..."
	./run-local.sh

compose-up: build ## Start with docker-compose (background)
	@echo "🚀 Starting with docker-compose..."
	docker-compose up -d
	@$(MAKE) --no-print-directory info
	@echo ""
	@echo "📊 View logs with: make logs"

compose-dev: build ## Start with docker-compose (foreground with logs)
	@echo "🚀 Starting with docker-compose in development mode..."
	docker-compose up
	
dev: compose-dev ## Alias for compose-dev

stop: ## Stop all containers
	@echo "🛑 Stopping containers..."
	docker-compose down
	docker stop kernel-browser-extended 2>/dev/null || true
	docker rm kernel-browser-extended 2>/dev/null || true
	@echo "✅ Containers stopped"

restart: ## Restart containers
	@$(MAKE) --no-print-directory stop
	@$(MAKE) --no-print-directory compose-up

logs: ## Show container logs
	docker-compose logs -f kernel-browser || docker logs -f kernel-browser-extended

status: ## Show container status
	@echo "Docker Compose Status:"
	@docker-compose ps || true
	@echo ""
	@echo "Direct Container Status:"
	@docker ps --filter name=kernel-browser

shell: ## Get shell access to running container
	docker exec -it kernel-browser-extended bash || docker-compose exec kernel-browser bash

info: ## Show connection information
	@echo ""
	@echo "🌐 Service Access Points:"
	@echo "   WebRTC Client:        http://localhost:8080"
	@echo "   Chrome DevTools:      http://localhost:9222/json"
	@echo "   Recording API:        http://localhost:444/api"
	@echo "   Enhanced DevTools UI: http://localhost:8001"
	@echo "   DevTools Health:      http://localhost:8001/health"

test: ## Test service endpoints
	@echo "🧪 Testing service endpoints..."
	@echo -n "WebRTC Client (8080): "
	@curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/ || echo "Failed to connect"
	@echo ""
	@echo -n "Chrome DevTools (9222): "
	@curl -s -o /dev/null -w "%{http_code}" http://localhost:9222/json/version || echo "Failed to connect" 
	@echo ""
	@echo -n "Recording API (444): "
	@curl -s -o /dev/null -w "%{http_code}" http://localhost:444/ && echo " (404 is normal - API is running)" || echo "Failed to connect"
	@echo ""
	@echo -n "DevTools UI (8001): "
	@curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/ || echo "Failed to connect"
	@echo ""
	@echo -n "DevTools Health (8001): "
	@curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/health || echo "Failed to connect"
	@echo ""
	@echo "🎯 All services are ready! Access points:"
	@echo "   WebRTC Client:        http://localhost:8080"
	@echo "   Chrome DevTools:      http://localhost:9222/json"
	@echo "   Enhanced DevTools UI: http://localhost:8001"

clean: stop ## Clean up everything
	@echo "🧹 Cleaning up..."
	docker-compose down -v 2>/dev/null || true
	docker rmi kernel-browser:extended 2>/dev/null || true
	docker system prune -f
	rm -rf recordings/* 2>/dev/null || true
	rm -rf kernel-images/images/chromium-headful/.tmp 2>/dev/null || true
	@echo "✅ Cleanup complete"

# Alternative commands for different approaches
native-build: init ## Build using kernel-images native script directly
	cd kernel-images/images/chromium-headful && \
	UKC_TOKEN=dummy-token UKC_METRO=dummy-metro IMAGE=kernel-browser:local ./build-docker.sh

native-run: ## Run using kernel-images native script directly  
	cd kernel-images/images/chromium-headful && \
	UKC_TOKEN=dummy-token UKC_METRO=dummy-metro IMAGE=kernel-browser:local NAME=kernel-browser-local ENABLE_WEBRTC=true ./run-docker.sh

# Quick development workflow
quick: init build compose-up test ## Quick setup: init + build + run + test

