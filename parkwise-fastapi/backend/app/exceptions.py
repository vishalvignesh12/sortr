from fastapi import HTTPException, status, Request
from fastapi.responses import JSONResponse
from typing import Union
import logging
from .logging_config import log_error

# Custom Exception Classes
class ParkWiseException(Exception):
    """Base exception class for ParkWise application"""
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

class SlotNotFoundException(ParkWiseException):
    """Raised when a requested parking slot is not found"""
    pass

class SlotOccupiedException(ParkWiseException):
    """Raised when trying to reserve an already occupied slot"""
    pass

class SlotReservedException(ParkWiseException):
    """Raised when trying to reserve an already reserved slot"""
    pass

class BookingNotFoundException(ParkWiseException):
    """Raised when a requested booking is not found"""
    pass

class BookingExpiredException(ParkWiseException):
    """Raised when trying to access an expired booking"""
    pass

class InvalidCredentialsException(ParkWiseException):
    """Raised when user provides invalid login credentials"""
    pass

class UserAlreadyExistsException(ParkWiseException):
    """Raised when trying to register a user with an existing email"""
    pass

class InsufficientPermissionsException(ParkWiseException):
    """Raised when a user doesn't have permission to perform an action"""
    pass

class APIKeyExpiredException(ParkWiseException):
    """Raised when using an expired API key"""
    pass

class APIKeyDeactivatedException(ParkWiseException):
    """Raised when using a deactivated API key"""
    pass

class RateLimitExceededException(ParkWiseException):
    """Raised when rate limit is exceeded"""
    pass

class PaymentProcessingException(ParkWiseException):
    """Raised when payment processing fails"""
    pass

class DatabaseConnectionException(ParkWiseException):
    """Raised when there's an issue with database connectivity"""
    pass

class RedisConnectionException(ParkWiseException):
    """Raised when there's an issue with Redis connectivity"""
    pass

class ExternalServiceException(ParkWiseException):
    """Raised when external services (like prediction) are unavailable"""
    pass

# Exception Handler Functions
async def parkwise_exception_handler(request: Request, exc: ParkWiseException):
    """Handle ParkWise custom exceptions"""
    log_error(exc, f"ParkWiseException: {exc.message}", request)
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "parkwise_error",
            "message": exc.message,
            "details": exc.details
        }
    )

async def slot_not_found_handler(request: Request, exc: SlotNotFoundException):
    """Handle slot not found exceptions"""
    log_error(exc, "SlotNotFoundException", request)
    
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "error": "slot_not_found",
            "message": exc.message,
            "details": exc.details
        }
    )

async def slot_occupied_handler(request: Request, exc: SlotOccupiedException):
    """Handle slot occupied exceptions"""
    log_error(exc, "SlotOccupiedException", request)
    
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "error": "slot_occupied",
            "message": exc.message,
            "details": exc.details
        }
    )

async def booking_not_found_handler(request: Request, exc: BookingNotFoundException):
    """Handle booking not found exceptions"""
    log_error(exc, "BookingNotFoundException", request)
    
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "error": "booking_not_found",
            "message": exc.message,
            "details": exc.details
        }
    )

async def invalid_credentials_handler(request: Request, exc: InvalidCredentialsException):
    """Handle invalid credentials exceptions"""
    log_error(exc, "InvalidCredentialsException", request)
    
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={
            "error": "invalid_credentials",
            "message": exc.message,
            "details": exc.details
        }
    )

async def insufficient_permissions_handler(request: Request, exc: InsufficientPermissionsException):
    """Handle insufficient permissions exceptions"""
    log_error(exc, "InsufficientPermissionsException", request)
    
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={
            "error": "insufficient_permissions",
            "message": exc.message,
            "details": exc.details
        }
    )

async def api_key_expired_handler(request: Request, exc: APIKeyExpiredException):
    """Handle expired API key exceptions"""
    log_error(exc, "APIKeyExpiredException", request)
    
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={
            "error": "api_key_expired",
            "message": exc.message,
            "details": exc.details
        }
    )

async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceededException):
    """Handle rate limit exceeded exceptions"""
    log_error(exc, "RateLimitExceededException", request)
    
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "error": "rate_limit_exceeded",
            "message": exc.message,
            "details": exc.details
        }
    )

# HTTP Exception Handler
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle FastAPI HTTP exceptions"""
    log_error(exc, f"HTTPException: {exc.status_code}", request)
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "http_error",
            "message": exc.detail if hasattr(exc, 'detail') else "An error occurred",
            "status_code": exc.status_code
        }
    )

# General Exception Handler
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions"""
    log_error(exc, "GeneralException", request)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "internal_server_error",
            "message": "An unexpected error occurred",
            "details": str(exc) if __name__ == "__main__" else None  # Only include details in development
        }
    )

# Error Response Model
class ErrorResponse:
    def __init__(self, error_type: str, message: str, details: dict = None):
        self.error_type = error_type
        self.message = message
        self.details = details or {}

# Initialize handlers mapping
EXCEPTION_HANDLERS = {
    ParkWiseException: parkwise_exception_handler,
    SlotNotFoundException: slot_not_found_handler,
    SlotOccupiedException: slot_occupied_handler,
    BookingNotFoundException: booking_not_found_handler,
    InvalidCredentialsException: invalid_credentials_handler,
    InsufficientPermissionsException: insufficient_permissions_handler,
    APIKeyExpiredException: api_key_expired_handler,
    RateLimitExceededException: rate_limit_exceeded_handler,
}