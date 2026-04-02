# Code Standards & Conventions

## Python Version & Environment

- **Minimum Version:** Python 3.10
- **Build System:** Hatchling + hatch-vcs (automatic versioning from git tags)
- **Package Import:** `dnse_email_otp` (snake_case, not `dnse-emailotp`)

## Linting & Formatting

### Ruff Configuration

**File:** `pyproject.toml`

```toml
[tool.ruff]
line-length = 100
target-version = "py310"
exclude = ["src/dnse_email_otp/_version.py"]

[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP", "D", "S"]

[tool.ruff.lint.pydocstyle]
convention = "google"

[tool.ruff.lint.per-file-ignores]
"tests/**" = ["S101", "S105", "S106", "D", "E501", "F841"]
```

**Rules Applied:**
- `E` — PEP 8 errors
- `F` — Pyflakes (undefined names, unused imports)
- `I` — isort (import sorting)
- `B` — flake8-bugbear (common bugs)
- `UP` — pyupgrade (modern Python syntax)
- `D` — pydocstring (Google-style docstrings required)
- `S` — bandit (security linting)

**Test Exceptions:**
- `S101` — Assertions allowed in tests
- `S105`, `S106` — Hardcoded secrets OK in test fixtures
- `D` — Docstrings optional in test files
- `E501` — Line length relaxed in tests
- `F841` — Unused variables allowed in tests

### Running Ruff

```bash
# Check
ruff check src/ tests/

# Fix auto-fixable issues
ruff check --fix src/ tests/

# Format
ruff format src/ tests/
```

## Type Checking

### Pyright Configuration

**File:** `pyproject.toml`

```toml
[tool.pyright]
typeCheckingMode = "strict"
pythonVersion = "3.10"
reportMissingTypeStubs = "none"

[[tool.pyright.executionEnvironments]]
root = "tests"
reportPrivateUsage = "none"
reportUnusedVariable = "none"
reportUnknownVariableType = "none"
reportUnknownMemberType = "none"
reportUnknownArgumentType = "none"
```

**Rules:**
- Strict type checking enabled for all source code
- No partial types or inferred `Any`
- Test environment relaxed: allows dynamic behavior, unused variables, unknown types
- Missing third-party `.pyi` stubs permitted (imapclient)

### Running Pyright

```bash
# Check all code
pyright

# In CI/pre-commit
pyright --outputjson
```

## Naming Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Modules | snake_case | `listener.py`, `models.py` |
| Classes | PascalCase | `EmailMessage`, `ImapListener` |
| Functions | snake_case | `wait_for_new_message()`, `fetch_unseen()` |
| Constants | UPPER_SNAKE_CASE | `_DEFAULT_HOST`, `_IDLE_TIMEOUT_SECS` |
| Private Functions | `_leading_underscore` | `_ensure_connected()`, `_parse_email()` |
| Private Constants | `_leading_underscore` | `_DEFAULT_PORT`, `_MAX_RECONNECT_RETRIES` |
| Type Variables | PascalCase | `T`, `P` (minimal use) |
| Dataclass Fields | snake_case | `uid`, `subject`, `sender` |

## Docstring Style

**Google Format** (per ruff pydocstyle)

### Module Docstring
```python
"""IMAP IDLE listener for real-time email arrival detection."""
```

### Class Docstring
```python
class ImapListener:
    """IMAP IDLE listener for detecting new emails in real time.
    
    Connects to an IMAP server (Gmail by default) and uses IDLE
    to wait for new message notifications without polling.
    
    Args:
        email_address: Email address for IMAP login.
        password: App password (not account password when 2FA enabled).
    """
```

### Function Docstring
```python
def wait_for_new_message(self, timeout: float = 60.0) -> EmailMessage | None:
    """Wait for a new email via IMAP IDLE.
    
    Args:
        timeout: Max seconds to wait for a new message.
    
    Returns:
        First unseen EmailMessage, or None if timeout elapsed.
    """
```

