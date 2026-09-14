import os
import logging
import pandas as pd
from src.parsers import parse_austin, parse_dallas, parse_san_antonio, parse_arlington, parse_el_paso

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def run_pipeline():
    logging.info("Starting Texas Building Permit Ingestion Pipeline...")
    
    # Read Socrata app token if set in environment (optional)
    app_token = os.getenv("SOCRATA_APP_TOKEN", None)

    # 1. Execute Extractor and Parser Functions
    city_parsers = [
        lambda: parse_austin(app_token=app_token),
        lambda: parse_dallas(app_token=app_token),
        parse_san_antonio,
        parse_arlington,
        parse_el_paso
    ]

    city_dfs = []
    for parser in city_parsers:
        try:
            df = parser()
            if not df.empty:
                city_dfs.append(df)
        except Exception as e:
            logging.error(f"Failed to execute parser: {e}")

    if not city_dfs:
        logging.error("No permit datasets were extracted. Terminating pipeline.")
        return

    # 2. Concatenate Extracted Datasets
    full_df = pd.concat(city_dfs, ignore_index=True)

    # 3. Calculate Permit Review Duration (Calendar Days)
    full_df['review_days'] = (full_df['issue_date'] - full_df['app_date']).dt.days

    # 4. Filter Invalid Records
    clean_df = full_df[
        (full_df['review_days'] >= 0) &
        (full_df['project_type'].isin(['Single Family', 'Multifamily'])) &
        (full_df['work_scope'].isin(['New Construction', 'Alteration/Renovation']))
    ].copy()

    # 5. Aggregate Metrics (Mean & Median Review Times)
    summary_df = clean_df.groupby(['city', 'project_type', 'work_scope']).agg(
        total_permits=('review_days', 'count'),
        avg_review_days=('review_days', lambda x: round(x.mean(), 1)),
        median_review_days=('review_days', lambda x: round(x.median(), 1))
    ).reset_index()

    # 6. Ensure Output Directory Exists & Export CSV Files
    os.makedirs("data", exist_ok=True)
    summary_df.to_csv("data/texas_permit_summary.csv", index=False)
    clean_df.to_csv("data/texas_permit_detailed.csv", index=False)

    logging.info("Pipeline Complete. Data written to data/ directory.")
    logging.info("\nAggregated Results:\n" + summary_df.to_string(index=False))

if __name__ == "__main__":
    run_pipeline()
