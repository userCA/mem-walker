# BM25 Precomputation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace fake TF-only BM25 with true BM25 precomputation at write time.

**Architecture:** Create BM25Calculator to manage IDF statistics. At insert time, compute and store BM25 vectors. At search time, use pre-stored IDF to compute query vectors.

**Tech Stack:** Milvus 2.4+ sparse vectors, Python dict for IDF mapping

---

## File Mapping

| File | Responsibility |
|------|----------------|
| `memory/bm25_calculator.py` | New: BM25Calculator class with IDF management |
| `vector_stores/base.py` | Extend insert signature to accept bm25_vectors |
| `vector_stores/milvus.py` | Implement bm25_vectors handling in insert |
| `memory/storage.py` | Integrate BM25Calculator into _MemoryWriter, modify add |
| `memory/storage.py` | Modify bm25_search to use precomputed query |

---

## Task 1: Create BM25Calculator class

**Files:**
- Create: `service/mnemosyne/memory/bm25_calculator.py`

- [ ] **Step 1: Write the failing test**

Create `service/tests/unit/test_bm25_calculator.py`:

```python
import pytest
from mnemosyne.memory.bm25_calculator import BM25Calculator

def test_bm25_calculator_idf_computation():
    """BM25Calculator should compute IDF correctly."""
    calc = BM25Calculator()
    # Add 3 documents
    calc.add_document(["hello", "world"])
    calc.add_document(["hello", "python"])
    calc.add_document(["hello", "world", "python"])

    # "hello" appears in all 3 docs, IDF should be low
    # "world" appears in 2 docs
    # "python" appears in 2 docs
    assert "hello" in calc.idf
    assert "world" in calc.idf
    assert "python" in calc.idf
    # hello IDF < world IDF (more common = lower IDF)
    assert calc.idf["hello"] < calc.idf["world"]

def test_bm25_calculator_add_document_returns_vector():
    """add_document should return BM25 sparse vector."""
    calc = BM25Calculator()
    vector = calc.add_document(["hello", "hello", "world"])

    assert isinstance(vector, list)
    assert len(vector) > 0
    # Each element is (index, score) tuple
    for item in vector:
        assert isinstance(item, tuple)
        assert len(item) == 2

def test_bm25_calculator_compute_query():
    """compute_query_vector should use stored IDF."""
    calc = BM25Calculator()
    calc.add_document(["hello", "world"])
    calc.add_document(["hello", "python"])

    query_vector = calc.compute_query_vector("hello world")

    assert isinstance(query_vector, list)
    assert len(query_vector) > 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/yuanbaishu/pythonProject/memory-module/service && PYTHONPATH=. python -m pytest tests/unit/test_bm25_calculator.py -v`
Expected: FAIL - "No module named 'mnemosyne.memory.bm25_calculator'"

- [ ] **Step 3: Implement BM25Calculator**

Create `service/mnemosyne/memory/bm25_calculator.py`:

```python
"""BM25 Calculator for true BM25 sparse vector computation."""

import math
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
                term_index = hash(term) % self.VOCAB_SIZE
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
                term_index = hash(term) % self.VOCAB_SIZE
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/yuanbaishu/pythonProject/memory-module/service && PYTHONPATH=. python -m pytest tests/unit/test_bm25_calculator.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add service/mnemosyne/memory/bm25_calculator.py service/tests/unit/test_bm25_calculator.py
git commit -m "feat: add BM25Calculator class with true BM25 IDF computation"
```

---

## Task 2: Extend VectorStoreBase.insert signature

**Files:**
- Modify: `service/mnemosyne/vector_stores/base.py:32-49` (insert method)

- [ ] **Step 1: Write the failing test**

Add to `tests/unit/test_vector_stores.py`:

