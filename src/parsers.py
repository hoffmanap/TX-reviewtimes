import pandas as pd
import logging
from src.extractors import fetch_socrata_permits, fetch_arcgis_permits

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def parse_austin(app_token=None) -> pd.DataFrame:
    """Austin - Socrata (Dataset: 3syk-w9eu / 3syk-wavh)"""
    df = fetch_socrata_permits("data.austintexas.gov", "3syk-w9eu", app_token=app_token, limit=5000)
    if df.empty:
        df = fetch_socrata_permits("data.austintexas.gov", "3syk-wavh", app_token=app_token, limit=5000)
    
    if df.empty:
        logging.warning("Austin fetch returned empty dataset.")
        return pd.DataFrame()

    normalized = pd.DataFrame()
    normalized['city'] = ['Austin'] * len(df)

    # Dynamic column mapping to handle API field variations
    app_col = next((col for col in ['applied_date', 'application_date', 'issue_date'] if col in df.columns), None)
    issue_col = next((col for col in ['issue_date', 'issued_date'] if col in df.columns), None)

    if not app_col or not issue_col:
        logging.warning("Austin missing required date columns.")
        return pd.DataFrame()

    normalized['app_date'] = pd.to_datetime(df[app_col], errors='coerce')
    normalized['issue_date'] = pd.to_datetime(df[issue_col], errors='coerce')

    def classify_type(row):
        work_desc = str(row.get('work_description', row.get('description', ''))).lower()
        permit_type = str(row.get('permit_type_desc', row.get('permit_type', ''))).lower()
        if any(term in work_desc or term in permit_type for term in ['multi', 'apartment', 'condo']):
            return 'Multifamily'
        elif any(term in work_desc or term in permit_type for term in ['single family', 'duplex', 'triplex', 'townhome', 'residential']):
            return 'Single Family'
        return 'Other'

    def classify_scope(row):
        work_class = str(row.get('work_class', row.get('work_type', ''))).lower()
        if 'new' in work_class:
            return 'New Construction'
        elif any(term in work_class for term in ['remodel', 'alteration', 'addition', 'repair']):
            return 'Alteration/Renovation'
        return 'Other'

    normalized['project_type'] = df.apply(classify_type, axis=1)
    normalized['work_scope'] = df.apply(classify_scope, axis=1)
    return normalized


def parse_dallas(app_token=None) -> pd.DataFrame:
    """Dallas - Socrata (Dataset: y5xm-423z)"""
    df = fetch_socrata_permits("data.dallasopendata.com", "y5xm-423z", app_token=app_token, limit=5000)
    if df.empty:
        logging.warning("Dallas fetch returned empty dataset.")
        return pd.DataFrame()

    normalized = pd.DataFrame()
    normalized['city'] = ['Dallas'] * len(df)
    
    date_col = next((col for col in ['issued_date', 'issue_date', 'file_date'] if col in df.columns), None)
    if not date_col:
        return pd.DataFrame()

    normalized['app_date'] = pd.to_datetime(df[date_col], errors='coerce')
    normalized['issue_date'] = pd.to_datetime(df[date_col], errors='coerce')

    def classify_type(row):
        permit_type = str(row.get('permit_type', '')).lower()
        land_use = str(row.get('land_use', '')).lower()
        if 'multi' in land_use or 'apartment' in land_use:
            return 'Multifamily'
        elif 'single family' in land_use or 'residential' in permit_type:
            return 'Single Family'
        return 'Other'

    def classify_scope(row):
        work_type = str(row.get('work_type', '')).lower()
        if 'new' in work_type:
            return 'New Construction'
        elif any(term in work_type for term in ['alteration', 'renovation', 'addition', 'remodel']):
            return 'Alteration/Renovation'
        return 'Other'

    normalized['project_type'] = df.apply(classify_type, axis=1)
    normalized['work_scope'] = df.apply(classify_scope, axis=1)
    return normalized


