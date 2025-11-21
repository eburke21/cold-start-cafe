"""Tests for ranking evaluation metrics.

Each test uses hand-computed values to verify exact metric behavior.
"""

import math

import pytest

from app.services.metrics import ndcg_at_k, precision_at_k, recall_at_k


class TestPrecisionAtK:
    """Verify precision@k computation."""

    def test_perfect_precision(self):
        """All recommendations are relevant → precision = 1.0."""
        recs = [1, 2, 3, 4, 5]
        relevant = {1, 2, 3, 4, 5, 6, 7}
        assert precision_at_k(recs, relevant, k=5) == 1.0

    def test_zero_precision(self):
        """No recommendations are relevant → precision = 0.0."""
        recs = [10, 11, 12, 13, 14]
        relevant = {1, 2, 3}
        assert precision_at_k(recs, relevant, k=5) == 0.0

    def test_partial_precision(self):
        """3 of 5 recommendations are relevant → precision = 0.6."""
        recs = [1, 10, 2, 11, 3]
        relevant = {1, 2, 3}
        assert precision_at_k(recs, relevant, k=5) == 0.6

    def test_precision_uses_only_top_k(self):
        """Only the first k recommendations matter."""
        recs = [1, 10, 11, 12, 13, 2, 3]  # Relevant items at positions 0, 5, 6
        relevant = {1, 2, 3}
        assert precision_at_k(recs, relevant, k=3) == pytest.approx(1 / 3)

    def test_empty_recs(self):
        """Empty recommendation list → precision = 0.0."""
        assert precision_at_k([], {1, 2, 3}, k=10) == 0.0

    def test_k_zero(self):
        """k=0 → precision = 0.0 (edge case)."""
        assert precision_at_k([1, 2, 3], {1, 2, 3}, k=0) == 0.0


class TestRecallAtK:
    """Verify recall@k computation."""

    def test_perfect_recall(self):
        """All relevant items appear in top-k → recall = 1.0."""
        recs = [1, 2, 3, 10, 11]
        relevant = {1, 2, 3}
        assert recall_at_k(recs, relevant, k=5) == 1.0

    def test_zero_recall(self):
        """No relevant items in recommendations → recall = 0.0."""
        recs = [10, 11, 12]
        relevant = {1, 2, 3}
        assert recall_at_k(recs, relevant, k=3) == 0.0

    def test_partial_recall(self):
        """2 of 4 relevant items found → recall = 0.5."""
        recs = [1, 2, 10, 11, 12]
        relevant = {1, 2, 3, 4}
        assert recall_at_k(recs, relevant, k=5) == 0.5

    def test_empty_relevant_set(self):
        """No relevant items in ground truth → recall = 0.0."""
        recs = [1, 2, 3]
        assert recall_at_k(recs, set(), k=3) == 0.0

    def test_empty_recs(self):
        """Empty recommendation list → recall = 0.0."""
        assert recall_at_k([], {1, 2, 3}, k=10) == 0.0


class TestNDCGAtK:
    """Verify NDCG@k computation with hand-computed values."""

    def test_perfect_ndcg(self):
        """All relevant items at top positions → NDCG = 1.0."""
        recs = [1, 2, 3]
        relevant = {1, 2, 3}
        assert ndcg_at_k(recs, relevant, k=3) == pytest.approx(1.0)

    def test_zero_ndcg(self):
        """No relevant items → NDCG = 0.0."""
        recs = [10, 11, 12]
        relevant = {1, 2, 3}
        assert ndcg_at_k(recs, relevant, k=3) == 0.0

    def test_single_relevant_at_position_1(self):
        """One relevant item at position 1 (index 0).

        DCG  = 1/log₂(2) = 1.0
        IDCG = 1/log₂(2) = 1.0
        NDCG = 1.0
        """
        recs = [1, 10, 11]
        relevant = {1}
        assert ndcg_at_k(recs, relevant, k=3) == pytest.approx(1.0)

    def test_single_relevant_at_position_3(self):
        """One relevant item at position 3 (index 2).

        DCG  = 1/log₂(4) = 0.5
        IDCG = 1/log₂(2) = 1.0
        NDCG = 0.5
        """
        recs = [10, 11, 1]
        relevant = {1}
        assert ndcg_at_k(recs, relevant, k=3) == pytest.approx(0.5)

    def test_two_relevant_swapped_order(self):
        """Two relevant items — verify position matters.

        recs = [1, 10, 2]  relevant = {1, 2}
        DCG  = 1/log₂(2) + 1/log₂(4) = 1.0 + 0.5 = 1.5
        IDCG = 1/log₂(2) + 1/log₂(3) = 1.0 + 0.6309... = 1.6309...
        NDCG = 1.5 / 1.6309... ≈ 0.9197
        """
        recs = [1, 10, 2]
        relevant = {1, 2}
        expected_dcg = 1.0 / math.log2(2) + 1.0 / math.log2(4)
        expected_idcg = 1.0 / math.log2(2) + 1.0 / math.log2(3)
        assert ndcg_at_k(recs, relevant, k=3) == pytest.approx(expected_dcg / expected_idcg)

    def test_empty_relevant_set(self):
        """No relevant items → NDCG = 0.0."""
        recs = [1, 2, 3]
        assert ndcg_at_k(recs, set(), k=3) == 0.0

    def test_empty_recs(self):
        """Empty recommendation list → NDCG = 0.0."""
        assert ndcg_at_k([], {1, 2, 3}, k=3) == 0.0

    def test_more_relevant_than_k(self):
        """When |relevant| > k, IDCG is capped at k items."""
        recs = [1, 2, 3]
        relevant = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10}
        # All 3 recs are relevant: DCG = IDCG (both use k=3 items)
        assert ndcg_at_k(recs, relevant, k=3) == pytest.approx(1.0)
