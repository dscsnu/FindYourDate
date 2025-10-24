from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

import os

load_dotenv()

DATABASE_URL = os.getenv("SUPABASE_DB_URL")  # full postgres:// URL
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
