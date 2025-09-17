"""
Updated main.py using the new modular structure.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File
from pydantic import BaseModel
import os
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
from pathlib import Path
import sys

# Ensure local `src` modules are importable when run as a module
CURRENT_DIR = Path(__file__).parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

# Import our new modules
from embeddings import EmbeddingService, OllamaEmbeddingProvider, OpenAIEmbeddingProvider
from rag.vector_store import VectorStore
from workers import DoclingDocumentWorker, IngestionWorker
from rag import SearchService, RAGService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Knowledge Agent Document Processor")

# Configuration
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6336")
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "ollama")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "mxbai-embed-large")
EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", "1024"))
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize services
vector_store = VectorStore(qdrant_url=QDRANT_URL)

# Initialize embedding service based on provider
embedding_service = None
if EMBEDDING_PROVIDER == "ollama":
    embedding_service = EmbeddingService.create_ollama_provider(
        base_url=OLLAMA_BASE_URL,
        model=EMBEDDING_MODEL
    )
elif EMBEDDING_PROVIDER == "openai":
    if not OPENAI_API_KEY:
        raise ValueError("OpenAI API key required when using OpenAI provider")
    embedding_service = EmbeddingService.create_openai_provider(
        api_key=OPENAI_API_KEY,
        model=EMBEDDING_MODEL
    )
if embedding_service is None:
    raise ValueError(f"Unsupported embedding provider: {EMBEDDING_PROVIDER}")

# Initialize enhanced workers and services with chart extraction
docling_worker = DoclingDocumentWorker(
    embedding_service, 
    vector_store,
    enable_ocr=True,
    enable_vlm=True,
    enable_tables=True,
    enable_chart_extraction=True  # Enable chart extraction for PPT-to-PDF files
)
ingestion_worker = IngestionWorker(embedding_service, vector_store)
search_service = SearchService(vector_store, embedding_service)
rag_service = RAGService(search_service)

# Pydantic models
class DocumentUploadResponse(BaseModel):
    job_id: str
    status: str
    message: str
    file_name: str

class JobStatus(BaseModel):
    job_id: str
    status: str
    file_name: Optional[str] = None
    chunks_processed: Optional[int] = None
    error: Optional[str] = None
    created_at: Optional[str] = None
    completed_at: Optional[str] = None

class SearchRequest(BaseModel):
    query: str
    collection_name: str = "knowledge_base"
    limit: int = 5
    score_threshold: float = 0.7

class SearchResponse(BaseModel):
    results: List[Dict[str, Any]]
    query: str
    total_results: int

class QuestionRequest(BaseModel):
    question: str
    collection_name: str = "knowledge_base"
    max_context_chunks: int = 3
    score_threshold: float = 0.7

class QuestionResponse(BaseModel):
    question: str
    answer: str
    context: str
    sources: List[Dict[str, Any]]
    context_found: bool
    confidence: float


@app.get("/health")
async def health():
    return {"status": "ok", "service": "document-processor"}


@app.get("/")
async def root():
    return {
        "service": "document-processor", 
        "env": os.getenv("APP_ENV", "local"),
        "embedding_provider": EMBEDDING_PROVIDER,
        "embedding_model": EMBEDDING_MODEL
    }


@app.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    collection_name: str = "knowledge_base",
    metadata: Optional[Dict[str, Any]] = None
):
    """Upload and process a document using Docling's advanced processing."""
    try:
        # Validate file type
        file_ext = Path(file.filename).suffix.lower()
        
        # Docling supports 95+ formats
        if not docling_worker.docling_processor.is_supported(Path(file.filename)):
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type: {file_ext}. Check supported formats at /supported-formats"
            )
        
        # Create temporary file
        temp_dir = Path("/tmp/document_processor")
        temp_dir.mkdir(exist_ok=True)
        
        temp_file_path = temp_dir / f"{uuid.uuid4()}{file_ext}"
        
        # Save uploaded file
        with open(temp_file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Create ingestion job
        job_id = ingestion_worker.create_job(
            file_paths=[str(temp_file_path)],
            collection_name=collection_name,
            metadata={**(metadata or {}), "processor": "docling"}
        )
        
        # Start background processing
        background_tasks.add_task(
            process_upload_job,
            job_id,
            str(temp_file_path)
        )
        
        return DocumentUploadResponse(
            job_id=job_id,
            status="started",
            message=f"Document upload started for {file.filename} using Docling processor",
            file_name=file.filename
        )
        
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


async def process_upload_job(job_id: str, file_path: str):
    """Process an upload job in the background using Docling."""
    try:
        # Use Docling worker for advanced processing
        await docling_worker.process_document(file_path, "knowledge_base")
    except Exception as e:
        logger.error(f"Error processing upload job {job_id}: {e}")
    finally:
        # Clean up temporary file
        temp_file = Path(file_path)
        if temp_file.exists():
            temp_file.unlink()


@app.get("/jobs/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    """Get the status of a processing job."""
    job = ingestion_worker.get_job_status(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return JobStatus(**job)


@app.get("/jobs")
async def list_jobs(status: Optional[str] = None):
    """List all processing jobs."""
    jobs = ingestion_worker.list_jobs(status=status)
    return {"jobs": jobs}


@app.post("/search", response_model=SearchResponse)
async def search_knowledge(request: SearchRequest):
    """Search for relevant content in the knowledge base."""
    try:
        results = await search_service.search(
            query=request.query,
            collection_name=request.collection_name,
            limit=request.limit,
            score_threshold=request.score_threshold
        )
        
        return SearchResponse(
            results=results,
            query=request.query,
            total_results=len(results)
        )
        
    except Exception as e:
        logger.error(f"Error searching knowledge base: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.post("/ask", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest):
    """Ask a question and get relevant context."""
    try:
        response = await rag_service.ask_question(
            question=request.question,
            collection_name=request.collection_name,
            max_context_chunks=request.max_context_chunks,
            score_threshold=request.score_threshold
        )
        
        return QuestionResponse(**response)
        
    except Exception as e:
        logger.error(f"Error processing question: {e}")
        raise HTTPException(status_code=500, detail=f"Question processing failed: {str(e)}")


@app.get("/collections")
async def list_collections():
    """List all QDrant collections."""
    try:
        collections = await vector_store.list_collections()
        return {"collections": collections}
    except Exception as e:
        logger.error(f"Error listing collections: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list collections: {str(e)}")


@app.get("/collections/{collection_name}/info")
async def get_collection_info(collection_name: str):
    """Get information about a specific collection."""
    try:
        info = await vector_store.get_collection_info(collection_name)
        return {"collection_info": info}
    except Exception as e:
        logger.error(f"Error getting collection info: {e}")
        raise HTTPException(status_code=404, detail=f"Collection not found: {str(e)}")


@app.get("/supported-formats")
async def get_supported_formats():
    """Get list of supported file formats."""
    try:
        docling_formats = docling_worker.get_supported_formats()
        
    return {
            "supported_formats": {
                "count": len(docling_formats),
                "formats": docling_formats
            },
            "processor": "docling",
            "capabilities": [
                "Advanced PDF understanding",
                "OCR for scanned documents", 
                "Visual Language Models",
                "Table structure extraction",
                "95+ file formats supported"
            ]
        }
    except Exception as e:
        logger.error(f"Error getting supported formats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get supported formats: {str(e)}")


@app.get("/docling-capabilities")
async def get_docling_capabilities():
    """Get Docling processing capabilities."""
    try:
        capabilities = docling_worker.get_processing_capabilities()
        return capabilities
        except Exception as e:
        logger.error(f"Error getting Docling capabilities: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get capabilities: {str(e)}")


@app.post("/test-embeddings")
async def test_embeddings():
    """Test embedding generation with current configuration."""
    try:
        test_texts = ["This is a test sentence for embedding generation."]
        embeddings = await embedding_service.generate_embeddings(test_texts)
        
        return {
            "status": "ok",
            "provider": EMBEDDING_PROVIDER,
            "model": EMBEDDING_MODEL,
            "dimension": len(embeddings[0]) if embeddings else 0,
            "expected_dimension": EMBEDDING_DIMENSION,
            "test_successful": True
        }
    except Exception as e:
        return {
            "status": "error",
            "provider": EMBEDDING_PROVIDER,
            "model": EMBEDDING_MODEL,
            "error": str(e),
            "test_successful": False
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
