"""Authentication dependencies to avoid circular imports.

This module contains shared authentication functions that can be imported
by decorators and other modules without creating circular dependencies.
"""

from typing import Dict, Any
from fastapi import HTTPException, Request, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.db.models import User
from app.db.session import get_db


async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """
    Resolve current user from HttpOnly cookie or Bearer header.
    
    This function is moved here to avoid circular imports with rate limiting decorators.
    """
    
    token = request.cookies.get("kc_access_token")  # Default cookie name
    
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.lower().startswith("bearer "):
            token = auth_header.split(" ", 1)[1].strip()
    
    if not token:
        raise HTTPException(status_code=401, detail="No authentication token provided")
    
    payload = decode_access_token(token or "")
    if not payload or not payload.get("sub"):
        raise HTTPException(status_code=401, detail="Invalid token")
    
    result = await db.execute(select(User).where(User.username == payload["sub"]))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    return {
        "id": str(user.id),
        "username": user.username, 
        "full_name": user.full_name, 
        "role": user.role
    }


async def require_admin(user=Depends(get_current_user)):
    """Dependency to require admin role."""
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user
