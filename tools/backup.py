"""Consistent online backup of the database (safe while the app is running).

    python -m tools.backup /backups            # uses GRIT_DB, keeps the newest 14
    python -m tools.backup /backups --keep 30 --db /data/grit.db
"""
from __future__ import annotations

import argparse
import sqlite3
import time
from pathlib import Path


def backup(src: str, dest_dir: str, keep: int = 14) -> Path:
    out_dir = Path(dest_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    now = time.time()
    out = out_dir / f"grit-{time.strftime('%Y%m%d-%H%M%S', time.gmtime(now))}-{int(now * 1000) % 1000:03d}.db"
    source, target = sqlite3.connect(src), sqlite3.connect(out)
    try:
        source.backup(target)
        if target.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise RuntimeError("backup failed its integrity check")
    finally:
        target.close()
        source.close()
    for old in sorted(out_dir.glob("grit-*.db"))[:-keep]:
        old.unlink()
    return out


if __name__ == "__main__":
    from server.config import Settings

    ap = argparse.ArgumentParser()
    ap.add_argument("dest")
    ap.add_argument("--db", default=Settings.from_env().db_path)
    ap.add_argument("--keep", type=int, default=14)
    a = ap.parse_args()
    print(backup(a.db, a.dest, a.keep))
