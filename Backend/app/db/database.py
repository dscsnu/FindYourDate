from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

import os

load_dotenv()

DATABASE_URL = os.getenv("SUPABASE_DB_URL")  # full postgres:// URL

# Create engine with connection pooling disabled for better error handling
if DATABASE_URL:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,  # Verify connections before using them
        connect_args={"connect_timeout": 10}  # 10 second timeout
    )
    SessionLocal = sessionmaker(bind=engine)
else:
    engine = None
    SessionLocal = None

# Declarative base for models
Base = declarative_base()
