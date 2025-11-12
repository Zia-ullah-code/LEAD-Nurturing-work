# Testing Guide

## Quick Start

### 1. Install Dependencies

```bash
cd agent_backend
pip install -r requirements.txt
```

### 2. Run All Tests

```bash
# Option 1: Using the evaluation script
python run_eval.py

# Option 2: Using pytest directly
pytest agent_app/tests/

# Option 3: With verbose output
pytest -v agent_app/tests/
```

### 3. Run Specific Test Categories

```bash
# API tests
pytest agent_app/tests/test_api.py -v

# RAG tests
pytest agent_app/tests/test_rag.py -v

# T2SQL tests
pytest agent_app/tests/test_t2sql.py -v

# Agent flow tests
pytest agent_app/tests/test_agent.py -v

# Document ingestion tests
pytest agent_app/tests/test_document_ingestion.py -v

# Integration tests
pytest agent_app/tests/test_integration.py -v
```

## Test Structure

```
agent_backend/
├── conftest.py                          # Pytest configuration and fixtures
├── pytest.ini                           # Pytest settings
├── run_eval.py                          # Evaluation script
├── agent_app/
│   └── tests/
│       ├── __init__.py
│       ├── README.md                    # Detailed test documentation
│       ├── test_api.py                  # API workflow tests
│       ├── test_rag.py                  # Document RAG tests
│       ├── test_t2sql.py                # T2SQL tests
│       ├── test_agent.py                # Agent flow tests
│       ├── test_document_ingestion.py   # Document upload/ingestion tests
│       └── test_integration.py          # Integration tests
```

## Test Coverage

### API Workflow Tests (test_api.py)
- ✅ Hello endpoint
- ✅ RAG search endpoint
- ✅ Lead filtering (project, unit type, budget, status, date)
- ✅ Campaign creation (Email, WhatsApp)
- ✅ Message generation
- ✅ Reply fetching
- ✅ Response structure validation

### Document RAG Tests (test_rag.py)
- ✅ Document loading
- ✅ Chunking and splitting
- ✅ Embedding generation
- ✅ ChromaDB storage
- ✅ Query functionality
- ✅ API integration

### T2SQL Tests (test_t2sql.py)
- ✅ SQL generation from natural language
- ✅ Query execution
- ✅ Database schema retrieval
- ✅ Error handling
- ✅ SQL injection prevention

### Agent Flow Tests (test_agent.py)
- ✅ Intent detection
- ✅ Agent workflow execution
- ✅ Reply processing
- ✅ Lead status updates

### Document Ingestion Tests (test_document_ingestion.py)
- ✅ Document upload API
- ✅ File processing pipeline
- ✅ Chunking with overlap
- ✅ Embedding generation
- ✅ ChromaDB storage

### Integration Tests (test_integration.py)
- ✅ End-to-end workflows
- ✅ Campaign creation to message sending
- ✅ RAG and T2SQL integration
- ✅ Agent flow integration
- ✅ Message logging
- ✅ Campaign metrics

## Test Fixtures

Available fixtures in `conftest.py`:

- `api_client` - Django test client
- `sample_lead` - Single sample lead
- `sample_leads` - Multiple sample leads
- `sample_campaign` - Sample campaign with leads
- `temp_pdf_directory` - Temporary directory for PDFs
- `authenticated_client` - Authenticated test client

## Running Tests with Coverage

```bash
# Install pytest-cov
pip install pytest-cov

# Run tests with coverage
pytest --cov=agent_app --cov-report=html agent_app/tests/

# View coverage report
# Open htmlcov/index.html in browser
```

## Test Execution Options

### Verbose Output
```bash
pytest -v agent_app/tests/
```

### Show Print Statements
```bash
pytest -s agent_app/tests/
```

### Run Specific Test
```bash
pytest agent_app/tests/test_api.py::TestAPIWorkflow::test_filter_leads_by_project
```

### Run Tests Matching Pattern
```bash
pytest -k "test_filter" agent_app/tests/
```

### Stop on First Failure
```bash
pytest -x agent_app/tests/
```

### Show Slowest Tests
```bash
pytest --durations=10 agent_app/tests/
```

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure Django is set up: `python manage.py check`
   - Verify all dependencies are installed: `pip install -r requirements.txt`

2. **Database Errors**
   - Tests use in-memory SQLite by default
   - Ensure Django settings are correct
   - Run migrations if needed: `python manage.py migrate`

3. **ChromaDB Errors**
   - Some RAG tests may skip if ChromaDB is not set up
   - This is expected behavior - tests will report as "skipped"

4. **API Errors**
   - Ensure test client is properly configured
   - Check that API endpoints are correctly defined
   - Verify Django server is not running on test port

### Skipped Tests

Tests that require external services (ChromaDB, Gemini API, etc.) will be skipped if those services are not available. This is expected behavior.

## CI/CD Integration

The test suite is designed to run in CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: |
    cd agent_backend
    pip install -r requirements.txt
    pytest agent_app/tests/ -v
```

## Next Steps

1. Run the test suite to verify all tests pass
2. Add DeepEval evaluation (as mentioned in documentation)
3. Generate coverage reports to identify gaps
4. Integrate with CI/CD pipeline
5. Add performance tests if needed

## Documentation

For more detailed information, see:
- `agent_app/tests/README.md` - Detailed test documentation
- `TEST_SUITE_SUMMARY.md` - Test suite summary
- `pytest.ini` - Pytest configuration

## Support

For issues or questions:
1. Check the test documentation in `agent_app/tests/README.md`
2. Review test output for specific error messages
3. Verify all dependencies are installed
4. Check Django settings configuration

