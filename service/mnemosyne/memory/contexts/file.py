"""File Memory Context - Local file-based memory storage.

This context provides local file persistence capability for the Mnemosyne memory system.
It supports storing and retrieving file contents with vector embeddings.
"""

import hashlib
import json
import os
from typing import Any, Dict, List, Optional

from ...embeddings.base import EmbeddingBase
from ...llms.base import LLMBase
from ...vector_stores.base import VectorStoreBase
from ...vector_stores.sqlite import SQLiteVectorStore
from ..utils import format_memory_result
from .base import MemoryContext

from ...utils import get_logger

logger = get_logger(__name__)


class FileMemoryContext(MemoryContext):
    """Local file-based memory context.

    Provides local file persistence using SQLite + FAISS for vector storage.
    Supports both file path input and direct text content.
    """

    def __init__(
        self,
        storage: SQLiteVectorStore,
        embedding: EmbeddingBase,
        llm: Optional[LLMBase] = None
    ):
        """Initialize File Memory Context.

        Args:
            storage: SQLiteVectorStore instance for persistence
            embedding: Embedding model for vectorization
            llm: Optional LLM for fact extraction
        """
        self.storage = storage
        self.embedding = embedding
        self.llm = llm

        # Supported file extensions for text reading
        self._text_extensions = {".txt", ".md", ".json", ".xml", ".csv", ".log", ".py", ".js", ".ts", ".java", ".c", ".cpp", ".h", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf"}

    def add(self, content: Any, **kwargs) -> str:
        """Add memory from file or text content.

        Args:
            content: File path (str) or text content
            **kwargs:
                user_id: str (required)
                metadata: dict (optional)
                infer: bool (optional, default True) - whether to extract facts via LLM
                file_path: str (optional) - explicit file path

        Returns:
            Memory ID
        """
        user_id = kwargs.get("user_id")
        if not user_id:
            raise ValueError("user_id is required for FileMemoryContext")

        metadata = kwargs.get("metadata", {})
        file_path = kwargs.get("file_path")

        # Determine if content is a file path
        if isinstance(content, str):
            if file_path and os.path.isfile(file_path):
                # Explicit file path provided
                content = self._read_file_content(file_path)
                metadata["file_path"] = file_path
                metadata["file_type"] = self._get_file_type(file_path)
            elif os.path.isfile(content):
                # Content is itself a file path
                file_path = content
                content = self._read_file_content(file_path)
                metadata["file_path"] = file_path
                metadata["file_type"] = self._get_file_type(file_path)

        # Generate content hash for deduplication
        content_hash = self._compute_hash(content)
        metadata["content_hash"] = content_hash

        # Check for duplicates
        if self.storage.exists(content_hash, user_id):
            logger.debug(f"Duplicate content detected (hash={content_hash[:8]}...)")
            # Return existing memory ID would be better, but interface returns str
            # For now, we still store but this could be optimized
            existing = self.storage.list(filters={"user_id": user_id, "content_hash": content_hash}, limit=1)
            if existing:
                return existing[0]["id"]

        # Extract facts using LLM if enabled
        if kwargs.get("infer", True) and self.llm:
            try:
                facts = self._extract_facts(content, user_id)
                if facts:
                    content = facts[0].get("fact", content)
                    metadata["extracted_facts"] = facts
            except Exception as e:
                logger.warning(f"LLM fact extraction failed: {e}")

        # Generate embedding
        vector = self.embedding.embed(content)

        # Prepare payload
        payload = {
            "user_id": user_id,
            "content": content,
            "original_message": str(content)[:10000] if len(str(content)) > 10000 else str(content),
            "metadata": metadata
        }

        # Insert into storage
        ids = self.storage.insert([vector], [payload])
        return ids[0]

    def search(self, query: Any, **kwargs) -> List[Dict[str, Any]]:
        """Search memories.

        Args:
            query: Search query (str or file path)
            **kwargs:
                user_id: str (required)
                limit: int (default 10)

        Returns:
            List of search results
        """
        user_id = kwargs.get("user_id")
        if not user_id:
            raise ValueError("user_id is required for FileMemoryContext")

        limit = kwargs.get("limit", 10)

        # Generate query embedding
        query_text = str(query)
        if os.path.isfile(query):
            query_text = self._read_file_content(query)

        query_vector = self.embedding.embed(query_text)

        # Search storage
        results = self.storage.search(
            query_vector=query_vector,
            limit=limit,
            filters={"user_id": user_id}
        )

        return [format_memory_result(r) for r in results]

    def get(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific memory by ID.

        Args:
            memory_id: Memory identifier

        Returns:
            Memory data or None
        """
        result = self.storage.get(memory_id)
        return format_memory_result(result) if result else None

    def delete(self, memory_id: str) -> bool:
        """Delete a memory by ID.

        Args:
            memory_id: Memory identifier

        Returns:
            True if deleted successfully
        """
        return self.storage.delete(memory_id)

    def update(self, memory_id: str, data: Any, **kwargs) -> Dict[str, Any]:
        """Update a memory.

        Args:
            memory_id: Memory identifier
            data: New content
            **kwargs:
                metadata: dict (optional)

        Returns:
            Updated memory data
        """
        payload = {"content": str(data)}
        if "metadata" in kwargs:
            payload["metadata"] = kwargs["metadata"]

        self.storage.update(memory_id, payload=payload)
        return self.get(memory_id) or {}

    def get_all(self, user_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get all memories for a user.

        Args:
            user_id: User identifier
            limit: Optional limit

        Returns:
            List of memories
        """
        results = self.storage.get_by_user(user_id, limit=limit)
        return [format_memory_result(r) for r in results]

    def close(self) -> None:
        """Close connections."""
        if hasattr(self.storage, 'close'):
            self.storage.close()

    def _read_file_content(self, file_path: str) -> str:
        """Read content from a text file.

        Args:
            file_path: Path to file

        Returns:
            File content as string
        """
        ext = self._get_file_type(file_path)

        if ext == "json":
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return json.dumps(data, ensure_ascii=False, indent=2)
        else:
            # Try UTF-8 first, fall back to binary read with replacement
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except UnicodeDecodeError:
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    return f.read()

    def _get_file_type(self, file_path: str) -> str:
        """Get file extension without dot.

        Args:
            file_path: Path to file

        Returns:
            File extension (e.g., "txt", "md", "json")
        """
        ext = os.path.splitext(file_path)[1].lower()
        return ext[1:] if ext else "unknown"

    def _compute_hash(self, content: str) -> str:
        """Compute MD5 hash of content.

        Args:
            content: Content to hash

        Returns:
            MD5 hex digest
        """
        return hashlib.md5(content.encode('utf-8')).hexdigest()

    def _extract_facts(self, content: str, user_id: str) -> List[Dict]:
        """Extract facts from content using LLM.

        Args:
            content: Content to analyze
            user_id: User identifier

        Returns:
            List of extracted facts
        """
        if not self.llm:
            return []

        try:
            # Simple prompt for fact extraction
            prompt = f"""Extract key facts from the following content. Return a JSON array of facts.

Content:
{content[:2000]}

Response format:
[{{"fact": "fact text", "topic": "topic name"}}]
"""
            response = self.llm.generate(prompt, user_id=user_id)

            # Try to parse JSON response
            if response:
                # Find JSON array in response
                start = response.find('[')
                end = response.rfind(']') + 1
                if start != -1 and end != 0:
                    facts = json.loads(response[start:end])
                    return facts if isinstance(facts, list) else []

        except Exception as e:
            logger.warning(f"Fact extraction failed: {e}")

        return []
