import pytest
from mnemosyne.adapter.dto.common import ApiResponse, PaginatedResponse

def test_api_response_success():
    response = ApiResponse(success=True, data={"key": "value"})
    assert response.success is True
    assert response.data == {"key": "value"}
    assert response.error is None

def test_api_response_error():
    response = ApiResponse(success=False, data=None, error={"code": "NOT_FOUND", "message": "Not found"})
    assert response.success is False
    assert response.error["code"] == "NOT_FOUND"

def test_paginated_response():
    response = PaginatedResponse(
        items=[{"id": "1"}, {"id": "2"}],
        total=10,
        page=1,
        page_size=2,
        has_more=True
    )
    assert len(response.items) == 2
    assert response.total == 10
    assert response.has_more is True