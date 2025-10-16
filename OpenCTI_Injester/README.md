# OpenCTI Injester - GitHub Data Collector

A containerized threat intelligence platform that collects data from GitHub repositories and ingests it into OpenCTI.

## Overview

The OpenCTI Injester is a Flask-based application with a plugin architecture designed to collect threat intelligence data from GitHub repositories and automatically ingest it into OpenCTI. This version is completely rewritten to remove all scraping functionality and focus on GitHub-based data collection.

### Key Features

- **Plugin Architecture**: Modular design supporting multiple data sources
- **Scheduled Collection**: Automated daily data collection at 10:00 AM
- **OpenCTI Integration**: Automatic STIX bundle generation and ingestion at 11:00 AM
- **Offline Deployment**: Self-contained package for air-gapped environments
- **Docker Support**: Containerized deployment with Docker Compose
- **Web Interface**: Simple web UI for configuration and monitoring

## Plugins

### TOR Plugin
- **Source**: GitHub repository with TOR node CSV data
- **Data**: Exit node IP addresses and metadata
- **Features**:
  - Daily CSV download from configurable GitHub URL
  - New node detection (marked as "NEW 24h")
  - Historical node archiving
  - STIX bundle generation for OpenCTI

### MalwareBazaar Plugin
- **Source**: GitHub repository with malware sample datasets
- **Data**: Zipped malware samples with metadata
- **Features**:
  - Daily download of new zip files
  - Automatic extraction with password protection
  - Sample deduplication by SHA256
  - STIX bundle generation for indicators

## Quick Start

### Docker Deployment (Recommended)

1. **Build and run**:
   ```bash
   docker-compose up -d opencti-injester
   ```

2. **Access the application**:
   - URL: http://localhost:5055
   - Default password: `admin`

### Local Development

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the application**:
   ```bash
   python run.py
   ```

## Configuration

### Main Application Settings

Edit `config.json` in the root directory:

```json
{
  "flask_port": 5000,
  "flask_host": "0.0.0.0",
  "opencti_url": "http://your-opencti-instance:8080",
  "opencti_api_key": "your-api-key-here",
  "auto_ingest": true,
  "ingest_interval": 3600
}
```

#### Settings Description

- **flask_port**: Port for the web interface (default: 5000)
- **flask_host**: Host binding for Flask (default: 0.0.0.0)
- **opencti_url**: URL of your OpenCTI instance
- **opencti_api_key**: API key for OpenCTI authentication
- **auto_ingest**: Enable automatic ingestion to OpenCTI
- **ingest_interval**: Interval between ingestion runs (seconds)

## Plugin System

Each plugin operates independently and can be enabled/disabled through its configuration. Plugins are located in the `/plugin` directory.

### Available Plugins

1. **MalwareBazaar**: Malware sample collection and analysis
2. **VirusTotal**: File and URL reputation checking
3. **URLhaus**: Malicious URL tracking
4. **ThreatFox**: IOC collection from various sources

## Offline Deployment

For air-gapped environments:

### Creating Offline Package

```bash
# Prepare offline package with all dependencies
./prepare_offline.sh
```

This creates:
- Docker images (saved as tar files)
- Python packages
- Configuration files
- Deployment script

### Deploying Offline Package

On the target system:

```bash
# Deploy the offline package
./deploy_offline.sh
```

## API Endpoints

### Main Application

- `GET /`: Dashboard overview
- `GET /api/status`: System status
- `POST /api/ingest`: Trigger manual ingestion
- `GET /api/plugins`: List active plugins

### Plugin Endpoints

Each plugin exposes endpoints under `/plugin/{plugin_name}/`:
- `GET /plugin/{plugin_name}/`: Plugin dashboard
- `GET /plugin/{plugin_name}/settings`: Plugin configuration
- `POST /plugin/{plugin_name}/import`: Import data

## Directory Structure

```
OpenCTI_Injester/
├── run.py                 # Main application entry point
├── config.json           # Main configuration
├── requirements.txt      # Python dependencies
├── docker-compose.yml    # Docker composition
├── Dockerfile           # Container definition
├── plugin/              # Plugin directory
│   ├── malwarebazaar/
│   ├── virustotal/
│   ├── urlhaus/
│   └── threatfox/
├── static/              # Static assets
├── templates/           # HTML templates
└── offline-packages/    # Offline deployment packages
```

## Monitoring

### Logs

- Application logs: `./logs/app.log`
- Plugin logs: `./logs/{plugin_name}.log`
- Docker logs: `docker logs opencti_injester`

### Health Checks

The application provides health check endpoints:
- `/health`: Basic health status
- `/api/metrics`: Detailed metrics

## Security Considerations

1. **API Keys**: Store API keys securely and never commit them to version control
2. **Network Security**: Use HTTPS for production deployments
3. **Access Control**: Implement authentication for the web interface
4. **Malware Handling**: Exercise caution when handling malware samples
5. **OpenCTI Connection**: Use secure connections to OpenCTI

## Troubleshooting

### Common Issues

1. **Connection to OpenCTI Failed**
   - Verify OpenCTI URL and API key
   - Check network connectivity
   - Ensure OpenCTI is running

2. **Plugin Not Loading**
   - Check plugin configuration file
   - Verify plugin dependencies
   - Review plugin logs

3. **Docker Issues**
   - Ensure Docker daemon is running
   - Check port conflicts
   - Verify Docker compose configuration

## Contributing

Contributions are welcome! To add a new plugin:

1. Create a new directory in `/plugin`
2. Implement the plugin interface
3. Add configuration file
4. Create templates and static assets
5. Submit a pull request

## License

[Your License Here]

## Support

For issues and questions:
- GitHub Issues: [repository issues page]
- Documentation: [documentation link]
- Community: [community forum/discord]