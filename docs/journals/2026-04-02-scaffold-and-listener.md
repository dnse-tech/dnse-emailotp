# dnse-emailotp Scaffold & IMAP IDLE Listener Implementation

**Date**: 2026-04-02 16:54
**Severity**: Low (foundational work)
**Component**: Core architecture, IMAP listener
**Status**: Resolved

## What Happened

Completed full project scaffold and IMAP IDLE listener implementation. Created production-grade foundation for Gmail OTP retrieval library.

## Deliverables

1. **Project scaffold**: hatch-based pyproject.toml, src layout, git init with v0.0.1 tag
2. **ImapListener class**: Real-time IDLE email detection with auto-reconnect (exponential backoff, 3 retries max), context manager, multipart/plain/HTML parsing
3. **EmailMessage dataclass**: Frozen, typed (uid, subject, sender, date, body_text, body_html)
4. **Stubs**: parser.py (extract_otp) and helper.py (wait_for_otp) — NotImplementedError placeholders
5. **Test suite**: 57 unit tests, 80% coverage; pyright strict + ruff clean
6. **Documentation**: PDR, system architecture, code standards, codebase summary

## Critical Decisions

- **imapclient>=2.3** (not stdlib imaplib — lacks IDLE support)
- Gmail defaults (imap.gmail.com:993) but configurable
- IDLE re-issue every 28 min (RFC 2177 compliance: < 29 min max)
- models.py separate from listener.py (prevent circular imports)
- max_fetch=50 cap on unseen emails (prevent OOM)

## Code Review Findings & Fixes

- Typed _with_reconnect callback (was Any)
- Added max_fetch limit on fetch_unseen
- Moved parsedate_to_datetime import to module top level

## Review Scores

Security: 8/10 | Quality: 8/10 | Architecture: 9/10

## Next Steps

1. Implement extract_otp with regex patterns for common OTP formats
2. Implement wait_for_otp integrating ImapListener + extract_otp
3. Add integration tests (Gmail sandbox)
