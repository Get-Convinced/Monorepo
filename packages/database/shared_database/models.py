"""
SQLAlchemy models for AI Knowledge Agent database schema.

This module defines all database models for tracking document processing,
ingestion jobs, vector store references, and processing statistics.
"""

import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum as PyEnum

from sqlalchemy import (
    Column, String, Integer, DateTime, Text, Boolean, 
    Float, JSON, ForeignKey, Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class ProcessingStatus(PyEnum):
    """Processing status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ProcessorType(PyEnum):
    """Document processor type enumeration."""
    GPT_4O = "gpt-4o"
    GPT_4O_MINI = "gpt-4o-mini"
    GPT_5 = "gpt-5"
    DOCLING = "docling"


class FileType(PyEnum):
    """File type enumeration."""
    PDF = "pdf"
    DOC = "doc"
    DOCX = "docx"
    PPT = "ppt"
    PPTX = "pptx"
    TXT = "txt"
    MD = "md"
    HTML = "html"
    XML = "xml"
    OTHER = "other"


class UserRole(PyEnum):
    """User role enumeration."""
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class Organization(Base):
    """Organization model for multi-tenancy."""
    
    __tablename__ = "organizations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    slug = Column(String(100), nullable=False, unique=True, index=True)  # URL-friendly identifier
    description = Column(Text, nullable=True)
    
    # Organization settings
    settings = Column(JSON, nullable=True)  # Organization-specific configuration
    s3_bucket_name = Column(String(255), nullable=False)  # S3 bucket for this org
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    members = relationship("OrganizationMember", back_populates="organization", cascade="all, delete-orphan")
    ingestion_jobs = relationship("IngestionJob", back_populates="organization", cascade="all, delete-orphan")
    s3_files = relationship("S3File", back_populates="organization", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_organizations_slug', 'slug'),
        Index('idx_organizations_created', 'created_at'),
    )


class User(Base):
    """User model."""
    
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), nullable=False, unique=True, index=True)
    name = Column(String(255), nullable=False)
    
    # User profile data
    profile_data = Column(JSON, nullable=True)  # Additional user information
    avatar_url = Column(String(500), nullable=True)
    
    # Authentication (for future use)
    is_active = Column(Boolean, default=True, nullable=False)
    email_verified = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    organization_memberships = relationship("OrganizationMember", back_populates="user", cascade="all, delete-orphan")
    ingestion_jobs = relationship("IngestionJob", back_populates="user", cascade="all, delete-orphan")
    s3_files = relationship("S3File", back_populates="user", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_users_email', 'email'),
        Index('idx_users_created', 'created_at'),
        Index('idx_users_active', 'is_active'),
    )


class OrganizationMember(Base):
    """Organization membership model."""
    
    __tablename__ = "organization_members"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Role and permissions
    role = Column(String(50), nullable=False, default=UserRole.MEMBER.value, index=True)
    permissions = Column(JSON, nullable=True)  # Additional permissions beyond role
    
    # Membership status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    joined_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    organization = relationship("Organization", back_populates="members")
    user = relationship("User", back_populates="organization_memberships")
    
    __table_args__ = (
        UniqueConstraint('organization_id', 'user_id', name='uq_org_member'),
        Index('idx_org_members_role', 'role'),
        Index('idx_org_members_active', 'is_active'),
    )


class S3File(Base):
    """S3 file storage tracking."""
    
    __tablename__ = "s3_files"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # File information
    file_name = Column(String(500), nullable=False, index=True)
    original_file_name = Column(String(500), nullable=False)  # Original uploaded filename
    file_path = Column(Text, nullable=False)  # Logical path within organization
    s3_key = Column(Text, nullable=False, index=True)  # S3 object key
    s3_bucket = Column(String(255), nullable=False, index=True)
    
    # File metadata
    file_size_bytes = Column(Integer, nullable=False)
    content_type = Column(String(255), nullable=True)
    file_hash = Column(String(64), nullable=True, index=True)  # SHA-256 hash
    
    # Additional metadata
    file_metadata = Column(JSON, nullable=True)  # Custom metadata
    tags = Column(JSON, nullable=True)  # File tags for organization
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    organization = relationship("Organization", back_populates="s3_files")
    user = relationship("User", back_populates="s3_files")
    
    __table_args__ = (
        Index('idx_s3_files_org_created', 'organization_id', 'created_at'),
        Index('idx_s3_files_user_created', 'user_id', 'created_at'),
        Index('idx_s3_files_bucket_key', 's3_bucket', 's3_key'),
        Index('idx_s3_files_hash', 'file_hash'),
    )


class IngestionJob(Base):
    """Track document ingestion jobs."""
    
    __tablename__ = "ingestion_jobs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    collection_name = Column(String(255), nullable=False, index=True)
    status = Column(String(50), nullable=False, default=ProcessingStatus.PENDING.value, index=True)
    
    # Job metadata
    created_by = Column(String(255), nullable=True)  # User or system that created the job (legacy field)
    priority = Column(Integer, default=0, index=True)  # Higher number = higher priority
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    failed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Job configuration
    job_metadata = Column(JSON, nullable=True)  # Job-level metadata
    processing_options = Column(JSON, nullable=True)  # Processing configuration
    
    # Results and error tracking
    error_message = Column(Text, nullable=True)
    error_details = Column(JSON, nullable=True)
    
    # Summary statistics
    total_files = Column(Integer, default=0)
    successful_files = Column(Integer, default=0)
    failed_files = Column(Integer, default=0)
    total_chunks_created = Column(Integer, default=0)
    
    # Relationships
    organization = relationship("Organization", back_populates="ingestion_jobs")
    user = relationship("User", back_populates="ingestion_jobs")
    documents = relationship("ProcessedDocument", back_populates="ingestion_job", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_ingestion_jobs_status_created', 'status', 'created_at'),
        Index('idx_ingestion_jobs_collection', 'collection_name', 'status'),
    )


class ProcessedDocument(Base):
    """Track individual document processing results."""
    
    __tablename__ = "processed_documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ingestion_job_id = Column(UUID(as_uuid=True), ForeignKey("ingestion_jobs.id"), nullable=False)
    
    # File information
    file_name = Column(String(500), nullable=False, index=True)
    file_path = Column(Text, nullable=False)
    file_type = Column(String(50), nullable=False, index=True)
    file_size_bytes = Column(Integer, nullable=False)
    file_hash = Column(String(64), nullable=True, index=True)  # SHA-256 hash for deduplication
    
    # Processing information
    processor_type = Column(String(50), nullable=False, index=True)
    processing_method = Column(String(100), nullable=True)
    status = Column(String(50), nullable=False, default=ProcessingStatus.PENDING.value, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    failed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Processing results
    processing_metadata = Column(JSON, nullable=True)  # Rich metadata from processors
    structured_elements = Column(JSON, nullable=True)  # Tables, figures, etc.
    page_statistics = Column(JSON, nullable=True)  # Page-level stats
    
    # Vector store information
    collection_name = Column(String(255), nullable=False, index=True)
    vector_point_ids = Column(JSON, nullable=True)  # List of Qdrant point IDs
    total_chunks_created = Column(Integer, default=0)
    total_points_stored = Column(Integer, default=0)
    
    # Error tracking
    error_message = Column(Text, nullable=True)
    error_details = Column(JSON, nullable=True)
    
    # Processing performance
    processing_duration_seconds = Column(Float, nullable=True)
    token_usage = Column(Integer, nullable=True)  # For GPT models
    model_used = Column(String(100), nullable=True)  # Specific model version
    
    # Relationships
    ingestion_job = relationship("IngestionJob", back_populates="documents")
    vector_references = relationship("VectorStoreReference", back_populates="document", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_processed_docs_job_status', 'ingestion_job_id', 'status'),
        Index('idx_processed_docs_file_hash', 'file_hash'),
        Index('idx_processed_docs_processor_type', 'processor_type', 'status'),
        UniqueConstraint('file_hash', 'collection_name', name='uq_document_file_hash_collection'),
    )


class VectorStoreReference(Base):
    """Track vector store points and their metadata."""
    
    __tablename__ = "vector_store_references"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("processed_documents.id"), nullable=False)
    
    # Vector store information
    collection_name = Column(String(255), nullable=False, index=True)
    point_id = Column(String(255), nullable=False, index=True)  # Qdrant point ID
    chunk_index = Column(Integer, nullable=False)
    chunk_type = Column(String(100), nullable=False, index=True)
    
    # Content and metadata
    content_preview = Column(Text, nullable=True)  # First 500 chars for debugging
    chunk_metadata = Column(JSON, nullable=True)  # Chunk-specific metadata
    
    # Vector information
    embedding_model = Column(String(100), nullable=False)
    embedding_dimension = Column(Integer, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    document = relationship("ProcessedDocument", back_populates="vector_references")
    
    __table_args__ = (
        Index('idx_vector_refs_collection_point', 'collection_name', 'point_id'),
        Index('idx_vector_refs_document_chunk', 'document_id', 'chunk_index'),
        UniqueConstraint('point_id', 'collection_name', name='uq_vector_point_id_collection'),
    )


class ProcessingStatistics(Base):
    """Track processing performance and statistics."""
    
    __tablename__ = "processing_statistics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Time period
    date = Column(DateTime(timezone=True), nullable=False, index=True)
    hour = Column(Integer, nullable=True, index=True)  # For hourly aggregation
    
    # Processing metrics
    total_documents_processed = Column(Integer, default=0)
    successful_documents = Column(Integer, default=0)
    failed_documents = Column(Integer, default=0)
    
    # Processor-specific metrics
    gpt_documents = Column(Integer, default=0)
    docling_documents = Column(Integer, default=0)
    
    # Performance metrics
    avg_processing_time_seconds = Column(Float, nullable=True)
    total_processing_time_seconds = Column(Float, default=0)
    
    # Token usage (for GPT models)
    total_tokens_used = Column(Integer, default=0)
    avg_tokens_per_document = Column(Float, nullable=True)
    
    # File type breakdown
    file_type_breakdown = Column(JSON, nullable=True)  # {"pdf": 10, "docx": 5, ...}
    
    # Vector store metrics
    total_chunks_created = Column(Integer, default=0)
    total_points_stored = Column(Integer, default=0)
    
    # Error tracking
    error_breakdown = Column(JSON, nullable=True)  # {"timeout": 2, "parse_error": 1, ...}
    
    __table_args__ = (
        Index('idx_processing_stats_date_hour', 'date', 'hour'),
        Index('idx_processing_stats_date', 'date'),
    )


class SystemConfiguration(Base):
    """Store system-wide configuration and settings."""
    
    __tablename__ = "system_configuration"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Configuration key-value pairs
    key = Column(String(255), nullable=False, unique=True, index=True)
    value = Column(JSON, nullable=False)
    description = Column(Text, nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    updated_by = Column(String(255), nullable=True)
    
    # Configuration type
    config_type = Column(String(100), nullable=False, index=True)  # "processor", "embedding", "vector_store", etc.
    is_active = Column(Boolean, default=True, index=True)


class ProcessingLog(Base):
    """Detailed processing logs for debugging and monitoring."""
    
    __tablename__ = "processing_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("processed_documents.id"), nullable=True)
    ingestion_job_id = Column(UUID(as_uuid=True), ForeignKey("ingestion_jobs.id"), nullable=True)
    
    # Log details
    level = Column(String(20), nullable=False, index=True)  # "INFO", "WARNING", "ERROR", "DEBUG"
    message = Column(Text, nullable=False)
    details = Column(JSON, nullable=True)
    
    # Context
    processor_type = Column(String(50), nullable=True, index=True)
    processing_stage = Column(String(100), nullable=True, index=True)  # "initialization", "processing", "embedding", etc.
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    __table_args__ = (
        Index('idx_processing_logs_document_level', 'document_id', 'level'),
        Index('idx_processing_logs_job_stage', 'ingestion_job_id', 'processing_stage'),
        Index('idx_processing_logs_created_level', 'created_at', 'level'),
    )
