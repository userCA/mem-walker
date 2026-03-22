import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

class PerformanceMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start_time) * 1000

        response.headers["X-Process-Time-Ms"] = f"{duration_ms:.2f}"
        return response