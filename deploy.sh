#!/bin/bash

set -euo pipefail

# Kernel-Browser Cloud Run Deployment Script
echo "🚀 Starting kernel-browser deployment to Google Cloud Run..."

# Configuration
PROJECT_ID="${PROJECT_ID:-}"
REGION="${REGION:-us-central1}"
SERVICE_NAME="kernel-browser"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
error() {
    echo -e "${RED}ERROR: $1${NC}" >&2
    exit 1
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

info() {
    echo -e "ℹ️  $1"
}

# Check prerequisites
check_prerequisites() {
    info "Checking prerequisites..."
    
    # Check if gcloud is installed
    if ! command -v gcloud &> /dev/null; then
        error "gcloud CLI is not installed. Please install it from https://cloud.google.com/sdk/docs/install"
    fi
    
    # Check if docker is installed
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed. Please install it from https://docs.docker.com/get-docker/"
    fi
    
    # Check if git is installed
    if ! command -v git &> /dev/null; then
        error "Git is not installed. Please install it first."
    fi
    
    success "All prerequisites are installed"
}

# Get or validate project ID
setup_project() {
    if [ -z "$PROJECT_ID" ]; then
        PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
        if [ -z "$PROJECT_ID" ]; then
            error "No Google Cloud project configured. Please run: gcloud config set project YOUR_PROJECT_ID"
        fi
    fi
    
    info "Using Google Cloud Project: $PROJECT_ID"
    
    # Confirm project selection
    read -p "Is this the correct project? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        error "Please set the correct project with: gcloud config set project YOUR_PROJECT_ID"
    fi
}

# Enable required APIs
enable_apis() {
    info "Enabling required Google Cloud APIs..."
    
    local apis=(
        "cloudbuild.googleapis.com"
        "run.googleapis.com"
        "containerregistry.googleapis.com"
        "compute.googleapis.com"
        "storage.googleapis.com"
    )
    
    for api in "${apis[@]}"; do
        info "Enabling $api..."
        gcloud services enable "$api" --project="$PROJECT_ID" --quiet
    done
    
    success "All required APIs are enabled"
}

# Create service account with necessary permissions
create_service_account() {
    info "Creating service account for kernel-browser..."
    
    local sa_name="kernel-browser-sa"
    local sa_email="${sa_name}@${PROJECT_ID}.iam.gserviceaccount.com"
    
    # Create service account if it doesn't exist
    if ! gcloud iam service-accounts describe "$sa_email" --project="$PROJECT_ID" &>/dev/null; then
        gcloud iam service-accounts create "$sa_name" \
            --display-name="Kernel Browser Service Account" \
            --description="Service account for kernel-browser Cloud Run service" \
            --project="$PROJECT_ID"
        success "Service account created: $sa_email"
    else
        info "Service account already exists: $sa_email"
    fi
    
    # Grant necessary permissions
    local roles=(
        "roles/storage.objectAdmin"  # For recordings storage
        "roles/logging.logWriter"    # For Cloud Logging
        "roles/monitoring.metricWriter"  # For monitoring
    )
    
    for role in "${roles[@]}"; do
        gcloud projects add-iam-policy-binding "$PROJECT_ID" \
            --member="serviceAccount:$sa_email" \
            --role="$role" \
            --quiet
    done
    
    success "Service account permissions configured"
}

# Update git submodules
update_submodules() {
    info "Updating git submodules..."
    
    if [ ! -f .gitmodules ]; then
        error "No .gitmodules file found. Make sure kernel-images is added as a submodule."
    fi
    
    git submodule update --init --recursive
    
    if [ ! -d "kernel-images" ]; then
        error "kernel-images submodule not found. Please run: git submodule add https://github.com/onkernel/kernel-images.git"
    fi
    
    success "Submodules updated"
}

# Build and deploy using Cloud Build
deploy_with_cloudbuild() {
    info "Building and deploying with Cloud Build..."
    
    # Submit build
    gcloud builds submit \
        --config=cloudbuild.yaml \
        --project="$PROJECT_ID" \
        --timeout="2h" \
        --machine-type="e2-highcpu-32"
    
    success "Build and deployment completed"
}

# Alternative: Local build and deploy
deploy_local() {
    warning "Using local build (slower but more reliable for testing)"
    
    info "Building Docker image locally..."
    local image_name="gcr.io/$PROJECT_ID/kernel-browser:$(date +%s)"
    
    docker build -f Dockerfile.cloudrun -t "$image_name" .
    
    info "Pushing image to Container Registry..."
    docker push "$image_name"
    
    info "Deploying to Cloud Run..."
    
    # Update service.yaml with project ID and image
    sed -i.bak "s/PROJECT_ID/$PROJECT_ID/g" service.yaml
    sed -i.bak "s|gcr.io/PROJECT_ID/kernel-browser:latest|$image_name|g" service.yaml
    
    gcloud run services replace service.yaml \
        --region="$REGION" \
        --project="$PROJECT_ID"
    
    # Restore original service.yaml
    mv service.yaml.bak service.yaml
    
    success "Local build and deployment completed"
}

# Get service information
get_service_info() {
    info "Getting service information..."
    
    local service_url
    service_url=$(gcloud run services describe "$SERVICE_NAME" \
        --region="$REGION" \
        --project="$PROJECT_ID" \
        --format="value(status.url)" 2>/dev/null)
    
    if [ -n "$service_url" ]; then
        success "Deployment successful!"
        echo
        echo "🌐 Service Endpoints:"
        echo "   Main Interface:    $service_url"
        echo "   WebRTC Client:     $service_url/"
        echo "   Chrome DevTools:   $service_url/ws"
        echo "   Recording API:     $service_url/api"
        echo "   Health Check:      $service_url/health"
        echo
        echo "📊 Service Details:"
        gcloud run services describe "$SERVICE_NAME" \
            --region="$REGION" \
            --project="$PROJECT_ID" \
            --format="table(spec.template.spec.containers[0].resources.limits.cpu,spec.template.spec.containers[0].resources.limits.memory,status.conditions[0].status)"
    else
        error "Failed to get service URL"
    fi
}

# Main deployment flow
main() {
    echo "Kernel Browser - Google Cloud Run Deployment"
    echo "============================================"
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --project)
                PROJECT_ID="$2"
                shift 2
                ;;
            --region)
                REGION="$2"
                shift 2
                ;;
            --local)
                LOCAL_BUILD=true
                shift
                ;;
            --help)
                echo "Usage: $0 [OPTIONS]"
                echo "Options:"
                echo "  --project PROJECT_ID   Set Google Cloud project ID"
                echo "  --region REGION        Set deployment region (default: us-central1)"
                echo "  --local               Use local Docker build instead of Cloud Build"
                echo "  --help                Show this help message"
                exit 0
                ;;
            *)
                error "Unknown option: $1"
                ;;
        esac
    done
    
    check_prerequisites
    setup_project
    enable_apis
    create_service_account
    update_submodules
    
    if [ "${LOCAL_BUILD:-false}" = "true" ]; then
        deploy_local
    else
        deploy_with_cloudbuild
    fi
    
    get_service_info
    
    success "Deployment complete! 🎉"
}

# Run main function
main "$@"