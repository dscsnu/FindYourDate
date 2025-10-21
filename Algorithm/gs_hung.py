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
        # If new_person not in prefs, cannot prefer them
        if new_person not in prefs:
            return False
        # If current_person not in prefs (including None), treat new_person as preferred
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
        # Skip this pair; try the next preference
        # (guard against infinite recursion if proposer has exhausted list)
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
    """Ensure all pairs are stored as (man, woman) and exclude None matches."""
    normalized = set()
    for a, b in pairs:
        if b is None:
            continue
        if a.startswith("M"):
            normalized.add((a, b))
        else:
            normalized.add((b, a))
    return normalized


# ============================================================
#                HUNGARIAN ALGORITHM (robust to unequal sizes)
# ============================================================

def hungarian_match(men_subset, women_subset, all_people):
    """
    Find optimal pairings (min total dissatisfaction) using Hungarian algorithm.
    This handles unequal leftover sizes by padding with dummy nodes (large cost),
    then returns only real-real matches.
    """
    if not men_subset and not women_subset:
        return []

    m_count = len(men_subset)
    w_count = len(women_subset)
    n = max(m_count, w_count)

    # pad lists so they're both length n (with None placeholders)
    men_padded = list(men_subset) + [None] * (n - m_count)
    women_padded = list(women_subset) + [None] * (n - w_count)

    LARGE = 10**6
    cost = np.full((n, n), LARGE, dtype=float)

    for i, m_name in enumerate(men_padded):
        for j, w_name in enumerate(women_padded):
            if m_name is None or w_name is None:
                # pairing with dummy has very large cost to discourage it
                cost[i, j] = LARGE
            else:
                m_obj = all_people[m_name]
                w_obj = all_people[w_name]
                # use +1 indexing implicitly but not required; keep as 0-based sum
                try:
                    rank_m = m_obj.preferences.index(w_obj)
                except ValueError:
                    rank_m = len(all_people)  # penalty if missing
                try:
                    rank_w = w_obj.preferences.index(m_obj)
                except ValueError:
                    rank_w = len(all_people)
                cost[i, j] = rank_m + rank_w

    row_ind, col_ind = linear_sum_assignment(cost)

    matches = []
    for i, j in zip(row_ind, col_ind):
        if i < m_count and j < w_count:
            m_name = men_padded[i]
            w_name = women_padded[j]
            # double-check not None
            if m_name is not None and w_name is not None and cost[i, j] < LARGE:
                matches.append((m_name, w_name))

    return matches


# ============================================================
#                 DISSATISFACTION METRICS
# ============================================================

def dissatisfaction_stats(pairs, all_people):
    """Return mean, median, and mode of dissatisfaction for both men and women."""
    men_dissat, women_dissat = [], []

    for m, w in pairs:
        m_obj, w_obj = all_people[m], all_people[w]
        # safe index usage (should always exist in your setup)
        try:
            men_dissat.append(m_obj.preferences.index(w_obj) + 1)
        except ValueError:
            men_dissat.append(len(all_people))  # fallback large rank
        try:
            women_dissat.append(w_obj.preferences.index(m_obj) + 1)
        except ValueError:
            women_dissat.append(len(all_people))

    def safe_mode(lst):
        try:
            return mode(lst)
        except StatisticsError:
            return "No unique mode"

    return {
        "men": {
            "mean": np.mean(men_dissat) if men_dissat else float("nan"),
            "median": median(men_dissat) if men_dissat else float("nan"),
            "mode": safe_mode(men_dissat) if men_dissat else None
        },
        "women": {
            "mean": np.mean(women_dissat) if women_dissat else float("nan"),
            "median": median(women_dissat) if women_dissat else float("nan"),
            "mode": safe_mode(women_dissat) if women_dissat else None
        }
    }


def satisfaction_threshold_analysis(pairs, all_people, threshold=10):
    """Count how many men/women got a partner within their top N choices."""
    men_below = women_below = 0
    total = len(pairs)

    if total == 0:
        return {
            "threshold": threshold,
            "men": {"count": 0, "percent": 0.0},
            "women": {"count": 0, "percent": 0.0}
        }

    for m, w in pairs:
        m_obj, w_obj = all_people[m], all_people[w]
        try:
            m_rank = m_obj.preferences.index(w_obj) + 1
        except ValueError:
            m_rank = len(all_people)
        try:
            w_rank = w_obj.preferences.index(m_obj) + 1
        except ValueError:
            w_rank = len(all_people)
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
#                 STABILITY MEASUREMENT
# ============================================================

