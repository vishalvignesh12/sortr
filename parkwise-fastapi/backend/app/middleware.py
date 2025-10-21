import time
from fastapi import Request
from .logging_config import log_api_call, log_error

async def logging_middleware(request: Request, call_next):
    start_time = time.time()
    
    try:
        response = await call_next(request)
        execution_time = time.time() - start_time
        
        # Extract user ID from request if available
        user_id = getattr(request.state, "user_id", None)
        
        log_api_call(request, response.status_code, execution_time, user_id)
        
        return response
        
    except Exception as e:
        execution_time = time.time() - start_time
        log_error(e, "API_CALL_ERROR", request)
        raise