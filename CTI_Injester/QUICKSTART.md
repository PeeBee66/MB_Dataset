# Quick Start Guide

## Current Status ✅

**Application is RUNNING and READY!**

- 🌐 Web Interface: **http://localhost:5066**
- 🔑 Default Password: **admin**
- 🐳 Container: **opencti-injester** (running)
- 📦 Docker Image: **cti_injester-opencti-injester** (627MB)

## Management Commands

Use the `./run.sh` script for easy management:

```bash
# Start the application
./run.sh start

# Stop the application
./run.sh stop

# Restart the application
./run.sh restart

# Check status
./run.sh status

# View live logs
./run.sh logs

# Rebuild Docker image
./run.sh build

# Access container shell
./run.sh shell

# Clean up everything
./run.sh clean
```

## Quick Access

### Web Interface
```
http://localhost:5066
```

Default credentials:
- Password: `admin`

### View Logs
```bash
./run.sh logs
```

### Check Status
```bash
./run.sh status
```

## What's Available

### Installed Plugins

1. **TOR Nodes Monitor**
   - URL: http://localhost:5066/plugin/tor/
   - Monitors TOR exit nodes from GitHub
   - Auto-fetch: Daily at 10:00 AM
   - Config: `plugin/tor/config.json`

2. **MalwareBazaar Dataset**
   - URL: http://localhost:5066/plugin/malwarebazaar/
   - Collects malware samples from GitHub
   - Config: `plugin/malwarebazaar/config.json`

## Configuration

### Plugin Settings

Edit the configuration files before first use:

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

### Change Default Password

Edit `docker-compose.yml`:
```yaml
environment:
  - APP_PASSWORD=your-secure-password
  - SECRET_KEY=your-random-secret-key
```

Then restart:
```bash
./run.sh restart
```

## Troubleshooting

### Container Won't Start

Check logs:
```bash
./run.sh logs
```

### Port Already in Use

Change port in `docker-compose.yml`:
```yaml
ports:
  - "5067:5055"  # Changed from 5066
```

Then:
```bash
./run.sh stop
./run.sh start
```

### Rebuild Image

If you make changes to code:
```bash
./run.sh build
./run.sh start
```

## Data Persistence

Data is stored in these directories (mounted as volumes):

```
plugin/tor/data/              # TOR node data
plugin/malwarebazaar/data/    # Malware samples
flask_session/                # User sessions
```

These directories persist even after container stops.

## Next Steps

1. **Configure Plugins**: Edit plugin config files with your OpenCTI credentials
2. **Access Web UI**: Go to http://localhost:5066
3. **Monitor Logs**: Run `./run.sh logs` to watch activity
4. **Test Fetch**: Use plugin dashboards to manually trigger data collection

## Offline Installation

This application includes full offline support:

```bash
./install_offline.sh  # Automated offline installation
```

See `INSTALL_OFFLINE.md` for complete offline deployment guide.

## Architecture Documentation

- `CLAUDE.md` - Full technical documentation for developers
- `INSTALL_OFFLINE.md` - Complete offline installation guide
- `OFFLINE_PACKAGE_README.md` - Package details and specifications
- `README.md` - General project information

## Support

### Check Status
```bash
./run.sh status
```

### View Real-time Logs
```bash
./run.sh logs
```

### Access Container
```bash
./run.sh shell
```

### Restart Everything
```bash
./run.sh restart
```
