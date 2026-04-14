# Milvus UserId Partition Key Design

## Overview

Add user_id as a Partition Key in `MilvusVectorStore` to enable automatic user-based data routing. This reduces search scan volume by 90%+ by ensuring queries targeting a specific user only scan that user's partition.

## Background

Currently, `MilvusVectorStore` stores `user_id` as a regular VARCHAR field with a scalar index. When searching with a user_id filter, Milvus must scan the entire collection and then apply the filter expression. With partition keys, Milvus automatically routes queries to the relevant partition based on user_id value.

## Design

### 1. Schema Change

**File**: `service/mnemosyne/vector_stores/milvus.py:87`

```python
# Before
FieldSchema(name="user_id", dtype=DataType.VARCHAR, max_length=64),

# After
FieldSchema(name="user_id", dtype=DataType.VARCHAR, max_length=64, is_partition_key=True),
```

**Constraint**: `is_partition_key` cannot be combined with `is_primary_key`. The `id` field remains the primary key.

### 2. Migration Strategy: Forced Rebuild

Old collections without partition key are automatically detected and rebuilt:

```python
def _init_collection(self) -> None:
    collection_name = self.config.collection_name

    if utility.has_collection(collection_name):
        if self._needs_rebuild():
            logger.warning(f"Collection {collection_name} lacks partition key, rebuilding...")
            utility.drop_collection(collection_name)
            self.create_collection(
                name=collection_name,
                vector_size=self.config.vector_size,
                distance_metric=self.config.distance_metric
            )
        else:
            logger.info(f"Loading existing collection: {collection_name}")
            self.collection = Collection(collection_name)
            self._ensure_scalar_indexes()
            self._ensure_bm25_index()
            self.collection.load()
    else:
        self.create_collection(...)
```

### 3. Detection Logic

```python
def _needs_rebuild(self) -> bool:
    """Check if collection needs rebuild (missing partition key)."""
    try:
        for field in self.collection.schema.fields:
            if field.name == "user_id" and field.is_partition_key:
                return False  # Has partition key
        return True  # Needs rebuild
    except:
        return False
```

### 4. Search Behavior

Existing search code remains unchanged:

```python
expr = f'user_id == "{filters["user_id"]}"'
```

Milvus automatically optimizes partition key filters to route directly to the target partition.

| Scenario | Before | After |
|----------|--------|-------|
| Search with user_id | Full scan + filter | Direct partition routing |
| Search without user_id | Full scan | Full scan (no optimization) |

### 5. Configuration

`MilvusConfig.scalar_index_config` - the `user_id` entry becomes redundant but can remain harmlessly.

## Implementation Steps

1. Add `_needs_rebuild()` method to `MilvusVectorStore`
2. Modify `_init_collection()` to check and rebuild if needed
3. Update schema in `create_collection()` to use `is_partition_key=True`
4. Verify existing tests pass

## Verification

1. Insert vectors for 3 different user_ids
2. Search with user_id=A, verify only A's data returned
3. Search with user_id=B, verify only B's data returned
4. Verify complete isolation between users

## Files Modified

- `service/mnemosyne/vector_stores/milvus.py`
