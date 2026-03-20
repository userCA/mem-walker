"""FAISS Index Manager for local vector storage.

This module provides FAISS index management for local vector storage,
supporting multiple user indices with persistent storage.
"""

import os
import pickle
from typing import Dict, List, Optional, Tuple

import faiss
import numpy as np

from ..utils import get_logger

logger = get_logger(__name__)


class FAISSIndexManager:
    """FAISS Index Manager for creating and managing vector indices.

    Supports multiple user indices with persistent storage.
    """

    def __init__(self, index_dir: str = "./data/vectors"):
        """Initialize FAISS Index Manager.

        Args:
            index_dir: Directory for storing index files
        """
        self.index_dir = index_dir
        os.makedirs(index_dir, exist_ok=True)
        self.indices: Dict[str, Dict] = {}  # user_id -> {"index": faiss.Index, "ids": List[str], "type": str}

    def create_index(self, user_id: str, dimension: int, index_type: str = "flat") -> None:
        """Create a new index for a user.

        Args:
            user_id: User identifier
            dimension: Vector dimension
            index_type: Type of index ("flat", "ivf", "hnsw")
        """
        if index_type == "flat":
            # Inner product for cosine similarity (after normalization)
            index = faiss.IndexFlatIP(dimension)
        elif index_type == "ivf":
            quantizer = faiss.IndexFlatIP(dimension)
            index = faiss.IndexIVFFlat(quantizer, dimension, 100)
        elif index_type == "hnsw":
            index = faiss.IndexHNSWFlat(dimension, 32)
        else:
            raise ValueError(f"Unsupported index type: {index_type}")

        self.indices[user_id] = {
            "index": index,
            "ids": [],
            "type": index_type,
            "dimension": dimension
        }
        logger.debug(f"Created {index_type} index for user {user_id} (dim={dimension})")

    def add_vectors(self, user_id: str, vectors: List[List[float]], ids: List[str]) -> None:
        """Add vectors to user's index.

        Args:
            user_id: User identifier
            vectors: List of vectors to add
            ids: List of corresponding IDs
        """
        if user_id not in self.indices:
            if not vectors:
                return
            dim = len(vectors[0])
            self.create_index(user_id, dim)

        index_data = self.indices[user_id]
        index = index_data["index"]

        # Convert to numpy array and normalize for cosine similarity
        vecs = np.array(vectors, dtype=np.float32)
        if vecs.ndim == 1:
            vecs = vecs.reshape(1, -1)

        # L2 normalize for cosine similarity
        faiss.normalize_L2(vecs)

        index.add(vecs)
        index_data["ids"].extend(ids)
        logger.debug(f"Added {len(vectors)} vectors to index for user {user_id}")

    def search(self, user_id: str, query_vector: List[float], k: int = 10) -> List[Tuple[str, float]]:
        """Search for similar vectors.

        Args:
            user_id: User identifier
            query_vector: Query vector
            k: Number of results to return

        Returns:
            List of (id, score) tuples
        """
        if user_id not in self.indices:
            return []

        index_data = self.indices[user_id]
        index = index_data["index"]

        query = np.array([query_vector], dtype=np.float32)
        if query.ndim == 1:
            query = query.reshape(1, -1)

        # L2 normalize for cosine similarity
        faiss.normalize_L2(query)

        distances, indices = index.search(query, min(k, index.ntotal))

        results = []
        for i, idx in enumerate(indices[0]):
            if idx >= 0 and idx < len(index_data["ids"]):
                results.append((index_data["ids"][idx], float(distances[0][i])))

        return results

    def delete_vector(self, user_id: str, vector_id: str) -> bool:
        """Mark a vector as deleted (soft delete - FAISS doesn't support direct deletion).

        Note: FAISS indices don't support efficient deletion. This marks the ID
        as deleted in the tracking. For true deletion, the index needs reconstruction.

        Args:
            user_id: User identifier
            vector_id: ID of vector to delete

        Returns:
            True if found and marked, False otherwise
        """
        if user_id not in self.indices:
            return False

        index_data = self.indices[user_id]
        if vector_id in index_data["ids"]:
            # Mark as deleted by prefixing (will be filtered in search results)
            deleted_idx = index_data["ids"].index(vector_id)
            index_data["ids"][deleted_idx] = f"_DELETED_{vector_id}"
            return True

        return False

    def save_index(self, user_id: str) -> None:
        """Persist index to disk.

        Args:
            user_id: User identifier
        """
        if user_id not in self.indices:
            return

        index_data = self.indices[user_id]
        index_path = os.path.join(self.index_dir, f"{user_id}.index")
        id_path = os.path.join(self.index_dir, f"{user_id}.ids")
        meta_path = os.path.join(self.index_dir, f"{user_id}.meta")

        # Save FAISS index
        faiss.write_index(index_data["index"], index_path)

        # Save IDs
        with open(id_path, 'wb') as f:
            pickle.dump(index_data["ids"], f)

        # Save metadata
        meta = {
            "type": index_data.get("type", "flat"),
            "dimension": index_data.get("dimension", 0)
        }
        with open(meta_path, 'wb') as f:
            pickle.dump(meta, f)

        logger.debug(f"Saved index for user {user_id} to {self.index_dir}")

    def load_index(self, user_id: str) -> bool:
        """Load index from disk.

        Args:
            user_id: User identifier

        Returns:
            True if loaded successfully, False otherwise
        """
        index_path = os.path.join(self.index_dir, f"{user_id}.index")
        id_path = os.path.join(self.index_dir, f"{user_id}.ids")
        meta_path = os.path.join(self.index_dir, f"{user_id}.meta")

        if not (os.path.exists(index_path) and os.path.exists(id_path)):
            return False

        try:
            # Load FAISS index
            index = faiss.read_index(index_path)

            # Load IDs
            with open(id_path, 'rb') as f:
                ids = pickle.load(f)

            # Load metadata
            meta = {}
            if os.path.exists(meta_path):
                with open(meta_path, 'rb') as f:
                    meta = pickle.load(f)

            self.indices[user_id] = {
                "index": index,
                "ids": ids,
                "type": meta.get("type", "flat"),
                "dimension": meta.get("dimension", 0)
            }

            logger.debug(f"Loaded index for user {user_id} from {self.index_dir}")
            return True

        except Exception as e:
            logger.error(f"Failed to load index for user {user_id}: {e}")
            return False

    def load_all_indices(self) -> None:
        """Load all available indices from disk."""
        if not os.path.exists(self.index_dir):
            return

        for filename in os.listdir(self.index_dir):
            if filename.endswith(".index"):
                user_id = filename[:-6]  # Remove .index suffix
                if self.load_index(user_id):
                    logger.info(f"Loaded index for user {user_id}")

    def save_all_indices(self) -> None:
        """Persist all indices to disk."""
        for user_id in self.indices:
            self.save_index(user_id)

    def get_index_size(self, user_id: str) -> int:
        """Get the number of vectors in user's index.

        Args:
            user_id: User identifier

        Returns:
            Number of vectors (including deleted)
        """
        if user_id not in self.indices:
            return 0
        return len(self.indices[user_id]["ids"])

    def list_users(self) -> List[str]:
        """List all user IDs with indices.

        Returns:
            List of user IDs
        """
        return list(self.indices.keys())
