"""In-memory sliding window rate limiter middleware.

Tracks request counts per IP (or session for signal endpoints) using a
sliding window counter. Returns 429 with Retry-After header when limits
are exceeded. Designed for single-process deployments.
"""

import time
from collections import defaultdict

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

logger = structlog.get_logger()

# Rate limit rules: (path_prefix, key_type, max_requests, window_seconds)
# key_type: "ip" uses client IP, "session" extracts session_id from path
RATE_LIMITS: list[tuple[str, str, int, int]] = [
    # POST /api/v1/simulation — max 10 per IP per minute
    ("/api/v1/simulation", "ip", 10, 60),
    # POST /api/v1/challenge — max 5 per IP per minute
    ("/api/v1/challenge", "ip", 5, 60),
]

# Signal endpoint: max 30 per session per minute
SIGNAL_LIMIT = 30
SIGNAL_WINDOW = 60


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Sliding window rate limiter.

    Uses a dict of (key → list[timestamp]) to track recent requests.
    Expired entries are pruned on each check.
    """

    def __init__(self, app):
        super().__init__(app)
        self._buckets: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        from app.config import settings

        # Skip rate limiting if disabled (e.g., during tests)
        if not settings.RATE_LIMIT_ENABLED:
            return await call_next(request)

        # Only rate-limit POST requests
        if request.method != "POST":
            return await call_next(request)

        path = request.url.path
        now = time.time()

        # Check signal endpoint: /api/v1/simulation/{session_id}/signal
        if "/simulation/" in path and path.endswith("/signal"):
            parts = path.split("/")
            # Extract session_id from path: /api/v1/simulation/{session_id}/signal
            if len(parts) >= 5:
                session_id = parts[4]
                bucket_key = f"signal:{session_id}"
                result = self._check_limit(bucket_key, now, SIGNAL_LIMIT, SIGNAL_WINDOW)
                if result is not None:
                    return result

        # Check general rate limits
        for prefix, key_type, max_requests, window in RATE_LIMITS:
            # Match exact path (not sub-paths like /simulation/{id}/signal)
            if path == prefix:
                if key_type == "ip":
                    client_ip = self._get_client_ip(request)
                    bucket_key = f"{prefix}:{client_ip}"
                else:
                    bucket_key = f"{prefix}:global"
                result = self._check_limit(bucket_key, now, max_requests, window)
                if result is not None:
                    return result

        return await call_next(request)

    def _check_limit(
        self,
        bucket_key: str,
        now: float,
        max_requests: int,
        window_seconds: int,
    ) -> JSONResponse | None:
        """Check if a request should be rate-limited.

        Returns a 429 response if the limit is exceeded, or None to allow.
        """
        cutoff = now - window_seconds
        # Prune expired entries
        self._buckets[bucket_key] = [t for t in self._buckets[bucket_key] if t > cutoff]

        if len(self._buckets[bucket_key]) >= max_requests:
            retry_after = int(self._buckets[bucket_key][0] + window_seconds - now) + 1
            logger.warning(
                "Rate limit exceeded",
                bucket=bucket_key,
                limit=max_requests,
                window=window_seconds,
                retry_after=retry_after,
            )
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please try again later."},
                headers={"Retry-After": str(retry_after)},
            )

        # Record this request
        self._buckets[bucket_key].append(now)
        return None

    @staticmethod
    def _get_client_ip(request: Request) -> str:
        """Extract client IP, respecting X-Forwarded-For for proxied requests."""
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
