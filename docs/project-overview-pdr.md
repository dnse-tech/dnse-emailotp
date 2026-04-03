# Project Overview & Product Requirements

## Product Definition

**dnse-emailotp** is a Python library for retrieving one-time passwords (OTPs) from Gmail via IMAP IDLE. It monitors an inbox in real-time, detects new emails without polling, and extracts OTP codes from email bodies.

**Use Case:** Automated account registration, login flows, or integrations requiring OTP verification from Gmail accounts.

## Key Features

- **Real-time IDLE Monitoring:** Uses IMAP IDLE (RFC 2177) to detect new messages without polling overhead
- **Auto-Reconnect:** Recovers from connection failures with exponential backoff (up to 3 retries)
- **Email Parsing:** Extracts subject, sender, date, plain text, and HTML body from RFC822 messages
- **OTP Extraction:** Identifies 6-digit OTP codes from DNSE emails (Vietnamese plain-text and HTML formats)
- **Convenience API:** High-level `wait_for_otp()` function combining listener and parser
- **Context Manager:** Safe resource cleanup via `with` statements
- **Structured Data:** Frozen dataclass (`EmailMessage`) for type-safe message handling
- **Gmail Optimized:** Pre-configured for Gmail IMAP (imap.gmail.com:993)

## Target Users

- Backend engineers building OTP-gated flows
- Test automation frameworks
- Integration services handling 2FA verification
- DNSE platform integrations

## Requirements

### Functional

1. **Message Retrieval:** Connect to Gmail via IMAP and wait for new emails using IDLE
2. **Email Parsing:** Extract metadata (subject, sender, date) and body (text/HTML) from RFC822 format
3. **OTP Extraction:** Extract 6-digit OTP codes from DNSE emails (Vietnamese plain-text: "Mã OTP ... là:\n\n{code}" and HTML: letter-spacing span format)
4. **Convenience API:** `wait_for_otp()` function combining listener + parser with timeout and error handling
5. **Error Handling:** Graceful reconnection on network failures, TimeoutError when email or OTP not found

### Non-Functional

- Python ≥3.10 compatibility
- Type-safe: strict Pyright mode enabled
- Dependency-light: only `imapclient>=2.3`
- RFC 2177 compliant (IDLE timeout < 29 minutes)
- Respects Gmail rate limits (max 50 concurrent connections, capped fetch at 50 unseen)

## Scope

### In Scope

- IMAP IDLE listener implementation
- Email parsing and message structure
- Connection resilience
- Gmail-specific defaults

### Out of Scope (Future Phases)

- Persistent message history
- Gmail OAuth support (App Password only)
- Other email providers
- Variable OTP formats beyond 6-digit DNSE codes

## Success Metrics

- Listener connects/disconnects reliably under normal conditions
- Auto-reconnect succeeds after temporary network outages
- Email parsing preserves all MIME parts (text/HTML) correctly
- Zero polling overhead (IDLE only)
