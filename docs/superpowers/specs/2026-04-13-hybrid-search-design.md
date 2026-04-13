# Hybrid Search Design: Vector + BM25 Parallel Retrieval

**Date**: 2026-04-13
**Status**: Approved

## Overview

Implement parallel hybrid search combining vector similarity and BM25 keyword matching with Reciprocal Rank Fusion (RRF) for the Mnemosyne memory system.

## Architecture

```
Query
  │
  ├─── ThreadPoolExecutor (parallel)
  │       ├── embed(query) ─→ query_vector ─→ Milvus vector search ─→ results_vector
  │       │
  │       └── BM25Search(query, user_id) ─→ results_bm25
  │
  └─── RRF Fusion (k=60) ─→ final_results
```

## Data Flow

### Add Memory
- Write to Milvus vector storage (existing)
- Write to Milvus BM25 index (new, synchronous)
- No extra storage copy needed

### Search Memory
- Parallel execution: vector search (limit*2) + BM25 search (limit*2)
- RRF fusion (k=60)
- Return top_k results

## Changes

### 1. `vector_stores/milvus.py`
- Add `bm25_search()` method using Milvus 2.4+ BM25/sparse vector
- No new files required

### 2. `memory/storage.py` (_MemoryReader.search)
- Add BM25 branch in ThreadPoolExecutor
- Add RRF fusion before returning results
- Handle BM25 failures gracefully

## RRF Algorithm

```python
def reciprocal_rank_fusion(results_list, k=60):
    scores = {}
    for results in results_list:
        for rank, item in enumerate(results):
            item_id = item["id"]
            scores[item_id] = scores.get(item_id, 0) + 1 / (k + rank + 1)
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)
```

## Error Handling

| Scenario | Handling |
|----------|----------|
| BM25 search fails | Fallback to vector-only search, log warning |
| Milvus BM25 unavailable | Check version, raise clear error if < 2.4 |
| Vector search fails | Return BM25 results only |

## Requirements

- Milvus version >= 2.4
- Python `pymilvus` with BM25 support
- No additional storage or services

## Testing

- Unit tests for RRF fusion
- Integration test for hybrid search
- Fallback behavior test when BM25 fails
