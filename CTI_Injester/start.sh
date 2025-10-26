#!/bin/bash
#
# OpenCTI Injester - Start Script
# Simple script to start the application
#

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}═══════════════════════════════════════════${NC}"
echo -e "${BLUE}   OpenCTI Injester - Starting Application ${NC}"
echo -e "${BLUE}═══════════════════════════════════════════${NC}"
echo ""

# Change to script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Error: Docker is not installed${NC}"
    echo "  Please install Docker first: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker daemon is running
if ! docker info &> /dev/null; then
    echo -e "${RED}✗ Error: Docker daemon is not running${NC}"
    echo "  Please start Docker service"
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}✗ Error: Docker Compose is not installed${NC}"
    echo "  Please install Docker Compose"
    exit 1
fi

echo -e "${GREEN}✓ Prerequisites check passed${NC}"
echo ""

# Check if container is already running
if docker ps | grep -q opencti-injester; then
    echo -e "${YELLOW}⚠ Application is already running!${NC}"
    echo ""
    echo "Container status:"
    docker ps --filter "name=opencti-injester" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    echo ""
    echo -e "Access web interface: ${BLUE}http://localhost:5066${NC}"
    echo -e "Default password: ${YELLOW}admin${NC}"
    echo ""
    echo "To restart: ./stop.sh && ./start.sh"
    exit 0
fi

# Build if image doesn't exist
if ! docker images | grep -q opencti_injester-opencti-injester; then
    echo -e "${BLUE}→ Building Docker image (first time only)...${NC}"
    docker-compose build opencti-injester
    echo ""
fi

# Start the application
echo -e "${BLUE}→ Starting OpenCTI Injester container...${NC}"
docker-compose up -d opencti-injester

# Wait a moment for container to start
sleep 3

# Check if container started successfully
if docker ps | grep -q opencti-injester; then
    echo ""
    echo -e "${GREEN}═══════════════════════════════════════════${NC}"
    echo -e "${GREEN}   ✓ Application Started Successfully!     ${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════${NC}"
    echo ""
    echo "Web Interface:"
    echo -e "  URL: ${BLUE}http://localhost:5066${NC}"
    echo -e "  Password: ${YELLOW}admin${NC}"
    echo ""
    echo "Plugins:"
    echo "  • TOR Plugin: http://localhost:5066/plugin/tor/"
    echo "  • MalwareBazaar: http://localhost:5066/plugin/malwarebazaar/"
    echo ""
    echo "Management:"
    echo "  • View logs: docker logs -f opencti-injester"
    echo "  • Stop app: ./stop.sh"
    echo "  • Full management: ./run.sh help"
    echo ""
    echo "Container status:"
    docker ps --filter "name=opencti-injester" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    echo ""
else
    echo ""
    echo -e "${RED}✗ Failed to start application${NC}"
    echo ""
    echo "Check logs with: docker logs opencti-injester"
    exit 1
fi
