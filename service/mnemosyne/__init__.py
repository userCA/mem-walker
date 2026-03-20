"""
Mnemosyne - Holographic Cognitive Memory System

A modular, extensible memory system for AI applications.

Example:
    >>> from mnemosyne import Memory
    >>> memory = Memory()
    >>> memory_id = memory.add("I love coffee", user_id="user_123")
    >>> results = memory.search("beverage preferences", user_id="user_123")
"""

__version__ = "0.1.0"

# Core API
from .memory import Memory

# Configuration
from .configs import GlobalSettings

# Component bases (for custom implementations)
from .embeddings import EmbeddingBase
from .graphs import GraphStoreBase
from .llms import LLMBase
from .reranker import RerankerBase
from .vector_stores import VectorStoreBase

# Default implementations
from .embeddings import OpenAIEmbedding
from .graphs import Neo4jGraphStore
from .llms import OpenAILLM
from .reranker import BM25Reranker
from .vector_stores import MilvusVectorStore

# Exceptions
from .exceptions import (
    ConfigurationError,
    EmbeddingError,
    GraphStoreError,
    LLMError,
    MemoryError,
    MnemosyneError,
    VectorStoreError,
)

__all__ = [
    # Core
    "Memory",
    "GlobalSettings",
    # Bases
    "EmbeddingBase",
    "VectorStoreBase",
    "GraphStoreBase",
    "LLMBase",
    "RerankerBase",
    # Default implementations
    "OpenAIEmbedding",
    "MilvusVectorStore",
    "Neo4jGraphStore",
    "OpenAILLM",
    "BM25Reranker",
    # Exceptions
    "MnemosyneError",
    "ConfigurationError",
    "EmbeddingError",
    "VectorStoreError",
    "GraphStoreError",
    "LLMError",
    "MemoryError",
]
