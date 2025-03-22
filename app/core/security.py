"""Security utilities"""
from fastapi import Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import time
from app.config.settings import security_settings


class RateLimiter:
    """Rate limiter implementation"""

    def __init__(self, max_requests: int, time_window: int):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = {}

    def is_allowed(self, client_id: str) -> bool:
        """Check if request is allowed"""
        current_time = time.time()

        # Clean up old requests
        self.requests = {
            k: v for k, v in self.requests.items()
            if current_time - v[0] < self.time_window
        }

        # Check rate limit
        if client_id not in self.requests:
            self.requests[client_id] = [(current_time, 1)]
            return True

        requests_in_window = sum(1 for t, _ in self.requests[client_id]
                                 if current_time - t < self.time_window)

        if requests_in_window >= self.max_requests:
            return False

        self.requests[client_id].append((current_time, requests_in_window + 1))
        return True


# Initialize rate limiter
rate_limiter = RateLimiter(
    max_requests=security_settings.RATE_LIMIT_REQUESTS,
    time_window=security_settings.RATE_LIMIT_WINDOW
)


def get_client_id(request: Request) -> str:
    """Get client identifier"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0]
    return request.client.host


async def rate_limit_middleware(request: Request, call_next):
    """Rate limiting middleware"""
    client_id = get_client_id(request)

    if not rate_limiter.is_allowed(client_id):
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Please try again later."
        )

    return await call_next(request)


def setup_cors(app):
    """Setup CORS middleware with enhanced security"""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=security_settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
        expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining"],
        max_age=3600
    )


def validate_api_key(request: Request):
    """Validate API key"""
    api_key = request.headers.get("X-API-Key")
    if not api_key or api_key != security_settings.API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )


class SecurityMiddleware:
    """Security middleware"""

    async def __call__(self, request: Request, call_next):
        # Validate API key for protected endpoints
        if request.url.path not in ["/health", "/docs", "/redoc"]:
            validate_api_key(request)

        # Apply rate limiting
        response = await rate_limit_middleware(request, call_next)

        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return response
