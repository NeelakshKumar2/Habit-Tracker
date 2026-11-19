"""Do the tests actually catch bugs?  Break the code on purpose, one change at a time, and confirm the suite fails.
    python tools/mutation_check.py"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
M = [
    ("one person can read everyone's challenges", "server/api.py", "WHERE user_id=? ORDER BY created DESC, id", "WHERE ? > 0 ORDER BY created DESC, id"),
    ("CSRF header check removed", "server/main.py", 'if request.headers.get("X-Requested-With") != "grit":', "if False:"),
    ("delete account without the password", "server/auth.py", 'if not _check_password(db, u["id"], u["email"], body.get("password")):', "if False:"),
    ("session tokens stored in plain text", "server/security.py", "return hashlib.sha256(token.encode()).hexdigest()", "return token"),
    ("login brute-force throttle removed", "server/auth.py", '    check_login_throttle(db, email)\n    row = db.execute("SELECT id, password_hash', '    row = db.execute("SELECT id, password_hash'),
    ("password check always succeeds", "server/security.py", "return hmac.compare_digest(got, digest)", "return True"),
    ("expired sessions accepted", "server/auth.py", 'WHERE s.token_hash = ? AND s.expires_at > ?", (h, now))', 'WHERE s.token_hash = ? AND ? > 0", (h, now))'),
    ("image size guard removed (decompression bomb)", "server/avatar.py", "MAX_PIXELS = 16_000_000", "MAX_PIXELS = 10 ** 12"),
    ("deleted data left on disk (secure_delete off)", "server/db.py", 'PRAGMA secure_delete=ON', 'PRAGMA secure_delete=OFF'),
    ("ticks may point outside the challenge", "server/validators.py", "k.isdigit() and int(k) < days", "k.isdigit() and int(k) < 10 ** 9"),
    ("password change keeps other sessions", "server/auth.py", '        db.execute("DELETE FROM sessions WHERE user_id=? AND token_hash<>?", (u["id"], g.session_hash))\n', ""),
    ("password reset keeps old sessions", "server/auth.py", '        db.execute("DELETE FROM sessions WHERE user_id=?", (row["user_id"],))\n', ""),
    ("CSP allows inline scripts", "server/main.py", "script-src 'self';", "script-src 'self' 'unsafe-inline';"),
    ("browser stops escaping HTML", "web/js/core/util.js", "replace(/[&<>\"']/g,", "replace(/[\\u0000]/g,"),
    ("browser score formula drifts from the server", "web/js/core/domain.js", "raw*cons*rec/1200", "raw*cons*rec/1300"),
]


def main() -> int:
    survived = []
    for name, rel, old, new in M:
        with tempfile.TemporaryDirectory() as d:
            work = Path(d) / "p"
            shutil.copytree(ROOT, work, ignore=shutil.ignore_patterns(".git", "__pycache__", "*.db*", ".venv"))
            f = work / rel
            src = f.read_text()
            assert src.count(old) == 1, f"mutation target not unique/found: {name} ({src.count(old)})"
            f.write_text(src.replace(old, new))
            r = subprocess.run([sys.executable, "-W", "ignore", "-m", "unittest", "discover", "-f", "-s", "tests", "-t", "."], cwd=work, capture_output=True, text=True)
            killed = r.returncode != 0
            failing = next((l.split()[1] for l in r.stderr.splitlines() if l.startswith(("FAIL:", "ERROR:"))), "test process crashed (out of memory)")
            print(f"{'KILLED  ' if killed else 'SURVIVED'}  {name:50} caught by {failing if killed else '-'}", flush=True)
            if not killed:
                survived.append(name)
    print(f"\n{len(M) - len(survived)}/{len(M)} mutants killed")
    return 1 if survived else 0


if __name__ == "__main__":
    sys.exit(main())
