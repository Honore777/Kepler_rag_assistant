"""Students API.

These endpoints manage student records in Supabase Postgres.
"""

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth_deps import require_admin
from app.db.session import get_db
from app.models.schemas import StudentCreate, StudentItem, StudentUpdate
from app.services import students as students_service

router = APIRouter()


@router.get("/", response_model=List[StudentItem])
async def list_students(limit: int = 200, _admin=Depends(require_admin), db: AsyncSession = Depends(get_db)):
    """List student records.

    Admin-only because this can contain sensitive institutional data.
    """

    rows = await students_service.list_students(db, limit=limit)
    return [StudentItem(**row) for row in rows]


@router.get("/{student_id}", response_model=StudentItem)
async def get_student(student_id: str, _admin=Depends(require_admin), db: AsyncSession = Depends(get_db)):
    """Fetch one student by id."""

    return StudentItem(**(await students_service.get_student(db, student_id)))


@router.post("/", response_model=StudentItem)
async def create_student(payload: StudentCreate, _admin=Depends(require_admin), db: AsyncSession = Depends(get_db)):
    """Create a new student entry in Supabase."""

    row = await students_service.create_student(db, payload.model_dump())
    return StudentItem(**row)


@router.patch("/{student_id}", response_model=StudentItem)
async def update_student(
    student_id: str,
    payload: StudentUpdate,
    _admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Partially update an existing student."""

    row = await students_service.update_student(db, student_id, payload.model_dump(exclude_none=True))
    return StudentItem(**row)


@router.delete("/{student_id}")
async def delete_student(student_id: str, _admin=Depends(require_admin), db: AsyncSession = Depends(get_db)):
    """Delete a student and return a minimal status payload."""

    await students_service.delete_student(db, student_id)
    return {"status": "ok", "id": student_id}
