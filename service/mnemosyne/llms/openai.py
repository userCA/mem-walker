"""OpenAI LLM implementation."""

import json
from typing import Any, Dict, List, Optional

from openai import OpenAI

from ..exceptions import LLMError
from ..utils import get_logger
from .base import LLMBase
from .configs import OpenAILLMConfig

logger = get_logger(__name__)


class OpenAILLM(LLMBase):
    """
    OpenAI LLM implementation.
    
    Uses OpenAI's GPT models for text generation and extraction tasks.
    """
    
    def __init__(self, config: Optional[OpenAILLMConfig] = None):
        """
        Initialize OpenAI LLM.
        
        Args:
            config: Configuration for OpenAI LLM
        """
        if config is None:
            config = OpenAILLMConfig()
        
        self.config = config
        
        try:
            self.client = OpenAI(
                api_key=config.api_key,
                organization=config.organization,
                base_url=config.base_url
            )
        except Exception as e:
            raise LLMError(f"Failed to initialize OpenAI client: {e}")
        
        logger.info(f"Initialized OpenAI LLM with model: {config.model}")
    
    def _parse_json(self, text: str) -> Any:
        """Parse JSON from text, handling markdown code blocks."""
        text = text.strip()
        
        # Remove markdown code blocks if present
        if text.startswith("```"):
            # Find the first newline after the opening ```
            first_newline = text.find("\n")
            if first_newline != -1:
                # Find the last ```
                last_backticks = text.rfind("```")
                if last_backticks > first_newline:
                    text = text[first_newline:last_backticks].strip()
        
        # Also try to find the first { or [ and last } or ] if straightforward parse fails
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Try to extract JSON substring
            start_idx = -1
            end_idx = -1
            
            # Check for array
            if '[' in text and ']' in text:
                start_idx = text.find('[')
                end_idx = text.rfind(']') + 1
            # Check for object
            elif '{' in text and '}' in text:
                start_idx = text.find('{')
                end_idx = text.rfind('}') + 1
                
            if start_idx != -1 and end_idx != -1:
                try:
                    return json.loads(text[start_idx:end_idx])
                except json.JSONDecodeError:
                    pass
            
            raise

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """Generate text completion."""
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens or self.config.max_tokens
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            raise LLMError(f"Text generation failed: {e}")
    
    def extract_facts(
        self,
        messages: str,
        user_id: str,
        existing_facts: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Extract factual information from messages."""
        system_prompt = """You are a fact extraction assistant. Extract key facts from the conversation.
Return facts as a JSON array of objects with fields: "fact" (the extracted fact), "category" (type of fact), "confidence" (0.0-1.0).
Focus on preferences, personal information, relationships, and important events."""
        
        user_prompt = f"Extract facts from this conversation:\n\n{messages}"
        
        if existing_facts:
            user_prompt += f"\n\nExisting facts:\n" + "\n".join(existing_facts)
            user_prompt += "\n\nOnly extract NEW facts not already in the existing facts."
        
        try:
            response = self.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.3  # Lower temperature for extraction
            )
            
            # Parse JSON response
            facts = json.loads(response)
            
            logger.debug(f"Extracted {len(facts)} facts")
            return facts
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse facts JSON: {e}")
            return []
        except Exception as e:
            logger.error(f"Fact extraction failed: {e}")
            return []
    
    def extract_entities(
        self,
        text: str
    ) -> List[Dict[str, Any]]:
        """Extract entities and relationships."""
        system_prompt = """You are an entity extraction assistant. Extract entities and relationships from text.
Return as JSON array with fields: "entity" (entity name), "type" (PERSON, PLACE, THING, etc.), "relations" (array of {target, type}).
Example: [{"entity": "John", "type": "PERSON", "relations": [{"target": "Google", "type": "WORKS_AT"}]}]"""
        
        user_prompt = f"Extract entities and relationships:\n\n{text}"
        
        try:
            response = self.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.3
            )
            
            entities = self._parse_json(response)
            logger.debug(f"Extracted {len(entities)} entities")
            return entities
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse entities JSON: {e}")
            return []
        except Exception as e:
            logger.error(f"Entity extraction failed: {e}")
            return []
    
    def detect_conflicts(
        self,
        new_fact: str,
        existing_facts: List[str]
    ) -> Optional[Dict[str, Any]]:
        """Detect conflicts between facts."""
        system_prompt = """You are a conflict detection assistant. Determine if a new fact conflicts with existing facts.
Return JSON: {"has_conflict": true/false, "conflicting_fact": "...", "reason": "..."}
Return null if no conflict."""
        
        user_prompt = f"""New fact: {new_fact}

Existing facts:
{chr(10).join(f"- {fact}" for fact in existing_facts)}

Does the new fact conflict with any existing facts?"""
        
        try:
            response = self.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.1  # Very low temperature for consistency
            )
            
            if response.strip().lower() == "null":
                return None
            
            conflict = self._parse_json(response)
            return conflict if conflict.get("has_conflict") else None
            
        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"Conflict detection failed: {e}")
            return None
