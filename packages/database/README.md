# Shared Database Package

This package provides shared database models, migrations, and utilities for the AI Knowledge Agent monorepo.

## Features

- **Comprehensive Schema**: Tracks ingestion jobs, processed documents, vector store references, and processing statistics
- **Async Support**: Full async/await support with SQLAlchemy 2.0
- **Migration Management**: Alembic-based migrations for schema versioning
- **Service Layer**: High-level database operations for both backend and document-processor apps
- **Type Safety**: Full type hints and Pydantic integration

## Database Schema

### Core Tables

1. **`ingestion_jobs`** - Track document ingestion jobs and their status
2. **`processed_documents`** - Individual document processing results with rich metadata
3. **`vector_store_references`** - Links between processed documents and Qdrant vector points
4. **`processing_statistics`** - Performance metrics and statistics
5. **`system_configuration`** - System-wide configuration storage
6. **`processing_logs`** - Detailed processing logs for debugging

### Key Features

- **Deduplication**: File hash-based deduplication across collections
- **Rich Metadata**: Stores processor-specific metadata (GPT tokens, Docling elements, etc.)
- **Performance Tracking**: Processing duration, token usage, error tracking
- **Vector Store Integration**: Tracks Qdrant collection and point references
- **Audit Trail**: Complete processing history with timestamps

## Installation

```bash
# Install in development mode
cd packages/database
pip install -e .

# Or install with dev dependencies
pip install -e ".[dev]"
```

## Usage

### In Backend App

```python
from shared_database import DatabaseClient, DocumentProcessingService
from shared_database.database import get_async_session

# FastAPI dependency
@app.post("/upload")
async def upload_document(
    file: UploadFile,
    session: AsyncSession = Depends(get_async_session)
):
    service = DocumentProcessingService(session)
    
    # Create ingestion job
    job = await service.create_ingestion_job(
        collection_name="knowledge_base",
        file_paths=[file.filename],
        metadata={"source": "web_upload"}
    )
    
    return {"job_id": job.id}
```

### In Document Processor App

```python
from shared_database import DocumentProcessingService, ProcessingStatus
from shared_database.models import ProcessorType

# Update processing results
await service.update_document_processing_result(
    document_id=document.id,
    status=ProcessingStatus.COMPLETED,
    processing_metadata=result.get("metadata", {}),
    vector_point_ids=point_ids,
    total_chunks_created=len(chunks),
    processing_duration_seconds=duration
)
```

## Database Setup

### 1. Environment Variables

```bash
# .env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=ai_knowledge_agent
DB_USER=postgres
DB_PASSWORD=postgres
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
```

### 2. Create Database

```bash
# Using Docker Compose (recommended)
docker-compose up -d postgres

# Or manually
createdb ai_knowledge_agent
```

### 3. Run Migrations

```bash
# Initialize Alembic (first time only)
alembic init alembic

# Create initial migration
alembic revision --autogenerate -m "Initial schema"

# Apply migrations
alembic upgrade head
```

## Integration with Apps

### Backend App Integration

1. Add dependency to `apps/backend/pyproject.toml`:
```toml
dependencies = [
    # ... existing dependencies
    "shared-database @ file://../../packages/database",
]
```

2. Use in FastAPI endpoints for job management and status tracking

### Document Processor App Integration

1. Add dependency to `apps/document-processor/pyproject.toml`:
```toml
dependencies = [
    # ... existing dependencies
    "shared-database @ file://../../packages/database",
]
```

2. Replace in-memory job storage with database persistence
3. Add comprehensive logging and error tracking

## Development

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black src/
isort src/
```

### Type Checking

```bash
mypy src/
```

## Migration Workflow

1. **Modify Models**: Update `src/models.py`
2. **Generate Migration**: `alembic revision --autogenerate -m "Description"`
3. **Review Migration**: Check generated migration file
4. **Apply Migration**: `alembic upgrade head`
5. **Test**: Verify changes work correctly

## Architecture Benefits

- **Centralized Schema**: Single source of truth for database structure
- **Type Safety**: Shared models ensure consistency across apps
- **Migration Management**: Proper schema versioning and rollback capability
- **Performance**: Optimized queries with proper indexing
- **Scalability**: Designed for high-volume document processing
- **Observability**: Comprehensive logging and statistics tracking