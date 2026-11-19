import sqlite3
import time

from tests.helpers import GOOD_PW, H, AppCase, challenge


class RegisterTests(AppCase):
    def test_register_signs_you_in_with_a_hardened_cookie(self):
        r = self.register()
        self.assertEqual(r.status_code, 201)
        cookie = r.headers["Set-Cookie"]
        self.assertIn("HttpOnly", cookie)
        self.assertIn("SameSite=Lax", cookie)
        self.assertEqual(self.client.get("/api/auth/me").get_json()["user"]["email"], "ada@example.com")

    def test_secure_cookie_prefix_in_production_mode(self):
        self.overrides = {"secure_cookies": True}
        self.setUp()
        c = self.app.test_client()
        cookie = self.register(c).headers["Set-Cookie"]
        self.assertTrue(cookie.startswith("__Host-grit_session="))
        self.assertIn("Secure", cookie)
        self.overrides = {}

    def test_email_is_case_insensitive_and_unique(self):
        self.register(email="Ada@Example.com")
        r = self.register(self.new_client(), email="ada@example.COM")
        self.assertEqual(r.status_code, 409)

    def test_bad_email_and_weak_passwords_are_rejected(self):
        for email, pw in [("nope", GOOD_PW), ("a@b", GOOD_PW), ("a@b.co", "short"), ("a@b.co", "password123"),
                          ("a@b.co", "aaaaaaaaaaaa"), ("a@b.co", "x" * 129), ("a@b.co", None), ("a@b.co", 12345678901234)]:
            self.assertEqual(self.register(self.new_client(), email=email, password=pw).status_code, 422, (email, pw))

    def test_password_equal_to_email_is_rejected(self):
        self.assertEqual(self.register(email="verylongname@example.com", password="verylongname@example.com").status_code, 422)

    def test_passwords_are_scrypt_hashed_and_salted(self):
        self.register(email="a@example.com")
        self.register(self.new_client(), email="b@example.com")
        rows = sqlite3.connect(self.db_path).execute("SELECT password_hash FROM users ORDER BY id").fetchall()
        self.assertTrue(all(r[0].startswith("scrypt$") and GOOD_PW not in r[0] for r in rows))
        self.assertNotEqual(rows[0][0], rows[1][0])  # same password, different salt

    def test_registration_is_rate_limited_per_ip(self):
        self.overrides = {"register_ip_limit": 3}
        self.setUp()
        codes = [self.register(self.new_client(), email=f"u{i}@example.com").status_code for i in range(5)]
        self.assertEqual(codes, [201, 201, 201, 429, 429])
        self.overrides = {}


