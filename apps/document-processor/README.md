# Document Processor

A modular document processing service for ingesting PDF, DOCX, and PPT files into a QDrant vector database for AI-powered search and retrieval.

## Features

- **Multi-format Support**: Process PDF, DOCX, and PowerPoint files
- **Text Extraction**: Extract text content and metadata from documents
- **Chunking**: Split documents into manageable chunks for processing
- **Vector Embeddings**: Generate embeddings using OpenAI or Ollama
- **Vector Storage**: Store and search vectors in QDrant
- **RAG Support**: Retrieve relevant context for question answering
- **Background Processing**: Asynchronous document processing
- **Comprehensive Testing**: Full test suite with fixtures and sample data

## Architecture

```
src/
├── processors/          # Document processors for different file types
│   ├── base_processor.py
│   ├── pdf_processor.py
│   ├── docx_processor.py
│   └── ppt_processor.py
├── embeddings/          # Embedding generation and management
│   ├── providers.py
│   └── embedding_service.py
├── workers/             # Background workers for processing
│   ├── document_worker.py
│   └── ingestion_worker.py
├── rag/                 # RAG components
│   ├── vector_store.py
│   ├── search_service.py
│   └── rag_service.py
└── main.py             # FastAPI application

tests/                   # Test suite
├── conftest.py         # Pytest fixtures
├── test_processors.py  # Processor tests
├── test_embeddings.py  # Embedding tests
├── test_vector_store.py # Vector store tests
├── test_document_worker.py # Worker tests
├── test_integration.py # Integration tests
└── test_data/          # Sample documents

scripts/                 # Utility scripts
├── test_document_ingestion.py
├── run_tests.py
└── create_sample_documents.py
```

## Installation

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables**:
   ```bash
   export QDRANT_URL="http://localhost:6336"
   export EMBEDDING_PROVIDER="ollama"  # or "openai"
   export EMBEDDING_MODEL="mxbai-embed-large"
   export OLLAMA_BASE_URL="http://localhost:11434"
   export OPENAI_API_KEY="your-api-key"  # if using OpenAI
   ```

3. **Start required services**:
   - QDrant: `docker run -p 6333:6333 qdrant/qdrant`
   - Ollama (if using): `ollama serve`

## Usage

### Running the Service

```bash
# Using the new modular structure
python src/main_new.py

# Or with uvicorn
uvicorn src.main_new:app --host 0.0.0.0 --port 8000
```

### API Endpoints

#### Upload Document
```bash
curl -X POST "http://localhost:8000/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@document.pdf" \
  -F "collection_name=knowledge_base"
```

#### Search Knowledge Base
```bash
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "machine learning",
    "collection_name": "knowledge_base",
    "limit": 5
  }'
```

#### Ask Question
```bash
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is this document about?",
    "collection_name": "knowledge_base"
  }'
```

#### Check Job Status
```bash
curl "http://localhost:8000/jobs/{job_id}"
```

### Programmatic Usage

```python
from embeddings import EmbeddingService, OllamaEmbeddingProvider
from rag.vector_store import VectorStore
from workers import DocumentWorker

# Initialize services
embedding_service = EmbeddingService.create_ollama_provider()
vector_store = VectorStore()
document_worker = DocumentWorker(embedding_service, vector_store)

# Process a document
result = await document_worker.process_document(
    file_path="/path/to/document.pdf",
    collection_name="knowledge_base",
    metadata={"source": "test"}
)

print(f"Processed {result['chunks_processed']} chunks")
```

## Testing

### Run All Tests
```bash
python scripts/run_tests.py
```

### Run Specific Tests
```bash
python scripts/run_tests.py test_processors.py
```

### Create Sample Documents
```bash
python scripts/create_sample_documents.py
```

### Test Document Ingestion
```bash
python scripts/test_document_ingestion.py
```

### Using pytest directly
```bash
cd apps/document-processor
pytest tests/ -v --asyncio-mode=auto
```

## Document Processors

### PDF Processor
- Uses `pdfplumber` for better text extraction
- Falls back to `PyPDF2` if needed
- Extracts metadata including page count, creation date, etc.

### DOCX Processor
- Uses `python-docx` for Word document processing
- Extracts text from paragraphs, tables, headers, and footers
- Extracts document properties and statistics

### PPT Processor
- Uses `python-pptx` for PowerPoint processing
- Extracts text from slides, shapes, and tables
- Handles both `.ppt` and `.pptx` formats

## Embedding Providers

### Ollama Provider
- Local embedding generation
- Supports various models (mxbai-embed-large, etc.)
- No API key required

### OpenAI Provider
- Cloud-based embedding generation
- Requires API key
- Supports text-embedding-3-small, text-embedding-3-large, etc.

## Vector Store

- Uses QDrant for vector storage and search
- Supports cosine similarity search
- Configurable collection creation
- Filter support for metadata queries

## Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `QDRANT_URL` | `http://localhost:6336` | QDrant server URL |
| `EMBEDDING_PROVIDER` | `ollama` | Embedding provider (ollama/openai) |
| `EMBEDDING_MODEL` | `mxbai-embed-large` | Embedding model name |
| `EMBEDDING_DIMENSION` | `1024` | Vector dimension |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `OPENAI_API_KEY` | - | OpenAI API key (if using OpenAI) |

## Development

### Adding New Document Processors

1. Create a new processor class inheriting from `BaseDocumentProcessor`
2. Implement `extract_text()` and `extract_metadata()` methods
3. Add the processor to `DocumentWorker.processors`
4. Add tests in `tests/test_processors.py`

### Adding New Embedding Providers

1. Create a new provider class inheriting from `EmbeddingProvider`
2. Implement `generate_embeddings()` method
3. Add factory method to `EmbeddingService`
4. Add tests in `tests/test_embeddings.py`

## Troubleshooting

### Common Issues

1. **QDrant Connection Error**: Ensure QDrant is running on the correct port
2. **Ollama Connection Error**: Check if Ollama is running and the model is available
3. **OpenAI API Error**: Verify API key and model availability
4. **Document Processing Error**: Check file format support and file permissions

### Debug Mode

Set logging level to DEBUG for detailed logs:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## License

This project is part of the AI Knowledge Agent MVP implementation.
