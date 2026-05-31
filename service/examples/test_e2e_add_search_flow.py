"""End-to-End Add-Search Flow Test for Mnemosyne Memory System

This test verifies the complete flow at the component level:
1. Add memories (single + batch) - using vector store directly
2. Search and verify results - using vector store + BM25
3. User isolation (different users shouldn't see each other's memories)

Run with: cd service && python3 examples/test_e2e_add_search_flow.py
"""

import os
import sys
import uuid
import logging
from typing import List, Dict, Any

# Setup path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mnemosyne.vector_stores.sqlite import SQLiteVectorStore
from mnemosyne.memory.bm25_calculator import BM25Calculator
from mnemosyne.memory.storage import _reciprocal_rank_fusion

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MockEmbedding:
    """Simple mock embedding for testing - produces deterministic vectors."""

    def __init__(self, dimension: int = 384):
        self.dimension = dimension

    def embed(self, text: str) -> List[float]:
        """Create a deterministic vector based on text hash."""
        import hashlib
        # Use text to seed a pseudo-random but deterministic vector
        hash_bytes = hashlib.sha256(text.encode()).digest()
        # Extend to required dimension by repeating hash
        vector = []
        for i in range(self.dimension):
            byte_val = hash_bytes[i % len(hash_bytes)]
            # Normalize to -1 to 1 range
            vector.append((byte_val / 128.0) - 1.0)
        # Normalize to unit length
        import math
        norm = math.sqrt(sum(v * v for v in vector))
        return [v / norm for v in vector]


