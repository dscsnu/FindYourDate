"""
Simple script to create all database tables.
Run this after you verify your database connection is working.
"""

from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Import models and database setup
from app.db.database import engine, Base
from app.models.user_model import User
from app.models.match_history import MatchHistory
from app.models.match_score import MatchScore

def create_tables():
    """Create all tables in the database."""
    try:
        print("Creating database tables...")
        print(f"Database URL: {os.getenv('SUPABASE_DB_URL')[:50]}...")
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        print("✅ Successfully created all tables!")
        print("\nTables created:")
        print("  - users")
        print("  - match_history")
        print("  - match_scores")
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        print("\nPlease check:")
        print("  1. Your internet connection")
        print("  2. Your Supabase project is active")
        print("  3. The database URL in .env is correct")
        return False
    
    return True

if __name__ == "__main__":
    create_tables()
