import random
import json
import os
import numpy as np
from scipy.optimize import linear_sum_assignment
from statistics import median, mode, StatisticsError

MATCHES_FILE = "matches.json"

# ============================================================
#                      PERSON CLASS
# ============================================================

class Person:
    def __init__(self, name, gender, preferences):
        self.name = name
        self.gender = gender
        self.preferences = preferences  # list of Person objects
        self.current_match = None
        self.next_proposal_index = 0

    def get_next_preference(self):
        if self.next_proposal_index < len(self.preferences):
            person = self.preferences[self.next_proposal_index]
            self.next_proposal_index += 1
            return person
        return None

    def prefers(self, new_person, current_person):
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
    receiver = proposer.get_next_preference()
    if not receiver:
        return

    # Skip pairs from file
    past_pairs = []
    if os.path.exists(MATCHES_FILE):
        with open(MATCHES_FILE, "r") as f:
            try:
                past_pairs = json.load(f)
            except json.JSONDecodeError:
                pass

    pair = (proposer.name, receiver.name)
    if pair in past_pairs:
        return propose(proposer, free_proposers)

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
    free_proposers = proposers[:]
    while free_proposers:
        new_free = []
        for proposer in free_proposers:
            propose(proposer, new_free)
        free_proposers = new_free
    return [(p, p.current_match) for p in proposers if p.current_match]


def reset_all(people):
    for p in people:
        p.current_match = None
        p.next_proposal_index = 0


def normalize(pairs):
    """Ensure all pairs are (man, woman) tuples using Person objects."""
    normalized = set()
    for a, b in pairs:
        if not b:
            continue
        if a.gender == "M":
            normalized.add((a, b))
        else:
            normalized.add((b, a))
    return normalized


# ============================================================
#                HUNGARIAN ALGORITHM
# ============================================================

def hungarian(men_subset, women_subset, all_people):
    if not men_subset or not women_subset:
        return []

    m_count, w_count = len(men_subset), len(women_subset)
    n = max(m_count, w_count)
    men_padded = men_subset + [None] * (n - m_count)
    women_padded = women_subset + [None] * (n - w_count)

    LARGE = 10**6
    cost = np.full((n, n), LARGE, dtype=float)

    for i, m_obj in enumerate(men_padded):
        for j, w_obj in enumerate(women_padded):
            if not m_obj or not w_obj:
                continue
            try:
                rank_m = m_obj.preferences.index(w_obj)
            except ValueError:
                rank_m = len(all_people)
            try:
                rank_w = w_obj.preferences.index(m_obj)
            except ValueError:
                rank_w = len(all_people)
            cost[i, j] = rank_m + rank_w

    row_ind, col_ind = linear_sum_assignment(cost)
    matches = []
    for i, j in zip(row_ind, col_ind):
        if i < m_count and j < w_count:
            m_obj, w_obj = men_padded[i], women_padded[j]
            if m_obj and w_obj and cost[i, j] < LARGE:
                matches.append((m_obj, w_obj))
    return matches


# ============================================================
#                 DISSATISFACTION METRICS
# ============================================================

def dissatisfaction_stats(pairs, all_people):
    men_dissat, women_dissat = [], []

    for m_obj, w_obj in pairs:
        men_dissat.append(
            m_obj.preferences.index(w_obj) + 1 if w_obj in m_obj.preferences else len(all_people)
        )
        women_dissat.append(
            w_obj.preferences.index(m_obj) + 1 if m_obj in w_obj.preferences else len(all_people)
        )

    def safe_mode(lst):
        try:
            return mode(lst)
        except StatisticsError:
            return "No unique mode"

    return {
        "men": {"mean": np.mean(men_dissat), "median": median(men_dissat), "mode": safe_mode(men_dissat)},
        "women": {"mean": np.mean(women_dissat), "median": median(women_dissat), "mode": safe_mode(women_dissat)},
    }


def satisfaction_threshold_analysis(pairs, all_people, threshold=10):
    men_below = women_below = 0
    total = len(pairs)
    for m_obj, w_obj in pairs:
        m_rank = m_obj.preferences.index(w_obj) + 1 if w_obj in m_obj.preferences else len(all_people)
        w_rank = w_obj.preferences.index(m_obj) + 1 if m_obj in w_obj.preferences else len(all_people)
        if m_rank <= threshold:
            men_below += 1
        if w_rank <= threshold:
            women_below += 1
    return {
        "threshold": threshold,
        "men": {"count": men_below, "percent": (men_below / total) * 100},
        "women": {"count": women_below, "percent": (women_below / total) * 100},
    }


