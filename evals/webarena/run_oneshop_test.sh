#!/bin/bash

# Run OneShop (shopping) evaluations from WebArena against BrowserOperator
# This script sets up environment variables and runs a batch of shopping tasks

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== OneShop WebArena Evaluation Runner ===${NC}\n"

# Check if BrowserOperator container is running
echo -e "${YELLOW}Checking BrowserOperator container...${NC}"
if ! docker ps | grep -q kernel-browser-extended; then
    echo -e "${RED}Error: BrowserOperator container is not running${NC}"
    echo "Start it with: make compose-up"
    exit 1
fi
echo -e "${GREEN}✓ Container is running${NC}\n"

# Check if eval-server API is accessible
echo -e "${YELLOW}Checking eval-server API...${NC}"
if ! curl -s http://localhost:8080/status > /dev/null 2>&1; then
    echo -e "${RED}Error: eval-server API is not accessible at http://localhost:8080${NC}"
    exit 1
fi
echo -e "${GREEN}✓ API is accessible${NC}\n"

# Set WebArena site URLs
# These use actual WebArena domain names (onestopshop.com, etc.)
# Docker host overrides route them to 172.16.55.59
export SHOPPING="http://onestopshop.com"
export SHOPPING_ADMIN="http://onestopshop.com/admin"
export REDDIT="http://reddit.com"
export GITLAB="http://gitlab.com"
export WIKIPEDIA="http://wikipedia.org"
export MAP="http://openstreetmap.org"
export HOMEPAGE="http://homepage.com"

echo -e "${YELLOW}Environment variables set:${NC}"
echo "  SHOPPING=$SHOPPING"
echo "  SHOPPING_ADMIN=$SHOPPING_ADMIN"
echo ""

# Default: run first 10 shopping tasks
LIMIT=${1:-10}
VERBOSE=${2:---verbose}

echo -e "${YELLOW}Running $LIMIT shopping tasks from WebArena...${NC}"
echo ""

# Run WebArena with shopping site filter
python3 run_webarena.py \
    --all \
    --site shopping \
    --limit "$LIMIT" \
    $VERBOSE

echo ""
echo -e "${GREEN}=== Evaluation complete ===${NC}"
echo -e "Check ${YELLOW}reports/${NC} directory for detailed results"
