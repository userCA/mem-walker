"""BM25 Precomputation Integration Tests

Tests the full flow of BM25 precomputation from write to search,
including the hybrid search combining vector + BM25 results.
Uses real components (SQLiteVectorStore, real BM25Calculator).
"""

import pytest
import tempfile
import os
import hashlib

from mnemosyne.memory.bm25_calculator import BM25Calculator
from mnemosyne.memory.storage import _reciprocal_rank_fusion

VOCAB_SIZE = 100000

def _term_index(term: str) -> int:
    """Deterministic term index matching BM25Calculator."""
    return int(hashlib.md5(term.encode('utf-8')).hexdigest(), 16) % VOCAB_SIZE


class TestBM25CalculatorIntegration:
    """Integration tests for BM25Calculator with realistic data."""

    def test_bm25_idf_reflects_document_frequency(self):
        """
        Verify IDF values correctly reflect document frequency.
        Common terms (in more docs) should have lower IDF.
        """
        calc = BM25Calculator()

        # Add documents with known frequencies
        calc.add_document(["hello", "world", "customer", "issue"])  # "hello" appears 1x
        calc.add_document(["hello", "support", "ticket"])              # "hello" appears 2x
        calc.add_document(["hello", "feedback", "response"])          # "hello" appears 3x
        calc.add_document(["world", "feedback"])                      # "world" appears 2x

        # "hello" appears in 3/4 docs, "world" in 2/4 docs
        # "hello" IDF should be lower than "world" IDF
        assert calc.idf["hello"] < calc.idf["world"], \
            f"Expected hello IDF ({calc.idf['hello']:.4f}) < world IDF ({calc.idf['world']:.4f})"

    def test_bm25_query_vector_quality(self):
        """
        Verify query vectors have higher scores for rare terms.
        """
        calc = BM25Calculator()

        # Add documents
        calc.add_document(["the", "quick", "brown", "fox"])      # common words
        calc.add_document(["dog", "cat", "bird"])                # rare words
        calc.add_document(["the", "lazy", "dog"])                # "the" is common

        # Query for rare vs common terms
        rare_query_vec = calc.compute_query_vector("bird")       # rare term
        common_query_vec = calc.compute_query_vector("the")       # common term

        # Find the scores for each term
        rare_score = next((s for idx, s in rare_query_vec if idx == _term_index("bird")), 0)
        common_score = next((s for idx, s in common_query_vec if idx == _term_index("the")), 0)

        # Rare term should have higher IDF-weighted score
        assert rare_score > common_score, \
            f"Rare term score ({rare_score}) should be > common term score ({common_score})"

    def test_bm25_documents_with_repeated_terms(self):
        """
        Verify BM25 properly handles repeated terms in a document.
        """
        calc = BM25Calculator()

        # Document with repeated terms
        vec1 = calc.add_document(["hello", "hello", "hello", "world"])  # "hello" x3

        # Document with single occurrence
        vec2 = calc.add_document(["hello", "world"])  # "hello" x1

        # The repeated term should have higher BM25 score
        # Find "hello" scores in each vector
        hello_idx = _term_index("hello")

        hello_score1 = next((s for idx, s in vec1 if idx == hello_idx), 0)
        hello_score2 = next((s for idx, s in vec2 if idx == hello_idx), 0)

        # Due to term frequency saturation (k1=1.5), repeated term score
        # should be higher but with diminishing returns
        assert hello_score1 > hello_score2, \
            f"Repeated term score ({hello_score1}) should be > single ({hello_score2})"

    def test_bm25_persistence_across_sessions(self):
        """
        Verify IDF statistics persist correctly across save/load cycles.
        """
        calc1 = BM25Calculator()
        calc1.add_document(["apple", "banana", "cherry"])
        calc1.add_document(["banana", "date"])
        calc1.add_document(["cherry", "elderberry"])

        # Save to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name

        try:
            calc1.save(temp_path)

            # Load into new calculator (simulating new session)
            calc2 = BM25Calculator()
            calc2.load(temp_path)

            # Verify statistics match exactly
            assert calc2.corpus_size == calc1.corpus_size
            assert calc2.doc_freqs == calc1.doc_freqs
            assert calc2.idf == calc1.idf
            assert calc2.avg_doc_len == calc1.avg_doc_len

            # Verify new query produces same results
            query_vec1 = calc1.compute_query_vector("apple banana")
            query_vec2 = calc2.compute_query_vector("apple banana")
            assert query_vec1 == query_vec2

        finally:
            os.unlink(temp_path)

    def test_bm25_term_normalization(self):
        """
        Verify terms are normalized (lowercased) consistently.
        """
        calc = BM25Calculator()

        # Add with mixed case
        calc.add_document(["Hello", "WORLD"])

        # Query with different case should produce same result
        vec_upper = calc.compute_query_vector("HELLO world")
        vec_lower = calc.compute_query_vector("hello WORLD")

        assert len(vec_upper) > 0
        assert len(vec_lower) > 0
        # Both should produce same indices (after normalization)
        indices_upper = {idx for idx, _ in vec_upper}
        indices_lower = {idx for idx, _ in vec_lower}
        assert indices_upper == indices_lower


