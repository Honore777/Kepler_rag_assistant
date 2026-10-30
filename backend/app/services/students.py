"""Students service backed by async SQLAlchemy.

Routes call these helpers so DB logic stays out of API modules.
"""

from fastapi import HTTPException
from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Student


def _to_dict(student: Student) -> dict:
    return {
        "id": str(student.id),
        "student_code": student.student_code,
        "full_name": student.full_name,
        "email": student.email,
        "program": student.program,
        "status": student.status,
        "profile_image_url": student.profile_image_url,
        "created_at": student.created_at.isoformat() if student.created_at else None,
    }


async def list_students(db: AsyncSession, limit: int = 200):
    """Return a paginated list of students."""

    result = await db.execute(select(Student).limit(limit).order_by(Student.created_at.desc()))
    rows = result.scalars().all()
    return [_to_dict(r) for r in rows]


async def get_student(db: AsyncSession, student_id: str):
    """Return one student by primary id."""

    result = await db.execute(select(Student).where(Student.id == student_id))
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="student not found")
    return _to_dict(row)


async def create_student(db: AsyncSession, payload: dict):
    """Insert a new student record."""

    row = Student(**payload)
    db.add(row)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="student code/email already exists")
    await db.refresh(row)
    return _to_dict(row)


async def update_student(db: AsyncSession, student_id: str, payload: dict):
    """Update an existing student record by id."""

    if not payload:
        raise HTTPException(status_code=400, detail="no fields provided")

    stmt = update(Student).where(Student.id == student_id).values(**payload).returning(Student)
    try:
        result = await db.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            await db.rollback()
            raise HTTPException(status_code=404, detail="student not found")
        await db.commit()
        return _to_dict(row)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="student code/email already exists")


async def delete_student(db: AsyncSession, student_id: str):
    """Delete a student record by id."""

    stmt = delete(Student).where(Student.id == student_id).returning(Student.id)
    result = await db.execute(stmt)
    deleted = result.scalar_one_or_none()
    if deleted is None:
        await db.rollback()
        raise HTTPException(status_code=404, detail="student not found")
    await db.commit()
    return {"id": str(deleted)}
