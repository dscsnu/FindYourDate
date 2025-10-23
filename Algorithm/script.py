import random
import heapq
import statistics
from statistics import StatisticsError
from collections import defaultdict, Counter, namedtuple
import numpy as np
from scipy.optimize import linear_sum_assignment
import networkx as nx

# -------------------------
# CONFIG - To be replaced by configuration or removed entirely 🗑️
# -------------------------
N_STRAIGHT_MEN = 90
N_STRAIGHT_WOMEN = 78
N_GAY_MEN = 4
N_LESBIAN_WOMEN = 7
N_BI_MEN = 6
N_BI_WOMEN = 15

# thresholds for summary
TOP_K = 15
BOTTOM_K = 30

# probability a straight user accepts bisexuals
STRAIGHT_ACCEPTS_BI_PROB = 0.75

# Large cost constant for non-mutual/non-existent edges
LARGE_COST = 10**6

# -------------------------
# Person Class & Helpers
# -------------------------
class Person:
    """Represents an individual user in the matching system."""
    def __init__(self, name: str, gender: str, orientation: str, accepts_bi: bool = True):
        self.name = name
        self.gender = gender 
        self.orientation = orientation
        self.accepts_bi = accepts_bi
        self.preferences = []  # List of Person objects, ordered by preference
        self.matched_to = None # The Person object they are matched with

    def __repr__(self):
        return f"{self.name}({self.gender},{self.orientation})"

def cat_label(person: Person) -> str:
    """Returns a simplified category label for statistics."""
    if person.orientation == "straight":
        return "straight_men" if person.gender == "M" else "straight_women"
    if person.orientation == "gay":
        return "gay_men"
    if person.orientation == "lesbian":
        return "lesbian_women"
    if person.orientation == "bi":
        return "bi_men" if person.gender == "M" else "bi_women"
    return "other"

# -------------------------
# Population Generation and Preferences 🗑️ (To be replaced by form data loading)
# -------------------------
def generate_population(seed=None) -> list[Person]:
    """Generates the population based on config and determines initial preference lists."""
    if seed is not None:
        random.seed(seed)
    people = []

    # --- START: GENERATION BLOCK 🗑️ ---
    # Create persons per spec
    for i in range(N_STRAIGHT_MEN):
        accepts_bi = random.random() < STRAIGHT_ACCEPTS_BI_PROB
        people.append(Person(f"M{i}", "M", "straight", accepts_bi))
    for i in range(N_STRAIGHT_WOMEN):
        accepts_bi = random.random() < STRAIGHT_ACCEPTS_BI_PROB
        people.append(Person(f"W{i}", "W", "straight", accepts_bi))
    for i in range(N_GAY_MEN):
        people.append(Person(f"G{i}", "M", "gay", accepts_bi=True))
    for i in range(N_LESBIAN_WOMEN):
        people.append(Person(f"L{i}", "W", "lesbian", accepts_bi=True))
    for i in range(N_BI_MEN):
        people.append(Person(f"BM{i}", "M", "bi", accepts_bi=True))
    for i in range(N_BI_WOMEN):
        people.append(Person(f"BW{i}", "W", "bi", accepts_bi=True))
    # --- END: GENERATION BLOCK 🗑️ ---

    # For each person, create a preference list based on orientation rules
    for p in people:
        targets = []
        if p.orientation == "straight":
            # Straight M/W targets: Opposite gender, Straight or Bi (if p accepts bi)
            target_gender = "W" if p.gender == "M" else "M"
            for q in people:
                if q.gender == target_gender:
                    if q.orientation == "straight":
                        targets.append(q)
                    elif q.orientation == "bi" and p.accepts_bi:
                        targets.append(q)
        
        elif p.orientation in ("gay", "lesbian"):
            # Gay/Lesbian targets: Same gender, same orientation or Bi (if p accepts bi, always true here)
            target_orientation = p.orientation
            target_gender = p.gender
            for q in people:
                if q.gender == target_gender and q is not p:
                    if q.orientation == target_orientation:
                        targets.append(q)
                    elif q.orientation == "bi" and p.accepts_bi:
                        targets.append(q)
                        
        elif p.orientation == "bi":
            # Bi targets: Anyone except self, unless Q is straight and rejects bi partners, or a strict gay/lesbian mismatch
            for q in people:
                if q is p:
                    continue
                
                # Bi rejected by Straight who does not accept bi
                if q.orientation == "straight" and not q.accepts_bi:
                    continue
                    
                # Bi man rejected by Lesbian/Bi woman rejected by Gay (gender mismatch)
                if q.orientation == "gay" and q.gender == "M" and p.gender == "W":
                    continue
                if q.orientation == "lesbian" and q.gender == "W" and p.gender == "M":
                    continue
                    
                targets.append(q)

        random.shuffle(targets) # Randomly shuffle to simulate a ranked list
        p.preferences = targets

    return people

