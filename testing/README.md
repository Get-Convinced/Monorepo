# Testing Suite for AI Knowledge Agent

This directory contains all testing scripts and utilities for the AI Knowledge Agent project.

## Test Scripts

### 1. `test-infrastructure.sh`
Tests basic infrastructure components:
- PostgreSQL connection
- Redis connection  
- Qdrant connection
- Ollama connection

### 2. `test-services.sh`
Tests individual service health:
- Backend API health
- Document processor health
- Firecrawl health

### 3. `test-embeddings.sh`
Tests embedding functionality:
- Ollama embedding generation
- OpenAI embedding generation (if configured)
- Embedding dimension validation

### 4. `test-scraping.sh`
Tests complete scraping pipeline:
- Website scraping via Firecrawl
- Content processing and chunking
- Embedding generation
- Qdrant ingestion

### 5. `test-integration.sh`
Complete end-to-end integration test:
- Runs all above tests in sequence
- Validates complete pipeline

## Usage

### Run Individual Tests
```bash
cd testing
./test-infrastructure.sh
./test-services.sh
./test-embeddings.sh
./test-scraping.sh
```

### Run Complete Integration Test
```bash
cd testing
./test-integration.sh
```

## Prerequisites

1. **Services Running**: Ensure all Docker services are running:
   ```bash
   docker compose up -d
   ```

2. **Ollama Running**: Ensure Ollama is running with mxbai-embed-large model:
   ```bash
   ollama serve
   ollama pull mxbai-embed-large
   ```

3. **Document Processor**: Start the document processor service:
   ```bash
   cd apps/document-processor
   source .venv/bin/activate
   uvicorn src.main:app --host 0.0.0.0 --port 8081
   ```

## Configuration

Tests use the following default endpoints:
- Backend: http://localhost:8082
- Document Processor: http://localhost:8081
- Firecrawl: http://localhost:3002
- Qdrant: http://localhost:6336
- Ollama: http://localhost:11434

## Test Data

The tests use the following test URLs and data:
- Example.com for basic scraping tests
- Test collection names: `test_collection`, `integration_test`
- Sample text for embedding tests

## Troubleshooting

### Common Issues

1. **Service Not Running**: Check `docker compose ps` and service logs
2. **Port Conflicts**: Ensure no other services are using the required ports
3. **Ollama Model Missing**: Run `ollama pull mxbai-embed-large`
4. **Permission Issues**: Ensure test scripts are executable: `chmod +x *.sh`

### Logs

Check service logs for debugging:
```bash
docker compose logs -f [service_name]
```

Service names: `postgres`, `redis`, `qdrant`, `firecrawl`
