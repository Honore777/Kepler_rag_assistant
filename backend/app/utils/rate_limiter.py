"""Role-based rate limiting using local Redis for phase 1 deployment.

This provides user-based rate limiting with different limits per role:
- Student: 10 requests/minute
- Staff: 20 requests/minute  
- Admin: 50 requests/minute

Uses sliding window algorithm with Redis for distributed compatibility.
"""

import asyncio
import time
from typing import Dict, Optional
import redis.asyncio as redis
from fastapi import HTTPException, Request

from app.core.config import settings


class RoleBasedRateLimiter:
    """Professional rate limiting with role-based limits and Redis backend."""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self._redis_warned = False
        self.role_limits = {
            "student": settings.RATE_LIMIT_STUDENT,
            "staff": settings.RATE_LIMIT_STAFF,
            "admin": settings.RATE_LIMIT_ADMIN
        }
        self._redis_lock = asyncio.Lock()
    
    async def _get_redis_client(self) -> redis.Redis:
        """Lazy initialization of Redis client with connection pooling."""
        if self.redis_client is None:
            async with self._redis_lock:
                if self.redis_client is None:
                    # Local Redis connection for phase 1
                    self.redis_client = redis.from_url(
                        settings.REDIS_URL,
                        password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
                        encoding="utf-8",
                        decode_responses=True,
                        max_connections=20  # Connection pool
                    )
                    # Test connection
                    await self.redis_client.ping()
        return self.redis_client
    
    def _get_limit_key(self, user_id: str, endpoint: str) -> str:
        """Generate unique key for rate limiting per user and endpoint."""
        timestamp = int(time.time() // 60)  # 1-minute window
        return f"rate_limit:{user_id}:{endpoint}:{timestamp}"
    
    async def check_rate_limit(self, user_id: str, role: str, endpoint: str) -> bool:
        """
        Check if user has exceeded their role-based rate limit.
        
        Args:
            user_id: Unique user identifier (username)
            role: User role (student, staff, admin)
            endpoint: API endpoint being accessed
            
        Returns:
            True if request is allowed, False if limit exceeded
        """
        try:
            client = await self._get_redis_client()
            max_requests = self.role_limits.get(role.lower(), settings.RATE_LIMIT_STUDENT)
            
            # Use sliding window with current minute key
            key = self._get_limit_key(user_id, endpoint)
            
            # Increment counter atomically
            current_count = await client.incr(key)
            
            # Set expiration on first access (1 minute)
            if current_count == 1:
                await client.expire(key, 60)
            
            return current_count <= max_requests
            
        except redis.ConnectionError:
            # If Redis is down, allow request (fail-open)
            # Log this for monitoring
            if not self._redis_warned:
                self._redis_warned = True
                print("Redis connection failed (rate limiting disabled). Start Redis or set REDIS_URL.")
            return True
        except Exception as e:
            print(f"Rate limiting error: {e}")
            return True  # Fail-open for reliability
    
    async def get_user_stats(self, user_id: str, endpoint: str) -> Dict:
        """Get current rate limit statistics for a user."""
        try:
            client = await self._get_redis_client()
            key = self._get_limit_key(user_id, endpoint)
            current = await client.get(key) or 0
            ttl = await client.ttl(key)
            
            return {
                "current_requests": int(current),
                "time_to_reset": max(0, ttl),
                "limit_per_minute": self.role_limits.get("student", 10)  # Default
            }
        except Exception:
            return {"error": "Unable to fetch stats"}
    
    async def cleanup_expired_keys(self):
        """Cleanup expired rate limit keys (maintenance task)."""
        try:
            client = await self._get_redis_client()
            # Redis automatically expires keys, but we can clean up patterns
            pattern = "rate_limit:*:*:*"
            keys = await client.keys(pattern)
            if keys:
                # Check TTL and remove expired keys
                for key in keys:
                    ttl = await client.ttl(key)
                    if ttl == -1:  # No expiration set
                        await client.expire(key, 60)
        except Exception as e:
            print(f"Cleanup error: {e}")


# Global limiter instance
rate_limiter = RoleBasedRateLimiter()
