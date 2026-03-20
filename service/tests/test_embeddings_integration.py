import unittest
import sys
from pathlib import Path
import os
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mnemosyne.embeddings import (
    FastEmbedEmbedding,
    FastEmbedConfig,
    HuggingFaceEmbedding,
    HuggingFaceEmbeddingConfig
)

class TestEmbeddingsIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        load_dotenv()

    def test_fastembed(self):
        """Test FastEmbed embedding."""
        print("=" * 60)
        print("Testing FastEmbed Embedding")
        print("=" * 60)
        
        config = FastEmbedConfig()
        print(f"Model: {config.model}")
        print(f"Dimension: {config.dimension}")
        print(f"Cache dir: {config.cache_dir}")
        print(f"Env FASTEMBED_CACHE_PATH: {os.getenv('FASTEMBED_CACHE_PATH')}")
        
        embedder = FastEmbedEmbedding(config)
        
        # Test single text
        text = "This is a test sentence."
        embedding = embedder.embed(text)
        print(f"\nSingle text embedding shape: {len(embedding)}")
        print(f"First 5 values: {embedding[:5]}")
        
        self.assertEqual(len(embedding), config.dimension)
        
        # Test batch
        texts = ["First sentence.", "Second sentence.", "Third sentence."]
        embeddings = embedder.embed(texts)
        print(f"\nBatch embeddings shape: {len(embeddings)} x {len(embeddings[0])}")
        
        self.assertEqual(len(embeddings), 3)
        self.assertEqual(len(embeddings[0]), config.dimension)
        
        print("✓ FastEmbed test passed!\n")

    def test_huggingface(self):
        """Test HuggingFace embedding."""
        print("=" * 60)
        print("Testing HuggingFace Embedding (Local Mode)")
        print("=" * 60)
        
        try:
            config = HuggingFaceEmbeddingConfig()
            print(f"Model: {config.model}")
            print(f"Dimension: {config.dimension}")
            
            embedder = HuggingFaceEmbedding(config)
            
            # Test single text
            text = "This is a test sentence."
            embedding = embedder.embed(text)
            print(f"\nSingle text embedding shape: {len(embedding)}")
            print(f"First 5 values: {embedding[:5]}")
            
            self.assertEqual(len(embedding), config.dimension)
            
            # Test batch
            texts = ["First sentence.", "Second sentence.", "Third sentence."]
            embeddings = embedder.embed(texts)
            print(f"\nBatch embeddings shape: {len(embeddings)} x {len(embeddings[0])}")
            
            self.assertEqual(len(embeddings), 3)
            self.assertEqual(len(embeddings[0]), config.dimension)
            
            print("✓ HuggingFace test passed!\n")
        except Exception as e:
            if os.getenv("HF_HUB_OFFLINE") == "1":
                 self.skipTest(f"Skipping due to offline mode issues: {e}")
            else:
                 raise e

if __name__ == "__main__":
    unittest.main()
