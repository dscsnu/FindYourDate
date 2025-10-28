"""
Run the complete matchmaking pipeline

This script:
1. Gets all emails from Qdrant vector DB
2. Gets user data from PostgreSQL
3. Checks valid pairs and runs cosine similarity
4. Runs matching algorithms (Greedy → Hungarian/MWPM)
5. Stores matches in DB and exports to JSON
"""

import sys
from pathlib import Path

# Add the Backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.db.database import SessionLocal
from app.core.matchmaking.pipeline import execute_full_match_pipeline

def main():
    print("Initializing database session...")
    db = SessionLocal()
    
    try:
        # Run the complete pipeline
        num_matches = execute_full_match_pipeline(db, export_json=True)
        print(f"\n✅ Pipeline completed successfully!")
        print(f"📊 Total matches created: {num_matches}")
        
    except Exception as e:
        print(f"\n❌ Error during matchmaking pipeline: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        db.close()
        print("\nDatabase session closed.")

if __name__ == "__main__":
    main()
