import os
import re
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

import yaml

from server import db as dbmod
from tests.helpers import GOOD_PW, H, AppCase
from tools.backup import backup

ROOT = Path(__file__).resolve().parent.parent


class OpsTests(AppCase):
    def test_backup_is_consistent_restorable_and_pruned(self):
        self.register()
        self.client.put("/api/challenges/c1", json={"name": "Keep me", "days": 21, "start": "2026-11-01", "created": 1}, headers=H)
        out = Path(self.dir.name) / "bk"
        files = []
        for _ in range(3):
            files.append(backup(self.db_path, str(out), keep=2))
            time.sleep(0.01)
        self.assertEqual(len({f.name for f in files}), 3)
        self.assertEqual(len(list(out.glob("grit-*.db"))), 2)   # oldest one pruned
        self.assertFalse(files[0].exists())
        restored = sqlite3.connect(files[-1])
        self.assertEqual(restored.execute("PRAGMA integrity_check").fetchone()[0], "ok")
        self.assertEqual(restored.execute("SELECT COUNT(*) FROM challenges").fetchone()[0], 1)
        # a restored copy boots and the person can sign in again
        from server.main import create_app
        app2 = create_app({"db_path": str(files[-1]), "scrypt_n": 2 ** 10, "secure_cookies": False})
        r = app2.test_client().post("/api/auth/login", json={"email": "ada@example.com", "password": GOOD_PW}, headers=H)
        self.assertEqual(r.status_code, 200)

    def test_migrations_are_idempotent_and_versioned(self):
        self.assertEqual(dbmod.migrate(self.db_path), len(dbmod.MIGRATIONS))
        self.assertEqual(dbmod.migrate(self.db_path), len(dbmod.MIGRATIONS))
        tables = {r[0] for r in sqlite3.connect(self.db_path).execute("SELECT name FROM sqlite_master WHERE type='table'")}
        self.assertTrue({"users", "sessions", "challenges", "profiles", "avatars", "auth_attempts", "password_resets"} <= tables)

    def test_v1_database_upgrades_in_place_without_losing_users(self):
        path = os.path.join(self.dir.name, "old.db")
        conn = dbmod.connect(path)
        conn.execute("PRAGMA journal_mode=WAL")
        for stmt in dbmod.MIGRATIONS[0]:
            conn.execute(stmt)
        conn.execute("PRAGMA user_version=1")
        conn.execute("INSERT INTO users (email, password_hash, created_at, pw_changed_at) VALUES ('old@example.com','x',1,1)")
        conn.close()
        self.assertEqual(dbmod.migrate(path), len(dbmod.MIGRATIONS))
        check = sqlite3.connect(path)
        self.assertEqual(check.execute("SELECT email FROM users").fetchone()[0], "old@example.com")
        self.assertEqual(check.execute("SELECT COUNT(*) FROM password_resets").fetchone()[0], 0)

    def test_wal_and_foreign_keys_are_on(self):
        self.assertEqual(sqlite3.connect(self.db_path).execute("PRAGMA journal_mode").fetchone()[0], "wal")
        self.assertEqual(dbmod.connect(self.db_path).execute("PRAGMA foreign_keys").fetchone()[0], 1)
        self.assertEqual(dbmod.connect(self.db_path).execute("PRAGMA secure_delete").fetchone()[0], 1)


