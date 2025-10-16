# OpenCTI Injester - Developer Build Guide

## Project Overview
OpenCTI Injester is a Flask-based plugin system for ingesting threat intelligence data into OpenCTI. The primary plugin is MalwareBazaar, which downloads malware samples, creates STIX bundles, and ingests them into OpenCTI.

## System Requirements

### Core Dependencies
- Python 3.8+
- Flask 2.0+
- Docker (optional, for containerized deployment)
- Git

### Python Package Requirements
```bash
# Core Flask
flask>=2.0.0
werkzeug>=2.0.0

# OpenCTI Integration
pycti>=5.0.0
stix2>=3.0.0

# API & Network
requests>=2.28.0
urllib3>=1.26.0

# File Processing
python-magic>=0.4.27
pyzipper>=0.3.6

# Scheduling & Background Tasks
schedule>=1.1.0
python-dateutil>=2.8.2

# Data Processing
pandas>=1.5.0
pytz>=2023.3
```

## Project Structure
```
/home/ws-admin/PROJECTS/OpenCTI_Injester/
├── run.py                      # Main Flask application entry point
├── config.py                   # Global configuration
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Docker container definition
├── docker-compose.yml          # Docker compose configuration
├── plugin/                     # Plugin directory
│   └── malwarebazaar/         # MalwareBazaar plugin
│       ├── main.py            # Plugin blueprint and routes
│       ├── config.json        # Plugin configuration
│       ├── stix_builder.py    # STIX bundle generator
│       ├── catalog.json       # Sample metadata catalog
│       ├── templates/         # HTML templates
│       │   └── malwarebazaar/
│       │       ├── index.html
│       │       └── settings.html
│       ├── samples/           # Downloaded malware samples
│       ├── stix/              # Generated STIX bundles
│       ├── auto_imports/      # Auto-import directory
│       ├── auto_exports/      # Auto-export directory
│       └── auto_backups/      # Auto-backup directory
└── static/                    # Static assets (CSS, JS)

```

## Installation Steps

### 1. Clone/Setup Project
```bash
# Create project directory
mkdir -p /home/ws-admin/PROJECTS/OpenCTI_Injester
cd /home/ws-admin/PROJECTS/OpenCTI_Injester

# Initialize git (optional)
git init
```

### 2. Create Core Application Files

#### run.py
```python
from flask import Flask, render_template
import os
import importlib.util
from pathlib import Path

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'

# Plugin loader
def load_plugins():
    plugin_dir = Path(__file__).parent / 'plugin'
    for plugin_folder in plugin_dir.iterdir():
        if plugin_folder.is_dir():
            main_file = plugin_folder / 'main.py'
            if main_file.exists():
                spec = importlib.util.spec_from_file_location(
                    f"plugin.{plugin_folder.name}", 
                    main_file
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                if hasattr(module, 'bp'):
                    app.register_blueprint(
                        module.bp, 
                        url_prefix=f'/plugin/{plugin_folder.name}'
                    )

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    load_plugins()
    app.run(host='0.0.0.0', port=5055, debug=True)
```

### 3. Install Python Dependencies
```bash
pip3 install flask requests pycti stix2 python-magic pyzipper schedule python-dateutil pytz
```

### 4. Configure OpenCTI Connection

Create initial config for MalwareBazaar plugin:
```json
{
  "api_key": "YOUR_MALWAREBAZAAR_API_KEY",
  "bazaar_urls": ["https://mb-api.abuse.ch/api/v1/"],
  "tags": ["apk", "ios", "macho"],
  "max_samples_per_tag": 100,
  "download_interval_hours": 1,
  "timeout_seconds": 60,
  "samples_directory": "/home/ws-admin/PROJECTS/OpenCTI_Injester/plugin/malwarebazaar/samples",
  "opencti_url": "https://YOUR_OPENCTI_IP:4000",
  "opencti_api_key": "YOUR_OPENCTI_API_KEY",
  "opencti_ssl_verify": false,
  "opencti_timeout": 30,
  "enabled": true,
  "auto_ingest_after_download": true
}
```

## Key Features & Fixes Applied

### 1. Delete Functionality Enhancement
The delete functionality has been enhanced to ensure complete removal of sample folders:
- Temporarily disables the plugin during deletion
- Adds 2-second delay for running downloads to finish
- Force removes files even if in use
- Double-checks for remaining files after deletion
- Restores original enabled state when complete

### 2. Backup/Import Format Compatibility
- Backup creates `.tar` files
- Import function handles both `.tar` and `.tar.gz` formats
- Automatic format detection in import_offline_package()

### 3. Configuration Fields
- Removed duplicate `samples_per_tag` field
- Uses only `max_samples_per_tag` for sample limits
- All settings properly persist through the web UI

### 4. SSL/HTTPS Support
- SSL verification can be disabled for self-signed certificates
- Set `opencti_ssl_verify: false` in config for self-signed certs
- Uses `verify=False` in requests when SSL verification is disabled

## Operation Modes

### 1. Download Mode
- **Enabled**: `"enabled": true, "auto_import_enabled": false`
- Downloads fresh samples from MalwareBazaar API
- Runs on schedule (hourly or daily at 12:00 PM)
- Auto-ingests to OpenCTI if configured

