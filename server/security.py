"""Password hashing, session tokens and input rules. Standard library only."""
from __future__ import annotations

import base64
import hashlib
import hmac
import re
import secrets
import unicodedata

_MAXMEM = 128 * 1024 * 1024
_EMAIL = re.compile(r"^[^@\s]{1,64}@[^@\s]{1,190}\.[^@\s.]{2,24}$")
COMMON = {
    "password", "password1", "password12", "password123", "passw0rd123", "1234567890", "12345678910",
    "qwertyuiop", "qwerty12345", "qwerty123456", "iloveyou123", "letmein1234", "welcome1234",
    "administrator", "abc1234567", "1q2w3e4r5t", "1qaz2wsx3edc", "0123456789", "9876543210",
    "passwordpassword", "changeme123", "trustno1234", "football123", "monkey12345", "dragon12345",
}


def _b64(raw: bytes) -> str:
    return base64.b64encode(raw).decode("ascii")


def hash_password(password: str, n: int = 2 ** 15, r: int = 8, p: int = 3) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=n, r=r, p=p, maxmem=_MAXMEM, dklen=32)
    return f"scrypt${n}${r}${p}${_b64(salt)}${_b64(digest)}"


def _parse(stored: str):
    scheme, n, r, p, salt, digest = stored.split("$")
    if scheme != "scrypt":
        raise ValueError("unknown scheme")
    return int(n), int(r), int(p), base64.b64decode(salt), base64.b64decode(digest)


def verify_password(stored: str, password: str) -> bool:
    try:
        n, r, p, salt, digest = _parse(stored)
        got = hashlib.scrypt(password.encode(), salt=salt, n=n, r=r, p=p, maxmem=_MAXMEM, dklen=len(digest))
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(got, digest)


def needs_rehash(stored: str, n: int, r: int, p: int) -> bool:
    try:
        sn, sr, sp, *_ = _parse(stored)
    except ValueError:
        return True
    return (sn, sr, sp) != (n, r, p)


def new_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """Only the hash of a session token is stored, so a leaked database cannot be used to sign in."""
    return hashlib.sha256(token.encode()).hexdigest()


def normalize_email(value) -> str:
    return unicodedata.normalize("NFKC", value).strip().lower() if isinstance(value, str) else ""


def email_error(email: str) -> str | None:
    if not email or len(email) > 254 or not _EMAIL.match(email):
        return "Enter a valid email address."
    return None


def password_error(password, email: str = "") -> str | None:
    if not isinstance(password, str):
        return "Enter a password."
    if len(password) < 10:
        return "Use at least 10 characters."
    if len(password) > 128:
        return "Use at most 128 characters."
    low = password.lower()
    if low in COMMON or len(set(password)) < 4:
        return "That password is too easy to guess. Try a longer phrase."
    if email and (low == email or low == email.split("@")[0]):
        return "Your password should not be your email."
    return None


def clean_name(value, limit: int = 30) -> str:
    if not isinstance(value, str):
        return ""
    return "".join(ch for ch in value if ch.isprintable()).strip()[:limit]
