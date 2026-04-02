# Project Overview & Product Requirements

## Product Definition

**dnse-emailotp** is a Python library for retrieving one-time passwords (OTPs) from Gmail via IMAP IDLE. It monitors an inbox in real-time, detects new emails without polling, and extracts OTP codes from email bodies.

**Use Case:** Automated account registration, login flows, or integrations requiring OTP verification from Gmail accounts.

## Key Features

- **Real-time IDLE Monitoring:** Uses IMAP IDLE (RFC 2177) to detect new messages without polling overhead
- **Auto-Reconnect:** Recovers from connection failures with exponential backoff (up to 3 retries)
- **Email Parsing:** Extracts subject, sender, date, plain text, and HTML body from RFC822 messages
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
3. **OTP Extraction:** Identify and extract OTP codes from email bodies
4. **Convenience API:** High-level function combining listener + parser
5. **Error Handling:** Graceful reconnection on network failures

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

- OTP extraction logic (parser stub)
- High-level convenience API (helper stub)
- Persistent message history
- Gmail OAuth support (App Password only)
- Other email providers

## Success Metrics

- Listener connects/disconnects reliably under normal conditions
- Auto-reconnect succeeds after temporary network outages
- Email parsing preserves all MIME parts (text/HTML) correctly
- Zero polling overhead (IDLE only)
