# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**OpenCTI Injester** is a Flask-based threat intelligence platform that collects data from GitHub repositories and ingests it into OpenCTI. The application features a plugin architecture with two main data collectors:

- **TOR Plugin**: Monitors TOR exit nodes from GitHub CSV data
- **MalwareBazaar Plugin**: Collects malware samples from GitHub repositories and creates STIX bundles

The system automatically fetches data daily, generates STIX 2.1 bundles, and ingests them into OpenCTI for threat intelligence analysis.

**Offline Capability**: The application is fully offline-installable with all Python dependencies (62 packages, 43MB) pre-bundled in `offline-packages/`. Installation requires NO internet access - only Docker is needed.

## Development Commands

### Running the Application

```bash
# Local development
python3 run.py

# Access web interface at http://localhost:5055

# Docker deployment (recommended)
docker-compose up -d opencti-injester

# Offline/air-gapped deployment
docker-compose --profile offline up -d opencti-injester-offline
```

### Testing and Verification

```bash
# Verify OpenCTI ingestion
python3 verify_ingestion.py

# Query specific entities
python3 query_specific_entities.py

# Manual import helper (lists all samples)
./manual_import_all.sh
```

### Offline Deployment

```bash
# Install on air-gapped system (no internet required)
./install_offline.sh

# Build includes all dependencies
docker-compose build opencti-injester

# Start application
docker-compose up -d opencti-injester
```

## Architecture

### Plugin System

The application uses a **dynamic plugin loader** (`run.py:load_plugins()`):

1. Scans `/plugin` directory for subdirectories
2. Each plugin must have `main.py` with `create_blueprint()` function
3. Plugins registered at `/plugin/{plugin_name}` URL prefix
4. Plugins can optionally implement `initialize_scheduler()` for scheduled tasks

**Plugin Structure**:
```
plugin/{plugin_name}/
├── main.py              # Blueprint and routes (required)
├── config.json          # Plugin configuration
├── data/                # Plugin data directory
└── templates/           # Plugin-specific templates
    └── {plugin_name}/
        └── index.html
```

### Scheduling System

- Uses **APScheduler** (`BackgroundScheduler`) shared across all plugins
- Initialized in `run.py` and passed to plugins via `initialize_scheduler()`
- TOR Plugin: Fetches daily at 10:00 AM
- MalwareBazaar Plugin: Custom schedule based on configuration

### Data Flow

1. **Fetch**: Plugin downloads data from GitHub (CSV for TOR, tar files for MalwareBazaar)
2. **Process**: Data is parsed, deduplicated, and stored locally
3. **STIX Generation**: Creates STIX 2.1 bundles with proper relationships
4. **Ingestion**: Sends to OpenCTI via GraphQL API (native API, not pycti bundle import)

### TOR Plugin Architecture

**4-File CSV System** (`plugin/tor/main.py:fetch_tor_nodes()`):
- `tor_nodes_latest.csv`: Current snapshot from GitHub
- `tor_nodes_old.csv`: Previous snapshot (for comparison)
- `NEW_NODES.csv`: Newly detected nodes (auto-ingested immediately)
- `OLD_NODES.csv`: Removed/dead nodes (append-only archive)

**STIX Objects Created**:
- `infrastructure`: TOR relay nodes
- `ipv4-addr`: IP addresses
- `relationship`: "consists-of" (infrastructure → IP)
- `identity`: "TOR Network Monitor" (consistent UUID for attribution)

**Ingestion Strategy**: Processes each node individually to avoid overwhelming OpenCTI API.

### MalwareBazaar Plugin Architecture

Downloads tar files from GitHub, extracts samples, and catalogs metadata.

**Directory Structure**:
- `data/downloads/`: Raw tar files from GitHub
- `data/samples/{tag}/{sha256}/`: Extracted samples organized by tag
- `data/stix_bundles/`: Generated STIX bundles
- `malware_catalog.json`: Metadata catalog

**STIX Objects Created**:
- `malware`: Malware entity with types, labels, confidence
- `file`: Observable with 6 hash types (MD5, SHA-1, SHA-256, SHA3-384, ssdeep, TLSH)
- `indicator`: STIX pattern for detection
- `relationship`: malware→file (related-to), indicator→malware (indicates)
- `identity`: "Malware Bazaar Auto Plugin" (consistent attribution)

### OpenCTI Integration

**Known Platform Issue**: The `pycti` library's `import_bundle_from_json()` method returns success but **fails to persist entities** (only indicators are saved). This is an OpenCTI platform bug documented in `MANUAL_IMPORT_GUIDE.md`.

**Current Workaround**: Both plugins use **native GraphQL API** to create entities individually:
- Create IPv4/File observables first
- Create Infrastructure/Malware entities
- Create Relationships linking entities
- Process one entity at a time to ensure persistence

**Configuration**: Both plugins require:
- `opencti_url`: OpenCTI instance URL
- `opencti_token`: API token with write permissions
- `verify_ssl`: Set to `false` for self-signed certificates
- `auto_ingest`: Enable automatic ingestion after fetch

## Important Implementation Details

### SSL/Certificate Handling

All OpenCTI connections use `verify=False` for self-signed certificates:
```python
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
requests.post(url, verify=config.get('verify_ssl', False), ...)
```

### Deterministic UUIDs

Both plugins use **UUID5** (namespace-based) for consistent IDs:
```python
# TOR plugin
infrastructure_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"tor-infrastructure-{ip_address}"))

# Prevents duplicate entities across fetches
```

### Session Management

Uses **Flask-Session** with filesystem storage:
- Simple authentication: session flag `authenticated=True`
- Default password: `admin` (via `APP_PASSWORD` env var)
- Session files stored in `./flask_session/`

