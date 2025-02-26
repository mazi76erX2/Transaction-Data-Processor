# OpenTax Financial Transactions System

A complete solution for processing and analyzing financial transaction data using Apache Airflow, FastAPI, and PostgreSQL.

## System Overview

This system consists of three main components:
1. **ETL Pipeline**: Airflow DAG that processes financial transaction data daily
2. **API Service**: FastAPI application that provides transaction insights
3. **Database**: PostgreSQL database for storing and querying transaction data

## Prerequisites

- Docker and Docker Compose
- Git
- Python 3.9+

## Project Structure

```
.
├── dags/                   # Airflow DAGs
│   └── etl_transactions.py # Main ETL pipeline
├── data/                   # Data directory
│   └── financial_transactions.csv  # Sample data file
├── fastapi/                # FastAPI application
│   ├── app.py              # Main API application
│   ├── Dockerfile          # Docker configuration for FastAPI
│   └── requirements.txt    # Python dependencies
├── logs/                   # Airflow log files
├── fastapi/                # FastAPI application
├── schema.sql              # Database schema
├── .gitignore              # Git ignore file
├── init-db.sql             # Database initialization script
├── docker-compose.yml      # Docker Compose configuration
├── README.md               # This file
├── README-task.md          # Task file
└── Take-Home Assignment_Backend Engineer.md    # Other task file
```

## Setup Instructions

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/opentax-financial-system.git
   cd opentax-financial-system
   ```

2. Create necessary directories and add permissions:
   ```bash
   mkdir -p data logs
   chmod -R 777 dags/            
   chmod -R 777 logs/
   chmod -R 777 data/
   ```

3. Start the services:
   ```bash
   docker-compose up -d
   ```

4. Access the services:
   - Airflow: http://localhost:8080 (username: admin, password: admin)
   - FastAPI: http://localhost:8000 (API documentation: http://localhost:8000/docs)
   - PostgreSQL: localhost:5432 (username: airflow, password: airflow)

## Using the Airflow DAG

The ETL pipeline performs the following steps:
1. Extracts data from the CSV file
2. Transforms the data (normalizes dates, removes duplicates, etc.)
3. Loads the data into the PostgreSQL database

To run the DAG manually:
1. Go to the Airflow UI (http://localhost:8080)
2. Navigate to the DAGs page
3. Find the "etl_transactions" DAG
4. Click the "Play" button to trigger the DAG

## Using the API

The FastAPI service provides an endpoint to get transaction summaries for users:

```
GET /transactions/{user_id}/summary
```

### Example Request:
```bash
curl http://localhost:8000/transactions/123/summary
```

### Example Response:
```json
{
  "user_id": 123,
  "total_transactions": 50,
  "total_amount": 10240.50,
  "average_transaction_amount": 204.81
}
```

## Database Schema

The main transactions table has the following schema:

```sql
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    transaction_id VARCHAR(50) UNIQUE NOT NULL,
    user_id INT NOT NULL,
    amount FLOAT NOT NULL,
    transaction_date DATE NOT NULL
);
```

Indexes:
- Primary key on `id`
- Unique index on `transaction_id`
- Index on `user_id`
- Index on `transaction_date`

## Development Notes

### Adding New Data
Place new data files in the `data` directory and update the `CSV_FILE_PATH` in the DAG file if necessary.

### Modifying the API
The FastAPI application can be extended with new endpoints as needed. After modifying the code, restart the FastAPI container:

```bash
docker compose restart fastapi
```

### Database Maintenance
The system includes an initialization script (`init-db.sql`) that creates the necessary database and tables. For routine maintenance or schema changes, connect to the PostgreSQL instance:

```bash
docker compose exec postgres psql -U airflow
```

## Task C: Database Query Optimization for Financial Transactions

When handling large datasets of financial transactions, performance considerations become critical. Here are key strategies to optimize database queries and overall system performance:

## Indexing Strategies

1. **Create appropriate indexes** on frequently queried columns:
   - Primary key (`id`) is automatically indexed
   - `user_id` index for fast user-specific queries
   - `transaction_date` index for date range queries
   - Compound indexes for queries that filter on multiple columns (e.g., `(user_id, transaction_date)`)

2. **Consider partial indexes** for specific query patterns:
   ```sql
   -- Example: Index for transactions with large amounts (e.g., > $10,000)
   CREATE INDEX idx_large_transactions ON transactions(user_id, amount)
   WHERE amount > 10000;
   ```

## Query Optimization

1. **Use specific column selection** instead of `SELECT *`:
   ```sql
   -- Instead of SELECT * FROM transactions
   SELECT transaction_id, amount, transaction_date FROM transactions WHERE user_id = 123;
   ```

2. **Implement pagination** for large result sets:
   ```sql
   SELECT * FROM transactions WHERE user_id = 123 
   ORDER BY transaction_date DESC LIMIT 100 OFFSET 0;
   ```

3. **Optimize aggregation queries** using window functions for complex analytics:
   ```sql
   -- Efficient way to get running totals
   SELECT 
     transaction_date, 
     amount, 
     SUM(amount) OVER (PARTITION BY user_id ORDER BY transaction_date) as running_total
   FROM transactions 
   WHERE user_id = 123;
   ```

## Database Architecture

1. **Partitioning** the transactions table:
   - Time-based partitioning by month or year (e.g., `transactions_2024_01`, `transactions_2024_02`)
   - Significantly improves query performance when filtering by date ranges

2. **Materialized views** for common analytical queries:
   ```sql
   CREATE MATERIALIZED VIEW user_monthly_summaries AS
   SELECT 
     user_id, 
     DATE_TRUNC('month', transaction_date) as month,
     COUNT(*) as transaction_count,
     SUM(amount) as total_amount,
     AVG(amount) as avg_amount
   FROM transactions
   GROUP BY user_id, DATE_TRUNC('month', transaction_date);

   -- Refresh as needed
   REFRESH MATERIALIZED VIEW user_monthly_summaries;
   ```

3. **Connection pooling** to manage database connections efficiently

## Application-Level Optimizations

1. **Implement caching** for frequently accessed data:
   - Redis for API response caching
   - In-memory caching for high-frequency queries

2. **Batch processing** for insertions and updates:
   ```python
   # Instead of individual inserts
   session.bulk_insert_mappings(Transaction, transactions_list)
   ```

3. **Async database operations** in FastAPI to handle concurrent requests efficiently

## Monitoring and Maintenance

1. **Regular VACUUM and ANALYZE** operations to maintain index efficiency

2. **Monitor slow queries** using PostgreSQL's query planner:
   ```sql
   EXPLAIN ANALYZE SELECT * FROM transactions WHERE user_id = 123;
   ```

3. **Set up database metrics** to track query performance over time

By implementing these optimizations, the system will be able to handle large volumes of financial transactions while maintaining fast query response times and overall system performance.