### Exception Documentation
```python
def wait_for_otp(...) -> str:
    """Wait for OTP email and extract code.
    
    Raises:
        TimeoutError: No OTP email within timeout.
        NotImplementedError: Stub -- not yet implemented.
    """
```

## Import Organization

Order by: standard library → third-party → local

```python
from __future__ import annotations

import email as email_stdlib
import logging
import ssl
from collections.abc import Callable
from datetime import datetime, timezone
from email.message import EmailMessage as StdlibEmailMessage
from email.utils import parsedate_to_datetime
from typing import Any

from imapclient import IMAPClient

from dnse_email_otp.models import EmailMessage
```

## Type Annotations

**All public APIs must have full type hints:**

```python
def connect(self) -> None:
    """Connect and authenticate to the IMAP server."""

def wait_for_new_message(self, timeout: float = 60.0) -> EmailMessage | None:
    """Wait for a new email via IMAP IDLE."""

def fetch_unseen(self) -> list[EmailMessage]:
    """Fetch all unseen messages from the selected folder."""
```

**Use modern union syntax:**
- Preferred: `str | None`
- Avoid: `Optional[str]`, `Union[str, None]`

**Handle imapclient unknowns:**
- Suppress with `# type: ignore[reportUnknownMemberType]`
- Document in comment why (third-party untyped library)

## Immutability & Frozen Dataclasses

Use `@dataclass(frozen=True)` for data models:

```python
@dataclass(frozen=True)
class EmailMessage:
    """Parsed email message from IMAP fetch."""
    uid: int
    subject: str
    # ... cannot be modified after instantiation
```

## Error Handling

- Use specific exception types: `ConnectionError`, `TimeoutError`, `NotImplementedError`
- Catch broad exceptions only in infrastructure code:
  ```python
  except (OSError, IMAPClient.Error) as exc:
      logger.warning("Connection error: %s", exc)
  ```
- Log at appropriate level:
  - `logger.info()` — State changes (connect, disconnect)
  - `logger.warning()` — Recoverable errors, retries
  - `logger.debug()` — Detailed flow (logout failures, edge cases)

## Testing Standards

**Framework:** pytest ≥8

**Coverage Target:** High coverage for critical paths (listener, parser when implemented)

**Naming:** `test_*.py` or `*_test.py`

```bash
# Run tests with coverage
pytest --cov=src/dnse_email_otp tests/

# Run specific test
pytest tests/test_listener.py::test_wait_for_new_message
```

## File Structure

```
src/dnse_email_otp/
├── __init__.py          # Public API exports
├── models.py            # Data structures (EmailMessage)
├── listener.py          # ImapListener implementation
├── parser.py            # OTP extraction (stub)
├── helper.py            # Convenience API (stub)
└── _version.py          # Auto-generated by hatch-vcs

tests/
├── test_listener.py     # ImapListener tests
├── test_models.py       # EmailMessage tests
├── test_parser.py       # extract_otp tests
└── test_helper.py       # wait_for_otp tests
```

## Line Length & Readability

- **Ruff Line Limit:** 100 characters
- **Exception:** Test assertions can exceed (excluded via `E501` in test config)
- Break long parameter lists:
  ```python
  def __init__(
      self,
      email_address: str,
      password: str,
      *,
      host: str = _DEFAULT_HOST,
      port: int = _DEFAULT_PORT,
  ) -> None:
  ```

## Logging

Use module-level logger:

```python
logger = logging.getLogger(__name__)

# Use structured logs
logger.info("Connected to %s:%d folder=%s", host, port, folder)
logger.warning("Connection error: %s", error)
logger.debug("Logout failed (connection may already be closed)")
```

## Pre-Commit Checklist

Before committing:
1. Run `ruff check --fix src/ tests/`
2. Run `ruff format src/ tests/`
3. Run `pyright`
4. Run `pytest`
5. Verify no secrets in `.env`, credentials, or API keys
