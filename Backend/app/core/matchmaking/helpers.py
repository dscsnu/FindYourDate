from sqlalchemy.orm import Session
from db.database import SessionLocal
from models import User, MatchHistory
from typing import List, Dict, Any


def decompose_pools(matches: list, unmatched: list) -> dict:
    straight_men, straight_women = [], []
    gay_men, lesbian_women = [], []

    for a, b, _ in matches:
        if a.gender != b.gender:
            m, w = (a, b) if a.gender == "M" else (b, a)
            straight_men.append(m)
            straight_women.append(w)
        elif a.gender == "M":
            gay_men.extend([a, b])
        elif a.gender == "W":
            lesbian_women.extend([a, b])

    for p in unmatched:
        if p.gender == "M":
            if p.orientation in ("straight", "bi"):
                straight_men.append(p)
            if p.orientation in ("gay"):
                gay_men.append(p)
        elif p.gender == "W":
            if p.orientation in ("straight", "bi"):
                straight_women.append(p)
            if p.orientation in ("lesbian"):
                lesbian_women.append(p)

    return {
        "straight_men": straight_men,
        "straight_women": straight_women,
        "gay_men": gay_men,
        "lesbian_women": lesbian_women,
    }

def push_matches_to_db(session: Session, matches: Dict[int, int], algo_name: str):
    for user_id, partner_id in matches.items():
        entry = MatchHistory(
            user_id=user_id,
            matched_user_id=partner_id,
            algorithm=algo_name
        )
        session.add(entry)
    session.commit()


def clean_straight_matches_after_cosine(users: List[User], cosine_results: Dict[int, List[int]]):
    valid_pairs = {}

    # Build a lookup for quick access
    user_lookup = {u.id: u for u in users}

    for uid, candidate_ids in cosine_results.items():
        u = user_lookup[uid]
        valid_list = []
        for cid in candidate_ids:
            c = user_lookup[cid]
            # Only remove if straight user says no to non-straight match
            if (
                u.orientation.lower() == "straight"
                and not u.accept_non_straight
                and c.orientation.lower() != "straight"
            ):
                continue
            valid_list.append(cid)
        valid_pairs[uid] = valid_list

    return valid_pairs
