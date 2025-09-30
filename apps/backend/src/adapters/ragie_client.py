"""
Ragie API HTTP client.

This client handles all interactions with the Ragie API including
document management, metadata updates, and chunk retrieval for RAG.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Any
import httpx
from datetime import datetime

from ..models.ragie import (
    RagieDocument,
    RagieDocumentList,
    RagieRetrievalResult,
    RagieChunk,
    RagieDocumentStatus,
    RagieErrorResponse
)

logger = logging.getLogger(__name__)


class RagieError(Exception):
    """Base exception for Ragie API errors."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data or {}


class RagieAuthError(RagieError):
    """Authentication error with Ragie API."""
    pass


class RagieNotFoundError(RagieError):
    """Resource not found error."""
    pass


class RagieValidationError(RagieError):
    """Validation error for request data."""
    pass


class RagieClient:
    """
    HTTP client for Ragie API operations.
    
    Handles authentication, request/response processing, error handling,
    and retry logic for all Ragie API interactions.
    """
    
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.ragie.ai",
        timeout: float = 30.0,
        max_retries: int = 3
    ):
        """
        Initialize Ragie client.
        
        Args:
            api_key: Ragie API key for authentication
            base_url: Base URL for Ragie API
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            
        Raises:
            ValueError: If api_key or base_url is empty
        """
        if not api_key:
            raise ValueError("API key is required")
        if not base_url:
            raise ValueError("Base URL is required")
            
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        
        # Create HTTP client with default headers
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "User-Agent": "AI-Knowledge-Agent/1.0"
            }
        )
        
        logger.info("Initialized Ragie client", extra={
            "base_url": base_url,
            "timeout": timeout,
            "max_retries": max_retries
        })
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    def _get_headers(self, partition: str) -> Dict[str, str]:
        """
        Get request headers with partition.
        
        Args:
            partition: Organization partition for request scoping
            
        Returns:
            Headers dictionary with authentication and partition
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Add partition header if provided
        if partition:
            headers["partition"] = partition
            
        return headers
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        partition: str,
        json_data: Optional[Dict] = None,
        files: Optional[Dict] = None,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None
    ) -> httpx.Response:
        """
        Make HTTP request with basic error handling.
        
        NOTE: Retry logic and fallback mechanisms are not implemented yet.
        Errors are logged but not retried automatically.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            partition: Organization partition
            json_data: JSON request body
            files: File upload data
            params: Query parameters
            
        Returns:
            HTTP response object
            
        Raises:
            RagieError: For various API errors
        """
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers(partition)
        
        # Remove Content-Type for file uploads
        if files:
            headers.pop("Content-Type", None)
        
        try:
            logger.info(f"🌐 Making {method} request to Ragie API", extra={
                "url": url,
                "partition": partition,
                "has_files": bool(files),
                "has_json": bool(json_data),
                "has_params": bool(params),
                "has_data": bool(data),
                "headers": {k: v for k, v in headers.items() if k.lower() != 'authorization'},  # Don't log auth header
                "json_payload": json_data,
                "request_details": {
                    "method": method,
                    "endpoint": url,
                    "content_type": headers.get("Content-Type"),
                    "has_auth": "Authorization" in headers
                }
            })
            
            response = await self.client.request(
                method=method,
                url=url,
                headers=headers,
                json=json_data,
                files=files,
                params=params,
                data=data
            )
            
            logger.info(f"📡 Ragie API response", extra={
                "status_code": response.status_code,
                "response_headers": dict(response.headers),
                "content_length": len(response.content),
                "url": url
            })
            
            # Handle successful responses
            if response.status_code < 400:
                return response
            
            # Handle client errors (4xx)
            if 400 <= response.status_code < 500:
                await self._handle_client_error(response)
            
            # Handle server errors (5xx)
            if response.status_code >= 500:
                await self._handle_server_error(response)
                
        except httpx.TimeoutException as e:
            logger.error("Ragie API request timeout", extra={
                "url": url,
                "method": method,
                "partition": partition,
                "error": str(e)
            })
            raise RagieError(f"Request timeout: {str(e)}")
        
        except Exception as e:
            logger.error("Unexpected error in Ragie API request", extra={
                "url": url,
                "method": method,
                "partition": partition,
                "error": str(e),
                "error_type": type(e).__name__
            })
            raise RagieError(f"Unexpected error: {str(e)}")
        
        # Should never reach here
        raise RagieError("Unhandled response")
    
    async def _handle_client_error(self, response: httpx.Response) -> None:
        """Handle 4xx client errors."""
        try:
            error_data = response.json()
            error_msg = error_data.get("error", f"HTTP {response.status_code}")
        except Exception:
            error_data = {}
            error_msg = f"HTTP {response.status_code}"
        
        logger.error(f"❌ Ragie API client error", extra={
            "status_code": response.status_code,
            "error_message": error_msg,
            "error_data": error_data,
            "response_text": response.text[:500] if hasattr(response, 'text') else "no text",
            "url": str(response.url)
        })
        
        if response.status_code == 401:
            raise RagieAuthError(error_msg, response.status_code, error_data)
        elif response.status_code == 404:
            raise RagieNotFoundError(error_msg, response.status_code, error_data)
        elif response.status_code == 422:
            raise RagieValidationError(error_msg, response.status_code, error_data)
        else:
            raise RagieError(error_msg, response.status_code, error_data)
    
    async def _handle_server_error(self, response: httpx.Response) -> None:
        """Handle 5xx server errors."""
        try:
            error_data = response.json()
            error_msg = error_data.get("error", f"Server error: HTTP {response.status_code}")
        except Exception:
            error_data = {}
            error_msg = f"Server error: HTTP {response.status_code}"
        
        logger.error(f"🔥 Ragie API server error", extra={
            "status_code": response.status_code,
            "error_message": error_msg,
            "error_data": error_data,
            "response_text": response.text[:500] if hasattr(response, 'text') else "no text",
            "url": str(response.url)
        })
        
        raise RagieError(error_msg, response.status_code, error_data)
    
    async def upload_document(
        self,
        file_content: bytes,
        filename: str,
        partition: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> RagieDocument:
        """
        Upload a document to Ragie.
        
        Args:
            file_content: Binary file content
            filename: Original filename
            partition: Organization partition
            metadata: Optional document metadata
            
        Returns:
            Created document information
            
        Raises:
            RagieError: If upload fails
        """
        # Determine content type based on file extension
        import mimetypes
        content_type, _ = mimetypes.guess_type(filename)
        if not content_type:
            content_type = 'application/octet-stream'
        
        logger.info("Uploading document to Ragie", extra={
            "file_name": filename,
            "partition": partition,
            "file_size": len(file_content),
            "has_metadata": bool(metadata),
            "metadata_keys": list(metadata.keys()) if metadata else None,
            "content_type": content_type
        })
        
        files = {
            "file": (filename, file_content, content_type)
        }
        
        # Add metadata as form data if provided (must be JSON string)
        data = {}
        if metadata:
            import json
            data["metadata"] = json.dumps(metadata)
            logger.info("Adding metadata to request", extra={
                "metadata_json": data["metadata"],
                "metadata_length": len(data["metadata"])
            })
        
        try:
            response = await self._make_request(
                method="POST",
                endpoint="/documents",
                partition=partition,
                files=files,
                data=data  # Pass form data along with files
            )
            
            logger.info(f"🌐 Ragie API response received", extra={
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "response_size": len(response.content)
            })
            
            document_data = response.json()
            
            logger.info(f"📄 Ragie document data", extra={
                "raw_response": document_data,
                "response_keys": list(document_data.keys()) if isinstance(document_data, dict) else "non-dict"
            })
            
            document = self._parse_document(document_data)
            
            logger.info("✅ Document uploaded successfully to Ragie", extra={
                "document_id": document.id,
                "status": document.status,
                "document_name": document.name,
                "partition": partition
            })
            
            return document
            
        except Exception as e:
            logger.error(f"💥 Ragie upload failed", extra={
                "file_name": filename,
                "partition": partition,
                "error_type": type(e).__name__,
                "error_message": str(e)
            })
            raise
    
    async def create_document_from_url(
        self,
        url: str,
        partition: str,
        mode: str = "hi_res",
        metadata: Optional[Dict[str, Any]] = None
    ) -> RagieDocument:
        """
        Create document from URL (S3 pre-signed URL approach).
        
        Args:
            url: Public URL to the document file
            partition: Partition (organization ID) for the document
            metadata: Optional metadata for the document
            
        Returns:
            Document object
        """
        logger.info("Creating document from URL", extra={
            "url": url[:100] + "..." if len(url) > 100 else url,  # Truncate long URLs
            "partition": partition,
            "has_metadata": bool(metadata),
            "metadata_keys": list(metadata.keys()) if metadata else None
        })
        
        # Prepare request payload according to Ragie OpenAPI spec
        payload = {
            "url": url,
            "partition": partition,
            "mode": mode
        }
        
        if metadata:
            payload["metadata"] = metadata
        
        logger.info(f"📤 Sending request to Ragie /documents/url", extra={
            "method": "POST",
            "endpoint": "/documents/url",
            "full_payload": payload,
            "full_s3_url": url,  # Show complete URL for testing
            "partition": partition,
            "mode": mode,
            "metadata_count": len(metadata) if metadata else 0,
            "payload_keys": list(payload.keys())
        })
        
        # Also print directly to console to ensure we see it
        print(f"🔗 FULL S3 URL SENT TO RAGIE: {url}")
        print(f"📦 FULL PAYLOAD SENT TO RAGIE: {payload}")
        
        try:
            response = await self._make_request(
                method="POST",
                endpoint="/documents/url",
                partition=partition,  # Still pass for headers (auth context)
                json_data=payload
            )
            
            logger.info(f"🌐 Ragie URL API response received", extra={
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "response_size": len(response.content)
            })
            
            document_data = response.json()
            
            logger.info(f"📄 Ragie URL document data", extra={
                "raw_response": document_data,
                "response_keys": list(document_data.keys()) if isinstance(document_data, dict) else "non-dict"
            })
            
            document = self._parse_document(document_data)
            
            logger.info("✅ Document created from URL successfully", extra={
                "document_id": document.id,
                "status": document.status,
                "document_name": document.name,
                "partition": partition,
                "source_url": url[:50] + "..." if len(url) > 50 else url
            })
            
            return document
            
        except Exception as e:
            logger.error(f"💥 Ragie URL document creation failed", extra={
                "url": url[:100] + "..." if len(url) > 100 else url,
                "partition": partition,
                "error_type": type(e).__name__,
                "error_message": str(e)
            })
            raise
    
    async def list_documents(
        self,
        partition: str,
        limit: int = 100,
        cursor: Optional[str] = None
    ) -> RagieDocumentList:
        """
        List documents in partition with pagination.
        
        Args:
            partition: Organization partition
            limit: Maximum documents to return (max 100)
            cursor: Pagination cursor for next page
            
        Returns:
            Paginated document list
        """
        params = {"page_size": min(limit, 100)}
        if cursor:
            params["cursor"] = cursor
        
        # Debug: Print the exact request details
        print(f"🔍 RagieClient DEBUG: Making list_documents request:")
        print(f"🔍   URL: {self.base_url}/documents")
        print(f"🔍   partition: '{partition}'")
        print(f"🔍   params: {params}")
        print(f"🔍   headers will include: partition: '{partition}'")
        
        response = await self._make_request(
            method="GET",
            endpoint="/documents",
            partition=partition,
            params=params
        )
        
        data = response.json()
        
        # Debug: Print the raw response
        print(f"🔍 RagieClient DEBUG: Raw response from Ragie API:")
        print(f"🔍   status_code: {response.status_code}")
        print(f"🔍   response_data: {data}")
        
        documents = [self._parse_document(doc) for doc in data.get("documents", [])]
        
        result = RagieDocumentList(
            documents=documents,
            cursor=data.get("cursor"),
            has_more=data.get("has_more", False)
        )
        
        print(f"🔍 RagieClient DEBUG: Parsed result:")
        print(f"🔍   documents_count: {len(result.documents)}")
        print(f"🔍   has_more: {result.has_more}")
        print(f"🔍   cursor: {result.cursor}")
        
        return result
    
    async def get_document(self, document_id: str, partition: str) -> RagieDocument:
        """
        Get a specific document by ID.
        
        Args:
            document_id: Ragie document ID
            partition: Organization partition
            
        Returns:
            Document information
            
        Raises:
            RagieNotFoundError: If document doesn't exist
        """
        response = await self._make_request(
            method="GET",
            endpoint=f"/documents/{document_id}",
            partition=partition
        )
        
        document_data = response.json()
        return self._parse_document(document_data)
    
    async def delete_document(self, document_id: str, partition: str) -> None:
        """
        Delete a document from Ragie.
        
        Args:
            document_id: Ragie document ID
            partition: Organization partition
        """
        await self._make_request(
            method="DELETE",
            endpoint=f"/documents/{document_id}",
            partition=partition
        )
        
        logger.info("Document deleted successfully", extra={
            "document_id": document_id,
            "partition": partition
        })
    
    async def update_document_metadata(
        self,
        document_id: str,
        partition: str,
        metadata: Dict[str, Any]
    ) -> RagieDocument:
        """
        Update document metadata.
        
        Args:
            document_id: Ragie document ID
            partition: Organization partition
            metadata: New metadata
            
        Returns:
            Updated document information
        """
        response = await self._make_request(
            method="PATCH",
            endpoint=f"/documents/{document_id}/metadata",
            partition=partition,
            json_data={"metadata": metadata}
        )
        
        document_data = response.json()
        return self._parse_document(document_data)
    
    async def retrieve_chunks(
        self,
        query: str,
        partition: str,
        max_chunks: int = 10,
        document_ids: Optional[List[str]] = None,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> RagieRetrievalResult:
        """
        Retrieve relevant document chunks for RAG.
        
        Args:
            query: Search query
            partition: Organization partition
            max_chunks: Maximum chunks to return
            document_ids: Filter by specific document IDs
            metadata_filter: Filter by metadata
            
        Returns:
            Retrieval results with scored chunks
        """
        request_data = {
            "query": query,
            "max_chunks": max_chunks
        }
        
        if document_ids:
            request_data["document_ids"] = document_ids
        
        if metadata_filter:
            request_data["metadata_filter"] = metadata_filter
        
        response = await self._make_request(
            method="POST",
            endpoint="/retrievals",
            partition=partition,
            json_data=request_data
        )
        
        data = response.json()
        chunks = []
        
        for scored_chunk in data.get("scored_chunks", []):
            chunk_data = scored_chunk["chunk"]
            score = scored_chunk["score"]
            
            chunk = RagieChunk(
                id=chunk_data["id"],
                document_id=chunk_data["document_id"],
                text=chunk_data["text"],
                score=score,
                metadata=chunk_data.get("metadata", {})
            )
            chunks.append(chunk)
        
        return RagieRetrievalResult(chunks=chunks)
    
    async def get_document_source(
        self,
        document_id: str,
        partition: str
    ) -> Tuple[bytes, str]:
        """
        Get the original source file of a document.
        
        Args:
            document_id: Ragie document ID
            partition: Organization partition
            
        Returns:
            Tuple of (file_content, content_type)
        """
        response = await self._make_request(
            method="GET",
            endpoint=f"/documents/{document_id}/source",
            partition=partition
        )
        
        content_type = response.headers.get("content-type", "application/octet-stream")
        return response.content, content_type
    
    def _parse_document(self, data: Dict[str, Any]) -> RagieDocument:
        """
        Parse Ragie API document response into domain model.
        
        Args:
            data: Raw document data from API
            
        Returns:
            Parsed document model
        """
        return RagieDocument(
            id=data["id"],
            name=data["name"],
            status=RagieDocumentStatus(data["status"]),
            created_at=datetime.fromisoformat(data["created_at"].replace("Z", "+00:00")),
            updated_at=datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00")),
            metadata=data.get("metadata", {})
        )
