"""Main Memory class - Context Manager Facade.

This is the primary interface users interact with.
It manages different memory contexts (strategies) like Default (Fact), Profile, and File.
"""

import os
from typing import Any, Dict, List, Optional

from ..configs import GlobalSettings
from ..embeddings import CachedEmbedding, OpenAIEmbedding
from ..embeddings.base import EmbeddingBase
from ..exceptions import ConfigurationError
from ..graphs import Neo4jGraphStore
from ..graphs.base import GraphStoreBase
from ..llms import LocalSLM, OpenAILLM
from ..llms.base import LLMBase
from ..reranker import BM25Reranker
from ..reranker.base import RerankerBase
from ..utils import get_logger, setup_logging
from ..vector_stores import MilvusVectorStore, SQLiteVectorStore
from ..vector_stores.base import VectorStoreBase

# Internal components
from .base import MemoryBase
from .contexts.file import FileMemoryContext
from .storage import _MemoryLifecycle, _MemoryReader, _MemoryWriter
from .utils import format_memory_result

# Contexts
from .contexts.base import MemoryContext
from .contexts.generic import GenericMemoryContext
from .contexts.profile import ProfileMemoryContext
from .profiles.manager import UserProfileKBManager

logger = get_logger(__name__)


class Memory(MemoryBase):
    """
    Main Memory class - Context Manager Facade.

    Manages multiple memory contexts:
    - "default": Generic Fact/Experience Memory (Legacy behavior)
    - "profile": User Profile Knowledge Base
    - "file": Local File Memory (SQLite + FAISS)

    Example:
        >>> memory = Memory()
        >>> # Default usage (Generic Context)
        >>> memory.add("I love coffee", user_id="u1")
        >>>
        >>> # Profile usage (Profile Context)
        >>> memory.context("profile").add("User prefers dark mode", user_id="u1", agent_id="a1")
        >>>
        >>> # File usage (Local File Context)
        >>> memory.context("file").add("/path/to/file.txt", user_id="u1")
    """

    def __init__(
        self,
        embedding: Optional[EmbeddingBase] = None,
        vector_store: Optional[VectorStoreBase] = None,
        graph_store: Optional[GraphStoreBase] = None,
        llm: Optional[LLMBase] = None,
        reranker: Optional[RerankerBase] = None,
        config: Optional[GlobalSettings] = None
    ):
        """Initialize Memory system and contexts."""
        # Load config
        if config is None:
            config = GlobalSettings.from_env()
        self.config = config

        # Setup logging
        setup_logging(level=config.log_level, log_file=config.log_file)
        logger.info("Initializing Mnemosyne Memory System (Context Architecture)")

        # Initialize Core Components
        try:
            # Embedding
            base_embedding = embedding or OpenAIEmbedding(config.embedding_config)
            self.embedding = CachedEmbedding(base_embedding, cache_size=1024)

            # Storage backend selection
            self._setup_storage_backend(vector_store)

            # Graph store (still uses Neo4j unless explicitly configured otherwise)
            self.graph_store = graph_store or Neo4jGraphStore(config.graph_store_config)

            # LLMs
            self.llm = llm or OpenAILLM(config.llm_config)
            self.local_slm = self._init_local_slm(config)

            # Reranker
            self.reranker = reranker or BM25Reranker(config.reranker_config)

        except Exception as e:
            raise ConfigurationError(f"Failed to initialize specific components: {e}")

        # Initialize Contexts
        self.contexts: Dict[str, MemoryContext] = {}

        # 1. Default (Generic) Context
        self._init_default_context()

        # 2. Profile Context
        self._init_profile_context()

        # 3. File Context (Local storage)
        self._init_file_context()

        logger.info("Memory system initialized successfully with contexts: %s", list(self.contexts.keys()))

    def _setup_storage_backend(self, vector_store: Optional[VectorStoreBase] = None):
        """Setup storage backend based on configuration.

        Supports:
        - milvus: External Milvus service (default)
        - local: Local SQLite + FAISS (zero dependency)
        - auto: Automatically select based on environment
        """
        if vector_store is not None:
            # User provided custom vector store
            self.vector_store = vector_store
            self._using_local_storage = isinstance(vector_store, SQLiteVectorStore)
            logger.info("Using user-provided vector store")
            return

        backend = self.config.storage_backend_config.backend
        local_config = self.config.local_storage_config

        if backend == "local" or (backend == "auto" and local_config.enabled):
            # Use local SQLite storage
            try:
                self.vector_store = SQLiteVectorStore(
                    db_path=local_config.db_path,
                    vector_size=local_config.vector_size,
                    use_faiss=local_config.use_faiss,
                    index_dir=local_config.vector_index_dir
                )
                self._using_local_storage = True
                logger.info(f"Using local SQLite storage: {local_config.db_path}")
            except Exception as e:
                logger.warning(f"Failed to initialize local storage, falling back to Milvus: {e}")
                self.vector_store = MilvusVectorStore(self.config.vector_store_config)
                self._using_local_storage = False
        else:
            # Use Milvus
            self.vector_store = MilvusVectorStore(self.config.vector_store_config)
            self._using_local_storage = False
            logger.info("Using Milvus vector store")

    def _is_local_mode(self) -> bool:
        """Check if running in local mode."""
        return self._using_local_storage

    def _init_local_slm(self, config: GlobalSettings) -> LLMBase:
        """Initialize Local SLM if enabled."""
        if config.enable_local_slm:
            try:
                slm = LocalSLM(config.local_slm_config)
                logger.info("LocalSLM initialized")
                return slm
            except Exception as e:
                logger.warning(f"Failed to initialize LocalSLM: {e}")
        return self.llm

    def _init_default_context(self):
        """Initialize the Default Generic Context (Legacy logic)."""
        writer = _MemoryWriter(self.embedding, self.vector_store, self.graph_store, self.llm)
        reader = _MemoryReader(self.embedding, self.vector_store, self.graph_store, self.local_slm)
        lifecycle = _MemoryLifecycle(self.vector_store, self.graph_store)

        self.default_context = GenericMemoryContext(
            writer=writer,
            reader=reader,
            lifecycle=lifecycle,
            config=self.config,
            reranker=self.reranker
        )
        self.contexts["default"] = self.default_context

    def _init_profile_context(self):
        """Initialize the Profile Knowledge Base Context."""
        try:
            # Profile KB has its own manager but reuses our embedding and config
            # Note: UserProfileKBManager internals might create its own VectorStore connection (to same Milvus)
            profile_manager = UserProfileKBManager(
                embedding=self.embedding, # Use same cached embedding
                config=self.config
            )

            self.contexts["profile"] = ProfileMemoryContext(profile_manager)
            logger.info("Profile Context initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Profile Context: {e}")
            # Non-critical failure, system can still run default context

    def _init_file_context(self):
        """Initialize the File Memory Context (Local storage)."""
        # Only initialize if using local storage
        if not self._using_local_storage:
            logger.debug("File Context skipped (not using local storage)")
            return

        try:
            from ..vector_stores.sqlite import SQLiteVectorStore

            # File context requires SQLiteVectorStore
            if not isinstance(self.vector_store, SQLiteVectorStore):
                logger.warning("File Context requires SQLiteVectorStore, skipping")
                return

            file_context = FileMemoryContext(
                storage=self.vector_store,
                embedding=self.embedding,
                llm=self.local_slm
            )
            self.contexts["file"] = file_context
            logger.info("File Context initialized (local storage)")
        except Exception as e:
            logger.warning(f"Failed to initialize File Context: {e}")

    def context(self, name: str = "default") -> MemoryContext:
        """
        Get a specific memory context.

        Args:
            name: Context name ("default", "profile", "file", etc.)

        Returns:
            MemoryContext implementation
        """
        if name not in self.contexts:
            raise ValueError(f"Context '{name}' not found. Available: {list(self.contexts.keys())}")
        return self.contexts[name]

    # --- Proxy Methods for Default Context (Backward Compatibility) ---

    def add(self, messages: str, user_id: str, metadata: Optional[Dict[str, Any]] = None, infer: bool = True) -> str:
        """Add to default context."""
        return self.default_context.add(messages, user_id=user_id, metadata=metadata, infer=infer)

    def add_batch(self, messages: List[str], user_id: str) -> List[str]:
        """Batch add to default context."""
        return self.default_context.add_batch(messages, user_id=user_id)

    def search(self, query: str, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search default context."""
        return self.default_context.search(query, user_id=user_id, limit=limit)

    def get(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """Get from default context."""
        return self.default_context.get(memory_id)

    def get_all(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all from default context."""
        return self.default_context.get_all(user_id)

    def delete(self, memory_id: str) -> bool:
        """Delete from default context."""
        return self.default_context.delete(memory_id)

    def update(self, memory_id: str, data: str) -> Dict[str, Any]:
        """Update default context."""
        # GenericContext update signature: update(memory_id, data)
        return self.default_context.update(memory_id, data)

    def close(self) -> None:
        """Close all contexts."""
        logger.info("Closing Memory system connections")

        for name, ctx in self.contexts.items():
            try:
                ctx.close()
            except Exception as e:
                logger.warning(f"Error closing context {name}: {e}")

        # Close shared stores if they have close methods and weren't closed by contexts
        if hasattr(self.graph_store, 'close'):
            self.graph_store.close()

        if hasattr(self.vector_store, 'close'):
            self.vector_store.close()

        logger.info("Memory system closed")
