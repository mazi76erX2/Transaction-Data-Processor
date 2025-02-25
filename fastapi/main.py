from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db, Transaction
from pydantic import BaseModel

# Create FastAPI app
app = FastAPI(title="Financial Transactions API")

# Define your models and endpoints here

@app.get("/")
async def root():
    return {"message": "Welcome to the Financial Transactions API"}

# TODO: Implement the GET /transactions/{user_id}/summary endpoint here