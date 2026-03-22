import httpx
from typing import List
from .base import LLMProvider, LLMMessage
from ..exception.adapters import LLMError

class DeepSeekProvider(LLMProvider):
    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com", model: str = "deepseek-chat"):
        self.api_key = api_key
        self.base_url = base_url
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
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                result = response.json()
                if result.get("choices") and len(result["choices"]) > 0:
                    return result["choices"][0]["message"]["content"]
                raise LLMError("No response content from DeepSeek")
        except httpx.HTTPStatusError as e:
            raise LLMError(f"DeepSeek API error: {e.response.status_code}")
        except Exception as e:
            raise LLMError(f"DeepSeek call failed: {str(e)}")

    async def close(self):
        pass