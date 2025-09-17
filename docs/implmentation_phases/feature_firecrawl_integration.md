# Feature: Firecrawl Integration for Website Scraping

## Overview
Integration of Firecrawl service into the document processor for website scraping and content ingestion into Qdrant vector database.

## Implementation Status: ✅ COMPLETED

## Components Added

### 1. Docker Compose Integration
- Added Firecrawl service to `docker-compose.yml`
- Configured with Redis and PostgreSQL dependencies
- Exposed on port 3002
- Uses shared Redis and PostgreSQL instances

### 2. Document Processor Enhancements
- **New Dependencies**: httpx, openai, tiktoken, langchain-text-splitters
- **New Endpoints**:
  - `POST /scrape` - Scrape URL and ingest to Qdrant
  - `GET /collections` - List Qdrant collections
  - `GET /collections/{name}/info` - Get collection details
  - `POST /test-firecrawl` - Test Firecrawl connectivity

### 3. Core Features
- **Web Scraping**: Uses Firecrawl API to scrape websites with markdown output
- **Content Processing**: Chunks content using RecursiveCharacterTextSplitter
- **Embeddings**: Generates embeddings using OpenAI text-embedding-3-small
- **Vector Storage**: Stores in Qdrant with metadata (URL, title, chunk index, etc.)
- **Background Processing**: Async job processing for scraping tasks

### 4. Configuration
- Environment variables for Firecrawl URL, Qdrant URL, OpenAI API key
- Configurable chunk size and overlap
- Local environment file created

### 5. Testing & Documentation
- Updated `LOCAL_DEVELOPMENT.md` with Firecrawl instructions
- Created `test-scraping.sh` script for end-to-end testing
- Added smoke tests for all services

## API Usage Examples

### Scrape a Website
```bash
curl -X POST http://localhost:8081/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "collection_name": "knowledge_base",
    "metadata": {"source": "website", "category": "documentation"}
  }'
```

### List Collections
```bash
curl -s http://localhost:8081/collections
```

### Get Collection Info
```bash
curl -s http://localhost:8081/collections/knowledge_base/info
```

## Architecture Flow
1. **Request**: Client sends URL to `/scrape` endpoint
2. **Scraping**: Document processor calls Firecrawl API
3. **Processing**: Content is chunked and embedded using OpenAI
4. **Storage**: Chunks with embeddings stored in Qdrant
5. **Response**: Job ID returned for tracking

## Requirements
- **OpenAI API Key**: Required for embedding generation
- **Firecrawl Service**: Running on port 3002
- **Qdrant**: Running on port 6336
- **Redis & PostgreSQL**: For Firecrawl's internal operations

## Testing
Run the integration test:
```bash
./test-scraping.sh
```

## Next Steps
- [ ] Add job status tracking and retrieval
- [ ] Implement retry logic for failed scraping jobs
- [ ] Add support for bulk URL processing
- [ ] Integrate with frontend knowledge sources UI
- [ ] Add content deduplication logic
- [ ] Implement crawling (multi-page) vs single page scraping
