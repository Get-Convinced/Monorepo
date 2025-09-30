"""
Simplified Ragie models with only essential data structures.

This module contains only the core models needed for Ragie integration,
removing complex validation and unused structures.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class RagieDocumentStatus(str, Enum):
    """Document processing status in Ragie."""
    PENDING = "pending"
    PARTITIONING = "partitioning"
    PARTITIONED = "partitioned"
    REFINED = "refined"
    CHUNKED = "chunked"
    INDEXED = "indexed"
    SUMMARY_INDEXED = "summary_indexed"
    KEYWORD_INDEXED = "keyword_indexed"
    READY = "ready"
    FAILED = "failed"


class RagieDocument(BaseModel):
    """Ragie document model - core fields only."""
    id: str = Field(..., description="Unique document identifier")
    name: str = Field(..., description="Document filename")
    status: RagieDocumentStatus = Field(..., description="Processing status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Document metadata")


class RagieDocumentList(BaseModel):
    """Paginated list of documents."""
    documents: List[RagieDocument] = Field(..., description="List of documents")
    cursor: Optional[str] = Field(None, description="Pagination cursor for next page")
    has_more: bool = Field(False, description="Whether more documents are available")


class RagieChunk(BaseModel):
    """Document chunk from retrieval."""
    id: str = Field(..., description="Chunk identifier")
    document_id: str = Field(..., description="Parent document ID")
    text: str = Field(..., description="Chunk text content")
    score: float = Field(..., description="Relevance score")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Chunk metadata")


class RagieRetrievalResult(BaseModel):
    """Result from document retrieval query."""
    chunks: List[RagieChunk] = Field(..., description="Retrieved chunks")
    document_ids: List[str] = Field(..., description="Document IDs that matched")
    average_score: float = Field(..., description="Average relevance score")


# Upload progress tracking model
class UploadProgress(BaseModel):
    """Upload progress tracking."""
    upload_id: str = Field(..., description="Unique upload identifier")
    filename: str = Field(..., description="Original filename")
    status: str = Field(..., description="Upload status: uploading, processing, completed, failed")
    upload_progress: int = Field(0, description="File upload progress (0-100)")
    processing_progress: int = Field(0, description="Ragie processing progress (0-100)")
    processing_status: Optional[str] = Field(None, description="Ragie document status")
    document_id: Optional[str] = Field(None, description="Ragie document ID when available")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    stage_description: Optional[str] = Field(None, description="Human-readable stage description")


# Error response model
class RagieErrorResponse(BaseModel):
    """Error response from Ragie API."""
    success: bool = False
    error: Dict[str, Any] = Field(..., description="Error information")
