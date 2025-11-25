"""
CORS Override Middleware
Overrides CORS headers for file endpoints to ensure specific origin is used
instead of wildcard when credentials mode is enabled.
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from fastapi import Request
from api.dependencies.logging import logger


class CORSEOverrideMiddleware(BaseHTTPMiddleware):
    """
    Middleware that runs after CORS middleware to override headers
    for file endpoints when credentials mode requires specific origin.
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.file_path_patterns = [
            "/api/v1/files/serve/",
            "/api/v1/files/",
        ]
    
    def _is_file_endpoint(self, path: str) -> bool:
        """Check if the request path is a file endpoint"""
        return any(pattern in path for pattern in self.file_path_patterns)
    
    async def dispatch(self, request: Request, call_next):
        """Override CORS headers for file endpoints"""
        # Only process file endpoints
        if not self._is_file_endpoint(request.url.path):
            response = await call_next(request)
            return response
        
        # Get the origin from request
        origin = request.headers.get("origin")
        
        if origin:
            # For file endpoints with origin header, we need specific origin, not wildcard
            logger.debug(f"[CORS_OVERRIDE] Processing file endpoint: {request.url.path}, origin: {origin}")
            
            # Call the next middleware/route handler
            response = await call_next(request)
            
            # Override CORS headers to use specific origin
            # This ensures credentials mode works correctly
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            
            # Ensure other CORS headers are present
            if "Access-Control-Allow-Methods" not in response.headers:
                response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS, HEAD"
            if "Access-Control-Allow-Headers" not in response.headers:
                response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type, Accept, Origin, X-Requested-With"
            
            logger.debug(f"[CORS_OVERRIDE] Overrode headers - Access-Control-Allow-Origin={origin}, Access-Control-Allow-Credentials=true")
            
            return response
        else:
            # No origin header, let default behavior proceed
            response = await call_next(request)
            return response

