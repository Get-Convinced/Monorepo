"""
Database-backed ingestion worker for handling document ingestion jobs.

This replaces the in-memory job storage with persistent database tracking.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import UUID
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

try:
    from .docling_document_worker import DoclingDocumentWorker
    from .unified_document_worker import UnifiedDocumentWorker
    from ..embeddings import EmbeddingService
    from ..rag.vector_store import VectorStore
    from ..processors.unified_document_processor import GPTModel
except ImportError:
    # Fallback for when running as script
    from workers.docling_document_worker import DoclingDocumentWorker
    from workers.unified_document_worker import UnifiedDocumentWorker
    from embeddings import EmbeddingService
    from rag.vector_store import VectorStore
    from processors.unified_document_processor import GPTModel

# Import database components
from shared_database import (
    DocumentProcessingService, 
    LoggingService,
    ProcessingStatus, 
    ProcessorType
)

logger = logging.getLogger(__name__)


class DatabaseIngestionWorker:
    """Database-backed worker for managing document ingestion jobs."""
    
    def __init__(
        self, 
        db_session: AsyncSession,
        embedding_service: EmbeddingService, 
        vector_store: VectorStore,
        openai_api_key: str,
        gpt_model: GPTModel = GPTModel.GPT_4O,
        use_unified_worker: bool = True
    ):
        self.db_session = db_session
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        self.openai_api_key = openai_api_key
        self.gpt_model = gpt_model
        
        # Initialize services
        self.db_service = DocumentProcessingService(db_session)
        self.logging_service = LoggingService(db_session)
        
        # Initialize document worker
        if use_unified_worker:
            self.document_worker = UnifiedDocumentWorker(
                embedding_service=embedding_service,
                vector_store=vector_store,
                openai_api_key=openai_api_key,
                gpt_model=gpt_model
            )
        else:
            self.document_worker = DoclingDocumentWorker(embedding_service, vector_store)
    
    async def create_job(
        self, 
        file_paths: List[str], 
        collection_name: str = "knowledge_base",
        metadata: Optional[Dict[str, Any]] = None,
        created_by: Optional[str] = None,
        priority: int = 0
    ) -> UUID:
        """Create a new ingestion job in the database."""
        try:
            # Create job in database
            job = await self.db_service.create_ingestion_job(
                collection_name=collection_name,
                file_paths=file_paths,
                metadata=metadata,
                processing_options={
                    "gpt_model": self.gpt_model.value,
                    "use_unified_worker": True,
                    "embedding_model": "mxbai-embed-large"
                },
                created_by=created_by,
                priority=priority
            )
            
            # Log job creation
            await self.logging_service.log_processing_event(
                level="INFO",
                message=f"Created ingestion job for {len(file_paths)} files",
                ingestion_job_id=job.id,
                processor_type="ingestion_worker",
                processing_stage="job_creation",
                details={
                    "file_count": len(file_paths),
                    "collection_name": collection_name,
                    "priority": priority
                }
            )
            
            logger.info(f"Created database job {job.id} for {len(file_paths)} files")
            return job.id
            
        except Exception as e:
            logger.error(f"Error creating job: {e}")
            await self.logging_service.log_processing_event(
                level="ERROR",
                message=f"Failed to create ingestion job: {str(e)}",
                processor_type="ingestion_worker",
                processing_stage="job_creation",
                details={"error": str(e)}
            )
            raise
    
    async def process_job(self, job_id: UUID) -> Dict[str, Any]:
        """Process an ingestion job using database tracking."""
        try:
            # Get job from database
            job = await self.db_service.get_ingestion_job(job_id)
            if not job:
                raise ValueError(f"Job {job_id} not found in database")
            
            # Update job status to processing
            await self.db_service.update_ingestion_job_status(
                job_id=job_id,
                status=ProcessingStatus.PROCESSING
            )
            
            # Log job start
            await self.logging_service.log_processing_event(
                level="INFO",
                message=f"Started processing job with {len(job.documents)} documents",
                ingestion_job_id=job_id,
                processor_type="ingestion_worker",
                processing_stage="job_start"
            )
            
            logger.info(f"Processing database job {job_id}")
            
            # Process each document
            successful_documents = 0
            failed_documents = 0
            total_chunks = 0
            
            for document in job.documents:
                try:
                    # Log document processing start
                    await self.logging_service.log_processing_event(
                        level="INFO",
                        message=f"Started processing document: {document.file_name}",
                        ingestion_job_id=job_id,
                        document_id=document.id,
                        processor_type="document_worker",
                        processing_stage="document_start"
                    )
                    
                    # Process document
                    result = await self.document_worker.process_document(
                        file_path=Path(document.file_path),
                        collection_name=document.collection_name,
                        metadata=document.job_metadata or {}
                    )
                    
                    # Determine processor type from result
                    processor_type = ProcessorType.DOCLING
                    if result.get("processor", "").startswith("gpt_"):
                        processor_type = ProcessorType.GPT_4O  # Default to GPT_4O
                    
                    # Update document in database
                    await self.db_service.update_document_processing_result(
                        document_id=document.id,
                        status=ProcessingStatus.COMPLETED if result.get("success", False) else ProcessingStatus.FAILED,
                        processing_metadata=result.get("metadata", {}),
                        structured_elements=result.get("structured_elements"),
                        page_statistics=result.get("page_statistics"),
                        vector_point_ids=result.get("vector_point_ids"),
                        total_chunks_created=result.get("chunks_created", 0),
                        total_points_stored=result.get("points_stored", 0),
                        processing_duration_seconds=result.get("processing_duration"),
                        token_usage=result.get("token_usage"),
                        model_used=result.get("model"),
                        error_message=result.get("error") if not result.get("success", False) else None
                    )
                    
                    if result.get("success", False):
                        successful_documents += 1
                        total_chunks += result.get("chunks_created", 0)
                        
                        # Log successful processing
                        await self.logging_service.log_processing_event(
                            level="INFO",
                            message=f"Successfully processed document: {document.file_name}",
                            ingestion_job_id=job_id,
                            document_id=document.id,
                            processor_type=processor_type.value,
                            processing_stage="document_complete",
                            details={
                                "chunks_created": result.get("chunks_created", 0),
                                "points_stored": result.get("points_stored", 0),
                                "processing_time": result.get("processing_duration")
                            }
                        )
                    else:
                        failed_documents += 1
                        
                        # Log failed processing
                        await self.logging_service.log_processing_event(
                            level="ERROR",
                            message=f"Failed to process document: {document.file_name}",
                            ingestion_job_id=job_id,
                            document_id=document.id,
                            processor_type=processor_type.value,
                            processing_stage="document_failed",
                            details={"error": result.get("error")}
                        )
                    
                except Exception as e:
                    failed_documents += 1
                    logger.error(f"Error processing document {document.file_name} in job {job_id}: {e}")
                    
                    # Update document status to failed
                    await self.db_service.update_document_processing_result(
                        document_id=document.id,
                        status=ProcessingStatus.FAILED,
                        error_message=str(e),
                        error_details={"exception": str(e)}
                    )
                    
                    # Log error
                    await self.logging_service.log_processing_event(
                        level="ERROR",
                        message=f"Exception processing document: {document.file_name}",
                        ingestion_job_id=job_id,
                        document_id=document.id,
                        processor_type="document_worker",
                        processing_stage="document_exception",
                        details={"error": str(e)}
                    )
            
            # Update job summary
            await self.db_service.update_ingestion_job_summary(
                job_id=job_id,
                successful_files=successful_documents,
                failed_files=failed_documents,
                total_chunks_created=total_chunks
            )
            
            # Update job status to completed
            await self.db_service.update_ingestion_job_status(
                job_id=job_id,
                status=ProcessingStatus.COMPLETED
            )
            
            # Log job completion
            await self.logging_service.log_processing_event(
                level="INFO",
                message=f"Completed job: {successful_documents}/{len(job.documents)} documents processed successfully",
                ingestion_job_id=job_id,
                processor_type="ingestion_worker",
                processing_stage="job_complete",
                details={
                    "successful_documents": successful_documents,
                    "failed_documents": failed_documents,
                    "total_chunks": total_chunks
                }
            )
            
            logger.info(f"Completed database job {job_id}: {successful_documents}/{len(job.documents)} documents processed, {total_chunks} chunks created")
            
            # Return job summary
            return {
                "job_id": str(job_id),
                "status": "completed",
                "successful_documents": successful_documents,
                "failed_documents": failed_documents,
                "total_chunks": total_chunks,
                "collection_name": job.collection_name
            }
            
        except Exception as e:
            logger.error(f"Error processing database job {job_id}: {e}")
            
            # Update job status to failed
            await self.db_service.update_ingestion_job_status(
                job_id=job_id,
                status=ProcessingStatus.FAILED,
                error_message=str(e),
                error_details={"exception": str(e)}
            )
            
            # Log job failure
            await self.logging_service.log_processing_event(
                level="ERROR",
                message=f"Job processing failed: {str(e)}",
                ingestion_job_id=job_id,
                processor_type="ingestion_worker",
                processing_stage="job_failed",
                details={"error": str(e)}
            )
            
            raise
    
    async def get_job_status(self, job_id: UUID) -> Optional[Dict[str, Any]]:
        """Get the status of a job from database."""
        try:
            job = await self.db_service.get_ingestion_job(job_id)
            if not job:
                return None
            
            return {
                "id": str(job.id),
                "collection_name": job.collection_name,
                "status": job.status,
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                "total_files": job.total_files,
                "successful_files": job.successful_files,
                "failed_files": job.failed_files,
                "total_chunks_created": job.total_chunks_created,
                "error_message": job.error_message,
                "documents": [
                    {
                        "id": str(doc.id),
                        "file_name": doc.file_name,
                        "status": doc.status,
                        "processor_type": doc.processor_type,
                        "total_chunks_created": doc.total_chunks_created,
                        "error_message": doc.error_message
                    }
                    for doc in job.documents
                ]
            }
        except Exception as e:
            logger.error(f"Error getting job status {job_id}: {e}")
            return None
    
    async def list_jobs(
        self, 
        status: Optional[ProcessingStatus] = None,
        collection_name: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List jobs from database with optional filters."""
        try:
            jobs = await self.db_service.list_jobs(
                status=status,
                collection_name=collection_name,
                limit=limit,
                offset=offset
            )
            
            return [
                {
                    "id": str(job.id),
                    "collection_name": job.collection_name,
                    "status": job.status,
                    "created_at": job.created_at.isoformat() if job.created_at else None,
                    "started_at": job.started_at.isoformat() if job.started_at else None,
                    "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                    "total_files": job.total_files,
                    "successful_files": job.successful_files,
                    "failed_files": job.failed_files,
                    "total_chunks_created": job.total_chunks_created,
                    "error_message": job.error_message
                }
                for job in jobs
            ]
        except Exception as e:
            logger.error(f"Error listing jobs: {e}")
            return []
    
    async def get_processing_statistics(self) -> Dict[str, Any]:
        """Get processing statistics from database."""
        try:
            return await self.db_service.get_processing_statistics()
        except Exception as e:
            logger.error(f"Error getting processing statistics: {e}")
            return {}
    
    async def process_job_async(self, job_id: UUID):
        """Process a job asynchronously (for background tasks)."""
        try:
            await self.process_job(job_id)
        except Exception as e:
            logger.error(f"Error in async job processing {job_id}: {e}")


