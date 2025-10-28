# FindYourDate

## Algorithm: The Hybrid Two-Stage Optimization

We start with a list of all users, each represented as a `Person` object. Each person has a vector `embedding` (representing their profile features/preferences) and a dynamically generated **preference list** (`preferences`), which is a list of potential partners sorted by **cosine similarity** to their own embedding.

We use three algorithms in a two-stage process:

### Stage 1: Initial Allocation (Greedy Global Min-Heap)

1.  **Generate All Mutual Pairs:** The system first identifies all **mutually preferred** pairs. A pair $(A, B)$ is considered if $B$ is in $A$'s preference list AND $A$ is in $B$'s preference list.
2.  **Calculate Cost:** The cost for each mutual pair is calculated as **$1 - \text{Compatibility}$**. A lower cost indicates a higher-quality, more satisfying match for both parties.
3.  **Greedy Selection:** All mutual pairs are loaded into a **Min-Heap**. The algorithm iteratively extracts the pair with the **lowest cost** (highest mutual preference).
    * If both individuals in the extracted pair are unmatched, they're paired, removed from the unmatched pool, and the match is recorded.
    * If either is already matched, the pair is discarded.
4.  **Result:** This greedy approach efficiently forms the most highly-preferred, **non-conflicting** pairs first, securing the best initial matches.

### Stage 2: Re-Optimization and Completion (Pool Decomposition)

The matches formed in Stage 1, along with the remaining unmatched users, are now decomposed into pools based on the structure of the required pairings. This decomposition is crucial for preventing same-sex matches from interfering with heterosexual matching and vice-versa, allowing us to apply the optimal algorithm to each group.

#### 🛠️ How Decomposition Works

The `decompose_pools` helper function partitions all individuals into four major pools:

| Pool | Purpose | Pairing Algorithm |
| :--- | :--- | :--- |
| **`straight_men`** | Forms opposite-sex pairs with `straight_women`. | **Hungarian Algorithm** (Bipartite) |
| **`straight_women`** | Forms opposite-sex pairs with `straight_men`. | **Hungarian Algorithm** (Bipartite) |
| **`gay_men`** | Forms same-sex pairs within the pool. | **Edmond's Blossom (MWPM)** (General Graph) |
| **`lesbian_women`** | Forms same-sex pairs within the pool. | **Edmond's Blossom (MWPM)** (General Graph) |

**Bisexual User Decomposition Logic:**

Bisexual users are handled dynamically based on their Stage 1 status, prioritizing the pool that reflects their initial match or offers the greatest re-optimization opportunity:

* **Matched Bi Users:** They are assigned to **one exclusive pool** corresponding to the gender composition of their match, honoring the greedy decision:
    * A bisexual person in a **Man-Woman pair** is sent to the **`straight`** pools.
    * A bisexual man in a **Man-Man pair** is sent to the **`gay_men`** pool.
    * A bisexual woman in a **Woman-Woman pair** is sent to the **`lesbian_women`** pool.
* **Unmatched Bi Users:** Any bisexual user who was *not* matched in Stage 1 is placed **only in the `straight` pools** (e.g., a bisexual man is placed only in `straight_men`). This is done to concentrate unmatched Bi users where they have the largest number of potential partners (M-W matching) for the final, powerful bipartite optimization.

---

### Matching Algorithms (Stage 2 Re-optimization)

The two types of pools are processed using distinct, globally optimizing algorithms:

1.  **Hungarian Algorithm (for Bipartite Heterosexual Matching):**
    * Applied to the `straight_men` and `straight_women` pools (which now contain the bulk of unmatched Bi users).
    * It finds the global matching solution that **minimizes the total sum of costs** across the two sets.
2.  **Edmond's Blossom Algorithm (networkx Minimum Weight Perfect Matching):**
    * Applied to the same-sex pools (`gay_men` and `lesbian_women`).
    * Since same-sex matching is a **general graph problem**, this algorithm computes the minimum-weight perfect matching, ensuring the highest-quality same-sex connections possible.

### Why we use Hungarian and Blossom?

The **Greedy Algorithm (Stage 1)** is limited because it is **local and shortsighted**. It makes decisions based only on the single best available pair at the moment, which often leads to a **suboptimal global result**.

**Stage 2 Re-optimization** addresses this by using **globally optimizing algorithms** that find a globally superior set of matches, maximizing the average quality across the entire population.

The two distinct algorithms are necessary because they solve two fundamentally different types of graph matching problems optimally: the **Hungarian Algorithm** for the two distinct sets of the **Bipartite Graph** (M $\leftrightarrow$ W), and the **MWPM (Blossom)** for the single set of the **General Graph** (M $\leftrightarrow$ M or W $\leftrightarrow$ W).

---

### The Final Match List

The matches from the Hungarian (opposite-sex) and MWPM (same-sex) runs are combined to form the final list of recommended pairings.

---

## Data Filtering and Validation

#### 🧑‍🤝‍🧑 How we find the valid partners

The `valid_partner(a, b)` function implements the core business logic for who can be considered a potential partner for another user based on **gender** and **orientation**, considering a user's explicit preference settings:

* **Straight Users:** Only list the opposite gender, respecting their toggle (`a.accepts_bi`) for listing $\text{Bi}$ users.
* **Gay/Lesbian Users:** Only list the same gender, compatible with $\text{Gay/Lesbian}$ users and $\text{Bi}$ users of the same gender.
* **Bi Users:** List nearly everyone who is compatible with their gender and does not have an exclusive preference against them.

This stringent filtering ensures the `preferences` lists and, consequently, all matching algorithms, only consider connections that meet the users' specified constraints, leading to high-quality and respectful pairings.