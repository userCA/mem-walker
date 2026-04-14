import pytest
import inspect
from mnemosyne.vector_stores.base import VectorStoreBase

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
