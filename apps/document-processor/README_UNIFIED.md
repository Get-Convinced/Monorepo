# Unified Document Processor

A refactored document processing system that intelligently routes different file types to appropriate processors and stores all outputs in a vector database.

## Architecture

### File Type Routing
- **PDF/PPT files** → GPT models (gpt-4o, gpt-4o-mini, gpt-5) for visual analysis
- **Other files** → Docling processor for structural analysis
- **All outputs** → mxbai embedding → Qdrant vector storage

### Components

1. **UnifiedDocumentProcessor** - Routes files to appropriate processors
2. **UnifiedDocumentWorker** - Handles processing, embedding, and storage
3. **GPT4oVisualParser** - Visual analysis for PDF/PPT files
4. **DoclingProcessor** - Structural analysis for other files

## Supported File Types

### Visual Processing (GPT Models)
- PDF files
- PPT files  
- PPTX files

### Structural Processing (Docling)
- DOC/DOCX files
- TXT files
- MD files
- HTML files
- XML files

## Supported GPT Models

- `gpt-4o` - Full GPT-4o model for maximum visual intelligence
- `gpt-4o-mini` - Efficient GPT-4o-mini for cost-effective processing
- `gpt-5` - Cutting-edge GPT-5 model (when available)

## Usage

### Basic Usage

```python
import asyncio
from pathlib import Path
from embeddings import EmbeddingService
from rag.vector_store import VectorStore
from workers.unified_document_worker import UnifiedDocumentWorker
from processors.unified_document_processor import GPTModel

async def process_documents():
    # Initialize services
    vector_store = VectorStore(qdrant_url="http://localhost:6336")
    embedding_service = EmbeddingService.create_ollama_provider(
        base_url="http://localhost:11434",
        model="mxbai-embed-large"
    )
    
    # Initialize worker
    worker = UnifiedDocumentWorker(
        embedding_service=embedding_service,
        vector_store=vector_store,
        openai_api_key="your-openai-api-key",
        gpt_model=GPTModel.GPT_4O,  # or GPT_4O_MINI, GPT_5
        visual_extraction_dpi=600
    )
    
    # Process documents
    files = [Path("document.pdf"), Path("presentation.pptx"), Path("text.txt")]
    results = await worker.process_multiple_documents(
        file_paths=files,
        collection_name="my_collection"
    )
    
    print(f"Processed {results['successful']} documents")

asyncio.run(process_documents())
```

### Configuration Options

```python
worker = UnifiedDocumentWorker(
    embedding_service=embedding_service,
    vector_store=vector_store,
    openai_api_key=openai_api_key,
    gpt_model=GPTModel.GPT_4O,           # GPT model for visual processing
    text_chunk_size=1000,                # Chunk size for Docling
    text_chunk_overlap=200,              # Overlap between chunks
    visual_extraction_dpi=600,           # DPI for visual extraction
    enable_ocr=True,                     # Enable OCR in Docling
    enable_vlm=True,                     # Enable VLM in Docling
    enable_tables=True,                  # Enable table extraction
    enable_chart_extraction=True         # Enable chart extraction
)
```

## Environment Variables

```bash
# Required
export OPENAI_API_KEY="sk-your-openai-api-key"

# Optional
export QDRANT_URL="http://localhost:6336"
export OLLAMA_BASE_URL="http://localhost:11434"
export EMBED_MODEL="mxbai-embed-large"
export GPT_MODEL="gpt-4o"  # gpt-4o, gpt-4o-mini, gpt-5
```

## Testing

### Run Test Script

```bash
# Set your OpenAI API key
export OPENAI_API_KEY="sk-your-openai-api-key"

# Run test (modify file paths in script first)
python test_unified_processor.py
```

### Run Example

```bash
# Set your OpenAI API key
export OPENAI_API_KEY="sk-your-openai-api-key"

# Run example (modify file paths in script first)
python example_usage.py
```

## Processing Flow

1. **File Type Detection** - Determines if file is PDF/PPT (visual) or other (structural)
2. **Processor Selection** - Routes to GPT models or Docling based on file type
3. **Content Extraction** - Extracts content using appropriate processor
4. **Embedding Generation** - Generates embeddings using mxbai
5. **Vector Storage** - Stores in Qdrant vector database

## Output Structure

### GPT Processing (PDF/PPT)
```json
{
  "content": "Full GPT analysis output",
  "processor": "gpt_gpt-4o",
  "file_type": "pdf",
  "processing_method": "visual_analysis",
  "total_pages": 10,
  "page_metadata": [...],
  "token_usage": 1500
}
```

### Docling Processing (Other Files)
```json
{
  "content": "Extracted text content",
  "processor": "docling",
  "file_type": "txt",
  "processing_method": "structural_analysis",
  "metadata": {...},
  "structured_elements": {...}
}
```

## Benefits

- **Intelligent Routing** - Automatically selects best processor for each file type
- **Unified Interface** - Single API for all document types
- **Flexible Models** - Support for multiple GPT models
- **Vector Storage** - All outputs stored in searchable vector database
- **Scalable** - Easy to add new file types and processors

## Migration from Previous System

The new unified system replaces the previous hybrid approach with:
- Cleaner architecture
- Better separation of concerns
- More flexible model selection
- Unified embedding and storage pipeline
