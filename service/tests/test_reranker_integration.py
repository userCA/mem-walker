"""Test reranker implementations."""

import os
import sys
import unittest
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mnemosyne.reranker import BM25Reranker, CrossEncoderReranker, RerankerConfig

class TestRerankerIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        load_dotenv()
        
    def test_bm25(self):
        print("\n" + "="*60)
        print("Testing BM25 Reranker")
        print("="*60)
        
        reranker = BM25Reranker()
        
        query = "apple"
        candidates = [
            {"content": "apple pie recipe", "id": 1},
            {"content": "banana bread", "id": 2},
            {"content": "apple computer", "id": 3},
            {"content": "orange juice", "id": 4}
        ]
        
        results = reranker.rerank(query, candidates)
        
        for r in results:
            print(f"Content: {r['content']:<20} Score: {r['score']:.4f}")
        
        self.assertTrue(len(results) > 0)
        self.assertTrue("bm25_score" in results[0])

    def test_cross_encoder(self):
        print("\n" + "="*60)
        print("Testing Cross-Encoder Reranker")
        print("="*60)
        
        model_name = os.getenv("RERANKER_MODEL", "BAAI/bge-reranker-base")
        print(f"Model: {model_name}")
        
        try:
            config = RerankerConfig(model_name=model_name)
            reranker = CrossEncoderReranker(config)
            
            query = "organic food"
            candidates = [
                {"content": "natural and healthy vegetables from the farm", "id": 1},
                {"content": "processed fast food with chemicals", "id": 2},
                {"content": "iphone 15 pro max review", "id": 3},
                {"content": "how to grow organic tomatoes", "id": 4}
            ]
            
            results = reranker.rerank(query, candidates)
            
            for r in results:
                print(f"Content: {r['content']:<45} Score: {r['score']:.4f}")
            
            self.assertTrue(len(results) > 0)
            self.assertTrue("cross_encoder_score" in results[0])
                
        except Exception as e:
            print(f"Skipping CrossEncoder test (model might be missing in offline mode): {e}")
            # If we're offline and don't have the model, this test might fail or skip
            # For integration tests, skipping is better than failing if environment isn't perfect
            if os.getenv("HF_HUB_OFFLINE") == "1":
                 self.skipTest(f"Skipping due to offline mode and missing model: {e}")
            else:
                 raise e

if __name__ == "__main__":
    unittest.main()
