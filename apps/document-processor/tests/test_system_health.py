"""
System Health Check Tests
========================

Tests to verify that all required systems are running and properly configured:
- Qdrant vector database
- Ollama embedding service
- OpenAI API access
- Test data availability
"""

import pytest
import httpx
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any

from conftest import TestConfig, TestUtils

logger = logging.getLogger(__name__)


class TestSystemHealth:
    """Test system health and configuration."""
    
    @pytest.mark.integration
    @pytest.mark.requires_qdrant
    async def test_qdrant_connection(self, test_config):
        """Test Qdrant database connectivity."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{test_config.QDRANT_URL}/")
                assert response.status_code == 200
                logger.info("✅ Qdrant is accessible")
            except httpx.ConnectError:
                pytest.fail(f"❌ Cannot connect to Qdrant at {test_config.QDRANT_URL}")
    
    @pytest.mark.integration
    @pytest.mark.requires_qdrant
    async def test_qdrant_collections_management(self, vector_store, test_config):
        """Test Qdrant collection creation and deletion."""
        test_collection = f"{test_config.TEST_COLLECTION}_health_check"
        
        # Test collection creation
        await vector_store.ensure_collection_exists(test_collection, test_config.EMBED_DIMENSION)
        logger.info(f"✅ Created collection: {test_collection}")
        
        # Test collection info retrieval
        info = await vector_store.get_collection_info(test_collection)
        assert info is not None
        logger.info(f"✅ Retrieved collection info: {info}")
        
        # Test collection deletion
        await vector_store.delete_collection(test_collection)
        logger.info(f"✅ Deleted collection: {test_collection}")
    
    @pytest.mark.integration
    @pytest.mark.requires_ollama
    async def test_ollama_connection(self, test_config):
        """Test Ollama service connectivity."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{test_config.OLLAMA_BASE_URL}/api/tags")
                assert response.status_code == 200
                models = response.json()
                logger.info(f"✅ Ollama is accessible with {len(models.get('models', []))} models")
            except httpx.ConnectError:
                pytest.fail(f"❌ Cannot connect to Ollama at {test_config.OLLAMA_BASE_URL}")
    
    @pytest.mark.integration
    @pytest.mark.requires_ollama
    async def test_embedding_model_availability(self, test_config):
        """Test if the required embedding model is available."""
        async with httpx.AsyncClient() as client:
            try:
                # Check if model is available
                response = await client.get(f"{test_config.OLLAMA_BASE_URL}/api/tags")
                models = response.json()
                model_names = [model["name"] for model in models.get("models", [])]
                
                if test_config.EMBED_MODEL in model_names:
                    logger.info(f"✅ Embedding model '{test_config.EMBED_MODEL}' is available")
                else:
                    logger.warning(f"⚠️ Embedding model '{test_config.EMBED_MODEL}' not found")
                    logger.info(f"Available models: {model_names}")
                    
                    # Try to pull the model
                    logger.info(f"Attempting to pull model '{test_config.EMBED_MODEL}'...")
                    pull_response = await client.post(
                        f"{test_config.OLLAMA_BASE_URL}/api/pull",
                        json={"name": test_config.EMBED_MODEL}
                    )
                    if pull_response.status_code == 200:
                        logger.info(f"✅ Successfully pulled model '{test_config.EMBED_MODEL}'")
                    else:
                        pytest.skip(f"Could not pull embedding model '{test_config.EMBED_MODEL}'")
                        
            except httpx.ConnectError:
                pytest.fail(f"❌ Cannot connect to Ollama at {test_config.OLLAMA_BASE_URL}")
    
    @pytest.mark.integration
    @pytest.mark.requires_ollama
    async def test_embedding_service_functionality(self, embedding_service, test_config):
        """Test embedding service functionality."""
        test_text = "This is a test document for embedding."
        
        # Test single text embedding
        embeddings = await embedding_service.generate_embeddings([test_text])
        assert isinstance(embeddings, list)
        assert len(embeddings) == 1
        embedding = embeddings[0]
        assert len(embedding) == test_config.EMBED_DIMENSION
        assert all(isinstance(x, float) for x in embedding)
        logger.info(f"✅ Single text embedding: {len(embedding)} dimensions")
        
        # Test multiple texts embedding
        test_texts = [
            "First test document.",
            "Second test document.",
            "Third test document."
        ]
        embeddings = await embedding_service.generate_embeddings(test_texts)
        assert isinstance(embeddings, list)
        assert len(embeddings) == len(test_texts)
        assert all(len(emb) == test_config.EMBED_DIMENSION for emb in embeddings)
        logger.info(f"✅ Multiple text embeddings: {len(embeddings)} texts, {len(embeddings[0])} dimensions each")
    
    @pytest.mark.requires_openai
    async def test_openai_api_key(self, test_config):
        """Test OpenAI API key configuration."""
        if not test_config.OPENAI_API_KEY:
            pytest.fail("❌ OPENAI_API_KEY not set in environment variables")
    
    @pytest.mark.requires_openai
    async def test_openai_api_connectivity(self, test_config):
        """Test OpenAI API connectivity."""
        if not test_config.OPENAI_API_KEY:
            pytest.skip("OPENAI_API_KEY not set")
        
        import openai
        client = openai.AsyncOpenAI(api_key=test_config.OPENAI_API_KEY)
        
        try:
            # Test with a simple completion
            response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Hello, this is a connectivity test."}],
                max_tokens=10
            )
            assert response.choices[0].message.content is not None
            logger.info("✅ OpenAI API is accessible")
        except Exception as e:
            pytest.fail(f"❌ OpenAI API connectivity failed: {e}")
    
    def test_test_data_availability(self, test_config):
        """Test that required test data files are available."""
        test_files = test_config.get_existing_test_files()
        
        assert len(test_files) > 0, "No test data files found"
        logger.info(f"✅ Found {len(test_files)} test data files:")
        
        for file_path in test_files:
            assert file_path.exists(), f"Test file does not exist: {file_path}"
            assert file_path.stat().st_size > 0, f"Test file is empty: {file_path}"
            logger.info(f"   📄 {file_path.name} ({file_path.stat().st_size} bytes)")
    
    def test_environment_configuration(self, test_config):
        """Test environment configuration."""
        config_info = {
            "Qdrant URL": test_config.QDRANT_URL,
            "Ollama URL": test_config.OLLAMA_BASE_URL,
            "Embedding Model": test_config.EMBED_MODEL,
            "Embedding Dimension": test_config.EMBED_DIMENSION,
            "GPT Model": test_config.GPT_MODEL,
            "Test Collection": test_config.TEST_COLLECTION,
            "OpenAI API Key": "***" if test_config.OPENAI_API_KEY else "Not set"
        }
        
        logger.info("🔧 Environment Configuration:")
        for key, value in config_info.items():
            logger.info(f"   {key}: {value}")
        
        # Basic validation
        assert test_config.QDRANT_URL.startswith("http"), "Qdrant URL should start with http"
        assert test_config.OLLAMA_BASE_URL.startswith("http"), "Ollama URL should start with http"
        assert test_config.EMBED_DIMENSION > 0, "Embedding dimension should be positive"
        assert test_config.VISUAL_EXTRACTION_DPI > 0, "Visual extraction DPI should be positive"
    
    @pytest.mark.integration
    async def test_full_system_integration(self, vector_store, embedding_service, test_config):
        """Test full system integration - all components working together."""
        test_collection = f"{test_config.TEST_COLLECTION}_integration"
        
        try:
            # 1. Create collection
            await vector_store.ensure_collection_exists(test_collection, test_config.EMBED_DIMENSION)
            logger.info("✅ Step 1: Collection created")
            
            # 2. Generate embeddings
            test_text = "Integration test document content."
            embeddings = await embedding_service.generate_embeddings([test_text])
            embedding = embeddings[0]
            logger.info("✅ Step 2: Embedding generated")
            
            # 3. Store in vector database
            points = [{
                "id": 1,  # Use integer ID instead of string
                "vector": embedding,
                "payload": {
                    "text": test_text,
                    "test_type": "integration"
                }
            }]
            
            await vector_store.upsert_points(test_collection, points)
            logger.info("✅ Step 3: Vector stored")
            
            # 4. Search vectors
            search_results = await vector_store.search(
                collection_name=test_collection,
                query_vector=embedding,
                limit=5
            )
            assert len(search_results) > 0
            logger.info("✅ Step 4: Vector search successful")
            
            # 5. Verify stored data
            collection_info = await vector_store.get_collection_info(test_collection)
            assert collection_info["points_count"] > 0
            logger.info("✅ Step 5: Data verification successful")
            
        finally:
            # Cleanup
            await vector_store.delete_collection(test_collection)
            logger.info("✅ Cleanup: Collection deleted")
        
        logger.info("🎉 Full system integration test passed!")


