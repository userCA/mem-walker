"""Unit tests for SQLiteVectorStore and FAISSIndexManager."""

import os
import shutil
import tempfile
import unittest

import numpy as np

from mnemosyne.vector_stores.faiss_manager import FAISSIndexManager
from mnemosyne.vector_stores.sqlite import SQLiteVectorStore


class TestFAISSIndexManager(unittest.TestCase):
    """Tests for FAISSIndexManager."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.manager = FAISSIndexManager(index_dir=self.test_dir)
        self.user_id = "test_user"
        self.dimension = 4

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_create_index(self):
        """Test index creation."""
        self.manager.create_index(self.user_id, self.dimension)
        self.assertIn(self.user_id, self.manager.indices)
        self.assertEqual(self.manager.get_index_size(self.user_id), 0)

    def test_add_vectors(self):
        """Test adding vectors to index."""
        self.manager.create_index(self.user_id, self.dimension)

        vectors = [[0.1, 0.2, 0.3, 0.4], [0.5, 0.6, 0.7, 0.8]]
        ids = ["id1", "id2"]

        self.manager.add_vectors(self.user_id, vectors, ids)

        self.assertEqual(self.manager.get_index_size(self.user_id), 2)

    def test_search(self):
        """Test searching vectors."""
        self.manager.create_index(self.user_id, self.dimension)

        vectors = [
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
        ]
        ids = ["id1", "id2", "id3"]

        self.manager.add_vectors(self.user_id, vectors, ids)

        # Search for a vector similar to [1.0, 0.0, 0.0, 0.0]
        query = [0.9, 0.1, 0.0, 0.0]
        results = self.manager.search(self.user_id, query, k=2)

        self.assertGreater(len(results), 0)
        # First result should be id1 (most similar)
        self.assertEqual(results[0][0], "id1")

    def test_save_and_load(self):
        """Test index persistence."""
        self.manager.create_index(self.user_id, self.dimension)

        vectors = [[0.1, 0.2, 0.3, 0.4]]
        ids = ["id1"]

        self.manager.add_vectors(self.user_id, vectors, ids)
        self.manager.save_index(self.user_id)

        # Create new manager and load
        new_manager = FAISSIndexManager(index_dir=self.test_dir)
        loaded = new_manager.load_index(self.user_id)

        self.assertTrue(loaded)
        self.assertEqual(new_manager.get_index_size(self.user_id), 1)


class TestSQLiteVectorStore(unittest.TestCase):
    """Tests for SQLiteVectorStore."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, "test_memories.db")
        self.index_dir = os.path.join(self.test_dir, "vectors")
        self.vector_size = 4

        self.store = SQLiteVectorStore(
            db_path=self.db_path,
            vector_size=self.vector_size,
            use_faiss=True,
            index_dir=self.index_dir
        )

    def tearDown(self):
        """Clean up test fixtures."""
        self.store.close()
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_insert_and_get(self):
        """Test inserting and retrieving vectors."""
        vectors = [[0.1, 0.2, 0.3, 0.4]]
        payloads = [{"user_id": "user1", "content": "test content"}]

        ids = self.store.insert(vectors, payloads)

        self.assertEqual(len(ids), 1)
        self.assertEqual(len(ids), 1)

        # Retrieve
        result = self.store.get(ids[0])
        self.assertIsNotNone(result)
        self.assertEqual(result["content"], "test content")
        self.assertEqual(result["user_id"], "user1")

    def test_search(self):
        """Test vector search."""
        # Insert test vectors
        vectors = [
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ]
        payloads = [
            {"user_id": "user1", "content": "vector1"},
            {"user_id": "user1", "content": "vector2"},
            {"user_id": "user1", "content": "vector3"},
            {"user_id": "user1", "content": "vector4"},
        ]

        self.store.insert(vectors, payloads)

        # Search
        query = [0.9, 0.1, 0.0, 0.0]
        results = self.store.search(query, limit=2, filters={"user_id": "user1"})

        self.assertGreater(len(results), 0)
        self.assertLessEqual(len(results), 2)
        # First result should be most similar
        self.assertEqual(results[0]["content"], "vector1")

    def test_delete(self):
        """Test deleting vectors."""
        vectors = [[0.1, 0.2, 0.3, 0.4]]
        payloads = [{"user_id": "user1", "content": "test"}]

        ids = self.store.insert(vectors, payloads)

        # Delete
        deleted = self.store.delete(ids[0])
        self.assertTrue(deleted)

        # Verify deleted
        result = self.store.get(ids[0])
        self.assertIsNone(result)

    def test_update(self):
        """Test updating vectors."""
        vectors = [[0.1, 0.2, 0.3, 0.4]]
        payloads = [{"user_id": "user1", "content": "original"}]

        ids = self.store.insert(vectors, payloads)

        # Update
        updated = self.store.update(ids[0], payload={"content": "updated"})
        self.assertTrue(updated)

        # Verify
        result = self.store.get(ids[0])
        self.assertEqual(result["content"], "updated")

    def test_list(self):
        """Test listing vectors."""
        vectors = [[0.1, 0.2, 0.3, 0.4], [0.5, 0.6, 0.7, 0.8]]
        payloads = [
            {"user_id": "user1", "content": "content1"},
            {"user_id": "user1", "content": "content2"},
        ]

        self.store.insert(vectors, payloads)

        # List
        results = self.store.list(filters={"user_id": "user1"})
        self.assertEqual(len(results), 2)

    def test_collection_info(self):
        """Test collection info."""
        vectors = [[0.1, 0.2, 0.3, 0.4]]
        payloads = [{"user_id": "user1", "content": "test"}]

        self.store.insert(vectors, payloads)

        info = self.store.collection_info()
        self.assertEqual(info["num_entities"], 1)
        self.assertEqual(info["vector_size"], self.vector_size)
        self.assertTrue(info["use_faiss"])

    def test_delete_collection(self):
        """Test deleting entire collection."""
        vectors = [[0.1, 0.2, 0.3, 0.4]]
        payloads = [{"user_id": "user1", "content": "test"}]

        self.store.insert(vectors, payloads)

        self.store.delete_collection()

        info = self.store.collection_info()
        self.assertEqual(info["num_entities"], 0)


class TestSQLiteVectorStoreWithoutFAISS(unittest.TestCase):
    """Tests for SQLiteVectorStore without FAISS."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, "test_memories.db")
        self.vector_size = 4

        self.store = SQLiteVectorStore(
            db_path=self.db_path,
            vector_size=self.vector_size,
            use_faiss=False
        )

    def tearDown(self):
        """Clean up test fixtures."""
        self.store.close()
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_insert_without_faiss(self):
        """Test inserting vectors without FAISS."""
        vectors = [[0.1, 0.2, 0.3, 0.4]]
        payloads = [{"user_id": "user1", "content": "test"}]

        ids = self.store.insert(vectors, payloads)
        self.assertEqual(len(ids), 1)

    def test_search_fallback(self):
        """Test search fallback when FAISS is disabled."""
        vectors = [[0.1, 0.2, 0.3, 0.4]]
        payloads = [{"user_id": "user1", "content": "test"}]

        self.store.insert(vectors, payloads)

        # Should use SQLite fallback
        results = self.store.search([0.1, 0.2, 0.3, 0.4], limit=10, filters={"user_id": "user1"})

        self.assertGreater(len(results), 0)


if __name__ == '__main__':
    unittest.main()
