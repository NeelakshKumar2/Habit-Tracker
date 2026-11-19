"""Runs the real browser-side JavaScript (in Node, with a small DOM stub) against a real running server."""
import json
import os
import shutil
import subprocess
import tempfile
import threading
import unittest

from werkzeug.serving import make_server

from server.main import create_app


@unittest.skipUnless(shutil.which("node"), "node not installed")
class FrontendE2E(unittest.TestCase):
    def test_front_end_against_live_server(self):
        with tempfile.TemporaryDirectory() as d:
            app = create_app({"db_path": os.path.join(d, "t.db"), "scrypt_n": 2 ** 10, "secure_cookies": False})
            srv = make_server("127.0.0.1", 0, app, threaded=True)
            threading.Thread(target=srv.serve_forever, daemon=True).start()
            try:
                p = subprocess.run(["node", "tests/frontend_e2e.mjs", f"http://127.0.0.1:{srv.server_port}"], capture_output=True, text=True, timeout=120)
            finally:
                srv.shutdown()
        self.assertTrue(p.stdout.strip(), p.stderr[-2000:])
        results = json.loads(p.stdout.strip().splitlines()[-1])
        failed = [r for r in results if not r["ok"]]
        self.assertEqual(failed, [], f"{len(results)} checks ran; failed: {failed}\n{p.stderr[-1500:]}")
        self.assertGreaterEqual(len(results), 20)


if __name__ == "__main__":
    unittest.main()
