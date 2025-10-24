from sqlalchemy.orm import Session
from app.models.user import User
from app.models.match_history import MatchHistory
from app.core.matchmaking.person import Person
from app.core.matchmaking.algorithms import (
    greedy_global_minheap,
    hungarian,
    min_weight_graph_matching
)
from typing import List, Dict
import random
from helpers import decompose_pools
from similarity import cosine_similarity, valid_partner

def load_people(db: Session) -> List[Person]:
    users = db.query(User).all()
    return [Person(u) for u in users]

def assign_preferences(people: list):
    for a in people:
        scored_partners = []
        for b in people:
            if not valid_partner(a, b):
                continue
            sim = cosine_similarity(np.array(a.embedding), np.array(b.embedding))
            scored_partners.append((b, sim))

        a.preferences = [b for b, _ in sorted(scored_partners, key=lambda x: x[1], reverse=True)]

def store_matches(db: Session, matches: list, algo="hybrid"):
    for a, b, cost in matches:
        db.add(
            MatchHistory(
                user_id=a.db_id,
                matched_user_id=b.db_id,
                similarity_score=cost,
                algorithm=algo,
            )
        )
    db.commit()


def execute_full_match_pipeline(db: Session):
    people = load_people(db)
    if not people:
        print("No users found.")
        return 0

    print(f"Loaded {len(people)} users. Assigning preferences...")
    assign_preferences(people)

    # --- Stage 1: Greedy Matching ---
    print("\nRunning Stage 1: Greedy Matching...")
    matches, unmatched = greedy_global_minheap(people)
    print(f"Greedy formed {len(matches)} pairs, {len(unmatched)} unmatched remain.")

    # --- Stage 2: Decompose ALL (matched + unmatched) ---
    print("\nRunning Stage 2: Decomposing everyone into gender/orientation pools...")
    pools = decompose_pools(matches, unmatched)
    print(f"Straight men: {len(pools['straight_men'])}, Straight women: {len(pools['straight_women'])}")
    print(f"Gay men: {len(pools['gay_men'])}, Lesbian women: {len(pools['lesbian_women'])}")

    # --- Stage 3: Re-optimization ---
    print("\nRunning Stage 3: Re-optimization with Hungarian + MWPM...")
    hetero_matches = hungarian(pools["straight_men"], pools["straight_women"])
    gay_matches = min_weight_graph_matching(pools["gay_men"])
    lesbian_matches = min_weight_graph_matching(pools["lesbian_women"])

    final_matches = hetero_matches + gay_matches + lesbian_matches

    # --- Stage 4: Store in DB ---
    print(f"\nStoring {len(final_matches)} final matches in database...")
    store_matches(db, final_matches)

    print("Matchmaking pipeline complete.")
    print(f"Total final matches: {len(final_matches)}")

    return len(final_matches)