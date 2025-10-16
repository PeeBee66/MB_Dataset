#!/usr/bin/env python3
"""
Query specific entities by ID from the import result
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

# Query for specific malware by ID
malware_by_id_query = """
query ($id: String!) {
  malware(id: $id) {
    id
    name
    malware_types
    created
    modified
    createdBy {
      ... on Identity {
        id
        name
      }
    }
  }
}
"""

# Query for specific identity by ID
identity_by_id_query = """
query ($id: String!) {
  identity(id: $id) {
    id
    name
    identity_class
    created
    modified
  }
}
"""

# Query for specific relationship by ID
relationship_by_id_query = """
query ($id: String!) {
  stixCoreRelationship(id: $id) {
    id
    relationship_type
    created
    modified
    from {
      ... on BasicObject {
        id
        entity_type
      }
    }
    to {
      ... on BasicObject {
        id
        entity_type
      }
    }
  }
}
"""

def run_query(query, variables, name):
    """Run a GraphQL query with variables"""
    print(f"\n{'='*60}")
    print(f"Querying: {name}")
    print(f"Variables: {variables}")
    print('='*60)

    try:
        response = requests.post(
            f"{OPENCTI_URL}/graphql",
            headers=headers,
            json={"query": query, "variables": variables},
            verify=False
        )

        if response.status_code == 200:
            data = response.json()

            if 'errors' in data:
                print(f"GraphQL Errors: {json.dumps(data['errors'], indent=2)}")
                return None

            print(f"Result: {json.dumps(data['data'], indent=2)}")
            return data['data']
        else:
            print(f"HTTP Error: {response.status_code}")
            return None
    except Exception as e:
        print(f"Exception: {e}")
        return None

# Test with the IDs from the import result
print("Testing entity queries with IDs from import result")

# Test malware
run_query(
    malware_by_id_query,
    {"id": "malware--09f18c9d-890d-fa8a-b258-2263bb18d1ef"},
    "Malware by ID"
)

# Test identity
run_query(
    identity_by_id_query,
    {"id": "identity--42796d2f-d41e-b122-441e-45d34529c0e8"},
    "Identity by ID"
)

# Test relationship
run_query(
    relationship_by_id_query,
    {"id": "relationship--9626d865-18d7-4100-81c6-bb117a487e87"},
    "Relationship by ID"
)
