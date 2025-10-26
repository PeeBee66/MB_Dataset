#!/bin/bash
#
# OpenCTI Injester - Offline Installation Script
# This script installs the application without requiring internet access
#

set -e

echo "=========================================="
echo "OpenCTI Injester - Offline Installation"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo -e "${YELLOW}Warning: Running as root. This is not recommended.${NC}"
fi

# Check for Docker
echo -n "Checking for Docker... "
if ! command -v docker &> /dev/null; then
    echo -e "${RED}FAILED${NC}"
    echo "Docker is not installed. Please install Docker first."
    exit 1
fi
echo -e "${GREEN}OK${NC}"

# Check for Docker Compose
echo -n "Checking for Docker Compose... "
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}FAILED${NC}"
    echo "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi
echo -e "${GREEN}OK${NC}"

# Check if offline-packages directory exists
echo -n "Checking for offline packages... "
if [ ! -d "offline-packages" ]; then
    echo -e "${RED}FAILED${NC}"
    echo "offline-packages directory not found!"
    echo "Please ensure the complete application package is present."
    exit 1
fi

PACKAGE_COUNT=$(ls -1 offline-packages/*.whl offline-packages/*.tar.gz 2>/dev/null | wc -l)
if [ "$PACKAGE_COUNT" -lt 10 ]; then
    echo -e "${RED}FAILED${NC}"
    echo "Insufficient packages found in offline-packages/ directory."
    echo "Expected 60+ packages, found: $PACKAGE_COUNT"
    exit 1
fi
echo -e "${GREEN}OK (found $PACKAGE_COUNT packages)${NC}"

# Check directory structure
echo -n "Checking directory structure... "
REQUIRED_FILES=("run.py" "requirements.txt" "Dockerfile" "docker-compose.yml")
MISSING_FILES=()

for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        MISSING_FILES+=("$file")
    fi
done

if [ ${#MISSING_FILES[@]} -ne 0 ]; then
    echo -e "${RED}FAILED${NC}"
    echo "Missing required files: ${MISSING_FILES[*]}"
    exit 1
fi
echo -e "${GREEN}OK${NC}"

# Create necessary directories
echo "Creating data directories..."
mkdir -p plugin/tor/data
mkdir -p plugin/malwarebazaar/data
mkdir -p flask_session

# Build Docker image
echo ""
echo "Building Docker image (this may take a few minutes)..."
docker-compose build opencti-injester

if [ $? -ne 0 ]; then
    echo -e "${RED}Docker build failed!${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}Installation completed successfully!${NC}"
echo ""
echo "=========================================="
echo "Next Steps:"
echo "=========================================="
echo ""
echo "1. Configure plugins (edit config files):"
echo "   - plugin/tor/config.json"
echo "   - plugin/malwarebazaar/config.json"
echo ""
echo "2. Start the application:"
echo "   docker-compose up -d opencti-injester"
echo ""
echo "3. Access the web interface:"
echo "   http://localhost:5055"
echo "   Default password: admin"
echo ""
echo "4. Check logs:"
echo "   docker-compose logs -f opencti-injester"
echo ""
echo "=========================================="
