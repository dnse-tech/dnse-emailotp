# dnse-emailotp

Gmail OTP retrieval via IMAP IDLE for DNSE.

## Install

```bash
pip install dnse-emailotp
```

## Quick Start

```python
from dnse_email_otp import ImapListener

with ImapListener("you@gmail.com", "app-password") as listener:
    msg = listener.wait_for_new_message(timeout=60)
    if msg:
        print(msg.subject, msg.body_text)
```

## Requirements

- Python >= 3.10
- Gmail account with [App Password](https://support.google.com/accounts/answer/185833) (required when 2FA is enabled)