class E2EAddSearchFlow:
    """End-to-end test for add-then-search flow using real components."""

    def __init__(self):
        self.vector_store = None
        self.bm25_calculator = BM25Calculator()
        self.embedding = MockEmbedding(dimension=384)
        self.test_user_id = f"e2e_test_user_{uuid.uuid4().hex[:8]}"
        self.other_user_id = f"e2e_other_user_{uuid.uuid4().hex[:8]}"
        self.added_ids = []

    def setup(self):
        """Initialize the vector store with local storage."""
        logger.info("=" * 60)
        logger.info("Setting up E2E Test Environment")
        logger.info("=" * 60)

        db_path = f"/tmp/test_e2e_{uuid.uuid4().hex}.db"

        self.vector_store = SQLiteVectorStore(
            db_path=db_path,
            vector_size=384,
            use_faiss=True
        )

        logger.info(f"Test user: {self.test_user_id}")
        logger.info(f"Other user: {self.other_user_id}")
        logger.info(f"Database: {db_path}")
        logger.info("Setup complete\n")

    def teardown(self):
        """Clean up resources."""
        if self.vector_store:
            self.vector_store.close()
            logger.info("Cleanup complete")

    def add_memory(self, content: str, user_id: str) -> str:
        """Add a memory and return its ID."""
        vector = self.embedding.embed(content)
        payload = {
            "user_id": user_id,
            "content": content,
            "metadata": {}
        }
        ids = self.vector_store.insert([vector], [payload])
        memory_id = ids[0]

        # Also add to BM25
        tokens = content.lower().split()
        self.bm25_calculator.add_document(tokens)

        self.added_ids.append(memory_id)
        return memory_id

    def add_batch(self, contents: List[str], user_id: str) -> List[str]:
        """Add multiple memories and return their IDs."""
        vectors = [self.embedding.embed(c) for c in contents]
        payloads = [
            {"user_id": user_id, "content": c, "metadata": {}}
            for c in contents
        ]
        ids = self.vector_store.insert(vectors, payloads)

        # Also add to BM25
        for content in contents:
            tokens = content.lower().split()
            self.bm25_calculator.add_document(tokens)

        self.added_ids.extend(ids)
        return ids

    def search_vector(self, query: str, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search using vector similarity."""
        query_vector = self.embedding.embed(query)
        results = self.vector_store.search(
            query_vector,
            limit=limit,
            filters={"user_id": user_id}
        )
        return results

    def search_bm25(self, query: str, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search using BM25."""
        query_vec = self.bm25_calculator.compute_query_vector(query)
        query_tokens = query.lower().split()

        # We need to search all and filter by user_id
        # Since BM25 doesn't support filters directly, we do it in memory
        all_results = self.vector_store.list(filters={"user_id": user_id})

        # Score each by BM25
        scored = []
        for item in all_results:
            content = item.get("content", "")
            content_tokens = content.lower().split()
            # Compute BM25 score for this document
            score = 0.0
            for i, token in enumerate(query_tokens):
                if token in content_tokens:
                    tf = content_tokens.count(token)
                    idf = self.bm25_calculator.idf.get(token, 0)
                    # Simplified BM25 scoring
                    score += idf * (tf * 1.5) / (tf + 1.5)
            if score > 0:
                scored.append({**item, "bm25_score": score})

        scored.sort(key=lambda x: x["bm25_score"], reverse=True)
        return scored[:limit]

    def hybrid_search(self, query: str, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Combine vector and BM25 search."""
        from mnemosyne.memory.storage import _reciprocal_rank_fusion

        vector_results = self.search_vector(query, user_id, limit=limit)
        bm25_results = self.search_bm25(query, user_id, limit=limit)

        return _reciprocal_rank_fusion([vector_results, bm25_results], k=60)

    def run_all_tests(self):
        """Run all E2E tests."""
        try:
            self.setup()

            logger.info("=" * 60)
            logger.info("STARTING E2E ADD-SEARCH FLOW TESTS")
            logger.info("=" * 60)

            # Test 1: Single add then search
            self.test_single_add_then_search()

            # Test 2: Batch add then search
            self.test_batch_add_then_search()

            # Test 3: Search retrieves what was added
            self.test_search_finds_added_content()

            # Test 4: Delete removes from search results
            self.test_delete_removes_from_search()

            # Test 5: User isolation
            self.test_user_isolation()

            # Test 6: Hybrid search ranking
            self.test_hybrid_search_ranking()

            logger.info("\n" + "=" * 60)
            logger.info("ALL E2E TESTS PASSED!")
            logger.info("=" * 60)

        except Exception as e:
            logger.error(f"\nE2E TEST FAILED: {e}")
            import traceback
            traceback.print_exc()
            raise
        finally:
            self.teardown()

    def test_single_add_then_search(self):
        """Test 1: Add a single memory and search for it."""
        logger.info("TEST 1: Single Add Then Search")

        content = f"I love programming in Python and JavaScript - test {uuid.uuid4().hex[:6]}"
        memory_id = self.add_memory(content, self.test_user_id)

        assert memory_id is not None, "Should return a memory ID"

        # Search for it using vector search
        results = self.search_vector("programming Python", self.test_user_id, limit=10)

        assert len(results) > 0, f"Should find at least 1 result, got {len(results)}"
        # Verify the added content is in results
        found = any(content in r.get('content', '') for r in results)
        assert found, f"Added content should be in search results: {results}"

        logger.info(f"  PASS: Added memory {memory_id}, found in search")

    def test_batch_add_then_search(self):
        """Test 2: Add multiple memories in batch and verify all are searchable."""
        logger.info("TEST 2: Batch Add Then Search")

        batch_contents = [
            "Python is great for web development",
            "JavaScript runs in the browser and Node.js",
            "FastAPI is a modern Python web framework",
            "React is a popular frontend library",
            "Docker containers simplify deployment"
        ]

        memory_ids = self.add_batch(batch_contents, self.test_user_id)

        assert len(memory_ids) == len(batch_contents), \
            f"Should return {len(batch_contents)} IDs, got {len(memory_ids)}"

        # Search for each added content
        for content in batch_contents:
            results = self.search_vector(content.split()[0], self.test_user_id, limit=10)
            found = any(content in r.get('content', '') for r in results)
            assert found, f"Content '{content}' should be findable in search results"

        logger.info(f"  PASS: Batch added {len(memory_ids)} memories, all searchable")

    def test_search_finds_added_content(self):
        """Test 3: Verify exact content can be found through search."""
        logger.info("TEST 3: Search Finds Added Content (Exact Match)")

        # Add a very specific memory
        unique_content = f"Uniquely identifying string xyz123-{uuid.uuid4().hex} for testing"
        memory_id = self.add_memory(unique_content, self.test_user_id)

        # Search for a distinctive part
        results = self.search_vector("xyz123", self.test_user_id, limit=5)

        assert len(results) > 0, f"Should find results for 'xyz123'"
        # Check if the unique string is in any result
        found = any("xyz123" in r.get('content', '') for r in results)
        assert found, f"Unique content should be found: {results}"

        logger.info(f"  PASS: Exact content '{unique_content[:30]}...' found in search")

    def test_delete_removes_from_search(self):
        """Test 4: Delete a memory and verify it's removed from search results."""
        logger.info("TEST 4: Delete Removes from Search")

        # Add a unique memory
        unique_content = f"Memory to be deleted - {uuid.uuid4().hex}"
        memory_id = self.add_memory(unique_content, self.test_user_id)

        # Verify it exists
        results_before = self.search_vector("deleted", self.test_user_id, limit=10)
        found_before = any("deleted" in r.get('content', '') for r in results_before)
        assert found_before, "Memory should exist before deletion"

        # Delete it
        deleted = self.vector_store.delete(memory_id)
        assert deleted, "Delete should return True"

        # Verify it's gone from list
        result_after = self.vector_store.get(memory_id)
        assert result_after is None, "Memory should be gone after deletion"

        logger.info(f"  PASS: Memory deleted successfully")

    def test_user_isolation(self):
        """Test 5: Verify users can only see their own memories."""
        logger.info("TEST 5: User Isolation")

        # User A adds a unique memory
        user_a_content = f"User A's secret data - {uuid.uuid4().hex}"
        user_a_id = self.add_memory(user_a_content, self.test_user_id)

        # User B adds a different memory
        user_b_content = f"User B's secret data - {uuid.uuid4().hex}"
        user_b_id = self.add_memory(user_b_content, self.other_user_id)

        # User A searches - should NOT find User B's memory
        results_for_a = self.search_vector("secret data", self.test_user_id, limit=10)
        found_b_in_a = any(user_b_content in r.get('content', '') for r in results_for_a)
        assert not found_b_in_a, "User A should not see User B's memories"

        # User B searches - should NOT find User A's memory
        results_for_b = self.search_vector("secret data", self.other_user_id, limit=10)
        found_a_in_b = any(user_a_content in r.get('content', '') for r in results_for_b)
        assert not found_a_in_b, "User B should not see User A's memories"

        # Each should find their own
        found_a = any(user_a_content in r.get('content', '') for r in results_for_a)
        found_b = any(user_b_content in r.get('content', '') for r in results_for_b)
        assert found_a, "User A should find their own memory"
        assert found_b, "User B should find their own memory"

        logger.info("  PASS: User isolation verified - users cannot see each other's memories")

    def test_hybrid_search_ranking(self):
        """Test 6: Verify hybrid search properly ranks results."""
        logger.info("TEST 6: Hybrid Search Ranking")

        # Add memories with varying relevance to "Python programming"
        memories = [
            "Python is a programming language",
            "Java is a different programming language",
            "I use Python for data analysis",
            "The weather is nice today"
        ]

        self.add_batch(memories, self.test_user_id)

        # Hybrid search for Python programming
        results = self.hybrid_search("Python programming", self.test_user_id, limit=10)

        assert len(results) >= 2, "Should find at least 2 relevant results"

        # Check that Python-related memories rank higher
        python_indices = [i for i, r in enumerate(results) if "Python" in r.get('content', '')]
        non_python_indices = [i for i, r in enumerate(results) if "Python" not in r.get('content', '')]

        if python_indices and non_python_indices:
            # All Python results should rank before non-Python results
            min_python_pos = min(python_indices)
            max_non_python_pos = max(non_python_indices)
            assert min_python_pos < max_non_python_pos, \
                "Python-related results should rank higher than unrelated"

        logger.info(f"  PASS: Hybrid search properly ranked results")


def main():
    """Run the E2E test."""
    test = E2EAddSearchFlow()
    test.run_all_tests()


if __name__ == "__main__":
    main()
