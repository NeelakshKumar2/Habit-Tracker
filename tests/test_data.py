import io
import json

from tests.helpers import GOOD_PW, H, AppCase, challenge, png


class IsolationTests(AppCase):
    def test_every_data_route_needs_a_session(self):
        c = self.new_client()
        for method, url in [("get", "/api/state"), ("get", "/api/score"), ("get", "/api/review"), ("get", "/api/me/avatar"),
                            ("get", "/api/account/export"), ("get", "/api/auth/me")]:
            self.assertEqual(getattr(c, method)(url).status_code, 401, url)
        for method, url in [("put", "/api/challenges/c1"), ("delete", "/api/challenges/c1"), ("put", "/api/profile"),
                            ("put", "/api/me/avatar"), ("delete", "/api/me/avatar"), ("delete", "/api/account"),
                            ("post", "/api/auth/change-password"), ("post", "/api/auth/logout-all")]:
            self.assertEqual(getattr(c, method)(url, json={}, headers=H).status_code, 401, url)

    def test_people_cannot_see_or_touch_each_others_data(self):
        a, b = self.user("a@example.com"), self.user("b@example.com")
        a.put("/api/challenges/same-id", json=challenge(name="A private goal"), headers=H)
        b.put("/api/challenges/same-id", json=challenge(name="B private goal"), headers=H)   # same id, no collision
        self.assertEqual([c["name"] for c in a.get("/api/state").get_json()["challenges"]], ["A private goal"])
        self.assertEqual([c["name"] for c in b.get("/api/state").get_json()["challenges"]], ["B private goal"])
        b.delete("/api/challenges/same-id", headers=H)
        self.assertEqual(len(a.get("/api/state").get_json()["challenges"]), 1)               # A unaffected
        self.assertNotIn("A private goal", b.get("/api/account/export").get_data(as_text=True))

    def test_scores_are_computed_from_your_data_only(self):
        a, b = self.user("a@example.com"), self.user("b@example.com")
        a.put("/api/challenges/c1", json=challenge(ticks={str(i): True for i in range(10)}), headers=H)
        self.assertGreater(a.get("/api/score?on=2026-11-12").get_json()["score"], 0)
        self.assertEqual(b.get("/api/score?on=2026-11-12").get_json()["score"], 0)

    def test_sql_injection_strings_are_inert(self):
        a = self.user("a@example.com")
        evil = "x'); DROP TABLE users;--"
        self.assertEqual(a.put("/api/challenges/c1", json=challenge(name=evil), headers=H).status_code, 200)
        self.assertEqual(a.put("/api/challenges/" + "1;DROP", json=challenge(), headers=H).status_code, 422)
        self.assertEqual(a.get("/api/state").get_json()["challenges"][0]["name"], evil)
        self.assertEqual(self.login(self.new_client(), email="a@example.com").status_code, 200)


class ValidationTests(AppCase):
    def setUp(self):
        super().setUp()
        self.me = self.user("v@example.com")

    def put(self, **over):
        return self.me.put("/api/challenges/c1", json=challenge(**over), headers=H).status_code

    def test_challenge_rules(self):
        self.assertEqual(self.put(), 200)
        for bad in [{"days": 0}, {"days": 731}, {"days": True}, {"days": 2.5}, {"name": ""}, {"name": "x" * 81}, {"name": 7},
                    {"start": "20261101"}, {"start": "2026-13-45"}, {"start": "tomorrow"}, {"created": -1}, {"created": True}]:
            self.assertEqual(self.put(**bad), 422, bad)

    def test_ticks_and_notes_must_sit_inside_the_challenge(self):
        self.assertEqual(self.put(days=21, ticks={"21": True}), 422)       # day 21 is outside a 21 day challenge
        self.assertEqual(self.put(days=21, notes={"99999": "x"}), 422)
        self.assertEqual(self.put(ticks={"x": True}), 422)
        self.assertEqual(self.put(ticks={"0": "yes"}), 422)
        self.assertEqual(self.put(notes={"0": "n" * 401}), 422)
        self.assertEqual(self.put(notes={"0": "n" * 400}), 200)

    def test_false_ticks_are_dropped_and_blank_notes_ignored(self):
        self.put(ticks={"0": True, "1": False}, notes={"0": "  ", "1": "kept"})
        c = self.me.get("/api/state").get_json()["challenges"][0]
        self.assertEqual((c["ticks"], c["notes"]), ({"0": True}, {"1": "kept"}))

    def test_per_user_challenge_cap_and_storage_cap(self):
        self.overrides = {"max_challenges": 3, "max_user_bytes": 2000}
        self.setUp()
        me = self.user("cap@example.com")
        codes = [me.put(f"/api/challenges/c{i}", json=challenge(), headers=H).status_code for i in range(4)]
        self.assertEqual(codes, [200, 200, 200, 409])
        self.assertEqual(me.put("/api/challenges/c0", json=challenge(name="renamed"), headers=H).status_code, 200)  # edits still fine
        big = {str(i): "n" * 400 for i in range(10)}
        self.assertEqual(me.put("/api/challenges/c1", json=challenge(notes=big), headers=H).status_code, 413)
        self.overrides = {}

    def test_profile_rules_and_export(self):
        ok = self.me.put("/api/profile", json={"name": "Ada", "intent": {"habit": "Walk", "when": "after coffee"}}, headers=H)
        self.assertEqual(ok.status_code, 200)
        self.assertEqual(self.me.put("/api/profile", json={"name": "n" * 5000}, headers=H).get_json() is not None, True)
        self.assertEqual(self.me.put("/api/profile", json={"intent": {"habit": "h" * 81}}, headers=H).status_code, 422)
        self.assertEqual(self.me.put("/api/profile", json={"intent": "nope"}, headers=H).status_code, 422)
        st = self.me.get("/api/state").get_json()
        self.assertEqual(len(st["profile"]["name"]), 30)  # long names are trimmed, not trusted
        doc = json.loads(self.me.get("/api/account/export").get_data())
        self.assertEqual(doc["account"]["email"], "v@example.com")
        self.assertNotIn("password", json.dumps(doc).lower())

    def test_json_body_rules(self):
        self.assertEqual(self.me.put("/api/challenges/c1", data="not json", headers=H).status_code, 400)
        self.assertEqual(self.me.put("/api/challenges/c1", json=[1, 2], headers=H).status_code, 400)
        self.assertEqual(self.me.put("/api/challenges/c1", json=challenge(notes={"0": "x" * 500_000}), headers=H).status_code, 413)

    def test_score_date_param_validated(self):
        self.assertEqual(self.me.get("/api/score?on=garbage").status_code, 422)


