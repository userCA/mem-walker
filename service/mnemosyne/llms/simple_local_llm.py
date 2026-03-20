"""Simple Local LLM implementation.

This module provides a lightweight Async LLM implementation compatible with OpenAI API,
based on user-provided example code.
"""

import json
from typing import Any, Dict, List, Optional
import os
from openai import OpenAI
import logging

from .base import LLMBase

# Create a module-level logger since we don't have the server.logger module
logger = logging.getLogger(__name__)

class SimpleLocalLLM(LLMBase):
    """
    Simple Local LLM implementation using OpenAI (Synchronous).
    """
    
    def __init__(self, model_name: str = "", base_url: str = ""):
        """
        Initialize SimpleLocalLLM.
        
        Args:
            model_name: Model name to use (defaults to env var LOCAL_LLM_MODEL)
            base_url: API base URL (defaults to env var LOCAL_LLM_BASE_URL)
        """
        # Load from env if not provided
        self.model_name = model_name or os.getenv("LOCAL_LLM_MODEL", "")
        self.base_url = base_url or os.getenv("LOCAL_LLM_BASE_URL", "")
        
        if not self.base_url:
            logger.warning("LOCAL_LLM_BASE_URL not set, using default")
            
        self.client = OpenAI(
            api_key="EMPTY",  # Local models usually don't need key or accept any key
            base_url=self.base_url,
        )
        logger.info(f"Initialized SimpleLocalLLM (Sync) with model={self.model_name} at {self.base_url}")

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
        """
        Generate text completion from prompt (Synchronous, Non-streaming).
        
        Args:
            prompt: User prompt
            system_prompt: Optional system instructions
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        logger.debug(f"LLM Input: {messages}")
        
        try:
            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                extra_body={
                    "chat_template_kwargs": {"enable_thinking": False},
                },
                stream=False
            )
            
            response = completion.choices[0].message.content or ""
            logger.debug(f"LLM Output: {response[:100]}...")
            return response
            
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return "System is busy, please try again later."

    def extract_facts(self, messages: str, user_id: str, existing_facts: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Extract factual information from messages."""
        system_prompt = """你是一个事实提取助手。从对话中提取关键事实。
返回一个包含以下字段的JSON对象数组："fact"（提取的事实），"category"（事实类型），"confidence"（置信度 0.0-1.0）。
关注偏好、个人信息、关系和重要事件。
必须保持输入内容的原始语言（例如：如果输入是中文，提取的事实必须是中文）。
提取的事实中，请将第一人称（"我"）替换为用户ID或"用户"。"""
        
        user_prompt = f"用户ID: {user_id}\n\n从以下对话中提取事实:\n\n{messages}"
        
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
            facts = self._parse_json(response)
            
            logger.debug(f"Extracted {len(facts)} facts")
            return facts
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse facts JSON: {e}")
            return []
        except Exception as e:
            logger.error(f"Fact extraction failed: {e}")
            return []

    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract entities and relationships."""
        system_prompt = """你是一个实体提取助手。从文本中提取实体和关系。
返回一个JSON数组，包含字段："entity"（实体名称），"type"（PERSON, PLACE, THING等），"relations"（{target, type}数组）。
示例: [{"entity": "张三", "type": "PERSON", "relations": [{"target": "谷歌", "type": "WORKS_AT"}]}]
必须保持输入内容的原始语言。"""
        
        user_prompt = f"提取实体和关系:\n\n{text}"
        
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

    def detect_conflicts(self, new_fact: str, existing_facts: List[str]) -> Optional[Dict[str, Any]]:
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
                temperature=0.1
            )
            
            result = self._parse_json(response)
            if result.get("has_conflict"):
                return result
            return None
            
        except Exception as e:
            logger.error(f"Conflict detection failed: {e}")
            return None
