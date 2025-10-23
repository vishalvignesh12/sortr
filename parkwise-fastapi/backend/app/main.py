from fastapi import FastAPI, Response, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from .routes import bookings, predictions, auth, users, payments, notifications, admin, api_keys, export, geolocation, backup, cv_routes, edge, anpr, violations, heatmaps
from .worker import prediction_consumer, start_workers
from .core import settings
from .middleware import logging_middleware
from .metrics import get_metrics, metrics_middleware
from .cache import cache
from .websocket import websocket_endpoint, notify_slot_update, notify_booking_update, notify_system_alert
from .security_headers import SecurityHeadersMiddleware, RateLimitMiddleware, InputValidationMiddleware
from .exceptions import (
    general_exception_handler, 
    http_exception_handler, 
    parkwise_exception_handler,
    slot_not_found_handler,
    slot_occupied_handler,
    booking_not_found_handler,
    invalid_credentials_handler,
    insufficient_permissions_handler,
    api_key_expired_handler,
    rate_limit_exceeded_handler,
    ParkWiseException,
    SlotNotFoundException,
    SlotOccupiedException,
    BookingNotFoundException,
    InvalidCredentialsException,
    InsufficientPermissionsException,
    APIKeyExpiredException,
    RateLimitExceededException
)
from .backup import run_retention_policies
from sqlalchemy import text
from .db import get_session
import asyncio
import httpx
import redis.asyncio as redis
from . import anpr_processor
import logging

logger = logging.getLogger(__name__)

# Initialize the limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="ParkWise Backend")

# Add middleware (order matters - from outside to inside)
app.add_middleware(InputValidationMiddleware)  # Input validation first
app.add_middleware(SecurityHeadersMiddleware)  # Security headers next
app.add_middleware(RateLimitMiddleware, max_requests=1000, window_seconds=3600)  # Rate limiting
app.middleware("http")(logging_middleware)  # Logging
app.middleware("http")(metrics_middleware)  # Metrics

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Exception handlers
app.add_exception_handler(Exception, general_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(ParkWiseException, parkwise_exception_handler)
app.add_exception_handler(SlotNotFoundException, slot_not_found_handler)
app.add_exception_handler(SlotOccupiedException, slot_occupied_handler)
app.add_exception_handler(BookingNotFoundException, booking_not_found_handler)
app.add_exception_handler(InvalidCredentialsException, invalid_credentials_handler)
app.add_exception_handler(InsufficientPermissionsException, insufficient_permissions_handler)
app.add_exception_handler(APIKeyExpiredException, api_key_expired_handler)
app.add_exception_handler(RateLimitExceededException, rate_limit_exceeded_handler)

app.include_router(bookings.router)
app.include_router(predictions.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(payments.router)
app.include_router(notifications.router)
app.include_router(admin.router)
app.include_router(api_keys.router)
app.include_router(export.router)
app.include_router(geolocation.router)
app.include_router(backup.router)
app.include_router(cv_routes.router)
app.include_router(edge.router)
app.include_router(anpr.router)
app.include_router(violations.router)
app.include_router(heatmaps.router)

# WebSocket endpoint
@app.websocket("/ws/{connection_type}")
async def websocket_endpoint_wrapper(websocket: WebSocket, connection_type: str):
    await websocket_endpoint(websocket, connection_type)

@app.on_event("startup")
async def startup():
    # Initialize cache
    await cache.connect()
    
    # Initialize ANPR (EasyOCR reader)
    logger.info("Initializing ANPR system...")
    gpu_enabled = getattr(settings, 'EASYOCR_GPU', True)
    anpr_success = anpr_processor.initialize_anpr_reader(gpu=gpu_enabled)
    
    if anpr_success:
        logger.info("ANPR system initialized successfully")
        app.state.anpr_enabled = True
    else:
        logger.warning("ANPR system initialization failed - continuing without ANPR")
        app.state.anpr_enabled = False
    
    # launch prediction consumer in the background
    loop = asyncio.get_event_loop()
    loop.create_task(prediction_consumer())
    # Run retention policies in background
    loop.create_task(run_retention_policies())
    # optionally start expire holds scheduler in background task
    loop.create_task(start_workers())

@app.on_event("shutdown")
async def shutdown():
    # Close cache connection
    await cache.close()

@app.get("/health")
async def health():
    """Basic health check"""
    return {"status": "healthy", "service": "backend", "timestamp": asyncio.get_event_loop().time()}

@app.get("/health/ready")
async def readiness_check():
    """Readiness check - verify service dependencies are ready"""
    try:
        # Check database connection
        async for session in get_session():
            await session.execute(text("SELECT 1"))
            break  # Only need to test one connection
        
        # Check Redis connection (includes cache)
        redis_client = redis.from_url(settings.REDIS_URL)
        await redis_client.ping()
        await redis_client.close()
        
        # Check predictor service
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.PREDICTOR_URL}/health", timeout=5.0)
            predictor_healthy = response.status_code == 200
        
        return {
            "status": "ready",
            "database": "connected",
            "redis": "connected", 
            "predictor": "healthy" if predictor_healthy else "unhealthy",
            "timestamp": asyncio.get_event_loop().time()
        }
    except Exception as e:
        return {
            "status": "not ready",
            "error": str(e),
            "timestamp": asyncio.get_event_loop().time()
        }

@app.get("/health/live")
async def liveness_check():
    """Liveness check - verify service itself is operational"""
    return {
        "status": "alive",
        "service": "backend",
        "uptime": asyncio.get_event_loop().time(),
        "timestamp": asyncio.get_event_loop().time()
    }

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(content=get_metrics(), media_type="text/plain")