import pytest
from mnemosyne.vector_stores.base import VectorStoreBase

def test_bm25_search_abstract():
    """VectorStoreBase should have bm25_search abstract method"""
    with pytest.raises(TypeError):
        # Cannot instantiate abstract class
        store = VectorStoreBase()