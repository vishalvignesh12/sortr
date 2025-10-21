import logging
import sys
from datetime import datetime
from typing import Any
from fastapi import Request
from .core import settings

# Create formatter
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Create console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)

# Create file handler
file_handler = logging.FileHandler("parkwise.log")
file_handler.setFormatter(formatter)

# Configure the root logger
logging.basicConfig(
    level=logging.INFO,
    handlers=[console_handler, file_handler],
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Create loggers
logger = logging.getLogger("parkwise")
logger.setLevel(logging.INFO)

access_logger = logging.getLogger("access")
access_logger.setLevel(logging.INFO)

error_logger = logging.getLogger("error")
error_logger.setLevel(logging.ERROR)

def log_api_call(request: Request, response_status: int, execution_time: float, user_id: str = None):
    """Log API calls with detailed information"""
    access_logger.info(
        f"API_CALL - {request.method} {request.url.path} - "
        f"Status: {response_status} - Time: {execution_time:.3f}s - "
        f"User: {user_id if user_id else 'Anonymous'} - "
        f"IP: {request.client.host if request.client else 'Unknown'}"
    )

def log_error(error: Exception, context: str = "", request: Request = None):
    """Log errors with context"""
    error_logger.error(
        f"ERROR - Context: {context} - "
        f"Error: {str(error)} - "
        f"Type: {type(error).__name__} - "
        f"Request: {request.url.path if request else 'N/A'}"
    )

def log_info(message: str, extra: dict = None):
    """Log general information"""
    if extra:
        message += f" - Extra: {extra}"
    logger.info(message)

def log_warning(message: str, extra: dict = None):
    """Log warnings"""
    if extra:
        message += f" - Extra: {extra}"
    logger.warning(message)