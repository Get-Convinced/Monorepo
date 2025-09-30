"""
API tests for Ragie document management endpoints.

Following TDD principles - these tests define the expected API behavior
before implementation.
"""

import pytest
from unittest.mock import AsyncMock, Mock
from httpx import AsyncClient
from datetime import datetime
import json

from src.main import app
from src.services.ragie_service import RagieService, Result
from src.models.ragie import (
    RagieDocument,
    RagieDocumentStatus,
    RagieDocumentList,
    RagieRetrievalResult,
    RagieChunk
)


class TestRagieRoutes:
    """Test suite for Ragie API endpoints."""
    
    @pytest.fixture
    def mock_ragie_service(self):
        """Create mock Ragie service."""
        return AsyncMock(spec=RagieService)
    
    @pytest.fixture
    def sample_document(self):
        """Sample document for testing."""
        return RagieDocument(
            id="doc-123",
            name="test-document.pdf",
            status=RagieDocumentStatus.READY,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            metadata={
                "title": "Test Document",
                "description": "A test document",
                "tags": ["research", "important"]
            }
        )
    
    @pytest.fixture
    async def client(self):
        """Create test client."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client

    @pytest.mark.asyncio
    async def test_upload_document_success(
        self, 
        client, 
        mock_ragie_service, 
        sample_document,
        monkeypatch
    ):
        """Test successful document upload via API."""
        # Arrange
        mock_ragie_service.upload_document.return_value = Result(
            success=True, 
            data=sample_document
        )
        
        # Mock the service dependency
        monkeypatch.setattr("src.api.ragie.get_ragie_service", lambda: mock_ragie_service)
        
        file_content = b"fake pdf content"
        metadata = {"title": "Test Document", "tags": ["research"]}
        
        # Act
        response = await client.post(
            "/api/v1/ragie/documents/upload",
            files={"file": ("test.pdf", file_content, "application/pdf")},
            data={"metadata": json.dumps(metadata)},
            headers={
                "Authorization": "Bearer test-token",
                "X-Organization-ID": "org-123"
            }
        )
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == "doc-123"
        assert data["data"]["name"] == "test-document.pdf"
        assert data["data"]["status"] == "ready"
        
        # Verify service was called correctly
        mock_ragie_service.upload_document.assert_called_once()
        call_args = mock_ragie_service.upload_document.call_args
        assert call_args[1]["filename"] == "test.pdf"
        assert call_args[1]["organization_id"] == "org-123"
        assert call_args[1]["metadata"] == metadata

    @pytest.mark.asyncio
    async def test_upload_document_no_file(self, client):
        """Test document upload without file."""
        # Act
        response = await client.post(
            "/api/v1/ragie/documents/upload",
            headers={
                "Authorization": "Bearer test-token",
                "X-Organization-ID": "org-123"
            }
        )
        
        # Assert
        assert response.status_code == 422
        data = response.json()
        assert data["success"] is False
        assert "file" in data["error"]["message"].lower()

    @pytest.mark.asyncio
    async def test_upload_document_unauthorized(self, client):
        """Test document upload without authentication."""
        # Act
        response = await client.post(
            "/api/v1/ragie/documents/upload",
            files={"file": ("test.pdf", b"content", "application/pdf")}
        )
        
        # Assert
        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "UNAUTHORIZED"

    @pytest.mark.asyncio
    async def test_upload_document_no_organization(self, client):
        """Test document upload without organization ID."""
        # Act
        response = await client.post(
            "/api/v1/ragie/documents/upload",
            files={"file": ("test.pdf", b"content", "application/pdf")},
            headers={"Authorization": "Bearer test-token"}
        )
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "organization" in data["error"]["message"].lower()

    @pytest.mark.asyncio
    async def test_upload_document_service_error(
        self, 
        client, 
        mock_ragie_service,
        monkeypatch
    ):
        """Test document upload when service fails."""
        # Arrange
        mock_ragie_service.upload_document.return_value = Result(
            success=False, 
            error="Upload failed"
        )
        
        monkeypatch.setattr("src.api.ragie.get_ragie_service", lambda: mock_ragie_service)
        
        # Act
        response = await client.post(
            "/api/v1/ragie/documents/upload",
            files={"file": ("test.pdf", b"content", "application/pdf")},
            headers={
                "Authorization": "Bearer test-token",
                "X-Organization-ID": "org-123"
            }
        )
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "Upload failed" in data["error"]["message"]

    @pytest.mark.asyncio
    async def test_list_documents_success(
        self, 
        client, 
        mock_ragie_service, 
        sample_document,
        monkeypatch
    ):
        """Test successful document listing."""
        # Arrange
        document_list = RagieDocumentList(
            documents=[sample_document],
            cursor="next-cursor",
            has_more=True
        )
        mock_ragie_service.list_documents.return_value = Result(
            success=True, 
            data=document_list
        )
        
        monkeypatch.setattr("src.api.ragie.get_ragie_service", lambda: mock_ragie_service)
        
        # Act
        response = await client.get(
            "/api/v1/ragie/documents?limit=10&cursor=start-cursor",
            headers={
                "Authorization": "Bearer test-token",
                "X-Organization-ID": "org-123"
            }
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]["documents"]) == 1
        assert data["data"]["documents"][0]["id"] == "doc-123"
        assert data["data"]["cursor"] == "next-cursor"
        assert data["data"]["has_more"] is True
        
        # Verify service was called correctly
        mock_ragie_service.list_documents.assert_called_once_with(
            organization_id="org-123",
            limit=10,
            cursor="start-cursor"
        )

    @pytest.mark.asyncio
    async def test_get_document_success(
        self, 
        client, 
        mock_ragie_service, 
        sample_document,
        monkeypatch
    ):
        """Test successful document retrieval."""
        # Arrange
        mock_ragie_service.get_document.return_value = Result(
            success=True, 
            data=sample_document
        )
        
        monkeypatch.setattr("src.api.ragie.get_ragie_service", lambda: mock_ragie_service)
        
        # Act
        response = await client.get(
            "/api/v1/ragie/documents/doc-123",
            headers={
                "Authorization": "Bearer test-token",
                "X-Organization-ID": "org-123"
            }
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == "doc-123"
        
        mock_ragie_service.get_document.assert_called_once_with(
            document_id="doc-123",
            organization_id="org-123"
        )

    @pytest.mark.asyncio
    async def test_get_document_not_found(
        self, 
        client, 
        mock_ragie_service,
        monkeypatch
    ):
        """Test document retrieval when document doesn't exist."""
        # Arrange
        mock_ragie_service.get_document.return_value = Result(
            success=False, 
            error="Document not found"
        )
        
        monkeypatch.setattr("src.api.ragie.get_ragie_service", lambda: mock_ragie_service)
        
        # Act
        response = await client.get(
            "/api/v1/ragie/documents/nonexistent",
            headers={
                "Authorization": "Bearer test-token",
                "X-Organization-ID": "org-123"
            }
        )
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert "not found" in data["error"]["message"].lower()

    @pytest.mark.asyncio
    async def test_delete_document_success(
        self, 
        client, 
        mock_ragie_service,
        monkeypatch
    ):
        """Test successful document deletion."""
        # Arrange
        mock_ragie_service.delete_document.return_value = Result(success=True)
        
        monkeypatch.setattr("src.api.ragie.get_ragie_service", lambda: mock_ragie_service)
        
        # Act
        response = await client.delete(
            "/api/v1/ragie/documents/doc-123",
            headers={
                "Authorization": "Bearer test-token",
                "X-Organization-ID": "org-123"
            }
        )
        
        # Assert
        assert response.status_code == 204
        
        mock_ragie_service.delete_document.assert_called_once_with(
            document_id="doc-123",
            organization_id="org-123"
        )

    @pytest.mark.asyncio
    async def test_update_document_metadata_success(
        self, 
        client, 
        mock_ragie_service, 
        sample_document,
        monkeypatch
    ):
        """Test successful metadata update."""
        # Arrange
        updated_metadata = {
            "title": "Updated Title",
            "tags": ["updated", "metadata"]
        }
        updated_document = RagieDocument(
            **sample_document.dict(),
            metadata=updated_metadata
        )
        
        mock_ragie_service.update_document_metadata.return_value = Result(
            success=True, 
            data=updated_document
        )
        
        monkeypatch.setattr("src.api.ragie.get_ragie_service", lambda: mock_ragie_service)
        
        # Act
        response = await client.patch(
            "/api/v1/ragie/documents/doc-123/metadata",
            json={"metadata": updated_metadata},
            headers={
                "Authorization": "Bearer test-token",
                "X-Organization-ID": "org-123"
            }
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["metadata"]["title"] == "Updated Title"
        assert "updated" in data["data"]["metadata"]["tags"]
        
        mock_ragie_service.update_document_metadata.assert_called_once_with(
            document_id="doc-123",
            organization_id="org-123",
            metadata=updated_metadata
        )

    @pytest.mark.asyncio
    async def test_retrieve_chunks_success(
        self, 
        client, 
        mock_ragie_service,
        monkeypatch
    ):
        """Test successful chunk retrieval."""
        # Arrange
        chunks = [
            RagieChunk(
                id="chunk-1",
                document_id="doc-123",
                text="Relevant content",
                score=0.95,
                metadata={"page": 1}
            )
        ]
        retrieval_result = RagieRetrievalResult(chunks=chunks)
        
        mock_ragie_service.retrieve_chunks.return_value = Result(
            success=True, 
            data=retrieval_result
        )
        
        monkeypatch.setattr("src.api.ragie.get_ragie_service", lambda: mock_ragie_service)
        
        # Act
        response = await client.post(
            "/api/v1/ragie/query",
            json={
                "query": "What is the main topic?",
                "max_chunks": 5
            },
            headers={
                "Authorization": "Bearer test-token",
                "X-Organization-ID": "org-123"
            }
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]["chunks"]) == 1
        assert data["data"]["chunks"][0]["score"] == 0.95
        
        mock_ragie_service.retrieve_chunks.assert_called_once_with(
            query="What is the main topic?",
            organization_id="org-123",
            max_chunks=5,
            document_ids=None,
            metadata_filter=None
        )

    @pytest.mark.asyncio
    async def test_get_document_source_success(
        self, 
        client, 
        mock_ragie_service,
        monkeypatch
    ):
        """Test successful document source retrieval."""
        # Arrange
        file_content = b"original file content"
        content_type = "application/pdf"
        
        mock_ragie_service.get_document_source.return_value = Result(
            success=True, 
            data={
                "content": file_content,
                "content_type": content_type
            }
        )
        
        monkeypatch.setattr("src.api.ragie.get_ragie_service", lambda: mock_ragie_service)
        
        # Act
        response = await client.get(
            "/api/v1/ragie/documents/doc-123/source",
            headers={
                "Authorization": "Bearer test-token",
                "X-Organization-ID": "org-123"
            }
        )
        
        # Assert
        assert response.status_code == 200
        assert response.content == file_content
        assert response.headers["content-type"] == content_type
        
        mock_ragie_service.get_document_source.assert_called_once_with(
            document_id="doc-123",
            organization_id="org-123"
        )
