"""
Request tracking middleware for VITA backend
"""
import time
import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from core.logger import logger

class RequestTrackingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to track requests with trace_id and measure duration
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate trace_id
        trace_id = str(uuid.uuid4())
        
        # Add trace_id to request state
        request.state.trace_id = trace_id
        
        # Start timer
        start_time = time.time()
        
        # Log request start
        logger.bind(
            trace_id=trace_id,
            method=request.method,
            path=request.url.path,
            client_host=request.client.host if request.client else None,
        ).info("Request started")
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Add trace_id to response headers
            response.headers["X-Trace-ID"] = trace_id
            
            # Log request completion
            logger.bind(
                trace_id=trace_id,
                status_code=response.status_code,
                duration_ms=round(duration_ms, 2),
            ).info("Request completed")
            
            return response
            
        except Exception as e:
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log error
            logger.bind(
                trace_id=trace_id,
                duration_ms=round(duration_ms, 2),
                error_type=type(e).__name__,
                error_message=str(e),
            ).error(f"Request failed: {e}")
            
            # Re-raise the exception
            raise

class PerformanceMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log slow requests
    """
    
    SLOW_REQUEST_THRESHOLD_MS = 1000  # 1 second
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        response = await call_next(request)
        
        duration_ms = (time.time() - start_time) * 1000
        
        # Log slow requests
        if duration_ms > self.SLOW_REQUEST_THRESHOLD_MS:
            trace_id = getattr(request.state, "trace_id", "unknown")
            logger.bind(
                trace_id=trace_id,
                duration_ms=round(duration_ms, 2),
                method=request.method,
                path=request.url.path,
            ).warning(f"Slow request detected: {duration_ms:.2f}ms")
        
        return response

def setup_middleware(app: ASGIApp):
    """
    Setup all middleware for the application
    
    Args:
        app: FastAPI application instance
    """
    app.add_middleware(RequestTrackingMiddleware)
    app.add_middleware(PerformanceMiddleware) 