# -------------------------
# Build Candidate Pairs for Greedy Stage
# -------------------------
HeapEntry = namedtuple("HeapEntry", ["cost", "a_id", "b_id", "a", "b"])

def build_candidate_pairs(people: list[Person]) -> tuple:
    """
    Builds a sorted list and min-heap of all valid candidate pairs.
    Only includes pairs that are mutually listed in preferences.
    """
    id_map = {i: p for i, p in enumerate(people)}
    person_to_id = {p: i for i, p in id_map.items()}
    pref_sets = {p: set(p.preferences) for p in people}

    candidates = []
    heap = []
    seen = set() 

    for i, a in id_map.items():
        for b in a.preferences:
            j = person_to_id[b]
            if i == j: continue
            key = tuple(sorted((i, j)))
            if key in seen: continue

            # CRITICAL CHECK: Must be a mutual preference
            if a not in pref_sets[b]:
                continue
            
            # --- COST CALCULATION ---
            rank_a = a.preferences.index(b) + 1
            rank_b = b.preferences.index(a) + 1
            cost = rank_a + rank_b
            # LATER CHANGE: COST = 1 - COMPATIBILITY (If using compatibility scores) 
            # cost = 1 - compatibility_score(a, b) 
            # --- END COST CALCULATION ---

            entry = HeapEntry(cost=cost, a_id=i, b_id=j, a=a, b=b)
            candidates.append(entry)
            heap.append((cost, i, j, a, b))
            seen.add(key)

    candidates_sorted = sorted(candidates, key=lambda e: (e.cost))
    heapq.heapify(heap)

    return candidates_sorted, heap, id_map, person_to_id

# -------------------------
# Greedy Matching (Stage 1)
# -------------------------
def greedy_global_minheap(people: list[Person], print_top_n: int = None) -> tuple:
    """Executes the greedy matching algorithm based on minimum rank-sum cost."""
    candidates_sorted, heap, _, _ = build_candidate_pairs(people)

    print("\n=== All potential mutual pairs (lowest cost first) ===")
    for idx, e in enumerate(candidates_sorted):
        if print_top_n is not None and idx >= print_top_n:
            remaining = len(candidates_sorted) - print_top_n
            print(f"  ... ({remaining} more pairs not shown)")
            break
        print(f"  {e.a} ↔ {e.b} | cost = {e.cost}")
    print()

    target_pairs = len(people) // 2
    matched = set()
    matches = []

    while heap and len(matches) < target_pairs:
        cost, _, _, a, b = heapq.heappop(heap)
        
        # Skip if either person is already matched
        if a in matched or b in matched:
            continue
            
        a.matched_to = b
        b.matched_to = a
        matched.add(a)
        matched.add(b)
        matches.append((a, b, cost))
        print(f"✅ Matched {a} ↔ {b} | cost = {cost}")

    unmatched = [p for p in people if p not in matched]
    if unmatched:
        print(f"\nUnmatched people: {len(unmatched)}")

    return matches, unmatched

