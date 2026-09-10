import os

from dotenv import load_dotenv
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

# Older code read DATABASE_URL, newer code read SUPABASE_DB_URL. Accept either.
DATABASE_URL = os.getenv("SUPABASE_DB_URL") or os.getenv("DATABASE_URL")

# Sized for the concurrent request load, not the default 5+10. Every request
# that touches Postgres holds a connection for its whole handler, so the pool
# has to be at least as wide as the worker threads that can run at once.
POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "20"))
MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "20"))

if DATABASE_URL:
    engine = create_engine(
        DATABASE_URL,
        pool_size=POOL_SIZE,
        max_overflow=MAX_OVERFLOW,
        pool_pre_ping=True,
        pool_recycle=300,  # Supabase's pooler drops idle connections
        pool_timeout=30,
        connect_args={"connect_timeout": 10},
    )
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
else:
    engine = None
    SessionLocal = None

# Declarative base for models
Base = declarative_base()


def get_db():
    """Request-scoped session. A Session is not thread-safe, so never share one."""
    if SessionLocal is None:
        raise HTTPException(status_code=503, detail="Database is not available")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