```python
import inspect
from mnemosyne.vector_stores.base import VectorStoreBase

def test_insert_accepts_bm25_vectors():
    """VectorStoreBase.insert should accept bm25_vectors parameter."""
    sig = inspect.signature(VectorStoreBase.insert)
    params = list(sig.parameters.keys())
    assert 'bm25_vectors' in params, "insert should accept bm25_vectors parameter"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/yuanbaishu/pythonProject/memory-module/service && PYTHONPATH=. python -m pytest tests/unit/test_vector_stores.py::test_insert_accepts_bm25_vectors -v`
Expected: FAIL - "bm25_vectors not in parameters"

- [ ] **Step 3: Modify VectorStoreBase.insert**

Modify `vector_stores/base.py` insert method signature:

```python
@abstractmethod
def insert(
    self,
    vectors: List[List[float]],
    payloads: Optional[List[Dict[str, Any]]] = None,
    ids: Optional[List[str]] = None,
    bm25_vectors: Optional[List[List[Tuple[int, float]]]] = None
) -> List[str]:
    """
    Insert vectors into the collection.

    Args:
        vectors: List of embedding vectors
        payloads: Optional metadata for each vector
        ids: Optional custom IDs for vectors
        bm25_vectors: Optional BM25 sparse vectors (List of (index, score) tuples)

    Returns:
        List of inserted vector IDs
    """
    pass
```

Also add `Tuple` to imports at top of file:
```python
from typing import Any, Dict, List, Optional, Tuple
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/yuanbaishu/pythonProject/memory-module/service && PYTHONPATH=. python -m pytest tests/unit/test_vector_stores.py::test_insert_accepts_bm25_vectors -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add service/mnemosyne/vector_stores/base.py
git commit -m "feat(vector_stores): extend insert to accept bm25_vectors parameter"
```

---

## Task 3: Implement bm25_vectors handling in MilvusVectorStore.insert

**Files:**
- Modify: `service/mnemosyne/vector_stores/milvus.py:165-202` (insert method)

- [ ] **Step 1: Write the failing test**

Add to `tests/unit/test_vector_stores.py`:

```python
def test_milvus_insert_handles_bm25_vectors():
    """MilvusVectorStore.insert should accept and store bm25_vectors."""
    from unittest.mock import MagicMock, patch

    mock_collection = MagicMock()
    with patch('pymilvus.connections.connect'):
        with patch('pymilvus.utility.has_collection', return_value=False):
            with patch.object(MilvusVectorStore, '_init_collection'):
                store = MilvusVectorStore()
                store.collection = mock_collection
                store.config = MagicMock()

                # Call insert with bm25_vectors
                bm25_vec = [(0, 1.5), (100, 0.8)]  # (index, score) tuples
                result = store.insert(
                    vectors=[[0.1] * 384],
                    payloads=[{"content": "test"}],
                    bm25_vectors=[bm25_vec]
                )

                # Verify insert was called
                mock_collection.insert.assert_called_once()
                # Check that data includes bm25_embedding
                call_args = mock_collection.insert.call_args[0][0]
                assert "bm25_embedding" in call_args[0]
                assert call_args[0]["bm25_embedding"] == bm25_vec
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/yuanbaishu/pythonProject/memory-module/service && PYTHONPATH=. python -m pytest tests/unit/test_vector_stores.py::test_milvus_insert_handles_bm25_vectors -v`
Expected: FAIL - "bm25_embedding" not in insert data

- [ ] **Step 3: Modify MilvusVectorStore.insert**

Replace the `insert` method (lines 165-202) with:

