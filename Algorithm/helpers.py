from sqlalchemy.orm import Session
from db.database import SessionLocal
from models import User, MatchHistory
from typing import List, Dict


def split_user_groups(users: List[User]) -> Dict[str, List[User]]:
    male_pool = []
    female_pool = []
    gay_pool = []
    lesbian_pool = []

    for u in users:
        gender = u.gender.lower()
        orient = u.orientation.lower()

        # Straight
        if orient == "straight":
            if gender == "male":
                male_pool.append(u)
            elif gender == "female":
                female_pool.append(u)

        # Gay / Lesbian
        elif orient == "gay":
            if gender == "male":
                gay_pool.append(u)
            elif gender == "female":
                lesbian_pool.append(u)

        # Bisexual
        elif orient == "bi" or orient == "bisexual":
            # Add to both male/female straight pools
            if gender == "male":
                male_pool.append(u)
                gay_pool.append(u)
            elif gender == "female":
                female_pool.append(u)
                lesbian_pool.append(u)
                female_pool.append(u)

    return {
        "male_pool": male_pool,
        "female_pool": female_pool,
        "gay_pool": gay_pool,
        "lesbian_pool": lesbian_pool
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