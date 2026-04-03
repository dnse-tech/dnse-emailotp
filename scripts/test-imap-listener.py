"""Test script: connect to Gmail IMAP, wait for new email, print and save to file.

Usage:
    export GMAIL_ADDRESS="you@gmail.com"
    export GMAIL_APP_PASSWORD="xxxx xxxx xxxx xxxx"
    python scripts/test-imap-listener.py

    # Custom timeout and output file:
    python scripts/test-imap-listener.py --timeout 120 --output email-template.txt

    # Fetch latest existing unseen email:
    python scripts/test-imap-listener.py --fetch-existing
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path

from dnse_email_otp import EmailMessage, ImapListener

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)

_DEFAULT_OUTPUT = "scripts/email-template.json"


def main() -> None:
    """Connect to Gmail, wait for email via IDLE, print and save result."""
    parser = argparse.ArgumentParser(description="Test IMAP IDLE listener")
    parser.add_argument(
        "--timeout", type=float, default=60.0, help="Seconds to wait (default: 60)"
    )
    parser.add_argument(
        "--fetch-existing", action="store_true", help="Fetch latest unseen email"
    )
    parser.add_argument(
        "--output", "-o", type=str, default=_DEFAULT_OUTPUT,
        help=f"Output file path (default: {_DEFAULT_OUTPUT})",
    )
    args = parser.parse_args()

    email_addr = os.environ.get("GMAIL_ADDRESS", "")
    app_password = os.environ.get("GMAIL_APP_PASSWORD", "")
    if not email_addr or not app_password:
        print(
            "Error: set GMAIL_ADDRESS and GMAIL_APP_PASSWORD env vars",
            file=sys.stderr,
        )
        sys.exit(1)

    with ImapListener(email_addr, app_password) as listener:
        if args.fetch_existing:
            print("--- Fetching latest unseen email ---")
            msg = listener.fetch_latest_unseen()
        else:
            print(f"--- Waiting for new email (timeout={args.timeout}s) ---")
            msg = listener.wait_for_new_message(timeout=args.timeout)

        if msg is None:
            print("No email found.")
            sys.exit(1)

        _print_message(msg)
        _save_message(msg, args.output)


def _print_message(msg: EmailMessage) -> None:
    """Print email message fields to stdout."""
    print(f"UID:     {msg.uid}")
    print(f"From:    {msg.sender}")
    print(f"Subject: {msg.subject}")
    print(f"Date:    {msg.date}")
    print(f"Body:\n{msg.body_text}")
    if msg.body_html:
        print(f"HTML:    (length={len(msg.body_html)})")
    print("---")


def _save_message(msg: EmailMessage, output_path: str) -> None:
    """Save email message to a JSON file as a template."""
    data = {
        "uid": msg.uid,
        "subject": msg.subject,
        "sender": msg.sender,
        "date": msg.date.isoformat(),
        "body_text": msg.body_text,
        "body_html": msg.body_html,
    }
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    print(f"Saved to: {path}")


if __name__ == "__main__":
    main()
