"""SQLite storage with versioned migrations. WAL mode lets many readers run beside one writer,
foreign keys cascade so deleting a user removes everything they own, and secure_delete zeroes
freed pages so a deleted account does not linger in the file."""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager

from flask import current_app, g

MIGRATIONS: list[list[str]] = [
    [  # v1
        """CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            display_name TEXT NOT NULL DEFAULT '',
            created_at INTEGER NOT NULL,
            pw_changed_at INTEGER NOT NULL)""",
        """CREATE TABLE sessions (
            token_hash TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            created_at INTEGER NOT NULL,
            expires_at INTEGER NOT NULL,
            last_seen INTEGER NOT NULL,
            user_agent TEXT NOT NULL DEFAULT '')""",
        "CREATE INDEX sessions_user ON sessions(user_id)",
        "CREATE INDEX sessions_exp ON sessions(expires_at)",
        """CREATE TABLE challenges (
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            id TEXT NOT NULL,
            data TEXT NOT NULL,
            created INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (user_id, id)) WITHOUT ROWID""",
        """CREATE TABLE profiles (
            user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
            data TEXT NOT NULL)""",
        """CREATE TABLE avatars (
            user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
            mime TEXT NOT NULL,
            data BLOB NOT NULL,
            updated_at INTEGER NOT NULL)""",
        """CREATE TABLE auth_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kind TEXT NOT NULL,
            key TEXT NOT NULL,
            at INTEGER NOT NULL)""",
        "CREATE INDEX attempts_lookup ON auth_attempts(kind, key, at)",
        "CREATE INDEX attempts_at ON auth_attempts(at)",
    ],
    [  # v2: password reset links
        """CREATE TABLE password_resets (
            token_hash TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            expires_at INTEGER NOT NULL)""",
        "CREATE INDEX resets_user ON password_resets(user_id)",
    ],
]


def connect(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(path, timeout=10, isolation_level=None)  # autocommit; we open transactions ourselves
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=10000")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA secure_delete=ON")
    return conn


def migrate(path: str) -> int:
    """Bring the database to the latest schema. Safe when several workers start at once."""
    conn = connect(path)
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        for i, statements in enumerate(MIGRATIONS):
            conn.execute("BEGIN IMMEDIATE")
            try:
                if conn.execute("PRAGMA user_version").fetchone()[0] <= i:
                    for stmt in statements:
                        conn.execute(stmt)
                    conn.execute(f"PRAGMA user_version={i + 1}")
                conn.execute("COMMIT")
            except Exception:
                conn.execute("ROLLBACK")
                raise
        return conn.execute("PRAGMA user_version").fetchone()[0]
    finally:
        conn.close()


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = connect(current_app.extensions["grit"].db_path)
    return g.db


def close_db(_exc=None) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


@contextmanager
def tx(db: sqlite3.Connection):
    """A write transaction that takes the write lock up front, so check-then-insert is race free."""
    db.execute("BEGIN IMMEDIATE")
    try:
        yield db
    except BaseException:
        db.execute("ROLLBACK")
        raise
    else:
        db.execute("COMMIT")