def parse_san_antonio() -> pd.DataFrame:
    """San Antonio - ArcGIS FeatureServer"""
    url = "https://gis.sanantonio.gov/arcgis/rest/services/DSD/BuildingPermits/FeatureServer/0/query"
    df = fetch_arcgis_permits(url, limit=5000)
    if df.empty:
        logging.warning("San Antonio fetch returned empty dataset.")
        return pd.DataFrame()

    normalized = pd.DataFrame()
    normalized['city'] = ['San Antonio'] * len(df)
    normalized['app_date'] = pd.to_datetime(df.get('APPLIED_DATE'), unit='ms', errors='coerce')
    normalized['issue_date'] = pd.to_datetime(df.get('ISSUED_DATE'), unit='ms', errors='coerce')

    def classify_type(row):
        category = str(row.get('PERMIT_TYPE', '')).lower()
        desc = str(row.get('PERMIT_DESCRIPTION', '')).lower()
        if 'multi' in category or 'apartment' in desc:
            return 'Multifamily'
        elif 'commercial' not in category and ('single' in desc or 'res' in category):
            return 'Single Family'
        return 'Other'

    def classify_scope(row):
        scope = str(row.get('WORK_CLASS', '')).lower()
        if 'new' in scope:
            return 'New Construction'
        elif any(term in scope for term in ['remodel', 'alteration', 'repair', 'addition']):
            return 'Alteration/Renovation'
        return 'Other'

    normalized['project_type'] = df.apply(classify_type, axis=1)
    normalized['work_scope'] = df.apply(classify_scope, axis=1)
    return normalized


def parse_arlington() -> pd.DataFrame:
    """Arlington - ArcGIS FeatureServer"""
    url = "https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/Issued_Permits/FeatureServer/0/query"
    df = fetch_arcgis_permits(url, limit=5000)
    if df.empty:
        logging.warning("Arlington fetch returned empty dataset.")
        return pd.DataFrame()

    normalized = pd.DataFrame()
    normalized['city'] = ['Arlington'] * len(df)
    normalized['app_date'] = pd.to_datetime(df.get('ApplicationDate'), unit='ms', errors='coerce')
    normalized['issue_date'] = pd.to_datetime(df.get('IssueDate'), unit='ms', errors='coerce')

    def classify_type(row):
        desc = str(row.get('PermitType', '')).lower()
        if 'multi' in desc or 'apartment' in desc:
            return 'Multifamily'
        elif 'single family' in desc or 'residential' in desc:
            return 'Single Family'
        return 'Other'

    def classify_scope(row):
        scope = str(row.get('WorkClass', '')).lower()
        if 'new' in scope:
            return 'New Construction'
        elif any(term in scope for term in ['alteration', 'remodel', 'addition']):
            return 'Alteration/Renovation'
        return 'Other'

    normalized['project_type'] = df.apply(classify_type, axis=1)
    normalized['work_scope'] = df.apply(classify_scope, axis=1)
    return normalized


def parse_el_paso() -> pd.DataFrame:
    """El Paso - ArcGIS FeatureServer"""
    url = "https://gis.elpasotexas.gov/arcgis/rest/services/OpenData/BuildingPermits/FeatureServer/0/query"
    df = fetch_arcgis_permits(url, limit=5000)
    if df.empty:
        logging.warning("El Paso fetch returned empty dataset.")
        return pd.DataFrame()

    normalized = pd.DataFrame()
    normalized['city'] = ['El Paso'] * len(df)
    normalized['app_date'] = pd.to_datetime(df.get('APPLICATION_DATE'), unit='ms', errors='coerce')
    normalized['issue_date'] = pd.to_datetime(df.get('ISSUE_DATE'), unit='ms', errors='coerce')

    def classify_type(row):
        use_type = str(row.get('PROPOSED_USE', '')).lower()
        class_type = str(row.get('PERMIT_CLASS', '')).lower()
        if 'multi' in use_type or 'apartment' in use_type:
            return 'Multifamily'
        elif 'single' in use_type or 'residential' in class_type:
            return 'Single Family'
        return 'Other'

    def classify_scope(row):
        scope = str(row.get('WORK_TYPE', '')).lower()
        if 'new' in scope:
            return 'New Construction'
        elif any(term in scope for term in ['alteration', 'addition', 'repair']):
            return 'Alteration/Renovation'
        return 'Other'

    normalized['project_type'] = df.apply(classify_type, axis=1)
    normalized['work_scope'] = df.apply(classify_scope, axis=1)
    return normalized
