"""Role-based rate limiting decorators for FastAPI endpoints.

Provides decorators that automatically enforce rate limits based on user roles:
- @rate_limit_by_role() - General role-based limiting
- @rate_limit_student() - Student-specific limits
- @rate_limit_staff() - Staff-specific limits  
- @rate_limit_admin() - Admin-specific limits
"""

from functools import wraps
from typing import Callable
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

from app.core.security import decode_access_token
from app.utils.rate_limiter import rate_limiter


def _extract_user_from_request(request: Request):
    """Extract user info from JWT token in cookie or header."""
    token = request.cookies.get("kc_access_token")
    
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.lower().startswith("bearer "):
            token = auth_header.split(" ", 1)[1].strip()
    
    if not token:
        raise HTTPException(status_code=401, detail="No authentication token provided")
    
    payload = decode_access_token(token or "")
    if not payload or not payload.get("sub"):
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return {
        "username": payload["sub"],
        "role": payload.get("role", "student")
    }


def rate_limit_by_role():
    """
    Decorator that applies rate limiting based on authenticated user's role.
    
    Automatically detects user role and applies appropriate limits:
    - Student: 10 requests/minute
    - Staff: 20 requests/minute
    - Admin: 50 requests/minute
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            try:
                # Extract user from JWT token (no DB needed)
                user = _extract_user_from_request(request)
                user_id = user["username"]
                role = user["role"]
                endpoint = request.url.path
                
                # Check rate limit for this user/role
                allowed = await rate_limiter.check_rate_limit(user_id, role, endpoint)
                
                if not allowed:
                    # Get user's specific limit for better error message
                    role_limits = {
                        "student": 10,
                        "staff": 20, 
                        "admin": 50
                    }
                    limit = role_limits.get(role.lower(), 10)
                    
                    return JSONResponse(
                        status_code=429,
                        content={
                            "detail": f"Rate limit exceeded for {role}",
                            "limit_per_minute": limit,
                            "role": role,
                            "retry_after": 60
                        }
                    )
                
                return await func(request, *args, **kwargs)
                
            except HTTPException:
                # Re-raise auth errors
                raise
            except Exception as e:
                # Log rate limiting errors but don't break the endpoint
                print(f"Rate limiting error: {e}")
                return await func(request, *args, **kwargs)
        
        return wrapper
    return decorator


def rate_limit_student(max_requests: int = 10):
    """Decorator for student-specific rate limiting."""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            try:
                user = _extract_user_from_request(request)
                if user["role"] != "student":
                    # Non-students get higher limits
                    max_requests = max_requests * 2
                
                endpoint = request.url.path
                allowed = await rate_limiter.check_rate_limit(
                    user["username"], 
                    user["role"], 
                    endpoint
                )
                
                if not allowed:
                    return JSONResponse(
                        status_code=429,
                        content={
                            "detail": f"Student rate limit exceeded ({max_requests}/minute)",
                            "limit_per_minute": max_requests,
                            "retry_after": 60
                        }
                    )
                
                return await func(request, *args, **kwargs)
                
            except HTTPException:
                raise
            except Exception as e:
                print(f"Student rate limiting error: {e}")
                return await func(request, *args, **kwargs)
        
        return wrapper
    return decorator


def rate_limit_staff(max_requests: int = 20):
    """Decorator for staff-specific rate limiting."""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            try:
                user = _extract_user_from_request(request)
                endpoint = request.url.path
                allowed = await rate_limiter.check_rate_limit(
                    user["username"], 
                    user["role"], 
                    endpoint
                )
                
                if not allowed:
                    return JSONResponse(
                        status_code=429,
                        content={
                            "detail": f"Staff rate limit exceeded ({max_requests}/minute)",
                            "limit_per_minute": max_requests,
                            "retry_after": 60
                        }
                    )
                
                return await func(request, *args, **kwargs)
                
            except HTTPException:
                raise
            except Exception as e:
                print(f"Staff rate limiting error: {e}")
                return await func(request, *args, **kwargs)
        
        return wrapper
    return decorator


def rate_limit_admin(max_requests: int = 50):
    """Decorator for admin-specific rate limiting."""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            try:
                user = _extract_user_from_request(request)
                endpoint = request.url.path
                allowed = await rate_limiter.check_rate_limit(
                    user["username"], 
                    user["role"], 
                    endpoint
                )
                
                if not allowed:
                    return JSONResponse(
                        status_code=429,
                        content={
                            "detail": f"Admin rate limit exceeded ({max_requests}/minute)",
                            "limit_per_minute": max_requests,
                            "retry_after": 60
                        }
                    )
                
                return await func(request, *args, **kwargs)
                
            except HTTPException:
                raise
            except Exception as e:
                print(f"Admin rate limiting error: {e}")
                return await func(request, *args, **kwargs)
        
        return wrapper
    return decorator


def get_rate_limit_stats():
    """Decorator to get current rate limit statistics for user."""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            try:
                user = await get_current_user(request)
                endpoint = request.url.path
                stats = await rate_limiter.get_user_stats(user["username"], endpoint)
                
                # Add stats to request state for endpoint to use
                request.state.rate_limit_stats = stats
                
                return await func(request, *args, **kwargs)
                
            except HTTPException:
                raise
            except Exception as e:
                print(f"Rate limit stats error: {e}")
                request.state.rate_limit_stats = {"error": "Unable to fetch stats"}
                return await func(request, *args, **kwargs)
        
        return wrapper
    return decorator