class SecurityTests(AppCase):
    def test_state_changing_requests_need_the_csrf_header(self):
        me = self.user("s@example.com")
        self.assertEqual(me.put("/api/challenges/c1", json=challenge()).status_code, 403)
        self.assertEqual(me.delete("/api/account", json={"password": GOOD_PW}).status_code, 403)
        self.assertEqual(self.new_client().post("/api/auth/login", json={"email": "s@example.com", "password": GOOD_PW}).status_code, 403)

    def test_foreign_origin_is_blocked_same_origin_allowed(self):
        me = self.user("s@example.com")
        evil = {**H, "Origin": "https://evil.example"}
        self.assertEqual(me.put("/api/challenges/c1", json=challenge(), headers=evil).status_code, 403)
        same = {**H, "Origin": "http://localhost"}
        self.assertEqual(me.put("/api/challenges/c1", json=challenge(), headers=same).status_code, 200)

    def test_security_headers_everywhere(self):
        for url in ["/", "/app.html", "/auth.html", "/api/health", "/js/app.js"]:
            r = self.client.get(url)
            directives = {d.split()[0]: d.split()[1:] for d in r.headers["Content-Security-Policy"].split(";") if d.strip()}
            self.assertEqual(directives["script-src"], ["'self'"], url)         # no inline or third-party scripts, ever
            self.assertEqual(directives["object-src"], ["'none'"], url)
            self.assertIn("frame-ancestors 'none'", r.headers["Content-Security-Policy"], url)
            self.assertEqual(r.headers["X-Content-Type-Options"], "nosniff", url)
            self.assertEqual(r.headers["X-Frame-Options"], "DENY", url)
        self.assertEqual(self.client.get("/api/health").headers["Cache-Control"], "no-store")

    def test_hsts_only_over_secure_deployments(self):
        self.overrides = {"secure_cookies": True}
        self.setUp()
        self.assertIn("max-age", self.client.get("/api/health").headers["Strict-Transport-Security"])
        self.overrides = {}

    def test_no_inline_scripts_so_the_strict_csp_holds(self):
        import glob
        import re
        for path in glob.glob("web/*.html"):
            html = open(path, encoding="utf-8").read()
            for m in re.finditer(r"<script\b([^>]*)>", html):
                attrs = m.group(1)
                self.assertTrue("src=" in attrs or "application/ld+json" in attrs, f"inline script in {path}")
            self.assertIsNone(re.search(r"\son[a-z]+=", html), f"inline handler in {path}")

    def test_static_server_blocks_traversal_dotfiles_and_api_shadowing(self):
        for url in ["/../server/main.py", "/..%2fserver%2fmain.py", "/%2e%2e/requirements.txt", "/.gitignore", "/js/../../README.md", "/api/nothing"]:
            self.assertEqual(self.client.get(url).status_code, 404, url)
        self.assertIn(self.client.get("/api/auth/register").status_code, (404, 405))

    def test_errors_are_json_and_do_not_leak_internals(self):
        r = self.client.get("/api/does-not-exist")
        self.assertEqual(r.get_json(), {"error": "The requested URL was not found on the server. If you entered the URL manually please check your spelling and try again."})
        self.assertNotIn("Traceback", r.get_data(as_text=True))

    def test_health_ready_robots_and_sitemap(self):
        self.assertEqual(self.client.get("/api/health").get_json()["status"], "ok")
        self.assertEqual(self.client.get("/api/ready").get_json()["status"], "ready")
        robots = self.client.get("/robots.txt").get_data(as_text=True)
        self.assertIn("Disallow: /app.html", robots)
        self.assertNotIn("auth.html", self.client.get("/sitemap.xml").get_data(as_text=True))
        self.assertEqual(self.client.get("/").status_code, 200)


