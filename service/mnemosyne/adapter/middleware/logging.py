import uuid
import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = structlog.get_logger()

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        logger.info(
            "request_start",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            client=request.client.host if request.client else "unknown"
        )

        response = await call_next(request)

        logger.info(
            "request_end",
            request_id=request_id,
            status_code=response.status_code
        )

        return response