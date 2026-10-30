"""Professional document loading service using LangChain.

This service provides clean, extensible document loading for multiple file types:
- Text files (.txt, .md)
- PDF files (.pdf) 
- Word documents (.docx, .doc)
- Extensible for future formats

Uses LangChain community loaders for production-grade reliability.
"""

import os
from pathlib import Path
from typing import List, Optional
from langchain_community.document_loaders import (
    TextLoader,
    PyPDFLoader,
    Docx2txtLoader,
    UnstructuredMarkdownLoader,
)

class DocumentLoadError(Exception):
    """Custom exception for document loading errors."""
    pass

class ProfessionalDocumentLoader:
    """Professional document loader with LangChain integration."""
    
    # Supported file extensions and their corresponding loaders
    SUPPORTED_FORMATS = {
        # Text files
        '.txt': TextLoader,
        '.md': UnstructuredMarkdownLoader,
        '.markdown': UnstructuredMarkdownLoader,
        
        # PDF files
        '.pdf': PyPDFLoader,
        
        # Word documents
        '.docx': Docx2txtLoader,
        '.doc': Docx2txtLoader,
    }
    
    def __init__(self, encoding: str = 'utf-8'):
        """Initialize document loader with default encoding."""
        self.encoding = encoding
    
    def get_file_extension(self, file_path: str) -> str:
        """Extract and normalize file extension."""
        return Path(file_path).suffix.lower()
    
    def validate_file(self, file_path: str) -> bool:
        """Validate that file exists and is supported."""
        if not os.path.exists(file_path):
            raise DocumentLoadError(f"File not found: {file_path}")
        
        ext = self.get_file_extension(file_path)
        if ext not in self.SUPPORTED_FORMATS:
            raise DocumentLoadError(
                f"Unsupported file type: {ext}. "
                f"Supported formats: {', '.join(self.SUPPORTED_FORMATS.keys())}"
            )
        
        return True
    
    def load_document(self, file_path: str, **loader_kwargs) -> List:
        """
        Load document using appropriate LangChain loader.
        
        Args:
            file_path: Path to the document file
            **loader_kwargs: Additional arguments for specific loaders
            
        Returns:
            List of LangChain Document objects
            
        Raises:
            DocumentLoadError: If loading fails
        """
        try:
            # Validate file
            self.validate_file(file_path)
            
            # Get file extension
            ext = self.get_file_extension(file_path)
            
            # Get appropriate loader class
            loader_class = self.SUPPORTED_FORMATS[ext]
            
            # Configure loader based on file type
            if ext in ['.txt']:
                # Text files need encoding
                loader = loader_class(file_path, encoding=self.encoding, **loader_kwargs)
            elif ext in ['.md', '.markdown']:
                # Markdown files
                loader = loader_class(file_path, **loader_kwargs)
            elif ext == '.pdf':
                # PDF files
                loader = loader_class(file_path, **loader_kwargs)
            elif ext in ['.docx', '.doc']:
                # Word documents
                loader = loader_class(file_path, **loader_kwargs)
            else:
                loader = loader_class(file_path, **loader_kwargs)
            
            # Load the document
            documents = loader.load()
            
            if not documents:
                raise DocumentLoadError(f"No content loaded from: {file_path}")
            
            # Add metadata about the source file
            for doc in documents:
                if not hasattr(doc, 'metadata') or not doc.metadata:
                    doc.metadata = {}
                
                # Add file metadata
                doc.metadata.update({
                    'source_file': os.path.basename(file_path),
                    'source_path': file_path,
                    'file_type': ext,
                    'file_size': os.path.getsize(file_path),
                })
            
            return documents
            
        except Exception as e:
            if isinstance(e, DocumentLoadError):
                raise
            raise DocumentLoadError(f"Failed to load document {file_path}: {str(e)}")
    
    def load_documents_from_directory(self, directory_path: str, **loader_kwargs) -> List:
        """
        Load all supported documents from a directory.
        
        Args:
            directory_path: Path to directory containing documents
            **loader_kwargs: Additional arguments for loaders
            
        Returns:
            List of all loaded documents
        """
        if not os.path.exists(directory_path):
            raise DocumentLoadError(f"Directory not found: {directory_path}")
        
        if not os.path.isdir(directory_path):
            raise DocumentLoadError(f"Path is not a directory: {directory_path}")
        
        all_documents = []
        loaded_files = []
        failed_files = []
        
        # Walk through directory
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                file_path = os.path.join(root, file)
                
                try:
                    documents = self.load_document(file_path, **loader_kwargs)
                    all_documents.extend(documents)
                    loaded_files.append(file_path)
                except DocumentLoadError as e:
                    failed_files.append((file_path, str(e)))
                    continue
        
        return {
            'documents': all_documents,
            'loaded_files': loaded_files,
            'failed_files': failed_files,
            'total_loaded': len(loaded_files),
            'total_failed': len(failed_files)
        }
    
    def get_supported_formats(self) -> List[str]:
        """Return list of supported file formats."""
        return list(self.SUPPORTED_FORMATS.keys())
    
    def is_supported(self, file_path: str) -> bool:
        """Check if file format is supported."""
        return self.get_file_extension(file_path) in self.SUPPORTED_FORMATS


# Global instance for easy access
document_loader = ProfessionalDocumentLoader()


def load_document(file_path: str, **kwargs) -> List:
    """
    Convenience function to load a single document.
    
    Args:
        file_path: Path to the document
        **kwargs: Additional loader arguments
        
    Returns:
        List of LangChain Document objects
    """
    return document_loader.load_document(file_path, **kwargs)


def load_documents_from_directory(directory_path: str, **kwargs) -> dict:
    """
    Convenience function to load all documents from directory.
    
    Args:
        directory_path: Path to directory
        **kwargs: Additional loader arguments
        
    Returns:
        Dictionary with loading results
    """
    return document_loader.load_documents_from_directory(directory_path, **kwargs)
