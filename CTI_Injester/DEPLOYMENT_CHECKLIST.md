# OpenCTI Injester - Deployment Checklist

Quick reference checklist for deploying the OpenCTI Injester application.

---

## Pre-Deployment Checklist

### Required Software
- [ ] Docker installed (version 20.10+)
  ```bash
  docker --version
  ```
- [ ] Docker Compose installed (version 2.0+)
  ```bash
  docker-compose --version
  ```
- [ ] Docker daemon running
  ```bash
  docker info
  ```

### System Requirements
- [ ] Minimum 2GB RAM available
- [ ] Minimum 5GB disk space free
- [ ] Port 5066 available (or choose different port in docker-compose.yml)

### OpenCTI Prerequisites
- [ ] OpenCTI instance running and accessible
- [ ] OpenCTI API token generated (Settings → API Access)
- [ ] Network connectivity between container and OpenCTI

---

## Deployment Steps

### 1. Initial Setup
```bash
# Navigate to application directory
cd /path/to/CTI_Injester

# Verify all files present
ls -l
```

**Required Files:**
- [ ] `start.sh` - Start script
- [ ] `stop.sh` - Stop script
- [ ] `run.sh` - Management script
- [ ] `docker-compose.yml` - Container configuration
- [ ] `Dockerfile` - Image definition
- [ ] `requirements.txt` - Python dependencies
- [ ] `run.py` - Main application
- [ ] `plugin/` directory with TOR and MalwareBazaar plugins
- [ ] `offline-packages/` directory (62 packages)
- [ ] `templates/` directory

### 2. Configure Environment (Optional)

Edit `docker-compose.yml`:
```yaml
environment:
  - APP_PASSWORD=admin              # Change this!
  - SECRET_KEY=change-this-secret   # Change this!
```

- [ ] Changed default password (if needed)
- [ ] Changed secret key (recommended for production)

### 3. Start Application

```bash
# Make scripts executable (if needed)
chmod +x start.sh stop.sh run.sh

# Start application
./start.sh
```

- [ ] Container built successfully
- [ ] Container started successfully
- [ ] No errors in startup logs

### 4. Verify Application

```bash
# Check container status
docker ps | grep opencti-injester

# Check logs
docker logs opencti-injester
```

- [ ] Container status shows "Up"
- [ ] Web interface accessible at http://localhost:5066
- [ ] No errors in application logs

### 5. Access Web Interface

```bash
# Open browser to:
http://localhost:5066
```

- [ ] Login page loads
- [ ] Login successful with password: `admin`
- [ ] Dashboard displays correctly
- [ ] Both plugin cards visible (TOR and MalwareBazaar)

### 6. Configure TOR Plugin

Navigate to: http://localhost:5066/plugin/tor/settings

