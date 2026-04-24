# DocTalk Tests

This directory contains the test suite for DocTalk.

## Test Structure

- `test_webapp.py` - Webapp integration tests (static file serving, CORS, routing)
- `conftest.py` - Shared pytest fixtures and configuration

## Running Tests

### Run all tests
```bash
python -m pytest
```

### Run specific test file
```bash
python -m pytest test/test_webapp.py
```

### Run tests with verbose output
```bash
python -m pytest -v
```

### Run only unit tests (no external dependencies)
```bash
python -m pytest -m unit
```

### Run only integration tests
```bash
python -m pytest -m integration
```

## Test Categories

- **Unit tests** - Fast tests with no external dependencies (mocked)
- **Integration tests** - Tests that may require Azure resources or real files

## Writing New Tests

1. Create test files with `test_*.py` naming pattern
2. Use fixtures from `conftest.py`
3. Mark tests appropriately:
   - `@pytest.mark.unit` for unit tests
   - `@pytest.mark.integration` for integration tests
   - `@pytest.mark.slow` for slow-running tests
4. Use descriptive test names: `test_<what>_<expected_behavior>`

## Test Coverage

Current test files:
- `test_webapp.py` - 12 tests covering static file serving, CORS, and API/static file coexistence
