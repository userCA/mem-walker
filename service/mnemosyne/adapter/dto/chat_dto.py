from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum

class ChatRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class ChatMessage(BaseModel):
    id: str
    role: ChatRole
    content: str
    status: str = "sent"
    createdAt: datetime = Field(default_factory=datetime.now)

class ChatSession(BaseModel):
    id: str
    title: str
    messages: list[ChatMessage] = Field(default_factory=list)
    memoryCount: int = 0
    createdAt: datetime = Field(default_factory=datetime.now)
    updatedAt: datetime = Field(default_factory=datetime.now)
    isPinned: bool = False
    isExpanded: bool = True

class ChatConfig(BaseModel):
    model: str = "gpt-4"
    temperature: float = 0.7
    maxTokens: int = 2000
    topP: float = 1.0
    repeatPenalty: float = 1.1

class SendMessageRequest(BaseModel):
    content: str
    config: Optional[dict] = None