class LoginTests(AppCase):
    def setUp(self):
        super().setUp()
        self.register()
        self.fresh = self.new_client()

    def test_login_works_and_wrong_credentials_get_one_generic_message(self):
        self.assertEqual(self.login(self.fresh).status_code, 200)
        wrong_pw = self.login(self.new_client(), password="not the password")
        no_user = self.login(self.new_client(), email="ghost@example.com")
        self.assertEqual((wrong_pw.status_code, no_user.status_code), (401, 401))
        self.assertEqual(wrong_pw.get_json(), no_user.get_json())  # no hint about which emails exist

    def test_five_failures_lock_that_client_then_throttle_returns_429(self):
        c = self.new_client()
        codes = [self.login(c, password=f"wrong password {i}").status_code for i in range(7)]
        self.assertEqual(codes, [401] * 5 + [429, 429])
        self.assertEqual(self.login(c).status_code, 429)  # even the right password is held back while locked
        self.assertIn("Retry-After", self.login(c).headers)

    def test_success_clears_the_failure_count(self):
        c = self.new_client()
        for i in range(3):
            self.login(c, password=f"wrong password {i}")
        self.assertEqual(self.login(c).status_code, 200)
        for i in range(4):
            self.assertEqual(self.login(c, password=f"wrong again {i}").status_code, 401)

    def test_session_tokens_are_stored_only_as_hashes(self):
        self.login(self.fresh)
        token = self.fresh.get_cookie("grit_session").value
        raw = sqlite3.connect(self.db_path).execute("SELECT token_hash FROM sessions").fetchall()
        self.assertTrue(raw and all(token not in r[0] and len(r[0]) == 64 for r in raw))

    def test_logout_kills_the_session_server_side(self):
        self.login(self.fresh)
        token = self.fresh.get_cookie("grit_session").value
        self.assertEqual(self.fresh.post("/api/auth/logout", headers=H).status_code, 200)
        replay = self.new_client()
        replay.set_cookie("grit_session", token)
        self.assertEqual(replay.get("/api/auth/me").status_code, 401)

    def test_expired_sessions_are_refused(self):
        self.login(self.fresh)
        db = sqlite3.connect(self.db_path)
        db.execute("UPDATE sessions SET expires_at=?", (int(time.time()) - 1,))
        db.commit()
        self.assertEqual(self.fresh.get("/api/auth/me").status_code, 401)

    def test_forged_or_junk_cookies_are_refused(self):
        for junk in ["", "abc", "x" * 500, "' OR 1=1 --"]:
            c = self.new_client()
            c.set_cookie("grit_session", junk)
            self.assertEqual(c.get("/api/state").status_code, 401)

    def test_logout_everywhere_signs_out_other_devices(self):
        phone = self.new_client()
        self.login(phone)
        self.login(self.fresh)
        self.assertEqual(self.fresh.post("/api/auth/logout-all", headers=H).status_code, 200)
        self.assertEqual(phone.get("/api/auth/me").status_code, 401)

    def test_change_password_needs_current_one_and_revokes_other_sessions(self):
        phone = self.new_client()
        self.login(phone)
        self.login(self.fresh)
        bad = self.fresh.post("/api/auth/change-password", json={"current": "nope nope nope", "new": "a brand new phrase"}, headers=H)
        self.assertEqual(bad.status_code, 403)
        weak = self.fresh.post("/api/auth/change-password", json={"current": GOOD_PW, "new": "short"}, headers=H)
        self.assertEqual(weak.status_code, 422)
        ok = self.fresh.post("/api/auth/change-password", json={"current": GOOD_PW, "new": "a brand new phrase"}, headers=H)
        self.assertEqual(ok.status_code, 200)
        self.assertEqual(self.fresh.get("/api/auth/me").status_code, 200)   # this device stays in
        self.assertEqual(phone.get("/api/auth/me").status_code, 401)        # others are out
        self.assertEqual(self.login(self.new_client()).status_code, 401)   # old password is dead
        self.assertEqual(self.login(self.new_client(), password="a brand new phrase").status_code, 200)

    def test_old_cheap_hashes_are_upgraded_on_login(self):
        self.overrides = {"scrypt_n": 2 ** 11}
        self.setUp()
        self.register()
        self.app.extensions["grit"] = self.app.extensions["grit"].__class__(**{**self.app.extensions["grit"].__dict__, "scrypt_n": 2 ** 12})
        self.assertEqual(self.login(self.new_client()).status_code, 200)
        stored = sqlite3.connect(self.db_path).execute("SELECT password_hash FROM users").fetchone()[0]
        self.assertTrue(stored.startswith(f"scrypt${2 ** 12}$"))
        self.overrides = {}


class DeleteAccountTests(AppCase):
    def test_delete_needs_the_password(self):
        self.register()
        self.assertEqual(self.client.delete("/api/account", json={"password": "wrong wrong wrong"}, headers=H).status_code, 403)
        self.assertEqual(self.client.delete("/api/account", json={}, headers=H).status_code, 403)
        self.assertEqual(self.client.get("/api/auth/me").status_code, 200)

    def test_delete_removes_every_trace_and_leaves_others_alone(self):
        from tests.helpers import png
        other = self.user("bob@example.com")
        other.put("/api/challenges/x1", json=challenge(name="Bob keeps this"), headers=H)
        self.register()
        self.client.put("/api/challenges/c1", json=challenge(notes={"0": "ZZUNIQUEMARKERZZ"}), headers=H)
        self.client.put("/api/me/avatar", data={"file": (__import__("io").BytesIO(png()), "me.png")}, headers=H)
        probe = sqlite3.connect(self.db_path)
        uid = probe.execute("SELECT id FROM users WHERE email='ada@example.com'").fetchone()[0]
        probe.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        probe.close()
        with open(self.db_path, "rb") as f:   # control: the marker really is in the file before deletion
            self.assertIn(b"ZZUNIQUEMARKERZZ", f.read())
        self.assertEqual(self.client.delete("/api/account", json={"password": GOOD_PW}, headers=H).status_code, 200)
        db = sqlite3.connect(self.db_path)
        for table in ("challenges", "profiles", "avatars", "sessions"):
            self.assertEqual(db.execute(f"SELECT COUNT(*) FROM {table} WHERE user_id=?", (uid,)).fetchone()[0], 0, table)
        self.assertIsNone(db.execute("SELECT 1 FROM users WHERE email='ada@example.com'").fetchone())
        self.assertEqual(self.client.get("/api/state").status_code, 401)           # session gone
        self.assertEqual(self.login(self.new_client()).status_code, 401)           # cannot sign back in
        self.assertEqual(other.get("/api/state").get_json()["challenges"][0]["name"], "Bob keeps this")
        db.close()
        with open(self.db_path, "rb") as f:                                         # not even recoverable from the file
            self.assertNotIn(b"ZZUNIQUEMARKERZZ", f.read())

    def test_email_can_be_registered_again_after_deletion(self):
        self.register()
        self.client.delete("/api/account", json={"password": GOOD_PW}, headers=H)
        self.assertEqual(self.register(self.new_client()).status_code, 201)


