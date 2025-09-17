"""
Document Processing and Ingestion Tests
======================================

Tests for document processing, chunking, embedding, and storage in Qdrant:
- PDF document processing with GPT models
- Document chunking and embedding
- Vector storage and retrieval
- End-to-end document ingestion workflow
"""

import pytest
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, List

from conftest import TestConfig, TestUtils

logger = logging.getLogger(__name__)


class TestDocumentProcessor:
    """Test document processor functionality."""
    
    @pytest.mark.requires_openai
    async def test_processor_initialization(self, document_processor, test_config):
        """Test document processor initialization."""
        processor_info = document_processor.get_processor_info()
        
        assert processor_info["gpt_model"] == test_config.GPT_MODEL
        assert processor_info["visual_extraction_dpi"] == test_config.VISUAL_EXTRACTION_DPI
        assert "pdf" in processor_info["supported_visual_types"]
        assert "docx" in processor_info["supported_docling_types"]
        
        logger.info("✅ Document processor initialized correctly")
        logger.info(f"   GPT Model: {processor_info['gpt_model']}")
        logger.info(f"   Visual DPI: {processor_info['visual_extraction_dpi']}")
    
    @pytest.mark.requires_openai
    async def test_pdf_processing(self, document_processor, test_config):
        """Test PDF document processing with GPT models."""
        test_files = test_config.get_existing_test_files()
        pdf_files = [f for f in test_files if f.suffix.lower() == '.pdf']
        
        if not pdf_files:
            pytest.skip("No PDF test files available")
        
        # Test with first available PDF
        pdf_file = pdf_files[0]
        logger.info(f"Testing PDF processing with: {pdf_file.name}")
        
        result = await document_processor.process_document(pdf_file)
        
        # Validate processing result
        TestUtils.assert_processing_result(result)
        assert result["processor"].startswith("gpt_")
        assert result["file_type"] == "pdf"
        assert result["processing_method"] == "visual_analysis"
        assert "content" in result and result["content"]
        
        # Check for page-specific metadata
        if "page_metadata" in result:
            assert isinstance(result["page_metadata"], list)
            assert len(result["page_metadata"]) > 0
            logger.info(f"   Processed {len(result['page_metadata'])} pages")
        
        logger.info(f"✅ PDF processing successful: {len(result['content'])} characters extracted")
    
    @pytest.mark.requires_openai
    @pytest.mark.slow
    async def test_multiple_pdf_processing(self, document_processor, test_config):
        """Test processing multiple PDF documents."""
        test_files = test_config.get_existing_test_files()
        pdf_files = [f for f in test_files if f.suffix.lower() == '.pdf']
        
        if len(pdf_files) < 2:
            pytest.skip("Need at least 2 PDF files for this test")
        
        results = []
        for pdf_file in pdf_files[:2]:  # Test first 2 PDFs
            logger.info(f"Processing: {pdf_file.name}")
            result = await document_processor.process_document(pdf_file)
            results.append(result)
            
            # Basic validation
            TestUtils.assert_processing_result(result)
            assert result["file_type"] == "pdf"
        
        # Verify all results are different
        contents = [r["content"] for r in results]
        assert len(set(contents)) == len(contents), "All processed documents should have different content"
        
        logger.info(f"✅ Processed {len(results)} PDF documents successfully")
    
    def test_file_type_detection(self, document_processor):
        """Test file type detection."""
        test_cases = [
            ("test.pdf", "pdf"),
            ("test.PDF", "pdf"),
            ("test.docx", "docx"),
            ("test.txt", "txt"),
            ("test.md", "md"),
            ("test.html", "html"),
            ("test.unknown", "txt")  # Should default to txt
        ]
        
        for filename, expected_type in test_cases:
            file_path = Path(filename)
            file_type = document_processor.get_file_type(file_path)
            assert file_type.value == expected_type, f"Expected {expected_type}, got {file_type.value} for {filename}"
        
        logger.info("✅ File type detection working correctly")
    
    def test_visual_file_detection(self, document_processor):
        """Test visual file type detection."""
        from processors.unified_document_processor import FileType
        
        visual_types = [FileType.PDF, FileType.PPT, FileType.PPTX]
        non_visual_types = [FileType.DOC, FileType.DOCX, FileType.TXT, FileType.MD, FileType.HTML, FileType.XML]
        
        for file_type in visual_types:
            assert document_processor.is_visual_file(file_type), f"{file_type.value} should be visual"
        
        for file_type in non_visual_types:
            assert not document_processor.is_visual_file(file_type), f"{file_type.value} should not be visual"
        
        logger.info("✅ Visual file detection working correctly")


