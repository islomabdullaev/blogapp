"""Security headers middleware"""
from typing import Callable
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Check if this is a documentation endpoint
        path = request.url.path
        is_docs = any(
            path.startswith(p) 
            for p in ["/docs", "/redoc", "/openapi.json", "/static"]
        )
        
        # For documentation endpoints, skip most security headers to allow proper rendering
        if is_docs:
            # Only add minimal security headers for docs
            response.headers["X-Content-Type-Options"] = "nosniff"
            # Don't set X-Frame-Options for docs (allows iframe embedding if needed)
            # Don't set strict CSP for docs
            return response
        
        # Add full security headers for all other endpoints
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        return response

