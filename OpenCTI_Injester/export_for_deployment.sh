#!/bin/bash

# OpenCTI Injester - Export for Deployment Script
# This script creates a complete deployment package including the built Docker image

set -e

echo "=========================================="
echo "OpenCTI Injester - Export for Deployment"
echo "=========================================="
echo ""

# Ensure the latest image is built
echo "[1/5] Building latest Docker image..."
docker compose build opencti-injester

# Save the built image
echo ""
echo "[2/5] Saving Docker image..."
docker save opencti_injester-opencti-injester:latest -o opencti_injester.tar
gzip -f opencti_injester.tar
echo "✓ Docker image saved: opencti_injester.tar.gz ($(du -h opencti_injester.tar.gz | cut -f1))"

# Download Python packages for offline installation (fallback)
echo ""
echo "[3/5] Downloading Python packages for offline installation..."
OFFLINE_DIR="./offline-packages"
mkdir -p "$OFFLINE_DIR"
pip3 download -r requirements.txt -d "$OFFLINE_DIR" 2>/dev/null || echo "⚠ Package download skipped (optional)"
echo "✓ Python packages saved to: $OFFLINE_DIR/"

# Create deployment archive
echo ""
echo "[4/5] Creating deployment package..."
ARCHIVE_NAME="opencti-injester-export-$(date +%Y%m%d-%H%M%S).tar.gz"

tar -czf "$ARCHIVE_NAME" \
    --exclude='opencti-injester-export-*.tar.gz' \
    --exclude='backup_old' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.git' \
    --exclude='flask_session' \
    --exclude='plugin/tor/data/*' \
    --exclude='plugin/malwarebazaar/data/*' \
    --exclude='.dockerignore' \
    Dockerfile \
    docker-compose.yml \
    requirements.txt \
    run.py \
    templates/ \
    static/ \
    plugin/ \
    offline-packages/ \
    opencti_injester.tar.gz \
    deploy_offline.sh \
    MANUAL_IMPORT_GUIDE.md \
    manual_import_all.sh \
    check_specific_bundle.py \
    DEPLOYMENT_README.md

echo "✓ Deployment package created: $ARCHIVE_NAME"

# Calculate sizes
echo ""
echo "[5/5] Package Summary"
echo "=========================================="
echo "Main Package: $ARCHIVE_NAME"
echo "Size: $(du -h "$ARCHIVE_NAME" | cut -f1)"
echo ""
echo "Contents:"
echo "  - Docker image: opencti_injester.tar.gz"
echo "  - Application code (Flask, plugins)"
echo "  - Python requirements"
echo "  - Offline packages (pip cache)"
echo "  - Deployment scripts"
echo "  - Manual import guides and tools"
echo ""
echo "=========================================="
echo "DEPLOYMENT INSTRUCTIONS"
echo "=========================================="
echo ""
echo "1. Transfer to target system:"
echo "   scp $ARCHIVE_NAME user@target:/path/to/deploy/"
echo ""
echo "2. On target system, extract:"
echo "   tar -xzf $ARCHIVE_NAME"
echo "   cd opencti-injester/"
echo ""
echo "3. Load Docker image:"
echo "   gunzip opencti_injester.tar.gz"
echo "   docker load -i opencti_injester.tar"
echo ""
echo "4. Start the application:"
echo "   docker compose up -d opencti-injester"
echo ""
echo "   OR for offline deployment:"
echo "   ./deploy_offline.sh"
echo ""
echo "5. Access the application:"
echo "   http://localhost:5055"
echo "   Default password: admin"
echo ""
echo "=========================================="
echo "✓ Export complete!"
echo "=========================================="