**Required Settings:**
- [ ] `opencti_url` = Your OpenCTI URL (e.g., https://opencti.example.com)
- [ ] `opencti_token` = Your OpenCTI API token
- [ ] `verify_ssl` = `false` (for self-signed certs) or `true` (production)
- [ ] `auto_ingest` = `true` (enable automatic ingestion)
- [ ] `enabled` = `true`

**Save and Test:**
- [ ] Click "Save Settings"
- [ ] Click "Fetch TOR Nodes" to test
- [ ] Verify nodes are fetched successfully
- [ ] Check OpenCTI for ingested data (optional)

### 7. Configure MalwareBazaar Plugin

Navigate to: http://localhost:5066/plugin/malwarebazaar/settings

**Required Settings:**
- [ ] `opencti_url` = Your OpenCTI URL
- [ ] `opencti_token` = Your OpenCTI API token
- [ ] `verify_ssl` = `false` (for self-signed certs) or `true` (production)
- [ ] `auto_ingest` = `true` (enable automatic ingestion)
- [ ] `enabled` = `true`

**Save and Test:**
- [ ] Click "Save Settings"
- [ ] Click "Download Samples" to test (optional - downloads large files)
- [ ] Verify dashboard shows statistics

### 8. Verify Scheduler

```bash
# Check scheduler status
curl http://localhost:5066/api/scheduler/status
```

**Expected Jobs:**
- [ ] TOR Plugin: Daily fetch at 10:00 UTC
- [ ] MalwareBazaar Plugin: Daily fetch at 13:00 UTC

### 9. Test Ingestion (Optional)

**TOR Plugin:**
1. [ ] Navigate to http://localhost:5066/plugin/tor/
2. [ ] Click "Fetch TOR Nodes" button
3. [ ] Wait for completion
4. [ ] Click "Ingest to OpenCTI" button
5. [ ] Verify success message
6. [ ] Check OpenCTI for new infrastructure entities

**MalwareBazaar Plugin:**
1. [ ] Navigate to http://localhost:5066/plugin/malwarebazaar/
2. [ ] Click "Ingest to OpenCTI" button (uses existing samples)
3. [ ] Verify success message
4. [ ] Check OpenCTI for new malware entities

---

## Post-Deployment Verification

### Application Health
```bash
# Container status
docker ps -a | grep opencti-injester
# Expected: Status "Up"

# Application logs (last 50 lines)
docker logs --tail 50 opencti-injester
# Expected: No errors, shows "Running on http://0.0.0.0:5055"

# Disk usage
du -sh .
# Expected: ~500MB-2GB depending on data
```

- [ ] Container running without restarts
- [ ] No error messages in logs
- [ ] Application responds to HTTP requests

### Data Directories
```bash
# Check data directories exist
ls -l plugin/tor/data/
ls -l plugin/malwarebazaar/data/
ls -l flask_session/
```

- [ ] `plugin/tor/data/` exists and writable
- [ ] `plugin/malwarebazaar/data/` exists and writable
- [ ] `flask_session/` exists and writable

### OpenCTI Connectivity
```bash
# Test connection from container
docker exec opencti-injester curl -I YOUR_OPENCTI_URL
# Expected: HTTP 200 or 302 response
```

- [ ] Container can reach OpenCTI URL
- [ ] No SSL certificate errors (or verify_ssl=false configured)
- [ ] API token valid and working

---

## Troubleshooting Quick Reference

### Container Won't Start
```bash
# Check Docker is running
docker info

# Check port availability
netstat -tulpn | grep 5066

# Rebuild and restart
docker-compose down
docker-compose build --no-cache
./start.sh
```

### Can't Access Web Interface
```bash
# Check container is running
docker ps | grep opencti-injester

# Check application logs
docker logs opencti-injester

# Test port locally
curl -I http://localhost:5066
```

### Plugins Not Working
```bash
# Check plugin configuration files
cat plugin/tor/config.json
cat plugin/malwarebazaar/config.json

# Verify file permissions
ls -la plugin/*/data/

# Restart container
docker-compose restart opencti-injester
```

### OpenCTI Connection Issues
```bash
# Test from container
docker exec opencti-injester curl -I YOUR_OPENCTI_URL

# Check API token in plugin settings
# Verify SSL settings (verify_ssl: false for self-signed)

# Check application logs for detailed errors
docker logs opencti-injester | grep -i "opencti\|error"
```

---

## Management Commands

| Task | Command |
|------|---------|
| Start application | `./start.sh` |
| Stop application | `./stop.sh` |
| Restart | `docker-compose restart opencti-injester` |
| View logs | `docker logs -f opencti-injester` |
| Check status | `./run.sh status` |
| Access shell | `./run.sh shell` |
| Rebuild | `docker-compose build --no-cache` |

---

## Scheduled Operations

The application automatically performs these operations:

| Plugin | Schedule | Action |
|--------|----------|--------|
| TOR | 10:00 UTC daily | Fetch new TOR nodes from GitHub |
| TOR | After fetch | Auto-ingest NEW nodes only to OpenCTI |
| MalwareBazaar | 13:00 UTC daily | Download new samples from GitHub |
| MalwareBazaar | After download | Auto-ingest NEW samples only to OpenCTI |

**Manual Operations:**
- **Manual Fetch**: Trigger immediate fetch from plugin dashboard
- **Manual Ingest**: Ingests ALL data (including already ingested) - use for re-ingestion

---

## Backup Recommendations

```bash
# Create backup
mkdir -p backups/$(date +%Y%m%d)
cp -r plugin/tor/data backups/$(date +%Y%m%d)/
cp -r plugin/malwarebazaar/data backups/$(date +%Y%m%d)/
cp plugin/*/config.json backups/$(date +%Y%m%d)/
tar -czf backups/backup_$(date +%Y%m%d).tar.gz backups/$(date +%Y%m%d)/
```

**Backup Schedule:**
- [ ] Daily automated backup configured
- [ ] Backups stored securely
- [ ] Restore procedure tested

---

## Deployment Complete!

Once all checklist items are complete:

✅ **Application Status:** Running
✅ **Web Interface:** Accessible
✅ **Plugins:** Configured
✅ **OpenCTI:** Connected
✅ **Scheduler:** Active

**Access URLs:**
- Dashboard: http://localhost:5066/
- TOR Plugin: http://localhost:5066/plugin/tor/
- MalwareBazaar: http://localhost:5066/plugin/malwarebazaar/
- Scheduler Status: http://localhost:5066/api/scheduler/status

**Default Credentials:**
- Password: `admin` (change in docker-compose.yml)

---

**For detailed documentation, see:**
- `DEPLOYMENT.md` - Complete deployment guide
- `README.md` - Application overview
- `CLAUDE.md` - Developer documentation

**For support:**
- Check logs: `docker logs opencti-injester`
- Review troubleshooting section above
- See DEPLOYMENT.md for detailed solutions
