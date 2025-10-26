# OpenCTI Injester - Deployment Guide

This guide provides complete instructions for deploying the OpenCTI Injester application in any environment.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Deployment Steps](#deployment-steps)
- [Configuration](#configuration)
- [Post-Deployment Verification](#post-deployment-verification)
- [Troubleshooting](#troubleshooting)
- [Maintenance](#maintenance)

---

## Prerequisites

### Required Software

1. **Docker** (version 20.10 or higher)
   - Installation: https://docs.docker.com/get-docker/
   - Verify: `docker --version`

2. **Docker Compose** (version 2.0 or higher)
   - Usually included with Docker Desktop
   - Standalone installation: https://docs.docker.com/compose/install/
   - Verify: `docker-compose --version`

### System Requirements

- **OS**: Linux, macOS, or Windows with WSL2
- **RAM**: Minimum 2GB, Recommended 4GB
- **Disk Space**: Minimum 5GB free space
- **Network**: Internet access for initial build (or use offline deployment)

### OpenCTI Requirements

- **OpenCTI Instance**: Running OpenCTI v6.x or higher
- **API Token**: Admin-level API token from OpenCTI
- **Network Access**: Container must reach OpenCTI instance

### Port Requirements

The application requires the following port to be available:
- **5066** - Web interface (external port)
- **5055** - Internal container port

To change the external port, edit `docker-compose.yml` line 6: `"5066:5055"` → `"YOUR_PORT:5055"`

---

## Quick Start

### 1. Deploy Application

```bash
# Navigate to application directory
cd /path/to/CTI_Injester

# Start the application
./start.sh
```

### 2. Access Web Interface

- **URL**: http://localhost:5066
- **Default Password**: `admin`

### 3. Configure Plugins

Navigate to each plugin's settings page:
- **TOR Plugin**: http://localhost:5066/plugin/tor/settings
- **MalwareBazaar Plugin**: http://localhost:5066/plugin/malwarebazaar/settings

Required configuration for both plugins:
- `opencti_url`: Your OpenCTI instance URL (e.g., `https://opencti.example.com`)
- `opencti_token`: Your OpenCTI API token
- `verify_ssl`: Set to `false` for self-signed certificates, `true` for production
- `auto_ingest`: Set to `true` to enable automatic ingestion

---

## Deployment Steps

### Standard Deployment (Internet Access)

#### Step 1: Prepare Application Directory

```bash
# Clone or copy application files
cd /path/to/CTI_Injester

# Verify all required files are present
ls -l
# Should see: docker-compose.yml, Dockerfile, requirements.txt, run.py, etc.
```

#### Step 2: Configure Environment Variables (Optional)

Edit `docker-compose.yml` to customize:

```yaml
environment:
  - APP_PASSWORD=your_secure_password    # Change default password
  - SECRET_KEY=your_random_secret_key    # Change for production
  - PYTHONUNBUFFERED=1                   # Keep this as-is
```

#### Step 3: Build and Start

```bash
# Build Docker image
docker-compose build opencti-injester

# Start application
./start.sh

# Or use docker-compose directly
docker-compose up -d opencti-injester
```

#### Step 4: Verify Container Status

```bash
# Check if container is running
docker ps | grep opencti-injester

# Check application logs
docker logs opencti-injester

# Follow logs in real-time
docker logs -f opencti-injester
```

#### Step 5: Access and Configure

1. Open browser: http://localhost:5066
2. Login with password: `admin` (or your custom password)
3. Configure plugin settings (see Configuration section)

---

### Offline Deployment (Air-Gapped Environments)

For systems without internet access, use the offline deployment method:

#### Prerequisites for Offline Deployment

All required files are included in the repository:
- `offline-packages/` - 62 Python packages (43MB total)
- `Dockerfile` - Configured for offline installation
- `docker-compose.yml` - Container configuration

#### Offline Deployment Steps

```bash
# 1. Copy entire application directory to target system
# Use USB drive, network transfer, etc.

# 2. Run offline installation script
./install_offline.sh

# 3. Start application
./start.sh
```

**Note**: Offline installation uses `--no-index` pip flag to install from local packages only. No internet connection required.

For detailed offline deployment instructions, see: [INSTALL_OFFLINE.md](INSTALL_OFFLINE.md)

---

## Configuration

### Plugin Configuration Files

Both plugins have configuration files that can be edited directly:

#### TOR Plugin Configuration

**File**: `plugin/tor/config.json`

```json
{
  "enabled": true,
  "github_url": "https://raw.githubusercontent.com/PeeBee66/Updated_TOR_Nodes/main/tor_nodes_latest.csv",
  "verify_ssl": false,
  "opencti_url": "http://localhost:8080",
  "opencti_token": "YOUR_OPENCTI_API_TOKEN",
  "auto_ingest": true
}
```

**Key Settings**:
- `enabled`: Enable/disable the plugin
- `github_url`: Source URL for TOR node CSV data
- `opencti_url`: Your OpenCTI instance URL
- `opencti_token`: API token from OpenCTI (Settings → API Access)
- `auto_ingest`: Auto-ingest new nodes at 10:00 UTC daily
- `verify_ssl`: Set to `false` for self-signed certificates

#### MalwareBazaar Plugin Configuration

**File**: `plugin/malwarebazaar/config.json`

```json
{
  "enabled": true,
  "github_url": "https://api.github.com/repos/PeeBee66/MB_Dataset/contents/uploads",
  "verify_ssl": false,
  "opencti_url": "https://172.21.32.183:4000",
  "opencti_token": "YOUR_OPENCTI_API_TOKEN",
  "auto_ingest": true
}
```

**Key Settings**:
- `enabled`: Enable/disable the plugin
- `github_url`: GitHub API URL for malware dataset
- `opencti_url`: Your OpenCTI instance URL
- `opencti_token`: API token from OpenCTI
- `auto_ingest`: Auto-ingest new samples at 13:00 UTC daily
- `verify_ssl`: Set to `false` for self-signed certificates

### Applying Configuration Changes

After editing configuration files:

```bash
# Restart container to apply changes
./stop.sh
./start.sh

# Or use docker-compose
docker-compose restart opencti-injester
```

---

## Post-Deployment Verification

### 1. Container Health Check

```bash
# Check container status
docker ps -a | grep opencti-injester

# Expected output: Container status should be "Up"
```

### 2. Web Interface Check

```bash
# Test web interface is accessible
curl -I http://localhost:5066

# Expected output: HTTP/1.1 200 OK or HTTP/1.1 302 Found (redirect to login)
```

### 3. Plugin Status Check

Access the web interface and verify:
- Dashboard loads correctly
- Plugin cards are visible
- Statistics are displayed

### 4. OpenCTI Connection Test

1. Navigate to plugin settings page
2. Enter OpenCTI URL and API token
3. Save settings
4. Trigger manual fetch
5. Check OpenCTI for ingested data

### 5. Scheduled Tasks Verification

```bash
# Access container shell
docker exec -it opencti-injester /bin/bash

# Check scheduler status (inside container)
# The scheduler runs automatically - check logs for scheduled jobs

# Exit container
exit
```

Check application logs for scheduler entries:
```bash
docker logs opencti-injester | grep -i "scheduler\|scheduled"
```

Expected entries:
- `TOR Plugin: Scheduled daily fetch at 10:00 UTC`
- `MalwareBazaar Plugin: Scheduled daily fetch at 13:00 UTC`

---

## Troubleshooting

### Container Won't Start

**Problem**: `./start.sh` fails or container exits immediately

**Solutions**:

1. Check Docker is running:
   ```bash
   docker info
   ```

2. Check logs for errors:
   ```bash
   docker logs opencti-injester
   ```

3. Verify port 5066 is not in use:
   ```bash
   netstat -tulpn | grep 5066
   # Or on macOS:
   lsof -i :5066
   ```

4. Rebuild image:
   ```bash
   docker-compose build --no-cache opencti-injester
   ./start.sh
   ```

### OpenCTI Connection Failed

**Problem**: Cannot connect to OpenCTI or ingestion fails

**Solutions**:

1. Verify OpenCTI URL is accessible from container:
   ```bash
   docker exec opencti-injester curl -I YOUR_OPENCTI_URL
   ```

2. Check API token is valid:
   - Login to OpenCTI web interface
   - Navigate to Settings → API Access
   - Verify token matches configuration

3. Check SSL certificate issues:
   - For self-signed certs, set `verify_ssl: false` in config
   - For production, ensure valid SSL certificate

4. Check firewall rules:
   - Ensure container can reach OpenCTI network
   - Check if port 8080 (or your OpenCTI port) is accessible

### Plugins Not Loading

**Problem**: Plugins don't appear in dashboard or show errors

**Solutions**:

1. Check plugin configuration files exist:
   ```bash
   ls -l plugin/*/config.json
   ```

2. Verify configuration is valid JSON:
   ```bash
   python3 -m json.tool plugin/tor/config.json
   python3 -m json.tool plugin/malwarebazaar/config.json
   ```

3. Check plugin data directories have proper permissions:
   ```bash
   ls -ld plugin/*/data/
   ```

4. Review application logs for plugin loading errors:
   ```bash
   docker logs opencti-injester | grep -i "plugin"
   ```

### Data Not Ingesting

**Problem**: Manual or automatic ingestion not working

**Solutions**:

1. Verify data was fetched successfully:
   ```bash
   # TOR plugin
   ls -lh plugin/tor/data/

   # MalwareBazaar plugin
   ls -lh plugin/malwarebazaar/data/samples/
   ```

2. Check STIX bundles were generated:
   ```bash
   # TOR plugin
   ls -l plugin/tor/data/*.json

   # MalwareBazaar plugin
   find plugin/malwarebazaar/data/samples -name "*_stix_bundle.json"
   ```

3. Review ingestion logs:
   ```bash
   docker logs opencti-injester | grep -i "ingest\|stix"
   ```

4. Test manual ingestion:
   - Access plugin dashboard
   - Click "Ingest to OpenCTI" button
   - Check for success/error messages

### Permission Denied Errors

**Problem**: Permission errors accessing data directories

**Solutions**:

1. Check directory ownership:
   ```bash
   ls -la plugin/*/data/
   ```

2. Fix permissions if needed:
   ```bash
   # Make directories writable
   chmod -R 755 plugin/tor/data
   chmod -R 755 plugin/malwarebazaar/data
   chmod -R 755 flask_session
   ```

---

## Maintenance

### Starting the Application

```bash
# Simple start
./start.sh

# Or use run.sh for more options
./run.sh start
```

### Stopping the Application

```bash
# Simple stop
./stop.sh

# Or use run.sh
./run.sh stop
```

### Restarting the Application

```bash
# Quick restart
docker-compose restart opencti-injester

# Or full stop/start
./stop.sh && ./start.sh

# Or use run.sh
./run.sh restart
```

### Viewing Logs

```bash
# View recent logs
docker logs opencti-injester

# Follow logs in real-time
docker logs -f opencti-injester

# View last 100 lines
docker logs --tail 100 opencti-injester

# Or use run.sh
./run.sh logs
```

### Updating the Application

```bash
# Stop application
./stop.sh

# Pull latest code changes (if using git)
git pull

# Rebuild image
docker-compose build --no-cache opencti-injester

# Start application
./start.sh
```

### Backing Up Data

```bash
# Create backup directory
mkdir -p backups/$(date +%Y%m%d)

# Backup plugin data
cp -r plugin/tor/data backups/$(date +%Y%m%d)/tor_data
cp -r plugin/malwarebazaar/data backups/$(date +%Y%m%d)/malwarebazaar_data

# Backup configurations
cp plugin/tor/config.json backups/$(date +%Y%m%d)/
cp plugin/malwarebazaar/config.json backups/$(date +%Y%m%d)/
cp docker-compose.yml backups/$(date +%Y%m%d)/

# Create compressed archive
tar -czf backups/opencti_injester_backup_$(date +%Y%m%d).tar.gz \
  backups/$(date +%Y%m%d)/
```

### Cleaning Up

```bash
# Remove stopped containers
docker-compose down

# Remove containers and volumes (WARNING: deletes all data)
docker-compose down -v

# Remove Docker images
docker rmi opencti_injester-opencti-injester

# Or use run.sh clean command (interactive)
./run.sh clean
```

### Monitoring

#### Check Application Status

```bash
# Quick status
./run.sh status

# Detailed container info
docker inspect opencti-injester
```

#### Check Disk Usage

```bash
# Check data directory sizes
du -sh plugin/*/data/

# Check total application size
du -sh .
```

#### Check Scheduler Status

```bash
# Access scheduler status endpoint
curl http://localhost:5066/api/scheduler/status
```

---

## Quick Reference

### Management Scripts

| Command | Description |
|---------|-------------|
| `./start.sh` | Start the application |
| `./stop.sh` | Stop the application |
| `./run.sh help` | Show all management commands |
| `./run.sh status` | Show application status |
| `./run.sh logs` | View application logs |
| `./run.sh build` | Rebuild Docker image |
| `./run.sh shell` | Access container shell |

### Docker Commands

| Command | Description |
|---------|-------------|
| `docker ps` | Show running containers |
| `docker logs opencti-injester` | View container logs |
| `docker exec -it opencti-injester /bin/bash` | Access container shell |
| `docker-compose restart opencti-injester` | Restart container |
| `docker-compose down` | Stop and remove containers |

### Plugin Endpoints

| URL | Description |
|-----|-------------|
| `http://localhost:5066/` | Main dashboard |
| `http://localhost:5066/plugin/tor/` | TOR plugin dashboard |
| `http://localhost:5066/plugin/malwarebazaar/` | MalwareBazaar dashboard |
| `http://localhost:5066/api/scheduler/status` | Scheduler status |

### Data Directories

| Directory | Purpose |
|-----------|---------|
| `plugin/tor/data/` | TOR node CSV files |
| `plugin/malwarebazaar/data/downloads/` | Downloaded tar archives |
| `plugin/malwarebazaar/data/samples/` | Extracted malware samples |
| `plugin/malwarebazaar/data/stix_bundles/` | Generated STIX bundles |
| `flask_session/` | Web session data |

---

## Support

For additional help:
- **Documentation**: Review README.md and CLAUDE.md
- **Logs**: Check `docker logs opencti-injester` for errors
- **OpenCTI Docs**: https://docs.opencti.io
- **Docker Docs**: https://docs.docker.com

---

**Last Updated**: 2025-10-23