# -------------------------
# Re-optimization Helpers (Stage 2)
# -------------------------
def decompose_pools(matches: list, unmatched: list) -> dict:
    """Decomposes all individuals (matched and unmatched) into gender/orientation pools."""
    straight_men, straight_women = [], []
    gay_men, lesbian_women = [], []
    
    # Pool people from Stage 1 matches
    for a, b, _ in matches:
        if a.gender != b.gender: # M-W Pairings (Straight/Bi focus)
            m, w = (a, b) if a.gender == "M" else (b, a)
            straight_men.append(m)
            straight_women.append(w)
        elif a.gender == "M": # M-M Pairings (Gay/Bi focus)
            gay_men.extend([a, b])
        elif a.gender == "W": # W-W Pairings (Lesbian/Bi focus)
            lesbian_women.extend([a, b])

    # Pool unmatched people
    for p in unmatched:
        if p.gender == "M":
            if p.orientation in ("straight", "bi"): straight_men.append(p)
            elif p.orientation == "gay": gay_men.append(p)
        elif p.gender == "W":
            if p.orientation in ("straight", "bi"): straight_women.append(p)
            elif p.orientation == "lesbian": lesbian_women.append(p)
            
    return {
        'straight_men': straight_men, 
        'straight_women': straight_women, 
        'gay_men': gay_men, 
        'lesbian_women': lesbian_women
    }

def hungarian(men_subset: list[Person], women_subset: list[Person], all_people: list[Person]) -> list:
    """Bipartite matching re-optimization using the Hungarian algorithm (M-W pairs)."""
    if not men_subset or not women_subset:
        return []

    m_count, w_count = len(men_subset), len(women_subset)
    n = max(m_count, w_count)
    men_padded = men_subset + [None] * (n - m_count)
    women_padded = women_subset + [None] * (n - w_count)

    cost = np.full((n, n), LARGE_COST, dtype=float)
    
    pref_sets_m = {p: set(p.preferences) for p in men_subset}
    pref_sets_w = {p: set(p.preferences) for p in women_subset}

    for i, m_obj in enumerate(men_padded):
        for j, w_obj in enumerate(women_padded):
            if not m_obj or not w_obj:
                continue
            
            # CRITICAL MUTUALITY CHECK
            m_prefers_w = w_obj in pref_sets_m.get(m_obj, set())
            w_prefers_m = m_obj in pref_sets_w.get(w_obj, set())

            if m_prefers_w and w_prefers_m:
                # --- COST CALCULATION ---
                rank_m = m_obj.preferences.index(w_obj) + 1
                rank_w = w_obj.preferences.index(m_obj) + 1
                cost[i, j] = rank_m + rank_w
                # LATER CHANGE: COST = 1 - COMPATIBILITY (If using compatibility scores) 
                # cost[i, j] = 1 - compatibility_score(m_obj, w_obj)
                # --- END COST CALCULATION ---
            else:
                cost[i, j] = LARGE_COST # Set cost to LARGE for non-mutual pairs.

    row_ind, col_ind = linear_sum_assignment(cost)
    matches = []
    for i, j in zip(row_ind, col_ind):
        if i < m_count and j < w_count:
            m_obj, w_obj = men_padded[i], women_padded[j]
            if cost[i, j] < LARGE_COST: # Only take mutual, non-padded pairs
                matches.append((m_obj, w_obj, cost[i,j]))
    return matches

def min_weight_graph_matching(people: list[Person]) -> list:
    """
    Computes minimum-weight perfect matching (MWPM) for same-sex pools. 
    MWPM is used as a general graph matching algorithm.
    """
    if not people:
        return []
    
    n = len(people)
    G = nx.Graph()
    G.add_nodes_from(range(n))
    
    # Calculate dummy node cost (high penalty for not matching someone)
    MAX_RANK_SUM = 2 * (n + 1)
    DUMMY_COST = MAX_RANK_SUM * 2 

    for i, p in enumerate(people):
        for j, q in enumerate(people):
            if i < j: 
                # CRITICAL MUTUALITY CHECK
                q_in_p = q in p.preferences
                p_in_q = p in q.preferences
                
                if q_in_p and p_in_q:
                    # --- COST CALCULATION ---
                    rank_p = p.preferences.index(q) + 1
                    rank_q = q.preferences.index(p) + 1
                    cost = rank_p + rank_q
                    # LATER CHANGE: COST = 1 - COMPATIBILITY (If using compatibility scores) 
                    # cost = 1 - compatibility_score(p, q)
                    # --- END COST CALCULATION ---
                    G.add_edge(i, j, weight=cost)

    if n % 2 != 0:
        DUMMY_NODE = n
        G.add_node(DUMMY_NODE)
        for i in range(n):
            # Connect all people to the dummy node with a high cost
            G.add_edge(i, DUMMY_NODE, weight=DUMMY_COST) 

    # Compute minimum-weight perfect matching
    matching = nx.algorithms.matching.min_weight_matching(G, weight="weight")
    
    final_matches = []
    # Extract real matches
    for u, v in matching:
        if u < n and v < n:
            p, q = people[u], people[v]
            # Double-check mutuality to ensure no high-cost edge was artificially selected 
            if q in p.preferences and p in q.preferences:
                rank_p = p.preferences.index(q) + 1
                rank_q = q.preferences.index(p) + 1
                cost = rank_p + rank_q
                final_matches.append((p, q, cost))

    return final_matches