### 2. Import Mode  
- **Enabled**: `"enabled": false, "auto_import_enabled": true`
- Imports backup `.tar` files from auto_imports folder
- Processes daily at 12:00 PM
- Overwrites catalog with imported data

### 3. Disabled Mode
- **Enabled**: `"enabled": false, "auto_import_enabled": false`
- No automatic operations
- Manual operations only via web UI

## Web Interface Routes

### Main Routes
- `/` - Main application index
- `/plugin/malwarebazaar/` - Plugin dashboard
- `/plugin/malwarebazaar/settings` - Configuration page
- `/plugin/malwarebazaar/catalog` - View sample catalog

### API Endpoints
- `POST /plugin/malwarebazaar/download` - Manual download trigger
- `POST /plugin/malwarebazaar/ingest` - Manual ingestion to OpenCTI
- `POST /plugin/malwarebazaar/delete-data` - Delete all plugin data
- `POST /plugin/malwarebazaar/create-backup` - Create manual backup
- `POST /plugin/malwarebazaar/test-auto-import` - Test import functionality
- `GET /plugin/malwarebazaar/api/config` - Get current configuration
- `GET /plugin/malwarebazaar/api/stats` - Get statistics

## Docker Deployment (Optional)

### Dockerfile
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5055

CMD ["python", "run.py"]
```

### docker-compose.yml
```yaml
version: '3.8'

services:
  opencti-injester:
    build: .
    ports:
      - "5055:5055"
    volumes:
      - ./plugin:/app/plugin
      - ./static:/app/static
      - ./templates:/app/templates
    environment:
      - FLASK_ENV=development
    restart: unless-stopped
```

## Running the Application

### Development Mode
```bash
cd /home/ws-admin/PROJECTS/OpenCTI_Injester
python3 run.py
```

### Production Mode with Docker
```bash
docker-compose up -d
```

### Access Points
- Web Interface: `http://localhost:5055`
- MalwareBazaar Plugin: `http://localhost:5055/plugin/malwarebazaar/`

## Troubleshooting

### Common Issues

1. **SSL Certificate Errors**
   - Set `"opencti_ssl_verify": false` in config.json
   - For self-signed certificates

2. **Sample Folders Not Deleting**
   - Fixed with enhanced delete function
   - Temporarily disables scheduler during deletion

3. **Import Format Issues**
   - Import function now handles both .tar and .tar.gz
   - Automatic format detection

4. **Settings Not Saving**
   - Removed duplicate `samples_per_tag` field
   - Use only `max_samples_per_tag`

5. **Scheduler Running Multiple Times**
   - Singleton pattern implemented
   - Check with `ps aux | grep python` for duplicates

## Testing Checklist

- [ ] Flask application starts on port 5055
- [ ] Plugin loads successfully (check console output)
- [ ] Web interface accessible
- [ ] Settings page loads and saves correctly
- [ ] Manual download works
- [ ] OpenCTI connection test passes
- [ ] STIX bundles generate correctly
- [ ] Ingestion to OpenCTI succeeds
- [ ] Delete functionality removes all samples
- [ ] Backup creates .tar file successfully
- [ ] Import processes backup files correctly
- [ ] Scheduler runs at configured intervals

## Environment Variables (Optional)

```bash
export OPENCTI_URL="https://172.21.32.183:4000"
export OPENCTI_API_KEY="your-api-key"
export MALWAREBAZAAR_API_KEY="your-mb-key"
export FLASK_PORT=5055
```

## Security Considerations

1. **API Keys**: Store securely, never commit to git
2. **SSL Verification**: Only disable for development/testing
3. **File Permissions**: Ensure proper permissions on sample directories
4. **Network Access**: Restrict access to Flask port in production
5. **Sample Handling**: Downloaded samples are malware - handle with care

## Maintenance Tasks

### Daily
- Monitor disk space in samples directory
- Check OpenCTI ingestion success rate
- Review error logs

### Weekly  
- Clean old backup files (auto-cleanup configured)
- Review catalog size and optimize if needed
- Check for duplicate entries

### Monthly
- Update Python dependencies
- Review and optimize STIX bundle generation
- Performance tuning if needed

## Support & Documentation

- OpenCTI Documentation: https://docs.opencti.io/
- MalwareBazaar API: https://bazaar.abuse.ch/api/
- STIX 2.1 Specification: https://docs.oasis-open.org/cti/stix/v2.1/
- Flask Documentation: https://flask.palletsprojects.com/

## Version History

- v1.0 - Initial implementation
- v1.1 - Added backup/import functionality  
- v1.2 - Enhanced delete functionality
- v1.3 - Fixed SSL verification issues
- v1.4 - Resolved config field duplicates
- v1.5 - Import format compatibility (.tar and .tar.gz)

## Notes for Developers

1. Always test in a sandboxed environment when handling malware samples
2. Use virtual environments for Python dependencies
3. Implement proper error handling for all API calls
4. Log all critical operations for debugging
5. Maintain backward compatibility when updating config structure
6. Test all modes (download/import/disabled) after changes
7. Ensure STIX bundles comply with OpenCTI requirements
8. Monitor memory usage with large sample sets

---
Last Updated: August 2025
Author: OpenCTI Injester Development Team