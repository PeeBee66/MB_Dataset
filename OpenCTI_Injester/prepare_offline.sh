#!/bin/bash

# OpenCTI Injester - Offline Package Preparation Script
# This script downloads all required Python packages for offline installation

echo "======================================"
echo "OpenCTI Injester Offline Prep"
echo "======================================"

# Create offline packages directory
OFFLINE_DIR="./offline-packages"
mkdir -p "$OFFLINE_DIR"

echo "Downloading Python packages to $OFFLINE_DIR..."

# Download all packages with dependencies
pip download -r requirements.txt -d "$OFFLINE_DIR"

# Download Docker images
echo "Saving Docker images..."
docker pull python:3.11-slim
docker save python:3.11-slim -o python-3.11-slim.tar

echo "Creating deployment package..."

# Create deployment archive
ARCHIVE_NAME="opencti-injester-offline-$(date +%Y%m%d-%H%M%S).tar.gz"

tar -czf "$ARCHIVE_NAME" \
    --exclude='backup_old' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.git' \
    --exclude='flask_session' \
    --exclude='plugin/*/data' \
    .

echo "======================================"
echo "Offline package created: $ARCHIVE_NAME"
echo "Size: $(du -h "$ARCHIVE_NAME" | cut -f1)"
echo "======================================"
echo ""
echo "To deploy offline:"
echo "1. Copy $ARCHIVE_NAME to target system"
echo "2. Extract: tar -xzf $ARCHIVE_NAME"
echo "3. Load Docker image: docker load -i python-3.11-slim.tar"
echo "4. Run: docker-compose --profile offline up opencti-injester-offline"
echo ""