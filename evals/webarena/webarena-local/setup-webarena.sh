#!/bin/bash
# setup-webarena.sh
# Complete setup script for WebArena local environment

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
IMAGES_DIR="./webarena-images"
DOWNLOAD_BASE_URL="http://metis.lti.cs.cmu.edu/webarena-images"

# Print colored message
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if running in correct directory
check_directory() {
    if [ ! -f "docker-compose.yml" ]; then
        print_error "Must run from webarena-local directory"
        echo "Usage: cd evals/webarena-local && ./setup-webarena.sh"
        exit 1
    fi
}

# Check disk space (need ~75GB)
check_disk_space() {
    print_status "Checking disk space..."

    # Get available space in GB (works on macOS and Linux)
    if [[ "$OSTYPE" == "darwin"* ]]; then
        available_gb=$(df -g . | awk 'NR==2 {print $4}')
    else
        available_gb=$(df -BG . | awk 'NR==2 {print $4}' | sed 's/G//')
    fi

    if [ "$available_gb" -lt 80 ]; then
        print_warning "Low disk space: ${available_gb}GB available (80GB+ recommended)"
        read -p "Continue anyway? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        print_success "Sufficient disk space: ${available_gb}GB available"
    fi
}

# Download Docker image
download_image() {
    local name=$1
    local filename=$2
    local url="${DOWNLOAD_BASE_URL}/${filename}"

    print_status "Downloading ${name}..."

    if [ -f "${IMAGES_DIR}/${filename}" ]; then
        print_success "${name} already downloaded"
        return 0
    fi

    mkdir -p "$IMAGES_DIR"

    # Try wget first, fall back to curl
    if command -v wget &> /dev/null; then
        wget -c -O "${IMAGES_DIR}/${filename}" "$url"
    elif command -v curl &> /dev/null; then
        curl -C - -o "${IMAGES_DIR}/${filename}" "$url"
    else
        print_error "Neither wget nor curl found. Please install one."
        exit 1
    fi

    print_success "${name} downloaded successfully"
}

# Load Docker image
load_image() {
    local name=$1
    local filename=$2
    local image_name=$3

    print_status "Loading ${name} into Docker..."

    # Check if already loaded
    if docker images | grep -q "$image_name"; then
        print_success "${name} already loaded in Docker"
        return 0
    fi

    if [ ! -f "${IMAGES_DIR}/${filename}" ]; then
        print_error "Image file not found: ${IMAGES_DIR}/${filename}"
        return 1
    fi

    docker load --input "${IMAGES_DIR}/${filename}"
    print_success "${name} loaded into Docker"
}

# Download and load all images
setup_images() {
    echo ""
    echo "=========================================="
    echo "Step 1: Downloading Docker Images (~75GB)"
    echo "=========================================="
    echo ""
    print_warning "This will take 30-60 minutes depending on your connection"
    echo ""

    # Shopping website
    download_image "Shopping Website" "shopping_final_0712.tar"
    load_image "Shopping Website" "shopping_final_0712.tar" "shopping_final_0712"

    # Shopping admin
    download_image "Shopping Admin" "shopping_admin_final_0719.tar"
    load_image "Shopping Admin" "shopping_admin_final_0719.tar" "shopping_admin_final_0719"

    # Forum (Reddit)
    download_image "Forum (Reddit)" "postmill-populated-exposed-withimg.tar"
    load_image "Forum" "postmill-populated-exposed-withimg.tar" "postmill-populated-exposed-withimg"

    # GitLab
    download_image "GitLab" "gitlab-populated-final-port8023.tar"
    load_image "GitLab" "gitlab-populated-final-port8023.tar" "gitlab-populated-final-port8023"

    # Wikipedia
    download_image "Wikipedia" "kiwix33.tar"
    load_image "Wikipedia" "kiwix33.tar" "kiwix33"

    print_success "All Docker images downloaded and loaded!"
}

# Start services with docker-compose
start_services() {
    echo ""
    echo "=========================================="
    echo "Step 2: Starting Docker Services"
    echo "=========================================="
    echo ""

    print_status "Starting services (excluding OpenStreetMap)..."
    docker-compose up -d shopping shopping_admin forum gitlab kiwix homepage

    print_status "Waiting for services to initialize (120 seconds)..."
    sleep 120

    print_success "Services started!"
}

# Configure services for localhost
configure_services() {
    echo ""
    echo "=========================================="
    echo "Step 3: Configuring Services"
    echo "=========================================="
    echo ""

    # Configure shopping website
    print_status "Configuring shopping website..."
    docker exec webarena-shopping /var/www/magento2/bin/magento setup:store-config:set --base-url="http://localhost:7770" 2>&1 | grep -v "Warning" || true
    docker exec webarena-shopping mysql -u magentouser -pMyPassword magentodb -e 'UPDATE core_config_data SET value="http://localhost:7770/" WHERE path = "web/secure/base_url";' 2>&1 | grep -v "Warning" || true
    docker exec webarena-shopping /var/www/magento2/bin/magento cache:flush 2>&1 | grep -v "Warning" || true
    print_success "Shopping website configured"

    # Configure shopping admin
    print_status "Configuring shopping admin..."
    docker exec webarena-shopping-admin /var/www/magento2/bin/magento setup:store-config:set --base-url="http://localhost:7780" 2>&1 | grep -v "Warning" || true
    docker exec webarena-shopping-admin mysql -u magentouser -pMyPassword magentodb -e 'UPDATE core_config_data SET value="http://localhost:7780/" WHERE path = "web/secure/base_url";' 2>&1 | grep -v "Warning" || true
    docker exec webarena-shopping-admin /var/www/magento2/bin/magento cache:flush 2>&1 | grep -v "Warning" || true

    # Disable password reset requirements
    docker exec webarena-shopping-admin php /var/www/magento2/bin/magento config:set admin/security/password_is_forced 0 2>&1 | grep -v "Warning" || true
    docker exec webarena-shopping-admin php /var/www/magento2/bin/magento config:set admin/security/password_lifetime 0 2>&1 | grep -v "Warning" || true
    print_success "Shopping admin configured"

    # Configure GitLab
    print_status "Configuring GitLab..."
    docker exec webarena-gitlab sed -i "s|^external_url.*|external_url 'http://localhost:8023'|" /etc/gitlab/gitlab.rb 2>&1 | grep -v "Warning" || true
    docker exec webarena-gitlab gitlab-ctl reconfigure 2>&1 | tail -5
    print_success "GitLab configured"

    # Wait for GitLab to fully restart
    print_status "Waiting for GitLab to restart (60 seconds)..."
    sleep 60
}

