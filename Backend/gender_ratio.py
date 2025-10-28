import os
import sys
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from collections import Counter

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

from app.models.user_model import User

# Qdrant setup
QDRANT_HOST = os.getenv("QDRANT_HOST")
QDRANT_PORT = os.getenv("QDRANT_PORT")
QDRANT_URL = f"http://{QDRANT_HOST}:{QDRANT_PORT}" if QDRANT_HOST else None
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION", "find_my_date")

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL")

def get_all_emails_from_qdrant():
    """Retrieve all user emails from Qdrant collection"""
    print(f"Connecting to Qdrant at {QDRANT_URL}...")
    client = QdrantClient(
        url=QDRANT_URL,
    )
    
    print(f"Fetching all points from collection: {COLLECTION_NAME}")
    
    # Scroll through all points in the collection
    all_points = []
    offset = None
    
    while True:
        response = client.scroll(
            collection_name=COLLECTION_NAME,
            limit=100,
            with_payload=True,
            with_vectors=False,
            offset=offset
        )
        
        points, next_offset = response
        all_points.extend(points)
        
        if next_offset is None:
            break
        offset = next_offset
    
    print(f"Found {len(all_points)} points in Qdrant")
    
    # Extract emails from payload
    emails = []
    for point in all_points:
        if point.payload and 'email' in point.payload:
            emails.append(point.payload['email'])
    
    print(f"Extracted {len(emails)} emails")
    return emails

bisexual = 0

def get_gender_from_database(emails):
    """Look up gender for each email in PostgreSQL"""
    print("\nConnecting to PostgreSQL database...")
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    global bisexual
    
    gender_counts = Counter()
    users_found = 0
    users_not_found = []
    
    print("Looking up gender for each user...")
    for email in emails:
        user = db.query(User).filter(User.email == email).first()
        if user and user.orientation.lower() == 'bisexual':
            bisexual += 1
        if user:
            gender_counts[user.gender] += 1
            users_found += 1
        else:
            users_not_found.append(email)
    
    db.close()
    
    print(f"\nUsers found in database: {users_found}/{len(emails)}")
    if users_not_found:
        print(f"Users not found: {len(users_not_found)}")
        print("Emails not found:", users_not_found[:5], "..." if len(users_not_found) > 5 else "")
    
    return gender_counts

def display_gender_ratio(gender_counts):
    """Display gender statistics"""
    total = sum(gender_counts.values())
    global bisexual
    if total == 0:
        print("\nNo users found!")
        return
    
    print("\n" + "="*50)
    print("GENDER RATIO ANALYSIS")
    print("="*50)
    
    print(f"\nTotal users: {total}")
    # print(f' Bisexual users: {bisexual}')
    print("\nGender breakdown:")
    
    for gender, count in sorted(gender_counts.items()):
        percentage = (count / total) * 100
        gender_label = {
            'M': 'Male',
            'W': 'Female/Women',
            'F': 'Female'
        }.get(gender, gender)
        print(f"  {gender_label} ({gender}): {count} ({percentage:.1f}%)")
    
    # Calculate male to female ratio
    male_count = gender_counts.get('M', 0)
    female_count = gender_counts.get('W', 0) + gender_counts.get('F', 0)
    
    if female_count > 0:
        ratio = male_count / female_count
        print(f"\nMale to Female ratio: {ratio:.2f}:1")
        print(f"  ({male_count} males : {female_count} females)")
    elif male_count > 0:
        print(f"\nAll users are male ({male_count})")
    
    print("="*50)

def main():
    try:
        # Get all emails from Qdrant
        emails = get_all_emails_from_qdrant()
        
        if not emails:
            print("No emails found in Qdrant collection!")
            return
        
        # Look up gender in database
        gender_counts = get_gender_from_database(emails)
        
        # Display results
        display_gender_ratio(gender_counts)
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
