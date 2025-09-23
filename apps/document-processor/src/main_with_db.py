"""
Updated main.py using database-backed ingestion worker.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File, Depends
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

# Import our modules
from embeddings import EmbeddingService, OllamaEmbeddingProvider, OpenAIEmbeddingProvider
from rag.vector_store import VectorStore
from workers.database_ingestion_worker import DatabaseIngestionWorker
from workers.docling_document_worker import DoclingDocumentWorker
from rag import SearchService, RAGService
from processors.unified_document_processor import GPTModel

# Import database components
from shared_database import (
    DatabaseClient, 
    get_async_session,
    ProcessingStatus,
    DocumentProcessingService,
    LoggingService
)
from sqlalchemy.ext.asyncio import AsyncSession

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Knowledge Agent Document Processor (Database-backed)")

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

# Initialize search and RAG services
search_service = SearchService(vector_store, embedding_service)
rag_service = RAGService(search_service)

# Initialize database client
db_client = DatabaseClient()

# Pydantic models
class DocumentUploadResponse(BaseModel):
    job_id: str
    status: str
    message: str
    file_name: str

class JobStatusResponse(BaseModel):
    id: str
    collection_name: str
    status: str
    created_at: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    total_files: int
    successful_files: int
    failed_files: int
    total_chunks_created: int
    error_message: Optional[str] = None
    documents: List[Dict[str, Any]] = []

class JobListResponse(BaseModel):
    jobs: List[Dict[str, Any]]
    total: int
    limit: int
    offset: int

class ProcessingStatsResponse(BaseModel):
    date_range: Dict[str, Any]
    status_breakdown: Dict[str, int]
    processor_breakdown: Dict[str, int]
    file_type_breakdown: Dict[str, int]

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


def get_database_ingestion_worker(session: AsyncSession = Depends(get_async_session)) -> DatabaseIngestionWorker:
    """Dependency to get database ingestion worker."""
    return DatabaseIngestionWorker(
        db_session=session,
        embedding_service=embedding_service,
        vector_store=vector_store,
        openai_api_key=OPENAI_API_KEY or "",
        gpt_model=GPTModel.GPT_4O,
        use_unified_worker=True
    )


@app.get("/health")
async def health():
    return {"status": "ok", "service": "document-processor-db"}


@app.get("/")
async def root():
    return {
        "service": "document-processor-db", 
        "env": os.getenv("APP_ENV", "local"),
        "embedding_provider": EMBEDDING_PROVIDER,
        "embedding_model": EMBEDDING_MODEL,
        "database_enabled": True
    }


@app.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    collection_name: str = "knowledge_base",
    metadata: Optional[Dict[str, Any]] = None,
    worker: DatabaseIngestionWorker = Depends(get_database_ingestion_worker)
):
    """Upload and process a document using database-backed processing."""
    try:
        # Validate file type (basic validation)
        file_ext = Path(file.filename).suffix.lower()
        if not file_ext:
            raise HTTPException(
                status_code=400, 
                detail="File must have an extension"
            )
        
        # Create temporary file
        temp_dir = Path("/tmp/document_processor")
        temp_dir.mkdir(exist_ok=True)
        
        temp_file_path = temp_dir / f"{uuid.uuid4()}{file_ext}"
        
        # Save uploaded file
        with open(temp_file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Create database job
        job_id = await worker.create_job(
            file_paths=[str(temp_file_path)],
            collection_name=collection_name,
            metadata={
                **(metadata or {}), 
                "source": "web_upload",
                "original_filename": file.filename,
                "file_extension": file_ext
            },
            created_by="web_user"
        )
        
        # Start background processing
        background_tasks.add_task(
            process_upload_job_with_db,
            job_id,
            str(temp_file_path)
        )
        
        return DocumentUploadResponse(
            job_id=str(job_id),
            status="started",
            message=f"Document upload started for {file.filename} using database-backed processing",
            file_name=file.filename
        )
        
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


async def process_upload_job_with_db(job_id: str, file_path: str):
    """Process an upload job in the background using database worker."""
    try:
        async with db_client.async_session() as session:
            worker = DatabaseIngestionWorker(
                db_session=session,
                embedding_service=embedding_service,
                vector_store=vector_store,
                openai_api_key=OPENAI_API_KEY or "",
                gpt_model=GPTModel.GPT_4O,
                use_unified_worker=True
            )
            
            await worker.process_job(uuid.UUID(job_id))
            
    except Exception as e:
        logger.error(f"Error processing upload job {job_id}: {e}")
    finally:
        # Clean up temporary file
        temp_file = Path(file_path)
        if temp_file.exists():
            temp_file.unlink()


@app.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: str,
    worker: DatabaseIngestionWorker = Depends(get_database_ingestion_worker)
):
    """Get the status of a processing job."""
    try:
        job_data = await worker.get_job_status(uuid.UUID(job_id))
        if not job_data:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return JobStatusResponse(**job_data)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting job status {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/jobs", response_model=JobListResponse)
async def list_jobs(
    status: Optional[str] = None,
    collection_name: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    worker: DatabaseIngestionWorker = Depends(get_database_ingestion_worker)
):
    """List processing jobs with optional filters."""
    try:
        # Convert string status to enum if provided
        status_enum = None
        if status:
            try:
                status_enum = ProcessingStatus(status)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        
        jobs = await worker.list_jobs(
            status=status_enum,
            collection_name=collection_name,
            limit=limit,
            offset=offset
        )
        
        return JobListResponse(
            jobs=jobs,
            total=len(jobs),
            limit=limit,
            offset=offset
        )
        
    except Exception as e:
        logger.error(f"Error listing jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats", response_model=ProcessingStatsResponse)
async def get_processing_statistics(
    worker: DatabaseIngestionWorker = Depends(get_database_ingestion_worker)
):
    """Get processing statistics."""
    try:
        stats = await worker.get_processing_statistics()
        return ProcessingStatsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Error getting processing statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search", response_model=SearchResponse)
async def search_documents(request: SearchRequest):
    """Search for documents using vector similarity."""
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
        logger.error(f"Error searching documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ask", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest):
    """Ask a question and get an AI-generated answer with context."""
    try:
        response = await rag_service.ask_question(
            question=request.question,
            collection_name=request.collection_name,
            max_context_chunks=request.max_context_chunks,
            score_threshold=request.score_threshold
        )
        
        return QuestionResponse(**response)
        
    except Exception as e:
        logger.error(f"Error asking question: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/collections")
async def list_collections():
    """List all available collections."""
    try:
        collections = await vector_store.list_collections()
        return {"collections": collections}
        
    except Exception as e:
        logger.error(f"Error listing collections: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/supported-formats")
async def get_supported_formats():
    """Get list of supported file formats."""
    return {
        "visual_processing": ["pdf", "ppt", "pptx"],
        "structural_processing": ["doc", "docx", "txt", "md", "html", "xml"],
        "note": "Visual processing uses GPT models, structural processing uses Docling"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