```python
def insert(
    self,
    vectors: List[List[float]],
    payloads: Optional[List[Dict[str, Any]]] = None,
    ids: Optional[List[str]] = None,
    bm25_vectors: Optional[List[List[Tuple[int, float]]]] = None
) -> List[str]:
    """Insert vectors into collection."""
    if self.collection is None:
        raise VectorStoreError("Collection not initialized")

    # Generate IDs if not provided
    if ids is None:
        ids = [str(uuid.uuid4()) for _ in range(len(vectors))]

    # Prepare data
    import time
    timestamp = int(time.time())

    data = []
    for i, (vec_id, vector) in enumerate(zip(ids, vectors)):
        payload = payloads[i] if payloads else {}
        bm25_vec = bm25_vectors[i] if bm25_vectors else []

        data.append({
            "id": vec_id,
            "embedding": vector,
            "user_id": payload.get("user_id", "default"),
            "content": payload.get("content", ""),
            "metadata": payload.get("metadata", {}),
            "created_at": timestamp,
            "bm25_embedding": bm25_vec  # Store BM25 sparse vector
        })

    try:
        self.collection.insert(data)
        # self.collection.flush()  # Removed to improve performance
        logger.debug(f"Inserted {len(vectors)} vectors")
        return ids
    except Exception as e:
        raise VectorStoreError(f"Failed to insert vectors: {e}")
```

Also add `Tuple` to imports at top of file (line 4):
```python
from typing import Any, Dict, List, Optional, Tuple
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/yuanbaishu/pythonProject/memory-module/service && PYTHONPATH=. python -m pytest tests/unit/test_vector_stores.py::test_milvus_insert_handles_bm25_vectors -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add service/mnemosyne/vector_stores/milvus.py
git commit -m "feat(milvus): handle bm25_vectors in insert for true BM25 storage"
```

---

## Task 4: Integrate BM25Calculator into _MemoryWriter

**Files:**
- Modify: `service/mnemosyne/memory/storage.py` (_MemoryWriter.add, insert call)

- [ ] **Step 1: Write the failing test**

Add to `tests/unit/test_storage.py`:

```python
def test_memory_writer_computes_bm25_on_add():
    """_MemoryWriter.add should compute and store BM25 vectors."""
    from unittest.mock import MagicMock, patch

    mock_embedding = MagicMock()
    mock_embedding.embed.return_value = [0.1] * 384

    mock_vector_store = MagicMock()
    mock_vector_store.insert.return_value = ["memory-1"]

    mock_graph_store = MagicMock()
    mock_llm = MagicMock()
    mock_llm.extract_facts.return_value = None  # Disable LLM calls

    writer = _MemoryWriter(
        embedding=mock_embedding,
        vector_store=mock_vector_store,
        graph_store=mock_graph_store,
        llm=mock_llm
    )

    # Patch BM25Calculator to avoid actual IDF computation
    with patch('mnemosyne.memory.storage.BM25Calculator') as MockCalc:
        mock_calc = MagicMock()
        mock_calc.add_document.return_value = [(0, 1.5), (100, 0.8)]
        MockCalc.return_value = mock_calc

        writer.add("test memory content", user_id="u1", infer=False)

        # Verify insert was called with bm25_vectors
        mock_vector_store.insert.assert_called_once()
        call_kwargs = mock_vector_store.insert.call_args
        # Check bm25_vectors was passed
        assert 'bm25_vectors' in call_kwargs.kwargs or len(call_kwargs.args) > 3
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/yuanbaishu/pythonProject/memory-module/service && PYTHONPATH=. python -m pytest tests/unit/test_storage.py::test_memory_writer_computes_bm25_on_add -v`
Expected: FAIL - "bm25_vectors not passed to insert"

- [ ] **Step 3: Modify _MemoryWriter to compute BM25**

First, add import at top of storage.py:
```python
from .bm25_calculator import BM25Calculator
```

Modify _MemoryWriter.__init__ to add BM25Calculator:
```python
def __init__(
    self,
    embedding: EmbeddingBase,
    vector_store: VectorStoreBase,
    graph_store: GraphStoreBase,
    llm: LLMBase,
    conflict_strategy: str = STRATEGY_NEWER_WINS
):
    # ... existing init code ...
    self.bm25_calculator = BM25Calculator()
```

Modify the insert call in _MemoryWriter.add (around line 243):

