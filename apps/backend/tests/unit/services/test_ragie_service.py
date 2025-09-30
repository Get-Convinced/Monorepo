"""
Tests for simplified Ragie service.

This test suite demonstrates the simplified error handling approach
using direct exceptions instead of Result wrappers.
"""

import pytest
from unittest.mock import AsyncMock, Mock
from pathlib import Path

from src.services.ragie_service import (
    RagieService, UnsupportedFileTypeError, FileTooLargeError
)
from src.adapters.ragie_client import RagieError, RagieNotFoundError
from src.models.ragie import RagieDocument, RagieDocumentStatus


class TestRagieServiceSimplified:
    """Test suite for simplified Ragie service."""

    @pytest.fixture
    def mock_ragie_client(self):
        """Mock Ragie client."""
        return AsyncMock()

    @pytest.fixture
    def ragie_service(self, mock_ragie_client):
        """Ragie service with mocked client."""
        return RagieService(ragie_client=mock_ragie_client)

    @pytest.fixture
    def sample_document(self):
        """Sample document for testing."""
        return RagieDocument(
            id="doc-123",
            name="test.pdf",
            status=RagieDocumentStatus.READY,
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z",
            metadata={"title": "Test Document"}
        )

    @pytest.mark.asyncio
    async def test_upload_document_success(self, ragie_service, mock_ragie_client, sample_document):
        """Test successful document upload with simplified approach."""
        # Arrange
        file_content = b"fake pdf content"
        filename = "test.pdf"
        organization_id = "org-123"
        user_id = "user-456"
        metadata = {"title": "Test Document"}
        
        mock_ragie_client.upload_document.return_value = sample_document
        
        # Act - Direct call, no Result wrapper
        result = await ragie_service.upload_document(
            file_content=file_content,
            filename=filename,
            organization_id=organization_id,
            user_id=user_id,
            metadata=metadata
        )
        
        # Assert - Direct result, no .success checking
        assert result.id == "doc-123"
        assert result.name == "test.pdf"
        assert result.status == RagieDocumentStatus.READY
        
        mock_ragie_client.upload_document.assert_called_once_with(
            file_content=file_content,
            filename=filename,
            partition=organization_id,
            metadata=metadata
        )

    @pytest.mark.asyncio
    async def test_upload_document_unsupported_file_type(self, ragie_service, mock_ragie_client):
        """Test upload with unsupported file type raises exception directly."""
        # Arrange
        file_content = b"fake content"
        filename = "test.xyz"  # Unsupported extension
        organization_id = "org-123"
        user_id = "user-456"
        
        # Act & Assert - Direct exception, no Result wrapper
        with pytest.raises(UnsupportedFileTypeError) as exc_info:
            await ragie_service.upload_document(
                file_content=file_content,
                filename=filename,
                organization_id=organization_id,
                user_id=user_id
            )
        
        assert "not supported" in str(exc_info.value)
        mock_ragie_client.upload_document.assert_not_called()

    @pytest.mark.asyncio
    async def test_upload_document_file_too_large(self, ragie_service, mock_ragie_client):
        """Test upload with oversized file raises exception directly."""
        # Arrange
        file_content = b"x" * (51 * 1024 * 1024)  # 51MB - exceeds 50MB limit
        filename = "large.pdf"
        organization_id = "org-123"
        user_id = "user-456"
        
        # Act & Assert - Direct exception, no Result wrapper
        with pytest.raises(FileTooLargeError) as exc_info:
            await ragie_service.upload_document(
                file_content=file_content,
                filename=filename,
                organization_id=organization_id,
                user_id=user_id
            )
        
        assert "exceeds maximum" in str(exc_info.value)
        mock_ragie_client.upload_document.assert_not_called()

    @pytest.mark.asyncio
    async def test_upload_document_ragie_error(self, ragie_service, mock_ragie_client):
        """Test upload with Ragie API error raises service exception."""
        # Arrange
        file_content = b"fake pdf content"
        filename = "test.pdf"
        organization_id = "org-123"
        user_id = "user-456"
        
        mock_ragie_client.upload_document.side_effect = RagieError("API error")
        
        # Act & Assert - Service wraps Ragie errors
        with pytest.raises(Exception) as exc_info:
            await ragie_service.upload_document(
                file_content=file_content,
                filename=filename,
                organization_id=organization_id,
                user_id=user_id
            )
        
        assert "Upload failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_list_documents_success(self, ragie_service, mock_ragie_client):
        """Test successful document listing."""
        # Arrange
        from src.models.ragie import RagieDocumentList
        
        organization_id = "org-123"
        expected_list = RagieDocumentList(
            documents=[],
            cursor=None,
            has_more=False
        )
        
        mock_ragie_client.list_documents.return_value = expected_list
        
        # Act - Direct call, no Result wrapper
        result = await ragie_service.list_documents(organization_id=organization_id)
        
        # Assert - Direct result
        assert result.documents == []
        assert result.cursor is None
        assert result.has_more is False
        
        mock_ragie_client.list_documents.assert_called_once_with(
            partition=organization_id,
            limit=20,
            cursor=None
        )

    @pytest.mark.asyncio
    async def test_get_document_success(self, ragie_service, mock_ragie_client, sample_document):
        """Test successful document retrieval."""
        # Arrange
        document_id = "doc-123"
        organization_id = "org-123"
        
        mock_ragie_client.get_document.return_value = sample_document
        
        # Act - Direct call, no Result wrapper
        result = await ragie_service.get_document(
            document_id=document_id,
            organization_id=organization_id
        )
        
        # Assert - Direct result
        assert result.id == "doc-123"
        assert result.name == "test.pdf"
        
        mock_ragie_client.get_document.assert_called_once_with(
            document_id=document_id,
            partition=organization_id
        )

    @pytest.mark.asyncio
    async def test_get_document_not_found(self, ragie_service, mock_ragie_client):
        """Test document not found raises exception directly."""
        # Arrange
        document_id = "nonexistent"
        organization_id = "org-123"
        
        mock_ragie_client.get_document.side_effect = RagieNotFoundError("Not found")
        
        # Act & Assert - Direct exception
        with pytest.raises(Exception) as exc_info:
            await ragie_service.get_document(
                document_id=document_id,
                organization_id=organization_id
            )
        
        assert "not found" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_delete_document_success(self, ragie_service, mock_ragie_client):
        """Test successful document deletion."""
        # Arrange
        document_id = "doc-123"
        organization_id = "org-123"
        
        mock_ragie_client.delete_document.return_value = None
        
        # Act - Direct call, no Result wrapper
        await ragie_service.delete_document(
            document_id=document_id,
            organization_id=organization_id
        )
        
        # Assert - No exception means success
        mock_ragie_client.delete_document.assert_called_once_with(
            document_id=document_id,
            partition=organization_id
        )

    @pytest.mark.asyncio
    async def test_update_document_metadata_success(self, ragie_service, mock_ragie_client, sample_document):
        """Test successful metadata update."""
        # Arrange
        document_id = "doc-123"
        organization_id = "org-123"
        metadata = {"title": "Updated Title", "tags": ["updated"]}
        
        mock_ragie_client.patch_document_metadata.return_value = sample_document
        
        # Act - Direct call, no Result wrapper
        result = await ragie_service.update_document_metadata(
            document_id=document_id,
            organization_id=organization_id,
            metadata=metadata
        )
        
        # Assert - Direct result
        assert result.id == "doc-123"
        
        mock_ragie_client.patch_document_metadata.assert_called_once_with(
            document_id=document_id,
            partition=organization_id,
            metadata=metadata
        )
