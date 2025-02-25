from sqlalchemy import Column, Integer, String, Float, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Database connection string
SQLALCHEMY_DATABASE_URL = "postgresql+asyncpg://airflow:airflow@postgres:5432/finance_app"

# Create async engine
engine = create_async_engine(SQLALCHEMY_DATABASE_URL)
async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Create base class for models
Base = declarative_base()

# Define Transaction model
class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String(50), unique=True, nullable=False)
    user_id = Column(Integer, nullable=False)
    amount = Column(Float, nullable=False)
    transaction_date = Column(Date, nullable=False)

# Async session context manager
async def get_db():
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()