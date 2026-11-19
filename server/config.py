"""Settings. Everything comes from environment variables so one image runs anywhere."""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass, replace
from pathlib import Path


def _flag(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    return default if raw is None else raw.strip().lower() in {"1", "true", "yes", "on"}


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except ValueError:
        return default


def default_db_path() -> str:
    base = os.getenv("APPDATA") if sys.platform == "win32" else None
    folder = Path(base) / "Grit" if base else Path.home() / ".grit"
    folder.mkdir(parents=True, exist_ok=True)
    return str(folder / "grit.db")


@dataclass(frozen=True)
class Settings:
    env: str = "production"
    db_path: str = ""
    secure_cookies: bool = True
    trust_proxy: int = 0                    # number of reverse proxies in front of the app
    session_days: int = 30
    max_challenges: int = 100               # per user
    max_user_bytes: int = 5 * 1024 * 1024   # stored challenge data per user
    avatar_max_bytes: int = 2 * 1024 * 1024
    login_pair_limit: int = 5               # failures per (ip, email) per window
    login_email_limit: int = 25             # failures per email per window, any ip
    login_ip_limit: int = 60                # failures per ip per window
    register_ip_limit: int = 10             # sign ups per ip per hour
    throttle_window_s: int = 900
    register_window_s: int = 3600
    scrypt_n: int = 2 ** 15
    scrypt_r: int = 8
    scrypt_p: int = 3
    reset_minutes: int = 60
    public_url: str = ""                    # e.g. https://habits.example.com, used in emailed links
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "Habit Tracker <no-reply@localhost>"
    smtp_starttls: bool = True

    @classmethod
    def from_env(cls, **overrides) -> "Settings":
        env = os.getenv("GRIT_ENV", "production").lower()
        base = cls(
            env=env,
            db_path=os.getenv("GRIT_DB") or default_db_path(),
            secure_cookies=_flag("GRIT_SECURE_COOKIES", env == "production"),
            trust_proxy=_int("GRIT_TRUST_PROXY", 0),
            session_days=_int("GRIT_SESSION_DAYS", 30),
            public_url=os.getenv("GRIT_PUBLIC_URL", "").rstrip("/"),
            smtp_host=os.getenv("GRIT_SMTP_HOST", ""),
            smtp_port=_int("GRIT_SMTP_PORT", 587),
            smtp_user=os.getenv("GRIT_SMTP_USER", ""),
            smtp_password=os.getenv("GRIT_SMTP_PASSWORD", ""),
            smtp_from=os.getenv("GRIT_SMTP_FROM", "Habit Tracker <no-reply@localhost>"),
            smtp_starttls=_flag("GRIT_SMTP_STARTTLS", True),
        )
        return replace(base, **overrides)
