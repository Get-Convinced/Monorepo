"""
Simplified Ragie API endpoints for document management and retrieval.

This module provides FastAPI endpoints with simplified error handling
using direct exceptions instead of Result wrappers.
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, Request, BackgroundTasks
from fastapi.responses import Response
from pydantic import BaseModel, Field

from ..services.ragie_service import (
    RagieService, RagieServiceError, UnsupportedFileTypeError, FileTooLargeError
)
from ..services.s3_service import get_s3_service, S3ServiceError
from ..adapters.ragie_client import RagieClient, RagieError, RagieNotFoundError, RagieValidationError
from ..services.redis_service import redis_service, get_ragie_progress_percentage, get_stage_description
from ..auth import require_auth, get_organization_id
from ..models.ragie import UploadProgress
import os

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ragie", tags=["ragie"])


# Simplified Request/Response Models
class DocumentUploadResponse(BaseModel):
    """Response model for document upload."""
    upload_id: str
    filename: str
    status: str
    message: str


class DocumentListResponse(BaseModel):
    """Response model for document listing."""
    documents: List[Dict[str, Any]]
    cursor: Optional[str] = None
    has_more: bool = False


class QueryRequest(BaseModel):
    """Request model for chunk retrieval."""
    query: str = Field(..., description="Search query")
    max_chunks: Optional[int] = Field(10, description="Maximum chunks to return")
    document_ids: Optional[List[str]] = Field(None, description="Filter by document IDs")
    metadata_filter: Optional[Dict[str, Any]] = Field(None, description="Metadata filters")


class MetadataUpdateRequest(BaseModel):
    """Request model for metadata updates."""
    metadata: Dict[str, Any] = Field(..., description="Updated metadata")


# Dependency to get Ragie service
def get_ragie_service() -> RagieService:
    """Get configured Ragie service instance with S3 support."""
    api_key = os.getenv("RAGIE_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="Ragie API key not configured"
        )
    
    ragie_client = RagieClient(api_key=api_key)
    
    # Try to initialize S3 service for URL-based uploads
    try:
        ragie_s3_service = get_s3_service()
        logger.info("✅ S3 service initialized - using S3+URL upload method")
        return RagieService(ragie_client=ragie_client, ragie_s3_service=ragie_s3_service)
    except Exception as e:
        logger.warning(f"⚠️ S3 service initialization failed, falling back to direct upload: {e}")
        return RagieService(ragie_client=ragie_client)


async def upload_document_background(
    upload_id: str,
    file_content: bytes,
    filename: str,
    organization_id: str,
    user_id: str,
    metadata: Optional[Dict[str, Any]],
    ragie_service: RagieService
):
    """Background task for document upload with progress tracking."""
    try:
        # Update progress: starting upload process
        await redis_service.set_upload_progress(upload_id, UploadProgress(
            upload_id=upload_id,
            filename=filename,
            status="uploading",
            upload_progress=5,
            processing_progress=0,
            stage_description="Starting upload process..."
        ))
        
        # Upload to Ragie - simplified, no Result wrapper
        logger.info(f"🚀 Starting Ragie upload for {filename}", extra={
            "upload_id": upload_id,
            "file_name": filename,
            "file_size": len(file_content),
            "organization_id": organization_id,
            "user_id": user_id,
            "metadata": metadata
        })
        
        document = await ragie_service.upload_document(
            file_content=file_content,
            filename=filename,
            organization_id=organization_id,
            user_id=user_id,
            metadata=metadata,
            upload_id=upload_id
        )
        
        logger.info(f"✅ Upload successful for {filename}", extra={
            "upload_id": upload_id,
            "document_id": document.id,
            "document_status": document.status,
            "document_name": document.name,
            "document_size": getattr(document, 'size', 'unknown'),
            "created_at": document.created_at.isoformat() if hasattr(document, 'created_at') else 'unknown'
        })
        
        # Progress is now handled by the S3 service, no need to update here
        
    except (UnsupportedFileTypeError, FileTooLargeError, RagieValidationError, S3ServiceError) as e:
        # Client errors - user's fault
        logger.warning(f"❌ Upload validation failed for {filename}: {e}", extra={
            "upload_id": upload_id,
            "file_name": filename,
            "error_type": type(e).__name__,
            "error_message": str(e),
            "organization_id": organization_id,
            "user_id": user_id
        })
        await redis_service.set_upload_progress(upload_id, UploadProgress(
            upload_id=upload_id,
            filename=filename,
            status="failed",
            upload_progress=100,
            processing_progress=0,
            error_message=str(e),
            stage_description="Upload failed - invalid file"
        ))
        
    except Exception as e:
        # Unexpected errors
        logger.error(f"💥 Background upload failed for {filename}: {e}", extra={
            "upload_id": upload_id,
            "file_name": filename,
            "error_type": type(e).__name__,
            "error_message": str(e),
            "organization_id": organization_id,
            "user_id": user_id
        })
        await redis_service.set_upload_progress(upload_id, UploadProgress(
            upload_id=upload_id,
            filename=filename,
            status="failed",
            upload_progress=100,
            processing_progress=0,
            error_message=str(e),
            stage_description="Upload failed"
        ))


@router.post(
    "/documents/upload",
    response_model=DocumentUploadResponse,
    status_code=202,
    summary="Upload Document (Simplified)",
    description="Simplified document upload with progress tracking"
)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Document file to upload"),
    metadata: Optional[str] = Form(None, description="JSON metadata for the document"),
    user_id: str = Depends(require_auth),
    organization_id: str = Depends(get_organization_id),
    ragie_service: RagieService = Depends(get_ragie_service)
) -> DocumentUploadResponse:
    """Upload a document to Ragie with simplified error handling."""
    
    logger.info(f"📤 Upload request received", extra={
        "file_name": file.filename,
        "content_type": file.content_type,
        "user_id": user_id,
        "organization_id": organization_id,
        "has_metadata": bool(metadata)
    })
    
    # Simple validation
    if not file.filename:
        logger.error("❌ Upload rejected - no filename provided")
        raise HTTPException(status_code=422, detail="File must have a filename")
    
    # Parse metadata if provided
    parsed_metadata = None
    if metadata:
        try:
            parsed_metadata = json.loads(metadata)
            logger.info(f"📋 Metadata parsed successfully", extra={
                "metadata_keys": list(parsed_metadata.keys()) if isinstance(parsed_metadata, dict) else "non-dict",
                "metadata_size": len(str(parsed_metadata))
            })
        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid metadata JSON: {e}", extra={
                "metadata_raw": metadata[:200] + "..." if len(metadata) > 200 else metadata
            })
            raise HTTPException(status_code=422, detail="Invalid JSON in metadata field")
    
    # Generate upload ID
    upload_id = str(uuid.uuid4())
    
    # Initialize progress tracking
    await redis_service.set_upload_progress(upload_id, UploadProgress(
        upload_id=upload_id,
        filename=file.filename,
        status="uploading",
        upload_progress=0,
        processing_progress=0,
        stage_description="Receiving file..."
    ))
    
    # Read file content
    file_content = await file.read()
    
    logger.info(f"📁 File content read successfully", extra={
        "upload_id": upload_id,
        "file_name": file.filename,
        "file_size_bytes": len(file_content),
        "file_size_mb": round(len(file_content) / (1024 * 1024), 2)
    })
    
    # Update progress: file received
    await redis_service.set_upload_progress(upload_id, UploadProgress(
        upload_id=upload_id,
        filename=file.filename,
        status="uploading",
        upload_progress=25,
        processing_progress=0,
        stage_description="File received, preparing upload..."
    ))
    
    # Start background upload task
    background_tasks.add_task(
        upload_document_background,
        upload_id=upload_id,
        file_content=file_content,
        filename=file.filename,
        organization_id=organization_id,
        user_id=user_id,
        metadata=parsed_metadata,
        ragie_service=ragie_service
    )
    
    logger.info("Document upload started", extra={
        "upload_id": upload_id,
        "file_name": file.filename,
        "organization_id": organization_id,
        "user_id": user_id
    })
    
    return DocumentUploadResponse(
        upload_id=upload_id,
        filename=file.filename,
        status="uploading",
        message="Upload started. Use the upload_id to track progress."
    )


@router.get(
    "/upload-progress/{upload_id}",
    summary="Get Upload Progress (Simplified)",
    description="Get the current progress of a document upload"
)
async def get_upload_progress(
    upload_id: str,
    user_id: str = Depends(require_auth),
    organization_id: str = Depends(get_organization_id),
    ragie_service: RagieService = Depends(get_ragie_service)
) -> Dict[str, Any]:
    """Get upload progress with simplified error handling."""
    
    logger.info(f"📊 Progress check requested", extra={
        "upload_id": upload_id,
        "user_id": user_id,
        "organization_id": organization_id
    })
    
    # Get progress from Redis
    progress = await redis_service.get_upload_progress(upload_id)
    
    if not progress:
        logger.warning(f"❌ Progress not found for upload_id: {upload_id}")
        raise HTTPException(status_code=404, detail="Upload not found or expired")
    
    logger.info(f"📊 Current progress status", extra={
        "upload_id": upload_id,
        "status": progress.status,
        "upload_progress": progress.upload_progress,
        "processing_progress": progress.processing_progress,
        "document_id": progress.document_id,
        "error_message": progress.error_message
    })
    
    # If upload is complete and we have a document ID, get latest Ragie status
    if progress.document_id and progress.status == "processing":
        try:
            logger.info(f"🔄 Checking latest Ragie status for document: {progress.document_id}")
            document = await ragie_service.get_document(
                document_id=progress.document_id,
                organization_id=organization_id
            )
            
            logger.info(f"📄 Latest Ragie document status", extra={
                "document_id": progress.document_id,
                "ragie_status": document.status,
                "document_name": document.name,
                "updated_at": document.updated_at.isoformat() if hasattr(document, 'updated_at') else 'unknown'
            })
            
            # Update progress with latest Ragie status
            updated_progress = UploadProgress(
                upload_id=progress.upload_id,
                filename=progress.filename,
                status="completed" if document.status == "ready" else "processing",
                upload_progress=100,
                processing_progress=get_ragie_progress_percentage(document.status),
                processing_status=document.status,
                document_id=progress.document_id,
                stage_description=get_stage_description(document.status)
            )
            
            # Update Redis with latest status
            await redis_service.set_upload_progress(upload_id, updated_progress)
            progress = updated_progress
            
        except RagieNotFoundError:
            # Document was deleted or doesn't exist
            logger.warning(f"❌ Document not found in Ragie: {progress.document_id}")
            pass
        except Exception as e:
            logger.warning(f"⚠️ Failed to get latest document status: {e}", extra={
                "document_id": progress.document_id,
                "error_type": type(e).__name__
            })
    
    return {"success": True, "data": progress.dict()}


@router.get(
    "/documents",
    response_model=DocumentListResponse,
    summary="List Documents (Simplified)",
    description="List documents with simplified error handling"
)
async def list_documents(
    limit: int = Query(20, ge=1, le=100, description="Number of documents to return"),
    cursor: Optional[str] = Query(None, description="Pagination cursor"),
    user_id: str = Depends(require_auth),
    organization_id: str = Depends(get_organization_id),
    ragie_service: RagieService = Depends(get_ragie_service)
) -> DocumentListResponse:
    """List documents with simplified error handling."""
    
    logger.info(f"📋 list_documents called - user_id: {user_id}, org_id: {organization_id}, limit: {limit}")
    
    try:
        document_list = await ragie_service.list_documents(
            organization_id=organization_id,
            limit=limit,
            cursor=cursor
        )
        
        # Convert documents to dict for response
        documents_dict = []
        for doc in document_list.documents:
            doc_dict = doc.dict()
            doc_dict["created_at"] = doc.created_at.isoformat()
            doc_dict["updated_at"] = doc.updated_at.isoformat()
            documents_dict.append(doc_dict)
        
        return DocumentListResponse(
            documents=documents_dict,
            cursor=document_list.cursor,
            has_more=document_list.has_more
        )
        
    except RagieError as e:
        logger.error(f"Failed to list documents: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/documents/{document_id}",
    summary="Get Document (Simplified)",
    description="Get a specific document with simplified error handling"
)
async def get_document(
    document_id: str,
    user_id: str = Depends(require_auth),
    organization_id: str = Depends(get_organization_id),
    ragie_service: RagieService = Depends(get_ragie_service)
) -> Dict[str, Any]:
    """Get a specific document with simplified error handling."""
    
    try:
        document = await ragie_service.get_document(
            document_id=document_id,
            organization_id=organization_id
        )
        
        # Convert document to dict for response
        document_dict = document.dict()
        document_dict["created_at"] = document.created_at.isoformat()
        document_dict["updated_at"] = document.updated_at.isoformat()
        
        return {"success": True, "data": document_dict}
        
    except RagieNotFoundError:
        raise HTTPException(status_code=404, detail="Document not found")
    except RagieError as e:
        logger.error(f"Failed to get document: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.delete(
    "/documents/{document_id}",
    status_code=204,
    summary="Delete Document (Simplified)",
    description="Delete a document with simplified error handling"
)
async def delete_document(
    document_id: str,
    user_id: str = Depends(require_auth),
    organization_id: str = Depends(get_organization_id),
    ragie_service: RagieService = Depends(get_ragie_service)
) -> None:
    """Delete a document with simplified error handling."""
    
    try:
        await ragie_service.delete_document(
            document_id=document_id,
            organization_id=organization_id
        )
        
        logger.info("Document deleted successfully", extra={
            "document_id": document_id,
            "organization_id": organization_id,
            "user_id": user_id
        })
        
    except RagieNotFoundError:
        raise HTTPException(status_code=404, detail="Document not found")
    except RagieError as e:
        logger.error(f"Failed to delete document: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.patch(
    "/documents/{document_id}/metadata",
    summary="Update Document Metadata (Simplified)",
    description="Update document metadata with simplified error handling"
)
async def update_document_metadata(
    document_id: str,
    request: MetadataUpdateRequest,
    user_id: str = Depends(require_auth),
    organization_id: str = Depends(get_organization_id),
    ragie_service: RagieService = Depends(get_ragie_service)
) -> Dict[str, Any]:
    """Update document metadata with simplified error handling."""
    
    try:
        updated_document = await ragie_service.update_document_metadata(
            document_id=document_id,
            organization_id=organization_id,
            metadata=request.metadata
        )
        
        # Convert document to dict for response
        document_dict = updated_document.dict()
        document_dict["created_at"] = updated_document.created_at.isoformat()
        document_dict["updated_at"] = updated_document.updated_at.isoformat()
        
        logger.info("Document metadata updated successfully", extra={
            "document_id": document_id,
            "organization_id": organization_id,
            "user_id": user_id,
            "metadata_keys": list(request.metadata.keys())
        })
        
        return {"success": True, "data": document_dict}
        
    except RagieNotFoundError:
        raise HTTPException(status_code=404, detail="Document not found")
    except RagieValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except RagieError as e:
        logger.error(f"Failed to update metadata: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/query",
    summary="Query Documents (Simplified)",
    description="Retrieve relevant document chunks with simplified error handling"
)
async def query_documents(
    request: QueryRequest,
    user_id: str = Depends(require_auth),
    organization_id: str = Depends(get_organization_id),
    ragie_service: RagieService = Depends(get_ragie_service)
) -> Dict[str, Any]:
    """Retrieve relevant document chunks with simplified error handling."""
    
    try:
        retrieval_result = await ragie_service.retrieve_chunks(
            query=request.query,
            organization_id=organization_id,
            max_chunks=request.max_chunks or 10,
            document_ids=request.document_ids,
            metadata_filter=request.metadata_filter
        )
        
        # Convert scored_chunks to dict for response
        chunks_dict = [chunk.dict() for chunk in retrieval_result.scored_chunks]
        
        response_data = {
            "scored_chunks": chunks_dict
        }
        
        logger.info("Document query completed successfully", extra={
            "organization_id": organization_id,
            "user_id": user_id,
            "query_length": len(request.query),
            "chunks_found": len(retrieval_result.scored_chunks)
        })
        
        return {"success": True, "data": response_data}
        
    except RagieError as e:
        logger.error(f"Failed to query documents: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/documents/{document_id}/source",
    summary="Get Document Source (Simplified)",
    description="Get the original source file with simplified error handling"
)
async def get_document_source(
    document_id: str,
    user_id: str = Depends(require_auth),
    organization_id: str = Depends(get_organization_id),
    ragie_service: RagieService = Depends(get_ragie_service)
) -> Response:
    """Get the original source file with simplified error handling."""
    
    try:
        source_data = await ragie_service.get_document_source(
            document_id=document_id,
            organization_id=organization_id
        )
        content = source_data["content"]
        content_type = source_data["content_type"]
        
        logger.info("Document source retrieved successfully", extra={
            "document_id": document_id,
            "organization_id": organization_id,
            "user_id": user_id,
            "content_type": content_type
        })
        
        return Response(
            content=content,
            media_type=content_type
        )
        
    except RagieNotFoundError:
        raise HTTPException(status_code=404, detail="Document not found")
    except RagieError as e:
        logger.error(f"Failed to get document source: {e}")
        raise HTTPException(status_code=400, detail=str(e))
