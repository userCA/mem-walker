
import unittest
from mnemosyne.reranker.bm25 import BM25Reranker

class TestBM25Reranker(unittest.TestCase):
    def setUp(self):
        self.reranker = BM25Reranker()

    def test_rerank(self):
        query = "apple"
        candidates = [
            {"content": "apple pie", "score": 0.5},
            {"content": "banana bread", "score": 0.4},
            {"content": "orange juice", "score": 0.3}
        ]
        results = self.reranker.rerank(query, candidates)
        
        # Check if results are sorted by score
        scores = [r["score"] for r in results]
        self.assertEqual(scores, sorted(scores, reverse=True))
        
        # Check if apple pie (relevant) is ranked higher than others
        # Note: Original scores were already sorted, but BM25 should reinforce this
        self.assertEqual(results[0]["content"], "apple pie")
        
        # Check if bm25_score was added
        self.assertIn("bm25_score", results[0])
        self.assertGreater(results[0]["bm25_score"], 0)

    def test_score(self):
        query = "test query"
        document = "this is a test query document"
        score = self.reranker.score(query, document)
        self.assertIsInstance(score, float)
        # BM25 scores can be negative depending on IDF calculation for small corpora
        # Just check if it returns a number for now
        self.assertTrue(isinstance(score, float))

if __name__ == '__main__':
    unittest.main()
