# Document Processor Test Suite

Comprehensive test suite for the document processor system, following DRY principles and providing both automated and manual testing capabilities.

## 🏗️ Test Structure

```
tests/
├── conftest.py                 # Shared configuration and fixtures
├── test_system_health.py      # System health check tests
├── test_document_processing.py # Document processing and ingestion tests
├── manual_rag_tests.py        # Manual RAG and retrieval tests
├── test_data/                 # Test data files
│   ├── Bizom _ Discussion Deck.pdf
│   ├── Bizom _ Omnichannel_Celesta.pdf
│   └── Bizom _ Pitch Deck_Full Deck_UI Updated.pdf
└── README.md                  # This file
```

## 🚀 Quick Start

### Prerequisites

1. **Environment Setup**
   
   **Option 1: Using .env files (Recommended)**
   ```bash
   # Create .env.local file in the document-processor directory
   echo "OPENAI_API_KEY=your-openai-api-key" > .env.local
   echo "QDRANT_URL=http://localhost:6336" >> .env.local
   echo "OLLAMA_BASE_URL=http://localhost:11434" >> .env.local
   echo "EMBED_MODEL=mxbai-embed-large" >> .env.local
   echo "GPT_MODEL=gpt-4o" >> .env.local
   ```
   
   **Option 2: Environment variables**
   ```bash
   # Set required environment variables
   export OPENAI_API_KEY="your-openai-api-key"
   export QDRANT_URL="http://localhost:6336"
   export OLLAMA_BASE_URL="http://localhost:11434"
   export EMBED_MODEL="mxbai-embed-large"
   export GPT_MODEL="gpt-4o"
   ```

2. **Service Dependencies**
   - Qdrant vector database running on port 6336
   - Ollama service running on port 11434 with mxbai-embed-large model
   - OpenAI API access (for GPT models and RAG)

3. **Install Dependencies**
   ```bash
   cd apps/document-processor
   pip install -r requirements.txt
   ```

### Running Tests

#### Using the Test Runner (Recommended)

```bash
# Run all quick tests (default)
python run_tests.py

# Run specific test suites
python run_tests.py --system      # System health checks
python run_tests.py --process     # Document processing tests
python run_tests.py --integration # Integration tests
python run_tests.py --unit        # Unit tests
python run_tests.py --quick       # Quick tests (exclude slow)
python run_tests.py --all         # All automated tests
python run_tests.py --manual      # Manual RAG tests

# Run with verbose output
python run_tests.py --system --verbose
```

#### Using pytest directly

```bash
# Run all tests
pytest tests/

# Run specific test files
pytest tests/test_system_health.py
pytest tests/test_document_processing.py

# Run with markers
pytest tests/ -m "integration"
pytest tests/ -m "not slow"
pytest tests/ -m "requires_openai"

# Run with verbose output
pytest tests/ -v
```

## 📋 Test Categories

### 1. System Health Tests (`test_system_health.py`)

**Purpose**: Verify that all required systems are running and properly configured.

**Tests Include**:
- ✅ Qdrant database connectivity
- ✅ Ollama embedding service availability
- ✅ OpenAI API access
- ✅ Test data file availability
- ✅ Environment configuration validation
- ✅ Full system integration workflow
- ✅ Performance benchmarks

**Markers**: `integration`, `requires_qdrant`, `requires_ollama`, `requires_openai`

### 2. Document Processing Tests (`test_document_processing.py`)

**Purpose**: Test document processing, chunking, embedding, and storage in Qdrant.

**Tests Include**:
- ✅ Document processor initialization
- ✅ PDF processing with GPT models
- ✅ File type detection
- ✅ Document worker functionality
- ✅ Single and multiple document processing
- ✅ Document chunking
- ✅ Vector storage workflow
- ✅ Search accuracy testing
- ✅ Error handling and edge cases

**Markers**: `integration`, `requires_openai`, `slow`

### 3. Manual RAG Tests (`manual_rag_tests.py`)

**Purpose**: Interactive testing of RAG functionality for manual evaluation.

**Features**:
- 🤖 Interactive RAG question-answering
- 🔍 Vector search testing
- 📊 Collection statistics
- 🎯 Predefined test scenarios
- 📄 Document ingestion workflow

**Usage**:
```bash
python tests/manual_rag_tests.py
```

## 🏷️ Test Markers

The test suite uses pytest markers for categorization:

- `unit`: Unit tests (fast, isolated)
- `integration`: Integration tests (require external services)
- `slow`: Slow-running tests (may take several minutes)
- `requires_openai`: Tests requiring OpenAI API key
- `requires_qdrant`: Tests requiring Qdrant database
- `requires_ollama`: Tests requiring Ollama service

## 🔧 Configuration

### Environment Variables

