from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from app.db.redis_client import redis_client
from starlette.middleware.base import BaseHTTPMiddleware

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        ip_add = request.headers.get("X-Forwarded-For") or request.client.host
        
        key = f"rate_limit:{ip_add}"        
        current_requests = redis_client.incr(key)
        
        if current_requests == 1:
            redis_client.expire(key, 60)
            
        if current_requests > 100:
            return JSONResponse(status_code=429,content={"detail": "Too many requests. Please try again later."})
                    
        response = await call_next(request)
        return response