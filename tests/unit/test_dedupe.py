"""Unit tests for dita_etl.assess.dedupe."""

from dita_etl.assess.dedupe import (
    cluster_near_duplicates,
    jaccard_from_signatures,
    minhash_signature,
    shingle_tokens,
)


class TestShingleTokens:
    def test_basic(self):
        shingles = shingle_tokens("the quick brown fox", n=2)
        assert "the quick" in shingles
        assert "quick brown" in shingles
        assert "brown fox" in shingles

    def test_ngram_3(self):
        shingles = shingle_tokens("a b c d", n=3)
        assert shingles == ["a b c", "b c d"]

    def test_text_shorter_than_ngram(self):
        # Fewer tokens than window size → no complete n-gram can be formed
        shingles = shingle_tokens("hello", n=5)
        assert shingles == []

    def test_empty_text(self):
        assert shingle_tokens("", n=3) == []

    def test_lowercase_normalisation(self):
        shingles = shingle_tokens("Hello WORLD", n=2)
        assert shingles == ["hello world"]


class TestMinhashSignature:
    def test_returns_correct_length(self):
        sig = minhash_signature(["a b", "c d"], num_perm=32)
        assert len(sig) == 32

    def test_same_shingles_same_signature(self):
        shingles = ["the quick", "quick brown"]
        assert minhash_signature(shingles, 32) == minhash_signature(shingles, 32)

    def test_empty_shingles(self):
        sig = minhash_signature([], num_perm=16)
        assert len(sig) == 16  # all max values


class TestJaccardFromSignatures:
    def test_identical_signatures(self):
        sig = [1, 2, 3, 4]
        assert jaccard_from_signatures(sig, sig) == 1.0

    def test_completely_different(self):
        assert jaccard_from_signatures([1, 2], [3, 4]) == 0.0

    def test_empty_signatures_return_zero(self):
        assert jaccard_from_signatures([], []) == 0.0

    def test_partial_overlap(self):
        assert jaccard_from_signatures([1, 2, 3, 4], [1, 2, 9, 9]) == 0.5


class TestClusterNearDuplicates:
    _TEXT_A = "the quick brown fox jumps over the lazy dog " * 10
    _TEXT_B = "the quick brown fox jumps over the lazy dog " * 10  # identical
    _TEXT_C = "completely different content about something else entirely here " * 10

    def test_identical_texts_clustered_together(self):
        items = [("a", self._TEXT_A), ("b", self._TEXT_B)]
        clusters = cluster_near_duplicates(items, ngram=5, num_perm=64, threshold=0.9)
        # a and b should be in the same cluster
        merged = [c for c in clusters if "a" in c and "b" in c]
        assert len(merged) == 1

    def test_different_texts_in_different_clusters(self):
        items = [("a", self._TEXT_A), ("c", self._TEXT_C)]
        clusters = cluster_near_duplicates(items, ngram=5, num_perm=64, threshold=0.9)
        assert len(clusters) == 2

    def test_all_keys_appear_exactly_once(self):
        items = [("a", self._TEXT_A), ("b", self._TEXT_B), ("c", self._TEXT_C)]
        clusters = cluster_near_duplicates(items, ngram=5, num_perm=64, threshold=0.9)
        all_keys = [k for cluster in clusters for k in cluster]
        assert sorted(all_keys) == ["a", "b", "c"]

    def test_empty_input(self):
        assert cluster_near_duplicates([], ngram=5, num_perm=64, threshold=0.9) == []
