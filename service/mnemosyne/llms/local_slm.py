"""Local Small Language Model for fast entity extraction.

This module provides a lightweight LLM implementation using llama.cpp
for near-instant entity extraction during search operations.
"""

from typing import Any, Dict, List, Optional
import json
import time
from dataclasses import is_dataclass, asdict

import httpx
from openai import OpenAI

from .base import LLMBase
from ..utils import get_logger

logger = get_logger(__name__)


class CustomClient(httpx.Client):
    def __init__(self, *args, **kwargs):
        # Default header
        super().__init__(*args, timeout=httpx.Timeout(timeout=600.0, connect=5.0),
                         follow_redirects=True,
                         limits=httpx.Limits(max_connections=1000, max_keepalive_connections=100), **kwargs)

    def request(self, *args, **kwargs):
        # Ensure headers exist
        if 'headers' not in kwargs:
            kwargs['headers'] = {}
        else:
            # Convert headers to mutable dict
            kwargs['headers'] = dict(kwargs['headers'])

        response = super().request(*args, **kwargs)
        return response

    def send(self, request, *args, **kwargs):
        response = super().send(request, *args, **kwargs)
        return response


class LocalSLM(LLMBase):
    """
    Fast local small LLM for entity extraction using OpenAI-compatible API.
    
    Replaces direct llama.cpp binding with OpenAI client.
    """
    
    def __init__(self, config: Any):
        """
        Initialize LocalSLM.
        
        Args:
            config: Configuration object (dict or dataclass) with:
                - model_name (or model_path): Model name to use
                - base_url: API base URL
                - api_key: API key
        """
        # Handle config if it's a dataclass
        if is_dataclass(config):
            self.config = asdict(config)
        elif isinstance(config, dict):
            self.config = config
        else:
            self.config = {}

        self.model_name = self.config.get("model_name") or self.config.get("model_path", "")
        self.base_url = self.config.get("base_url", "http://localhost:8000/v1")
        self.api_key = self.config.get("api_key", "EMPTY")
        
        logger.info(f"Loading local SLM client for {self.model_name} at {self.base_url}")
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            http_client=CustomClient(),
        )
        logger.info("✅ Local SLM client initialized")

    def _call_llm(self, context: dict) -> str:
        """
        Internal method to call LLM non-streaming.
        """
        messages = context.get('messages', [])
        if not messages and 'prompt' in context:
            messages = [{"role": "user", "content": context['prompt']}]
            if context.get('system_prompt'):
                messages.insert(0, {"role": "system", "content": context['system_prompt']})

        logger.debug(f"LLM Input: {messages}")
        try:
            start_time = time.time()
            
            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                extra_body={
                    "chat_template_kwargs": {"enable_thinking": False},
                },
                stream=False,
                temperature=context.get('temperature', 0.1),
                max_tokens=context.get('max_tokens'),
                response_format=context.get('response_format')
            )

            full_response = completion.choices[0].message.content
            logger.debug(f"LLM Output: {full_response[:100]}...")
            logger.debug(f"Latency: {time.time() - start_time:.2f}s")
            
            return full_response
            
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return ""

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """Generate text completion."""
        context = {
            "prompt": prompt,
            "system_prompt": system_prompt,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        return self._call_llm(context).strip()

    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract entities using local SLM.
        """
        prompt = f"""<|im_start|>system
You are an entity extraction expert. Extract all entities from the text.
Return ONLY valid JSON in this exact format:
{{"entities": [{{"name": "entity_name", "type": "person|organization|location|topic"}}]}}
<|im_end|>
<|im_start|>user
{text}<|im_end|>
<|im_start|>assistant
"""
        
        context = {
            "prompt": prompt,
            "temperature": 0.1,
            "max_tokens": 128,
            "response_format": {"type": "json_object"}
        }
        
        result_text = self._call_llm(context)
            
        if not result_text:
            return []

        try:
            result = json.loads(result_text)
            
            # Convert to expected format
            entities = result.get("entities", [])
            return [
                {"entity": e.get("name"), "type": e.get("type", "unknown")}
                for e in entities
                if e.get("name")
            ]
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse SLM JSON output: {e}")
            return []
        except Exception as e:
            logger.error(f"Entity extraction failed: {e}")
            return []

    
    def extract_facts(
        self,
        messages: str,
        user_id: str,
        existing_facts: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        NOT IMPLEMENTED for LocalSLM.
        
        Fact extraction requires higher-quality LLM (e.g., GPT-4).
        This method should only be called during Write operations,
        where the main OpenAI LLM is used instead.
        """
        raise NotImplementedError(
            "LocalSLM is designed for Search path only. "
            "Use OpenAILLM for fact extraction in Write path."
        )
    
    def detect_conflicts(
        self,
        new_fact: str,
        existing_facts: List[str]
    ) -> Optional[Dict[str, Any]]:
        """
        NOT IMPLEMENTED for LocalSLM.
        
        Conflict detection requires reasoning capabilities of larger LLMs.
        """
        raise NotImplementedError(
            "LocalSLM is designed for Search path only. "
            "Use OpenAILLM for conflict detection."
        )
