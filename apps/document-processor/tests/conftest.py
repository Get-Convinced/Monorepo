"""
Test Configuration and Shared Fixtures
=====================================

This module provides shared configuration, fixtures, and utilities for all tests.
Following DRY principles to avoid code duplication across test modules.
"""

import os
import sys
import asyncio
import pytest
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from unittest.mock import Mock, AsyncMock

# Load environment variables from .env files
try:
    from dotenv import load_dotenv
    # Load from multiple possible .env files
    load_dotenv('.env.local')  # Local development
    load_dotenv('.env')        # General environment
    load_dotenv('.env.test')   # Test-specific environment
except ImportError:
    pass  # python-dotenv not available

# Add src to path
SRC_DIR = Path(__file__).parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from embeddings import EmbeddingService
from rag.vector_store import VectorStore
from workers.unified_document_worker import UnifiedDocumentWorker
from processors.unified_document_processor import GPTModel, UnifiedDocumentProcessor

# Configure logging for tests
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test Configuration
class TestConfig:
    """Centralized test configuration."""
    
    # Service URLs
    QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6336")
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    
    # Models
    EMBED_MODEL = os.getenv("EMBED_MODEL", "mxbai-embed-large")
    EMBED_DIMENSION = int(os.getenv("EMBED_DIMENSION", "1024"))
    GPT_MODEL = os.getenv("GPT_MODEL", "gpt-4o")
    
    # Collections
    TEST_COLLECTION = os.getenv("TEST_COLLECTION", "test_documents")
    INTEGRATION_COLLECTION = os.getenv("INTEGRATION_COLLECTION", "integration_test")
    
    # API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # Test Data Paths
    TEST_DATA_DIR = Path(__file__).parent / "test_data"
    BIZOM_DISCUSSION_DECK = TEST_DATA_DIR / "Bizom _ Discussion Deck.pdf"
    BIZOM_OMNICHANNEL = TEST_DATA_DIR / "Bizom _ Omnichannel_Celesta.pdf"
    BIZOM_PITCH_DECK = TEST_DATA_DIR / "Bizom _ Pitch Deck_Full Deck_UI Updated.pdf"
    
    # Test Settings
    VISUAL_EXTRACTION_DPI = 300  # Lower DPI for faster tests
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200
    
    @classmethod
    def get_test_files(cls) -> List[Path]:
        """Get list of available test files."""
        return [
            cls.BIZOM_DISCUSSION_DECK,
            cls.BIZOM_OMNICHANNEL,
            cls.BIZOM_PITCH_DECK
        ]
    
    @classmethod
    def get_existing_test_files(cls) -> List[Path]:
        """Get list of test files that actually exist."""
        return [f for f in cls.get_test_files() if f.exists()]


# Pytest Fixtures
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_config():
    """Provide test configuration."""
    return TestConfig()


@pytest.fixture(scope="session")
async def vector_store(test_config):
    """Provide vector store instance for tests."""
    store = VectorStore(qdrant_url=test_config.QDRANT_URL)
    yield store
    # Cleanup: delete test collections
    try:
        await store.delete_collection(test_config.TEST_COLLECTION)
        await store.delete_collection(test_config.INTEGRATION_COLLECTION)
    except Exception as e:
        logger.warning(f"Failed to cleanup collections: {e}")


@pytest.fixture(scope="session")
async def embedding_service(test_config):
    """Provide embedding service instance for tests."""
    service = EmbeddingService.create_ollama_provider(
        base_url=test_config.OLLAMA_BASE_URL,
        model=test_config.EMBED_MODEL
    )
    return service


@pytest.fixture(scope="session")
async def document_worker(test_config, embedding_service, vector_store):
    """Provide unified document worker for tests."""
    if not test_config.OPENAI_API_KEY:
        pytest.skip("OPENAI_API_KEY not set - skipping tests that require OpenAI")
    
    gpt_model = GPTModel(test_config.GPT_MODEL)
    worker = UnifiedDocumentWorker(
        embedding_service=embedding_service,
        vector_store=vector_store,
        openai_api_key=test_config.OPENAI_API_KEY,
        gpt_model=gpt_model,
        visual_extraction_dpi=test_config.VISUAL_EXTRACTION_DPI
    )
    return worker


