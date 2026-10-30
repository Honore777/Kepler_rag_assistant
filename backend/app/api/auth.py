"""Production-style JWT auth endpoints with enhanced security.

Security model:
- users are stored in Postgres (via SQLAlchemy async)
- JWT is issued and persisted in HttpOnly cookie
- admin-only authorization is enforced from token claims
- Input validation and rate limiting for abuse prevention
"""

from typing import Optional
import re

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import create_access_token, get_password_hash, verify_password
from app.core.auth_deps import get_current_user, require_admin
from app.db.models import User
from app.db.session import get_db

# Role-based rate limiting
from app.decorators.rate_limit import rate_limit_student, rate_limit_staff, rate_limit_admin

# IP-based rate limiting for public endpoints
from app.utils.ip_rate_limiter import check_ip_rate_limit

router = APIRouter()


class UserIn(BaseModel):
    username: str
    password: str
    full_name: Optional[str] = None
    role: Optional[str] = None
    registration_code: Optional[str] = None

    @validator('username')
    def validate_username(cls, v):
        if not v or not v.strip():
            raise ValueError('Username cannot be empty')
        if len(v) > 255:
            raise ValueError('Username too long (max 255 chars)')
        # Basic email validation for institutional emails
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v):
            raise ValueError('Invalid email format')
        return v.strip().lower()

    @validator('password')
    def validate_password(cls, v):
        if not v or len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if len(v) > 128:
            raise ValueError('Password too long (max 128 chars)')
        return v

    @validator('full_name')
    def validate_full_name(cls, v):
        if v and len(v) > 255:
            raise ValueError('Full name too long (max 255 chars)')
        return v.strip() if v else v


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict = None


def _set_auth_cookie(response: Response, token: str) -> None:
    """Store JWT in HttpOnly cookie to avoid localStorage XSS exposure."""

    response.set_cookie(
        key=settings.COOKIE_NAME,
        value=token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )


@router.post("/register")
async def register(request: Request, user: UserIn, db: AsyncSession = Depends(get_db)):
    """Register user in DB with IP-based rate limiting and institutional email validation.

    Client-supplied role is ignored to prevent privilege escalation.
    Students must use institutional email domain.
    """
    # 🔥 IP-based rate limiting (5 registrations per minute per IP)
    client_ip = request.client.host if request.client else "unknown"
    allowed, remaining = check_ip_rate_limit(client_ip, "/auth/register", max_requests=5)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail="Too many registration attempts from this IP. Please try again later."
        )

    existing = await db.execute(select(User).where(User.username == user.username))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=400, detail="user exists")

    requested_role = (user.role or "student").lower().strip()
    user_role = "student"

    # Staff/board accounts require invitation code from admin.
    if requested_role in ("staff", "board", "board_member"):
        if not settings.STAFF_REGISTRATION_CODE:
            raise HTTPException(status_code=400, detail="staff registration code is not configured")
        if user.registration_code != settings.STAFF_REGISTRATION_CODE:
            raise HTTPException(status_code=403, detail="invalid registration code")
        user_role = "board_member" if requested_role in ("board", "board_member") else "staff"

    # Students must use institutional email domain.
    if user_role == "student" and not user.username.endswith(f"@{settings.INSTITUTIONAL_DOMAIN}"):
        raise HTTPException(status_code=400, detail=f"student registration requires @{settings.INSTITUTIONAL_DOMAIN} email")

    row = User(
        username=user.username,
        full_name=user.full_name,
        role=user_role,
        password_hash=get_password_hash(user.password),
    )
    db.add(row)
    await db.commit()
    return {
        "status": "ok", 
        "username": user.username,
        "role": user_role,
        "institutional": user_role == "student"
    }


@router.post("/login", response_model=TokenOut)
async def login_json(request: Request, user: UserIn, response: Response, db: AsyncSession = Depends(get_db)):
    """JSON login that also sets secure HttpOnly auth cookie with IP-based rate limiting."""
    # 🔥 IP-based rate limiting (10 login attempts per minute per IP)
    client_ip = request.client.host if request.client else "unknown"
    allowed, remaining = check_ip_rate_limit(client_ip, "/auth/login", max_requests=10)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail="Too many login attempts from this IP. Please try again later."
        )

    result = await db.execute(select(User).where(User.username == user.username))
    record = result.scalar_one_or_none()
    if record is None or not verify_password(user.password, record.password_hash):
        raise HTTPException(status_code=401, detail="invalid credentials")

    token = create_access_token({"sub": record.username, "role": record.role})
    _set_auth_cookie(response, token)
    return TokenOut(
        access_token=token,
        user={
            "username": record.username,
            "full_name": record.full_name,
            "role": record.role
        }
    )


@router.post("/token", response_model=TokenOut)
async def token(request: Request, response: Response, form: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    """OAuth2-compatible endpoint used by docs/testing tools with IP-based rate limiting."""
    # 🔥 IP-based rate limiting (10 token requests per minute per IP)
    client_ip = request.client.host if request.client else "unknown"
    allowed, remaining = check_ip_rate_limit(client_ip, "/auth/token", max_requests=10)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail="Too many token requests from this IP. Please try again later."
        )

    result = await db.execute(select(User).where(User.username == form.username))
    record = result.scalar_one_or_none()
    if record is None or not verify_password(form.password, record.password_hash):
        raise HTTPException(status_code=401, detail="invalid credentials")

    token_value = create_access_token({"sub": record.username, "role": record.role})
    _set_auth_cookie(response, token_value)
    return TokenOut(
        access_token=token_value,
        user={
            "username": record.username,
            "full_name": record.full_name,
            "role": record.role
        }
    )


@router.post("/logout")
async def logout(response: Response):
    """Clear auth cookie from browser."""

    response.delete_cookie(settings.COOKIE_NAME, path="/")
    return {"status": "ok"}


class PasswordChange(BaseModel):
    current_password: str
    new_password: str

    @validator('new_password')
    def validate_new_password(cls, v):
        if not v or len(v) < 8:
            raise ValueError('New password must be at least 8 characters')
        if len(v) > 128:
            raise ValueError('New password too long (max 128 chars)')
        return v


@router.post("/change-password")
async def change_password(request: Request, payload: PasswordChange, db: AsyncSession = Depends(get_db)):
    """Change the authenticated user's password.

    Requires the current password (prevents takeover via a stolen session),
    is IP-rate-limited, and rehashes with the same algorithm as registration.
    Note: JWTs are stateless, so tokens issued before the change stay valid
    until they expire (ACCESS_TOKEN_EXPIRE_MINUTES).
    """
    client_ip = request.client.host if request.client else "unknown"
    allowed, _remaining = check_ip_rate_limit(client_ip, "/auth/change-password", max_requests=5)
    if not allowed:
        raise HTTPException(status_code=429, detail="Too many attempts. Please try again later.")

    user = await get_current_user(request, db)
    result = await db.execute(select(User).where(User.username == user["username"]))
    record = result.scalar_one_or_none()
    if record is None:
        raise HTTPException(status_code=404, detail="user not found")

    if not verify_password(payload.current_password, record.password_hash):
        raise HTTPException(status_code=403, detail="current password is incorrect")

    if verify_password(payload.new_password, record.password_hash):
        raise HTTPException(status_code=400, detail="new password must differ from current password")

    record.password_hash = get_password_hash(payload.new_password)
    await db.commit()
    return {"status": "ok", "message": "Password updated"}


# get_current_user and require_admin moved to app.core.auth_deps to avoid circular imports
