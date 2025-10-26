#!/bin/bash
#
# OpenCTI Injester - Quick Start Script
# This script provides easy management of the application
#

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Function to display usage
usage() {
    echo ""
    echo -e "${BLUE}OpenCTI Injester - Management Script${NC}"
    echo ""
    echo "Usage: ./run.sh [command]"
    echo ""
    echo "Commands:"
    echo "  start       - Start the application"
    echo "  stop        - Stop the application"
    echo "  restart     - Restart the application"
    echo "  status      - Show application status"
    echo "  logs        - Show application logs (follow mode)"
    echo "  build       - Rebuild Docker image"
    echo "  shell       - Access container shell"
    echo "  clean       - Stop and remove containers"
    echo "  help        - Show this help message"
    echo ""
    exit 0
}

# Function to check Docker
check_docker() {
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}Error: Docker is not installed${NC}"
        exit 1
    fi

    if ! docker info &> /dev/null; then
        echo -e "${RED}Error: Docker daemon is not running${NC}"
        exit 1
    fi
}

# Function to start application
start_app() {
    echo -e "${BLUE}Starting OpenCTI Injester...${NC}"

    # Check if container already running
    if docker ps | grep -q opencti-injester; then
        echo -e "${YELLOW}Application is already running!${NC}"
        echo ""
        show_status
        exit 0
    fi

    # Start the container
    docker-compose up -d opencti-injester

    if [ $? -eq 0 ]; then
        echo ""
        echo -e "${GREEN}✓ Application started successfully!${NC}"
        echo ""
        echo "Access the web interface at: http://localhost:5066"
        echo "Default password: admin"
        echo ""
        echo "View logs with: ./run.sh logs"
        echo ""
    else
        echo -e "${RED}Failed to start application${NC}"
        exit 1
    fi
}

# Function to stop application
stop_app() {
    echo -e "${BLUE}Stopping OpenCTI Injester...${NC}"
    docker-compose down

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Application stopped${NC}"
    else
        echo -e "${RED}Failed to stop application${NC}"
        exit 1
    fi
}

# Function to restart application
restart_app() {
    echo -e "${BLUE}Restarting OpenCTI Injester...${NC}"
    docker-compose restart opencti-injester

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Application restarted${NC}"
        echo ""
        echo "Access the web interface at: http://localhost:5066"
        echo ""
    else
        echo -e "${RED}Failed to restart application${NC}"
        exit 1
    fi
}

# Function to show status
show_status() {
    echo -e "${BLUE}Application Status:${NC}"
    echo ""

    if docker ps | grep -q opencti-injester; then
        echo -e "${GREEN}● Running${NC}"
        echo ""
        docker ps --filter "name=opencti-injester" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
        echo ""
        echo "Web Interface: http://localhost:5066"
        echo ""
    else
        echo -e "${YELLOW}● Stopped${NC}"
        echo ""

        # Check if container exists but is stopped
        if docker ps -a | grep -q opencti-injester; then
            echo "Container exists but is not running"
            echo "Start it with: ./run.sh start"
        else
            echo "Container does not exist"
            echo "Start it with: ./run.sh start"
        fi
        echo ""
    fi
}

# Function to show logs
show_logs() {
    echo -e "${BLUE}Showing application logs (Ctrl+C to exit)...${NC}"
    echo ""
    docker-compose logs -f opencti-injester
}

# Function to build image
build_image() {
    echo -e "${BLUE}Building Docker image...${NC}"
    echo ""
    docker-compose build --no-cache opencti-injester

    if [ $? -eq 0 ]; then
        echo ""
        echo -e "${GREEN}✓ Image built successfully${NC}"
        echo ""
        echo "Start the application with: ./run.sh start"
        echo ""
    else
        echo -e "${RED}Failed to build image${NC}"
        exit 1
    fi
}

# Function to access shell
access_shell() {
    if ! docker ps | grep -q opencti-injester; then
        echo -e "${RED}Error: Container is not running${NC}"
        echo "Start it first with: ./run.sh start"
        exit 1
    fi

    echo -e "${BLUE}Accessing container shell...${NC}"
    echo ""
    docker exec -it opencti-injester /bin/bash
}

# Function to clean up
clean_up() {
    echo -e "${BLUE}Cleaning up containers and volumes...${NC}"
    echo ""
    read -p "This will stop and remove all containers. Continue? (y/N) " -n 1 -r
    echo

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose down -v
        echo -e "${GREEN}✓ Cleanup complete${NC}"
    else
        echo "Cleanup cancelled"
    fi
}

# Main script logic
check_docker

case "${1:-}" in
    start)
        start_app
        ;;
    stop)
        stop_app
        ;;
    restart)
        restart_app
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    build)
        build_image
        ;;
    shell)
        access_shell
        ;;
    clean)
        clean_up
        ;;
    help|--help|-h)
        usage
        ;;
    "")
        echo -e "${YELLOW}No command specified${NC}"
        usage
        ;;
    *)
        echo -e "${RED}Unknown command: $1${NC}"
        usage
        ;;
esac
