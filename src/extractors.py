import logging
import requests
import pandas as pd
from sodapy import Socrata

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def fetch_socrata_permits(domain: str, dataset_id: str, app_token: str = None, limit: int = 5000) -> pd.DataFrame:
    """Fetches permit records from a Socrata Open Data endpoint."""
    logging.info(f"Fetching {limit} records from Socrata: {domain}/{dataset_id}")
    try:
        client = Socrata(domain, app_token)
        results = client.get(dataset_id, limit=limit)
        return pd.DataFrame.from_records(results)
    except Exception as e:
        logging.error(f"Error fetching Socrata data ({domain}/{dataset_id}): {e}")
        return pd.DataFrame()

def fetch_arcgis_permits(endpoint_url: str, limit: int = 5000) -> pd.DataFrame:
    """Fetches permit records from an ArcGIS REST FeatureServer query endpoint."""
    logging.info(f"Fetching {limit} records from ArcGIS Endpoint: {endpoint_url}")
    params = {
        'where': '1=1',
        'outFields': '*',
        'f': 'json',
        'resultRecordCount': limit,
        'returnGeometry': 'false'
    }
    try:
        response = requests.get(endpoint_url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if 'features' in data and len(data['features']) > 0:
            records = [feature['attributes'] for feature in data['features']]
            return pd.DataFrame(records)
        else:
            logging.warning(f"No records returned from ArcGIS endpoint: {endpoint_url}")
            return pd.DataFrame()
    except Exception as e:
        logging.error(f"Error fetching ArcGIS data ({endpoint_url}): {e}")
        return pd.DataFrame()
