import logging
import time
import uuid


from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Use existing request ID if present, otherwise generate a new one
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

        start_time = time.perf_counter()

        try:
            response = await call_next(request)

            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

            logger.info(
                "HTTP Request Completed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                },
            )

            response.headers["X-Request-ID"] = request_id

            return response

        except Exception:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

            logger.exception(
                "HTTP Request Failed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": duration_ms,
                },
            )

            raise
