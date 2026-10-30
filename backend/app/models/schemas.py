from typing import List, Optional
from pydantic import BaseModel


class DocumentCreateResponse(BaseModel):
    id: str
    name: str
    active: bool
    message: Optional[str] = None


class DocumentItem(BaseModel):
    id: str
    name: str
    type: Optional[str] = None
    allowed_roles: Optional[List[str]] = None
    active: bool
    status: Optional[str] = None
    file_size: Optional[int] = None
    created_at: Optional[str] = None
    uploaded_at: Optional[str] = None
    indexing_state: Optional[str] = None
    indexing_message: Optional[str] = None
    indexed_at: Optional[str] = None


class QueryRequest(BaseModel):
    question: str
    top_k: int = 4
    doc_ids: Optional[List[str]] = None
    history: Optional[List[str]] = None


class SourceItem(BaseModel):
    id: str
    metadata: dict
    text: str
    score: Optional[float] = None  # Relevance score (0-1, higher is better)


class QueryResponse(BaseModel):
    answer: str
    sources: List[SourceItem]
    debug: Optional[dict] = None


class StudentBase(BaseModel):
    """Core student fields shared by create/update/response models."""

    student_code: str
    full_name: str
    email: str
    program: Optional[str] = None
    status: str = "active"
    profile_image_url: Optional[str] = None


class StudentCreate(StudentBase):
    """Payload for creating a student record."""


class StudentUpdate(BaseModel):
    """Partial payload for updating a student record."""

    full_name: Optional[str] = None
    email: Optional[str] = None
    program: Optional[str] = None
    status: Optional[str] = None


class StudentItem(StudentBase):
    """Student record returned by API routes."""

    id: str
    created_at: Optional[str] = None