@pytest.fixture(scope="session")
async def document_processor(test_config):
    """Provide unified document processor for tests."""
    if not test_config.OPENAI_API_KEY:
        pytest.skip("OPENAI_API_KEY not set - skipping tests that require OpenAI")
    
    gpt_model = GPTModel(test_config.GPT_MODEL)
    processor = UnifiedDocumentProcessor(
        openai_api_key=test_config.OPENAI_API_KEY,
        gpt_model=gpt_model,
        visual_extraction_dpi=test_config.VISUAL_EXTRACTION_DPI
    )
    return processor


@pytest.fixture
def mock_vector_store():
    """Provide mock vector store for unit tests."""
    mock_store = Mock(spec=VectorStore)
    mock_store.ensure_collection_exists = AsyncMock(return_value=True)
    mock_store.delete_collection = AsyncMock(return_value=True)
    mock_store.upsert_points = AsyncMock(return_value={"status": "completed"})
    mock_store.search = AsyncMock(return_value=[])
    mock_store.get_collection_info = AsyncMock(return_value={"points_count": 0})
    return mock_store


@pytest.fixture
def mock_embedding_service():
    """Provide mock embedding service for unit tests."""
    mock_service = Mock(spec=EmbeddingService)
    mock_service.embed_text = AsyncMock(return_value=[0.1] * 1024)  # Mock 1024-dim vector
    mock_service.embed_texts = AsyncMock(return_value=[[0.1] * 1024] * 3)  # Mock multiple vectors
    return mock_service


# Test Utilities
class TestUtils:
    """Utility functions for tests."""
    
    @staticmethod
    def assert_processing_result(result: Dict[str, Any], expected_keys: List[str] = None):
        """Assert that processing result has expected structure."""
        if expected_keys is None:
            expected_keys = ["content", "processor", "file_type", "processing_method"]
        
        for key in expected_keys:
            assert key in result, f"Missing key '{key}' in processing result"
        
        assert result["content"], "Content should not be empty"
        assert result["processor"], "Processor should be specified"
        assert result["file_type"], "File type should be specified"
    
    @staticmethod
    def assert_worker_result(result: Dict[str, Any]):
        """Assert that worker result has expected structure."""
        expected_keys = [
            "total_documents", "successful", "failed", 
            "total_chunks", "total_points", "results"
        ]
        
        for key in expected_keys:
            assert key in result, f"Missing key '{key}' in worker result"
        
        assert isinstance(result["total_documents"], int)
        assert isinstance(result["successful"], int)
        assert isinstance(result["failed"], int)
        assert isinstance(result["total_chunks"], int)
        assert isinstance(result["total_points"], int)
        assert isinstance(result["results"], list)
    
    @staticmethod
    def create_test_metadata(test_type: str = "unit_test", **kwargs) -> Dict[str, Any]:
        """Create standardized test metadata."""
        return {
            "test_type": test_type,
            "timestamp": "2024-01-01T00:00:00Z",
            **kwargs
        }


# Pytest Markers
pytest_plugins = []

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )
    config.addinivalue_line(
        "markers", "requires_openai: mark test as requiring OpenAI API key"
    )
    config.addinivalue_line(
        "markers", "requires_qdrant: mark test as requiring Qdrant"
    )
    config.addinivalue_line(
        "markers", "requires_ollama: mark test as requiring Ollama"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test names."""
    for item in items:
        # Add markers based on test file names
        if "test_system" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        elif "test_process" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        elif "test_manual" in item.nodeid:
            item.add_marker(pytest.mark.slow)
        
        # Add markers based on test function names
        if "openai" in item.name.lower():
            item.add_marker(pytest.mark.requires_openai)
        if "qdrant" in item.name.lower():
            item.add_marker(pytest.mark.requires_qdrant)
        if "ollama" in item.name.lower():
            item.add_marker(pytest.mark.requires_ollama)
