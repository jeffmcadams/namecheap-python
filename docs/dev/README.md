# Development Guide

## 🛠️ Development Setup

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager
- Git

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/adriangalilea/namecheap-python.git
cd namecheap-python

# Install with uv (includes all extras and dev dependencies)
uv sync --all-extras

# Install pre-commit hooks
pre-commit install
```

## 🧪 Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=namecheap --cov-report=term-missing

# Run specific test file
uv run pytest tests/test_domains.py

# Run with verbose output
uv run pytest -vv
```

## 🔍 Code Quality

### Linting and Formatting

```bash
# Check code with ruff
uv run ruff check

# Fix auto-fixable issues
uv run ruff check --fix

# Format code
uv run ruff format

# Check formatting without changing files
uv run ruff format --check
```

### Type Checking

```bash
# Type check the main package
uv run mypy src/namecheap

# Type check everything (slower)
uv run mypy src/
```

### Pre-commit Hooks

The project uses pre-commit hooks to ensure code quality:

```bash
# Run all pre-commit hooks manually
pre-commit run --all-files

# Update pre-commit hooks
pre-commit autoupdate
```

## 📦 Building and Publishing

### Building Locally

```bash
# Build distribution packages
uv build

# This creates:
# - dist/namecheap-1.0.0-py3-none-any.whl
# - dist/namecheap-1.0.0.tar.gz
```

### Release Process

Releases are automated via GitHub Actions:

1. **Manual Release** (via GitHub UI):
   - Go to Actions → "Bump Version and Release"
   - Click "Run workflow"
   - Select version bump type (major/minor/patch)
   - This will:
     - Bump version in pyproject.toml
     - Create git tag
     - Build and publish to PyPI
     - Create GitHub release

2. **Tag-based Release**:
   ```bash
   # Create and push a tag
   git tag v1.0.0
   git push origin v1.0.0
   ```
   This triggers the publish workflow automatically.

## 🏗️ Project Structure

```
namecheap-python/
├── src/
│   ├── namecheap/          # Core SDK package
│   │   ├── __init__.py
│   │   ├── client.py       # Main client class
│   │   ├── models.py       # Pydantic models
│   │   ├── errors.py       # Custom exceptions
│   │   └── _api/           # API implementations
│   │       ├── base.py
│   │       ├── domains.py
│   │       └── dns.py
│   ├── namecheap_cli/      # CLI tool
│   │   ├── __init__.py
│   │   ├── __main__.py     # CLI entry point
│   │   └── completion.py   # Shell completions
│   └── namecheap_dns_tui/  # TUI application
│       ├── __init__.py
│       └── __main__.py     # TUI entry point
├── tests/                  # Test suite
├── examples/               # Usage examples
└── docs/                   # Documentation
```

## 🧩 Adding New Features

### Adding a New API Endpoint

1. Create model in `src/namecheap/models.py`:
   ```python
   class NewFeature(BaseModel):
       field: str
       another_field: int
   ```

2. Add API method in appropriate file under `src/namecheap/_api/`:
   ```python
   def new_feature(self, param: str) -> NewFeature:
       """Implement new feature."""
       response = self._request("namecheap.newfeature.action", {"Param": param})
       return NewFeature(**response)
   ```

3. Add tests in `tests/test_newfeature.py`

4. Update documentation

### Adding CLI Commands

1. Add command group or command in `src/namecheap_cli/__main__.py`:
   ```python
   @cli.group("newfeature")
   def newfeature_group():
       """New feature commands."""
       pass
   
   @newfeature_group.command("action")
   @click.argument("param")
   @pass_config
   def newfeature_action(config: Config, param: str):
       """Perform new feature action."""
       nc = config.init_client()
       result = nc.newfeature.action(param)
       # Handle output
   ```

2. Add tests and update CLI documentation

## 🐛 Debugging

### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Or set environment variable
export NAMECHEAP_DEBUG=true
```

### Common Issues

1. **Import errors**: Make sure you're using `uv run` or have activated the virtual environment
2. **API errors**: Check credentials and sandbox mode settings
3. **Type errors**: Run `mypy` to catch type issues early

## 📋 Checklist for PRs

- [ ] Code follows project style (run `uv run ruff check`)
- [ ] All tests pass (`uv run pytest`)
- [ ] Type hints added (`uv run mypy src/namecheap`)
- [ ] Documentation updated if needed
- [ ] Examples work correctly
- [ ] Commit messages are clear and descriptive

## 🔗 Useful Links

- [Namecheap API Documentation](https://www.namecheap.com/support/api/methods/)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Click Documentation](https://click.palletsprojects.com/)
- [Textual Documentation](https://textual.textualize.io/)
- [Ruff Documentation](https://docs.astral.sh/ruff/)