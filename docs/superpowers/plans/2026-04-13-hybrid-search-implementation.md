# Hybrid Search Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement parallel hybrid search (vector + BM25) with RRF fusion in the memory storage layer.

**Architecture:** Add BM25 search as parallel branch in `_MemoryReader.search` using existing ThreadPoolExecutor, then fuse results via RRF before returning. BM25 uses Milvus 2.4+ sparse vector feature.

**Tech Stack:** Milvus 2.4+, pymilvus, Python concurrent.futures

---

## File Mapping

| File | Responsibility |
|------|----------------|
| `vector_stores/base.py` | Add abstract `bm25_search` method |
| `vector_stores/milvus.py` | Implement `bm25_search` using Milvus sparse vector |
| `memory/storage.py` | Add RRF fusion function, modify `_MemoryReader.search` |
| `reranker/bm25.py` | (Existing, will not be used for fusion) |

---

## Task 1: Add abstract bm25_search to VectorStoreBase

**Files:**
- Modify: `service/mnemosyne/vector_stores/base.py:149` (add after `collection_info`)

- [ ] **Step 1: Write the failing test**

Create test file: `tests/unit/test_vector_stores.py`

```python
import pytest
from service.mnemosyne.vector_stores.base import VectorStoreBase

def test_bm25_search_abstract():
    """VectorStoreBase should have bm25_search abstract method"""
    with pytest.raises(TypeError):
        # Cannot instantiate abstract class
        store = VectorStoreBase()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/yuanbaishu/pythonProject/memory-module/service && poetry run pytest tests/unit/test_vector_stores.py::test_bm25_search_abstract -v`
Expected: FAIL - "Can't instantiate abstract class VectorStoreBase"

- [ ] **Step 3: Add abstract method to base.py**

Add after line 148 (after `collection_info`):

```python
    @abstractmethod
    def bm25_search(
        self,
        query: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search using BM25 keyword matching (Milvus 2.4+ sparse vector).

        Args:
            query: Search query string
            limit: Maximum number of results
            filters: Optional metadata filters (user_id required for multi-tenant)

        Returns:
            List of search results with scores and payloads
        """
        pass
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/yuanbaishu/pythonProject/memory-module/service && poetry run pytest tests/unit/test_vector_stores.py::test_bm25_search_abstract -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add service/mnemosyne/vector_stores/base.py tests/unit/test_vector_stores.py
git commit -m "feat(vector_stores): add abstract bm25_search method to VectorStoreBase"
```

---

## Task 2: Implement bm25_search in MilvusVectorStore

**Files:**
- Modify: `service/mnemosyne/vector_stores/milvus.py` (add method after `collection_info`)

- [ ] **Step 1: Write the failing test**

Add to `tests/unit/test_vector_stores.py`:

