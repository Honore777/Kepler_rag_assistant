"""Admin-only read endpoints used by the dashboard."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth_deps import require_admin
from app.db.models import User
from app.db.session import get_db

router = APIRouter()


@router.get("/users")
async def list_users(db: AsyncSession = Depends(get_db), _admin=Depends(require_admin)):
    """List all accounts (never includes password hashes)."""
    rows = (await db.execute(select(User).order_by(User.created_at.desc()))).scalars().all()
    return [
        {
            "id": str(u.id),
            "username": u.username,
            "full_name": u.full_name,
            "role": u.role,
            "created_at": u.created_at.isoformat() if u.created_at else None,
        }
        for u in rows
    ]
