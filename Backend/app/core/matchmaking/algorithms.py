import heapq, numpy as np, networkx as nx
from scipy.optimize import linear_sum_assignment
from collections import namedtuple
from app.core.matchmaking.helpers import decompose_pools

HeapEntry = namedtuple("HeapEntry", ["cost", "a_id", "b_id", "a", "b"])
LARGE_COST = 10**6

def build_candidate_pairs(people):
    id_map = {i: p for i, p in enumerate(people)}
    person_to_id = {p: i for i, p in id_map.items()}
    pref_sets = {p: set(p.preferences) for p in people}
    candidates, heap, seen = [], [], set()

    for i, a in id_map.items():
        for b in a.preferences:
            j = person_to_id[b]
            if i == j or (key := tuple(sorted((i, j)))) in seen:
                continue
            if a not in pref_sets[b]:
                continue
            rank_a = a.preferences.index(b) + 1
            rank_b = b.preferences.index(a) + 1
            cost = rank_a + rank_b
            entry = HeapEntry(cost, i, j, a, b)
            candidates.append(entry)
            heap.append((cost, i, j, a, b))
            seen.add(key)
    heapq.heapify(heap)
    return sorted(candidates, key=lambda e: e.cost), heap

def greedy_global_minheap(people):
    candidates_sorted, heap = build_candidate_pairs(people)
    matched, matches = set(), []
    while heap and len(matches) < len(people) // 2:
        cost, _, _, a, b = heapq.heappop(heap)
        if a in matched or b in matched:
            continue
        a.matched_to, b.matched_to = b, a
        matched.update({a, b})
        matches.append((a, b, cost))
    unmatched = [p for p in people if p not in matched]
    return matches, unmatched

def hungarian(men, women):
    if not men or not women:
        return []
    n = max(len(men), len(women))
    men_padded, women_padded = men + [None]*(n-len(men)), women + [None]*(n-len(women))
    cost = np.full((n, n), LARGE_COST) #later change:- cost = 1 - compactability
    pref_sets_m = {p: set(p.preferences) for p in men}
    pref_sets_w = {p: set(p.preferences) for p in women}
    for i, m in enumerate(men_padded):
        for j, w in enumerate(women_padded):
            if not m or not w:
                continue
            if w in pref_sets_m[m] and m in pref_sets_w[w]:
                cost[i, j] = (m.preferences.index(w) + 1) + (w.preferences.index(m) + 1)
    row_ind, col_ind = linear_sum_assignment(cost)
    return [
        (men_padded[i], women_padded[j], cost[i, j])
        for i, j in zip(row_ind, col_ind)
        if i < len(men) and j < len(women) and cost[i, j] < LARGE_COST
    ]

def min_weight_graph_matching(people):
    if not people:
        return []
    G = nx.Graph()
    n = len(people)
    G.add_nodes_from(range(n))
    for i in range(n):
        for j in range(i + 1, n):
            a, b = people[i], people[j]
            if b in a.preferences and a in b.preferences:
                rank_sum = (a.preferences.index(b) + 1) + (b.preferences.index(a) + 1)
                G.add_edge(i, j, weight=rank_sum)
    matching = nx.algorithms.matching.min_weight_matching(G, weight="weight")
    return [(people[i], people[j], (people[i].preferences.index(people[j]) + 1)
            + (people[j].preferences.index(people[i]) + 1))
            for i, j in matching if i < len(people) and j < len(people)]