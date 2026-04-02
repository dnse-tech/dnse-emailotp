# System Architecture

## Data Flow

```
User Code
   ↓
ImapListener (context manager) ← IMAP connection
   ├─ connect() → IMAPClient
   ├─ wait_for_new_message(timeout)
   │  ├─ _idle_once() → IMAP IDLE
   │  ├─ fetch_unseen() → [EmailMessage]
   │  └─ _with_reconnect() → auto-retry on error
   └─ disconnect() → cleanup
   ↓
EmailMessage (frozen dataclass)
   {uid, subject, sender, date, body_text, body_html}
   ↓
extract_otp(body_text) → OTP string [STUB]
   ↓
wait_for_otp(...) → OTP string [STUB]
```

## Module Structure

### `models.py` — Data Structures
- **EmailMessage:** Immutable dataclass representing a parsed email
  - `uid: int` — IMAP message UID
  - `subject, sender: str` — Email headers
  - `date: datetime` — Parsed timestamp
  - `body_text, body_html: str` — Email bodies

### `listener.py` — IMAP Client & IDLE
- **ImapListener:** Connects to IMAP server, monitors inbox via IDLE
  - **Public API:**
    - `connect()` — Establish SSL connection, login, select folder
    - `disconnect()` — Logout and cleanup
    - `wait_for_new_message(timeout)` — IDLE with timeout, return first unseen email
    - `fetch_unseen()` — Get list of all unseen messages
    - Context manager support (`__enter__`, `__exit__`)
  - **Internal Helpers:**
    - `_ensure_connected()` — Lazy connection check
    - `_idle_once()` — Single IDLE cycle
    - `_with_reconnect()` — Exponential backoff retry wrapper
  - **Internal Utilities:**
    - `_parse_email()` — Convert RFC822 bytes to EmailMessage
    - `_has_exists()` — Detect EXISTS in IDLE responses
    - `_parse_date()` — Handle email date header
    - `_get_payload_str()` — Extract text/HTML from MIME parts

### `parser.py` — OTP Extraction [STUB]
- **extract_otp(email_body: str) → str | None:** Placeholder for OTP extraction logic
  - Currently raises `NotImplementedError`

### `helper.py` — High-Level API [STUB]
- **wait_for_otp(...) → str:** Placeholder combining listener + parser
  - Currently raises `NotImplementedError`

### `__init__.py` — Public API
Exports:
- `EmailMessage`
- `ImapListener`
- `extract_otp`
- `wait_for_otp`
- `__version__`

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Frozen dataclass for EmailMessage | Immutability + type safety + memory efficiency |
| IMAP IDLE instead of polling | No polling overhead, near real-time, RFC 2177 standard |
| Auto-reconnect with backoff | Handles transient network failures transparently |
| Context manager pattern | Explicit resource cleanup, Pythonic |
| imapclient library | Mature IMAP impl, supports IDLE, handles RFC822 parsing |
| Gmail defaults | Simplifies setup for primary use case |

## Constants

| Name | Value | Purpose |
|------|-------|---------|
| `_DEFAULT_HOST` | `imap.gmail.com` | Gmail IMAP endpoint |
| `_DEFAULT_PORT` | `993` | IMAP over SSL |
| `_IDLE_TIMEOUT_SECS` | `28 * 60` | Re-issue IDLE before 29-min RFC limit |
| `_MAX_FETCH_UNSEEN` | `50` | Cap unseen fetch to prevent OOM |
| `_MAX_RECONNECT_RETRIES` | `3` | Max retry attempts on error |
| `_BACKOFF_BASE_SECS` | `1.0` | Initial backoff delay |
| `_BACKOFF_MAX_SECS` | `30.0` | Max backoff delay |

## Resilience & Error Handling

- **Connection Errors:** `ImapListener._with_reconnect()` catches `OSError` and `IMAPClient.Error`, retries with exponential backoff, raises `ConnectionError` if all retries exhausted
- **Parsing Failures:** Invalid date headers fall back to UTC now; missing RFC822 data logged as warning
- **MIME Extraction:** Handles multipart messages, respects first text/plain and first text/html found
- **Payload Decoding:** UTF-8 with error replacement handles malformed text

## IMAP Compliance

- RFC 2177 IDLE: 28-min timeout < 29-min requirement
- RFC 822 Message Format: Full parsing via stdlib + imapclient
- SSL/TLS: Default context for secure connections
