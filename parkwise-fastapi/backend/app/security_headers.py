from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response as StarletteResponse
import time
import re

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> StarletteResponse:
        # Add security headers to all responses
        response: StarletteResponse = await call_next(request)
        
        # Strict Transport Security (HSTS)
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
        
        # Content Security Policy (CSP)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' https://*.stripe.com; "
            "frame-ancestors 'none';"
        )
        
        # X-Frame-Options
        response.headers["X-Frame-Options"] = "DENY"
        
        # X-Content-Type-Options
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions Policy
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # Cross-Origin-Embedder-Policy
        response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
        
        # Cross-Origin-Opener-Policy
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        
        # Cross-Origin-Resource-Policy
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
        
        return response

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_requests: int = 100, window_seconds: int = 3600):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> StarletteResponse:
        # In a real implementation, this would use Redis or similar for distributed rate limiting
        # For now, we'll use an in-memory approach that works only with a single instance
        client_ip = self.get_client_ip(request)
        current_time = time.time()
        
        # Clean old entries
        self.requests = {ip: times for ip, times in self.requests.items() 
                         if any(t > current_time - self.window_seconds for t in times)}
        
        # Track request
        if client_ip not in self.requests:
            self.requests[client_ip] = []
        self.requests[client_ip].append(current_time)
        
        # Check rate limit
        recent_requests = [t for t in self.requests[client_ip] if t > current_time - self.window_seconds]
        if len(recent_requests) > self.max_requests:
            from fastapi import HTTPException
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        
        response = await call_next(request)
        return response
    
    def get_client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

class InputValidationMiddleware(BaseHTTPMiddleware):
    """Validate input to prevent common attacks"""
    
    # Common attack patterns to block
    dangerous_patterns = [
        r'<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>',  # XSS
        r'\b(union|select|insert|update|delete|drop|create|alter|exec|execute)\b',  # SQL injection
        r'\.\.\/',  # Directory traversal
        r'(\%3C)|(\%3E)',  # URL encoded XSS
    ]
    
    def __init__(self, app):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> StarletteResponse:
        # Sanitize the request body and query parameters
        # Note: This is a simplified version - in production, use proper validation libraries
        
        # For now, we'll just allow the request to continue
        # Proper validation would happen in Pydantic models with field validators
        response = await call_next(request)
        return response

def sanitize_input(input_str: str) -> str:
    """Basic input sanitization function"""
    if input_str is None:
        return input_str
    
    # Remove potentially dangerous characters/sequences
    sanitized = input_str
    
    # Remove script tags (basic XSS protection)
    sanitized = re.sub(r'<script[^>]*>.*?</script>', '', sanitized, flags=re.IGNORECASE | re.DOTALL)
    
    # Remove javascript: and vbscript: (basic XSS protection)
    sanitized = re.sub(r'javascript:', '', sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r'vbscript:', '', sanitized, flags=re.IGNORECASE)
    
    # Remove potentially dangerous SQL keywords (basic SQL injection protection)
    dangerous_keywords = ['union', 'select', 'insert', 'update', 'delete', 'drop', 'create', 'alter', 'exec', 'execute']
    for keyword in dangerous_keywords:
        # Replace whole words only to avoid false positives
        sanitized = re.sub(rf'\b{keyword}\b', '', sanitized, flags=re.IGNORECASE)
    
    return sanitized.strip()