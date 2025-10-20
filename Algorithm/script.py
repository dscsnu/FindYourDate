import random
import json
import os
import numpy as np
from scipy.optimize import linear_sum_assignment
from statistics import median, mode, StatisticsError


# ============================================================
#                      CONFIGURATION
# ============================================================

MATCHES_FILE = "matches.json"


# ============================================================
#                      PERSON CLASS
# ============================================================

class Person:
    """Represents an individual with preferences for potential partners."""
    def __init__(self, name, gender, preferences):
        self.name = name
        self.gender = gender
        self.preferences = preferences  # list of Person objects
        self.current_match = None
        self.next_proposal_index = 0

    def get_next_preference(self):
        """Return the next person this individual will propose to."""
        if self.next_proposal_index < len(self.preferences):
            person = self.preferences[self.next_proposal_index]
            self.next_proposal_index += 1
            return person
        return None

    def prefers(self, new_person, current_person):
        """Check if this person prefers 'new_person' over 'current_person'."""
        prefs = self.preferences
        if new_person not in prefs:
            return False
        if current_person not in prefs:
            return True
        return prefs.index(new_person) < prefs.index(current_person)


# ============================================================
#                GALE-SHAPLEY (STABLE MARRIAGE)
# ============================================================

def propose(proposer, free_proposers):
    """One round of proposals in Gale-Shapley."""
    receiver = proposer.get_next_preference()
    if not receiver:
        return

    # Load past pairs to skip if already matched before
    if os.path.exists(MATCHES_FILE):
        with open(MATCHES_FILE, "r") as f:
            try:
                past_pairs = json.load(f)
            except json.JSONDecodeError:
                past_pairs = []
    else:
        past_pairs = []

    pair = [proposer.name, receiver.name]
    if pair in past_pairs:
        print(f"Skipping {pair}")
        return propose(proposer, free_proposers)

    # Proposal logic
    if receiver.current_match is None:
        receiver.current_match = proposer
        proposer.current_match = receiver
        return

    current = receiver.current_match
    if receiver.prefers(proposer, current):
        receiver.current_match = proposer
        proposer.current_match = receiver
        current.current_match = None
        free_proposers.append(current)
    else:
        free_proposers.append(proposer)


def gale_shapley(proposers, receivers):
    """Run Gale-Shapley algorithm."""
    free_proposers = proposers[:]
    while free_proposers:
        new_free = []
        for proposer in free_proposers:
            propose(proposer, new_free)
        free_proposers = new_free
    return [(p.name, p.current_match.name if p.current_match else None) for p in proposers]


def reset_all(people):
    """Reset match and proposal index for all people."""
    for p in people:
        p.current_match = None
        p.next_proposal_index = 0


def normalize(pairs):
    """Ensure all pairs are stored as (man, woman)."""
    normalized = set()
    for a, b in pairs:
        if a.startswith("M"):
            normalized.add((a, b))
        else:
            normalized.add((b, a))
    return normalized


# ============================================================
#                HUNGARIAN ALGORITHM
# ============================================================

def hungarian_match(men_subset, women_subset, all_people):
    """Find optimal pairings (min total dissatisfaction) using Hungarian algorithm."""
    if not men_subset or not women_subset:
        return []

    size = min(len(men_subset), len(women_subset))
    men_subset, women_subset = men_subset[:size], women_subset[:size]

    cost = np.zeros((size, size))
    for i, m_name in enumerate(men_subset):
        m_obj = all_people[m_name]
        for j, w_name in enumerate(women_subset):
            w_obj = all_people[w_name]
            cost[i, j] = m_obj.preferences.index(w_obj) + w_obj.preferences.index(m_obj)

    row_ind, col_ind = linear_sum_assignment(cost)
    return [(men_subset[i], women_subset[j]) for i, j in zip(row_ind, col_ind)]


# ============================================================
#                 DISSATISFACTION METRICS
# ============================================================

