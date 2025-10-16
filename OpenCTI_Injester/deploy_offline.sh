#!/bin/bash

# OpenCTI Injester - Offline Deployment Script
# This script installs and runs the application in an offline environment

echo "======================================"
echo "OpenCTI Injester Offline Deploy"
echo "======================================"

# Check if Docker is available
if command -v docker &> /dev/null && command -v docker-compose &> /dev/null; then
    echo "Docker detected. Using Docker deployment..."

    # Load Docker image if available
    if [ -f "python-3.11-slim.tar" ]; then
        echo "Loading Docker image..."
        docker load -i python-3.11-slim.tar
    fi

    # Run with Docker Compose (offline profile)
    echo "Starting OpenCTI Injester with Docker..."
    docker-compose --profile offline up -d opencti-injester-offline

    echo "======================================"
    echo "Deployment Complete!"
    echo "Access: http://localhost:5055"
    echo "Default password: admin"
    echo "======================================"

else
    echo "Docker not available. Using local Python deployment..."

    # Check if offline packages exist
    if [ ! -d "offline-packages" ]; then
        echo "ERROR: offline-packages directory not found"
        echo "Please run prepare_offline.sh first"
        exit 1
    fi

    # Install from offline packages
    echo "Installing Python packages from offline cache..."
    pip install --no-index --find-links offline-packages/ -r requirements.txt

    # Create necessary directories
    echo "Creating directories..."
    mkdir -p plugin/tor/data
    mkdir -p plugin/malwarebazaar/data
    mkdir -p flask_session

    # Set environment variables
    export APP_PASSWORD=admin
    export SECRET_KEY=change-this-in-production

    # Start the application
    echo "Starting OpenCTI Injester..."
    echo "======================================"
    echo "Access: http://localhost:5055"
    echo "Default password: admin"
    echo "======================================"

    python run.py
fi