from fastapi import Request
from fastapi.responses import JSONResponse
from ..exception.adapters import AdapterError

async def adapter_exception_handler(request: Request, exc: AdapterError):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "data": None,
            "error": {
                "code": exc.code,
                "message": exc.message,
                "request_id": getattr(request.state, "request_id", None)
            }
        }
    )

async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "data": None,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": str(exc),
                "request_id": getattr(request.state, "request_id", None)
            }
        }
    )