"""Base abstract class for LLM providers."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class LLMBase(ABC):
    """
    Abstract base class for LLM providers.
    
    All LLM implementations should inherit from this class.
    """
    
    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Generate text completion from prompt.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system instructions
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text
        """
        pass
    
    @abstractmethod
    def extract_facts(
        self,
        messages: str,
        user_id: str,
        existing_facts: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract factual information from messages.
        
        Args:
            messages: Conversation messages
            user_id: User ID for context
            existing_facts: Previously extracted facts
            
        Returns:
            List of extracted facts with metadata
        """
        pass
    
    @abstractmethod
    def extract_entities(
        self,
        text: str
    ) -> List[Dict[str, Any]]:
        """
        Extract entities and relationships from text.
        
        Args:
            text: Input text
            
        Returns:
            List of entities with types and relationships
        """
        pass
    
    @abstractmethod
    def detect_conflicts(
        self,
        new_fact: str,
        existing_facts: List[str]
    ) -> Optional[Dict[str, Any]]:
        """
        Detect conflicts between new and existing facts.
        
        Args:
            new_fact: New fact to check
            existing_facts: List of existing facts
            
        Returns:
            Conflict information or None if no conflict
        """
        pass
