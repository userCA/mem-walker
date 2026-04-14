import pytest
import inspect
from unittest.mock import MagicMock, patch
from mnemosyne.vector_stores.base import VectorStoreBase
from mnemosyne.vector_stores.milvus import MilvusVectorStore

def test_bm25_search_method_exists_and_signature():
    """VectorStoreBase should have bm25_search method with correct signature"""
    # Check method exists
    assert hasattr(VectorStoreBase, 'bm25_search'), "bm25_search method should exist"

    # Check it's a method (not abstract)
    method = getattr(VectorStoreBase, 'bm25_search')
    assert callable(method), "bm25_search should be callable"

    # Check signature
    sig = inspect.signature(method)
    params = list(sig.parameters.keys())
    assert 'query' in params, "Should have 'query' parameter"
    assert 'limit' in params, "Should have 'limit' parameter"
    assert 'filters' in params, "Should have 'filters' parameter"

def test_bm25_search_raises_not_implemented():
    """A minimal concrete subclass should get NotImplementedError when calling bm25_search"""

    # Create minimal concrete implementation of abstract base
    class ConcreteStore(VectorStoreBase):
        def create_collection(self, name, vector_size, distance_metric="cosine"):
            pass
        def insert(self, vectors, payloads=None, ids=None):
            return []
        def search(self, query_vector, limit=10, filters=None):
            return []
        def delete(self, vector_id):
            return False
        def update(self, vector_id, vector=None, payload=None):
            return False
        def get(self, vector_id):
            return None
        def list(self, filters=None, limit=None):
            return []
        def delete_collection(self):
            pass
        def collection_info(self):
            return {}

    store = ConcreteStore()
    with pytest.raises(NotImplementedError):
        store.bm25_search(query="test")

def test_insert_accepts_bm25_vectors():
    """VectorStoreBase.insert should accept bm25_vectors parameter."""
    sig = inspect.signature(VectorStoreBase.insert)
    params = list(sig.parameters.keys())
    assert 'bm25_vectors' in params, "insert should accept bm25_vectors parameter"

def test_milvus_bm25_search():
    """MilvusVectorStore should implement bm25_search"""
    mock_collection = MagicMock()
    mock_collection.num_entities = 0
    with patch('pymilvus.connections.connect'):
        with patch('pymilvus.utility.has_collection', return_value=False):
            with patch.object(MilvusVectorStore, '_init_collection'):
                store = MilvusVectorStore()
                # Manually set the collection mock after initialization
                store.collection = mock_collection
                # Should have bm25_search method
                assert hasattr(store, 'bm25_search')
                assert callable(store.bm25_search)
                # Calling bm25_search should NOT raise NotImplementedError
                # (it should be implemented in MilvusVectorStore)
                result = store.bm25_search(query="test query", limit=5)
                assert isinstance(result, list)

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
