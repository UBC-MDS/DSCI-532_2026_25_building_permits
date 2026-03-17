'''
Converts the raw data in data/raw/ to a parquet file and outputs the parquet file to data/processed
'''
import os
import pandas as pd
from pathlib import Path

# declare the column names for each filter
ISSUE_DATE = 'IssueDate'
APPLIED_DATE = 'PermitNumberCreatedDate'
PERMIT_TYPE = 'TypeOfWork'

RAW_PATH = Path("data") / "raw" / "issued-building-permits.csv"
OUTPUT_PATH = Path("data") / "processed" / "issued-building-permits.parquet"

# Read in the data
permits_df = pd.read_csv(
    RAW_PATH,
    sep=';',
    encoding='utf-8'
)

# Standardize dates and strip whitespace for values we want to filter on
permits_df[ISSUE_DATE] = pd.to_datetime(permits_df[ISSUE_DATE])
permits_df[APPLIED_DATE] = pd.to_datetime(permits_df[APPLIED_DATE])
permits_df[PERMIT_TYPE] = permits_df[PERMIT_TYPE].astype(str).str.strip()

try:

    os.makedirs(OUTPUT_PATH.parent, exist_ok = True)
    
    permits_df.to_parquet(
        OUTPUT_PATH,
        index = False
    )

    print(f"Succesfully wrote to {OUTPUT_PATH}")

except Exception as e:
    raise e