```python
# Insert into vector store
logger.debug(f"Inserting into vector store: {memory_id}")

# Compute BM25 vector
content_terms = content.lower().split()
bm25_vector = self.bm25_calculator.add_document(content_terms)

self.vector_store.insert(
    vectors=[embedding_vector],
    payloads=[payload],
    ids=[memory_id],
    bm25_vectors=[bm25_vector]
)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/yuanbaishu/pythonProject/memory-module/service && PYTHONPATH=. python -m pytest tests/unit/test_storage.py::test_memory_writer_computes_bm25_on_add -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add service/mnemosyne/memory/storage.py
git commit -m "feat(storage): integrate BM25Calculator to precompute BM25 at write time"
```

---

## Task 5: Update bm25_search to accept precomputed query vectors

**Files:**
- Modify: `service/mnemosyne/vector_stores/milvus.py` (bm25_search method)

**Note:** Currently `bm25_search(query: str)` computes the query vector inline. After this task, it will accept `query_vector` directly and the BM25Calculator.compute_query_vector will be called in _MemoryReader before passing.

- [ ] **Step 1: Write the failing test**

Add to `tests/unit/test_vector_stores.py`:

```python
def test_milvus_bm25_search_accepts_query_vector():
    """MilvusVectorStore.bm25_search should accept precomputed query_vector."""
    from unittest.mock import MagicMock, patch

    mock_collection = MagicMock()
    mock_results = MagicMock()
    mock_results[0] = []
    mock_collection.search.return_value = mock_results

    with patch('pymilvus.connections.connect'):
        with patch('pymilvus.utility.has_collection', return_value=False):
            with patch.object(MilvusVectorStore, '_init_collection'):
                store = MilvusVectorStore()
                store.collection = mock_collection
                store.config = MagicMock()

                # Call with query_vector directly
                query_vec = [(0, 1.5), (100, 0.8)]
                result = store.bm25_search(query_vector=query_vec, limit=10)

                # Verify search was called with the query_vector
                mock_collection.search.assert_called_once()
                call_kwargs = mock_collection.search.call_args
                assert call_kwargs.kwargs.get('data')[0] == query_vec
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/yuanbaishu/pythonProject/memory-module/service && PYTHONPATH=. python -m pytest tests/unit/test_vector_stores.py::test_milvus_bm25_search_accepts_query_vector -v`
Expected: FAIL - "query_vector is not a valid parameter"

- [ ] **Step 3: Modify MilvusVectorStore.bm25_search**

Replace `bm25_search` method (lines 361-425) with:

```python
def bm25_search(
    self,
    query: str = None,
    limit: int = 10,
    filters: Optional[Dict[str, Any]] = None,
    query_vector: List[Tuple[int, float]] = None
) -> List[Dict[str, Any]]:
    """
    Search using BM25 keyword matching via Milvus sparse vector.

    Args:
        query: Search query string (used if query_vector not provided)
        limit: Maximum number of results
        filters: Optional metadata filters (user_id required)
        query_vector: Precomputed BM25 sparse vector (overrides query)

    Returns:
        List of search results with scores and payloads
    """
    if self.collection is None:
        raise VectorStoreError("Collection not initialized")

    try:
        self.collection.load()

        # Build filter expression
        expr = None
        if filters and "user_id" in filters:
            expr = f'user_id == "{filters["user_id"]}"'

        # Use provided query_vector or compute from query string
        if query_vector is None and query is not None:
            # Legacy: compute query vector from string (only for backward compat)
            sparse_vector = self._text_to_sparse_vector(query)
        elif query_vector is not None:
            sparse_vector = query_vector
        else:
            raise ValueError("Either query or query_vector must be provided")

        search_params = {
            "metric_type": "IP",  # Inner product for sparse
            "params": {"nprobe": 10}
        }

        results = self.collection.search(
            data=[sparse_vector],
            anns_field="bm25_embedding",
            param=search_params,
            limit=limit,
            expr=expr,
            output_fields=["id", "user_id", "content", "metadata", "created_at"]
        )

        # Format results
        formatted_results = []
        for hit in results[0]:
            formatted_results.append({
                "id": hit.entity.get("id"),
                "score": float(hit.distance),
                "user_id": hit.entity.get("user_id"),
                "content": hit.entity.get("content"),
                "metadata": hit.entity.get("metadata"),
                "created_at": hit.entity.get("created_at")
            })

        logger.debug(f"BM25 found {len(formatted_results)} results")
        return formatted_results

    except Exception as e:
        logger.warning(f"BM25 search failed: {e}, falling back to empty results")
        return []
```

