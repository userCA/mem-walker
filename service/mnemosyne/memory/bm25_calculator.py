"""BM25 Calculator for true BM25 sparse vector computation."""

import hashlib
import json
import math
import os
from typing import Any, Dict, List, Optional, Set, Tuple

from ..utils import get_logger

logger = get_logger(__name__)


class BM25Calculator:
    """
    Manages BM25 IDF statistics and computes BM25 sparse vectors.

    Uses standard BM25 formula:
    - IDF: log((N - n + 0.5) / (n + 0.5) + 1)
    - BM25 score: IDF * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * |d|/avg_d))
    """

    # BM25 parameters
    K1 = 1.5  # Term frequency saturation
    B = 0.75  # Length normalization

    # Vocabulary size for sparse vector indices
    VOCAB_SIZE = 100000

    def __init__(self, corpus_size: int = 0, avg_doc_len: float = 0.0):
        self.corpus_size = corpus_size
        self.avg_doc_len = avg_doc_len
        self.doc_freqs: Dict[str, int] = {}  # term -> number of docs containing term
        self.idf: Dict[str, float] = {}       # term -> IDF score
        self.total_doc_len: int = 0

    def add_document(self, terms: List[str]) -> List[Tuple[int, float]]:
        """
        Add a document to the corpus and return its BM25 sparse vector.

        Args:
            terms: List of terms in the document

        Returns:
            List of (term_index, bm25_score) tuples for non-zero terms
        """
        if terms is None:
            raise ValueError("terms cannot be None")
        if not terms:
            return []

        self.corpus_size += 1
        doc_len = len(terms)
        self.total_doc_len += doc_len
        self.avg_doc_len = self.total_doc_len / self.corpus_size

        # Update document frequencies
        unique_terms = set(terms)
        for term in unique_terms:
            self.doc_freqs[term] = self.doc_freqs.get(term, 0) + 1

        # Update IDF for affected terms
        self._update_idf(unique_terms)

        # Compute BM25 vector for this document
        return self._compute_doc_bm25_vector(terms)

    def _update_idf(self, terms: Set[str]) -> None:
        """Update IDF scores for affected terms."""
        for term in terms:
            df = self.doc_freqs.get(term, 0)
            # Smoothed IDF formula: log((N - n + 0.5) / (n + 0.5) + 1)
            n = max(1, df)
            idf = math.log((self.corpus_size - n + 0.5) / (n + 0.5) + 1)
            self.idf[term] = idf

    def _compute_doc_bm25_vector(self, terms: List[str]) -> List[Tuple[int, float]]:
        """Compute BM25 sparse vector for a document."""
        # Count term frequencies
        term_freqs: Dict[str, int] = {}
        for term in terms:
            term_freqs[term] = term_freqs.get(term, 0) + 1

        # Compute BM25 score for each term
        doc_len = len(terms)
        doc_vector = []

        for term, tf in term_freqs.items():
            idf = self.idf.get(term, 0.0)

            # BM25 formula: IDF * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * |d|/avg_d))
            numerator = tf * (self.K1 + 1)
            denominator = tf + self.K1 * (1 - self.B + self.B * doc_len / max(self.avg_doc_len, 1))
            bm25_score = idf * numerator / denominator

            if bm25_score > 0:
                # Map term to index via hash (deterministic)
                term_index = int(hashlib.md5(term.encode('utf-8')).hexdigest(), 16) % self.VOCAB_SIZE
                doc_vector.append((term_index, bm25_score))

        return doc_vector

    def compute_query_vector(self, query: str) -> List[Tuple[int, float]]:
        """
        Compute BM25 vector for a query using stored IDF.

        Args:
            query: Query string

        Returns:
            List of (term_index, bm25_score) tuples
        """
        if query is None:
            raise ValueError("query cannot be None")

        terms = query.lower().split()
        term_freqs: Dict[str, int] = {}
        for term in terms:
            term_freqs[term] = term_freqs.get(term, 0) + 1

        query_vector = []
        for term, tf in term_freqs.items():
            idf = self.idf.get(term, 0.0)
            if idf > 0:
                # For query, we use simplified BM25: IDF * tf
                # (no length normalization for query)
                bm25_score = idf * tf
                term_index = int(hashlib.md5(term.encode('utf-8')).hexdigest(), 16) % self.VOCAB_SIZE
                query_vector.append((term_index, bm25_score))

        return query_vector

    def get_idf(self, term: str) -> float:
        """Get IDF score for a term."""
        return self.idf.get(term, 0.0)

    def get_stats(self) -> Dict[str, Any]:
        """Get corpus statistics."""
        return {
            "corpus_size": self.corpus_size,
            "avg_doc_len": self.avg_doc_len,
            "vocab_size": len(self.doc_freqs),
        }

    def save(self, path: str) -> None:
        """Save IDF statistics to disk."""
        data = {
            "corpus_size": self.corpus_size,
            "avg_doc_len": self.avg_doc_len,
            "total_doc_len": self.total_doc_len,
            "doc_freqs": self.doc_freqs,
            "idf": self.idf
        }
        if os.path.dirname(path):
            os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            json.dump(data, f)
        logger.info(f"Saved BM25 statistics to {path}")

    def load(self, path: str) -> None:
        """Load IDF statistics from disk."""
        if not os.path.exists(path):
            logger.warning(f"BM25 statistics file not found: {path}")
            return

        with open(path, 'r') as f:
            data = json.load(f)

        self.corpus_size = data.get("corpus_size", 0)
        self.avg_doc_len = data.get("avg_doc_len", 0.0)
        self.total_doc_len = data.get("total_doc_len", 0)
        self.doc_freqs = data.get("doc_freqs", {})
        self.idf = data.get("idf", {})
        logger.info(f"Loaded BM25 statistics from {path}")