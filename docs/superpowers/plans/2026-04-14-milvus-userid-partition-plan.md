# Milvus UserId Partition Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `user_id` as a Partition Key in `MilvusVectorStore` to enable automatic user-based data routing, reducing search scan volume by 90%+.

**Architecture:** Modify the `user_id` field schema to use `is_partition_key=True`. Add detection logic to automatically rebuild old collections lacking the partition key. Existing search filters remain unchanged as Milvus auto-optimizes partition key lookups.

**Tech Stack:** Python, PyMilvus, Milvus vector database

---

## File Mapping

**Modified:**
- `service/mnemosyne/vector_stores/milvus.py` - Main implementation (schema change, rebuild detection)

---

## Task 1: Add `_needs_rebuild()` Method

**Files:**
- Modify: `service/mnemosyne/vector_stores/milvus.py`

- [ ] **Step 1: Add `_needs_rebuild()` method after `_ensure_bm25_index()` (line 214)**

```python
def _needs_rebuild(self) -> bool:
    """
    Check if collection needs rebuild (missing partition key).

    Returns True if the existing collection lacks the user_id partition key
    and needs to be rebuilt.
    """
    if self.collection is None:
        return False

    try:
        for field in self.collection.schema.fields:
            if field.name == "user_id" and field.is_partition_key:
                return False  # Has partition key, no rebuild needed
        return True  # Missing partition key
    except Exception as e:
        logger.warning(f"Failed to check partition key status: {e}")
        return True  # Assume rebuild needed on error
```

- [ ] **Step 2: Verify syntax**

Run: `cd /Users/yuanbaishu/pythonProject/memory-module/service && poetry run python -c "from mnemosyne.vector_stores.milvus import MilvusVectorStore; print('OK')"`
Expected: No errors

- [ ] **Step 3: Commit**

```bash
git add service/mnemosyne/vector_stores/milvus.py
git commit -m "feat(milvus): add _needs_rebuild() method to detect missing partition key"
```

---

## Task 2: Modify `_init_collection()` to Check and Rebuild

**Files:**
- Modify: `service/mnemosyne/vector_stores/milvus.py`

- [ ] **Step 1: Update `_init_collection()` method (lines 53-73)**

Replace the existing `_init_collection()` logic:

```python
def _init_collection(self) -> None:
    """Initialize or load collection."""
    collection_name = self.config.collection_name

    if utility.has_collection(collection_name):
        logger.info(f"Loading existing collection: {collection_name}")
        self.collection = Collection(collection_name)

        # Check if rebuild is needed (missing partition key)
        if self._needs_rebuild():
            logger.warning(
                f"Collection {collection_name} lacks user_id partition key, "
                "rebuilding collection to enable partition-based routing..."
            )
            utility.drop_collection(collection_name)
            self.create_collection(
                name=collection_name,
                vector_size=self.config.vector_size,
                distance_metric=self.config.distance_metric
            )
        else:
            # Create any missing indexes BEFORE loading the collection
            self._ensure_scalar_indexes()
            # Ensure BM25 sparse vector index exists
            self._ensure_bm25_index()
            # Now load the collection
            self.collection.load()
    else:
        logger.info(f"Creating new collection: {collection_name}")
        self.create_collection(
            name=collection_name,
            vector_size=self.config.vector_size,
            distance_metric=self.config.distance_metric
        )
        self.collection.load()
```

- [ ] **Step 2: Verify syntax**

Run: `cd /Users/yuanbaishu/pythonProject/memory-module/service && poetry run python -c "from mnemosyne.vector_stores.milvus import MilvusVectorStore; print('OK')"`
Expected: No errors

- [ ] **Step 3: Commit**

```bash
git add service/mnemosyne/vector_stores/milvus.py
git commit -m "feat(milvus): auto-rebuild collection when partition key missing"
```

---

## Task 3: Update Schema to Use `is_partition_key=True`

**Files:**
- Modify: `service/mnemosyne/vector_stores/milvus.py`

