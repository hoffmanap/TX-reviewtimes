import logging
import requests
import pandas as pd
from sodapy import Socrata

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*'
}

def fetch_socrata_permits(domain: str, dataset_id: str, app_token: str = None, limit: int = 5000) -> pd.DataFrame:
    """Fetches permit records from Socrata endpoints."""
    logging.info(f"Fetching {limit} records from Socrata: {domain}/{dataset_id}")
    try:
        if not app_token or str(app_token).strip() == "" or "SOCRATA" in str(app_token):
            app_token = None
            
        client = Socrata(domain, app_token=app_token, timeout=30)
        results = client.get(dataset_id, limit=limit)
        return pd.DataFrame.from_records(results)
    except Exception as e:
        logging.error(f"Error fetching Socrata data ({domain}/{dataset_id}): {e}")
        return pd.DataFrame()

def fetch_arcgis_permits(endpoint_url: str, limit: int = 5000) -> pd.DataFrame:
    """Fetches permit records from ArcGIS FeatureServer query endpoints with robust spatial params."""
    logging.info(f"Fetching {limit} records from ArcGIS Endpoint: {endpoint_url}")
    params = {
        'where': '1=1',
        'outFields': '*',
        'outSR': '4326',
        'f': 'json',
        'resultRecordCount': limit,
        'returnGeometry': 'false'
    }
    try:
        response = requests.get(endpoint_url, params=params, headers=DEFAULT_HEADERS, timeout=30)
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