class TestDocumentWorker:
    """Test document worker functionality."""
    
    @pytest.mark.requires_openai
    async def test_worker_initialization(self, document_worker, test_config):
        """Test document worker initialization."""
        worker_info = document_worker.get_worker_info()
        
        assert "processor_info" in worker_info
        assert "chunker_config" in worker_info
        
        processor_info = worker_info["processor_info"]
        assert processor_info["gpt_model"] == test_config.GPT_MODEL
        
        logger.info("✅ Document worker initialized correctly")
    
    @pytest.mark.requires_openai
    @pytest.mark.integration
    async def test_single_document_processing(self, document_worker, vector_store, test_config):
        """Test processing and storing a single document."""
        test_files = test_config.get_existing_test_files()
        if not test_files:
            pytest.skip("No test files available")
        
        # Use first available file
        test_file = test_files[0]
        test_collection = f"{test_config.TEST_COLLECTION}_single"
        
        try:
            # Setup collection
            await vector_store.ensure_collection_exists(test_collection, test_config.EMBED_DIMENSION)
            
            # Process document
            logger.info(f"Processing single document: {test_file.name}")
            result = await document_worker.process_document(
                file_path=test_file,
                collection_name=test_collection,
                metadata=TestUtils.create_test_metadata("single_document_test")
            )
            
            # Validate result
            TestUtils.assert_worker_result(result)
            assert result["total_documents"] == 1
            assert result["successful"] == 1
            assert result["failed"] == 0
            assert result["total_chunks"] > 0
            assert result["total_points"] > 0
            
            # Verify data in vector store
            collection_info = await vector_store.get_collection_info(test_collection)
            assert collection_info["points_count"] == result["total_points"]
            
            logger.info(f"✅ Single document processing successful:")
            logger.info(f"   Chunks: {result['total_chunks']}")
            logger.info(f"   Points: {result['total_points']}")
            
        finally:
            await vector_store.delete_collection(test_collection)
    
    @pytest.mark.requires_openai
    @pytest.mark.integration
    @pytest.mark.slow
    async def test_multiple_document_processing(self, document_worker, vector_store, test_config):
        """Test processing and storing multiple documents."""
        test_files = test_config.get_existing_test_files()
        if len(test_files) < 2:
            pytest.skip("Need at least 2 test files for this test")
        
        test_collection = f"{test_config.TEST_COLLECTION}_multiple"
        
        try:
            # Setup collection
            await vector_store.ensure_collection_exists(test_collection, test_config.EMBED_DIMENSION)
            
            # Process multiple documents
            logger.info(f"Processing {len(test_files)} documents")
            result = await document_worker.process_multiple_documents(
                file_paths=test_files,
                collection_name=test_collection,
                metadata=TestUtils.create_test_metadata("multiple_document_test")
            )
            
            # Validate result
            TestUtils.assert_worker_result(result)
            assert result["total_documents"] == len(test_files)
            assert result["successful"] >= 1  # At least one should succeed
            assert result["total_chunks"] > 0
            assert result["total_points"] > 0
            
            # Verify data in vector store
            collection_info = await vector_store.get_collection_info(test_collection)
            assert collection_info["points_count"] == result["total_points"]
            
            # Check individual results
            successful_results = [r for r in result["results"] if r.get("success")]
            failed_results = [r for r in result["results"] if not r.get("success")]
            
            logger.info(f"✅ Multiple document processing completed:")
            logger.info(f"   Total: {result['total_documents']}")
            logger.info(f"   Successful: {len(successful_results)}")
            logger.info(f"   Failed: {len(failed_results)}")
            logger.info(f"   Total Chunks: {result['total_chunks']}")
            logger.info(f"   Total Points: {result['total_points']}")
            
            # Log failed results for debugging
            for failed_result in failed_results:
                logger.warning(f"   Failed: {failed_result.get('file_path', 'unknown')} - {failed_result.get('error', 'unknown error')}")
            
        finally:
            await vector_store.delete_collection(test_collection)
    
    @pytest.mark.requires_openai
    @pytest.mark.integration
    async def test_document_chunking(self, document_worker, test_config):
        """Test document chunking functionality."""
        test_files = test_config.get_existing_test_files()
        if not test_files:
            pytest.skip("No test files available")
        
        test_file = test_files[0]
        
        # Process document without storing
        logger.info(f"Testing chunking with: {test_file.name}")
        result = await document_worker.process_document(
            file_path=test_file,
            collection_name="dummy_collection",  # Won't be used
            metadata=TestUtils.create_test_metadata("chunking_test"),
            store_vectors=False  # Don't store, just test chunking
        )
        
        # Validate chunking result
        assert result["total_chunks"] > 0, "Should create at least one chunk"
        assert result["total_points"] == 0, "Should not store vectors when store_vectors=False"
        
        # Check chunk details
        document_result = result["results"][0]
        if document_result.get("success"):
            chunks = document_result.get("chunks", [])
            assert len(chunks) > 0, "Should have chunks"
            
            # Validate chunk structure
            for chunk in chunks:
                assert "text" in chunk, "Chunk should have text"
                assert "metadata" in chunk, "Chunk should have metadata"
                assert len(chunk["text"]) > 0, "Chunk text should not be empty"
            
            logger.info(f"✅ Document chunking successful: {len(chunks)} chunks created")
            logger.info(f"   Average chunk length: {sum(len(c['text']) for c in chunks) / len(chunks):.0f} characters")
        else:
            logger.warning(f"Document processing failed: {document_result.get('error')}")


