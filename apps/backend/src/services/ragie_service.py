"""
Simplified Ragie service layer for document management and retrieval.

This service provides business logic for interacting with Ragie API,
with simplified error handling using direct exceptions instead of Result wrappers.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

from ..adapters.ragie_client import RagieClient, RagieError, RagieNotFoundError
from ..models.ragie import (
    RagieDocument,
    RagieDocumentList,
    RagieRetrievalResult
)
from .s3_service import S3Service, S3ServiceError

logger = logging.getLogger(__name__)


class RagieServiceError(Exception):
    """Base exception for Ragie service errors."""
    pass


class UnsupportedFileTypeError(RagieServiceError):
    """File type not supported."""
    pass


class FileTooLargeError(RagieServiceError):
    """File size exceeds maximum limit."""
    pass


class RagieService:
    """
    Simplified service layer for Ragie document management and retrieval operations.
    
    Uses direct exceptions instead of Result wrappers for cleaner code.
    """
    
    # Supported file types (PDFs, images, PPTs, DocX, Excel)
    SUPPORTED_EXTENSIONS = {
        '.pdf',
        '.ppt', '.pptx',
        '.doc', '.docx', 
        '.xls', '.xlsx',
        '.jpg', '.jpeg', '.png', '.gif'
    }
    
    # Maximum file size (50MB)
    MAX_FILE_SIZE = 50 * 1024 * 1024
    
    def __init__(self, ragie_client: RagieClient, ragie_s3_service: Optional[S3Service] = None, redis_service=None):
        """
        Initialize the Ragie service.
        
        Args:
            ragie_client: Configured Ragie API client
            ragie_s3_service: Optional S3 service for URL-based uploads
            redis_service: Optional Redis service for caching
        """
        self.ragie_client = ragie_client
        self.ragie_s3_service = ragie_s3_service
        self.redis_service = redis_service
        self.use_s3_upload = ragie_s3_service is not None
    
    def _validate_file(self, file_content: bytes, filename: str) -> None:
        """
        Validate file type and size.
        
        Args:
            file_content: File content bytes
            filename: Original filename
            
        Raises:
            UnsupportedFileTypeError: If file type is not supported
            FileTooLargeError: If file size exceeds limit
        """
        # Check file type
        file_path = Path(filename)
        if file_path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            raise UnsupportedFileTypeError(
                f"File type '{file_path.suffix}' not supported. "
                f"Supported types: {', '.join(sorted(self.SUPPORTED_EXTENSIONS))}"
            )
        
        # Check file size
        if len(file_content) > self.MAX_FILE_SIZE:
            raise FileTooLargeError(
                f"File size {len(file_content)} bytes exceeds maximum of {self.MAX_FILE_SIZE} bytes"
            )
    
    async def upload_document(
        self,
        file_content: bytes,
        filename: str,
        organization_id: str,
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None,
        upload_id: Optional[str] = None
    ) -> RagieDocument:
        """
        Upload a document to Ragie for processing and indexing.
        
        Args:
            file_content: Document file content as bytes
            filename: Original filename
            organization_id: Organization ID (used as partition)
            user_id: User ID for tracking
            metadata: Optional metadata dictionary
            upload_id: Optional upload ID for progress tracking
            
        Returns:
            RagieDocument: The uploaded document information
            
        Raises:
            UnsupportedFileTypeError: If file type is not supported
            FileTooLargeError: If file size exceeds limit
            RagieServiceError: If upload fails
        """
        try:
            # Validate file
            self._validate_file(file_content, filename)
            
            logger.info(
                f"Starting document upload file_name={filename} org_id={organization_id} "
                f"user_id={user_id} size_bytes={len(file_content)} "
                f"upload_method={'s3_url' if self.use_s3_upload else 'direct_upload'}"
            )
            
            if self.use_s3_upload and self.ragie_s3_service:
                # Use S3 + URL approach (preferred)
                logger.info(
                    f"Using S3+URL upload method file_name={filename} org_id={organization_id} user_id={user_id}"
                )
                document, s3_url = await self.ragie_s3_service.upload_document_for_ragie(
                    file_content=file_content,
                    filename=filename,
                    organization_id=organization_id,
                    user_id=user_id,
                    metadata=metadata or {},
                    upload_id=upload_id
                )
                
                logger.info(
                    f"Document uploaded via S3+URL successfully doc_id={document.id} "
                    f"file_name={filename} org_id={organization_id} user_id={user_id} "
                    f"s3_url={(s3_url[:100] + '...') if len(s3_url) > 100 else s3_url}"
                )
            else:
                # Fallback to direct upload
                logger.info(
                    f"Using direct upload method (fallback) file_name={filename} org_id={organization_id} user_id={user_id}"
                )
                document = await self.ragie_client.upload_document(
                    file_content=file_content,
                    filename=filename,
                    partition=organization_id,
                    metadata=metadata or {}
                )
                
                logger.info(
                    f"Document uploaded directly successfully doc_id={document.id} "
                    f"file_name={filename} org_id={organization_id} user_id={user_id}"
                )
            
            return document
            
        except (UnsupportedFileTypeError, FileTooLargeError):
            raise
        except (RagieError, S3ServiceError) as e:
            logger.error("Ragie/S3 API error during upload", extra={
                "file_name": filename,
                "organization_id": organization_id,
                "user_id": user_id,
                "error": str(e),
                "error_type": type(e).__name__,
                "upload_method": "s3_url" if self.use_s3_upload else "direct_upload"
            })
            raise RagieServiceError(f"Upload failed: {e}")
        except Exception as e:
            logger.error("Unexpected error during upload", extra={
                "file_name": filename,
                "organization_id": organization_id,
                "user_id": user_id,
                "error": str(e),
                "error_type": type(e).__name__,
                "upload_method": "s3_url" if self.use_s3_upload else "direct_upload"
            })
            raise RagieServiceError(f"Unexpected upload error: {e}")
    
    async def list_documents(
        self,
        organization_id: str,
        limit: int = 20,
        cursor: Optional[str] = None
    ) -> RagieDocumentList:
        """
        List documents for an organization.
        
        Args:
            organization_id: Organization ID (partition)
            limit: Maximum number of documents to return
            cursor: Pagination cursor
            
        Returns:
            RagieDocumentList: List of documents with pagination info
            
        Raises:
            RagieServiceError: If listing fails
        """
        try:
            logger.info("Listing documents", extra={
                "organization_id": organization_id,
                "limit": limit
            })
            
            document_list = await self.ragie_client.list_documents(
                partition=organization_id,
                limit=limit,
                cursor=cursor
            )
            
            logger.info("Documents listed successfully", extra={
                "organization_id": organization_id,
                "document_count": len(document_list.documents)
            })
            
            return document_list
            
        except RagieError as e:
            logger.error("Ragie API error during listing", extra={
                "organization_id": organization_id,
                "error": str(e)
            })
            raise RagieServiceError(f"Listing failed: {e}")
        except Exception as e:
            logger.error("Unexpected error during listing", extra={
                "organization_id": organization_id,
                "error": str(e)
            })
            raise RagieServiceError(f"Unexpected listing error: {e}")
    
    async def get_document(
        self,
        document_id: str,
        organization_id: str
    ) -> RagieDocument:
        """
        Get a specific document by ID.
        
        Args:
            document_id: Document ID
            organization_id: Organization ID (partition)
            
        Returns:
            RagieDocument: Document information
            
        Raises:
            RagieServiceError: If document not found or retrieval fails
        """
        try:
            logger.info("Getting document", extra={
                "document_id": document_id,
                "organization_id": organization_id
            })
            
            document = await self.ragie_client.get_document(
                document_id=document_id,
                partition=organization_id
            )
            
            logger.info("Document retrieved successfully", extra={
                "document_id": document_id,
                "organization_id": organization_id
            })
            
            return document
            
        except RagieNotFoundError as e:
            logger.warning("Document not found", extra={
                "document_id": document_id,
                "organization_id": organization_id
            })
            raise RagieServiceError(f"Document not found: {document_id}")
        except RagieError as e:
            logger.error("Ragie API error during get", extra={
                "document_id": document_id,
                "organization_id": organization_id,
                "error": str(e)
            })
            raise RagieServiceError(f"Get failed: {e}")
        except Exception as e:
            logger.error("Unexpected error during get", extra={
                "document_id": document_id,
                "organization_id": organization_id,
                "error": str(e)
            })
            raise RagieServiceError(f"Unexpected get error: {e}")
    
    async def delete_document(
        self,
        document_id: str,
        organization_id: str
    ) -> None:
        """
        Delete a document from Ragie.
        
        Args:
            document_id: Document ID
            organization_id: Organization ID (partition)
            
        Raises:
            RagieServiceError: If document not found or deletion fails
        """
        try:
            logger.info("Deleting document", extra={
                "document_id": document_id,
                "organization_id": organization_id
            })
            
            await self.ragie_client.delete_document(
                document_id=document_id,
                partition=organization_id
            )
            
            logger.info("Document deleted successfully", extra={
                "document_id": document_id,
                "organization_id": organization_id
            })
            
        except RagieNotFoundError as e:
            logger.warning("Document not found for deletion", extra={
                "document_id": document_id,
                "organization_id": organization_id
            })
            raise RagieServiceError(f"Document not found: {document_id}")
        except RagieError as e:
            logger.error("Ragie API error during deletion", extra={
                "document_id": document_id,
                "organization_id": organization_id,
                "error": str(e)
            })
            raise RagieServiceError(f"Deletion failed: {e}")
        except Exception as e:
            logger.error("Unexpected error during deletion", extra={
                "document_id": document_id,
                "organization_id": organization_id,
                "error": str(e)
            })
            raise RagieServiceError(f"Unexpected deletion error: {e}")
    
    async def update_document_metadata(
        self,
        document_id: str,
        organization_id: str,
        metadata: Dict[str, Any]
    ) -> RagieDocument:
        """
        Update document metadata/tags.
        
        Args:
            document_id: Document ID
            organization_id: Organization ID (partition)
            metadata: Updated metadata dictionary
            
        Returns:
            RagieDocument: Updated document information
            
        Raises:
            RagieServiceError: If document not found or update fails
        """
        try:
            logger.info("Updating document metadata", extra={
                "document_id": document_id,
                "organization_id": organization_id,
                "metadata_keys": list(metadata.keys())
            })
            
            document = await self.ragie_client.patch_document_metadata(
                document_id=document_id,
                partition=organization_id,
                metadata=metadata
            )
            
            logger.info("Document metadata updated successfully", extra={
                "document_id": document_id,
                "organization_id": organization_id
            })
            
            return document
            
        except RagieNotFoundError as e:
            logger.warning("Document not found for metadata update", extra={
                "document_id": document_id,
                "organization_id": organization_id
            })
            raise RagieServiceError(f"Document not found: {document_id}")
        except RagieError as e:
            logger.error("Ragie API error during metadata update", extra={
                "document_id": document_id,
                "organization_id": organization_id,
                "error": str(e)
            })
            raise RagieServiceError(f"Metadata update failed: {e}")
        except Exception as e:
            logger.error("Unexpected error during metadata update", extra={
                "document_id": document_id,
                "organization_id": organization_id,
                "error": str(e)
            })
            raise RagieServiceError(f"Unexpected metadata update error: {e}")
    
    async def retrieve_chunks(
        self,
        query: str,
        organization_id: str,
        max_chunks: int = 15,
        document_ids: Optional[List[str]] = None,
        metadata_filter: Optional[Dict[str, Any]] = None,
        min_score: Optional[float] = None,
        rerank: bool = True,  # Changed default to True for better quality
        max_chunks_per_document: Optional[int] = None,  # NEW: Enforce document diversity
        recency_bias: bool = False,  # NEW: Time-sensitive queries
        use_cache: bool = True  # NEW: Cache repeated queries
    ) -> RagieRetrievalResult:
        """
        Retrieve relevant document chunks for RAG with advanced features.
        
        Args:
            query: Search query
            organization_id: Organization ID (partition)
            max_chunks: Maximum number of chunks to return (adaptive based on query)
            document_ids: Optional list of document IDs to filter by (not supported directly; use metadata filter)
            metadata_filter: Optional metadata filters supporting $eq, $ne, $gt, $gte, $lt, $lte, $in, $nin
            min_score: Optional minimum relevance score threshold (0.0-1.0)
            rerank: Enable reranking for higher relevance (default: True)
            max_chunks_per_document: Max chunks per document (ensures diversity)
            recency_bias: Favor recent documents (useful for news, updates, etc.)
            use_cache: Enable Redis caching for repeated queries (default: True)
            
        Returns:
            RagieRetrievalResult: Retrieval results with scored chunks
            
        Raises:
            RagieServiceError: If retrieval fails
            
        Examples:
            # Basic retrieval with caching and reranking
            result = await service.retrieve_chunks(
                query="What are our Q4 goals?",
                organization_id="acme_corp"
            )
            
            # Time-sensitive query with recency bias
            result = await service.retrieve_chunks(
                query="Latest product announcements",
                organization_id="acme_corp",
                recency_bias=True,
                min_score=0.7
            )
            
            # Diverse retrieval with document cap
            result = await service.retrieve_chunks(
                query="Engineering best practices",
                organization_id="acme_corp",
                max_chunks=30,
                max_chunks_per_document=3,  # Max 3 chunks per doc
                metadata_filter={"department": {"$eq": "engineering"}}
            )
        """
        try:
            # Generate cache key
            cache_key = None
            if use_cache and self.redis_service:
                import hashlib
                cache_params = f"{query}:{organization_id}:{max_chunks}:{rerank}:{recency_bias}"
                if metadata_filter:
                    cache_params += f":{str(metadata_filter)}"
                cache_hash = hashlib.sha256(cache_params.encode()).hexdigest()[:16]
                cache_key = f"retrieval:{organization_id}:{cache_hash}"
                
                # Try cache first
                try:
                    cached = await self.redis_service.get(cache_key)
                    if cached:
                        logger.info("Cache hit for retrieval", extra={"cache_key": cache_key})
                        return RagieRetrievalResult(**cached)
                except Exception as e:
                    logger.warning(f"Cache lookup failed: {e}")
            
            logger.info("Retrieving chunks from Ragie",
                       extra={
                           "query": query[:100] + "..." if len(query) > 100 else query,
                           "organization_id": organization_id,
                           "max_chunks": max_chunks,
                           "rerank": rerank,
                           "recency_bias": recency_bias,
                           "max_chunks_per_doc": max_chunks_per_document,
                           "has_filter": bool(metadata_filter),
                           "use_cache": use_cache
                       })
            
            result = await self.ragie_client.retrieve_chunks(
                query=query,
                partition=organization_id,
                max_chunks=max_chunks,
                metadata_filter=metadata_filter,
                rerank=rerank,
                max_chunks_per_document=max_chunks_per_document,
                recency_bias=recency_bias,
                min_score_threshold=min_score or 0.0
            )
            
            # Cache successful results
            if use_cache and cache_key and self.redis_service:
                try:
                    # Cache for 5 minutes
                    await self.redis_service.set(
                        cache_key, 
                        result.model_dump(),
                        ttl_seconds=300
                    )
                except Exception as e:
                    logger.warning(f"Cache storage failed: {e}")
            
            # Log retrieval quality metrics
            if hasattr(result, "scored_chunks") and result.scored_chunks:
                scores = [chunk.score for chunk in result.scored_chunks]
                unique_docs = len(set(c.document_id for c in result.scored_chunks))
                logger.info(
                    "Retrieval completed",
                    extra={
                        "chunk_count": len(result.scored_chunks),
                        "avg_score": sum(scores) / len(scores),
                        "min_score": min(scores),
                        "max_score": max(scores),
                        "unique_docs": unique_docs,
                        "diversity_ratio": unique_docs / len(result.scored_chunks) if result.scored_chunks else 0
                    }
                )
            
            return result
            
        except RagieError as e:
            logger.error("Ragie API error during retrieval", extra={
                "organization_id": organization_id,
                "query": query[:100],
                "error": str(e)
            })
            raise RagieServiceError(f"Retrieval failed: {e}")
        except Exception as e:
            logger.error("Unexpected error during retrieval", extra={
                "organization_id": organization_id,
                "query": query[:100],
                "error": str(e)
            })
            raise RagieServiceError(f"Unexpected retrieval error: {e}")
    
    async def get_document_source(
        self,
        document_id: str,
        organization_id: str
    ) -> Dict[str, Any]:
        """
        Get the original source file of a document.
        
        Args:
            document_id: Document ID
            organization_id: Organization ID (partition)
            
        Returns:
            Dict containing 'content' (bytes) and 'content_type' (str)
            
        Raises:
            RagieServiceError: If document not found or source retrieval fails
        """
        try:
            logger.info("Getting document source", extra={
                "document_id": document_id,
                "organization_id": organization_id
            })
            
            source_data = await self.ragie_client.get_document_source(
                document_id=document_id,
                partition=organization_id
            )
            
            logger.info("Document source retrieved successfully", extra={
                "document_id": document_id,
                "organization_id": organization_id,
                "content_type": source_data.get("content_type", "unknown")
            })
            
            return source_data
            
        except RagieNotFoundError as e:
            logger.warning("Document source not found", extra={
                "document_id": document_id,
                "organization_id": organization_id
            })
            raise RagieServiceError(f"Document source not found: {document_id}")
        except RagieError as e:
            logger.error("Ragie API error during source retrieval", extra={
                "document_id": document_id,
                "organization_id": organization_id,
                "error": str(e)
            })
            raise RagieServiceError(f"Source retrieval failed: {e}")
        except Exception as e:
            logger.error("Unexpected error during source retrieval", extra={
                "document_id": document_id,
                "organization_id": organization_id,
                "error": str(e)
            })
            raise RagieServiceError(f"Unexpected source retrieval error: {e}")
