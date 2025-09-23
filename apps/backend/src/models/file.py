"""
File API models.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class FileUploadResponse(BaseModel):
    """Response model for file upload."""
    file_id: UUID
    file_name: str
    original_file_name: str
    file_size_bytes: int
    content_type: Optional[str]
    s3_key: str
    s3_bucket: str
    file_hash: Optional[str]
    organization_id: UUID
    user_id: UUID
    created_at: datetime
    message: str


class FileResponse(BaseModel):
    """Response model for file data."""
    id: UUID
    file_name: str
    original_file_name: str
    file_path: str
    s3_key: str
    s3_bucket: str
    file_size_bytes: int
    content_type: Optional[str]
    file_hash: Optional[str]
    file_metadata: Dict[str, Any]
    tags: List[str]
    organization_id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class FileListResponse(BaseModel):
    """Response model for file list."""
    files: List[FileResponse]
    total: int
    limit: int
    offset: int
    organization_id: Optional[UUID] = None
    user_id: Optional[UUID] = None


class FileDownloadRequest(BaseModel):
    """Request model for file download."""
    file_id: UUID = Field(..., description="File ID to download")


class FileDownloadResponse(BaseModel):
    """Response model for file download."""
    file_id: UUID
    file_name: str
    content_type: Optional[str]
    file_size_bytes: int
    download_url: str
    expires_at: datetime


class FileDeleteResponse(BaseModel):
    """Response model for file deletion."""
    file_id: UUID
    file_name: str
    deleted: bool
    message: str


class FileMetadataResponse(BaseModel):
    """Response model for file metadata."""
    file_id: UUID
    file_name: str
    s3_metadata: Dict[str, Any]
    file_hash: Optional[str]
    last_modified: Optional[datetime]
    storage_class: Optional[str]


class FileCopyRequest(BaseModel):
    """Request model for copying a file."""
    target_organization_id: UUID = Field(..., description="Target organization ID")
    target_user_id: UUID = Field(..., description="Target user ID")
    new_filename: Optional[str] = Field(None, description="New filename (optional)")


class FileCopyResponse(BaseModel):
    """Response model for file copy."""
    source_file_id: UUID
    new_file_id: UUID
    new_file_name: str
    new_s3_key: str
    message: str


class FileSearchRequest(BaseModel):
    """Request model for file search."""
    query: Optional[str] = Field(None, description="Search query")
    content_type: Optional[str] = Field(None, description="Filter by content type")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    min_size: Optional[int] = Field(None, description="Minimum file size in bytes")
    max_size: Optional[int] = Field(None, description="Maximum file size in bytes")
    date_from: Optional[datetime] = Field(None, description="Filter files created after this date")
    date_to: Optional[datetime] = Field(None, description="Filter files created before this date")
    limit: int = Field(default=100, ge=1, le=1000, description="Maximum number of results")
    offset: int = Field(default=0, ge=0, description="Number of results to skip")


class FileSearchResponse(BaseModel):
    """Response model for file search."""
    files: List[FileResponse]
    total: int
    query: Optional[str]
    filters_applied: Dict[str, Any]
    limit: int
    offset: int


