import random
import numpy as np
import networkx as nx
from statistics import mean, median, mode, StatisticsError


# =====================================================
# PERSON CLASS
# =====================================================
class Person:
    def __init__(self, name, gender, preferences):
        self.name = name
        self.gender = gender
        self.preferences = preferences


# =====================================================
# MIN-WEIGHT PERFECT MATCHING (NETWORKX)
# =====================================================
def min_weight_graph_matching(people):
    """Compute symmetric minimum-weight perfect matching for all people."""
    G = nx.Graph()
    n = len(people)

    # Build weighted graph (symmetric costs)
    for i, p in enumerate(people):
        for j, q in enumerate(people):
            if i < j:  # undirected edge
                rank_a = p.preferences.index(q) + 1 if q in p.preferences else n
                rank_b = q.preferences.index(p) + 1 if p in q.preferences else n
                cost = rank_a + rank_b
                G.add_edge(i, j, weight=cost)

    # Compute minimum-weight perfect matching
    matching = nx.algorithms.matching.min_weight_matching(G, weight="weight")
    return [(people[u], people[v]) for u, v in matching]


# =====================================================
# MATCHING QUALITY STATS
# =====================================================
def print_stats(pairs, threshold_top=20, threshold_bottom=10):
    """Print mean, median, and mode of ranks + satisfaction stats."""
    all_ranks = []
    total_prefs = 0

    for a, b in pairs:
        if b in a.preferences:
            rank_a = a.preferences.index(b) + 1
            all_ranks.append(rank_a)
            total_prefs = len(a.preferences)

        if a in b.preferences:
            rank_b = b.preferences.index(a) + 1
            all_ranks.append(rank_b)
            total_prefs = len(b.preferences)

    # Compute statistics
    mean_rank = mean(all_ranks)
    median_rank = median(all_ranks)
    try:
        mode_rank = mode(all_ranks)
    except StatisticsError:
        mode_rank = "No unique mode"

    total = len(all_ranks)
    top_satisfied = sum(1 for r in all_ranks if r <= threshold_top)
    bottom_satisfied = sum(1 for r in all_ranks if r > total_prefs - threshold_bottom)

    # Print summary
    print("\n--- Matching Stats ---")
    print(f"Mean rank: {mean_rank:.2f}")
    print(f"Median rank: {median_rank}")
    print(f"Mode rank: {mode_rank}")
    print(f"{top_satisfied} / {total} people ({(top_satisfied / total) * 100:.2f}%) "
          f"got a match in their top {threshold_top} preferences.")
    print(f"{bottom_satisfied} / {total} people ({(bottom_satisfied / total) * 100:.2f}%) "
          f"got a match in their bottom {threshold_bottom} preferences.\n")


# =====================================================
# STABILITY METRIC
# =====================================================
def measure_stability(pairs, people):
    """Measure how many blocking pairs exist and how many people are involved."""
    partner = {a: b for a, b in pairs}
    partner.update({b: a for a, b in pairs})

    blocking_pairs = 0
    involved = set()
    n = len(people)

    for i, p in enumerate(people):
        for j, q in enumerate(people):
            if i >= j or partner.get(p) == q:
                continue

            # Check if both prefer each other over current partners
            prefers_q = (
                q in p.preferences and partner.get(p) in p.preferences and
                p.preferences.index(q) < p.preferences.index(partner[p])
            )
            prefers_p = (
                p in q.preferences and partner.get(q) in q.preferences and
                q.preferences.index(p) < q.preferences.index(partner[q])
            )

            if prefers_q and prefers_p:
                blocking_pairs += 1
                involved.update([p, q])

    total_possible = (n * (n - 1)) // 2
    percent_blocking = (blocking_pairs / total_possible) * 100
    percent_people_involved = (len(involved) / n) * 100

    print("--- Stability Stats ---")
    print(f"Blocking pairs: {blocking_pairs} ({percent_blocking:.3f}% of all pairs)")
    print(f"People involved in ≥1 blocking pair: {len(involved)} "
          f"({percent_people_involved:.2f}% of all people)\n")

    return blocking_pairs, percent_blocking, len(involved), percent_people_involved


# =====================================================
# DRIVER FUNCTION
# =====================================================
def run_group(label, n=100, threshold_top=20, threshold_bottom=10):
    """Run full simulation for a single group."""
    print(f"\n==== {label.upper()} GROUP ====")
    people = [Person(f"{label}{i+1}", label, []) for i in range(n)]

    # Assign random preferences
    for p in people:
        p.preferences = random.sample([q for q in people if q is not p], n - 1)

    # Compute and analyze matching
    pairs = min_weight_graph_matching(people)
    print_stats(pairs, threshold_top, threshold_bottom)
    measure_stability(pairs, people)


# =====================================================
# TEST RUN
# =====================================================
if __name__ == "__main__":
    run_group("G", n=20, threshold_top=5, threshold_bottom=10)
    run_group("L", n=20, threshold_top=5, threshold_bottom=10)
    run_group("G", n=500, threshold_top=20, threshold_bottom=400)
    run_group("L", n=500, threshold_top=20, threshold_bottom=400)
