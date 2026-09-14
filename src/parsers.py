import pandas as pd
import logging
from src.extractors import fetch_socrata_permits, fetch_arcgis_permits

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def normalize_text(val):
    return str(val).lower() if pd.notna(val) else ''

def parse_austin(app_token=None) -> pd.DataFrame:
    df = fetch_socrata_permits("data.austintexas.gov", "3syk-w9eu", app_token=app_token, limit=5000)
    if df.empty:
        return pd.DataFrame()

    normalized = pd.DataFrame()
    normalized['city'] = ['Austin'] * len(df)

    # Dynamic column resolver for Austin schema
    app_col = next((col for col in ['issue_date', 'applied_date', 'application_date', 'status_date'] if col in df.columns), None)
    issue_col = next((col for col in ['issue_date', 'issued_date'] if col in df.columns), None)

    if not app_col or not issue_col:
        return pd.DataFrame()

    normalized['app_date'] = pd.to_datetime(df[app_col], errors='coerce')
    normalized['issue_date'] = pd.to_datetime(df[issue_col], errors='coerce')

    def classify_type(row):
        text = f"{normalize_text(row.get('work_description'))} {normalize_text(row.get('permit_type_desc'))} {normalize_text(row.get('permit_type'))} {normalize_text(row.get('description'))}"
        if any(k in text for k in ['multi', 'apartment', 'condo', 'apt', 'units', 'commercial']):
            return 'Multifamily'
        # Broad residential fallback for single family
        return 'Single Family'

    def classify_scope(row):
        text = f"{normalize_text(row.get('work_class'))} {normalize_text(row.get('work_type'))} {normalize_text(row.get('permit_type'))}"
        if any(k in text for k in ['new', 'addition', 'erect', 'construction', 'building']):
            return 'New Construction'
        return 'Alteration/Renovation'

    normalized['project_type'] = df.apply(classify_type, axis=1)
    normalized['work_scope'] = df.apply(classify_scope, axis=1)
    return normalized


def parse_dallas(app_token=None) -> pd.DataFrame:
    # Fixed Domain: www.dallasopendata.com
    df = fetch_socrata_permits("www.dallasopendata.com", "y5xm-423z", app_token=app_token, limit=5000)
    if df.empty:
        return pd.DataFrame()

    normalized = pd.DataFrame()
    normalized['city'] = ['Dallas'] * len(df)
    
    date_col = next((col for col in ['issued_date', 'issue_date', 'file_date'] if col in df.columns), None)
    if not date_col:
        return pd.DataFrame()

    normalized['app_date'] = pd.to_datetime(df[date_col], errors='coerce')
    normalized['issue_date'] = pd.to_datetime(df[date_col], errors='coerce')

    def classify_type(row):
        text = f"{normalize_text(row.get('permit_type'))} {normalize_text(row.get('land_use'))}"
        if any(k in text for k in ['multi', 'apartment', 'condo']):
            return 'Multifamily'
        return 'Single Family'

    def classify_scope(row):
        text = f"{normalize_text(row.get('work_type'))} {normalize_text(row.get('permit_type'))}"
        if any(k in text for k in ['new', 'addition', 'construction']):
            return 'New Construction'
        return 'Alteration/Renovation'

    normalized['project_type'] = df.apply(classify_type, axis=1)
    normalized['work_scope'] = df.apply(classify_scope, axis=1)
    return normalized


def parse_san_antonio() -> pd.DataFrame:
    url = "https://gis.sanantonio.gov/arcgis/rest/services/DSD/BuildingPermits/FeatureServer/0/query"
    df = fetch_arcgis_permits(url, limit=5000)
    if df.empty:
        return pd.DataFrame()

    normalized = pd.DataFrame()
    normalized['city'] = ['San Antonio'] * len(df)
    normalized['app_date'] = pd.to_datetime(df.get('APPLIED_DATE'), unit='ms', errors='coerce')
    normalized['issue_date'] = pd.to_datetime(df.get('ISSUED_DATE'), unit='ms', errors='coerce')

    def classify_type(row):
        text = f"{normalize_text(row.get('PERMIT_TYPE'))} {normalize_text(row.get('PERMIT_DESCRIPTION'))}"
        if any(k in text for k in ['multi', 'apartment', 'condo']):
            return 'Multifamily'
        return 'Single Family'

    def classify_scope(row):
        text = f"{normalize_text(row.get('WORK_CLASS'))} {normalize_text(row.get('PERMIT_TYPE'))}"
        if any(k in text for k in ['new', 'addition']):
            return 'New Construction'
        return 'Alteration/Renovation'

    normalized['project_type'] = df.apply(classify_type, axis=1)
    normalized['work_scope'] = df.apply(classify_scope, axis=1)
    return normalized


def parse_arlington() -> pd.DataFrame:
    url = "https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/Issued_Permits/FeatureServer/0/query"
    df = fetch_arcgis_permits(url, limit=5000)
    if df.empty:
        return pd.DataFrame()

    normalized = pd.DataFrame()
    normalized['city'] = ['Arlington'] * len(df)
    normalized['app_date'] = pd.to_datetime(df.get('ApplicationDate'), unit='ms', errors='coerce')
    normalized['issue_date'] = pd.to_datetime(df.get('IssueDate'), unit='ms', errors='coerce')

    def classify_type(row):
        text = f"{normalize_text(row.get('PermitType'))} {normalize_text(row.get('WorkClass'))}"
        if any(k in text for k in ['multi', 'apartment', 'condo']):
            return 'Multifamily'
        return 'Single Family'

    def classify_scope(row):
        text = f"{normalize_text(row.get('WorkClass'))} {normalize_text(row.get('PermitType'))}"
        if any(k in text for k in ['new', 'addition']):
            return 'New Construction'
        return 'Alteration/Renovation'

    normalized['project_type'] = df.apply(classify_type, axis=1)
    normalized['work_scope'] = df.apply(classify_scope, axis=1)
    return normalized


def parse_el_paso() -> pd.DataFrame:
    url = "https://gis.elpasotexas.gov/arcgis/rest/services/OpenData/BuildingPermits/FeatureServer/0/query"
    df = fetch_arcgis_permits(url, limit=5000)
    if df.empty:
        return pd.DataFrame()

    normalized = pd.DataFrame()
    normalized['city'] = ['El Paso'] * len(df)
    normalized['app_date'] = pd.to_datetime(df.get('APPLICATION_DATE'), unit='ms', errors='coerce')
    normalized['issue_date'] = pd.to_datetime(df.get('ISSUE_DATE'), unit='ms', errors='coerce')

    def classify_type(row):
        text = f"{normalize_text(row.get('PROPOSED_USE'))} {normalize_text(row.get('PERMIT_CLASS'))}"
        if any(k in text for k in ['multi', 'apartment', 'condo']):
            return 'Multifamily'
        return 'Single Family'

    def classify_scope(row):
        text = f"{normalize_text(row.get('WORK_TYPE'))} {normalize_text(row.get('PERMIT_CLASS'))}"
        if any(k in text for k in ['new', 'addition']):
            return 'New Construction'
        return 'Alteration/Renovation'

    normalized['project_type'] = df.apply(classify_type, axis=1)
    normalized['work_scope'] = df.apply(classify_scope, axis=1)
    return normalized
