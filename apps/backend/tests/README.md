# Backend Test Suite

Clean, organized test suite for the AI Knowledge Agent backend.

## 📁 Test Structure

```
tests/
├── test_auth.py           # All authentication tests (consolidated)
├── api/                   # API endpoint tests
│   └── test_ragie_routes.py
├── unit/                  # Unit tests
│   ├── adapters/
│   └── services/
├── conftest.py           # Test fixtures and configuration
├── run_tests.py          # Simple test runner
└── README.md            # This file
```

## 🧪 Running Tests

### Quick Start
```bash
# Run all tests
python tests/run_tests.py

# Run with coverage
python tests/run_tests.py --coverage

# Run specific test categories
python tests/run_tests.py --auth      # Authentication tests
python tests/run_tests.py --api       # API tests
python tests/run_tests.py --unit      # Unit tests

# Debug mode
python tests/run_tests.py --debug --verbose
```

### Direct pytest Usage
```bash
# All tests
pytest

# Specific test file
pytest tests/test_auth.py

# Specific test class
pytest tests/test_auth.py::TestAuthenticationSuccess

# With coverage
pytest --cov=src --cov-report=html
```

## 📋 Test Coverage

### Authentication Tests (`test_auth.py`)
- ✅ **Success Cases**: Public key retrieval, token verification, middleware
- ✅ **Failure Cases**: 401 Frontegg error, invalid tokens, missing headers
- ✅ **Auth Disabled**: Development mode with mock users
- ✅ **Ragie Integration**: API endpoints with authentication
- ✅ **Environment Config**: Dotenv loading and configuration
- ✅ **Performance**: Caching, concurrent requests

### API Tests (`api/`)
- ✅ **Ragie Routes**: Document management endpoints

### Unit Tests (`unit/`)
- ✅ **Services**: Business logic testing
- ✅ **Adapters**: External service integration

## 🔧 Debugging the 401 Error

The test suite includes comprehensive tests for the 401 Frontegg error we debugged:

```bash
# Test the specific 401 error scenario
pytest tests/test_auth.py::TestAuthenticationFailures::test_frontegg_401_error -v

# Test environment configuration
pytest tests/test_auth.py::TestEnvironmentConfiguration -v
```

### Quick Fix for Development
To disable authentication and eliminate the 401 error:

1. Edit `apps/backend/.env.local`
2. Comment out: `# FRONTEGG_CLIENT_ID=843bbe93-eb8d-49cf-b53b-90bd60265c82`
3. Restart the backend server

## 🧹 Cleanup Summary

**Removed redundant files:**
- `test_auth_integration.py` (507 lines) → Consolidated into `test_auth.py`
- `test_auth_comprehensive.py` (476 lines) → Consolidated into `test_auth.py`
- `test_ragie_auth_integration.py` (448 lines) → Consolidated into `test_auth.py`
- `test_auth_integration_manual.py` (372 lines) → Removed (manual testing)
- `run_auth_debug_tests.py` (311 lines) → Replaced with `run_tests.py`
- `run_auth_tests.py` (232 lines) → Replaced with `run_tests.py`
- `test_reproduce_401_error.py` (213 lines) → Consolidated into `test_auth.py`
- `test_auth_fixes.py` (212 lines) → Consolidated into `test_auth.py`
- `test_dotenv_debug.py` (204 lines) → Consolidated into `test_auth.py`
- `test_debug_auth.py` (38 lines) → Removed (debug only)
- `test_simple.py` (52 lines) → Removed (basic tests)

**Result:**
- **Before**: 3,338 lines across 13 files
- **After**: ~400 lines across 4 main files
- **Reduction**: ~90% fewer lines, much cleaner structure

## 🎯 Benefits

- ✅ **Single source of truth** for authentication tests
- ✅ **No redundancy** - each test has a clear purpose
- ✅ **Easy to run** - simple test runner
- ✅ **Easy to maintain** - consolidated codebase
- ✅ **Complete coverage** - all scenarios tested
- ✅ **Clear organization** - logical test grouping