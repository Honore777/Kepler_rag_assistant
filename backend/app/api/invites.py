"""Professional invite system for staff and board members.

This module implements secure invite tokens for institutional roles:
- Admin can generate invite tokens with specific roles
- Staff/board_members can register using invite tokens
- Tokens are single-use and expire
- Institutional email validation for students
- Role-based access control
"""

import uuid
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import get_password_hash
from app.core.auth_deps import require_admin
from app.db.models import InviteToken, User
from app.db.session import get_db

router = APIRouter()


class InviteRequest(BaseModel):
    """Request to generate an invite token."""
    email: str
    role: str  # staff or board_member
    expires_hours: int = 24  # Default 24 hours

    @validator('role')
    def validate_role(cls, v):
        if v not in ['staff', 'board_member']:
            raise ValueError('Role must be staff or board_member')
        return v

    @validator('email')
    def validate_email(cls, v):
        if not v or '@' not in v:
            raise ValueError('Valid email required')
        return v.strip().lower()


class RegisterWithInviteRequest(BaseModel):
    """Registration using invite token."""
    invite_token: str
    username: str
    password: str
    full_name: Optional[str] = None

    @validator('username')
    def validate_username(cls, v):
        if not v or not v.strip():
            raise ValueError('Username cannot be empty')
        if len(v) > 255:
            raise ValueError('Username too long (max 255 chars)')
        return v.strip().lower()

    @validator('password')
    def validate_password(cls, v):
        if not v or len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if len(v) > 128:
            raise ValueError('Password too long (max 128 chars)')
        return v


class InviteResponse(BaseModel):
    """Response with invite token and details."""
    token: str
    invite_url: str
    role: str
    expires_at: str
    allowed_roles: list


def generate_invite_token() -> str:
    """Generate secure invite token."""
    return secrets.token_urlsafe(32)


def _aware(dt) -> datetime:
    """Normalize a stored datetime to timezone-aware UTC for comparison."""
    if dt is None:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


async def _get_valid_invite(db: AsyncSession, token: str) -> InviteToken:
    """Fetch an invite token and enforce single-use + expiry."""
    invite = (
        await db.execute(select(InviteToken).where(InviteToken.token == token))
    ).scalar_one_or_none()

    if invite is None:
        raise HTTPException(status_code=400, detail="Invalid invite token")
    if invite.used_at is not None:
        raise HTTPException(status_code=400, detail="Invite token already used")
    if _aware(invite.expires_at) <= datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Invite token expired")
    return invite


@router.post("/generate")
async def generate_invite(
    request: InviteRequest,
    admin_user=Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate invite token for staff or board member registration.

    Admin can specify:
    - Target email
    - Role (staff or board_member)
    - Expiration time
    """
    token = generate_invite_token()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=request.expires_hours)

    try:
        created_by = uuid.UUID(str(admin_user["id"])) if admin_user.get("id") else None
    except (TypeError, ValueError):
        created_by = None

    invite = InviteToken(
        token=token,
        email=request.email,
        role=request.role,
        expires_at=expires_at,
        created_by=created_by,
    )
    db.add(invite)
    await db.commit()

    invite_url = f"{settings.FRONTEND_URL.rstrip('/')}/auth/register?token={token}"

    return InviteResponse(
        token=token,
        invite_url=invite_url,
        role=request.role,
        expires_at=expires_at.isoformat(),
        allowed_roles=["staff", "board_member"]
    )


@router.post("/register-with-invite")
async def register_with_invite(
    request: RegisterWithInviteRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user using an invite token.

    The token determines the role (staff or board_member) and the email it was
    issued for. Tokens are single-use and expire.
    """
    invite = await _get_valid_invite(db, request.invite_token)

    # The invite was issued for a specific email — the registrant must use it.
    if request.username != invite.email:
        raise HTTPException(
            status_code=400,
            detail="This invite was issued for a different email address"
        )

    existing = await db.execute(select(User).where(User.username == request.username))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=400, detail="User already exists")

    user = User(
        username=request.username,
        full_name=request.full_name,
        role=invite.role,  # Role comes from the token, never from the client
        password_hash=get_password_hash(request.password),
    )
    db.add(user)

    # Single-use: burn the token atomically with the registration.
    invite.used_at = datetime.now(timezone.utc)
    await db.commit()

    return {
        "status": "ok",
        "username": request.username,
        "role": invite.role,
        "message": f"Registered successfully as {invite.role}"
    }


@router.get("/validate-token/{token}")
async def validate_invite_token(token: str, db: AsyncSession = Depends(get_db)):
    """
    Validate an invite token and return its details.

    Useful for frontend to show registration form with pre-filled info.
    """
    invite = (
        await db.execute(select(InviteToken).where(InviteToken.token == token))
    ).scalar_one_or_none()

    if invite is None:
        return {"valid": False, "reason": "not_found"}

    used = invite.used_at is not None
    expired = _aware(invite.expires_at) <= datetime.now(timezone.utc)

    return {
        "valid": not used and not expired,
        "reason": "used" if used else ("expired" if expired else None),
        "email": invite.email,
        "role": invite.role,
        "expires_at": _aware(invite.expires_at).isoformat(),
    }


@router.get("/my-invites")
async def get_my_invites(
    admin_user=Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get invites generated by current admin."""
    try:
        admin_id = uuid.UUID(str(admin_user["id"]))
    except (TypeError, ValueError):
        admin_id = None

    stmt = select(InviteToken).order_by(InviteToken.created_at.desc())
    if admin_id is not None:
        stmt = stmt.where(InviteToken.created_by == admin_id)

    invites = (await db.execute(stmt)).scalars().all()

    return {
        "invites": [
            {
                "email": i.email,
                "role": i.role,
                "expires_at": _aware(i.expires_at).isoformat(),
                "used": i.used_at is not None,
                "created_at": _aware(i.created_at).isoformat() if i.created_at else None,
            }
            for i in invites
        ]
    }
