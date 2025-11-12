# Test Suite Documentation

## Overview

This test suite provides comprehensive testing for the Lead Nurturing Workflow with AI Agent system. The tests cover API workflows, Document RAG retrieval, T2SQL functionality, Agent flow, Document ingestion, and Integration tests.

## Test Structure

### Test Files

1. **test_api.py** - API workflow tests
   - Lead filtering endpoints
   - Campaign creation endpoints
   - Message generation endpoints
   - RAG search endpoints
   - Response structure validation

2. **test_rag.py** - Document RAG tests
   - Document loading
   - Chunking and splitting
   - Embedding generation
   - ChromaDB storage
   - Query functionality
   - API integration

3. **test_t2sql.py** - Text-to-SQL tests
   - SQL generation from natural language
   - Query execution
   - Database schema retrieval
   - Error handling
   - SQL injection prevention

4. **test_agent.py** - Agent flow tests
   - Intent detection
   - Agent workflow execution
   - Reply processing
   - Lead status updates
   - Campaign integration

5. **test_document_ingestion.py** - Document upload/ingestion tests
   - Document upload API
   - File processing pipeline
   - Chunking with overlap
   - Embedding generation
   - ChromaDB storage
   - Metadata preservation

6. **test_integration.py** - Integration tests
   - End-to-end workflows
   - Campaign creation to message sending
   - RAG and T2SQL integration
   - Agent flow integration
   - Message logging
   - Campaign metrics

## Running Tests

### Prerequisites

```bash
pip install -r requirements.txt
```

### Run All Tests

```bash
# From agent_backend directory
python run_eval.py

# OR using pytest directly
pytest agent_app/tests/

# OR with verbose output
pytest -v agent_app/tests/
```

### Run Specific Test Files

```bash
# Run API tests only
pytest agent_app/tests/test_api.py

# Run RAG tests only
pytest agent_app/tests/test_rag.py

# Run T2SQL tests only
pytest agent_app/tests/test_t2sql.py

# Run Agent tests only
pytest agent_app/tests/test_agent.py

# Run Document ingestion tests only
pytest agent_app/tests/test_document_ingestion.py

# Run Integration tests only
pytest agent_app/tests/test_integration.py
```

### Run Specific Test Classes

```bash
# Run specific test class
pytest agent_app/tests/test_api.py::TestAPIWorkflow

# Run specific test method
pytest agent_app/tests/test_api.py::TestAPIWorkflow::test_filter_leads_by_project
```

### Run Tests with Coverage

```bash
# Install pytest-cov if not already installed
pip install pytest-cov

# Run tests with coverage
pytest --cov=agent_app --cov-report=html agent_app/tests/

# View coverage report
# Open htmlcov/index.html in browser
```

## Test Configuration

### pytest.ini

The `pytest.ini` file in the agent_backend directory configures:
- Django settings module
- Test discovery patterns
- Markers for test categorization
- Default options

### conftest.py

The `conftest.py` file provides:
- Django database setup
- Test fixtures (sample_lead, sample_leads, sample_campaign)
- API client fixture
- Temporary directory fixtures
- Database reset between tests

## Test Fixtures

### Available Fixtures

- `api_client` - Django test client for API testing
- `sample_lead` - Single sample lead for testing
- `sample_leads` - Multiple sample leads for testing
- `sample_campaign` - Sample campaign with leads
- `temp_pdf_directory` - Temporary directory for PDF files
- `authenticated_client` - Authenticated test client (for JWT tests)

## Test Coverage

### API Workflow Tests
- ✅ Hello endpoint
- ✅ RAG search endpoint
- ✅ Lead filtering (by project, unit type, budget, status, date)
- ✅ Campaign creation
- ✅ Message generation
- ✅ Reply fetching
- ✅ Response structure validation

### Document RAG Tests
- ✅ Document loading
- ✅ Chunking and splitting
- ✅ Embedding generation
- ✅ ChromaDB storage
- ✅ Query functionality
- ✅ API integration
- ✅ Special character handling

### T2SQL Tests
- ✅ SQL generation from natural language
- ✅ Query execution
- ✅ Database schema retrieval
- ✅ Error handling
- ✅ SQL injection prevention
- ✅ Case insensitivity
- ✅ Multiple query types

### Agent Flow Tests
- ✅ Intent detection (auto_reply, notify_agent)
- ✅ Agent workflow execution
- ✅ Reply processing
- ✅ Lead status updates
- ✅ Campaign integration
- ✅ Multiple replies handling

### Document Ingestion Tests
- ✅ Document upload API
- ✅ File processing pipeline
- ✅ Chunking with overlap
- ✅ Embedding generation
- ✅ ChromaDB storage
- ✅ Metadata preservation
- ✅ Large document handling

### Integration Tests
- ✅ Complete campaign workflow
- ✅ Lead filter to campaign creation
- ✅ Message generation workflow
- ✅ RAG search integration
- ✅ T2SQL integration
- ✅ Agent flow integration
- ✅ Message logging integration
- ✅ Campaign metrics integration

## Notes

### External Dependencies

Some tests may skip if external dependencies are not available:
- ChromaDB setup (for RAG tests)
- Embedding model download (for RAG tests)
- Gemini API (for agent flow tests)
- Email service (for message sending tests)

### Test Data

Tests use in-memory SQLite database by default. Test data is reset between tests using the `reset_db` fixture.

### Skipped Tests

Tests that require external services (like ChromaDB, Gemini API) will be skipped if those services are not available. This is expected behavior and tests will report as "skipped" rather than "failed".

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure Django is properly set up
   - Check that all dependencies are installed
   - Verify PYTHONPATH includes project directories

2. **Database Errors**
   - Ensure Django settings are correct
   - Check that test database is properly configured
   - Verify migrations are up to date

3. **ChromaDB Errors**
   - Ensure ChromaDB is installed
   - Check that chroma_db directory exists
   - Verify embeddings model is downloaded

4. **API Errors**
   - Ensure Django server is not running on test port
   - Check that test client is properly configured
   - Verify API endpoints are correctly defined

## Continuous Integration

These tests are designed to run in CI/CD pipelines. The `run_eval.py` script provides a single entry point for running all tests.

## Contributing

When adding new tests:
1. Follow the existing test structure
2. Use appropriate fixtures
3. Add docstrings to test methods
4. Mark tests that require external services
5. Update this README if adding new test categories

