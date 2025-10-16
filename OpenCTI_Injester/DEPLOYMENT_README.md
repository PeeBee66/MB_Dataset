# OpenCTI Injester - Deployment Package

## Package Contents

This deployment package includes:

- **OpenCTI Injester Application** - Flask-based web interface for MalwareBazaar data ingestion
- **Docker Image** - Pre-built container image with all dependencies (`opencti_injester.tar.gz`)
- **STIX Bundle Download Endpoint** - New feature for manual STIX bundle downloads
- **Manual Import Tools** - Scripts and guides for manual OpenCTI import
- **Offline Deployment Support** - Can be deployed without internet access

## What's New in This Export

✅ **Download Endpoint Added**: New `/sample/<hash>/download` route for easy STIX bundle downloads
✅ **Manual Import Guide**: Complete documentation for manual OpenCTI imports
✅ **Verification Scripts**: Tools to check which entities exist in OpenCTI
✅ **Batch Import Helper**: Script to list all available STIX bundles

## Deployment Files

```
opencti-injester-export-20251016-031648.tar.gz  (44M)  - Main deployment package
opencti_injester.tar.gz                         (200M) - Docker image only
```

## Quick Deployment

### Method 1: Using Docker (Recommended)

1. **Extract the package:**
   ```bash
   tar -xzf opencti-injester-export-20251016-031648.tar.gz
   cd opencti-injester/
   ```

2. **Load Docker image:**
   ```bash
   gunzip opencti_injester.tar.gz
   docker load -i opencti_injester.tar
   ```

3. **Start the application:**
   ```bash
   docker compose up -d opencti-injester
   ```

4. **Access the application:**
   - URL: http://localhost:5055
   - Default password: `admin`

### Method 2: Offline Deployment

If Docker is not available or you need offline installation:

```bash
tar -xzf opencti-injester-export-20251016-031648.tar.gz
cd opencti-injester/
./deploy_offline.sh
```

## Configuration

### Environment Variables

Edit `docker-compose.yml` to configure:

```yaml
environment:
  - APP_PASSWORD=admin              # Change this!
  - SECRET_KEY=change-this-in-production-environment  # Change this!
  - PYTHONUNBUFFERED=1
```

### Data Persistence

The application stores data in:
- `plugin/tor/data/` - Tor exit node data
- `plugin/malwarebazaar/data/` - Malware samples and STIX bundles
- `flask_session/` - User sessions

These directories are mounted as volumes and persist across container restarts.

## Features

### MalwareBazaar Plugin

- Automatic download of recent malware samples
- STIX 2.1 bundle generation with complete metadata
- All hash types included (MD5, SHA-1, SHA-256, SHA3-384, TLSH, ssdeep)
- OpenCTI integration (API-based ingestion)
- Manual import support when API ingestion fails

### Tor Exit Node Plugin

- Daily updates of Tor exit node list
- IP address tracking
- Geographic location data

### STIX Bundle Management

**New Download Endpoint:**
```
http://localhost:5055/plugin/malwarebazaar/sample/<hash>/download
```

This allows direct download of STIX bundles for manual import into OpenCTI.

## Manual Import to OpenCTI

If automated API ingestion fails, use manual import:

### Method 1: Download and Upload

1. Download bundle:
   ```
   http://localhost:5055/plugin/malwarebazaar/sample/<hash>/download
   ```

2. Import in OpenCTI:
   - Go to: `https://<opencti-url>/dashboard/data/import`
   - Click "Import from file"
   - Upload the downloaded JSON file

### Method 2: Copy and Paste

1. View sample in plugin UI
2. Click "Copy STIX Bundle to Clipboard"
3. Paste into OpenCTI's "Import from text" feature

**See `MANUAL_IMPORT_GUIDE.md` for detailed instructions.**

## Verification Tools

### Check Entity Import Status

```bash
python3 check_specific_bundle.py
```

This script verifies which entities from a STIX bundle exist in OpenCTI.

### List All Available Bundles

```bash
./manual_import_all.sh
```

Shows all STIX bundles with download URLs and file paths.

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker logs opencti-injester

# Restart
docker compose restart opencti-injester
```

### Port Already in Use

Edit `docker-compose.yml` and change port mapping:
```yaml
ports:
  - "5056:5055"  # Use different port
```

### OpenCTI Integration Issues

1. **Check API Token**: Verify token in plugin settings
2. **Network Connectivity**: Ensure container can reach OpenCTI
3. **Use Manual Import**: If API fails, use manual import methods

### Permission Issues

```bash
# Fix data directory permissions
chmod -R 755 plugin/*/data
```

## Security Considerations

1. **Change Default Password**: Update `APP_PASSWORD` in `docker-compose.yml`
2. **Change Secret Key**: Update `SECRET_KEY` for production use
3. **Network Security**: Consider reverse proxy with SSL/TLS
4. **API Tokens**: Store OpenCTI tokens securely

## Monitoring

### View Logs

```bash
# Real-time logs
docker logs -f opencti-injester

# Or use Dozzle (if available)
http://localhost:9999
```

### Check Status

```bash
docker ps | grep opencti-injester
```

## Backup

### Backup Data

```bash
tar -czf opencti-injester-backup-$(date +%Y%m%d).tar.gz \
  plugin/tor/data \
  plugin/malwarebazaar/data \
  flask_session
```

### Restore Data

```bash
tar -xzf opencti-injester-backup-YYYYMMDD.tar.gz
docker compose restart opencti-injester
```

## Uninstall

```bash
# Stop and remove container
docker compose down

# Remove image
docker rmi opencti_injester-opencti-injester

# Remove data (optional)
rm -rf plugin/*/data flask_session
```

## Support

- **Plugin UI**: http://localhost:5055/plugin/malwarebazaar/
- **Manual Import Guide**: `MANUAL_IMPORT_GUIDE.md`
- **Export Script**: `export_for_deployment.sh`
- **Deployment Script**: `deploy_offline.sh`

## System Requirements

- Docker 20.10+ and Docker Compose 2.0+
- OR Python 3.11+ (for non-Docker deployment)
- 500MB disk space minimum
- 1GB RAM minimum

## License

This is a defensive security tool for threat intelligence collection and analysis. Use responsibly.
