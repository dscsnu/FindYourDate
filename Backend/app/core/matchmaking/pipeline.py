from sqlalchemy.orm import Session
from app.models.user_model import User
from app.models.match_history import MatchHistory
from app.core.matchmaking.person import Person
from app.core.matchmaking.algorithms import (
    greedy_global_minheap,
    hungarian,
    min_weight_graph_matching
)
from app.db.qdrant_client import qdrant, QDRANT_COLLECTION
from typing import List, Dict
import json
from datetime import datetime
import random
from .helpers import decompose_pools
from .similarity import cosine_similarity, valid_partner
import numpy as np

def get_all_emails_from_qdrant() -> List[str]:
    """
    Step 1: Get all emails from Qdrant vector database
    """
    print("Step 1: Fetching all emails from Qdrant vector database...")
    
    # Scroll through all points in the collection
    all_points = []
    offset = None
    
    while True:
        response = qdrant.scroll(
            collection_name=QDRANT_COLLECTION,
            limit=100,
            offset=offset,
            with_payload=True,
            with_vectors=False  # We don't need vectors yet, just emails
        )
        
        points, next_offset = response
        all_points.extend(points)
        
        if next_offset is None:
            break
        offset = next_offset
    
    emails = [point.payload.get("email") for point in all_points if point.payload.get("email")]
    print(f"Found {len(emails)} emails in Qdrant")
    return emails

def load_people_from_emails(db: Session, emails: List[str]) -> List[Person]:
    """
    Step 2: Get user data from PostgreSQL for the emails found in Qdrant
    """
    print("Step 2: Fetching user data from PostgreSQL...")
    users = db.query(User).filter(User.email.in_(emails)).all()
    print(f"Found {len(users)} users in PostgreSQL")
    
    # Create Person objects (embeddings are fetched in Person.__init__)
    people = []
    for user in users:
        person = Person(user)
        if person.embedding is None:
            print(f"Warning: No embedding found for {user.email}, skipping...")
            continue
        people.append(person)
    
    print(f"Loaded {len(people)} people with valid embeddings")
    return people

def assign_preferences(people: list):
    """
    Step 3: Check valid pairs and run cosine similarity
    """
    print("Step 3: Checking valid pairs and computing cosine similarity...")
    valid_pairs_count = 0
    
    for a in people:
        scored_partners = []
        for b in people:
            # Check if valid pair
            if not valid_partner(a, b):
                continue
            
            valid_pairs_count += 1

            # Run cosine similarity
            sim = cosine_similarity(np.array(a.embedding), np.array(b.embedding))
            scored_partners.append((b, sim))
            a.similarity_scores[b] = sim

        # Sort by similarity (highest first)
        a.preferences = [b for b, _ in sorted(scored_partners, key=lambda x: x[1], reverse=True)]
        if a.email == "sj993@snu.edu.in":
            print(f"Preference List: {[ (p.email, a.similarity_scores[p]) for p in a.preferences]}")
    print(f"Computed {valid_pairs_count} valid pair similarities")

def store_matches(db: Session, matches: list, algo="hybrid"):
    """
    Step 5a: Store matches in PostgreSQL database
    """
    print(f"Step 5a: Storing {len(matches)} matches in PostgreSQL...")
    for a, b, cost in matches:
        # Convert numpy types to Python native types for PostgreSQL
        similarity_score = float(1 - cost)  # Convert cost back to similarity
        user_id = int(a.db_id)
        matched_user_id = int(b.db_id)
        
        # Store both directions of the match
        db.add(
            MatchHistory(
                user_id=user_id,
                matched_user_id=matched_user_id,
                similarity_score=similarity_score,
                algorithm_used=algo,
            )
        )
        db.add(
            MatchHistory(
                user_id=matched_user_id,
                matched_user_id=user_id,
                similarity_score=similarity_score,
                algorithm_used=algo,
            )
        )
    db.commit()
    print("Matches stored in database")

def export_matches_to_json(matches: list, filename: str = None):
    """
    Step 5b: Export matches to JSON file
    """
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"matches_{timestamp}.json"
    
    print(f"Step 5b: Exporting matches to {filename}...")
    
    matches_data = []
    for a, b, cost in matches:
        similarity_score = 1 - cost  # Convert cost back to similarity
        match_entry = {
            "user_1": {
                "id": a.db_id,
                "name": a.name,
                "email": a.email,
                "gender": a.gender,
                "orientation": a.orientation,
                "age": a.age
            },
            "user_2": {
                "id": b.db_id,
                "name": b.name,
                "email": b.email,
                "gender": b.gender,
                "orientation": b.orientation,
                "age": b.age
            },
            "similarity_score": float(similarity_score),
            "cost": float(cost)
        }
        matches_data.append(match_entry)
    
    export_data = {
        "timestamp": datetime.now().isoformat(),
        "total_matches": len(matches),
        "matches": matches_data
    }
    
    with open(filename, 'w') as f:
        json.dump(export_data, f, indent=2)
    
    print(f"Matches exported to {filename}")
    return filename

def execute_full_match_pipeline(db: Session, export_json: bool = True):
    """
    Complete matchmaking pipeline:
    1. Get all emails from Qdrant vector DB
    2. Get user data from PostgreSQL
    3. Check valid pairs and run cosine similarity
    4. Run matching algorithms
    5. Store matches in DB and export to JSON
    """
    print("="*60)
    print("STARTING MATCHMAKING PIPELINE")
    print("="*60)
    
    # Step 1: Get emails from Qdrant
    emails = get_all_emails_from_qdrant()
    if not emails:
        print("No emails found in Qdrant vector database.")
        return 0
    
    # Step 2: Get user data from PostgreSQL
    people = load_people_from_emails(db, emails)
    if not people:
        print("No valid users found.")
        return 0

    # Step 3: Check valid pairs and compute cosine similarity
    assign_preferences(people)

    # Step 4: Run matching algorithms
    print("\nStep 4: Running matching algorithms...")
    
    # --- Stage 1: Greedy Matching ---
    print("\n  Stage 4.1: Greedy Matching...")
    matches, unmatched = greedy_global_minheap(people)
    print(f"  Greedy formed {len(matches)} pairs, {len(unmatched)} unmatched remain.")

    # --- Stage 2: Decompose ALL (matched + unmatched) ---
    print("\n  Stage 4.2: Decomposing into gender/orientation pools...")
    pools = decompose_pools(matches, unmatched)
    print(f"  Straight men: {len(pools['straight_men'])}, Straight women: {len(pools['straight_women'])}")
    print(f"  Gay men: {len(pools['gay_men'])}, Lesbian women: {len(pools['lesbian_women'])}")

    # --- Stage 3: Re-optimization ---
    print("\n  Stage 4.3: Re-optimization with Hungarian + MWPM...")
    hetero_matches = hungarian(pools["straight_men"], pools["straight_women"])
    gay_matches = min_weight_graph_matching(pools["gay_men"])
    lesbian_matches = min_weight_graph_matching(pools["lesbian_women"])

    final_matches = hetero_matches + gay_matches + lesbian_matches

    # Step 5: Store matches
    print(f"\nStep 5: Storing {len(final_matches)} final matches...")
    
    
    # Export to JSON
    json_file = None
    if export_json:
        json_file = export_matches_to_json(final_matches)
    store_matches(db, final_matches)
    print("\n" + "="*60)
    print("MATCHMAKING PIPELINE COMPLETE")
    print("="*60)
    print(f"Total final matches: {len(final_matches)}")
    if json_file:
        print(f"Results exported to: {json_file}")
    print("="*60)

    return len(final_matches)