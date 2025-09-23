"""
Database service layer for AI Knowledge Agent.

This module provides high-level database operations for both applications.
"""

import hashlib
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .models import (
    IngestionJob, ProcessedDocument, VectorStoreReference,
    ProcessingStatistics, SystemConfiguration, ProcessingLog,
    ProcessingStatus, ProcessorType, FileType,
    Organization, User, OrganizationMember, S3File, UserRole
)
from .database import get_db_client


class DocumentProcessingService:
    """Service for document processing operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_ingestion_job(
        self,
        organization_id: UUID,
        user_id: UUID,
        collection_name: str,
        file_paths: List[str],
        metadata: Optional[Dict[str, Any]] = None,
        processing_options: Optional[Dict[str, Any]] = None,
        created_by: Optional[str] = None,
        priority: int = 0
    ) -> IngestionJob:
        """Create a new ingestion job."""
        job = IngestionJob(
            organization_id=organization_id,
            user_id=user_id,
            collection_name=collection_name,
            status=ProcessingStatus.PENDING.value,
            job_metadata=metadata or {},
            processing_options=processing_options or {},
            created_by=created_by,
            priority=priority,
            total_files=len(file_paths)
        )
        
        self.session.add(job)
        await self.session.flush()  # Get the ID
        
        # Create ProcessedDocument records for each file
        for file_path in file_paths:
            file_hash = await self._calculate_file_hash(file_path)
            file_type = self._determine_file_type(file_path)
            
            document = ProcessedDocument(
                ingestion_job_id=job.id,
                file_name=file_path.split('/')[-1],
                file_path=file_path,
                file_type=file_type.value,
                file_size_bytes=0,  # Will be updated during processing
                file_hash=file_hash,
                collection_name=collection_name,
                status=ProcessingStatus.PENDING.value
            )
            self.session.add(document)
        
        await self.session.commit()
        return job
    
    async def get_ingestion_job(self, job_id: UUID) -> Optional[IngestionJob]:
        """Get ingestion job by ID with documents."""
        result = await self.session.execute(
            select(IngestionJob)
            .options(selectinload(IngestionJob.documents))
            .where(IngestionJob.id == job_id)
        )
        return result.scalar_one_or_none()
    
    async def update_ingestion_job_status(
        self,
        job_id: UUID,
        status: ProcessingStatus,
        error_message: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update ingestion job status."""
        update_data = {"status": status.value}
        
        if status == ProcessingStatus.PROCESSING:
            update_data["started_at"] = datetime.utcnow()
        elif status == ProcessingStatus.COMPLETED:
            update_data["completed_at"] = datetime.utcnow()
        elif status == ProcessingStatus.FAILED:
            update_data["failed_at"] = datetime.utcnow()
            update_data["error_message"] = error_message
            update_data["error_details"] = error_details
        
        result = await self.session.execute(
            update(IngestionJob)
            .where(IngestionJob.id == job_id)
            .values(**update_data)
        )
        
        await self.session.commit()
        return result.rowcount > 0
    
    async def update_ingestion_job_summary(
        self,
        job_id: UUID,
        successful_files: int,
        failed_files: int,
        total_chunks_created: int
    ) -> bool:
        """Update ingestion job summary statistics."""
        result = await self.session.execute(
            update(IngestionJob)
            .where(IngestionJob.id == job_id)
            .values(
                successful_files=successful_files,
                failed_files=failed_files,
                total_chunks_created=total_chunks_created
            )
        )
        
        await self.session.commit()
        return result.rowcount > 0
    
    async def create_processed_document(
        self,
        ingestion_job_id: UUID,
        file_path: str,
        file_name: str,
        file_size_bytes: int,
        processor_type: ProcessorType,
        processing_method: Optional[str] = None,
        collection_name: str = "knowledge_base"
    ) -> ProcessedDocument:
        """Create a processed document record."""
        file_hash = await self._calculate_file_hash(file_path)
        file_type = self._determine_file_type(file_path)
        
        document = ProcessedDocument(
            ingestion_job_id=ingestion_job_id,
            file_name=file_name,
            file_path=file_path,
            file_type=file_type.value,
            file_size_bytes=file_size_bytes,
            file_hash=file_hash,
            processor_type=processor_type.value,
            processing_method=processing_method,
            collection_name=collection_name,
            status=ProcessingStatus.PENDING.value
        )
        
        self.session.add(document)
        await self.session.flush()
        return document
    
    async def update_document_processing_result(
        self,
        document_id: UUID,
        status: ProcessingStatus,
        processing_metadata: Optional[Dict[str, Any]] = None,
        structured_elements: Optional[Dict[str, Any]] = None,
        page_statistics: Optional[Dict[str, Any]] = None,
        vector_point_ids: Optional[List[str]] = None,
        total_chunks_created: int = 0,
        total_points_stored: int = 0,
        processing_duration_seconds: Optional[float] = None,
        token_usage: Optional[int] = None,
        model_used: Optional[str] = None,
        error_message: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update document processing results."""
        update_data = {"status": status.value}
        
        if status == ProcessingStatus.PROCESSING:
            update_data["started_at"] = datetime.utcnow()
        elif status == ProcessingStatus.COMPLETED:
            update_data["completed_at"] = datetime.utcnow()
        elif status == ProcessingStatus.FAILED:
            update_data["failed_at"] = datetime.utcnow()
        
        if processing_metadata is not None:
            update_data["processing_metadata"] = processing_metadata
        if structured_elements is not None:
            update_data["structured_elements"] = structured_elements
        if page_statistics is not None:
            update_data["page_statistics"] = page_statistics
        if vector_point_ids is not None:
            update_data["vector_point_ids"] = vector_point_ids
        if total_chunks_created > 0:
            update_data["total_chunks_created"] = total_chunks_created
        if total_points_stored > 0:
            update_data["total_points_stored"] = total_points_stored
        if processing_duration_seconds is not None:
            update_data["processing_duration_seconds"] = processing_duration_seconds
        if token_usage is not None:
            update_data["token_usage"] = token_usage
        if model_used is not None:
            update_data["model_used"] = model_used
        if error_message is not None:
            update_data["error_message"] = error_message
        if error_details is not None:
            update_data["error_details"] = error_details
        
        result = await self.session.execute(
            update(ProcessedDocument)
            .where(ProcessedDocument.id == document_id)
            .values(**update_data)
        )
        
        await self.session.commit()
        return result.rowcount > 0
    
    async def create_vector_store_reference(
        self,
        document_id: UUID,
        collection_name: str,
        point_id: str,
        chunk_index: int,
        chunk_type: str,
        content_preview: Optional[str] = None,
        chunk_metadata: Optional[Dict[str, Any]] = None,
        embedding_model: str = "mxbai-embed-large",
        embedding_dimension: int = 1024
    ) -> VectorStoreReference:
        """Create vector store reference."""
        reference = VectorStoreReference(
            document_id=document_id,
            collection_name=collection_name,
            point_id=point_id,
            chunk_index=chunk_index,
            chunk_type=chunk_type,
            content_preview=content_preview,
            chunk_metadata=chunk_metadata,
            embedding_model=embedding_model,
            embedding_dimension=embedding_dimension
        )
        
        self.session.add(reference)
        await self.session.flush()
        return reference
    
    async def get_document_by_file_hash(
        self,
        file_hash: str,
        collection_name: str
    ) -> Optional[ProcessedDocument]:
        """Check if document with same hash already exists in collection."""
        result = await self.session.execute(
            select(ProcessedDocument)
            .where(
                and_(
                    ProcessedDocument.file_hash == file_hash,
                    ProcessedDocument.collection_name == collection_name
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def list_jobs(
        self,
        status: Optional[ProcessingStatus] = None,
        collection_name: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[IngestionJob]:
        """List ingestion jobs with optional filters."""
        query = select(IngestionJob)
        
        if status:
            query = query.where(IngestionJob.status == status.value)
        if collection_name:
            query = query.where(IngestionJob.collection_name == collection_name)
        
        query = query.order_by(IngestionJob.created_at.desc()).limit(limit).offset(offset)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_processing_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get processing statistics for date range."""
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=7)
        if not end_date:
            end_date = datetime.utcnow()
        
        # Get document counts by status
        status_counts = await self.session.execute(
            select(
                ProcessedDocument.status,
                func.count(ProcessedDocument.id).label('count')
            )
            .where(
                and_(
                    ProcessedDocument.created_at >= start_date,
                    ProcessedDocument.created_at <= end_date
                )
            )
            .group_by(ProcessedDocument.status)
        )
        
        # Get processor type breakdown
        processor_counts = await self.session.execute(
            select(
                ProcessedDocument.processor_type,
                func.count(ProcessedDocument.id).label('count')
            )
            .where(
                and_(
                    ProcessedDocument.created_at >= start_date,
                    ProcessedDocument.created_at <= end_date
                )
            )
            .group_by(ProcessedDocument.processor_type)
        )
        
        # Get file type breakdown
        file_type_counts = await self.session.execute(
            select(
                ProcessedDocument.file_type,
                func.count(ProcessedDocument.id).label('count')
            )
            .where(
                and_(
                    ProcessedDocument.created_at >= start_date,
                    ProcessedDocument.created_at <= end_date
                )
            )
            .group_by(ProcessedDocument.file_type)
        )
        
        return {
            "date_range": {"start": start_date, "end": end_date},
            "status_breakdown": {row.status: row.count for row in status_counts},
            "processor_breakdown": {row.processor_type: row.count for row in processor_counts},
            "file_type_breakdown": {row.file_type: row.count for row in file_type_counts}
        }
    
    async def _calculate_file_hash(self, file_path: str) -> Optional[str]:
        """Calculate SHA-256 hash of file."""
        try:
            import os
            if os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    return hashlib.sha256(f.read()).hexdigest()
        except Exception:
            pass
        return None
    
    def _determine_file_type(self, file_path: str) -> FileType:
        """Determine file type from extension."""
        ext = file_path.lower().split('.')[-1] if '.' in file_path else ''
        
        type_mapping = {
            'pdf': FileType.PDF,
            'doc': FileType.DOC,
            'docx': FileType.DOCX,
            'ppt': FileType.PPT,
            'pptx': FileType.PPTX,
            'txt': FileType.TXT,
            'md': FileType.MD,
            'html': FileType.HTML,
            'xml': FileType.XML,
        }
        
        return type_mapping.get(ext, FileType.OTHER)


