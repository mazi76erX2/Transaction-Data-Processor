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
├── dags/                                       # Airflow DAGs
│   └── etl_transactions.py                     # Main ETL pipeline
├── data/                                       # Data directory
│   └── financial_transactions.csv              # Sample data file
├── fastapi/                                    # FastAPI application
│   ├── app.py                                  # Main API application
│   ├── Dockerfile                              # Docker configuration for FastAPI
│   └── requirements.txt                        # Python dependencies
├── logs/                                       # Airflow log files
├── fastapi/                                    # FastAPI application
├── schema.sql                                  # Database schema
├── .gitignore                                  # Git ignore file
├── init-db.sql                                 # Database initialization script
├── docker-compose.yml                          # Docker Compose configuration
├── README.md                                   # This file
├── README-task.md                              # Task file
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

5. Change Postgres database settings if you receive errors with connection in your logs:
   - On the Airflow dashboard click on the Admin dropdown then connections.
   - Click on edit record on the postgres_default row
   - Add the following details: - Schema: `finance_app`, - Login: `airflow`, - Password: `airflow`, Host: `postgres`, Port: `5432`
   - Click Save

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

### Indexing Strategies

1. **Create appropriate indexes** on frequently queried columns:
   - Primary key (`id`) is automatically indexed
   - `user_id` index for fast user-specific queries
   - `transaction_date` index for date range queries
   - Compound indexes for queries that filter on multiple columns (e.g., `(user_id, transaction_date)`)

2. **Consider partial indexes** for specific query patterns:
   ```python
   # Example: Index for transactions with large amounts (e.g., > $10,000)
   class Transaction(Base):
      __tablename__ = 'transactions'
      
      transaction_id = Column(Integer, primary_key=True)
      user_id = Column(Integer, index=True)
      amount = Column(Float)
      transaction_date = Column(DateTime)
      
      # Create a partial index for large transactions
      __table_args__ = (
         Index('idx_large_transactions', 'user_id', 'amount', 
               postgresql_where=text('amount > 10000')),
      )
   ```

### Query Optimization

1. **Use specific column selection** instead of `SELECT *`:
   ```python
   # Instead of SELECT * FROM transactions
   def get_specific_user_transactions(db: Session, user_id: int):
      query = select(
         Transaction.transaction_id,
         Transaction.amount,
         Transaction.transaction_date
      ).where(Transaction.user_id == user_id)
      
      return db.execute(query).fetchall()
   ```

2. **Implement pagination** for large result sets:
   ```python
   def get_paginated_user_transactions(db: Session, user_id: int, limit: int = 100, offset: int = 0):
      query = select(Transaction).where(
         Transaction.user_id == user_id
      ).order_by(
         Transaction.transaction_date.desc()
      ).limit(limit).offset(offset)

      return db.execute(query).fetchall()
   ```

3. **Optimize aggregation queries** using window functions for complex analytics:
   ```python
   # Efficient way to get running totals
   from sqlalchemy.sql import func
   from sqlalchemy import over

   def get_running_totals(db: Session, user_id: int):
      running_total = func.sum(Transaction.amount).over(
         partition_by=Transaction.user_id,
         order_by=Transaction.transaction_date
      ).label('running_total')
      
      query = select(
         Transaction.transaction_date,
         Transaction.amount,
         running_total
      ).where(Transaction.user_id == user_id)
      
      return db.execute(query).fetchall()
   ```

### Database Architecture

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

### Application-Level Optimizations

1. **Implement caching** for frequently accessed data:
   - Redis for API response caching
   - In-memory caching for high-frequency queries

2. **Batch processing** for insertions and updates:
   ```python
   # Instead of individual inserts
   session.bulk_insert_mappings(Transaction, transactions_list)
   ```

3. **Async database operations** in FastAPI to handle concurrent requests efficiently

### Monitoring and Maintenance

1. **Regular VACUUM and ANALYZE** operations to maintain index efficiency

2. **Monitor slow queries** using PostgreSQL's query planner:
   ```python
   EXPLAIN ANALYZE SELECT * FROM transactions WHERE user_id = 123;
   ```

3. **Set up database metrics** to track query performance over time

By implementing these optimizations, the system will be able to handle large volumes of financial transactions while maintaining fast query response times and overall system performance.

## 🧠 Thought Process, Key Decisions, and Trade-offs

### FastAPI Service

**Thought Process:**
* **Asynchronous Design:** The endpoint is defined as `async def` to leverage asynchronous database operations. This makes the API more scalable under load since it doesn't block on I/O.
* **Dependency Injection:** Using `Depends(get_db)` ensures that each request gets a fresh, managed async database session, simplifying resource cleanup.
* **Aggregation in the Database:** Offloading the aggregation work (count, sum, avg) to the database minimizes data transfer and processing in Python, which is efficient and scalable.

**Key Decisions:**
* **Use of Pydantic for Response Models:** Enforces type safety and auto-generates API documentation.
* **Using SQLAlchemy Core:** Provides a clear and expressive way to construct queries with built-in functions (`func.count`, etc.) that let the database handle heavy-lifting.
* **Error Handling with HTTPException:** Ensures that the API returns meaningful HTTP status codes (like 404) when no data is found.

**Trade-offs:**
* **Complexity vs. Performance:** Asynchronous endpoints add some complexity but greatly improve performance under high concurrency.
* **Database Load:** Aggregation queries run on the database side; if the table grows very large, you may need further optimizations (indexes, partitioning) to maintain performance.

**Overall Trade-offs:**
* **Modularity vs. Complexity:** Splitting the process into extraction, transformation, and loading (ETL) improves maintainability but introduces complexity in handling dependencies (managed via XCom).
* **Performance:** Both FastAPI and Airflow aim to push heavy processing (e.g., aggregation, filtering) down to the database layer to leverage its efficiency, but this requires proper indexing and database tuning.
* **Scalability:** Asynchronous FastAPI endpoints and batch processing in Airflow can handle large volumes of data if the underlying database is properly optimized (using indexing, partitioning, etc.).

**Additional Considerations:**
* **Defaulting Instead of Dropping:** By defaulting missing or invalid `transaction_date` values to **2024-01-01** instead of dropping the rows, you preserve all transaction data. This may be important for auditing purposes or to avoid data loss. The trade-off is that you need to clearly document that any missing date is replaced with the default.

* **Logging the Default Action:** Logging both to the Airflow log file and inserting a record into the audit table (etl_logs) ensures that you can later review how many records had their dates defaulted. This helps with both debugging and audit compliance.

Built with ❤️ by [Xolani Mazibuko]