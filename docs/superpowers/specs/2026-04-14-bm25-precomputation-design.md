# BM25 Precomputation Design

**Date**: 2026-04-14
**Status**: Approved

## Overview

Replace the current "fake BM25" (TF-only vectors) with true BM25 precomputation. At write time, calculate and store the BM25 sparse vector for each memory. At query time, use standard BM25 algorithm with proper IDF weighting.

## Problem: Current Implementation

The current `bm25_search` uses `_text_to_sparse_vector` which:
- Only considers TF (term frequency)
- Ignores IDF (inverse document frequency)
- Is not true BM25

```python
# Current: simplified TF only
def _text_to_sparse_vector(self, text: str) -> List[float]:
    term_hash = hash(term) % 10000  # Hash collision!
    tf = freq / max_freq
    sparse[term_hash] = tf  # No IDF
```

## Solution: True BM25 Precomputation

### Architecture

```
add(memory):
    → Generate embedding vector (existing)
    → Compute BM25 vector using pre-built IDF statistics
    → Insert to Milvus: (embedding, bm25_embedding)

search(query):
    → Compute query BM25 vector with IDF weighting
    → Search in pre-computed bm25_embedding field
```

### Components

#### BM25Calculator

Manages IDF statistics and computes BM25 vectors.

```python
class BM25Calculator:
    """Manages BM25 IDF statistics and vector computation."""

    def __init__(self, corpus_size: int = 0, avg_doc_len: float = 0):
        self.corpus_size = corpus_size      # Total documents
        self.avg_doc_len = avg_doc_len       # Average document length
        self.doc_freqs: Dict[str, int] = {}  # term -> doc frequency
        self.idf: Dict[str, float] = {}      # term -> IDF score

    def add_document(self, terms: List[str]) -> List[Tuple[int, float]]:
        """Add document to corpus, return BM25 sparse vector."""
        # Update document frequency counts
        unique_terms = set(terms)
        for term in unique_terms:
            self.doc_freqs[term] = self.doc_freqs.get(term, 0) + 1

        # Recalculate IDF for affected terms
        self._update_idf(unique_terms)

        # Compute BM25 vector for this document
        return self._compute_bm25_vector(terms)

    def compute_query_vector(self, query: str) -> List[Tuple[int, float]]:
        """Compute BM25 vector for query using current IDF."""
        terms = query.lower().split()
        return self._compute_bm25_vector(terms, is_query=True)

    def _update_idf(self, terms: Set[str]):
        """Update IDF for affected terms."""
        for term in terms:
            df = self.doc_freqs.get(term, 0)
            # Smoothed IDF formula: log((N - n + 0.5) / (n + 0.5) + 1)
            n = max(1, df)
            idf = log((self.corpus_size - n + 0.5) / (n + 0.5) + 1)
            self.idf[term] = idf
```

#### Integration Points

**VectorStoreBase.insert** - extend signature:
```python
def insert(
    self,
    vectors: List[List[float]],
    payloads: Optional[List[Dict[str, Any]]] = None,
    ids: Optional[List[str]] = None,
    bm25_vectors: Optional[List[List[Tuple[int, float]]]] = None
) -> List[str]:
```

**MilvusVectorStore.insert** - handle bm25_vectors:
```python
def insert(self, vectors, payloads=None, ids=None, bm25_vectors=None):
    # Prepare data with both vector types
    data = [...]
    self.collection.insert(data)
```

**BM25Calculator persistence** - save IDF to disk:
```python
def save(self, path: str):
    with open(path, 'w') as f:
        json.dump({
            'corpus_size': self.corpus_size,
            'avg_doc_len': self.avg_doc_len,
            'doc_freqs': self.doc_freqs,
            'idf': self.idf
        }, f)

def load(self, path: str):
    # Load from disk on startup
```

## Data Flow

### Write Path

```
Memory.add(content):
    1. embedding = self.embedding.embed(content)
    2. terms = content.lower().split()
    3. bm25_vector = self.bm25_calculator.add_document(terms)
    4. self.vector_store.insert(
           vectors=[embedding],
           bm25_vectors=[bm25_vector],
           payloads=[payload],
           ids=[memory_id]
       )
```

### Read Path (unchanged)

```
Reader.bm25_search(query):
    1. query_vector = self.bm25_calculator.compute_query_vector(query)
    2. self.vector_store.bm25_search(query_vector, ...)
```

## Milvus Schema Change

The `bm25_embedding` field uses `SPARSE_FLOAT_VECTOR` type (already added).

Sparse vector format: `List[Tuple[int, float]]` where tuple is `(index, value)`.

## Error Handling

| Scenario | Handling |
|----------|----------|
| BM25 calculator not initialized | Fall back to vector-only search |
| Milvus insert fails | Raise error, do not update IDF |
| Empty document | Return empty BM25 vector |
| Unknown term in query | IDF = 0 for that term |

## Testing

1. Unit test `BM25Calculator` with known IDF values
2. Integration test: add documents, verify bm25 vectors stored correctly
3. Query test: verify BM25 results differ from simple TF search

## Files to Modify

| File | Change |
|------|--------|
| `vector_stores/base.py` | Extend `insert` signature |
| `vector_stores/milvus.py` | Implement bm25_vectors handling in insert |
| `memory/storage.py` | Add BM25Calculator, modify _MemoryWriter.add |
| `reranker/bm25.py` | Can be deprecated/removed (not used in new flow) |

## Deliverables

1. `BM25Calculator` class with IDF management
2. Modified `insert` to accept `bm25_vectors`
3. Modified `_MemoryWriter.add` to precompute BM25 at write time
4. Persisted IDF statistics on shutdown, loaded on startup
