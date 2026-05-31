"""Generic Memory Context implementation."""

from typing import Any, Dict, List, Optional

from ...configs import GlobalSettings
from ...embeddings.base import EmbeddingBase
from ...utils import get_logger
from ..base import MemoryBase
from ..storage import _MemoryLifecycle, _MemoryReader, _MemoryWriter
from ..utils import format_memory_result
from .base import MemoryContext

logger = get_logger(__name__)

class GenericMemoryContext(MemoryContext):
    """
    Generic Memory Context.

    Implements the standard functionality of Mnemosyne (Fact/Experience memory),
    wrapping the _Writer, _Reader, and _Lifecycle components.
    """

    def __init__(
        self,
        writer: _MemoryWriter,
        reader: _MemoryReader,
        lifecycle: _MemoryLifecycle,
        config: GlobalSettings,
        reranker=None,
        embedding: Optional[EmbeddingBase] = None
    ):
        self._writer = writer
        self._reader = reader
        self._lifecycle = lifecycle
        self.config = config
        self.reranker = reranker
        self._embedding = embedding
        
    def add(
        self,
        content: Any,
        **kwargs
    ) -> str:
        """
        Add memory (Standard/Fact).
        
        Args:
            content: str - The text content to remember
            **kwargs:
                user_id: str (required)
                metadata: dict (optional)
                infer: bool (optional, default True)
        """
        user_id = kwargs.get("user_id")
        if not user_id:
            raise ValueError("user_id is required for GenericMemoryContext")
            
        return self._writer.add(
            messages=content,
            user_id=user_id,
            metadata=kwargs.get("metadata"),
            infer=kwargs.get("infer", True)
        )

    def add_batch(self, content: List[str], **kwargs) -> List[str]:
        """Batch add."""
        user_id = kwargs.get("user_id")
        if not user_id:
            raise ValueError("user_id is required for GenericMemoryContext")
            
        return self._writer.add_batch(content, user_id)

    def search(
        self,
        query: Any,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Search memories.
        
        Args:
            query: str - Search query
            **kwargs:
                user_id: str (required)
                limit: int (default 10)
        """
        user_id = kwargs.get("user_id")
        if not user_id:
            raise ValueError("user_id is required for GenericMemoryContext")
            
        limit = kwargs.get("limit", 10)
        
        results = self._reader.search(
            query=str(query),
            user_id=user_id,
            limit=limit,
            use_graph=self.config.enable_graph_memory
        )
        
        # Optional reranking
        if self.config.enable_reranking and self.reranker and results:
            results = self.reranker.rerank(str(query), results, top_k=limit)
            
        return [format_memory_result(r) for r in results]

    def get(self, memory_id: str) -> Optional[Dict[str, Any]]:
        result = self._reader.get(memory_id)
        return format_memory_result(result) if result else None
        
    def get_all(
        self, user_id: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        results = self._reader.get_all(user_id, limit=limit, offset=offset)
        return [format_memory_result(r) for r in results]

    def delete(self, memory_id: str) -> bool:
        return self._lifecycle.delete(memory_id)
        
    def update(self, memory_id: str, data: Any, **kwargs) -> Dict[str, Any]:
        embedding = self._embedding or self._writer.embedding
        updated = self._lifecycle.update(memory_id, data, embedding)
        if updated:
            return self.get(memory_id) or {}
        return {}

    def apply_decay(self, user_id: str) -> Dict[str, Any]:
        """Apply confidence decay to all memories for a user."""
        return self._lifecycle.apply_decay(user_id)

    def cleanup_forgotten(self, user_id: str, dry_run: bool = False) -> Dict[str, Any]:
        """Clean up long-forgotten memories for a user."""
        return self._lifecycle.cleanup_forgotten(user_id, dry_run)

    def boost_confidence(self, memory_id: str, boost: float = 0.05) -> bool:
        """Boost confidence when memory is accessed."""
        return self._lifecycle.boost_confidence(memory_id, boost)

    def close(self) -> None:
        """
        Generic context doesn't own the connections (shared),
        but we can define behavior if needed.
        In current design, Memory Facade owns the connections.
        So this might be no-op or specific cleanups.
        """
        pass
