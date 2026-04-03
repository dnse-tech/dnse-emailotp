#!/usr/bin/env python3
"""Example: listen for incoming email, parse OTP, print it.

Usage:
    # Using environment variables (recommended):
    export EMAIL_ADDRESS="you@gmail.com"
    export EMAIL_APP_PASSWORD="xxxx-xxxx-xxxx-xxxx"
    python scripts/example-listen-parse-print-otp.py

    # Or pass directly:
    python scripts/example-listen-parse-print-otp.py --email you@gmail.com --password xxxx-xxxx-xxxx-xxxx

    # Custom timeout (default: 120s):
    python scripts/example-listen-parse-print-otp.py --timeout 180
"""

from __future__ import annotations

import argparse
import logging
import os
import sys

from dnse_email_otp import ImapListener, extract_otp

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Listen for DNSE OTP email and print the code.")
    parser.add_argument("--email", default=os.getenv("EMAIL_ADDRESS"), help="Gmail address (or set EMAIL_ADDRESS env var)")
    parser.add_argument("--password", default=os.getenv("EMAIL_APP_PASSWORD"), help="Gmail app password (or set EMAIL_APP_PASSWORD env var)")
    parser.add_argument("--timeout", type=float, default=120.0, help="Max seconds to wait (default: 120)")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if not args.email or not args.password:
        print("Error: email and password required. Use --email/--password or set EMAIL_ADDRESS/EMAIL_APP_PASSWORD env vars.")
        sys.exit(1)

    log.info("Connecting to Gmail IMAP for %s ...", args.email)
    log.info("Waiting up to %.0fs for new email...", args.timeout)

    # Step 1: Listen — connect via IMAP IDLE and wait for a new email
    with ImapListener(args.email, args.password) as listener:
        msg = listener.wait_for_new_message(timeout=args.timeout)

    if msg is None:
        log.warning("No email received within timeout.")
        sys.exit(1)

    log.info("Email received — from=%s subject=%s", msg.sender, msg.subject)

    # Step 2: Parse — extract 6-digit OTP from email body
    otp = extract_otp(msg.body_text) or extract_otp(msg.body_html)

    if otp is None:
        log.warning("No OTP found in email body.")
        sys.exit(1)

    # Step 3: Print
    print(f"\nOTP: {otp}\n")


if __name__ == "__main__":
    main()