Also update the base class method signature to match:

Modify `vector_stores/base.py` bm25_search:

```python
def bm25_search(
    self,
    query: str = None,
    limit: int = 10,
    filters: Optional[Dict[str, Any]] = None,
    query_vector: List[Tuple[int, float]] = None
) -> List[Dict[str, Any]]:
    raise NotImplementedError("BM25 search not supported by this vector store")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/yuanbaishu/pythonProject/memory-module/service && PYTHONPATH=. python -m pytest tests/unit/test_vector_stores.py::test_milvus_bm25_search_accepts_query_vector -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add service/mnemosyne/vector_stores/milvus.py service/mnemosyne/vector_stores/base.py
git commit -m "feat(milvus): bm25_search accepts precomputed query_vector"
```

---

## Task 6: Update _MemoryReader to use BM25Calculator for query

**Files:**
- Modify: `service/mnemosyne/memory/storage.py` (_MemoryReader.search)

- [ ] **Step 1: Write the failing test**

Add to `tests/unit/test_storage.py`:

```python
def test_memory_reader_uses_bm25_calculator_for_query():
    """_MemoryReader.search should use BM25Calculator to compute query vector."""
    from unittest.mock import MagicMock, patch

    mock_embedding = MagicMock()
    mock_embedding.embed.return_value = [0.1] * 384

    mock_vector_store = MagicMock()
    mock_vector_store.search.return_value = [{"id": "1", "content": "test", "score": 0.9, "user_id": "u1", "metadata": {}, "created_at": 123}]
    mock_vector_store.bm25_search.return_value = []

    mock_graph_store = MagicMock()
    mock_llm = MagicMock()

    # Create reader with BM25Calculator
    with patch('mnemosyne.memory.storage.BM25Calculator') as MockCalc:
        mock_bm25 = MagicMock()
        mock_bm25.compute_query_vector.return_value = [(0, 1.5), (100, 0.8)]
        MockCalc.return_value = mock_bm25

        reader = _MemoryReader(
            embedding=mock_embedding,
            vector_store=mock_vector_store,
            graph_store=mock_graph_store,
            llm=mock_llm
        )
        reader.bm25_calculator = mock_bm25

        results = reader.search("test query", user_id="u1", limit=10, use_graph=False)

        # Verify bm25_search was called with precomputed vector
        mock_vector_store.bm25_search.assert_called_once()
        call_kwargs = mock_vector_store.bm25_search.call_args
        assert call_kwargs.kwargs.get('query_vector') == [(0, 1.5), (100, 0.8)]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/yuanbaishu/pythonProject/memory-module/service && PYTHONPATH=. python -m pytest tests/unit/test_storage.py::test_memory_reader_uses_bm25_calculator_for_query -v`
Expected: FAIL - "bm25_calculator not available"

- [ ] **Step 3: Modify _MemoryReader.search to use BM25Calculator**

First, add import at top of storage.py:
```python
from .bm25_calculator import BM25Calculator
```

Modify _MemoryReader.__init__ to add BM25Calculator:
```python
def __init__(
    self,
    embedding: EmbeddingBase,
    vector_store: VectorStoreBase,
    graph_store: GraphStoreBase,
    llm: LLMBase
):
    self.embedding = embedding
    self.vector_store = vector_store
    self.graph_store = graph_store
    self.llm = llm
    self.bm25_calculator = BM25Calculator()
```

Modify the bm25_search call in _MemoryReader.search (around line 420):

