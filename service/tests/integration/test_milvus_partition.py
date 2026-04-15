"""Integration test for Milvus user_id partition key."""
import uuid

import pytest
from mnemosyne.vector_stores.milvus import MilvusVectorStore
from mnemosyne.vector_stores.configs import MilvusConfig


class TestMilvusUserIdPartition:
    """Test user_id partition key functionality."""

    @pytest.fixture
    def milvus_config(self):
        """Create test config with unique collection name."""
        config = MilvusConfig()
        config.collection_name = f"test_partition_{uuid.uuid4().hex[:8]}"
        return config

    @pytest.fixture
    def store(self, milvus_config):
        """Create and return vector store."""
        store = MilvusVectorStore(milvus_config)
        yield store
        # Cleanup
        try:
            store.delete_collection()
        except Exception:
            pass

    def test_partition_key_enabled(self, store):
        """Verify user_id is configured as partition key."""
        # Check schema
        schema_fields = {f.name: f for f in store.collection.schema.fields}
        assert "user_id" in schema_fields
        assert schema_fields["user_id"].is_partition_key is True

    def test_user_isolation(self, store):
        """Verify search only returns data for specified user."""
        # Insert vectors for different users
        vectors = [[0.1] * 1536, [0.2] * 1536, [0.3] * 1536]
        payloads = [
            {"user_id": "alice", "content": "Alice's data"},
            {"user_id": "bob", "content": "Bob's data"},
            {"user_id": "alice", "content": "Alice's second data"},
        ]

        store.insert(vectors, payloads)

        # Search for alice - should only get alice's data
        results = store.search(
            query_vector=[0.1] * 1536,
            limit=10,
            filters={"user_id": "alice"}
        )

        assert len(results) == 2
        user_ids = {r["user_id"] for r in results}
        assert user_ids == {"alice"}

    def test_no_user_filter_returns_all(self, store):
        """Verify search without user_id filter returns all data."""
        vectors = [[0.1] * 1536, [0.2] * 1536]
        payloads = [
            {"user_id": "alice", "content": "Alice's data"},
            {"user_id": "bob", "content": "Bob's data"},
        ]

        store.insert(vectors, payloads)

        # Search without user filter
        results = store.search(
            query_vector=[0.1] * 1536,
            limit=10
        )

        assert len(results) == 2