def measure_stability(pairs, all_people):
    """
    Measure stability based on individuals involved in blocking pairs.
    A blocking pair is (m, w) where both prefer each other over their current match.
    The function returns blocking-pair count and how many individuals are involved in >=1 blocking pair.
    """
    # Build match mapping (name->partner_name or None)
    match_dict = {}
    for a, b in pairs:
        match_dict[a] = b
        match_dict[b] = a

    # Ensure everyone is represented (unmatched => None)
    for name in all_people.keys():
        if name not in match_dict:
            match_dict[name] = None

    men = [p for p in all_people.values() if p.gender == "M"]
    women = [p for p in all_people.values() if p.gender == "W"]

    blocking_pairs = []
    involved_individuals = set()
    total_possible_pairs = len(men) * len(women) if men and women else 0

    for m in men:
        m_match_name = match_dict.get(m.name)
        m_match_obj = all_people[m_match_name] if m_match_name in all_people else None
        for w in women:
            w_match_name = match_dict.get(w.name)
            w_match_obj = all_people[w_match_name] if w_match_name in all_people else None

            # check if (m,w) block: both prefer each other over their current matches
            if m.prefers(w, m_match_obj) and w.prefers(m, w_match_obj):
                blocking_pairs.append((m.name, w.name))
                involved_individuals.add(m.name)
                involved_individuals.add(w.name)

    total_individuals = len(all_people)
    num_blocking_pairs = len(blocking_pairs)
    num_involved = len(involved_individuals)

    return {
        "blocking_pairs": num_blocking_pairs,
        "individuals_involved": num_involved,
        "individuals_percent": (num_involved / total_individuals) * 100 if total_individuals else 0.0,
        "pair_percent": (num_blocking_pairs / total_possible_pairs) * 100 if total_possible_pairs else 0.0
    }


# ============================================================
#                    MAIN TEST FUNCTION
# ============================================================

def test_matching(num_pairs=6):
    """Run full GS + Hungarian hybrid test."""
    # --- Create population ---
    men = [Person(f"M{i+1}", "M", []) for i in range(30)]
    women = [Person(f"W{i+1}", "W", []) for i in range(num_pairs)]

    # Randomized preferences (full lists)
    for m in men:
        m.preferences = random.sample(women, len(women))
    for w in women:
        w.preferences = random.sample(men, len(men))

    all_people = {p.name: p for p in men + women}

    # --- GS from both sides ---
    matches_men = gale_shapley(men, women)
    reset_all(men + women)
    matches_women = gale_shapley(women, men)

    # --- Identify common pairs (exclude None matches) ---
    men_norm = normalize(matches_men)
    women_norm = normalize(matches_women)
    common_pairs = men_norm.intersection(women_norm)

    # --- Identify leftovers (names) ---
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
    threshold_data = satisfaction_threshold_analysis(final_pairs, all_people, threshold=20)

    # --- Display results ---
    print(f"\n=== Final Combined Results (GS + Hungarian) ===")
    print(f"Men:   Mean: {stats['men']['mean']:.2f}, Median: {stats['men']['median']}, Mode: {stats['men']['mode']}")
    print(f"Women: Mean: {stats['women']['mean']:.2f}, Median: {stats['women']['median']}, Mode: {stats['women']['mode']}")
    print(f"\nWithin top {threshold_data['threshold']} choices:")
    print(f"Men:   {threshold_data['men']['count']}/{len(final_pairs)} ({threshold_data['men']['percent']:.2f}%)")
    print(f"Women: {threshold_data['women']['count']}/{len(final_pairs)} ({threshold_data['women']['percent']:.2f}%)")

    # --- Measure stability ---
    stability = measure_stability(final_pairs, all_people)
    print(f"\n--- Stability Stats ---")
    print(f"Blocking pairs: {stability['blocking_pairs']} "
          f"({stability['pair_percent']:.6f}% of all possible pairs)")
    print(f"Individuals involved: {stability['individuals_involved']} "
          f"({stability['individuals_percent']:.2f}% of population)")
    print("=" * 65)


# ============================================================
#                       EXECUTION
# ============================================================

if __name__ == "__main__":
    for i in range(5):
        print(f"\n### Test Run {i+1} ###")
        random.seed()
        test_matching(num_pairs=25)
