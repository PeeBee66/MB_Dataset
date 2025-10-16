#!/usr/bin/env python3
"""
TOR Plugin - Fetches TOR node data from GitHub repository
Pulls CSV data daily at 10:00 AM and ingests into OpenCTI at 11:00 AM
"""

from flask import Blueprint, render_template_string, render_template, jsonify, request
import requests
import csv
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import logging
import pandas as pd
from io import StringIO
import ssl
import urllib3

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Plugin metadata
PLUGIN_NAME = "TOR Nodes Monitor"
PLUGIN_DESCRIPTION = "Monitors and tracks TOR exit nodes from GitHub repository"

# Setup logging
logger = logging.getLogger(__name__)

# Plugin configuration
CONFIG_FILE = Path(__file__).parent / 'config.json'
DATA_DIR = Path(__file__).parent / 'data'

# The 4 CSV files structure
LATEST_NODES_FILE = DATA_DIR / 'tor_nodes_latest.csv'  # Direct rip from GitHub
OLD_NODES_FILE = DATA_DIR / 'tor_nodes_old.csv'      # Previous version of latest
DEAD_NODES_FILE = DATA_DIR / 'OLD_NODES.csv'         # Archive of removed nodes (append only)
NEW_NODES_FILE = DATA_DIR / 'NEW_NODES.csv'          # New nodes found (overwrite each time)

def load_config():
    """Load plugin configuration"""
    default_config = {
        'enabled': True,
        'github_url': 'https://raw.githubusercontent.com/PeeBee66/Updated_TOR_Nodes/main/tor_nodes_latest.csv',
        'verify_ssl': False,
        'opencti_url': 'http://localhost:8080',
        'opencti_token': '',
        'auto_ingest': True
    }

    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
            # Merge with defaults
            for key, value in default_config.items():
                if key not in config:
                    config[key] = value
            return config
    else:
        save_config(default_config)
        return default_config

def save_config(config):
    """Save plugin configuration"""
    CONFIG_FILE.parent.mkdir(exist_ok=True)
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

