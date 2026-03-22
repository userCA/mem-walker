from pydantic import BaseModel, Field
from typing import Any, Optional, Generic, TypeVar

T = TypeVar("T")

class ApiResponse(BaseModel):
    success: bool = True
    data: Optional[Any] = None
    error: Optional[dict] = None

class PaginatedResponse(BaseModel):
    items: list = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = Field(alias="pageSize", default=20)
    has_more: bool = Field(alias="hasMore", default=False)

    class Config:
        populate_by_name = True