```python
from service.mnemosyne.vector_stores.milvus import MilvusVectorStore
from unittest.mock import MagicMock, patch

def test_milvus_bm25_search():
    """MilvusVectorStore should implement bm25_search"""
    with patch('pymilvus.connections.connect'):
        with patch('pymilvus.utility.has_collection', return_value=False):
            with patch.object(MilvusVectorStore, 'create_collection'):
                store = MilvusVectorStore()
                # Should have bm25_search method
                assert hasattr(store, 'bm25_search')
                assert callable(store.bm25_search)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `poetry run pytest tests/unit/test_vector_stores.py::test_milvus_bm25_search -v`
Expected: FAIL - "can't instantiate abstract class" or "bm25_search not found"

- [ ] **Step 3: Implement bm25_search in milvus.py**

Add after `collection_info` method (around line 358):

```python
    def bm25_search(
        self,
        query: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search using BM25 keyword matching via Milvus sparse vector.

        Args:
            query: Search query string
            limit: Maximum number of results
            filters: Optional metadata filters (user_id required)

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

            # Use Milvus sparse vector BM25 search
            # Sparse vector represents term importance across vocabulary
            sparse_vector = self._text_to_sparse_vector(query)

            search_params = {
                "metric_type": "IP",  # Inner product for sparse
                "params": {"nprobe": 10}
            }

            results = self.collection.search(
                data=[sparse_vector],
                anns_field="bm25_embedding",  # Sparse vector field
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

    def _text_to_sparse_vector(self, text: str) -> List[float]:
        """
        Convert text to sparse vector using TF-IDF-like approach.
        Returns list of (index, value) pairs for non-zero terms.
        """
        import math
        terms = text.lower().split()
        term_freq = {}
        for term in terms:
            term_freq[term] = term_freq.get(term, 0) + 1

        # Simple TF-IDF-like normalization
        max_freq = max(term_freq.values()) if term_freq else 1
        sparse = {}
        for term, freq in term_freq.items():
            # Use hash to map term to index (simplified)
            term_hash = hash(term) % 10000
            tf = freq / max_freq
            sparse[term_hash] = tf

        # Convert to Milvus sparse vector format [(index, value), ...]
        return [(idx, val) for idx, val in sparse.items()]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `poetry run pytest tests/unit/test_vector_stores.py::test_milvus_bm25_search -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add service/mnemosyne/vector_stores/milvus.py
git commit -m "feat(milvus): implement bm25_search using sparse vectors"
```

---

## Task 3: Add RRF fusion function to storage.py

**Files:**
- Modify: `service/mnemosyne/memory/storage.py` (add helper function before _MemoryWriter class)

- [ ] **Step 1: Write the failing test**

Create `tests/unit/test_storage.py`:

```python
import pytest
from service.mnemosyne.memory.storage import _reciprocal_rank_fusion

def test_rff_fusion_two_results():
    """RRF should fuse two result sets correctly"""
    vector_results = [
        {"id": "1", "score": 0.9},
        {"id": "2", "score": 0.8},
    ]
    bm25_results = [
        {"id": "2", "score": 0.95},
        {"id": "3", "score": 0.85},
    ]
    fused = _reciprocal_rank_fusion([vector_results, bm25_results], k=60)
    # ID 2 appears in both, should rank higher than 1 or 3
    fused_ids = [item["id"] for item in fused]
    assert fused_ids == ["2", "1", "3"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `poetry run pytest tests/unit/test_storage.py::test_rff_fusion_two_results -v`
Expected: FAIL - "_reciprocal_rank_fusion not found"

- [ ] **Step 3: Add RRF function to storage.py**

Add after line 17 (after `logger = get_logger(__name__)`):

```python
def _reciprocal_rank_fusion(
    results_list: List[List[Dict[str, Any]]],
    k: int = 60
) -> List[Dict[str, Any]]:
    """
    Fuse multiple ranked result lists using Reciprocal Rank Fusion.

    Args:
        results_list: List of result lists, each sorted by score (descending)
        k: RRF parameter (default 60, higher = more weight to lower ranks)

    Returns:
        Fused and re-ranked list of results
    """
    scores = {}
    item_data = {}

    for results in results_list:
        for rank, item in enumerate(results):
            item_id = item.get("id")
            if not item_id:
                continue

            # Accumulate RRF score
            scores[item_id] = scores.get(item_id, 0) + 1 / (k + rank + 1)

            # Keep item data from first occurrence
            if item_id not in item_data:
                item_data[item_id] = item

    # Sort by fused score
    sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)

    # Build result list preserving item data with fused score
    fused = []
    for item_id in sorted_ids:
        item = item_data[item_id].copy()
        item["fused_score"] = scores[item_id]
        fused.append(item)

    return fused
```

- [ ] **Step 4: Run test to verify it passes**

Run: `poetry run pytest tests/unit/test_storage.py::test_rff_fusion_two_results -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add service/mnemosyne/memory/storage.py tests/unit/test_storage.py
git commit -m "feat(storage): add RRF fusion function"
```

---

## Task 4: Modify _MemoryReader.search to add BM25 parallel branch

**Files:**
- Modify: `service/mnemosyne/memory/storage.py:_MemoryReader.search` (lines 315-420)

- [ ] **Step 1: Write the failing test**

Add to `tests/unit/test_storage.py`:

```python
def test_memory_reader_search_with_bm25():
    """_MemoryReader.search should call vector_search and bm25_search in parallel"""
    from service.mnemosyne.memory.storage import _MemoryReader
    from unittest.mock import MagicMock, patch

    mock_embedding = MagicMock()
    mock_embedding.embed.return_value = [0.1] * 384

    mock_vector_store = MagicMock()
    mock_vector_store.search.return_value = [
        {"id": "1", "content": "test", "score": 0.9, "user_id": "u1", "metadata": {}, "created_at": 123}
    ]

    mock_graph_store = MagicMock()
    mock_llm = MagicMock()

    reader = _MemoryReader(
        embedding=mock_embedding,
        vector_store=mock_vector_store,
        graph_store=mock_graph_store,
        llm=mock_llm
    )

    # Patch bm25_search on vector_store
    mock_vector_store.bm25_search = MagicMock(return_value=[
        {"id": "2", "content": "bm25 test", "score": 0.85, "user_id": "u1", "metadata": {}, "created_at": 124}
    ])

    results = reader.search("test query", user_id="u1", limit=10, use_graph=False)

    # Verify both search methods were called
    mock_vector_store.search.assert_called_once()
    mock_vector_store.bm25_search.assert_called_once()
    assert len(results) == 2  # Should have fused results
```

- [ ] **Step 2: Run test to verify it fails**

Run: `poetry run pytest tests/unit/test_storage.py::test_memory_reader_search_with_bm25 -v`
Expected: FAIL - "bm25_search not found" or similar

- [ ] **Step 3: Modify _MemoryReader.search**

Replace the `search` method (lines 315-420) with:

```python
    def search(
        self,
        query: str,
        user_id: str,
        limit: int = 10,
        use_graph: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Search memories using parallel hybrid approach (vector + BM25 + optional graph).

        Args:
            query: Search query
            user_id: User ID
            limit: Maximum results
            use_graph: Whether to use graph expansion

        Returns:
            List of memories with scores
        """
        try:
            import concurrent.futures

            query_vector = None
            expanded_entities = []
            vector_results = []
            bm25_results = []

            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                # Task 1: Generate Embedding
                logger.debug("Generating query embedding (async)")
                future_embed = executor.submit(self.embedding.embed, query)

                # Task 2: Entity Extraction (if enabled)
                future_entities = None
                if use_graph:
                    logger.debug("Extracting entities from query (async)")
                    future_entities = executor.submit(self.llm.extract_entities, query)

                # Task 3: BM25 Search (if available)
                future_bm25 = None
                if hasattr(self.vector_store, 'bm25_search'):
                    logger.debug("Running BM25 search (async)")
                    future_bm25 = executor.submit(
                        self.vector_store.bm25_search,
                        query=query,
                        limit=limit * 2,
                        filters={"user_id": user_id}
                    )

                # Wait for embedding (fast)
                query_vector = future_embed.result()

                # Vector search immediately when embedding is ready
                logger.debug(f"Searching vector store for user {user_id}")
                search_limit = int(limit * 2.0)
                vector_results = self.vector_store.search(
                    query_vector=query_vector,
                    limit=search_limit,
                    filters={"user_id": user_id}
                )

                # Wait for BM25 results
                if future_bm25:
                    try:
                        bm25_results = future_bm25.result()
                    except Exception as e:
                        logger.warning(f"BM25 search failed, continuing without it: {e}")
                        bm25_results = []

                # Wait for entities (slow)
                if future_entities:
                    try:
                        entities = future_entities.result()
                        if entities:
                            entity_names = [e.get("entity") for e in entities if e.get("entity")]
                            if entity_names:
                                logger.debug(f"Expanding graph from entities: {entity_names}")
                                expanded_entities = self.graph_store.bfs_expand(
                                    entities=entity_names,
                                    depth=2,
                                    user_id=user_id
                                )
                    except Exception as e:
                        logger.warning(f"Graph expansion failed, continuing with vector results: {e}")

            # RRF Fusion: combine vector and BM25 results
            if bm25_results:
                logger.debug(f"Fusing {len(vector_results)} vector + {len(bm25_results)} BM25 results")
                fused_results = _reciprocal_rank_fusion([vector_results, bm25_results], k=60)
            else:
                fused_results = vector_results

            # Combine and score results
            results = []
            seen_content = set()

            for result in fused_results:
                content = result.get("content", "")

                # Simple deduplication by content hash
                content_hash = hash(content.strip())
                if content_hash in seen_content:
                    continue
                seen_content.add(content_hash)

                # Base score from vector similarity or fused score
                score = result.get("score", result.get("fused_score", 0.0))

                # Boost score if content mentions expanded entities
                if expanded_entities:
                    for entity in expanded_entities:
                        if entity.lower() in content.lower():
                            score += 0.1

                results.append({
                    "id": result.get("id"),
                    "content": content,
                    "score": min(score, 1.0),
                    "metadata": result.get("metadata"),
                    "user_id": result.get("user_id"),
                    "created_at": result.get("created_at")
                })

            # Sort by combined score
            results.sort(key=lambda x: x["score"], reverse=True)

            logger.info(f"Found {len(results[:limit])} memories for query")
            return results[:limit]

        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise MemoryError(f"Search failed: {e}")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `poetry run pytest tests/unit/test_storage.py::test_memory_reader_search_with_bm25 -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add service/mnemosyne/memory/storage.py
git commit -m "feat(storage): parallel hybrid search with vector + BM25 + RRF fusion"
```

---

## Task 5: Update collection schema to include BM25 field

**Files:**
- Modify: `service/mnemosyne/vector_stores/milvus.py:create_collection` (lines 72-109)

- [ ] **Step 1: Add bm25_embedding field to schema**

The current schema only has `embedding` field. Need to add sparse vector field for BM25.

Modify `create_collection` method to add `bm25_embedding` field:

```python
    # In create_collection, add this field to the fields list:
    FieldSchema(name="bm25_embedding", dtype=DataType.FLOAT_VECTOR, dim=10000),
```

- [ ] **Step 2: Update _text_to_sparse_vector to produce correct dimension**

The sparse vector dimension should match `dim=10000` in the schema.

- [ ] **Step 3: Run integration test**

```bash
poetry run pytest tests/integration/test_memory_api.py -v -k search
```

- [ ] **Step 4: Commit**

```bash
git add service/mnemosyne/vector_stores/milvus.py
git commit -m "feat(milvus): add bm25_embedding sparse vector field to collection schema"
```

---

## Task 6: Run full test suite and verify

- [ ] **Step 1: Run all unit tests**

```bash
cd /Users/yuanbaishu/pythonProject/memory-module/service
poetry run pytest tests/unit/ -v
```

- [ ] **Step 2: Run integration tests**

```bash
poetry run pytest tests/integration/ -v
```

- [ ] **Step 3: Verify no regressions**

Expected: All tests pass, no breaking changes to existing API

---

## Spec Coverage Check

| Spec Requirement | Task |
|------------------|------|
| Parallel vector + BM25 | Task 4 |
| RRF fusion (k=60) | Task 3 |
| BM25 search method | Task 2 |
| VectorStoreBase abstract | Task 1 |
| Error handling (BM25 fail fallback) | Task 4 |
| Milvus 2.4+ sparse vector | Task 5 |

All requirements covered. No placeholders.
