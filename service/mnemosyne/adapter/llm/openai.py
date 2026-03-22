import httpx
from typing import List
from .base import LLMProvider, LLMMessage
from ..exception.adapters import LLMError

class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.api_key = api_key
        self.model = model

    async def chat(self, messages: List[LLMMessage], **kwargs) -> str:
        temperature = kwargs.get("temperature", 0.7)
        max_tokens = kwargs.get("max_tokens", 2000)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                result = response.json()
                if result.get("choices") and len(result["choices"]) > 0:
                    return result["choices"][0]["message"]["content"]
                raise LLMError("No response content from OpenAI")
        except httpx.HTTPStatusError as e:
            raise LLMError(f"OpenAI API error: {e.response.status_code}")
        except Exception as e:
            raise LLMError(f"OpenAI call failed: {str(e)}")

    async def close(self):
        pass