class TestHybridSearchIntegration:
    """Integration tests for hybrid vector + BM25 search."""

    def test_rff_fusion_prefers_items_in_both_results(self):
        """
        Verify RRF fusion ranks highest items that appear in multiple result sets.
        """
        vector_results = [
            {"id": "A", "score": 0.9},
            {"id": "B", "score": 0.85},
            {"id": "C", "score": 0.8},
        ]
        bm25_results = [
            {"id": "B", "score": 0.95},
            {"id": "D", "score": 0.85},
            {"id": "A", "score": 0.75},
        ]

        fused = _reciprocal_rank_fusion([vector_results, bm25_results], k=60)
        fused_ids = [item["id"] for item in fused]

        # "A" and "B" appear in both results, should rank highest
        # Order between A and B depends on their combined scores
        assert fused_ids.index("A") < fused_ids.index("C")  # A in both, C in one
        assert fused_ids.index("A") < fused_ids.index("D")  # A in both, D in one
        assert fused_ids.index("B") < fused_ids.index("D")  # B in both, D in one

    def test_rff_fusion_with_different_k_values(self):
        """
        Verify RRF parameter k affects fusion behavior correctly.
        Higher k = more weight to lower-ranked items.
        """
        vector_results = [{"id": str(i), "score": 1.0 - i * 0.1} for i in range(10)]
        bm25_results = [{"id": str(i), "score": 1.0 - i * 0.1} for i in range(9, -1, -1)]  # reversed

        # With k=0 (aggressive), top-ranked items dominate
        fused_k0 = _reciprocal_rank_fusion([vector_results, bm25_results], k=0)

        # "0" is rank 1 in vector, rank 10 in BM25
        # "9" is rank 10 in vector, rank 1 in BM25
        pos_0_k0 = next(i for i, item in enumerate(fused_k0) if item["id"] == "0")
        pos_9_k0 = next(i for i, item in enumerate(fused_k0) if item["id"] == "9")

        # With k=0, rank 1 dominates more
        # "0" should rank higher than "9"
        assert pos_0_k0 < pos_9_k0  # "0" should rank higher than "9"

    def test_rff_preserves_item_metadata(self):
        """
        Verify RRF fusion preserves original item metadata.
        """
        vector_results = [
            {"id": "A", "score": 0.9, "content": "content A", "user_id": "u1"},
        ]
        bm25_results = [
            {"id": "A", "score": 0.95, "content": "content A", "user_id": "u1"},
        ]

        fused = _reciprocal_rank_fusion([vector_results, bm25_results])

        assert len(fused) == 1
        assert fused[0]["content"] == "content A"
        assert fused[0]["user_id"] == "u1"
        assert "fused_score" in fused[0]


class TestBM25EdgeCases:
    """Edge case tests for BM25 functionality."""

    def test_empty_document(self):
        """Verify handling of empty documents."""
        calc = BM25Calculator()
        vec = calc.add_document([])

        assert vec == [], "Empty document should return empty vector"
        assert calc.corpus_size == 1

    def test_single_term_document(self):
        """Verify handling of single-term documents."""
        calc = BM25Calculator()
        vec = calc.add_document(["only"])

        assert len(vec) == 1
        assert vec[0][0] == _term_index("only")  # term index
        assert vec[0][1] > 0  # positive score

    def test_query_with_unknown_terms(self):
        """Verify handling of query terms not in corpus."""
        calc = BM25Calculator()
        calc.add_document(["hello", "world"])

        # Query with term not in corpus
        query_vec = calc.compute_query_vector("unknown term xyz")

        # Should return vector for "unknown" and "term" and "xyz" if they exist
        # But IDF for unknown terms is 0, so they won't contribute
        # This test verifies no error is raised
        assert isinstance(query_vec, list)

    def test_large_corpus_idf_stability(self):
        """Verify IDF values stabilize as corpus grows."""
        calc = BM25Calculator()

        # Add many similar documents
        for i in range(100):
            calc.add_document(["test", "document", "number", str(i)])

        # IDF for "test" should be relatively stable after many docs
        idf_test = calc.idf.get("test", 0)

        # After 100 docs, IDF should be in a reasonable range
        # log(100) ≈ 4.6, with smoothing it should be < 10
        assert 0 < idf_test < 10, f"IDF ({idf_test}) should be in reasonable range"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