# ============================================================
#                 STABILITY MEASUREMENT
# ============================================================

def measure_stability(pairs, all_people):
    match_dict = {a: b for a, b in pairs}
    match_dict.update({b: a for a, b in pairs})

    men = [p for p in all_people.values() if p.gender == "M"]
    women = [p for p in all_people.values() if p.gender == "W"]

    blocking_pairs, involved = [], set()
    total_possible = len(men) * len(women)

    for m in men:
        m_match = match_dict.get(m)
        for w in women:
            w_match = match_dict.get(w)
            if m.prefers(w, m_match) and w.prefers(m, w_match):
                blocking_pairs.append((m, w))
                involved.update([m, w])

    n = len(all_people)
    return {
        "blocking_pairs": len(blocking_pairs),
        "individuals_involved": len(involved),
        "individuals_percent": (len(involved) / n) * 100 if n else 0.0,
        "pair_percent": (len(blocking_pairs) / total_possible) * 100 if total_possible else 0.0,
    }


def evaluate_matching(pairs, all_people, threshold=10):
    stats = dissatisfaction_stats(pairs, all_people)
    threshold_data = satisfaction_threshold_analysis(pairs, all_people, threshold)
    stability = measure_stability(pairs, all_people)

    print("=" * 65)
    print(f"Men: Mean: {stats['men']['mean']:.2f}, Median: {stats['men']['median']}, Mode: {stats['men']['mode']}")
    print(f"Women: Mean: {stats['women']['mean']:.2f}, Median: {stats['women']['median']}, Mode: {stats['women']['mode']}")
    print(f"\nWithin top {threshold_data['threshold']} choices:")
    print(f"Men: {threshold_data['men']['count']}/{len(pairs)} ({threshold_data['men']['percent']:.2f}%)")
    print(f"Women: {threshold_data['women']['count']}/{len(pairs)} ({threshold_data['women']['percent']:.2f}%)")
    print("=" * 65)
    print(f"Blocking pairs: {stability['blocking_pairs']} "
          f"({stability['pair_percent']:.6f}% of all possible pairs)")
    print(f"Individuals involved: {stability['individuals_involved']} "
          f"({stability['individuals_percent']:.2f}% of population)")
    print("=" * 65)


def print_pairings(pairs):
    print("\n" + "=" * 65)
    print(" " * 22 + "💞 FINAL PAIRINGS 💞")
    print("=" * 65)
    print(f"{'Man':<12} {'Woman':<12} {'Man→Woman Rank':<18} {'Woman→Man Rank'}")
    print("-" * 65)
    for m, w in sorted(pairs, key=lambda x: x[0].name):
        m_rank = m.preferences.index(w) + 1 if w in m.preferences else "N/A"
        w_rank = w.preferences.index(m) + 1 if m in w.preferences else "N/A"
        print(f"{m.name:<12} {w.name:<12} {str(m_rank):<18} {w_rank}")
    print("=" * 65 + "\n")


# ============================================================
#                    MAIN TEST FUNCTION
# ============================================================

def test_matching(num_pairs=6, threshold=10):
    men = [Person(f"M{i+1}", "M", []) for i in range(num_pairs)]
    women = [Person(f"W{i+1}", "W", []) for i in range(num_pairs)]

    for m in men:
        m.preferences = random.sample(women, len(women))
    for w in women:
        w.preferences = random.sample(men, len(men))

    all_people = {p.name: p for p in men + women}

    # not using the hybrid alg

    # matches_men = gale_shapley(men, women)
    # reset_all(men + women)
    # matches_women = gale_shapley(women, men)

    # men_norm = normalize(matches_men)
    # women_norm = normalize(matches_women)
    # common_pairs = men_norm.intersection(women_norm)

    # men_in_common = {m for m, _ in common_pairs}
    # women_in_common = {w for _, w in common_pairs}
    # leftover_men = [m for m in men if m not in men_in_common]
    # leftover_women = [w for w in women if w not in women_in_common]

    # hungarian_pairs = hungarian(leftover_men, leftover_women, all_people)
    # final_pairs = list(common_pairs) + hungarian_pairs

    final_pairs = hungarian(men, women, all_people)

    evaluate_matching(final_pairs, all_people, threshold)
    # print_pairings(final_pairs)

if __name__ == "__main__":
    for i in range(5):
        print(f"\n### Test Run {i+1} ###")
        random.seed()
        test_matching(num_pairs=500, threshold=15)