class LoggingService:
    """Service for processing logs."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def log_processing_event(
        self,
        level: str,
        message: str,
        document_id: Optional[UUID] = None,
        ingestion_job_id: Optional[UUID] = None,
        processor_type: Optional[str] = None,
        processing_stage: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> ProcessingLog:
        """Log a processing event."""
        log_entry = ProcessingLog(
            level=level,
            message=message,
            document_id=document_id,
            ingestion_job_id=ingestion_job_id,
            processor_type=processor_type,
            processing_stage=processing_stage,
            details=details
        )
        
        self.session.add(log_entry)
        await self.session.flush()
        return log_entry
    
    async def get_processing_logs(
        self,
        document_id: Optional[UUID] = None,
        ingestion_job_id: Optional[UUID] = None,
        level: Optional[str] = None,
        processing_stage: Optional[str] = None,
        limit: int = 100
    ) -> List[ProcessingLog]:
        """Get processing logs with filters."""
        query = select(ProcessingLog)
        
        if document_id:
            query = query.where(ProcessingLog.document_id == document_id)
        if ingestion_job_id:
            query = query.where(ProcessingLog.ingestion_job_id == ingestion_job_id)
        if level:
            query = query.where(ProcessingLog.level == level)
        if processing_stage:
            query = query.where(ProcessingLog.processing_stage == processing_stage)
        
        query = query.order_by(ProcessingLog.created_at.desc()).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()


class OrganizationService:
    """Service for organization operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_organization(
        self,
        name: str,
        slug: str,
        description: Optional[str] = None,
        settings: Optional[Dict[str, Any]] = None,
        s3_bucket_name: Optional[str] = None
    ) -> Organization:
        """Create a new organization."""
        if s3_bucket_name is None:
            # Generate bucket name from slug
            s3_bucket_name = f"org-{slug}-files"
        
        org = Organization(
            name=name,
            slug=slug,
            description=description,
            settings=settings or {},
            s3_bucket_name=s3_bucket_name
        )
        
        self.session.add(org)
        await self.session.flush()
        return org
    
    async def get_organization_by_id(self, org_id: UUID) -> Optional[Organization]:
        """Get organization by ID."""
        query = select(Organization).where(Organization.id == org_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_organization_by_slug(self, slug: str) -> Optional[Organization]:
        """Get organization by slug."""
        query = select(Organization).where(Organization.slug == slug)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def list_organizations(self, limit: int = 100, offset: int = 0) -> List[Organization]:
        """List organizations with pagination."""
        query = select(Organization).order_by(Organization.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def update_organization(
        self,
        org_id: UUID,
        name: Optional[str] = None,
        description: Optional[str] = None,
        settings: Optional[Dict[str, Any]] = None
    ) -> Optional[Organization]:
        """Update organization."""
        org = await self.get_organization_by_id(org_id)
        if not org:
            return None
        
        if name is not None:
            org.name = name
        if description is not None:
            org.description = description
        if settings is not None:
            org.settings = settings
        
        org.updated_at = datetime.utcnow()
        await self.session.flush()
        return org


class UserService:
    """Service for user operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_user(
        self,
        email: str,
        name: str,
        profile_data: Optional[Dict[str, Any]] = None,
        avatar_url: Optional[str] = None
    ) -> User:
        """Create a new user."""
        user = User(
            email=email,
            name=name,
            profile_data=profile_data or {},
            avatar_url=avatar_url
        )
        
        self.session.add(user)
        await self.session.flush()
        return user
    
    async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID."""
        query = select(User).where(User.id == user_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        query = select(User).where(User.email == email)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def update_user(
        self,
        user_id: UUID,
        name: Optional[str] = None,
        profile_data: Optional[Dict[str, Any]] = None,
        avatar_url: Optional[str] = None
    ) -> Optional[User]:
        """Update user."""
        user = await self.get_user_by_id(user_id)
        if not user:
            return None
        
        if name is not None:
            user.name = name
        if profile_data is not None:
            user.profile_data = profile_data
        if avatar_url is not None:
            user.avatar_url = avatar_url
        
        user.updated_at = datetime.utcnow()
        await self.session.flush()
        return user


class OrganizationMemberService:
    """Service for organization membership operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def add_member(
        self,
        organization_id: UUID,
        user_id: UUID,
        role: str = UserRole.MEMBER.value,
        permissions: Optional[Dict[str, Any]] = None
    ) -> OrganizationMember:
        """Add a user to an organization."""
        member = OrganizationMember(
            organization_id=organization_id,
            user_id=user_id,
            role=role,
            permissions=permissions or {}
        )
        
        self.session.add(member)
        await self.session.flush()
        return member
    
    async def get_organization_members(self, organization_id: UUID) -> List[OrganizationMember]:
        """Get all members of an organization."""
        query = (
            select(OrganizationMember)
            .options(selectinload(OrganizationMember.user))
            .where(
                and_(
                    OrganizationMember.organization_id == organization_id,
                    OrganizationMember.is_active == True
                )
            )
            .order_by(OrganizationMember.joined_at)
        )
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_user_organizations(self, user_id: UUID) -> List[OrganizationMember]:
        """Get all organizations a user belongs to."""
        query = (
            select(OrganizationMember)
            .options(selectinload(OrganizationMember.organization))
            .where(
                and_(
                    OrganizationMember.user_id == user_id,
                    OrganizationMember.is_active == True
                )
            )
            .order_by(OrganizationMember.joined_at)
        )
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def update_member_role(
        self,
        organization_id: UUID,
        user_id: UUID,
        role: str,
        permissions: Optional[Dict[str, Any]] = None
    ) -> Optional[OrganizationMember]:
        """Update member role and permissions."""
        query = select(OrganizationMember).where(
            and_(
                OrganizationMember.organization_id == organization_id,
                OrganizationMember.user_id == user_id
            )
        )
        result = await self.session.execute(query)
        member = result.scalar_one_or_none()
        
        if not member:
            return None
        
        member.role = role
        if permissions is not None:
            member.permissions = permissions
        member.updated_at = datetime.utcnow()
        
        await self.session.flush()
        return member
    
    async def remove_member(self, organization_id: UUID, user_id: UUID) -> bool:
        """Remove a member from an organization."""
        query = select(OrganizationMember).where(
            and_(
                OrganizationMember.organization_id == organization_id,
                OrganizationMember.user_id == user_id
            )
        )
        result = await self.session.execute(query)
        member = result.scalar_one_or_none()
        
        if not member:
            return False
        
        member.is_active = False
        member.updated_at = datetime.utcnow()
        await self.session.flush()
        return True


class S3FileService:
    """Service for S3 file operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_s3_file(
        self,
        organization_id: UUID,
        user_id: UUID,
        file_name: str,
        original_file_name: str,
        file_path: str,
        s3_key: str,
        s3_bucket: str,
        file_size_bytes: int,
        content_type: Optional[str] = None,
        file_hash: Optional[str] = None,
        file_metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
    ) -> S3File:
        """Create a new S3 file record."""
        s3_file = S3File(
            organization_id=organization_id,
            user_id=user_id,
            file_name=file_name,
            original_file_name=original_file_name,
            file_path=file_path,
            s3_key=s3_key,
            s3_bucket=s3_bucket,
            file_size_bytes=file_size_bytes,
            content_type=content_type,
            file_hash=file_hash,
            file_metadata=file_metadata or {},
            tags=tags or []
        )
        
        self.session.add(s3_file)
        await self.session.flush()
        return s3_file
    
    async def get_s3_file_by_id(self, file_id: UUID) -> Optional[S3File]:
        """Get S3 file by ID."""
        query = select(S3File).where(S3File.id == file_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_s3_file_by_s3_key(self, s3_bucket: str, s3_key: str) -> Optional[S3File]:
        """Get S3 file by bucket and key."""
        query = select(S3File).where(
            and_(
                S3File.s3_bucket == s3_bucket,
                S3File.s3_key == s3_key
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def list_organization_files(
        self,
        organization_id: UUID,
        limit: int = 100,
        offset: int = 0
    ) -> List[S3File]:
        """List files in an organization."""
        query = (
            select(S3File)
            .where(S3File.organization_id == organization_id)
            .order_by(S3File.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def list_user_files(
        self,
        user_id: UUID,
        organization_id: Optional[UUID] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[S3File]:
        """List files uploaded by a user."""
        query = select(S3File).where(S3File.user_id == user_id)
        
        if organization_id:
            query = query.where(S3File.organization_id == organization_id)
        
        query = query.order_by(S3File.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def delete_s3_file_record(self, file_id: UUID) -> bool:
        """Delete S3 file record from database."""
        query = select(S3File).where(S3File.id == file_id)
        result = await self.session.execute(query)
        s3_file = result.scalar_one_or_none()
        
        if not s3_file:
            return False
        
        await self.session.delete(s3_file)
        await self.session.flush()
        return True


# Update the main DatabaseClient class to include the new services
class DatabaseClient:
    """Enhanced database client with all services."""
    
    def __init__(self):
        from .database import get_async_session
        self.get_async_session = get_async_session
    
    # Document processing methods (existing)
    async def create_ingestion_job(self, session: AsyncSession, **kwargs) -> IngestionJob:
        service = DocumentProcessingService(session)
        return await service.create_ingestion_job(**kwargs)
    
    async def get_ingestion_job(self, session: AsyncSession, job_id: UUID) -> Optional[IngestionJob]:
        service = DocumentProcessingService(session)
        return await service.get_ingestion_job(job_id)
    
    async def update_ingestion_job(self, session: AsyncSession, job: IngestionJob) -> IngestionJob:
        service = DocumentProcessingService(session)
        return await service.update_ingestion_job(job)
    
    async def list_ingestion_jobs(self, session: AsyncSession, status: Optional[ProcessingStatus] = None) -> List[IngestionJob]:
        service = DocumentProcessingService(session)
        return await service.list_ingestion_jobs(status)
    
    async def create_processed_document(self, session: AsyncSession, **kwargs) -> ProcessedDocument:
        service = DocumentProcessingService(session)
        return await service.create_processed_document(**kwargs)
    
    async def update_processed_document(self, session: AsyncSession, document: ProcessedDocument) -> ProcessedDocument:
        service = DocumentProcessingService(session)
        return await service.update_processed_document(document)
    
    # Organization methods
    async def create_organization(self, session: AsyncSession, **kwargs) -> Organization:
        service = OrganizationService(session)
        return await service.create_organization(**kwargs)
    
    async def get_organization_by_id(self, session: AsyncSession, org_id: UUID) -> Optional[Organization]:
        service = OrganizationService(session)
        return await service.get_organization_by_id(org_id)
    
    async def get_organization_by_slug(self, session: AsyncSession, slug: str) -> Optional[Organization]:
        service = OrganizationService(session)
        return await service.get_organization_by_slug(slug)
    
    # User methods
    async def create_user(self, session: AsyncSession, **kwargs) -> User:
        service = UserService(session)
        return await service.create_user(**kwargs)
    
    async def get_user_by_id(self, session: AsyncSession, user_id: UUID) -> Optional[User]:
        service = UserService(session)
        return await service.get_user_by_id(user_id)
    
    async def get_user_by_email(self, session: AsyncSession, email: str) -> Optional[User]:
        service = UserService(session)
        return await service.get_user_by_email(email)
    
    # Organization member methods
    async def add_organization_member(self, session: AsyncSession, **kwargs) -> OrganizationMember:
        service = OrganizationMemberService(session)
        return await service.add_member(**kwargs)
    
    async def get_organization_members(self, session: AsyncSession, org_id: UUID) -> List[OrganizationMember]:
        service = OrganizationMemberService(session)
        return await service.get_organization_members(org_id)
    
    async def get_user_organizations(self, session: AsyncSession, user_id: UUID) -> List[OrganizationMember]:
        service = OrganizationMemberService(session)
        return await service.get_user_organizations(user_id)
    
    # S3 file methods
    async def create_s3_file(self, session: AsyncSession, **kwargs) -> S3File:
        service = S3FileService(session)
        return await service.create_s3_file(**kwargs)
    
    async def get_s3_file_by_id(self, session: AsyncSession, file_id: UUID) -> Optional[S3File]:
        service = S3FileService(session)
        return await service.get_s3_file_by_id(file_id)
    
    async def list_organization_files(self, session: AsyncSession, org_id: UUID, **kwargs) -> List[S3File]:
        service = S3FileService(session)
        return await service.list_organization_files(org_id, **kwargs)
