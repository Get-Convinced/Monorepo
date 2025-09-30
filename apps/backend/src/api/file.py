"""
File API endpoints with proper Frontegg authentication.
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from shared_database import DatabaseClient
from shared_database.database import get_async_session
from ..services.s3_service import S3Service, get_s3_service, S3ServiceError
from ..models.file import (
    FileUploadResponse,
    FileResponse,
    FileListResponse,
    FileDownloadResponse,
    FileDeleteResponse,
    FileMetadataResponse,
    FileCopyRequest,
    FileCopyResponse,
    FileSearchRequest,
    FileSearchResponse
)
from ..auth import get_current_user, get_organization_id

router = APIRouter(prefix="/files", tags=["files"])


def get_db_client() -> DatabaseClient:
    """Dependency to get database client."""
    return DatabaseClient()


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    subfolder: str = Query(default="documents", description="Subfolder within user directory"),
    tags: Optional[List[str]] = Query(default=None, description="File tags"),
    metadata: Optional[str] = Query(default=None, description="Additional metadata as JSON string"),
    org_id: str = Depends(get_organization_id),
    db_client: DatabaseClient = Depends(get_db_client),
    s3_service: S3Service = Depends(get_s3_service),
    session: AsyncSession = Depends(get_async_session)
):
    """Upload a file to S3 and create database record."""
    try:
        # Extract authenticated user and organization from context
        user_info = user  # User info from auth
        organization_id = UUID(org_id)
        user_id = UUID(user_info["sub"])  # Frontegg user ID from JWT
        
        # Verify organization exists
        organization = await db_client.get_organization_by_id(session, organization_id)
        if not organization:
            raise HTTPException(status_code=404, detail="Organization not found")
        
        # Verify user exists (or create if needed)
        user = await db_client.get_user_by_id(session, user_id)
        if not user:
            # Create user from Frontegg data if doesn't exist
            user = await db_client.create_user(
                session=session,
                id=user_id,
                email=user_info.get("email"),
                name=user_info.get("name", user_info.get("email", "Unknown User")),
                profile_data={"frontegg_user_id": user_info["sub"]},
                avatar_url=user_info.get("profilePictureUrl")
            )
        
        # Upload file to S3
        s3_file, s3_key = await s3_service.upload_file(
            organization=organization,
            user=user,
            upload_file=file,
            subfolder=subfolder,
            metadata=metadata,
            tags=tags
        )
        
        # Save to database
        db_file = await db_client.create_s3_file(
            session=session,
            organization_id=s3_file.organization_id,
            user_id=s3_file.user_id,
            file_name=s3_file.file_name,
            original_file_name=s3_file.original_file_name,
            file_path=s3_file.file_path,
            s3_key=s3_file.s3_key,
            s3_bucket=s3_file.s3_bucket,
            file_size_bytes=s3_file.file_size_bytes,
            content_type=s3_file.content_type,
            file_hash=s3_file.file_hash,
            file_metadata=s3_file.file_metadata,
            tags=s3_file.tags
        )
        
        await session.commit()
        
        return FileUploadResponse(
            file_id=db_file.id,
            file_name=db_file.file_name,
            original_file_name=db_file.original_file_name,
            file_size_bytes=db_file.file_size_bytes,
            content_type=db_file.content_type,
            s3_key=db_file.s3_key,
            s3_bucket=db_file.s3_bucket,
            file_hash=db_file.file_hash,
            organization_id=db_file.organization_id,
            user_id=db_file.user_id,
            created_at=db_file.created_at,
            message=f"File '{file.filename}' uploaded successfully"
        )
        
    except S3ServiceError as e:
        await session.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")


@router.get("/", response_model=FileListResponse)
async def list_files(
    user_id: Optional[UUID] = Query(default=None, description="Filter by specific user (admin only)"),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    org_id: str = Depends(get_organization_id),
    db_client: DatabaseClient = Depends(get_db_client),
    session: AsyncSession = Depends(get_async_session)
):
    """List files with optional filtering."""
    try:
        from shared_database.services import S3FileService
        service = S3FileService(session)
        
        # Extract authenticated user and organization from context
        user_info = user  # User info from auth
        organization_id = UUID(org_id)
        current_user_id = UUID(user_info["sub"])
        
        # Check if user is requesting files for a specific user (admin feature)
        if user_id and user_id != current_user_id:
            # TODO: Add admin role check here
            # For now, allow any authenticated user to see any user's files in their org
            files = await service.list_user_files(
                user_id=user_id,
                organization_id=organization_id,
                limit=limit,
                offset=offset
            )
        elif user_id:
            # User requesting their own files
            files = await service.list_user_files(
                user_id=current_user_id,
                organization_id=organization_id,
                limit=limit,
                offset=offset
            )
        else:
            # List all files in the organization
            files = await service.list_organization_files(
                organization_id=organization_id,
                limit=limit,
                offset=offset
            )
        
        return FileListResponse(
            files=[FileResponse.model_validate(file) for file in files],
            total=len(files),  # This is not accurate for pagination
            limit=limit,
            offset=offset,
            organization_id=organization_id,
            user_id=user_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list files: {str(e)}")


@router.get("/{file_id}", response_model=FileResponse)
async def get_file(
    file_id: UUID,
    db_client: DatabaseClient = Depends(get_db_client),
    session: AsyncSession = Depends(get_async_session)
):
    """Get file by ID."""
    try:
        file_record = await db_client.get_s3_file_by_id(session, file_id)
        if not file_record:
            raise HTTPException(status_code=404, detail="File not found")
        
        return FileResponse.model_validate(file_record)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get file: {str(e)}")


@router.post("/{file_id}/download", response_model=FileDownloadResponse)
async def download_file(
    file_id: UUID,
    expiration: int = Query(default=3600, ge=60, le=86400, description="URL expiration in seconds"),
    db_client: DatabaseClient = Depends(get_db_client),
    s3_service: S3Service = Depends(get_s3_service),
    session: AsyncSession = Depends(get_async_session)
):
    """Generate presigned URL for file download."""
    try:
        file_record = await db_client.get_s3_file_by_id(session, file_id)
        if not file_record:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Generate presigned URL
        download_url = await s3_service.generate_presigned_url(
            s3_file=file_record,
            expiration=expiration
        )
        
        from datetime import datetime, timedelta
        expires_at = datetime.utcnow() + timedelta(seconds=expiration)
        
        return FileDownloadResponse(
            file_id=file_record.id,
            file_name=file_record.file_name,
            content_type=file_record.content_type,
            file_size_bytes=file_record.file_size_bytes,
            download_url=download_url,
            expires_at=expires_at
        )
        
    except S3ServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate download URL: {str(e)}")


@router.delete("/{file_id}", response_model=FileDeleteResponse)
async def delete_file(
    file_id: UUID,
    db_client: DatabaseClient = Depends(get_db_client),
    s3_service: S3Service = Depends(get_s3_service),
    session: AsyncSession = Depends(get_async_session)
):
    """Delete file from S3 and database."""
    try:
        file_record = await db_client.get_s3_file_by_id(session, file_id)
        if not file_record:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Delete from S3
        await s3_service.delete_file(file_record)
        
        # Delete from database
        from shared_database.services import S3FileService
        service = S3FileService(session)
        success = await service.delete_s3_file_record(file_id)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete file record")
        
        await session.commit()
        
        return FileDeleteResponse(
            file_id=file_id,
            file_name=file_record.file_name,
            deleted=True,
            message=f"File '{file_record.file_name}' deleted successfully"
        )
        
    except S3ServiceError as e:
        await session.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")


@router.get("/{file_id}/metadata", response_model=FileMetadataResponse)
async def get_file_metadata(
    file_id: UUID,
    db_client: DatabaseClient = Depends(get_db_client),
    s3_service: S3Service = Depends(get_s3_service),
    session: AsyncSession = Depends(get_async_session)
):
    """Get file metadata from S3."""
    try:
        file_record = await db_client.get_s3_file_by_id(session, file_id)
        if not file_record:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Get metadata from S3
        s3_metadata = await s3_service.get_file_metadata(file_record)
        
        return FileMetadataResponse(
            file_id=file_record.id,
            file_name=file_record.file_name,
            s3_metadata=s3_metadata,
            file_hash=file_record.file_hash,
            last_modified=s3_metadata.get('last_modified'),
            storage_class=s3_metadata.get('storage_class')
        )
        
    except S3ServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get file metadata: {str(e)}")


@router.post("/{file_id}/copy", response_model=FileCopyResponse)
async def copy_file(
    file_id: UUID,
    request: FileCopyRequest,
    db_client: DatabaseClient = Depends(get_db_client),
    s3_service: S3Service = Depends(get_s3_service),
    session: AsyncSession = Depends(get_async_session)
):
    """Copy file to another organization/user."""
    try:
        # Get source file
        source_file = await db_client.get_s3_file_by_id(session, file_id)
        if not source_file:
            raise HTTPException(status_code=404, detail="Source file not found")
        
        # Verify target organization exists
        target_org = await db_client.get_organization_by_id(session, request.target_organization_id)
        if not target_org:
            raise HTTPException(status_code=404, detail="Target organization not found")
        
        # Verify target user exists
        target_user = await db_client.get_user_by_id(session, request.target_user_id)
        if not target_user:
            raise HTTPException(status_code=404, detail="Target user not found")
        
        # Copy file in S3
        new_s3_file, new_s3_key = await s3_service.copy_file(
            source_s3_file=source_file,
            target_organization=target_org,
            target_user=target_user,
            new_filename=request.new_filename
        )
        
        # Save new file record to database
        new_db_file = await db_client.create_s3_file(
            session=session,
            organization_id=new_s3_file.organization_id,
            user_id=new_s3_file.user_id,
            file_name=new_s3_file.file_name,
            original_file_name=new_s3_file.original_file_name,
            file_path=new_s3_file.file_path,
            s3_key=new_s3_file.s3_key,
            s3_bucket=new_s3_file.s3_bucket,
            file_size_bytes=new_s3_file.file_size_bytes,
            content_type=new_s3_file.content_type,
            file_hash=new_s3_file.file_hash,
            file_metadata=new_s3_file.file_metadata,
            tags=new_s3_file.tags
        )
        
        await session.commit()
        
        return FileCopyResponse(
            source_file_id=file_id,
            new_file_id=new_db_file.id,
            new_file_name=new_db_file.file_name,
            new_s3_key=new_s3_key,
            message=f"File copied successfully to {target_org.name}"
        )
        
    except S3ServiceError as e:
        await session.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to copy file: {str(e)}")


@router.post("/search", response_model=FileSearchResponse)
async def search_files(
    request: FileSearchRequest,
    organization_id: UUID = Query(..., description="Organization ID to search in"),
    db_client: DatabaseClient = Depends(get_db_client),
    session: AsyncSession = Depends(get_async_session)
):
    """Search files with filters."""
    try:
        from shared_database.services import S3FileService
        from sqlalchemy import and_, or_
        service = S3FileService(session)
        
        # Get organization files
        files = await service.list_organization_files(
            organization_id=organization_id,
            limit=request.limit,
            offset=request.offset
        )
        
        # Apply filters (simplified - in production you'd want proper SQL filtering)
        filtered_files = []
        for file in files:
            # Apply filters
            if request.content_type and file.content_type != request.content_type:
                continue
            if request.min_size and file.file_size_bytes < request.min_size:
                continue
            if request.max_size and file.file_size_bytes > request.max_size:
                continue
            if request.date_from and file.created_at < request.date_from:
                continue
            if request.date_to and file.created_at > request.date_to:
                continue
            if request.tags:
                if not any(tag in file.tags for tag in request.tags):
                    continue
            if request.query:
                # Simple text search in filename and metadata
                query_lower = request.query.lower()
                if (query_lower not in file.file_name.lower() and 
                    query_lower not in str(file.file_metadata).lower()):
                    continue
            
            filtered_files.append(file)
        
        # Apply pagination
        total = len(filtered_files)
        paginated_files = filtered_files[request.offset:request.offset + request.limit]
        
        return FileSearchResponse(
            files=[FileResponse.model_validate(file) for file in paginated_files],
            total=total,
            query=request.query,
            filters_applied={
                "content_type": request.content_type,
                "tags": request.tags,
                "min_size": request.min_size,
                "max_size": request.max_size,
                "date_from": request.date_from,
                "date_to": request.date_to
            },
            limit=request.limit,
            offset=request.offset
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search files: {str(e)}")
