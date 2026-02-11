# Testing

## Framework

- **pytest** for test execution
- **pytest-asyncio** for async tests (auto mode)
- Tests live in `tests/` directory

## Running Tests

```bash
# All tests
pytest

# Single file
pytest tests/test_tool_validation.py

# Single test
pytest tests/test_tool_validation.py::test_specific_name

# Verbose output
pytest -v

# With coverage
pytest --cov=nanobot
```

## Test Patterns

- Mock external services (LLM providers, chat platforms) to avoid API calls
- Tool validation tests in `tests/test_tool_validation.py`
- Channel integration tests in `tests/test_email_channel.py`
- Docker test script: `tests/test_docker.sh`

## Configuration

From `pyproject.toml`:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

Async tests don't need the `@pytest.mark.asyncio` decorator — `asyncio_mode = "auto"` handles it.
