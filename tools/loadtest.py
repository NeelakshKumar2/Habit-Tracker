"""Multi-process load test: several server processes share one SQLite file (like gunicorn workers) and
many virtual users hit them at once. Uses production password-hashing settings.
    python tools/loadtest.py --users 120 --workers 4 --concurrency 16"""
from __future__ import annotations

import argparse
import io
import os
import random
import sqlite3
import statistics
import subprocess
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
H = {"X-Requested-With": "grit"}
WORKER = ("import logging,sys;logging.disable(logging.CRITICAL);from server.main import create_app;"
          "from werkzeug.serving import make_server;make_server('127.0.0.1',int(sys.argv[1]),create_app(),threaded=True).serve_forever()")


def png(rnd) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (640, 480), tuple(rnd.randrange(256) for _ in range(3))).save(buf, "PNG")
    return buf.getvalue()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--users", type=int, default=120)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--concurrency", type=int, default=16)
    a = ap.parse_args()
    d = tempfile.mkdtemp()
    db = os.path.join(d, "load.db")
    env = {**os.environ, "GRIT_ENV": "development", "GRIT_TRUST_PROXY": "1", "GRIT_DB": db, "PYTHONPATH": str(ROOT)}
    ports = [18100 + i for i in range(a.workers)]
    procs = [subprocess.Popen([sys.executable, "-c", WORKER, str(p)], cwd=ROOT, env=env, stderr=subprocess.DEVNULL) for p in ports]  # started together: migrations race on purpose
    try:
        for p in ports:
            for _ in range(100):
                try:
                    requests.get(f"http://127.0.0.1:{p}/api/health", timeout=1)
                    break
                except requests.RequestException:
                    time.sleep(0.1)
        from server.security import hash_password
        t = time.perf_counter()
        hash_password("benchmark password")
        hash_ms = (time.perf_counter() - t) * 1000

        lat: dict[str, list[float]] = {}
        errors: list[str] = []
        lock = threading.Lock()
        png_data = png(random.Random(1))
        K = 3  # challenges written per user

        def call(op, session, method, path, expect=(200, 201, 204), **kw):
            base = f"http://127.0.0.1:{random.choice(ports)}"
            t0 = time.perf_counter()
            try:
                r = session.request(method, base + path, headers=H, timeout=60, **kw)
                ok = r.status_code in expect
            except requests.RequestException as e:
                r, ok = None, False
                with lock:
                    errors.append(f"{op}: {type(e).__name__}")
            dt = (time.perf_counter() - t0) * 1000
            with lock:
                lat.setdefault(op, []).append(dt)
                if not ok and r is not None:
                    errors.append(f"{op}: HTTP {r.status_code} {r.text[:80]}")
            return r

        def user(i: int):
            s = requests.Session()
            s.headers["X-Forwarded-For"] = f"10.1.{i // 250}.{i % 250 + 1}"   # each person has their own address, as behind a real proxy
            email, pw = f"load{i}@example.com", "load test passphrase"
            call("register", s, "POST", "/api/auth/register", json={"email": email, "password": pw, "name": f"U{i}"})
            call("state", s, "GET", "/api/state")                       # may land on a different worker than register
            for k in range(K):
                call("save challenge", s, "PUT", f"/api/challenges/c{k}", json={"name": f"Habit {k}", "days": 21, "start": "2026-11-01", "created": k, "ticks": {"0": True, "1": True}, "notes": {"0": "note"}})
            call("score", s, "GET", "/api/score")
            call("review", s, "GET", "/api/review")
            if i % 3 == 0:
                call("avatar upload", s, "PUT", "/api/me/avatar", files={"file": ("a.png", png_data, "image/png")})
                call("avatar get", s, "GET", "/api/me/avatar")
            call("logout", s, "POST", "/api/auth/logout")
            call("login", s, "POST", "/api/auth/login", json={"email": email, "password": pw})
            call("state", s, "GET", "/api/state")
            if i % 5 == 0:
                call("delete account", s, "DELETE", "/api/account", json={"password": pw})

        t0 = time.perf_counter()
        with ThreadPoolExecutor(a.concurrency) as ex:
            list(ex.map(user, range(a.users)))
        wall = time.perf_counter() - t0
        total = sum(len(v) for v in lat.values())

        conn = sqlite3.connect(db)
        deleted = len([i for i in range(a.users) if i % 5 == 0])
        want_users, want_ch = a.users - deleted, (a.users - deleted) * K
        got_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        got_ch = conn.execute("SELECT COUNT(*) FROM challenges").fetchone()[0]
        orphans = conn.execute("SELECT (SELECT COUNT(*) FROM challenges WHERE user_id NOT IN (SELECT id FROM users)) + (SELECT COUNT(*) FROM avatars WHERE user_id NOT IN (SELECT id FROM users)) + (SELECT COUNT(*) FROM sessions WHERE user_id NOT IN (SELECT id FROM users))").fetchone()[0]
        integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]

        print(f"cpu cores available : {os.cpu_count()}   server processes : {a.workers}   client threads : {a.concurrency}   virtual users : {a.users}")
        print(f"one password hash   : {hash_ms:.0f} ms (scrypt N=2^15, r=8, p=3)")
        print(f"requests            : {total} in {wall:.1f}s  ->  {total / wall:.0f} req/s")
        print(f"{'operation':16} {'n':>5} {'p50 ms':>8} {'p95 ms':>8} {'max ms':>8}")
        for op, v in sorted(lat.items()):
            v = sorted(v)
            print(f"{op:16} {len(v):5} {statistics.median(v):8.0f} {v[int(len(v) * 0.95) - 1]:8.0f} {v[-1]:8.0f}")
        print(f"unexpected errors   : {len(errors)}  {sorted(set(errors))[:5]}")
        print(f"users in db         : {got_users} (expected {want_users})")
        print(f"challenges in db    : {got_ch} (expected {want_ch}, none lost)")
        print(f"orphan rows         : {orphans} after {deleted} account deletions")
        print(f"sqlite integrity    : {integrity}")
        good = not errors and got_users == want_users and got_ch == want_ch and orphans == 0 and integrity == "ok"
        print("RESULT              :", "PASS" if good else "FAIL")
        return 0 if good else 1
    finally:
        for p in procs:
            p.terminate()


if __name__ == "__main__":
    sys.exit(main())
