"""Configuration for LLM providers."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class LLMConfig:
    """Base configuration for LLM providers."""
    
    model: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 2000
    api_key: Optional[str] = None
    
    # Performance settings
    max_retries: int = 3
    timeout: int = 60


@dataclass
class OpenAILLMConfig(LLMConfig):
    """Configuration for OpenAI LLM."""
    
    model: str = "gpt-4"
    organization: Optional[str] = None
    base_url: Optional[str] = None
