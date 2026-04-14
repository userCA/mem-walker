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


def test_rff_empty_results():
    """Should return empty list when no results"""
    fused = _reciprocal_rank_fusion([], k=60)
    assert fused == []


def test_rff_single_list():
    """Should work with single result list"""
    results = [
        [{"id": "1", "score": 0.9}, {"id": "2", "score": 0.8}]
    ]
    fused = _reciprocal_rank_fusion(results, k=60)
    assert len(fused) == 2
    assert fused[0]["id"] == "1"  # highest rank first


def test_rff_item_without_id():
    """Should skip items without id field"""
    results = [[{"content": "test", "score": 0.9}]]  # no "id"
    fused = _reciprocal_rank_fusion(results, k=60)
    assert fused == []


def test_rff_item_in_all_lists_ranks_highest():
    """Item appearing in all lists should rank highest"""
    list1 = [{"id": "1", "score": 0.9}, {"id": "2", "score": 0.8}]
    list2 = [{"id": "2", "score": 0.9}, {"id": "3", "score": 0.8}]
    list3 = [{"id": "2", "score": 0.9}, {"id": "4", "score": 0.8}]
    fused = _reciprocal_rank_fusion([list1, list2, list3], k=60)
    fused_ids = [item["id"] for item in fused]
    assert fused_ids[0] == "2"  # appears in all 3 lists


def test_rff_empty_list_in_results():
    """Should handle empty list in results"""
    fused = _reciprocal_rank_fusion([[{"id": "1"}], []], k=60)
    assert len(fused) == 1
    assert fused[0]["id"] == "1"