# -------------------------
# Statistics & Stability Analysis
# -------------------------
def compute_stats(people: list, matches: list, top_k: int, bottom_k: int) -> dict:
    """Computes per-category rank statistics for matched individuals."""
    # ... (function body remains unchanged as it is correct)
    rank_by_cat = defaultdict(list)

    for a, b, _ in matches:
        # Get rank for each person based on their preferences
        r_a = a.preferences.index(b) + 1
        r_b = b.preferences.index(a) + 1
        
        # Store ranks by category
        rank_by_cat[cat_label(a)].append(r_a)
        rank_by_cat[cat_label(b)].append(r_b)

    stats = {}
    categories = ["straight_men", "straight_women", "gay_men", "lesbian_women", "bi_men", "bi_women"]
    for cat in categories:
        ranks = rank_by_cat.get(cat, [])
        n = len(ranks)
        if n == 0:
            stats[cat] = {"n": 0, "mean": None, "median": None, "mode": None,
                          "top_k_count": 0, "top_k_pct": None,
                          "bottom_k_count": 0, "bottom_k_pct": None}
            continue
            
        try:
            mode_r = statistics.mode(ranks)
        except StatisticsError:
            mode_r = "No unique mode"
            
        top_k_count = sum(1 for r in ranks if r <= top_k)
        bottom_k_count = sum(1 for r in ranks if r >= bottom_k)
        
        stats[cat] = {
            "n": n,
            "mean": statistics.mean(ranks),
            "median": statistics.median(ranks),
            "mode": mode_r,
            "top_k_count": top_k_count,
            "top_k_pct": top_k_count / n * 100,
            "bottom_k_count": bottom_k_count,
            "bottom_k_pct": bottom_k_count / n * 100,
        }
    return stats

def measure_stability(people: list, matches: list) -> dict:
    """Measures stability by counting blocking pairs."""
    
    # --- FIX APPLIED HERE: Correctly build the bidirectional partner map ---
    partner = {}
    for a, b, _ in matches:
        partner[a] = b
        partner[b] = a
    # ---------------------------------------------------------------------
    
    blocking_pairs = 0
    involved = set()
    n = len(people)
    pref_sets = {p: set(p.preferences) for p in people}
    
    # Iterate over all unordered pairs (i < j)
    for i in range(n):
        p = people[i]
        for j in range(i + 1, n):
            q = people[j]
            if partner.get(p) == q: continue # Already partners
            
            p_part = partner.get(p)
            q_part = partner.get(q)
            
            pref_p = False
            pref_q = False
            
            # P prefers Q over current partner (p_part)?
            if q in pref_sets[p]:
                if p_part is None:
                    pref_p = True # Unmatched P prefers any listed Q
                elif p_part in pref_sets[p]:
                    # P lists both Q and p_part, check if Q is ranked higher
                    pref_p = p.preferences.index(q) < p.preferences.index(p_part)
            
            # Q prefers P over current partner (q_part)?
            if p in pref_sets[q]:
                if q_part is None:
                    pref_q = True # Unmatched Q prefers any listed P
                elif q_part in pref_sets[q]:
                    # Q lists both P and q_part, check if P is ranked higher
                    pref_q = q.preferences.index(p) < q.preferences.index(q_part)
            
            if pref_p and pref_q:
                blocking_pairs += 1
                involved.add(p); involved.add(q)

    total_possible_pairs = (n * (n - 1)) // 2
    return {
        "blocking_pairs": blocking_pairs,
        "pair_percent": blocking_pairs / total_possible_pairs * 100 if total_possible_pairs else 0.0,
        "individuals_involved": len(involved),
        "individuals_percent": len(involved) / n * 100 if n else 0.0
    }