def fetch_tor_nodes():
    """Fetch TOR nodes CSV from GitHub and implement 4-file comparison system"""
    config = load_config()

    try:
        logger.info(f"Fetching TOR nodes from: {config['github_url']}")

        # Prepare SSL context
        verify = config.get('verify_ssl', True)

        response = requests.get(
            config['github_url'],
            verify=verify,
            timeout=30,
            headers={'User-Agent': 'OpenCTI-Injester/1.0'}
        )
        response.raise_for_status()

        # Create data directory
        DATA_DIR.mkdir(exist_ok=True)

        # Step 1: If tor_nodes_latest.csv exists, rename it to tor_nodes_old.csv
        if LATEST_NODES_FILE.exists():
            logger.info("Moving current latest CSV to old CSV")
            # Remove old file if it exists
            if OLD_NODES_FILE.exists():
                OLD_NODES_FILE.unlink()
            # Rename latest to old
            LATEST_NODES_FILE.rename(OLD_NODES_FILE)

        # Step 2: Save new data as tor_nodes_latest.csv
        csv_data = response.text
        df_latest = pd.read_csv(StringIO(csv_data))
        df_latest.to_csv(LATEST_NODES_FILE, index=False)
        logger.info(f"Saved new data with {len(df_latest)} nodes to latest CSV")

        # Step 3: Compare latest with old to find changes
        new_nodes = []
        removed_nodes = []

        if OLD_NODES_FILE.exists():
            df_old = pd.read_csv(OLD_NODES_FILE)
            logger.info(f"Comparing with old data ({len(df_old)} nodes)")

            # Compare using IP addresses
            if 'IP' in df_latest.columns and 'IP' in df_old.columns:
                current_ips = set(df_latest['IP'].dropna().astype(str))
                previous_ips = set(df_old['IP'].dropna().astype(str))

                new_ips = current_ips - previous_ips
                removed_ips = previous_ips - current_ips

                logger.info(f"Found {len(new_ips)} new nodes, {len(removed_ips)} removed nodes")

                # Step 4: Process removed nodes - add to OLD_NODES.csv (append only)
                if removed_ips:
                    removed_data = df_old[df_old['IP'].astype(str).isin(removed_ips)].copy()
                    removed_data['removed_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    removed_data['removed_timestamp'] = datetime.now().isoformat()

                    # Append to dead nodes file (never overwrite)
                    if DEAD_NODES_FILE.exists():
                        removed_data.to_csv(DEAD_NODES_FILE, mode='a', header=False, index=False)
                    else:
                        removed_data.to_csv(DEAD_NODES_FILE, index=False)

                    for ip in removed_ips:
                        removed_nodes.append({
                            'ip': ip,
                            'timestamp': datetime.now().isoformat()
                        })

                # Step 5: Process new nodes - save to NEW_NODES.csv (overwrite each time)
                if new_ips:
                    new_data = df_latest[df_latest['IP'].astype(str).isin(new_ips)].copy()
                    new_data['detected_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    new_data['detected_timestamp'] = datetime.now().isoformat()
                    new_data['status'] = 'NEW (Since last fetch)'

                    # Save new nodes (overwrite each time)
                    new_data.to_csv(NEW_NODES_FILE, index=False)

                    for ip in new_ips:
                        # Get node details for the new IP
                        node_row = df_latest[df_latest['IP'].astype(str) == ip]
                        if len(node_row) > 0:
                            node_row = node_row.iloc[0]
                            new_nodes.append({
                                'ip': ip,
                                'name': node_row.get('Name', ''),
                                'is_exit': node_row.get('IsExit', '') == 'ExitNode',
                                'timestamp': datetime.now().isoformat(),
                                'status': 'NEW (Since last fetch)'
                            })
                else:
                    # No new nodes found - preserve existing NEW_NODES.csv to keep last batch of new IPs
                    logger.info("No new nodes detected - preserving existing NEW_NODES.csv")
                    if not NEW_NODES_FILE.exists():
                        # Create empty file only if it doesn't exist
                        empty_df = pd.DataFrame(columns=df_latest.columns.tolist() + ['detected_date', 'detected_timestamp', 'status'])
                        empty_df.to_csv(NEW_NODES_FILE, index=False)

        else:
            # First run - all nodes are "new"
            logger.info("First run - all nodes considered new")
            df_latest_new = df_latest.copy()
            df_latest_new['detected_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            df_latest_new['detected_timestamp'] = datetime.now().isoformat()
            df_latest_new['status'] = 'NEW (Since last fetch)'
            df_latest_new.to_csv(NEW_NODES_FILE, index=False)

            # Create empty dead nodes file
            empty_df = pd.DataFrame(columns=df_latest.columns.tolist() + ['removed_date', 'removed_timestamp'])
            empty_df.to_csv(DEAD_NODES_FILE, index=False)

        # Auto-ingest new nodes to OpenCTI immediately after detection
        if new_nodes:
            logger.info(f"Auto-ingesting {len(new_nodes)} new TOR nodes to OpenCTI")
            ingest_result = ingest_new_nodes_to_opencti()
            logger.info(f"Auto-ingestion result: {ingest_result}")

        return {
            'success': True,
            'total_nodes': len(df_latest),
            'new_nodes': new_nodes,
            'removed_nodes': removed_nodes,
            'timestamp': datetime.now().isoformat(),
            'new_count': len(new_nodes),
            'removed_count': len(removed_nodes)
        }

    except Exception as e:
        logger.error(f"Error fetching TOR nodes: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

def create_stix_bundle(nodes_df):
    """Create STIX bundle for TOR nodes optimized for OpenCTI"""
    import uuid

    stix_objects = []

    # Use consistent UUID for identity to avoid duplicates
    identity_uuid = "47a40fd9-02da-44cc-be3a-d0fb2bf18f74"
    identity_obj = {
        "type": "identity",
        "spec_version": "2.1",
        "id": f"identity--{identity_uuid}",
        "created": "2025-01-01T00:00:00.000Z",
        "modified": "2025-01-01T00:00:00.000Z",
        "name": "TOR Network Monitor",
        "identity_class": "organization",
        "description": "Automated TOR network monitoring system",
        "object_marking_refs": ["marking-definition--613f2e26-407d-48c7-9eca-b8e91df99dc9"]
    }
    stix_objects.append(identity_obj)

    for _, row in nodes_df.iterrows():
        if pd.notna(row.get('IP')):
            ip_address = str(row['IP']).strip()
            is_exit_str = str(row.get('IsExit', '')).strip().lower()
            is_exit = is_exit_str in ['yes', 'true', 'exitnode']

            # Handle NaN and None values properly
            node_name = str(row.get('Name', '')).strip() if pd.notna(row.get('Name')) else ''
            flags = str(row.get('Flags', '')).strip() if pd.notna(row.get('Flags')) else ''
            version = str(row.get('Version', '')).strip() if pd.notna(row.get('Version')) else ''
            collection_date = str(row.get('CollectionDate', '')).strip() if pd.notna(row.get('CollectionDate')) else ''

            # Convert collection date to proper ISO format
            if collection_date and '/' in collection_date:
                try:
                    # Convert from MM/DD/YYYY to YYYY-MM-DD
                    parts = collection_date.split('/')
                    if len(parts) == 3:
                        # Handle 2-digit or 4-digit years properly
                        year = parts[2]
                        if len(year) == 2:
                            year = f"20{year}"
                        elif len(year) == 4:
                            year = parts[2]
                        collection_date = f"{year}-{parts[0].zfill(2)}-{parts[1].zfill(2)}"
                except:
                    collection_date = datetime.now().strftime('%Y-%m-%d')

            if not collection_date:
                collection_date = datetime.now().strftime('%Y-%m-%d')

            # Generate deterministic UUIDs based on IP for consistency
            infrastructure_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"tor-infrastructure-{ip_address}"))
            ip_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"ipv4-{ip_address}"))
            relationship_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"tor-rel-{ip_address}"))

            # Create IPv4 address object (observables first)
            ip_obj = {
                "type": "ipv4-addr",
                "spec_version": "2.1",
                "id": f"ipv4-addr--{ip_uuid}",
                "value": ip_address,
                "object_marking_refs": ["marking-definition--613f2e26-407d-48c7-9eca-b8e91df99dc9"]
            }
            stix_objects.append(ip_obj)

            # Create Infrastructure object for TOR relay
            infrastructure_obj = {
                "type": "infrastructure",
                "spec_version": "2.1",
                "id": f"infrastructure--{infrastructure_uuid}",
                "created": f"{collection_date}T00:00:00.000Z",
                "modified": f"{collection_date}T00:00:00.000Z",
                "name": f"{node_name} Tor Relay" if node_name else f"Tor Relay {ip_address}",
                "infrastructure_types": ["anonymization"],
                "description": f"Tor {'exit ' if is_exit else ''}relay node {node_name if node_name else ip_address} observed in the Tor network. Version: {version}. Flags: {flags}.",
                "labels": ["tor", "relay", "exit" if is_exit else "non-exit"],
                "first_seen": f"{collection_date}T00:00:00.000Z",
                "last_seen": f"{collection_date}T00:00:00.000Z",
                "object_marking_refs": ["marking-definition--613f2e26-407d-48c7-9eca-b8e91df99dc9"],
                "created_by_ref": f"identity--{identity_uuid}",
                "external_references": [
                    {
                        "source_name": "tor-metrics",
                        "description": "Tor network status data",
                        "url": "https://metrics.torproject.org/"
                    }
                ]
            }
            stix_objects.append(infrastructure_obj)

            # Create relationship: infrastructure "consists-of" ip
            relationship_obj = {
                "type": "relationship",
                "spec_version": "2.1",
                "id": f"relationship--{relationship_uuid}",
                "created": f"{collection_date}T00:00:00.000Z",
                "modified": f"{collection_date}T00:00:00.000Z",
                "relationship_type": "consists-of",
                "source_ref": f"infrastructure--{infrastructure_uuid}",
                "target_ref": f"ipv4-addr--{ip_uuid}",
                "description": f"Tor relay infrastructure consists of IP address {ip_address}",
                "object_marking_refs": ["marking-definition--613f2e26-407d-48c7-9eca-b8e91df99dc9"],
                "created_by_ref": f"identity--{identity_uuid}"
            }
            stix_objects.append(relationship_obj)

    return {
        "type": "bundle",
        "id": f"bundle--{str(uuid.uuid4())}",
        "spec_version": "2.1",
        "objects": stix_objects
    }

