# Offline Package - Complete Installation Guide

## Package Contents

This is a **fully offline-capable** OpenCTI Injester package that requires **NO internet access** for installation.

### What's Included

```
CTI_Injester/
├── offline-packages/         # 43MB, 62 Python packages
│   ├── Flask, pandas, pycti, stix2
│   ├── All dependencies (no PyPI access needed)
│   └── Pre-built for Python 3.11
├── run.py                    # Main application
├── requirements.txt          # Dependency manifest
├── Dockerfile                # Offline-ready build
├── docker-compose.yml        # Deployment configuration
├── install_offline.sh        # Automated installation script
├── INSTALL_OFFLINE.md        # Detailed installation guide
├── templates/                # Web UI templates
└── plugin/                   # TOR & MalwareBazaar plugins
```

## Quick Start (Offline Installation)

### Prerequisites on Target System

✅ Docker Engine (any version)
✅ Docker Compose (any version)
❌ **NO internet access required for installation**

### Installation Steps

1. **Transfer this entire directory** to your offline system
2. **Run the installation script**:
   ```bash
   cd CTI_Injester
   ./install_offline.sh
   ```
3. **Configure plugins** (edit config files)
4. **Start the application**:
   ```bash
   docker-compose up -d opencti-injester
   ```
5. **Access web interface**: http://localhost:5055

## What Works Offline vs. Online

| Component | Offline Build | Runtime |
|-----------|--------------|---------|
| Docker image build | ✅ Fully offline | N/A |
| Python dependencies | ✅ Pre-bundled | ✅ Installed |
| Flask application | ✅ Included | ✅ Runs |
| Plugin system | ✅ Included | ✅ Runs |
| Data collection | N/A | ⚠️ Needs GitHub access |
| OpenCTI ingestion | N/A | ⚠️ Needs OpenCTI access |

**Summary**: Installation is 100% offline. Data collection requires network access to GitHub and OpenCTI.

## Package Details

### Python Packages (62 total, 43MB)

**Core Framework**:
- Flask 2.3.3
- Werkzeug 2.3.7
- Jinja2 3.1.6
- gunicorn 21.2.0

**Scheduling**:
- APScheduler 3.10.4

**Data Processing**:
- pandas 2.3.2
- numpy 2.2.6

**OpenCTI Integration**:
- pycti 6.8.6
- stix2 3.0.1
- stix2-patterns 1.2.1

**Web APIs**:
- requests 2.32.5
- urllib3 2.5.0
- fastapi 0.116.2
- uvicorn 0.35.0

**All Dependencies**: 62 packages including transitive dependencies

### Platform Compatibility

- **OS**: Linux x86_64 (manylinux2014)
- **Python**: 3.11 (Docker base image)
- **Architecture**: amd64

## Installation Script Features

The `install_offline.sh` script performs:

1. ✅ Verifies Docker installation
2. ✅ Verifies Docker Compose installation
3. ✅ Checks for offline-packages directory
4. ✅ Validates 60+ packages present
5. ✅ Checks directory structure
6. ✅ Creates data directories
7. ✅ Builds Docker image (offline)
8. ✅ Provides next steps

## Dockerfile Offline Build Process

The Dockerfile uses pip's offline installation mode:

```dockerfile
# Copy offline packages
COPY offline-packages/ /app/offline-packages/

# Install without internet (--no-index)
RUN pip install --no-index --find-links /app/offline-packages -r requirements.txt
```

**Key pip flags**:
- `--no-index`: Do not use PyPI index (no internet)
- `--find-links /app/offline-packages`: Use local directory

## Configuration

### Before First Run

Edit plugin configuration files:

**1. TOR Plugin** (`plugin/tor/config.json`):
```json
{
  "enabled": true,
  "github_url": "https://raw.githubusercontent.com/...",
  "opencti_url": "http://your-opencti:8080",
  "opencti_token": "your-token",
  "auto_ingest": true
}
```

**2. MalwareBazaar Plugin** (`plugin/malwarebazaar/config.json`):
```json
{
  "enabled": true,
  "github_url": "https://api.github.com/...",
  "opencti_url": "https://your-opencti:4000",
  "opencti_token": "your-token",
  "auto_ingest": true
}
```

## Common Commands

### Installation
```bash
./install_offline.sh
```

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

### Rebuild Image
```bash
docker-compose build --no-cache opencti-injester
docker-compose up -d opencti-injester
```

### Access Container Shell
```bash
docker exec -it opencti-injester /bin/bash
```

## Troubleshooting

### Build Fails

**Error**: "No matching distribution found for X"

**Cause**: Missing or incompatible package in offline-packages/

**Solution**: Verify all 62 packages are present:
```bash
ls -1 offline-packages/*.whl offline-packages/*.tar.gz | wc -l
# Should output: 62
```

### Container Exits Immediately

**Cause**: Configuration error or missing plugin configs

**Solution**: Check logs:
```bash
docker-compose logs opencti-injester
```

### Port Already in Use

**Error**: "bind: address already in use"

**Solution**: Change port in docker-compose.yml:
```yaml
ports:
  - "5056:5055"  # Changed from 5055:5055
```

## Network Requirements

While **installation is fully offline**, runtime operation requires:

### Required Network Access
- ✅ **GitHub**: For data collection (TOR nodes, malware samples)
- ✅ **OpenCTI**: For threat intelligence ingestion

### NOT Required
- ❌ **PyPI**: All Python packages pre-bundled
- ❌ **Docker Hub**: Image built locally
- ❌ **npm/yarn**: No JavaScript dependencies

## Security Considerations

1. **Malware Handling**: MalwareBazaar plugin downloads actual malware
   - Samples stored in `plugin/malwarebazaar/data/samples/`
   - Handle with appropriate caution

2. **API Tokens**: Configure in plugin configs
   - Never commit tokens to version control
   - Use secure storage methods

3. **Production Deployment**:
   ```yaml
   environment:
     - APP_PASSWORD=strong-password-here
     - SECRET_KEY=random-secret-key-here
   ```

## Package Generation (For Developers)

To regenerate offline packages:

```bash
# Download for Python 3.11
pip3 download -r requirements.txt \
  -d offline-packages/ \
  --python-version 3.11 \
  --platform manylinux2014_x86_64 \
  --only-binary=:all:
```

This ensures compatibility with the Python 3.11 Docker base image.

## File Sizes

- **offline-packages/**: 43 MB
- **Docker image**: ~500 MB (includes Python 3.11 base)
- **Total transfer**: ~50 MB (compressed)

## Support

For issues:
1. Review `INSTALL_OFFLINE.md` for detailed instructions
2. Check `CLAUDE.md` for architecture details
3. Review logs: `docker-compose logs -f`

## Success Indicators

✅ **Installation successful when**:
1. Script completes without errors
2. Docker image builds successfully
3. Container starts: `docker ps | grep opencti-injester`
4. Web interface accessible: http://localhost:5055
5. Logs show: "Loading plugins from..."

## Version Information

- **Application**: OpenCTI Injester
- **Python**: 3.11 (slim)
- **Flask**: 2.3.3
- **pycti**: 6.8.6
- **Package Date**: October 2025
- **Total Packages**: 62
