#!/usr/bin/env python3
"""
Verify OpenCTI ingestion by querying the GraphQL API
"""
import requests
import json
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

OPENCTI_URL = "https://172.21.32.183:4000"
OPENCTI_TOKEN = "350f38d0-44fe-47d2-b2a8-62acf3003ede"

headers = {
    "Authorization": f"Bearer {OPENCTI_TOKEN}",
    "Content-Type": "application/json"
}

# Query for malware entities
malware_query = """
query {
  malwares(first: 50) {
    edges {
      node {
        id
        name
        malware_types
        created
        createdBy {
          ... on Identity {
            name
          }
        }
      }
    }
  }
}
"""

# Query for relationships
relationships_query = """
query {
  stixCoreRelationships(first: 50, orderBy: created_at, orderMode: desc) {
    edges {
      node {
        id
        relationship_type
        created
        from {
          ... on StixDomainObject {
            id
            entity_type
          }
        }
        to {
          ... on StixDomainObject {
            id
            entity_type
          }
          ... on StixCyberObservable {
            id
            entity_type
          }
        }
      }
    }
  }
}
"""

# Query for identities
identities_query = """
query {
  identities(first: 50) {
    edges {
      node {
        id
        name
        identity_class
        created
      }
    }
  }
}
"""

# Query for file observables
files_query = """
query {
  stixCyberObservables(first: 50, types: ["StixFile"]) {
    edges {
      node {
        id
        observable_value
        ... on StixFile {
          hashes {
            algorithm
            hash
          }
        }
      }
    }
  }
}
"""

def run_query(query, name):
    """Run a GraphQL query and return results"""
    print(f"\n{'='*60}")
    print(f"Querying: {name}")
    print('='*60)

    try:
        response = requests.post(
            f"{OPENCTI_URL}/graphql",
            headers=headers,
            json={"query": query},
            verify=False
        )

        if response.status_code == 200:
            data = response.json()

            if 'errors' in data:
                print(f"GraphQL Errors: {json.dumps(data['errors'], indent=2)}")
                return None

            return data['data']
        else:
            print(f"HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"Exception: {e}")
        return None

def main():
    print("OpenCTI Ingestion Verification")
    print("="*60)

    # Check malware entities
    malware_data = run_query(malware_query, "Malware Entities")
    if malware_data and 'malwares' in malware_data:
        malwares = malware_data['malwares']['edges']
        print(f"\nFound {len(malwares)} malware entities:")
        for edge in malwares:
            node = edge['node']
            creator = node.get('createdBy', {})
            creator_name = creator.get('name', 'Unknown') if creator else 'None'
            print(f"  - {node['name']} ({', '.join(node.get('malware_types', []))})")
            print(f"    ID: {node['id']}")
            print(f"    Created by: {creator_name}")
            print(f"    Created: {node.get('created', 'N/A')}")

    # Check relationships
    rel_data = run_query(relationships_query, "Relationships")
    if rel_data and 'stixCoreRelationships' in rel_data:
        relationships = rel_data['stixCoreRelationships']['edges']
        print(f"\nFound {len(relationships)} relationships:")
        for edge in relationships[:10]:  # Show first 10
            node = edge['node']
            from_type = node['from'].get('entity_type', 'Unknown') if node.get('from') else 'Unknown'
            to_type = node['to'].get('entity_type', 'Unknown') if node.get('to') else 'Unknown'
            print(f"  - {from_type} -> {node['relationship_type']} -> {to_type}")
            print(f"    ID: {node['id']}")

    # Check identities
    id_data = run_query(identities_query, "Identities")
    if id_data and 'identities' in id_data:
        identities = id_data['identities']['edges']
        print(f"\nFound {len(identities)} identities:")
        for edge in identities:
            node = edge['node']
            print(f"  - {node['name']} ({node.get('identity_class', 'N/A')})")
            print(f"    ID: {node['id']}")

    # Check file observables
    files_data = run_query(files_query, "File Observables")
    if files_data and 'stixCyberObservables' in files_data:
        files = files_data['stixCyberObservables']['edges']
        print(f"\nFound {len(files)} file observables:")
        for edge in files[:3]:  # Show first 3
            node = edge['node']
            hashes = node.get('hashes', [])
            print(f"  - {node.get('observable_value', 'N/A')}")
            print(f"    ID: {node['id']}")
            print(f"    Hash count: {len(hashes)}")
            if hashes:
                for h in hashes:
                    print(f"      {h['algorithm']}: {h['hash'][:16]}...")

if __name__ == "__main__":
    main()
