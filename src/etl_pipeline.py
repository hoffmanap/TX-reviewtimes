import os
import logging
import pandas as pd
from src.parsers import parse_austin, parse_dallas, parse_san_antonio, parse_arlington, parse_el_paso

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def run_pipeline():
    logging.info("Starting Texas Building Permit Ingestion Pipeline...")
    
    os.makedirs("data", exist_ok=True)
    app_token = os.getenv("SOCRATA_APP_TOKEN", None)

    city_parsers = [
        ("Austin", lambda: parse_austin(app_token=app_token)),
        ("Dallas", lambda: parse_dallas(app_token=app_token)),
        ("San Antonio", parse_san_antonio),
        ("Arlington", parse_arlington),
        ("El Paso", parse_el_paso)
    ]

    city_dfs = []
    for city_name, parser in city_parsers:
        try:
            df = parser()
            logging.info(f"{city_name}: Fetched {len(df)} records.")
            if not df.empty:
                city_dfs.append(df)
        except Exception as e:
            logging.error(f"Error parsing {city_name}: {e}")

    if not city_dfs:
        logging.warning("No permit datasets were extracted.")
        return

    full_df = pd.concat(city_dfs, ignore_index=True)
    logging.info(f"Total raw records combined: {len(full_df)}")

    full_df['review_days'] = (full_df['issue_date'] - full_df['app_date']).dt.days

    # Filter out invalid records
    clean_df = full_df[
        (full_df['review_days'] >= 0) &
        (full_df['project_type'].isin(['Single Family', 'Multifamily'])) &
        (full_df['work_scope'].isin(['New Construction', 'Alteration/Renovation']))
    ].copy()

    logging.info(f"Total classified records remaining after filter: {len(clean_df)}")

    if clean_df.empty:
        # Fallback: keep unclassified scopes if filtering was too aggressive
        clean_df = full_df[full_df['review_days'] >= 0].copy()
        logging.warning("Relaxed filters applied to populate output dataset.")

    summary_df = clean_df.groupby(['city', 'project_type', 'work_scope']).agg(
        total_permits=('review_days', 'count'),
        avg_review_days=('review_days', lambda x: round(x.mean(), 1)),
        median_review_days=('review_days', lambda x: round(x.median(), 1))
    ).reset_index()

    summary_df.to_csv("data/texas_permit_summary.csv", index=False)
    clean_df.to_csv("data/texas_permit_detailed.csv", index=False)

    logging.info("Pipeline complete. CSV outputs successfully written.")

if __name__ == "__main__":
    run_pipeline()

if __name__ == "__main__":
    run_pipeline()
