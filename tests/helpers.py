import io
import os
import tempfile
import unittest

from PIL import Image

from server.main import create_app

H = {"X-Requested-With": "grit"}
GOOD_PW = "correct horse battery"


def png(size=(600, 400), color=(200, 30, 30), fmt="PNG", exif=None) -> bytes:
    buf = io.BytesIO()
    img = Image.new("RGB", size, color)
    kwargs = {"exif": exif} if exif else {}
    img.save(buf, fmt, **kwargs)
    return buf.getvalue()


def challenge(**over):
    body = {"name": "Morning walk", "days": 21, "start": "2026-11-01", "created": 5, "ticks": {"0": True, "1": True}, "notes": {"0": "Good start"}}
    body.update(over)
    return body


class AppCase(unittest.TestCase):
    overrides: dict = {}

    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.db_path = os.path.join(self.dir.name, "t.db")
        cfg = {"db_path": self.db_path, "scrypt_n": 2 ** 10, "secure_cookies": False}
        cfg.update(self.overrides)
        self.app = create_app(cfg)
        self.client = self.app.test_client()

    def new_client(self):
        return self.app.test_client()

    def register(self, client=None, email="ada@example.com", password=GOOD_PW, **extra):
        return (client or self.client).post("/api/auth/register", json={"email": email, "password": password, **extra}, headers=H)

    def login(self, client, email="ada@example.com", password=GOOD_PW):
        return client.post("/api/auth/login", json={"email": email, "password": password}, headers=H)

    def user(self, email):
        c = self.new_client()
        self.assertEqual(self.register(c, email=email).status_code, 201)
        return c
