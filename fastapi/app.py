from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
from pydantic import BaseModel
from database import get_db, Transaction

app = FastAPI(title="Financial Transactions API")


@app.get("/")
async def root():
    return {"message": "Welcome to the Financial Transactions API"}


class TransactionSummary(BaseModel):
    user_id: int
    total_transactions: int
    total_amount: float
    average_transaction_amount: float


@app.get("/transactions/{user_id}/summary", response_model=TransactionSummary)
async def get_transaction_summary(
    user_id: int, db: AsyncSession = Depends(get_db)
) -> TransactionSummary:
    # Build a SQL query to count, sum, and average transactions for the given user
    query = select(
        func.count(Transaction.id).label("total_transactions"),
        func.sum(Transaction.amount).label("total_amount"),
        func.avg(Transaction.amount).label("average_transaction_amount"),
    ).where(Transaction.user_id == user_id)

    result = await db.execute(query)
    summary = result.one()

    if summary.total_transactions == 0:
        raise HTTPException(
            status_code=404, detail="No transactions found for this user"
        )

    return TransactionSummary(
        user_id=user_id,
        total_transactions=summary.total_transactions,
        total_amount=(
            float(summary.total_amount) if summary.total_amount is not None else 0.0
        ),
        average_transaction_amount=(
            float(summary.average_transaction_amount)
            if summary.average_transaction_amount is not None
            else 0.0
        ),
    )
