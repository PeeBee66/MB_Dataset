# Offline Installation Guide

This guide explains how to install and run OpenCTI Injester in an **air-gapped environment** with **NO internet access**.

## Prerequisites

The target system must have:
- Docker Engine installed
- Docker Compose installed
- Sufficient disk space (minimum 500MB)

## Installation Steps

### 1. Transfer Application Files

Copy the entire application directory to your offline system, including:
```
CTI_Injester/
├── offline-packages/      # 43MB of Python packages (60+ files)
├── run.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── install_offline.sh
├── templates/
├── plugin/
└── ...
```

**Important**: The `offline-packages/` directory contains all Python dependencies and MUST be included.

### 2. Verify Package Integrity

Check that all packages are present:
```bash
cd CTI_Injester
ls -1 offline-packages/*.whl offline-packages/*.tar.gz | wc -l
```

Expected output: **60 or more packages**

### 3. Run Installation Script

Execute the offline installation script:
```bash
./install_offline.sh
```

The script will:
- ✅ Verify Docker and Docker Compose installation
- ✅ Check for offline packages (60+ files expected)
- ✅ Validate directory structure
- ✅ Create necessary directories
- ✅ Build Docker image using offline packages

### 4. Configure Application

Edit plugin configuration files:

**TOR Plugin** (`plugin/tor/config.json`):
```json
{
  "enabled": true,
  "github_url": "https://raw.githubusercontent.com/PeeBee66/Updated_TOR_Nodes/main/tor_nodes_latest.csv",
  "verify_ssl": false,
  "opencti_url": "http://your-opencti-server:8080",
  "opencti_token": "your-api-token-here",
  "auto_ingest": true
}
```

**MalwareBazaar Plugin** (`plugin/malwarebazaar/config.json`):
```json
{
  "enabled": true,
  "github_url": "https://api.github.com/repos/PeeBee66/MB_Dataset/contents/uploads",
  "verify_ssl": false,
  "opencti_url": "https://your-opencti-server:4000",
  "opencti_token": "your-api-token-here",
  "auto_ingest": true
}
```

### 5. Start Application

Start the containerized application:
```bash
docker-compose up -d opencti-injester
```

### 6. Verify Installation

Check that the container is running:
```bash
docker ps | grep opencti-injester
```

View logs:
```bash
docker-compose logs -f opencti-injester
```

Access web interface:
```
http://localhost:5055
```

Default credentials:
- Password: `admin`

## Troubleshooting

### Build Fails with Package Errors

**Problem**: Docker build fails with "No matching distribution found"

**Solution**: Ensure `offline-packages/` directory is present and contains all `.whl` and `.tar.gz` files.

### Container Exits Immediately

**Problem**: Container starts and stops

**Solution**: Check logs for errors:
```bash
docker-compose logs opencti-injester
```

Common issues:
- Missing plugin configuration files
- Invalid Python syntax
- Port 5055 already in use

### Missing Dependencies

**Problem**: Import errors when running

**Solution**: Rebuild the image:
```bash
docker-compose down
docker-compose build --no-cache opencti-injester
docker-compose up -d opencti-injester
```

### Plugin Data Not Persisting

**Problem**: Data resets after container restart

**Solution**: Ensure volumes are properly mounted in `docker-compose.yml`:
```yaml
volumes:
  - ./plugin/tor/data:/app/plugin/tor/data
  - ./plugin/malwarebazaar/data:/app/plugin/malwarebazaar/data
  - ./flask_session:/app/flask_session
```

## Architecture

### Offline Package Installation

The Dockerfile uses pip's offline installation mode:
```dockerfile
COPY offline-packages/ /app/offline-packages/
RUN pip install --no-index --find-links /app/offline-packages -r requirements.txt
```

Key flags:
- `--no-index`: Don't use PyPI (no internet)
- `--find-links`: Use local directory for packages

### Included Packages

The `offline-packages/` directory contains:
- **Core Framework**: Flask, Werkzeug, Jinja2
- **Scheduling**: APScheduler
- **Data Processing**: pandas, numpy
- **OpenCTI Integration**: pycti, stix2
- **Web Server**: gunicorn, uvicorn
- **All Dependencies**: 60+ packages totaling 43MB

## Commands Reference

### Start Application
```bash
docker-compose up -d opencti-injester
```

### Stop Application
```bash
docker-compose down
```

### View Logs
```bash
docker-compose logs -f opencti-injester
```

### Restart Application
```bash
docker-compose restart opencti-injester
```

### Rebuild Image
```bash
docker-compose build --no-cache opencti-injester
```

### Access Container Shell
```bash
docker exec -it opencti-injester /bin/bash
```

## Network Requirements

While the application can be **built and run offline**, the plugins require network access to:

1. **GitHub**: Fetch TOR nodes CSV and malware samples
2. **OpenCTI**: Ingest threat intelligence data

Ensure the offline system has:
- ✅ Access to GitHub (for data collection)
- ✅ Access to OpenCTI instance (for ingestion)
- ❌ No PyPI access required (all packages bundled)

## Security Considerations

1. **API Tokens**: Store OpenCTI tokens securely in plugin configs
2. **Network Isolation**: Consider firewall rules for outbound connections
3. **Malware Samples**: MalwareBazaar plugin downloads actual malware - handle with care
4. **Production Secrets**: Change default password and secret key:
   ```yaml
   environment:
     - APP_PASSWORD=your-secure-password
     - SECRET_KEY=your-random-secret-key
   ```

## Support

For issues with offline installation:
1. Check `docker-compose logs -f`
2. Verify all files were transferred correctly
3. Ensure Docker has sufficient resources (2GB RAM minimum)
4. Review CLAUDE.md for architecture details
