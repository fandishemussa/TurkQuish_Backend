import logging
import time
import uuid
from collections import defaultdict, deque
from typing import DefaultDict, Deque

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse, Response

logger = logging.getLogger("turkquish.request")


class RequestContextMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_requests_per_minute: int = 60):
        super().__init__(app)
        self.max_requests_per_minute = max(0, max_requests_per_minute)
        self._requests: DefaultDict[str, Deque[float]] = defaultdict(deque)

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        started_at = time.perf_counter()

        if self._is_rate_limited(_client_key(request), started_at):
            response: Response = JSONResponse(
                status_code=429,
                content={
                    "error": {
                        "code": "rate_limited",
                        "message": "Too many requests. Try again shortly.",
                        "requestId": request_id,
                    }
                },
            )
        else:
            response = await call_next(request)

        elapsed_ms = int((time.perf_counter() - started_at) * 1000)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time-ms"] = str(elapsed_ms)
        logger.info(
            "%s %s %s %sms request_id=%s",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
            request_id,
        )
        return response

    def _is_rate_limited(self, client_key: str, now: float) -> bool:
        if self.max_requests_per_minute <= 0:
            return False
        bucket = self._requests[client_key]
        window_start = now - 60.0
        while bucket and bucket[0] < window_start:
            bucket.popleft()
        if len(bucket) >= self.max_requests_per_minute:
            return True
        bucket.append(now)
        return False


def _client_key(request: Request) -> str:
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip()
    if request.client:
        return request.client.host
    return "unknown"