class TestVectorStorage:
    """Test vector storage and retrieval functionality."""
    
    @pytest.mark.integration
    async def test_vector_storage_workflow(self, vector_store, embedding_service, test_config):
        """Test complete vector storage workflow."""
        test_collection = f"{test_config.TEST_COLLECTION}_storage"
        
        try:
            # Setup collection
            await vector_store.ensure_collection_exists(test_collection, test_config.EMBED_DIMENSION)
            
            # Create test data
            test_texts = [
                "This is a test document about artificial intelligence.",
                "Machine learning is a subset of artificial intelligence.",
                "Deep learning uses neural networks for pattern recognition.",
                "Natural language processing helps computers understand text.",
                "Computer vision enables machines to interpret visual information."
            ]
            
            # Generate embeddings
            embeddings = await embedding_service.generate_embeddings(test_texts)
            
            # Create points
            points = [{
                "id": i,  # Use integer ID instead of string
                "vector": embeddings[i],
                "payload": {
                    "text": test_texts[i],
                    "index": i,
                    "category": "test"
                }
            } for i in range(len(test_texts))]
            
            # Store vectors
            await vector_store.upsert_points(test_collection, points)
            logger.info(f"✅ Stored {len(points)} vectors")
            
            # Verify storage
            collection_info = await vector_store.get_collection_info(test_collection)
            assert collection_info["points_count"] == len(points)
            
            # Test search
            query_text = "artificial intelligence machine learning"
            embeddings = await embedding_service.generate_embeddings([query_text])
            query_embedding = embeddings[0]
            
            search_results = await vector_store.search(
                collection_name=test_collection,
                query_vector=query_embedding,
                limit=3
            )
            
            assert len(search_results) > 0, "Search should return results"
            assert len(search_results) <= 3, "Should respect limit"
            
            # Verify search result structure
            for result in search_results:
                assert "id" in result, "Search result should have id"
                assert "score" in result, "Search result should have score"
                assert "payload" in result, "Search result should have payload"
                assert "text" in result["payload"], "Payload should have text"
            
            logger.info(f"✅ Vector storage workflow successful:")
            logger.info(f"   Stored: {len(points)} vectors")
            logger.info(f"   Retrieved: {len(search_results)} results")
            
            # Log top search results
            for i, result in enumerate(search_results[:2]):
                logger.info(f"   Result {i+1}: {result['payload']['text'][:50]}... (score: {result['score']:.3f})")
            
        finally:
            await vector_store.delete_collection(test_collection)
    
    @pytest.mark.integration
    async def test_vector_search_accuracy(self, vector_store, embedding_service, test_config):
        """Test vector search accuracy with known similar documents."""
        test_collection = f"{test_config.TEST_COLLECTION}_accuracy"
        
        try:
            await vector_store.ensure_collection_exists(test_collection, test_config.EMBED_DIMENSION)
            
            # Create test documents with known relationships
            documents = [
                {"text": "Python is a programming language", "category": "programming"},
                {"text": "Java is also a programming language", "category": "programming"},
                {"text": "Dogs are domestic animals", "category": "animals"},
                {"text": "Cats are also domestic animals", "category": "animals"},
                {"text": "Cars are vehicles for transportation", "category": "vehicles"},
                {"text": "Bicycles are also vehicles", "category": "vehicles"}
            ]
            
            # Store documents
            embeddings = await embedding_service.generate_embeddings([doc["text"] for doc in documents])
            points = [{
                "id": i,  # Use integer ID instead of string
                "vector": embeddings[i],
                "payload": documents[i]
            } for i in range(len(documents))]
            
            await vector_store.upsert_points(test_collection, points)
            
            # Test semantic search
            test_queries = [
                ("programming languages", "programming"),
                ("domestic pets", "animals"),
                ("transportation methods", "vehicles")
            ]
            
            for query_text, expected_category in test_queries:
                embeddings = await embedding_service.generate_embeddings([query_text])
                query_embedding = embeddings[0]
                results = await vector_store.search(
                    collection_name=test_collection,
                    query_vector=query_embedding,
                    limit=2
                )
                
                # Check if top results match expected category
                top_result = results[0] if results else None
                if top_result:
                    actual_category = top_result["payload"]["category"]
                    assert actual_category == expected_category, f"Query '{query_text}' should return {expected_category}, got {actual_category}"
                    logger.info(f"✅ Query '{query_text}' correctly returned {actual_category}")
            
        finally:
            await vector_store.delete_collection(test_collection)


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    @pytest.mark.requires_openai
    async def test_invalid_file_handling(self, document_processor):
        """Test handling of invalid or non-existent files."""
        # Test non-existent file
        non_existent_file = Path("non_existent_file.pdf")
        result = await document_processor.process_document(non_existent_file)
        
        assert "error" in result, "Should return error for non-existent file"
        assert result["content"].startswith("Error processing"), "Should have error message in content"
        
        logger.info("✅ Invalid file handling working correctly")
    
    @pytest.mark.integration
    async def test_empty_collection_handling(self, vector_store, embedding_service, test_config):
        """Test handling of empty collections."""
        test_collection = f"{test_config.TEST_COLLECTION}_empty"
        
        try:
            await vector_store.ensure_collection_exists(test_collection, test_config.EMBED_DIMENSION)
            
            # Search empty collection
            embeddings = await embedding_service.generate_embeddings(["test query"])
            query_embedding = embeddings[0]
            results = await vector_store.search(
                collection_name=test_collection,
                query_vector=query_embedding,
                limit=5
            )
            
            assert len(results) == 0, "Empty collection should return no results"
            logger.info("✅ Empty collection handling working correctly")
            
        finally:
            await vector_store.delete_collection(test_collection)
    
    @pytest.mark.requires_openai
    async def test_large_document_handling(self, document_processor, test_config):
        """Test handling of large documents."""
        test_files = test_config.get_existing_test_files()
        if not test_files:
            pytest.skip("No test files available")
        
        # Use the largest available file
        largest_file = max(test_files, key=lambda f: f.stat().st_size)
        logger.info(f"Testing large document: {largest_file.name} ({largest_file.stat().st_size} bytes)")
        
        result = await document_processor.process_document(largest_file)
        
        # Should either succeed or fail gracefully
        if "error" in result:
            logger.info(f"Large document processing failed gracefully: {result['error']}")
        else:
            TestUtils.assert_processing_result(result)
            logger.info(f"✅ Large document processing successful: {len(result['content'])} characters")