class DeployFileTests(unittest.TestCase):
    def test_wsgi_entry_boots_in_production_mode(self):
        with tempfile.TemporaryDirectory() as d:
            env = {**os.environ, "GRIT_ENV": "production", "GRIT_DB": os.path.join(d, "p.db"), "GRIT_TRUST_PROXY": "1"}
            code = "import wsgi; c=wsgi.app.test_client(); r=c.get('/api/ready'); print(r.status_code, r.headers['Strict-Transport-Security'])"
            out = subprocess.run([sys.executable, "-c", code], cwd=ROOT, env=env, capture_output=True, text=True)
            self.assertEqual(out.stdout.split()[0], "200", out.stderr[-500:])
            self.assertIn("max-age", out.stdout)

    def test_gunicorn_config_loads(self):
        ns: dict = {}
        exec(compile((ROOT / "deploy/gunicorn.conf.py").read_text(), "g", "exec"), ns)
        self.assertTrue(ns["preload_app"] and ns["workers"] >= 1 and ns["bind"].endswith(":8000"))

    def test_compose_and_dockerfile_follow_basics(self):
        compose = yaml.safe_load((ROOT / "docker-compose.yml").read_text())
        self.assertEqual(set(compose["services"]), {"grit", "caddy"})
        self.assertNotIn("ports", compose["services"]["grit"])         # the app is only reachable through the proxy
        self.assertEqual(compose["services"]["grit"]["environment"]["GRIT_TRUST_PROXY"], "1")
        df = (ROOT / "Dockerfile").read_text()
        self.assertRegex(df, r"(?m)^USER grit$")                        # not root
        self.assertIn("HEALTHCHECK", df)
        self.assertIn("gunicorn", df)
        self.assertNotRegex(df, r"COPY\s+\.\s")                          # never copies the whole tree (tests, .env, db files)
        self.assertTrue(re.search(r"\*\.db", (ROOT / ".dockerignore").read_text()))

    def test_requirements_are_pinned_to_minimums_and_small(self):
        reqs = [l for l in (ROOT / "requirements.txt").read_text().split() if l]
        self.assertEqual(sorted(r.split(">=")[0].lower() for r in reqs), ["flask", "gunicorn", "pillow"])


if __name__ == "__main__":
    unittest.main()


class ProductionPathTests(AppCase):
    def test_smtp_mailer_sends_a_message_without_blocking_the_request(self):
        from unittest import mock
        sent = {}

        class FakeSMTP:
            def __init__(self, host, port, timeout=None):
                sent["host"], sent["port"] = host, port
            def __enter__(self): return self
            def __exit__(self, *a): return False
            def starttls(self): sent["tls"] = True
            def login(self, u, p): sent["login"] = (u, p)
            def send_message(self, msg): sent["to"], sent["subject"], sent["body"] = msg["To"], msg["Subject"], msg.get_content()

        self.overrides = {"public_url": "https://h.example.com", "smtp_host": "smtp.example.com", "smtp_user": "u", "smtp_password": "p"}
        self.setUp()
        with mock.patch("server.mail.smtplib.SMTP", FakeSMTP):
            self.register()
            self.assertEqual(self.new_client().post("/api/auth/forgot", json={"email": "ada@example.com"}, headers=H).status_code, 200)
            import threading
            for t in threading.enumerate():
                if t is not threading.current_thread() and t.daemon:
                    t.join(2)
        self.assertEqual((sent["host"], sent["port"], sent["tls"], sent["login"]), ("smtp.example.com", 587, True, ("u", "p")))
        self.assertEqual(sent["to"], "ada@example.com")
        self.assertIn("https://h.example.com/auth.html#reset=", sent["body"])
        self.overrides = {}

    def test_smtp_failure_never_breaks_the_request(self):
        from unittest import mock
        self.overrides = {"public_url": "https://h.example.com", "smtp_host": "smtp.example.com"}
        self.setUp()
        with mock.patch("server.mail.smtplib.SMTP", side_effect=OSError("down")):
            self.register()
            self.assertEqual(self.new_client().post("/api/auth/forgot", json={"email": "ada@example.com"}, headers=H).status_code, 200)
        self.overrides = {}

    def test_unexpected_errors_return_generic_json_not_a_traceback(self):
        @self.app.get("/api/boom")
        def boom():
            zero = 0
            return 1 / zero  # intentional ZeroDivisionError – tests that the server returns JSON 500
        r = self.client.get("/api/boom")
        self.assertEqual(r.status_code, 500)
        self.assertNotIn("ZeroDivision", r.get_data(as_text=True))
        self.assertIn("error", r.get_json())

    def test_behind_a_proxy_throttling_uses_the_real_client_address(self):
        self.overrides = {"trust_proxy": 1}
        self.setUp()
        self.register()
        def attempt(ip):
            return self.new_client().post("/api/auth/login", json={"email": "ada@example.com", "password": "wrong wrong wrong"},
                                          headers={**H, "X-Forwarded-For": ip}).status_code
        self.assertEqual([attempt("203.0.113.9") for _ in range(6)], [401] * 5 + [429])   # one attacker is locked out...
        self.assertEqual(attempt("198.51.100.4"), 401)                                      # ...other visitors are not
        self.overrides = {}