- [ ] **Step 1: Update `user_id` field in `create_collection()` (line 87)**

```python
# Change from:
FieldSchema(name="user_id", dtype=DataType.VARCHAR, max_length=64),

# To:
FieldSchema(name="user_id", dtype=DataType.VARCHAR, max_length=64, is_partition_key=True),
```

- [ ] **Step 2: Verify syntax**

Run: `cd /Users/yuanbaishu/pythonProject/memory-module/service && poetry run python -c "from mnemosyne.vector_stores.milvus import MilvusVectorStore; print('OK')"`
Expected: No errors

- [ ] **Step 3: Commit**

```bash
git add service/mnemosyne/vector_stores/milvus.py
git commit -m "feat(milvus): set user_id as partition key for 90%+ scan reduction"
```

---

## Task 4: Integration Test

**Files:**
- Test: `service/tests/integration/test_milvus_partition.py` (create new)

- [ ] **Step 1: Create integration test file**

```python
"""Integration test for Milvus user_id partition key."""
import pytest
from mnemosyne.vector_stores.milvus import MilvusVectorStore
from mnemosyne.vector_stores.configs import MilvusConfig


class TestMilvusUserIdPartition:
    """Test user_id partition key functionality."""

    @pytest.fixture
    def milvus_config(self):
        """Create test config with unique collection name."""
        config = MilvusConfig()
        config.collection_name = f"test_partition_{id(self)}"
        return config

    @pytest.fixture
    def store(self, milvus_config):
        """Create and return vector store."""
        store = MilvusVectorStore(milvus_config)
        yield store
        # Cleanup
        try:
            store.delete_collection()
        except:
            pass

    def test_partition_key_enabled(self, store):
        """Verify user_id is configured as partition key."""
        # Check schema
        schema_fields = {f.name: f for f in store.collection.schema.fields}
        assert "user_id" in schema_fields
        assert schema_fields["user_id"].is_partition_key is True

    def test_user_isolation(self, store):
        """Verify search only returns data for specified user."""
        # Insert vectors for different users
        vectors = [[0.1] * 1536, [0.2] * 1536, [0.3] * 1536]
        payloads = [
            {"user_id": "alice", "content": "Alice's data"},
            {"user_id": "bob", "content": "Bob's data"},
            {"user_id": "alice", "content": "Alice's second data"},
        ]

        store.insert(vectors, payloads)

        # Search for alice - should only get alice's data
        results = store.search(
            query_vector=[0.1] * 1536,
            limit=10,
            filters={"user_id": "alice"}
        )

        assert len(results) == 2
        user_ids = {r["user_id"] for r in results}
        assert user_ids == {"alice"}

    def test_no_user_filter_returns_all(self, store):
        """Verify search without user_id filter returns all data."""
        vectors = [[0.1] * 1536, [0.2] * 1536]
        payloads = [
            {"user_id": "alice", "content": "Alice's data"},
            {"user_id": "bob", "content": "Bob's data"},
        ]

        store.insert(vectors, payloads)

        # Search without user filter
        results = store.search(
            query_vector=[0.1] * 1536,
            limit=10
        )

        assert len(results) == 2
```

- [ ] **Step 2: Run test (requires running Milvus instance)**

Run: `cd /Users/yuanbaishu/pythonProject/memory-module/service && poetry run pytest service/tests/integration/test_milvus_partition.py -v`
Expected: PASS (or SKIP if no Milvus available)

- [ ] **Step 3: Commit**

```bash
git add service/tests/integration/test_milvus_partition.py
git commit -m "test(milvus): add partition key integration test"
```

---

## Summary

| Task | Description | Files |
|------|-------------|-------|
| 1 | Add `_needs_rebuild()` method | milvus.py |
| 2 | Modify `_init_collection()` for auto-rebuild | milvus.py |
| 3 | Update schema with `is_partition_key=True` | milvus.py |
| 4 | Integration test | test_milvus_partition.py |