class TestSystemPerformance:
    """Test system performance characteristics."""
    
    @pytest.mark.slow
    @pytest.mark.integration
    async def test_embedding_performance(self, embedding_service, test_config):
        """Test embedding service performance."""
        import time
        
        test_texts = [
            "Performance test document number one with some content.",
            "Performance test document number two with different content.",
            "Performance test document number three with more content.",
            "Performance test document number four with additional content.",
            "Performance test document number five with final content."
        ]
        
        # Test single embedding performance
        start_time = time.time()
        embeddings = await embedding_service.generate_embeddings([test_texts[0]])
        single_time = time.time() - start_time
        logger.info(f"✅ Single embedding time: {single_time:.3f}s")
        
        # Test batch embedding performance
        start_time = time.time()
        embeddings = await embedding_service.generate_embeddings(test_texts)
        batch_time = time.time() - start_time
        logger.info(f"✅ Batch embedding time: {batch_time:.3f}s")
        
        # Performance assertions
        assert single_time < 5.0, f"Single embedding too slow: {single_time:.3f}s"
        assert batch_time < 10.0, f"Batch embedding too slow: {batch_time:.3f}s"
        assert batch_time < single_time * len(test_texts), "Batch processing should be more efficient"
    
    @pytest.mark.slow
    @pytest.mark.integration
    async def test_vector_store_performance(self, vector_store, embedding_service, test_config):
        """Test vector store performance."""
        import time
        
        test_collection = f"{test_config.TEST_COLLECTION}_performance"
        
        try:
            await vector_store.ensure_collection_exists(test_collection, test_config.EMBED_DIMENSION)
            
            # Generate test data
            test_texts = [f"Performance test document {i}" for i in range(10)]
            embeddings = await embedding_service.generate_embeddings(test_texts)
            
            # Test batch upsert performance
            points = [{
                "id": i,  # Use integer ID instead of string
                "vector": embeddings[i],
                "payload": {"text": test_texts[i], "index": i}
            } for i in range(len(test_texts))]
            
            start_time = time.time()
            await vector_store.upsert_points(test_collection, points)
            upsert_time = time.time() - start_time
            logger.info(f"✅ Batch upsert time: {upsert_time:.3f}s")
            
            # Test search performance
            query_embedding = embeddings[0]
            start_time = time.time()
            results = await vector_store.search(
                collection_name=test_collection,
                query_vector=query_embedding,
                limit=5
            )
            search_time = time.time() - start_time
            logger.info(f"✅ Search time: {search_time:.3f}s")
            
            # Performance assertions
            assert upsert_time < 5.0, f"Upsert too slow: {upsert_time:.3f}s"
            assert search_time < 2.0, f"Search too slow: {search_time:.3f}s"
            assert len(results) > 0, "Search should return results"
            
        finally:
            await vector_store.delete_collection(test_collection)