class AvatarTests(AppCase):
    def up(self, client, data, name="me.png"):
        return client.put("/api/me/avatar", data={"file": (io.BytesIO(data), name)}, headers=H)

    def test_upload_resizes_to_256_square_webp_and_serves_it(self):
        from PIL import Image
        me = self.user("p@example.com")
        r = self.up(me, png((1200, 500)))
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.get_json()["avatar"]["has"])
        got = me.get("/api/me/avatar")
        img = Image.open(io.BytesIO(got.data))
        self.assertEqual((got.mimetype, img.format, img.size), ("image/webp", "WEBP", (256, 256)))
        self.assertLess(len(got.data), 40_000)
        st = me.get("/api/state").get_json()
        self.assertEqual(st["user"]["avatar"], st["profile"]["avatar"])
        self.assertTrue(st["user"]["avatar"]["has"])

    def test_etag_gives_304_and_headers_are_locked_down(self):
        me = self.user("p@example.com")
        self.up(me, png())
        first = me.get("/api/me/avatar")
        again = me.get("/api/me/avatar", headers={"If-None-Match": first.headers["ETag"]})
        self.assertEqual(again.status_code, 304)
        self.assertIn("sandbox", first.headers["Content-Security-Policy"])
        self.assertEqual(first.headers["Cache-Control"], "private, max-age=86400")

    def test_jpeg_gif_webp_accepted_other_things_refused(self):
        me = self.user("p@example.com")
        for fmt in ("JPEG", "GIF", "WEBP", "PNG"):
            self.assertEqual(self.up(me, png(fmt=fmt)).status_code, 200, fmt)
        for name, blob in [("a.png", b"just text pretending"), ("a.png", b"<script>alert(1)</script>"), ("a.svg", b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>'),
                           ("a.png", b""), ("a.png", b"\x89PNG\r\n\x1a\n" + b"\x00" * 50), ("a.bmp", png(fmt="BMP")), ("a.pdf", b"%PDF-1.4 fake")]:
            self.assertEqual(self.up(me, blob, name).status_code, 415, name)
        self.assertEqual(me.put("/api/me/avatar", data={}, headers=H).status_code, 422)

    def test_oversize_upload_is_rejected(self):
        me = self.user("p@example.com")
        self.assertEqual(self.up(me, b"\x89PNG" + b"0" * (2 * 1024 * 1024 + 10)).status_code, 413)
        self.assertEqual(self.up(me, b"0" * (4 * 1024 * 1024)).status_code, 413)  # over the hard request cap too

    def test_decompression_bomb_is_rejected_cheaply(self):
        from PIL import Image
        buf = io.BytesIO()
        Image.new("1", (30000, 30000)).save(buf, "PNG")     # 900 megapixels, tiny on disk
        self.assertLess(len(buf.getvalue()), 2 * 1024 * 1024)
        me = self.user("p@example.com")
        self.assertEqual(self.up(me, buf.getvalue()).status_code, 415)

    def test_exif_metadata_is_stripped_and_rotation_applied(self):
        from PIL import Image
        exif = Image.Exif()
        exif[0x010F] = "SecretCameraMaker"
        exif[0x0112] = 6  # rotate 90
        me = self.user("p@example.com")
        self.up(me, png((400, 200), fmt="JPEG", exif=exif.tobytes()), "photo.jpg")
        data = me.get("/api/me/avatar").data
        self.assertNotIn(b"SecretCameraMaker", data)
        self.assertEqual(len(Image.open(io.BytesIO(data)).getexif()), 0)

    def test_polyglot_file_is_flattened_to_pixels(self):
        me = self.user("p@example.com")
        self.assertEqual(self.up(me, png() + b"<script>alert(1)</script>").status_code, 200)
        self.assertNotIn(b"<script>", me.get("/api/me/avatar").data)

    def test_avatars_are_private_per_user_and_removable(self):
        a, b = self.user("a@example.com"), self.user("b@example.com")
        self.up(a, png())
        self.assertEqual(b.get("/api/me/avatar").status_code, 404)
        self.assertEqual(a.delete("/api/me/avatar", headers=H).get_json()["avatar"], {"has": False, "v": 0})
        self.assertEqual(a.get("/api/me/avatar").status_code, 404)

    def test_transparent_png_gets_a_solid_background(self):
        from PIL import Image
        buf = io.BytesIO()
        Image.new("RGBA", (50, 50), (0, 0, 0, 0)).save(buf, "PNG")
        me = self.user("p@example.com")
        self.assertEqual(self.up(me, buf.getvalue()).status_code, 200)
        self.assertEqual(Image.open(io.BytesIO(me.get("/api/me/avatar").data)).mode, "RGB")
