from prometheus_client import Counter, Histogram, Gauge, generate_latest, REGISTRY
import time
from fastapi import Request, Response
from .logging_config import log_error

# Define metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total number of requests',
    ['method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'Request latency in seconds',
    ['method', 'endpoint']
)

ACTIVE_USERS = Gauge(
    'active_users',
    'Number of active users'
)

ACTIVE_CONNECTIONS = Gauge(
    'db_active_connections',
    'Number of active database connections'
)

def init_metrics():
    """Initialize metrics - called at startup"""
    pass

def increment_request_count(method: str, endpoint: str, status: str):
    """Increment request counter"""
    REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status).inc()

def record_request_latency(method: str, endpoint: str, duration: float):
    """Record request latency"""
    REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(duration)

def get_metrics():
    """Get all metrics in Prometheus format"""
    return generate_latest(REGISTRY)

# Middleware to track metrics
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    
    try:
        response = await call_next(request)
        return response
    finally:
        duration = time.time() - start_time
        increment_request_count(
            request.method,
            request.url.path,
            str(response.status_code)
        )
        record_request_latency(request.method, request.url.path, duration)