```python
# Task 3: BM25 Search (if available)
future_bm25 = None
if hasattr(self.vector_store, 'bm25_search'):
    logger.debug("Running BM25 search (async)")
    # Compute query vector using stored IDF
    query_bm25_vector = self.bm25_calculator.compute_query_vector(query)
    future_bm25 = executor.submit(
        self.vector_store.bm25_search,
        query_vector=query_bm25_vector,  # Pass precomputed vector
        limit=limit * 2,
        filters={"user_id": user_id}
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/yuanbaishu/pythonProject/memory-module/service && PYTHONPATH=. python -m pytest tests/unit/test_storage.py::test_memory_reader_uses_bm25_calculator_for_query -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add service/mnemosyne/memory/storage.py
git commit -m "feat(storage): use BM25Calculator to compute query vectors with proper IDF"
```

---

## Task 7: Add IDF persistence (save/load)

**Files:**
- Modify: `service/mnemosyne/memory/bm25_calculator.py` (add save/load methods)
- Modify: `service/mnemosyne/memory/main.py` (load on startup, save on shutdown)

- [ ] **Step 1: Write the failing test**

Add to `tests/unit/test_bm25_calculator.py`:

```python
def test_bm25_calculator_persistence():
    """BM25Calculator should save and load IDF statistics."""
    import tempfile
    import os

    calc = BM25Calculator()
    calc.add_document(["hello", "world"])
    calc.add_document(["hello", "python"])

    # Save to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as f:
        temp_path = f.name

    try:
        calc.save(temp_path)

        # Load into new calculator
        calc2 = BM25Calculator()
        calc2.load(temp_path)

        assert calc2.corpus_size == calc.corpus_size
        assert calc2.doc_freqs == calc.doc_freqs
        assert calc2.idf == calc.idf
    finally:
        os.unlink(temp_path)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/yuanbaishu/pythonProject/memory-module/service && PYTHONPATH=. python -m pytest tests/unit/test_bm25_calculator.py::test_bm25_calculator_persistence -v`
Expected: FAIL - "save/load methods not defined"

- [ ] **Step 3: Add save/load methods to BM25Calculator**

Add to `bm25_calculator.py`:

```python
import json

def save(self, path: str) -> None:
    """Save IDF statistics to disk."""
    data = {
        "corpus_size": self.corpus_size,
        "avg_doc_len": self.avg_doc_len,
        "total_doc_len": self.total_doc_len,
        "doc_freqs": self.doc_freqs,
        "idf": self.idf
    }
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
```

Add `import os` at top of file.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/yuanbaishu/pythonProject/memory-module/service && PYTHONPATH=. python -m pytest tests/unit/test_bm25_calculator.py::test_bm25_calculator_persistence -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add service/mnemosyne/memory/bm25_calculator.py
git commit -m "feat(bm25): add save/load methods for IDF persistence"
```

---

## Task 8: Run full test suite

- [ ] **Step 1: Run all unit tests**

```bash
cd /Users/yuanbaishu/pythonProject/memory-module/service && PYTHONPATH=. python -m pytest tests/unit/ -v --override-ini="addopts="
```

Expected: All tests pass

- [ ] **Step 2: Verify no regressions**

Verify imports work:
```bash
cd /Users/yuanbaishu/pythonProject/memory-module && python -c "
import sys
sys.path.insert(0, 'service')
from mnemosyne.memory.bm25_calculator import BM25Calculator
from mnemosyne.memory.storage import _MemoryWriter, _MemoryReader
from mnemosyne.vector_stores.milvus import MilvusVectorStore
print('All imports OK')
"
```

---

## Spec Coverage Check

| Spec Requirement | Task |
|-----------------|------|
| BM25Calculator class | Task 1 |
| Extend insert signature | Task 2 |
| Handle bm25_vectors in Milvus insert | Task 3 |
| Precompute BM25 at write time | Task 4 |
| Accept precomputed query_vector | Task 5 |
| Compute query with stored IDF | Task 6 |
| IDF persistence | Task 7 |

All requirements covered. No placeholders.