class ResetTests(AppCase):
    overrides = {"public_url": "https://habits.example.com"}

    def setUp(self):
        super().setUp()
        self.mails = []
        self.app.extensions["grit_mail"] = lambda to, subject, body: self.mails.append((to, subject, body))
        self.register()

    def token(self):
        import re
        return re.search(r"#reset=([\w-]+)", self.mails[-1][2]).group(1)

    def forgot(self, email="ada@example.com", client=None):
        return (client or self.new_client()).post("/api/auth/forgot", json={"email": email}, headers=H)

    def test_known_and_unknown_emails_get_the_same_answer_but_only_known_gets_mail(self):
        a, b = self.forgot(), self.forgot("ghost@example.com")
        self.assertEqual((a.status_code, a.get_json()), (b.status_code, b.get_json()))
        self.assertEqual([m[0] for m in self.mails], ["ada@example.com"])

    def test_link_uses_the_configured_public_url_not_the_host_header(self):
        self.new_client().post("/api/auth/forgot", json={"email": "ada@example.com"}, headers={**H, "Host": "evil.example"})
        self.assertIn("https://habits.example.com/auth.html#reset=", self.mails[-1][2])
        self.assertNotIn("evil.example", self.mails[-1][2])

    def test_no_public_url_in_production_means_no_email_not_a_poisoned_one(self):
        self.overrides = {"public_url": "", "env": "production"}
        self.setUp()
        self.mails = []
        self.app.extensions["grit_mail"] = lambda *a: self.mails.append(a)
        self.register()
        self.assertEqual(self.forgot().status_code, 200)
        self.assertEqual(self.mails, [])
        self.overrides = {"public_url": "https://habits.example.com"}

    def test_token_is_stored_hashed_and_expires(self):
        self.forgot()
        token = self.token()
        db = sqlite3.connect(self.db_path)
        stored = db.execute("SELECT token_hash FROM password_resets").fetchone()[0]
        self.assertNotIn(token, stored)
        db.execute("UPDATE password_resets SET expires_at=?", (int(time.time()) - 1,))
        db.commit()
        r = self.new_client().post("/api/auth/reset", json={"token": token, "new": "a brand new phrase"}, headers=H)
        self.assertEqual(r.status_code, 400)

    def test_reset_sets_password_ends_all_sessions_and_is_single_use(self):
        phone = self.new_client()
        self.login(phone)
        self.forgot()
        token = self.token()
        weak = self.new_client().post("/api/auth/reset", json={"token": token, "new": "short"}, headers=H)
        self.assertEqual(weak.status_code, 422)                       # link survives a weak attempt
        ok = self.new_client().post("/api/auth/reset", json={"token": token, "new": "a brand new phrase"}, headers=H)
        self.assertEqual(ok.status_code, 200)
        self.assertEqual(phone.get("/api/auth/me").status_code, 401)
        self.assertEqual(self.login(self.new_client()).status_code, 401)
        self.assertEqual(self.login(self.new_client(), password="a brand new phrase").status_code, 200)
        again = self.new_client().post("/api/auth/reset", json={"token": token, "new": "yet another phrase"}, headers=H)
        self.assertEqual(again.status_code, 400)

    def test_junk_tokens_are_refused_and_throttled(self):
        c = self.new_client()
        codes = [c.post("/api/auth/reset", json={"token": "x" * 30 + str(i), "new": "a brand new phrase"}, headers=H).status_code for i in range(22)]
        self.assertEqual(codes[:20], [400] * 20)
        self.assertEqual(codes[20:], [429, 429])

    def test_non_string_tokens_are_refused(self):
        self.assertEqual(self.new_client().post("/api/auth/reset", json={"token": 5, "new": "a brand new phrase"}, headers=H).status_code, 400)

    def test_forgot_is_rate_limited_per_email(self):
        codes = [self.forgot(client=self.new_client()).status_code for _ in range(5)]
        self.assertEqual(codes, [200, 200, 200, 429, 429])
        self.assertEqual(len(self.mails), 3)

    def test_new_request_invalidates_the_older_link(self):
        self.forgot()
        first = self.token()
        self.forgot()
        self.assertEqual(self.new_client().post("/api/auth/reset", json={"token": first, "new": "a brand new phrase"}, headers=H).status_code, 400)
        self.assertEqual(self.new_client().post("/api/auth/reset", json={"token": self.token(), "new": "a brand new phrase"}, headers=H).status_code, 200)

    def test_deleting_the_account_removes_pending_reset_links(self):
        self.forgot()
        self.client.delete("/api/account", json={"password": GOOD_PW}, headers=H)
        self.assertEqual(sqlite3.connect(self.db_path).execute("SELECT COUNT(*) FROM password_resets").fetchone()[0], 0)
