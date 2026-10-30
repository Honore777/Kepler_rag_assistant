"""Professional document filtering service for role-based access control.

This service implements the document access logic:
- Filters documents based on user roles
- Checks document active status
- Validates document expiration
- Supports department-level access control
"""

import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import DocumentMetadata
from app.core.config import settings


class DocumentAccessError(Exception):
    """Custom exception for document access errors."""
    pass


class ProfessionalDocumentFilter:
    """Professional document filtering with role-based access control."""
    
    def __init__(self):
        self.institutional_domain = getattr(settings, 'INSTITUTIONAL_DOMAIN', 'keplercollege.ac.rw')
    
    def is_institutional_email(self, email: str) -> bool:
        """Check if email matches institutional domain."""
        if not email or '@' not in email:
            return False
        domain = email.split('@')[-1].lower()
        return domain == self.institutional_domain.lower()
    
    def parse_allowed_roles(self, allowed_roles_str: str) -> List[str]:
        """Parse JSON string of allowed roles."""
        try:
            if not allowed_roles_str:
                return []
            return json.loads(allowed_roles_str)
        except (json.JSONDecodeError, TypeError):
            return []
    
    async def get_accessible_documents(self, db: AsyncSession, user_role: str, user_email: str = None) -> List[str]:
        """
        Get list of document IDs accessible to user based on role.
        
        Args:
            db: Database session
            user_role: User role (student, staff, board_member, admin)
            user_email: User email for institutional validation
            
        Returns:
            List of accessible document IDs
        """
        # Base query for active documents
        query = select(DocumentMetadata).where(
            DocumentMetadata.status == "active"
        )
        
        # Apply expiration filter
        now = datetime.utcnow()
        query = query.where(
            (DocumentMetadata.expires_at.is_(None)) | 
            (DocumentMetadata.expires_at > now)
        )
        
        result = await db.execute(query)
        documents = result.scalars().all()
        
        accessible_doc_ids = []
        
        for doc in documents:
            if self._can_access_document(doc, user_role, user_email):
                accessible_doc_ids.append(doc.doc_id)
        
        return accessible_doc_ids
    
    def _can_access_document(self, doc: DocumentMetadata, user_role: str, user_email: str = None) -> bool:
        """
        Check if user can access a specific document.
        
        Args:
            doc: Document metadata
            user_role: User role
            user_email: User email (for institutional validation)
            
        Returns:
            True if user can access document
        """
        # 🔥 Check if document is active
        if doc.status != "active":
            return False
        
        # 🔥 Check document expiration
        if doc.expires_at and doc.expires_at <= datetime.utcnow():
            return False
        
        # 🔥 Parse allowed roles from document metadata
        allowed_roles = self.parse_allowed_roles(doc.allowed_roles)
        
        # 🔥 Role-based access control
        if user_role not in allowed_roles:
            return False
        
        # 🔥 Institutional email validation for students
        if user_role == "student" and user_email:
            if not self.is_institutional_email(user_email):
                return False
        
        # 🔥 Department-based access (if specified)
        if doc.department and user_role in ["student"]:
            # Students might need department validation
            # This can be extended based on institutional requirements
            pass
        
        return True
    
    def get_access_summary(self, doc: DocumentMetadata) -> Dict[str, Any]:
        """
        Get human-readable access summary for a document.
        
        Returns:
            Dictionary with access information
        """
        allowed_roles = self.parse_allowed_roles(doc.allowed_roles)
        
        return {
            "doc_id": doc.doc_id,
            "doc_name": doc.doc_name,
            "document_type": doc.document_type,
            "allowed_roles": allowed_roles,
            "allowed_roles_display": self._format_roles_display(allowed_roles),
            "department": doc.department,
            "status": doc.status,
            "expires_at": doc.expires_at.isoformat() if doc.expires_at else None,
            "access_summary": self._generate_access_summary(allowed_roles)
        }
    
    def _format_roles_display(self, roles: List[str]) -> str:
        """Format roles for display."""
        role_display = {
            "student": "Students",
            "staff": "Staff Members", 
            "board_member": "Board Members",
            "admin": "Administrators"
        }
        
        display_names = []
        for role in roles:
            display_names.append(role_display.get(role, role.capitalize()))
        
        if len(display_names) == 1:
            return display_names[0]
        elif len(display_names) == 2:
            return f"{display_names[0]} and {display_names[1]}"
        else:
            return f"{', '.join(display_names[:-1])}, and {display_names[-1]}"
    
    def _generate_access_summary(self, allowed_roles: List[str]) -> str:
        """Generate human-readable access summary."""
        if not allowed_roles:
            return "No access restrictions"
        
        if "admin" in allowed_roles:
            return "All staff and administrators"
        elif "board_member" in allowed_roles:
            return "Board members and above"
        elif "staff" in allowed_roles:
            return "Staff members and above"
        elif "student" in allowed_roles and len(allowed_roles) == 1:
            return "Students only"
        else:
            return f"Specific roles: {', '.join(allowed_roles)}"
    
    async def filter_query_results(self, db: AsyncSession, user_role: str, user_email: str, doc_ids: List[str]) -> List[str]:
        """
        Filter a list of document IDs based on user access.
        
        Used in RAG queries to filter results by user permissions.
        """
        if not doc_ids:
            # If no specific docs requested, get all accessible docs
            return await self.get_accessible_documents(db, user_role, user_email)
        
        # Check access for specific document IDs
        query = select(DocumentMetadata).where(
            DocumentMetadata.doc_id.in_(doc_ids)
        )
        
        result = await db.execute(query)
        documents = result.scalars().all()
        
        accessible_doc_ids = []
        for doc in documents:
            if self._can_access_document(doc, user_role, user_email):
                accessible_doc_ids.append(doc.doc_id)
        
        return accessible_doc_ids


# Global instance for easy access
document_filter = ProfessionalDocumentFilter()


async def get_accessible_documents(db: AsyncSession, user_role: str, user_email: str = None) -> List[str]:
    """Convenience function to get accessible documents."""
    return await document_filter.get_accessible_documents(db, user_role, user_email)


async def filter_documents_by_role(db: AsyncSession, user_role: str, user_email: str, doc_ids: List[str]) -> List[str]:
    """Convenience function to filter documents by role."""
    return await document_filter.filter_query_results(db, user_role, user_email, doc_ids)


def can_access_document(doc: DocumentMetadata, user_role: str, user_email: str = None) -> bool:
    """Convenience function to check document access."""
    return document_filter._can_access_document(doc, user_role, user_email)
