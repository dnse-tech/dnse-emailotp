# Codebase Summary

## Project Overview

**dnse-emailotp** is a Python library for retrieving one-time passwords (OTPs) from Gmail via IMAP IDLE. It provides real-time email monitoring, parsing, and OTP extraction with automatic reconnection and error recovery.

**Package:** `dnse_email_otp` | **Min Python:** 3.10 | **Deps:** imapclient ≥2.3

---

## File-by-File Breakdown

### `__init__.py`
**Purpose:** Public API exports and version information

**Exports:**
- `EmailMessage` — Frozen dataclass for parsed emails
- `ImapListener` — Main IMAP listener class
- `extract_otp()` — OTP extraction from email body
- `wait_for_otp()` — High-level convenience API combining listener + parser
- `__version__` — Package version (from hatch-vcs)

**Implementation Notes:**
- Graceful fallback: `__version__ = "0.0.0"` if git versioning unavailable
- Imports handled via try-except to support non-VCS installations

---

### `models.py`
**Purpose:** Data structures for representing parsed emails

**Classes:**
- `EmailMessage` (frozen dataclass)
  - `uid: int` — IMAP message UID for server identification
  - `subject: str` — Email subject line
  - `sender: str` — Sender address from From header
  - `date: datetime` — Parsed timestamp (UTC with timezone)
  - `body_text: str` — Plain text body (empty string if none)
  - `body_html: str` — HTML body (empty string if none)

**Design Decisions:**
- Frozen: Immutable after creation, hashable, thread-safe
- datetime with timezone: Respects email date locality
- String bodies: Empty string default simplifies handling vs. None

**Dependencies:** None (standard library only)

---

### `listener.py`
**Purpose:** IMAP connection management and IDLE listener implementation

**Main Class: ImapListener**

**Constructor Parameters:**
- `email_address: str` — Gmail address for login
- `password: str` — Gmail app password (not account password if 2FA enabled)
- `host: str = "imap.gmail.com"` — IMAP server hostname
- `port: int = 993` — IMAP over SSL port
- `folder: str = "INBOX"` — Mailbox folder to monitor
- `idle_timeout: int = 28*60` — Seconds before re-issuing IDLE (< 29 min per RFC 2177)

**Public Methods:**

| Method | Purpose |
|--------|---------|
| `connect()` | Establish SSL connection, authenticate, select folder |
| `disconnect()` | Logout and cleanup (idempotent, catches errors) |
| `wait_for_new_message(timeout=60.0)` | Wait for new email via IDLE with auto-reconnect |
| `fetch_unseen()` | Fetch all unseen messages as list of EmailMessage |
| `__enter__` / `__exit__` | Context manager support |

**Context Manager:**
```python
with ImapListener("user@gmail.com", "apppass") as listener:
    msg = listener.wait_for_new_message(timeout=60)
```

**Internal Methods:**
- `_ensure_connected()` — Lazy connection, auto-connect if None
- `_idle_once(timeout)` — Single IDLE cycle with EXISTS check
- `_with_reconnect(fn)` — Execute function with exponential backoff retry on errors

**Resilience Features:**
- **Auto-Reconnect:** Up to 3 retries (configurable `_MAX_RECONNECT_RETRIES`)
- **Exponential Backoff:** 1s → 2s → 4s ... → 30s max
- **Graceful Disconnect:** Catches logout errors, finalizes cleanup
- **Lazy Connection:** Connects on first use, not in `__init__`

**Helper Functions:**
- `_parse_email(uid, raw_bytes)` — Convert RFC822 bytes to EmailMessage
  - Extracts subject, sender, date from headers
  - Walks MIME tree to find first text/plain and text/html parts
  - Handles multipart and non-multipart messages
  - Decodes UTF-8 with error replacement

- `_has_exists(responses)` — Detect EXISTS in IDLE responses
  - Checks tuple responses for b"EXISTS" flag
  - Returns True if new message notification found

- `_parse_date(date_str)` — Parse email Date header safely
  - Uses `email.utils.parsedate_to_datetime()`
  - Falls back to UTC now on parse error

- `_get_payload_str(part)` — Extract text/HTML from MIME part
  - Handles str payloads directly
  - Decodes bytes with UTF-8 (error replacement for malformed)
  - Returns empty string for binary/unsupported types

**IMAP Constants:**
- `_DEFAULT_HOST = "imap.gmail.com"`
- `_DEFAULT_PORT = 993` (SSL)
- `_DEFAULT_FOLDER = "INBOX"`
- `_IDLE_TIMEOUT_SECS = 28 * 60` (28 min, < 29 min RFC requirement)
- `_MAX_FETCH_UNSEEN = 50` (prevents OOM on neglected mailboxes)
- `_MAX_RECONNECT_RETRIES = 3`
- `_BACKOFF_BASE_SECS = 1.0`
- `_BACKOFF_MAX_SECS = 30.0`

**Dependencies:** imapclient, email (stdlib), ssl (stdlib), logging (stdlib)

---

### `parser.py`
**Purpose:** OTP extraction from email body text

**Function: extract_otp**

**Signature:**
```python
def extract_otp(email_body: str) -> str | None:
```

