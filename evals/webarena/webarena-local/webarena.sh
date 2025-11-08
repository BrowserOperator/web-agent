#!/bin/bash
# webarena.sh
# Simple management script for WebArena services

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Start services
start() {
    print_status "Starting WebArena services..."
    docker-compose up -d shopping shopping_admin forum gitlab kiwix homepage
    print_status "Waiting 30 seconds for services to initialize..."
    sleep 30
    print_success "Services started!"
    status
}

# Stop services
stop() {
    print_status "Stopping WebArena services..."
    docker-compose stop
    print_success "Services stopped!"
}

# Restart services
restart() {
    print_status "Restarting WebArena services..."
    docker-compose restart
    print_status "Waiting 30 seconds for services to initialize..."
    sleep 30
    print_success "Services restarted!"
    status
}

# Check service status
status() {
    echo ""
    echo "Service Status:"
    echo "==============="

    check_service "Shopping" "http://localhost:7770"
    check_service "Shopping Admin" "http://localhost:7780"
    check_service "Forum" "http://localhost:9999"
    check_service "GitLab" "http://localhost:8023"
    check_service "Wikipedia" "http://localhost:8888"
    check_service "Homepage" "http://localhost:4399"
    echo ""
}

# Check individual service
check_service() {
    local name=$1
    local url=$2
    local status_code=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")

    if [ "$status_code" = "200" ] || [ "$status_code" = "302" ]; then
        echo -e "  ${GREEN}✓${NC} ${name} (${url})"
    else
        echo -e "  ${RED}✗${NC} ${name} (${url}) - HTTP ${status_code}"
    fi
}

# View logs
logs() {
    local service=$1
    if [ -z "$service" ]; then
        docker-compose logs -f
    else
        docker-compose logs -f "$service"
    fi
}

# Open services in browser
open_browser() {
    print_status "Opening WebArena services in browser..."

    if [[ "$OSTYPE" == "darwin"* ]]; then
        open http://localhost:7770 &
        open http://localhost:9999 &
        open http://localhost:8023 &
        open http://localhost:8888 &
        open http://localhost:4399 &
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        xdg-open http://localhost:7770 &
        xdg-open http://localhost:9999 &
        xdg-open http://localhost:8023 &
        xdg-open http://localhost:8888 &
        xdg-open http://localhost:4399 &
    else
        print_status "Services running at:"
        echo "  http://localhost:7770 - Shopping"
        echo "  http://localhost:9999 - Forum"
        echo "  http://localhost:8023 - GitLab"
        echo "  http://localhost:8888 - Wikipedia"
        echo "  http://localhost:4399 - Homepage"
    fi
}

# Run WebArena test
test() {
    local task_id=${1:-3}
    print_status "Running WebArena task ${task_id}..."
    cd ..
    python3 run_webarena.py --task-id "$task_id" --verbose
}

# Show usage
usage() {
    echo "WebArena Service Manager"
    echo ""
    echo "Usage: ./webarena.sh [command]"
    echo ""
    echo "Commands:"
    echo "  start       Start all WebArena services"
    echo "  stop        Stop all services"
    echo "  restart     Restart all services"
    echo "  status      Check service health"
    echo "  logs [svc]  View logs (optional: specific service)"
    echo "  open        Open all services in browser"
    echo "  test [id]   Run WebArena task (default: task 3)"
    echo "  help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./webarena.sh start"
    echo "  ./webarena.sh status"
    echo "  ./webarena.sh logs gitlab"
    echo "  ./webarena.sh test 1"
    echo ""
}

# Main
case "${1:-help}" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    status)
        status
        ;;
    logs)
        logs "$2"
        ;;
    open)
        open_browser
        ;;
    test)
        test "$2"
        ;;
    help|--help|-h)
        usage
        ;;
    *)
        print_error "Unknown command: $1"
        echo ""
        usage
        exit 1
        ;;
esac
