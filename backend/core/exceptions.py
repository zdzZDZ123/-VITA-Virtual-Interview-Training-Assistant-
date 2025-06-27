"""
Custom exceptions and error handlers for VITA backend
"""
from typing import Optional, Dict, Any
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import BaseModel
from core.logger import logger


class ErrorResponse(BaseModel):
    """Standard error response model"""
    error: str
    message: str
    trace_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class VITAException(Exception):
    """Base exception for all VITA custom exceptions"""
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: str = "INTERNAL_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details
        super().__init__(message)


class ValidationException(VITAException):
    """Raised when input validation fails"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="VALIDATION_ERROR",
            details=details
        )


class AuthenticationException(VITAException):
    """Raised when authentication fails"""
    def __init__(self, message: str = "Authentication required"):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="AUTH_ERROR"
        )


class AuthorizationException(VITAException):
    """Raised when authorization fails"""
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="PERMISSION_ERROR"
        )


class NotFoundException(VITAException):
    """Raised when a resource is not found"""
    def __init__(self, resource: str, identifier: Any):
        super().__init__(
            message=f"{resource} not found",
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="NOT_FOUND",
            details={"resource": resource, "identifier": str(identifier)}
        )


class ExternalServiceException(VITAException):
    """Raised when an external service fails"""
    def __init__(self, service: str, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"External service error: {message}",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_code="EXTERNAL_SERVICE_ERROR",
            details={"service": service, **(details or {})}
        )


class RateLimitException(VITAException):
    """Raised when rate limit is exceeded"""
    def __init__(self, limit: int, window: str):
        super().__init__(
            message="Rate limit exceeded",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            error_code="RATE_LIMIT_EXCEEDED",
            details={"limit": limit, "window": window}
        )


class APIError(VITAException):
    """Raised when an API call fails"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_502_BAD_GATEWAY,
            error_code="API_ERROR",
            details=details
        )


class ConfigurationError(VITAException):
    """Raised when configuration is invalid"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="CONFIG_ERROR",
            details=details
        )


class ServiceUnavailableError(VITAException):
    """Raised when a service is unavailable"""
    def __init__(self, service: str, message: str = "Service temporarily unavailable"):
        super().__init__(
            message=f"{service}: {message}",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_code="SERVICE_UNAVAILABLE",
            details={"service": service}
        )


async def vita_exception_handler(request: Request, exc: VITAException) -> JSONResponse:
    """Handler for VITA custom exceptions"""
    trace_id = getattr(request.state, "trace_id", None)
    
    logger.bind(
        trace_id=trace_id,
        error_code=exc.error_code,
        status_code=exc.status_code,
        details=exc.details
    ).error(f"VITA exception: {exc.message}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.error_code,
            message=exc.message,
            trace_id=trace_id,
            details=exc.details
        ).dict(exclude_none=True)
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handler for HTTP exceptions"""
    trace_id = getattr(request.state, "trace_id", None)
    
    logger.bind(
        trace_id=trace_id,
        status_code=exc.status_code,
        detail=exc.detail
    ).error(f"HTTP exception: {exc.detail}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error="HTTP_ERROR",
            message=str(exc.detail),
            trace_id=trace_id
        ).dict(exclude_none=True)
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handler for validation exceptions"""
    trace_id = getattr(request.state, "trace_id", None)
    
    logger.bind(
        trace_id=trace_id,
        errors=exc.errors()
    ).error("Validation error")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            error="VALIDATION_ERROR",
            message="Invalid request data",
            trace_id=trace_id,
            details={"errors": exc.errors()}
        ).dict(exclude_none=True)
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handler for all unhandled exceptions"""
    trace_id = getattr(request.state, "trace_id", None)
    
    logger.bind(
        trace_id=trace_id,
        exception_type=type(exc).__name__,
        exception_message=str(exc)
    ).exception("Unhandled exception")
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="INTERNAL_ERROR",
            message="An unexpected error occurred",
            trace_id=trace_id
        ).dict(exclude_none=True)
    )


def setup_exception_handlers(app):
    """Setup all exception handlers for the application"""
    from fastapi import FastAPI
    
    app.add_exception_handler(VITAException, vita_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler) 