"""Ranking evaluation metrics for recommendation quality.

All metrics compare a ranked list of recommended movie IDs against a set
of ground-truth relevant movie IDs (movies the real user rated 4.0+).
"""

import math


def precision_at_k(recs: list[int], relevant: set[int], k: int = 10) -> float:
    """Fraction of the top-k recommendations that are relevant.

    precision@k = |recs[:k] ∩ relevant| / k
    """
    if k == 0:
        return 0.0
    top_k = recs[:k]
    hits = sum(1 for r in top_k if r in relevant)
    return hits / k


def recall_at_k(recs: list[int], relevant: set[int], k: int = 10) -> float:
    """Fraction of the relevant set captured in the top-k recommendations.

    recall@k = |recs[:k] ∩ relevant| / |relevant|
    """
    if not relevant:
        return 0.0
    top_k = recs[:k]
    hits = sum(1 for r in top_k if r in relevant)
    return hits / len(relevant)


def ndcg_at_k(recs: list[int], relevant: set[int], k: int = 10) -> float:
    """Normalized Discounted Cumulative Gain at k.

    DCG@k  = Σ_{i=1}^{k} rel_i / log₂(i + 1)
    IDCG@k = DCG of an ideal ranking (all relevant items first)
    NDCG@k = DCG@k / IDCG@k

    rel_i is binary: 1 if recs[i] is in the relevant set, 0 otherwise.
    """
    if not relevant:
        return 0.0

    top_k = recs[:k]

    # Actual DCG
    dcg = 0.0
    for i, movie_id in enumerate(top_k):
        if movie_id in relevant:
            dcg += 1.0 / math.log2(i + 2)  # i+2 because i is 0-indexed, formula uses 1-indexed

    # Ideal DCG: place all relevant items at the top
    ideal_hits = min(len(relevant), k)
    idcg = 0.0
    for i in range(ideal_hits):
        idcg += 1.0 / math.log2(i + 2)

    if idcg == 0.0:
        return 0.0

    return dcg / idcg
