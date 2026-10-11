import os
from sqlalchemy.ext.asyncio import create_async_engine,async_sessionmaker, AsyncAttrs
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL=os.getenv("POSTGRES_DB_URL")
engine=create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=10,
    max_overflow=20
)

AsyncSessionLocal=async_sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False
)
# 4. Define the Base Class for our future models
class Base(AsyncAttrs, DeclarativeBase):
    pass