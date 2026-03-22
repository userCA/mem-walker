from abc import ABC, abstractmethod
from typing import List, Optional
from pydantic import BaseModel

class LLMMessage(BaseModel):
    role: str
    content: str

class LLMProvider(ABC):
    """Interface for LLM providers."""

    @abstractmethod
    async def chat(self, messages: List[LLMMessage], **kwargs) -> str:
        """Send chat request and return assistant response."""
        pass

    @abstractmethod
    async def close(self):
        """Close the LLM connection."""
        pass