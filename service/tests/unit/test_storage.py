import pytest
from mnemosyne.memory.storage import _reciprocal_rank_fusion, _MemoryWriter

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


def test_memory_reader_search_with_bm25():
    """_MemoryReader.search should call vector_search and bm25_search in parallel"""
    from mnemosyne.memory.storage import _MemoryReader
    from unittest.mock import MagicMock

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


def test_memory_writer_computes_bm25_on_add():
    """_MemoryWriter.add should compute and store BM25 vectors."""
    from unittest.mock import MagicMock, patch

    mock_embedding = MagicMock()
    mock_embedding.embed.return_value = [0.1] * 384

    mock_vector_store = MagicMock()
    mock_vector_store.insert.return_value = ["memory-1"]
    mock_vector_store.list.return_value = []  # Prevent hash deduplication from skipping insert
    mock_vector_store.search.return_value = []  # Prevent semantic deduplication from causing issues

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

    with patch('mnemosyne.memory.storage.BM25Calculator') as MockCalc:
        mock_bm25 = MagicMock()
        mock_bm25.compute_query_vector.return_value = [(0, 1.5), (100, 0.8)]
        MockCalc.return_value = mock_bm25

        from mnemosyne.memory.storage import _MemoryReader
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