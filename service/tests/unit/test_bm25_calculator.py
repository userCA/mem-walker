import pytest
from mnemosyne.memory.bm25_calculator import BM25Calculator

def test_bm25_calculator_idf_computation():
    """BM25Calculator should compute IDF correctly."""
    calc = BM25Calculator()
    # Add 3 documents
    calc.add_document(["hello", "world"])
    calc.add_document(["hello", "python"])
    calc.add_document(["hello", "world", "python"])

    # "hello" appears in all 3 docs, IDF should be low
    # "world" appears in 2 docs
    # "python" appears in 2 docs
    assert "hello" in calc.idf
    assert "world" in calc.idf
    assert "python" in calc.idf
    # hello IDF < world IDF (more common = lower IDF)
    assert calc.idf["hello"] < calc.idf["world"]

def test_bm25_calculator_add_document_returns_vector():
    """add_document should return BM25 sparse vector."""
    calc = BM25Calculator()
    vector = calc.add_document(["hello", "hello", "world"])

    assert isinstance(vector, list)
    assert len(vector) > 0
    # Each element is (index, score) tuple
    for item in vector:
        assert isinstance(item, tuple)
        assert len(item) == 2

def test_bm25_calculator_compute_query_vector():
    """compute_query_vector should use stored IDF."""
    calc = BM25Calculator()
    calc.add_document(["hello", "world"])
    calc.add_document(["hello", "python"])

    query_vector = calc.compute_query_vector("hello world")

    assert isinstance(query_vector, list)
    assert len(query_vector) > 0

def test_bm25_calculator_persistence():
    """BM25Calculator should save and load IDF statistics."""
    import tempfile
    import os

    calc = BM25Calculator()
    calc.add_document(["hello", "world"])
    calc.add_document(["hello", "python"])

    # Save to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as f:
        temp_path = f.name

    try:
        calc.save(temp_path)

        # Load into new calculator
        calc2 = BM25Calculator()
        calc2.load(temp_path)

        assert calc2.corpus_size == calc.corpus_size
        assert calc2.doc_freqs == calc.doc_freqs
        assert calc2.idf == calc.idf
    finally:
        os.unlink(temp_path)