# Fix GitLab if it shows 502 errors
fix_gitlab() {
    print_status "Checking GitLab status..."

    if curl -s -o /dev/null -w "%{http_code}" http://localhost:8023 | grep -q "502"; then
        print_warning "GitLab showing 502 errors, attempting fix..."
        docker exec webarena-gitlab rm -f /var/opt/gitlab/postgresql/data/postmaster.pid
        docker exec webarena-gitlab /opt/gitlab/embedded/bin/pg_resetwal -f /var/opt/gitlab/postgresql/data
        docker exec webarena-gitlab gitlab-ctl restart
        print_status "Waiting for GitLab to recover (60 seconds)..."
        sleep 60
    fi
}

# Test all services
test_services() {
    echo ""
    echo "=========================================="
    echo "Step 4: Testing Services"
    echo "=========================================="
    echo ""

    local all_passed=true

    # Test each service
    test_service "Shopping" "http://localhost:7770" || all_passed=false
    test_service "Shopping Admin" "http://localhost:7780" || all_passed=false
    test_service "Forum" "http://localhost:9999" || all_passed=false
    test_service "GitLab" "http://localhost:8023" || all_passed=false
    test_service "Wikipedia" "http://localhost:8888" || all_passed=false
    test_service "Homepage" "http://localhost:4399" || all_passed=false

    echo ""
    if [ "$all_passed" = true ]; then
        print_success "All services are running!"
    else
        print_warning "Some services failed to start. Check logs with: docker-compose logs"
    fi
}

# Test individual service
test_service() {
    local name=$1
    local url=$2

    local status_code=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")

    if [ "$status_code" = "200" ] || [ "$status_code" = "302" ]; then
        print_success "${name} (${url}): OK"
        return 0
    else
        print_error "${name} (${url}): FAILED (HTTP ${status_code})"
        return 1
    fi
}

# Update WebArena task configs for localhost
update_task_configs() {
    echo ""
    echo "=========================================="
    echo "Step 5: Updating Task Configurations"
    echo "=========================================="
    echo ""

    print_status "Updating task URLs to use localhost..."

    local config_dir="../webarena/config_files/examples"

    if [ -d "$config_dir" ]; then
        # Backup original configs
        if [ ! -d "${config_dir}.backup" ]; then
            cp -r "$config_dir" "${config_dir}.backup"
            print_success "Backed up original configs to ${config_dir}.backup"
        fi

        # Replace metis.lti.cs.cmu.edu with localhost
        find "$config_dir" -name "*.json" -exec sed -i '' 's/metis\.lti\.cs\.cmu\.edu/localhost/g' {} \;
        print_success "Task configurations updated for localhost"
    else
        print_warning "Config directory not found: $config_dir"
    fi
}

# Print usage instructions
print_usage() {
    echo ""
    echo "=========================================="
    echo "Setup Complete!"
    echo "=========================================="
    echo ""
    echo "WebArena is now running on:"
    echo "  • Shopping:        http://localhost:7770"
    echo "  • Shopping Admin:  http://localhost:7780"
    echo "  • Forum (Reddit):  http://localhost:9999"
    echo "  • GitLab:          http://localhost:8023"
    echo "  • Wikipedia:       http://localhost:8888"
    echo "  • Homepage:        http://localhost:4399"
    echo ""
    echo "To run WebArena tasks:"
    echo "  cd .."
    echo "  python3 run_webarena.py --task-id 1 --verbose"
    echo "  python3 run_webarena.py --all --limit 10"
    echo ""
    echo "To stop services:"
    echo "  docker-compose down"
    echo ""
    echo "To restart services:"
    echo "  docker-compose start"
    echo ""
    echo "To view logs:"
    echo "  docker-compose logs -f [service-name]"
    echo ""
}

# Main execution
main() {
    echo ""
    echo "=========================================="
    echo "WebArena Local Setup Script"
    echo "=========================================="
    echo ""
    echo "This script will:"
    echo "  1. Download Docker images (~75GB)"
    echo "  2. Start all WebArena services"
    echo "  3. Configure services for localhost"
    echo "  4. Test all services"
    echo "  5. Update task configurations"
    echo ""
    print_warning "This will take 1-2 hours on first run"
    echo ""
    read -p "Continue? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 0
    fi

    # Run setup steps
    check_directory
    check_disk_space
    setup_images
    start_services
    configure_services
    fix_gitlab
    test_services
    update_task_configs
    print_usage

    print_success "WebArena setup complete!"
}

# Run main
main
