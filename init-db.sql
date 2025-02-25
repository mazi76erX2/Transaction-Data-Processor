-- Create a separate database for application data
CREATE DATABASE finance_app;

-- Connect to the finance_app database
\c finance_app;

-- Create transactions table
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    transaction_id VARCHAR(50) UNIQUE NOT NULL,
    user_id INT NOT NULL,
    amount FLOAT NOT NULL,
    transaction_date DATE NOT NULL
);

-- Create some indexes to improve query performance
CREATE INDEX idx_transactions_user_id ON transactions(user_id);
CREATE INDEX idx_transactions_date ON transactions(transaction_date);

-- Switch back to airflow database for Airflow metadata
\c airflow;