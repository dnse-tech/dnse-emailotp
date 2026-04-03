# dnse-emailotp

Gmail OTP retrieval via IMAP IDLE for DNSE.

## Install

```bash
pip install dnse-emailotp
```

## Quick Start

```python
from dnse_email_otp import ImapListener, extract_otp

with ImapListener("you@gmail.com", "app-password") as listener:
    msg = listener.wait_for_new_message(timeout=60)
    if msg:
        otp = extract_otp(msg.body_text)
        print(otp)  # "510345"
```

Or use the convenience helper:

```python
from dnse_email_otp import wait_for_otp

otp = wait_for_otp("you@gmail.com", "app-password", timeout=60)
print(otp)  # "510345"
```

## Requirements

- Python >= 3.10
- Gmail account with [App Password](https://support.google.com/accounts/answer/185833) (required when 2FA is enabled)

## License

Licensed under [PolyForm Noncommercial 1.0.0](LICENSE).

Free for personal and noncommercial use. For commercial licensing, contact [DNSE](https://dnse.com.vn).
