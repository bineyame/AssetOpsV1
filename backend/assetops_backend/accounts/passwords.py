"""3C0a (spec §3; D-3C0A.10, R3, R4): the password hash, its policy and the email rule.

scrypt from the standard library (n=32768, r=8, p=1, a 16-byte salt, a 32-byte key), stored self-describing as
`scrypt$32768$8$1$<salt>$<hash>` in unpadded URL-safe base64. A stored hash in any other form fails verification;
it never raises.
"""
from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import os
import re

from assetops_backend.accounts.model import AccountRefused

_N, _R, _P, _MAXMEM, _DKLEN = 32768, 8, 1, 67108864, 32
_FORM = re.compile(r"scrypt\$32768\$8\$1\$([A-Za-z0-9_-]{22})\$([A-Za-z0-9_-]{43})")
#: Printable ASCII with no `@`, space or control character on either side (R3).
_EMAIL = re.compile(r"[!-?A-~]{1,64}@[!-?A-~]{1,255}")
MAX_EMAIL = 320
MIN_PASSWORD, MAX_PASSWORD = 12, 128


def _b64(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _unb64(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def _derive(password: str, salt: bytes) -> bytes:
    return hashlib.scrypt(password.encode("utf-8"), salt=salt, n=_N, r=_R, p=_P, maxmem=_MAXMEM, dklen=_DKLEN)


def _hash(password: str, salt: bytes) -> str:
    return f"scrypt${_N}${_R}${_P}${_b64(salt)}${_b64(_derive(password, salt))}"


def hash_password(password: str) -> str:
    return _hash(password, os.urandom(16))


def verify_password(password: str, stored: str) -> bool:
    found = _FORM.fullmatch(stored) if isinstance(stored, str) else None
    if found is None:
        return False
    try:
        salt, expected = _unb64(found.group(1)), _unb64(found.group(2))
    except (binascii.Error, ValueError):
        return False
    if len(salt) != 16 or len(expected) != _DKLEN:
        return False
    return hmac.compare_digest(_derive(password, salt), expected)


#: Verified against on every refused sign-in that has no stored hash (R4), made once at import with a fixed salt.
DUMMY_HASH = _hash("assetops-dummy-password", b"assetops-dummy!!")


def check_policy(password: str) -> None:
    """12 to 128 characters, not all whitespace, kept exactly as typed."""
    if (not isinstance(password, str) or not MIN_PASSWORD <= len(password) <= MAX_PASSWORD
            or password.isspace()):
        raise AccountRefused("PASSWORD_POLICY", 422)


def normalise_email(text: str) -> tuple[str, str]:
    """(email, email_key): trimmed, then printable ASCII `local@domain`, at most 320 characters; the key is lower."""
    email = text.strip() if isinstance(text, str) else ""
    if len(email) > MAX_EMAIL or _EMAIL.fullmatch(email) is None:
        raise AccountRefused("BAD_EMAIL", 422)
    return email, email.lower()
