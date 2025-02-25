from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

# Define default arguments for the DAG
default_args = {
    'owner': 'candidate',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Define the DAG
dag = DAG(
    'etl_transactions',
    default_args=default_args,
    description='ETL pipeline for financial transactions',
    schedule_interval='0 0 * * *',  # Run daily at midnight
    start_date=datetime(2023, 1, 1),
    catchup=False,
)

# Task dependencies will be defined by the candidate
# extract_task >> transform_task >> load_task