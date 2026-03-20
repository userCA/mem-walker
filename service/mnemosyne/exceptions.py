"""Custom exceptions for Mnemosyne memory system."""


class MnemosyneError(Exception):
    """Base exception for all Mnemosyne errors."""
    pass


class ConfigurationError(MnemosyneError):
    """Raised when there's a configuration error."""
    pass


class EmbeddingError(MnemosyneError):
    """Raised when embedding operation fails."""
    pass


class VectorStoreError(MnemosyneError):
    """Raised when vector store operation fails."""
    pass


class GraphStoreError(MnemosyneError):
    """Raised when graph store operation fails."""
    pass


class LLMError(MnemosyneError):
    """Raised when LLM operation fails."""
    pass


class MemoryError(MnemosyneError):
    """Raised when memory operation fails."""
    pass


class ValidationError(MnemosyneError):
    """Raised when data validation fails."""
    pass
