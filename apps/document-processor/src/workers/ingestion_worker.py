"""
Ingestion worker for handling document ingestion jobs.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

try:
    from .docling_document_worker import DoclingDocumentWorker
    from ..embeddings import EmbeddingService
    from ..rag.vector_store import VectorStore
except ImportError:
    # Fallback for when running as script
    from workers.docling_document_worker import DoclingDocumentWorker
    from embeddings import EmbeddingService
    from rag.vector_store import VectorStore

logger = logging.getLogger(__name__)


class IngestionWorker:
    """Worker for managing document ingestion jobs."""
    
    def __init__(self, embedding_service: EmbeddingService, vector_store: VectorStore):
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        self.document_worker = DoclingDocumentWorker(embedding_service, vector_store)
        self.jobs = {}  # In-memory job storage (in production, use Redis or database)
    
    def create_job(
        self, 
        file_paths: List[str], 
        collection_name: str = "knowledge_base",
        metadata: Dict[str, Any] = None
    ) -> str:
        """Create a new ingestion job."""
        job_id = str(uuid.uuid4())
        
        self.jobs[job_id] = {
            "id": job_id,
            "file_paths": file_paths,
            "collection_name": collection_name,
            "metadata": metadata or {},
            "status": "pending",
            "created_at": datetime.utcnow().isoformat(),
            "results": [],
            "error": None
        }
        
        logger.info(f"Created ingestion job {job_id} for {len(file_paths)} files")
        return job_id
    
    async def process_job(self, job_id: str) -> Dict[str, Any]:
        """Process an ingestion job."""
        if job_id not in self.jobs:
            raise ValueError(f"Job {job_id} not found")
        
        job = self.jobs[job_id]
        job["status"] = "processing"
        job["started_at"] = datetime.utcnow().isoformat()
        
        try:
            logger.info(f"Processing job {job_id}")
            
            # Process each document
            results = []
            for file_path in job["file_paths"]:
                try:
                    result = await self.document_worker.process_document(
                        file_path=file_path,
                        collection_name=job["collection_name"],
                        metadata=job["metadata"]
                    )
                    results.append(result)
                except Exception as e:
                    logger.error(f"Error processing file {file_path} in job {job_id}: {e}")
                    results.append({
                        "success": False,
                        "file_path": file_path,
                        "error": str(e)
                    })
            
            job["results"] = results
            job["status"] = "completed"
            job["completed_at"] = datetime.utcnow().isoformat()
            
            # Calculate summary
            successful = sum(1 for r in results if r.get("success", False))
            total_chunks = sum(r.get("chunks_processed", 0) for r in results if r.get("success", False))
            
            job["summary"] = {
                "total_files": len(file_paths),
                "successful_files": successful,
                "failed_files": len(file_paths) - successful,
                "total_chunks": total_chunks
            }
            
            logger.info(f"Completed job {job_id}: {successful}/{len(file_paths)} files processed, {total_chunks} chunks ingested")
            
            return job
            
        except Exception as e:
            logger.error(f"Error processing job {job_id}: {e}")
            job["status"] = "failed"
            job["error"] = str(e)
            job["failed_at"] = datetime.utcnow().isoformat()
            raise
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a job."""
        return self.jobs.get(job_id)
    
    def list_jobs(self, status: str = None) -> List[Dict[str, Any]]:
        """List all jobs, optionally filtered by status."""
        jobs = list(self.jobs.values())
        if status:
            jobs = [job for job in jobs if job["status"] == status]
        return jobs
    
    async def process_job_async(self, job_id: str):
        """Process a job asynchronously (for background tasks)."""
        try:
            await self.process_job(job_id)
        except Exception as e:
            logger.error(f"Error in async job processing {job_id}: {e}")
