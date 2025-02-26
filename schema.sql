-- schema.sql
-- Create the transactions table
CREATE TABLE IF NOT EXISTS transactions (
    id SERIAL PRIMARY KEY,
    transaction_id VARCHAR(50) UNIQUE NOT NULL,
    user_id INT NOT NULL,
    amount FLOAT NOT NULL,
    transaction_date DATE NOT NULL
);

-- Create indexes for fast queries on frequently filtered columns
CREATE INDEX IF NOT EXISTS idx_transactions_user_id
    ON transactions(user_id);

CREATE INDEX IF NOT EXISTS idx_transactions_date
    ON transactions(transaction_date);