**Parameters:**
- `email_body: str` — Plain text or HTML email body

**Returns:**
- OTP string if found, None otherwise

**Implementation Details:**
- Extracts 6-digit OTP codes from DNSE emails
- **Pattern 1 (Vietnamese plain-text):** Matches "Mã OTP ... là:\n\n{6 digits}"
- **Pattern 2 (HTML fallback):** Matches `<span style="letter-spacing: 25px;">{6 digits}</span>`
- Returns first match found, None if no pattern matches
- Logs extraction method for debugging

**Dependencies:** re (stdlib)

---

### `helper.py`
**Purpose:** High-level convenience API combining listener and parser

**Function: wait_for_otp**

**Signature:**
```python
def wait_for_otp(
    email_address: str,
    app_password: str,
    *,
    host: str = "imap.gmail.com",
    port: int = 993,
    folder: str = "INBOX",
    timeout: float = 60.0,
) -> str:
```

**Parameters:**
- `email_address: str` — Gmail address
- `app_password: str` — Gmail app password
- `host: str` — IMAP hostname (default: Gmail)
- `port: int` — IMAP port (default: 993)
- `folder: str` — Mailbox folder (default: INBOX)
- `timeout: float` — Max seconds to wait for email (default: 60s)

**Returns:**
- OTP code string

**Raises:**
- `TimeoutError` — No email within timeout or OTP not found in email

**Implementation Flow:**
1. Creates ImapListener context with provided credentials
2. Calls `wait_for_new_message(timeout)` to retrieve email
3. If no message: logs warning, raises TimeoutError
4. Tries extracting OTP from `body_text`, then `body_html`
5. If OTP found: logs success, returns code
6. If OTP not found: logs warning, raises TimeoutError
7. Context manager ensures cleanup on success or error

**Dependencies:** listener.py, parser.py

---

### `_version.py`
**Purpose:** Auto-generated version file (created by hatch-vcs)

**Note:** Excluded from ruff linting; generated at build time from git tags

---

## Key Architecture Patterns

| Pattern | Implementation | Benefit |
|---------|----------------|---------|
| **Data Class** | Frozen EmailMessage | Immutable, hashable, thread-safe |
| **Context Manager** | `__enter__`, `__exit__` | Guaranteed cleanup |
| **Lazy Connection** | _ensure_connected() | Delayed auth, reduced memory at init |
| **Resilience Wrapper** | _with_reconnect() | Transparent error recovery |
| **MIME Walking** | msg.walk() iteration | Handles complex multipart emails |
| **Exponential Backoff** | Double on each retry | Respects server load, avoids hammering |

## Dependencies & Versions

| Dependency | Version | Purpose |
|-----------|---------|---------|
| imapclient | ≥2.3 | IMAP protocol, IDLE support |
| Python | ≥3.10 | Runtime |
| pytest | ≥8 (dev) | Testing |
| ruff | ≥0.8 (dev) | Linting/formatting |
| pyright | ≥1.1 (dev) | Type checking |
| hatchling | build req | Build system |
| hatch-vcs | build req | Git-based versioning |

## Test Coverage Strategy

**Framework:** pytest with coverage

**Modules to Test:**
- `listener.py` — Core IMAP logic (mocked server)
- `models.py` — Dataclass construction
- `parser.py` — OTP extraction (once implemented)
- `helper.py` — Integration flow (once implemented)

**Not Tested (external):**
- `__init__.py` — Public API re-exports
- `_version.py` — Auto-generated, build-system only

## Size Metrics

| File | Lines | Role |
|------|-------|------|
| listener.py | ~245 | IMAP listener core |
| models.py | ~28 | Data model |
| helper.py | ~35 | High-level API stub |
| parser.py | ~18 | OTP extraction stub |
| __init__.py | ~20 | Public API |

**Total:** ~350 LOC (main) + tests

## Next Phase: Implementation Roadmap

**Phase 1 (Complete):** Core listener architecture
- [x] EmailMessage dataclass
- [x] ImapListener with IDLE
- [x] Auto-reconnect with backoff
- [x] Email parsing (RFC822)
- [x] Context manager pattern

**Phase 2 (Complete):** OTP extraction and convenience API
- [x] extract_otp() — Pattern matching for 6-digit DNSE codes (Vietnamese + HTML formats)
- [x] wait_for_otp() — Combined listener + parser with timeout handling

**Phase 3 (Future):** Enhancements
- [ ] Multiple IMAP providers (not just Gmail)
- [ ] Gmail OAuth support
- [ ] Persistent message history
- [ ] Rate limiting

---

## Running the Code

**Installation:**
```bash
pip install dnse-emailotp
```

**Basic Usage:**
```python
from dnse_email_otp import ImapListener

with ImapListener("you@gmail.com", "app-password") as listener:
    msg = listener.wait_for_new_message(timeout=60)
    if msg:
        print(f"From: {msg.sender}")
        print(f"Subject: {msg.subject}")
        print(f"Body: {msg.body_text[:100]}")
```

**Development:**
```bash
# Lint & format
ruff check --fix src/ tests/
ruff format src/ tests/

# Type check
pyright

# Test
pytest --cov=src/dnse_email_otp tests/
```
