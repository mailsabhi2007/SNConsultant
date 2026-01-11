# Test Suite Documentation

This directory contains the comprehensive test suite for the ServiceNow Consulting Agent.

## Test Structure

- `unit/` - Unit tests for individual components
- `integration/` - Integration tests for component interactions
- `e2e/` - End-to-end workflow tests
- `fixtures/` - Test data and mocks
- `conftest.py` - Pytest configuration and shared fixtures

## Running Tests

### Run all tests
```bash
pytest
```

### Run with coverage
```bash
pytest --cov
```

### Run specific test file
```bash
pytest tests/unit/test_agent.py
```

### Run specific test
```bash
pytest tests/unit/test_agent.py::test_should_continue_blocks_live_instance
```

### Run with verbose output
```bash
pytest -v
```

### Run only unit tests
```bash
pytest tests/unit/
```

### Run only integration tests
```bash
pytest tests/integration/
```

### Run only e2e tests
```bash
pytest tests/e2e/
```

## Test Coverage Goals

- **Unit tests:** 80%+ coverage
- **Integration tests:** Critical paths covered
- **E2E tests:** Main user workflows covered

## Mocking Strategies

### LLM Mocking
- Use `unittest.mock` to mock `ChatAnthropic.invoke`
- Return predictable tool calls for testing workflow
- Return predictable responses for testing synthesis

### API Mocking
- Use `responses` library for HTTP mocking
- Mock Tavily API responses
- Mock ServiceNow API responses
- Test various error scenarios (404, 500, timeout)

### Vector Store Mocking
- Use in-memory ChromaDB for tests
- Create test database in temporary directory
- Clean up after each test

## Test Data

Sample test data is available in `fixtures/`:
- `sample_rules.txt` - Sample internal policy document
- `sample_servicenow_response.json` - Sample ServiceNow API response
- `sample_tavily_response.json` - Sample Tavily API response
- `sample_kb_results.json` - Sample knowledge base query results

## Environment Variables

Tests require the following environment variables (set in `conftest.py` fixtures):
- `ANTHROPIC_API_KEY` - For LLM API
- `OPENAI_API_KEY` - For embeddings
- `TAVILY_API_KEY` - For public docs search
- `SN_INSTANCE` - ServiceNow instance URL
- `SN_USER` - ServiceNow username
- `SN_PASSWORD` - ServiceNow password

## CI/CD Integration

Tests run automatically on:
- Push to main/develop branches
- Pull requests to main/develop branches

Coverage reports are generated and uploaded to Codecov.
