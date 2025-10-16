#!/bin/bash
# Manual import of all STIX bundles to OpenCTI via Web UI
# This script finds all STIX bundles and provides download links

OPENCTI_URL="https://172.21.32.183:4000"
PLUGIN_URL="http://localhost:5055"
SAMPLES_DIR="/home/ws-admin/PROJECTS/OpenCTI_Injester/plugin/malwarebazaar/data/samples"

echo "=========================================="
echo "STIX Bundle Manual Import Helper"
echo "=========================================="
echo ""
echo "Found the following STIX bundles:"
echo ""

count=0
for bundle in $(find "$SAMPLES_DIR" -name "*_stix_bundle.json"); do
    hash=$(basename "$bundle" | sed 's/_stix_bundle.json//')
    count=$((count + 1))

    echo "[$count] Hash: $hash"
    echo "    Download: ${PLUGIN_URL}/plugin/malwarebazaar/sample/${hash}/download"
    echo "    File: $bundle"
    echo ""
done

echo "=========================================="
echo "Total bundles found: $count"
echo "=========================================="
echo ""
echo "IMPORT INSTRUCTIONS:"
echo ""
echo "METHOD 1 - Web UI Import:"
echo "  1. Download a bundle using the URL above"
echo "  2. Go to: ${OPENCTI_URL}/dashboard/data/import"
echo "  3. Click 'Import from file' and upload the JSON file"
echo ""
echo "METHOD 2 - Direct File Import:"
echo "  You can copy any bundle file directly and import it"
echo "  Example: cat /path/to/bundle.json | clipboard"
echo "  Then paste into OpenCTI's 'Import from text' feature"
echo ""
