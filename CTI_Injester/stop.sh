#!/bin/bash
#
# OpenCTI Injester - Stop Script
# Simple script to stop the application
#

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}═══════════════════════════════════════════${NC}"
echo -e "${BLUE}   OpenCTI Injester - Stopping Application ${NC}"
echo -e "${BLUE}═══════════════════════════════════════════${NC}"
echo ""

# Change to script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo -e "${RED}✗ Error: Docker daemon is not running${NC}"
    exit 1
fi

# Check if container is running
if ! docker ps | grep -q opencti-injester; then
    echo -e "${YELLOW}⚠ Application is not running${NC}"
    echo ""

    # Check if container exists but is stopped
    if docker ps -a | grep -q opencti-injester; then
        echo "Container exists but is already stopped"
        echo ""
        echo "Options:"
        echo "  • Start it: ./start.sh"
        echo "  • Remove it: docker rm opencti-injester"
    else
        echo "Container does not exist"
        echo "Start it with: ./start.sh"
    fi
    echo ""
    exit 0
fi

# Stop the container
echo -e "${BLUE}→ Stopping OpenCTI Injester container...${NC}"
docker-compose down

# Verify it stopped
if ! docker ps | grep -q opencti-injester; then
    echo ""
    echo -e "${GREEN}═══════════════════════════════════════════${NC}"
    echo -e "${GREEN}   ✓ Application Stopped Successfully!     ${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════${NC}"
    echo ""
    echo "Data preserved in:"
    echo "  • ./plugin/tor/data/"
    echo "  • ./plugin/malwarebazaar/data/"
    echo "  • ./flask_session/"
    echo ""
    echo "To restart: ./start.sh"
    echo ""
else
    echo ""
    echo -e "${RED}✗ Failed to stop application${NC}"
    echo ""
    echo "Try manual stop: docker stop opencti-injester"
    exit 1
fi