# -------------------------
# Summary Printer
# -------------------------
def print_summary(people: list[Person], matches: list, stats: dict, stability: dict, top_k: int, bottom_k: int):
    """Prints a formatted summary of the matching results."""
    total_matches = len(matches)
    total_people = len(people)
    
    print("\n" + "="*65)
    print("== Matching Summary ==")
    print(f"Total people: {total_people}, Matches formed: {total_matches}, Matched people: {total_matches*2}")
    print("-"*65)
    
    categories = ["straight_men", "straight_women", "gay_men", "lesbian_women", "bi_men", "bi_women"]
    for cat in categories:
        s = stats[cat]
        if s["n"] == 0:
            print(f"{cat:<15} | n=  0 | mean=-- | med=-- | mode=-- | ≤{top_k}: -- | ≥{bottom_k}: --")
        else:
            mean_s = f"{s['mean']:.2f}"
            med_s = f"{s['median']:.2f}"
            print(f"{cat:<15} | n={s['n']:3d} | mean={mean_s:<6} | med={med_s:<6} | mode={s['mode']:<6} "
                  f"| ≤{top_k}: {s['top_k_count']:3d} ({s['top_k_pct']:.1f}%) | ≥{bottom_k}: {s['bottom_k_count']:3d} ({s['bottom_k_pct']:.1f}%)")
    
    print("-"*65)
    print(f"Blocking pairs: {stability['blocking_pairs']} ({stability['pair_percent']:.6f}% of all possible pairs)")
    print(f"People involved in blocking pairs: {stability['individuals_involved']} ({stability['individuals_percent']:.2f}% of population)")
    print("="*65 + "\n")

# -------------------------
# MAIN
# -------------------------
def main():
    # 🗑️ The entire following block up to the FIRST "--- STAGE 1" comment will be replaced 
    # 🗑️ by code that loads and prepares the 'people' list and their 'preferences' from form data.
    print("Generating population and preferences...")
    people = generate_population()
    print(f"Total people generated: {len(people)}")
    
    breakdown = Counter(cat_label(p) for p in people)
    print("Breakdown:", dict(breakdown))

    # --- STAGE 1: Greedy Matching ---
    matches, unmatched = greedy_global_minheap(people, print_top_n=100) 

    # --- STAGE 1 Summary ---
    stats = compute_stats(people, matches, top_k=TOP_K, bottom_k=BOTTOM_K)
    stability = measure_stability(people, matches)
    print("\n\n=============== STAGE 1: GREEDY MATCHING RESULTS ===============")
    print_summary(people, matches, stats, stability, top_k=TOP_K, bottom_k=BOTTOM_K)

    # --- STAGE 2: Re-optimization ---
    decomposed = decompose_pools(matches, unmatched)
    men = decomposed['straight_men']
    women = decomposed['straight_women']
    gay = decomposed['gay_men']
    lesbian = decomposed['lesbian_women']
    
    straight_pairings = hungarian(men, women, men + women)
    gay_pairings = min_weight_graph_matching(gay)
    lesbian_pairings = min_weight_graph_matching(lesbian)

    final_pairings = straight_pairings + gay_pairings + lesbian_pairings
    
    # --- STAGE 2 Final Summary ---
    stats = compute_stats(people, final_pairings, top_k=TOP_K, bottom_k=BOTTOM_K)
    stability = measure_stability(people, final_pairings)
    print("=============== STAGE 2: RE-OPTIMIZED MATCHING RESULTS ===============")
    print_summary(people, final_pairings, stats, stability, top_k=TOP_K, bottom_k=BOTTOM_K)


if __name__ == "__main__":
    main()    