The test suite automatically loads environment variables from the following files (in order):
1. `.env.local` - Local development settings (recommended)
2. `.env` - General environment settings
3. `.env.test` - Test-specific settings

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | - | OpenAI API key for GPT models |
| `QDRANT_URL` | `http://localhost:6336` | Qdrant database URL |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama service URL |
| `EMBED_MODEL` | `mxbai-embed-large` | Embedding model name |
| `EMBED_DIMENSION` | `1024` | Embedding vector dimension |
| `GPT_MODEL` | `gpt-4o` | GPT model for processing |
| `TEST_COLLECTION` | `test_documents` | Test collection name |

### Test Configuration (`conftest.py`)

The test configuration provides:
- **TestConfig**: Centralized configuration management
- **Fixtures**: Shared test fixtures for services and components
- **TestUtils**: Utility functions for test assertions
- **Markers**: Automatic test categorization

## 📊 Test Data

### Available Test Files

The test suite includes three Bizom PDF documents:
- `Bizom _ Discussion Deck.pdf` - Business discussion presentation
- `Bizom _ Omnichannel_Celesta.pdf` - Omnichannel solution overview
- `Bizom _ Pitch Deck_Full Deck_UI Updated.pdf` - Complete pitch deck

### Adding Test Data

To add new test files:
1. Place files in `tests/test_data/`
2. Update `TestConfig.get_test_files()` if needed
3. Tests will automatically discover available files

## 🎯 Manual Testing Workflow

### 1. System Health Check
```bash
python run_tests.py --system
```

### 2. Document Processing Test
```bash
python run_tests.py --process
```

### 3. Manual RAG Testing
```bash
python run_tests.py --manual
```

### 4. Full Integration Test
```bash
python run_tests.py --all
```

## 🐛 Troubleshooting

### Common Issues

1. **Qdrant Connection Failed**
   ```bash
   # Check if Qdrant is running
   curl http://localhost:6336/health
   
   # Start Qdrant with Docker
   docker run -p 6333:6333 -p 6336:6336 qdrant/qdrant
   ```

2. **Ollama Service Unavailable**
   ```bash
   # Check if Ollama is running
   curl http://localhost:11434/api/tags
   
   # Start Ollama service
   ollama serve
   
   # Pull required model
   ollama pull mxbai-embed-large
   ```

3. **OpenAI API Key Missing**
   ```bash
   # Set API key
   export OPENAI_API_KEY="your-api-key-here"
   
   # Or create .env file
   echo "OPENAI_API_KEY=your-api-key-here" > .env
   ```

4. **Test Data Not Found**
   ```bash
   # Check test data directory
   ls -la tests/test_data/
   
   # Add PDF files to tests/test_data/
   ```

### Debug Mode

Run tests with debug output:
```bash
python run_tests.py --system --verbose
pytest tests/ -v -s --tb=long
```

## 📈 Performance Expectations

### Test Execution Times

- **System Health Tests**: ~30 seconds
- **Document Processing Tests**: ~2-5 minutes (depends on document size)
- **Manual RAG Tests**: Interactive (user-controlled)
- **Full Test Suite**: ~5-10 minutes

### Performance Benchmarks

- **Single Embedding**: < 5 seconds
- **Batch Embedding**: < 10 seconds
- **Vector Storage**: < 5 seconds
- **Vector Search**: < 2 seconds

## 🔄 Continuous Integration

### GitHub Actions Example

```yaml
name: Document Processor Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      qdrant:
        image: qdrant/qdrant
        ports:
          - 6333:6333
          - 6336:6336
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        cd apps/document-processor
        pip install -r requirements.txt
    
    - name: Run system health tests
      run: |
        cd apps/document-processor
        python run_tests.py --system
      env:
        OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

## 📝 Contributing

### Adding New Tests

1. **Follow DRY Principles**: Use shared fixtures and utilities
2. **Use Appropriate Markers**: Mark tests with relevant categories
3. **Include Documentation**: Add docstrings and comments
4. **Test Edge Cases**: Include error handling and edge cases
5. **Performance Considerations**: Mark slow tests appropriately

### Test Naming Conventions

- Test files: `test_*.py`
- Test classes: `Test*`
- Test methods: `test_*`
- Fixtures: `*_fixture` or descriptive names

### Example Test Structure

```python
class TestNewFeature:
    """Test new feature functionality."""
    
    @pytest.mark.integration
    @pytest.mark.requires_openai
    async def test_feature_functionality(self, document_processor, test_config):
        """Test specific feature functionality."""
        # Arrange
        test_file = test_config.get_existing_test_files()[0]
        
        # Act
        result = await document_processor.process_document(test_file)
        
        # Assert
        TestUtils.assert_processing_result(result)
        assert result["feature_specific_field"] == expected_value
```

## 📚 Additional Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [Ollama Documentation](https://ollama.ai/docs)
- [OpenAI API Documentation](https://platform.openai.com/docs)
