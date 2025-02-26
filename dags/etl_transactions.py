import logging
from datetime import datetime, timedelta
from typing import Any

import pandas as pd
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.hooks.postgres_hook import PostgresHook

CSV_FILE_PATH: str = "/opt/airflow//data/financial_transactions.csv"

# Define default arguments for the DAG
default_args = {
    "owner": "Xolani Mazibuko",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    "start_date": datetime(2025, 1, 1),
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

    transactions: list[dict[str, Any]] = df.to_dict(orient="records")
    kwargs["ti"].xcom_push(key="raw_transactions", value=transactions)
    logging.info(f"Extracted {len(transactions)} transactions.")


def transform_task(**kwargs: Any) -> None:
    """
    Transforms the data:
      - Converts amounts to float.
      - Normalizes date formats to YYYY-MM-DD.
      - Removes duplicate transactions.
    """
    transactions: list[dict[str, Any]] = kwargs["ti"].xcom_pull(key="raw_transactions")
    if not transactions:
        raise ValueError("No transactions found for transformation.")

    df: pd.DataFrame = pd.DataFrame(transactions)

    # Clean the "amount" column by removing '$' and commas
    df["amount"] = df["amount"].replace({"[\$,]": ""}, regex=True).astype(float)
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df = df.dropna(subset=["amount"])

    df["transaction_date"] = pd.to_datetime(df["transaction_date"], errors="coerce")
    df = df.dropna(subset=["transaction_date"])
    df["transaction_date"] = df["transaction_date"].dt.strftime("%Y-%m-%d")

    df = df.drop_duplicates(subset=["transaction_id"])

    cleaned_transactions: list[dict[str, Any]] = df.to_dict(orient="records")
    kwargs["ti"].xcom_push(key="cleaned_transactions", value=cleaned_transactions)
    logging.info(
        f"Transformed data: {len(cleaned_transactions)} transactions after cleaning."
    )


def load_task(**kwargs: Any) -> None:
    """
    Loads the cleaned transactions into the PostgreSQL table (in 'finance_app' DB).
    Also creates the 'finance_app' database if it doesn't exist.
    Filters out any transactions that already exist in the table.
    """
    transactions: list[dict[str, Any]] = kwargs["ti"].xcom_pull(
        key="cleaned_transactions"
    )
    if not transactions:
        raise ValueError("No transactions found for loading.")

    # Connect to the 'postgres' database to create 'finance_app' if needed.
    admin_hook = PostgresHook(
        postgres_conn_id="postgres_default",
        schema="postgres",
    )
    admin_conn = admin_hook.get_conn()
    admin_conn.autocommit = True

    try:
        with admin_conn.cursor() as cursor:
            cursor.execute("SELECT 1 FROM pg_database WHERE datname='finance_app'")
            exists = cursor.fetchone()
            if not exists:
                logging.info("Creating finance_app database since it does not exist.")
                cursor.execute("CREATE DATABASE finance_app")
    except Exception as e:
        logging.error(f"Error checking/creating finance_app database: {e}")
        raise
    finally:
        admin_conn.close()

    # Connect to 'finance_app' and prepare the engine.
    pg_hook = PostgresHook(
        postgres_conn_id="postgres_default",
        schema="finance_app",  # This sets the target DB
    )
    engine = pg_hook.get_sqlalchemy_engine()

    df: pd.DataFrame = pd.DataFrame(transactions)

    try:
        with engine.connect() as connection:
            # Create the transactions table if it doesn't exist
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS transactions (
                    id SERIAL PRIMARY KEY,
                    transaction_id VARCHAR(50) UNIQUE NOT NULL,
                    user_id INT NOT NULL,
                    amount FLOAT NOT NULL,
                    transaction_date DATE NOT NULL
                )
                """
            )

            # Create indexes if they don't exist
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_transactions_user_id
                ON transactions(user_id)
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_transactions_date
                ON transactions(transaction_date)
                """
            )

            # Query existing transaction_ids from the table
            result = connection.execute("SELECT transaction_id FROM transactions")
            existing_ids = {row[0] for row in result.fetchall()}
            logging.info(f"Found {len(existing_ids)} existing transaction IDs.")

        # Filter out transactions that are already in the database
        if existing_ids:
            original_count = len(df)
            df = df[~df["transaction_id"].isin(existing_ids)]
            logging.info(
                f"Filtered out {original_count - len(df)} duplicate transactions."
            )

        # Insert new transactions if any remain
        if df.empty:
            logging.info("No new transactions to load.")
        else:
            df.to_sql(
                "transactions",
                engine,
                if_exists="append",  # Append only new data
                index=False,
                method="multi",
                chunksize=1000,
            )
            logging.info(f"Loaded {len(df)} new transactions into the database.")

        # Log the load operation in etl_logs table
        with engine.connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS etl_logs (
                    id SERIAL PRIMARY KEY,
                    execution_date TIMESTAMP NOT NULL,
                    records_loaded INT NOT NULL,
                    status VARCHAR(50) NOT NULL
                )
                """
            )
            connection.execute(
                """
                INSERT INTO etl_logs (execution_date, records_loaded, status)
                VALUES (%s, %s, %s)
                """,
                (datetime.now(), len(df), "SUCCESS"),
            )

    except Exception as e:
        logging.error(f"Error loading data into PostgreSQL: {e}")
        raise


with DAG(
    "etl_transactions",
    default_args=default_args,
    description="ETL pipeline for financial transactions",
    schedule_interval="0 0 * * *",  # Run daily at midnight
    start_date=datetime(2023, 1, 1),
    catchup=False,
) as dag:

    extract_task = PythonOperator(
        task_id="extract",
        python_callable=extract_task,
        provide_context=True,
    )

    transform_task = PythonOperator(
        task_id="transform",
        python_callable=transform_task,
        provide_context=True,
    )

    load_task = PythonOperator(
        task_id="load",
        python_callable=load_task,
        provide_context=True,
    )

    extract_task >> transform_task >> load_task