def ingest_new_nodes_to_opencti():
    """Auto-ingest only new TOR nodes (NEW_NODES.csv) to OpenCTI - process individually"""
    config = load_config()

    if not config.get('auto_ingest'):
        logger.info("Auto-ingest disabled")
        return {'success': False, 'message': 'Auto-ingest disabled'}

    try:
        # Check if NEW_NODES.csv exists and has data
        if not NEW_NODES_FILE.exists():
            logger.info("No new nodes to ingest")
            return {'success': True, 'message': 'No new nodes to ingest', 'ingested': 0}

        df = pd.read_csv(NEW_NODES_FILE)

        if df.empty:
            logger.info("NEW_NODES.csv is empty")
            return {'success': True, 'message': 'No new nodes to ingest', 'ingested': 0}

        # Clean up NaN values and convert to strings to avoid JSON serialization issues
        df = df.fillna('')

        logger.info(f"Auto-ingesting {len(df)} new TOR nodes to OpenCTI")

        # Process each new node individually
        successful_ingests = 0
        failed_ingests = 0

        for index, row in df.iterrows():
            try:
                # Skip rows without valid IP
                if not pd.notna(row.get('IP')) or str(row.get('IP')).strip() == '':
                    continue

                # Create a single-row dataframe for this node
                single_node_df = pd.DataFrame([row])

                # Create STIX bundle for this single node
                bundle = create_stix_bundle(single_node_df)

                # Send this single node to OpenCTI
                result = send_bundle_to_opencti(bundle, config)

                if result['success']:
                    successful_ingests += 1
                else:
                    failed_ingests += 1
                    logger.debug(f"Failed to auto-ingest node {row.get('IP')}: {result.get('error')}")

            except Exception as e:
                failed_ingests += 1
                logger.debug(f"Error auto-ingesting node {row.get('IP')}: {str(e)}")

        logger.info(f"Auto-ingestion complete: {successful_ingests} successful, {failed_ingests} failed")

        return {
            'success': successful_ingests > 0,
            'ingested': successful_ingests,
            'failed': failed_ingests,
            'total': len(df),
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error ingesting new nodes to OpenCTI: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

def ingest_to_opencti(only_new=False):
    """Manual ingest of TOR nodes to OpenCTI - process each line individually"""
    config = load_config()

    try:
        # Use the latest TOR nodes CSV file
        if not LATEST_NODES_FILE.exists():
            return {'success': False, 'error': 'No TOR nodes data available. Please fetch TOR nodes first.'}

        df = pd.read_csv(LATEST_NODES_FILE)

        if df.empty:
            return {'success': False, 'error': 'TOR nodes data is empty'}

        # Clean up NaN values and convert to strings to avoid JSON serialization issues
        df = df.fillna('')

        logger.info(f"Manual ingest: Processing {len(df)} TOR nodes from tor_nodes_latest.csv")

        # Process each node individually
        successful_ingests = 0
        failed_ingests = 0
        errors = []

        for index, row in df.iterrows():
            try:
                # Skip rows without valid IP
                if not pd.notna(row.get('IP')) or str(row.get('IP')).strip() == '':
                    continue

                # Create a single-row dataframe for this node
                single_node_df = pd.DataFrame([row])

                # Create STIX bundle for this single node
                bundle = create_stix_bundle(single_node_df)

                # Send this single node to OpenCTI
                result = send_bundle_to_opencti(bundle, config)

                if result['success']:
                    successful_ingests += 1
                    if successful_ingests % 100 == 0:
                        logger.info(f"Progress: {successful_ingests}/{len(df)} nodes ingested")
                else:
                    failed_ingests += 1
                    errors.append(f"Node {row.get('IP')}: {result.get('error', 'Unknown error')}")

                # Add a small delay to avoid overwhelming the API
                if index % 10 == 0:
                    import time
                    time.sleep(0.1)

            except Exception as e:
                failed_ingests += 1
                errors.append(f"Node {row.get('IP')}: {str(e)}")
                logger.debug(f"Failed to ingest node {row.get('IP')}: {str(e)}")

        logger.info(f"Ingestion complete: {successful_ingests} successful, {failed_ingests} failed")

        return {
            'success': successful_ingests > 0,
            'ingested': successful_ingests,
            'failed': failed_ingests,
            'total': len(df),
            'errors': errors[:10] if errors else [],  # Return first 10 errors
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error in manual ingestion to OpenCTI: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

def send_bundle_to_opencti(bundle, config):
    """Send individual objects to OpenCTI using native GraphQL API"""
    import json as json_module

    try:
        opencti_url = config.get('opencti_url', 'http://localhost:8080')
        opencti_token = config.get('opencti_token', '')

        if not opencti_token:
            logger.warning("OpenCTI token not configured")
            return {'success': False, 'error': 'OpenCTI token not configured'}

        # Extract objects from bundle
        objects = bundle.get('objects', [])

        # Find the infrastructure and IP objects
        infrastructure_obj = next((obj for obj in objects if obj['type'] == 'infrastructure'), None)
        ip_obj = next((obj for obj in objects if obj['type'] == 'ipv4-addr'), None)

        if not infrastructure_obj or not ip_obj:
            return {'success': False, 'error': 'Missing required objects in bundle'}

        headers = {
            'Authorization': f'Bearer {opencti_token}',
            'Content-Type': 'application/json'
        }

        # Use the TOR Network Monitor internal ID for author attribution
        identity_id = "a1e2e96c-242a-4ce9-a374-2593b62f0206"  # TOR Network Monitor internal ID

        # Step 1: Create IPv4 address first
        ip_mutation = """
        mutation CreateIPv4($type: String!, $IPv4Addr: IPv4AddrAddInput!) {
            stixCyberObservableAdd(type: $type, IPv4Addr: $IPv4Addr) {
                id
                observable_value
            }
        }
        """

        ip_variables = {
            "type": "IPv4-Addr",
            "IPv4Addr": {
                "value": ip_obj['value']
            },
            "createdBy": identity_id
        }

        ip_response = requests.post(
            f"{opencti_url}/graphql",
            headers=headers,
            json={
                'query': ip_mutation,
                'variables': ip_variables
            },
            verify=config.get('verify_ssl', False),
            timeout=30
        )

        if ip_response.status_code != 200:
            logger.error(f"Failed to create IP address: HTTP {ip_response.status_code}: {ip_response.text}")
            return {'success': False, 'error': f"IP creation failed: HTTP {ip_response.status_code}"}

        ip_result = ip_response.json()
        if 'errors' in ip_result:
            logger.error(f"GraphQL errors creating IP: {ip_result['errors']}")
            return {'success': False, 'error': f"IP creation GraphQL errors: {ip_result['errors']}"}

        if not ip_result.get('data', {}).get('stixCyberObservableAdd'):
            logger.error(f"No IP address created: {ip_result}")
            return {'success': False, 'error': f"No IP address created: {ip_result}"}

        ip_id = ip_result['data']['stixCyberObservableAdd']['id']
        logger.info(f"Created IPv4 address: {ip_obj['value']} with ID {ip_id}")

        # Step 2: Create infrastructure
        infra_mutation = """
        mutation CreateInfrastructure($input: StixDomainObjectAddInput!) {
            stixDomainObjectAdd(input: $input) {
                id
                standard_id
            }
        }
        """

        infra_input = {
            "type": "Infrastructure",
            "stix_id": infrastructure_obj['id'],
            "name": infrastructure_obj['name'],
            "description": infrastructure_obj['description'],
            "objectMarking": ["marking-definition--613f2e26-407d-48c7-9eca-b8e91df99dc9"],
            "created": infrastructure_obj['created'],
            "modified": infrastructure_obj['modified'],
            "createdBy": identity_id
        }

        # Add x_opencti_labels if present
        if 'x_opencti_labels' in infrastructure_obj:
            infra_input['labels'] = infrastructure_obj['x_opencti_labels']

        infra_response = requests.post(
            f"{opencti_url}/graphql",
            headers=headers,
            json={
                'query': infra_mutation,
                'variables': {'input': infra_input}
            },
            verify=config.get('verify_ssl', False),
            timeout=30
        )

        if infra_response.status_code != 200:
            logger.error(f"Failed to create infrastructure: HTTP {infra_response.status_code}: {infra_response.text}")
            return {'success': False, 'error': f"Infrastructure creation failed: HTTP {infra_response.status_code}"}

        infra_result = infra_response.json()
        if 'errors' in infra_result:
            logger.error(f"GraphQL errors creating infrastructure: {infra_result['errors']}")
            return {'success': False, 'error': f"Infrastructure creation GraphQL errors: {infra_result['errors']}"}

        if not infra_result.get('data', {}).get('stixDomainObjectAdd'):
            logger.error(f"No infrastructure created: {infra_result}")
            return {'success': False, 'error': f"No infrastructure created: {infra_result}"}

        infra_id = infra_result['data']['stixDomainObjectAdd']['id']
        logger.info(f"Created infrastructure: {infrastructure_obj['name']} with ID {infra_id}")

        # Step 3: Create relationship between infrastructure and IP
        rel_mutation = """
        mutation CreateRelationship($input: StixCoreRelationshipAddInput!) {
            stixCoreRelationshipAdd(input: $input) {
                id
                relationship_type
            }
        }
        """

        rel_input = {
            "relationship_type": "consists-of",
            "fromId": infra_id,
            "toId": ip_id,
            "objectMarking": ["marking-definition--613f2e26-407d-48c7-9eca-b8e91df99dc9"],
            "createdBy": identity_id
        }

        rel_response = requests.post(
            f"{opencti_url}/graphql",
            headers=headers,
            json={
                'query': rel_mutation,
                'variables': {'input': rel_input}
            },
            verify=config.get('verify_ssl', False),
            timeout=30
        )

        if rel_response.status_code != 200:
            logger.warning(f"Failed to create relationship: HTTP {rel_response.status_code}: {rel_response.text}")
        else:
            rel_result = rel_response.json()
            if 'errors' in rel_result:
                logger.warning(f"GraphQL errors creating relationship: {rel_result['errors']}")
            elif rel_result.get('data', {}).get('stixCoreRelationshipAdd'):
                rel_id = rel_result['data']['stixCoreRelationshipAdd']['id']
                logger.info(f"Created relationship between infrastructure and IP with ID {rel_id}")

        return {
            'success': True,
            'infrastructure_id': infra_id,
            'ip_id': ip_id,
            'timestamp': datetime.now().isoformat(),
            'method': 'Native GraphQL API'
        }

    except Exception as e:
        logger.error(f"Error sending bundle to OpenCTI: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

def initialize_scheduler(scheduler):
    """Initialize scheduled tasks for the plugin"""
    config = load_config()

    if not config.get('enabled'):
        logger.info("TOR plugin is disabled")
        return

    # Schedule daily fetch and auto-ingest at 10:00 AM
    scheduler.add_job(
        func=fetch_tor_nodes,
        trigger='cron',
        hour=10,
        minute=0,
        id='tor_fetch_daily',
        name='TOR Daily Fetch & Ingest',
        replace_existing=True
    )

    logger.info("TOR plugin scheduler initialized - fetch and auto-ingest at 10:00 daily")

def create_blueprint():
    """Create Flask blueprint for the plugin"""
    bp = Blueprint('tor', __name__)

    @bp.route('/')
    def index():
        """Main plugin page with new/dead/all nodes tabs"""
        config = load_config()

        # Get search and pagination parameters
        page = int(request.args.get('page', 1))
        per_page = 200
        search_query = request.args.get('search', '').strip()
        current_tab = request.args.get('tab', 'all-nodes')

        # Load statistics
        total_nodes = 0
        new_nodes_count = 0
        dead_nodes_count = 0
        exit_nodes_count = 0

        # Load all nodes data
        all_nodes = []
        new_nodes = []
        dead_nodes = []

        # Pagination variables
        total_pages = 1
        total_records = 0

        # Helper function to apply search filter to a dataframe
        def apply_search_filter(df, search_query):
            if not search_query:
                return df
            mask = (
                df['IP'].astype(str).str.contains(search_query, case=False, na=False) |
                df['Name'].astype(str).str.contains(search_query, case=False, na=False) |
                df['Version'].astype(str).str.contains(search_query, case=False, na=False) |
                df['Flags'].astype(str).str.contains(search_query, case=False, na=False)
            )
            return df[mask]

        # Load all datasets first
        df_latest = None
        df_new = None
        df_dead = None

        if LATEST_NODES_FILE.exists():
            df_latest = pd.read_csv(LATEST_NODES_FILE)
            total_nodes = len(df_latest)
            exit_nodes_count = len(df_latest[df_latest['IsExit'] == 'ExitNode'])

        if NEW_NODES_FILE.exists():
            df_new = pd.read_csv(NEW_NODES_FILE)
            new_nodes_count = len(df_new)

        if DEAD_NODES_FILE.exists():
            df_dead = pd.read_csv(DEAD_NODES_FILE)
            dead_nodes_count = len(df_dead)

        # Always load all datasets for template (needed for tab display)
        if df_new is not None:
            new_nodes = df_new.to_dict('records')
        if df_dead is not None:
            dead_nodes = df_dead.to_dict('records')
        if df_latest is not None:
            all_nodes = df_latest.to_dict('records')

        # Apply search and pagination only to the current active tab
        if current_tab == 'all-nodes' and df_latest is not None:
            df_filtered = apply_search_filter(df_latest, search_query)
            total_records = len(df_filtered)
            total_pages = (total_records + per_page - 1) // per_page if total_records > 0 else 1
            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page
            all_nodes = df_filtered.iloc[start_idx:end_idx].to_dict('records')
        elif current_tab == 'new-nodes' and df_new is not None:
            df_filtered = apply_search_filter(df_new, search_query)
            total_records = len(df_filtered)
            total_pages = (total_records + per_page - 1) // per_page if total_records > 0 else 1
            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page
            new_nodes = df_filtered.iloc[start_idx:end_idx].to_dict('records')
        elif current_tab == 'dead-nodes' and df_dead is not None:
            df_filtered = apply_search_filter(df_dead, search_query)
            total_records = len(df_filtered)
            total_pages = (total_records + per_page - 1) // per_page if total_records > 0 else 1
            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page
            dead_nodes = df_filtered.iloc[start_idx:end_idx].to_dict('records')

        # Get last updated time
        last_updated = None
        if LATEST_NODES_FILE.exists():
            import datetime
            timestamp = LATEST_NODES_FILE.stat().st_mtime
            last_updated = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

        # Prepare stats for template
        stats = {
            'total_nodes': total_nodes,
            'new_nodes': new_nodes_count,
            'dead_nodes': dead_nodes_count,
            'exit_nodes': exit_nodes_count
        }



        # Load template from file
        template_path = Path(__file__).parent / 'templates' / 'tor' / 'index.html'
        with open(template_path, 'r') as f:
            template = f.read()

        return render_template_string(template,
                                    config=config,
                                    stats=stats,
                                    all_nodes=all_nodes,
                                    new_nodes=new_nodes,
                                    dead_nodes=dead_nodes,
                                    last_updated=last_updated,
                                    search_query=search_query,
                                    current_tab=current_tab,
                                    page=page,
                                    total_pages=total_pages,
                                    total_records=total_records)

    @bp.route('/fetch', methods=['POST'])
    def fetch():
        """Manually trigger fetch"""
        result = fetch_tor_nodes()
        return jsonify(result)

    @bp.route('/fetch_nodes', methods=['POST'])
    def fetch_nodes_api():
        """API route for template to trigger fetch"""
        result = fetch_tor_nodes()
        return jsonify(result)

    @bp.route('/ingest', methods=['POST'])
    def ingest():
        """Manually trigger OpenCTI ingestion"""
        result = ingest_to_opencti()
        return jsonify(result)

    @bp.route('/ingest_to_opencti', methods=['POST'])
    def ingest_to_opencti_api():
        """API route for template to trigger ingestion"""
        result = ingest_to_opencti()
        return jsonify(result)

    @bp.route('/new-nodes')
    def new_nodes():
        """Get new nodes since last fetch"""
        if NEW_NODES_FILE.exists():
            df = pd.read_csv(NEW_NODES_FILE)
            return jsonify({'nodes': df.to_dict('records')})
        return jsonify({'nodes': []})

    @bp.route('/old-nodes')
    def old_nodes():
        """Get archived (dead) nodes"""
        if DEAD_NODES_FILE.exists():
            df = pd.read_csv(DEAD_NODES_FILE)
            return jsonify({'nodes': df.tail(100).to_dict('records')})
        return jsonify({'nodes': []})

    @bp.route('/settings', methods=['GET', 'POST'])
    def settings():
        """Get or update settings"""
        if request.method == 'POST':
            new_config = request.json
            current_config = load_config()
            current_config.update(new_config)
            save_config(current_config)
            return jsonify({'success': True})
        else:
            return jsonify(load_config())

    return bp