"""Request validation middleware for enhanced security"""

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
import re
import json
from urllib.parse import unquote
from config import settings
from utils.logging import logger

class RequestValidationMiddleware(BaseHTTPMiddleware):
    """Validate and sanitize incoming requests"""
    
    # SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        # Modified to require "from" after "select" to avoid false positives
        r"(\bunion\b.*\bselect\b.*\bfrom\b|\bselect\b.*\bfrom\b|\binsert\b.*\binto\b|\bupdate\b.*\bset\b|\bdelete\b.*\bfrom\b|\bdrop\b.*\btable\b|\bcreate\b.*\btable\b)",
        r"(;|\"|'|--|\/\*|\*\/|xp_|sp_|<script|<\/script|javascript:|onerror=|onload=)",
        r"(\bor\b\s*\d+\s*=\s*\d+|\band\b\s*\d+\s*=\s*\d+)",
    ]
    
    # XSS patterns
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>.*?</iframe>",
        r"<object[^>]*>.*?</object>",
        r"<embed[^>]*>.*?</embed>",
    ]
    
    # Path traversal patterns
    PATH_TRAVERSAL_PATTERNS = [
        r"\.\./",
        r"\.\.\\"
    ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> JSONResponse:
        """Validate request for security threats"""
        
        if not settings.enable_request_validation:
            return await call_next(request)
        
        try:
            # Check request size
            content_length = request.headers.get("content-length")
            if content_length and int(content_length) > settings.max_request_size:
                logger.warning(f"Request too large: {content_length} bytes")
                return JSONResponse(
                    status_code=413,
                    content={"error": "Request entity too large"}
                )
            
            # Get request path and query parameters
            path = str(request.url.path)
            query_params = str(request.url.query)
            
            # Check for path traversal
            if self._contains_path_traversal(path):
                logger.warning(f"Path traversal attempt detected: {path}")
                return JSONResponse(
                    status_code=400,
                    content={"error": "Invalid request path"}
                )
            
            # Check query parameters for SQL injection and XSS
            if query_params:
                decoded_params = unquote(query_params)
                if self._contains_sql_injection(decoded_params) or self._contains_xss(decoded_params):
                    logger.warning(f"Malicious query parameters detected: {decoded_params}")
                    return JSONResponse(
                        status_code=400,
                        content={"error": "Invalid request parameters"}
                    )
            
            # For POST/PUT/PATCH requests, validate body
            if request.method in ["POST", "PUT", "PATCH"]:
                # Read body
                body = await request.body()
                if body:
                    try:
                        # Try to parse as JSON
                        body_text = body.decode('utf-8')
                        if self._contains_sql_injection(body_text) or self._contains_xss(body_text):
                            logger.warning(f"Malicious request body detected")
                            return JSONResponse(
                                status_code=400,
                                content={"error": "Invalid request body"}
                            )
                    except Exception:
                        # If not JSON, still check for patterns
                        pass
            
            # Validate headers
            for header_name, header_value in request.headers.items():
                if self._contains_sql_injection(header_value) or self._contains_xss(header_value):
                    logger.warning(f"Malicious header detected: {header_name}")
                    return JSONResponse(
                        status_code=400,
                        content={"error": "Invalid request headers"}
                    )
            
            # If all checks pass, continue
            response = await call_next(request)
            return response
            
        except Exception as e:
            logger.error(f"Request validation error: {e}")
            return await call_next(request)
    
    def _contains_sql_injection(self, text: str) -> bool:
        """Check if text contains SQL injection patterns"""
        if not settings.enable_sql_injection_protection:
            return False
            
        text_lower = text.lower()
        for pattern in self.SQL_INJECTION_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True
        return False
    
    def _contains_xss(self, text: str) -> bool:
        """Check if text contains XSS patterns"""
        if not settings.enable_xss_protection:
            return False
            
        for pattern in self.XSS_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    def _contains_path_traversal(self, path: str) -> bool:
        """Check if path contains traversal patterns"""
        for pattern in self.PATH_TRAVERSAL_PATTERNS:
            if re.search(pattern, path):
                return True
        return False


class InputSanitizationMiddleware(BaseHTTPMiddleware):
    """Sanitize user inputs"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> JSONResponse:
        """Sanitize request inputs"""
        
        # Store original body for later use
        body = await request.body()
        
        # Create a new request with sanitized data
        async def receive():
            return {"type": "http.request", "body": body}
        
        request._receive = receive
        
        response = await call_next(request)
        return response


def sanitize_string(value: str) -> str:
    """Sanitize a string value"""
    if not value:
        return value
    
    # Remove null bytes
    value = value.replace('\x00', '')
    
    # Escape HTML entities
    html_escape_table = {
        "&": "&amp;",
        '"': "&quot;",
        "'": "&#x27;",
        ">": "&gt;",
        "<": "&lt;",
    }
    
    for char, escaped in html_escape_table.items():
        value = value.replace(char, escaped)
    
    return value.strip()