def dissatisfaction_stats(pairs, all_people):
    """Return mean, median, and mode of dissatisfaction for both men and women."""
    men_dissat, women_dissat = [], []

    for m, w in pairs:
        m_obj, w_obj = all_people[m], all_people[w]
        men_dissat.append(m_obj.preferences.index(w_obj) + 1)
        women_dissat.append(w_obj.preferences.index(m_obj) + 1)

    def safe_mode(lst):
        try:
            return mode(lst)
        except StatisticsError:
            return "No unique mode"

    return {
        "men": {
            "mean": np.mean(men_dissat),
            "median": median(men_dissat),
            "mode": safe_mode(men_dissat)
        },
        "women": {
            "mean": np.mean(women_dissat),
            "median": median(women_dissat),
            "mode": safe_mode(women_dissat)
        }
    }


def satisfaction_threshold_analysis(pairs, all_people, threshold=10):
    """Count how many men/women got a partner within their top N choices."""
    men_below = women_below = 0
    total = len(pairs)

    for m, w in pairs:
        m_obj, w_obj = all_people[m], all_people[w]
        m_rank = m_obj.preferences.index(w_obj) + 1
        w_rank = w_obj.preferences.index(m_obj) + 1
        if m_rank <= threshold:
            men_below += 1
        if w_rank <= threshold:
            women_below += 1

    return {
        "threshold": threshold,
        "men": {"count": men_below, "percent": (men_below / total) * 100},
        "women": {"count": women_below, "percent": (women_below / total) * 100}
    }


# ============================================================
#                    MAIN TEST FUNCTION
# ============================================================

def test_matching(num_pairs=6):
    """Run full GS + Hungarian hybrid test."""
    # --- Create population ---
    men = [Person(f"M{i+1}", "M", []) for i in range(num_pairs)]
    women = [Person(f"W{i+1}", "W", []) for i in range(num_pairs)]

    # Randomized preferences
    for m in men:
        m.preferences = random.sample(women, len(women))
    for w in women:
        w.preferences = random.sample(men, len(men))

    all_people = {p.name: p for p in men + women}

    # --- GS from both sides ---
    matches_men = gale_shapley(men, women)
    reset_all(men + women)
    matches_women = gale_shapley(women, men)

    # --- Identify common pairs ---
    men_norm = normalize(matches_men)
    women_norm = normalize(matches_women)
    common_pairs = men_norm.intersection(women_norm)

    # --- Identify leftovers ---
    men_in_common = {m for m, _ in common_pairs}
    women_in_common = {w for _, w in common_pairs}
    leftover_men = [m.name for m in men if m.name not in men_in_common]
    leftover_women = [w.name for w in women if w.name not in women_in_common]

    # --- Run Hungarian on leftovers ---
    hungarian_pairs = hungarian_match(leftover_men, leftover_women, all_people)

    # --- Combine results ---
    final_pairs = list(common_pairs) + hungarian_pairs

    # --- Calculate statistics ---
    stats = dissatisfaction_stats(final_pairs, all_people)
    threshold_data = satisfaction_threshold_analysis(final_pairs, all_people, threshold = 20)

    # --- Display results ---
    print(f"\n=== Final Combined Results (GS + Hungarian) ===")
    print(f"Men: Mean: {stats['men']['mean']:.2f}, Median: {stats['men']['median']}, Mode: {stats['men']['mode']}")
    print(f"Women: Mean: {stats['women']['mean']:.2f}, Median: {stats['women']['median']}, Mode: {stats['women']['mode']}")
    print(f"\nWithin top {threshold_data['threshold']} choices:")
    print(f"Men:   {threshold_data['men']['count']}/{len(final_pairs)} ({threshold_data['men']['percent']:.2f}%)")
    print(f"Women: {threshold_data['women']['count']}/{len(final_pairs)} ({threshold_data['women']['percent']:.2f}%)")
    print("=" * 65)


# ============================================================
#                       EXECUTION
# ============================================================

if __name__ == "__main__":
    for i in range(10):
        print(f"\n### Test Run {i+1} ###")
        random.seed()
        test_matching(num_pairs=500)