### Auto-Ingestion Flow

**TOR Plugin**:
1. Fetch runs at 10:00 AM daily
2. New nodes detected automatically
3. Auto-ingest triggers immediately for new nodes only (`NEW_NODES.csv`)
4. Each node sent individually to OpenCTI GraphQL API

**MalwareBazaar Plugin**:
1. Download scheduled based on `download_interval_hours`
2. Extract and catalog samples
3. Generate STIX bundles
4. Auto-ingest if `auto_ingest_after_download=true`

### Error Handling

Both plugins implement:
- Individual entity processing (not batch) to isolate failures
- Detailed logging with `logging.getLogger(__name__)`
- Success/failure counters for ingestion
- Graceful degradation (continues on individual failures)

## Configuration Files

### Main Application (`config.json` - not currently used)
The main config is primarily environment-based. Plugins have their own configs.

### TOR Plugin (`plugin/tor/config.json`)
```json
{
  "enabled": true,
  "github_url": "https://raw.githubusercontent.com/PeeBee66/Updated_TOR_Nodes/main/tor_nodes_latest.csv",
  "verify_ssl": false,
  "opencti_url": "http://localhost:8080",
  "opencti_token": "YOUR_TOKEN",
  "auto_ingest": true
}
```

### MalwareBazaar Plugin (`plugin/malwarebazaar/config.json`)
```json
{
  "enabled": true,
  "github_url": "https://api.github.com/repos/PeeBee66/MB_Dataset/contents/uploads",
  "verify_ssl": false,
  "opencti_url": "https://172.21.32.183:4000",
  "opencti_token": "YOUR_TOKEN",
  "auto_ingest": true
}
```

## Testing Workflow

1. **Test plugin loading**: Check console output when starting `run.py`
2. **Test manual fetch**: Use web UI or API endpoints to trigger fetch
3. **Verify local data**: Check CSV files (TOR) or samples directory (MalwareBazaar)
4. **Test STIX generation**: Bundles created in respective directories
5. **Test OpenCTI ingestion**: Use `verify_ingestion.py` to query GraphQL
6. **Check scheduler**: Visit `/api/scheduler/status` endpoint

## Deployment Modes

### Development
- Direct Python execution: `python3 run.py`
- Debug mode enabled
- Hot reload for templates
- Port 5055

### Production (Docker)
- Build from `Dockerfile`
- Volumes for persistent data
- Environment variables for secrets
- Restart policy: `unless-stopped`

### Offline (Air-gapped)
- Pre-downloaded Python packages in `offline-packages/` (62 packages, 43MB)
- Docker image with bundled dependencies (uses `--no-index` pip flag)
- No internet connectivity required for installation
- Installation script: `./install_offline.sh`
- Full guide: `INSTALL_OFFLINE.md`

## API Endpoints

### Main Application
- `GET /`: Dashboard (requires authentication)
- `GET /login`: Authentication page
- `GET /logout`: Clear session
- `GET /api/scheduler/status`: Scheduler jobs and status
- `GET /health`: Health check

### TOR Plugin (`/plugin/tor/`)
- `GET /`: Dashboard with new/dead/all nodes tabs
- `POST /fetch_nodes`: Trigger manual fetch
- `POST /ingest_to_opencti`: Manual ingestion to OpenCTI
- `GET /new-nodes`: Get newly detected nodes
- `GET /old-nodes`: Get archived dead nodes
- `GET|POST /settings`: Plugin configuration

### MalwareBazaar Plugin (`/plugin/malwarebazaar/`)
- `GET /`: Dashboard with samples catalog
- `POST /download`: Trigger manual download
- `POST /ingest`: Manual ingestion to OpenCTI
- `GET /sample/{sha256}/download`: Download STIX bundle
- `GET|POST /settings`: Plugin configuration

## Common Development Tasks

### Adding a New Plugin

1. Create `plugin/{name}/main.py` with `create_blueprint()` function
2. Define `PLUGIN_NAME` and `PLUGIN_DESCRIPTION` module variables
3. Implement `initialize_scheduler(scheduler)` for scheduled tasks
4. Create `plugin/{name}/templates/{name}/index.html`
5. Add `config.json` for plugin settings
6. Restart application - plugin auto-discovered

### Modifying STIX Bundle Structure

1. Edit STIX creation function in plugin (e.g., `create_stix_bundle()`)
2. Ensure all objects have `created_by_ref` for attribution
3. Use deterministic UUIDs for idempotency
4. Test ingestion with single entity first
5. Verify in OpenCTI GraphQL explorer

### Debugging OpenCTI Ingestion Issues

1. Check `verify_ingestion.py` for entity queries
2. Review OpenCTI platform logs: `docker logs opencti-platform`
3. Test GraphQL mutations in OpenCTI GraphQL playground
4. Use manual import via Web UI as validation
5. Compare STIX bundle against OpenCTI schema requirements

## Key Files

- `run.py` - Main Flask application and plugin loader (148 lines)
- `plugin/tor/main.py` - TOR plugin implementation (852 lines)
- `plugin/malwarebazaar/main.py` - MalwareBazaar plugin (extensive)
- `verify_ingestion.py` - OpenCTI verification queries
- `MANUAL_IMPORT_GUIDE.md` - Workaround for OpenCTI persistence bug
- `DEVELOPER_BUILD_GUIDE.md` - Detailed build instructions
- `requirements.txt` - Python dependencies

## Security Considerations

- API tokens stored in plugin configs (exclude from git)
- Malware samples handled in `data/samples/` - treat as hostile
- SSL verification disabled for self-signed certs (development only)
- Simple session-based auth (replace for production)
- No CSRF protection (add for production)
- Docker volumes for persistent data isolation
