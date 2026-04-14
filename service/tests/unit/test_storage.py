import pytest
from mnemosyne.memory.storage import _reciprocal_rank_fusion

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