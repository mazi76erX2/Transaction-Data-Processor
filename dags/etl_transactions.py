import logging
from datetime import datetime, timedelta
from typing import Any

import pandas as pd
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.hooks.postgres_hook import PostgresHook

CSV_FILE_PATH: str = "/data/financial_transactions.csv"

# Define default arguments for the DAG
default_args = {
    "owner": "candidate",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

# Define the DAG
dag = DAG(
    "etl_transactions",
    default_args=default_args,
    description="ETL pipeline for financial transactions",
    schedule_interval="0 0 * * *",  # Run daily at midnight
    start_date=datetime(2023, 1, 1),
    catchup=False,
)

# Task dependencies will be defined by the candidate
# extract_task >> transform_task >> load_task


def extract_task(**kwargs: Any) -> None:
    """
    Extracts data from a CSV file into a list of dictionaries.
    """
    try:
        df: pd.DataFrame = pd.read_csv(CSV_FILE_PATH)
    except Exception as e:
        logging.error(f"Failed to read CSV file: {e}")
        raise

    # Convert DataFrame to a list of dicts (JSON-serializable)
    transactions: list[dict[str, Any]] = df.to_dict(orient="records")
    kwargs["ti"].xcom_push(key="raw_transactions", value=transactions)
    logging.info(f"Extracted {len(transactions)} transactions.")
