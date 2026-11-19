"""Accounts: register, sign in, sign out, change password and delete account."""
from __future__ import annotations

import json
import random
import time

from flask import Blueprint, current_app, g, jsonify, request

from . import security as sec
from .db import get_db, tx
from .errors import ApiError, json_body

bp = Blueprint("auth", __name__)


def cfg():
    return current_app.extensions["grit"]


def cookie_name() -> str:
    return "__Host-grit_session" if cfg().secure_cookies else "grit_session"


def client_ip() -> str:
    return request.remote_addr or "unknown"


def _set_cookie(resp, token: str) -> None:
    resp.set_cookie(cookie_name(), token, max_age=cfg().session_days * 86400, httponly=True,
                    secure=cfg().secure_cookies, samesite="Lax", path="/")


def _clear_cookie(resp) -> None:
    resp.delete_cookie(cookie_name(), path="/", httponly=True, secure=cfg().secure_cookies, samesite="Lax")


def create_session(db, user_id: int) -> str:
    token, now = sec.new_token(), int(time.time())
    db.execute("DELETE FROM sessions WHERE expires_at < ?", (now,))
    db.execute(
        "INSERT INTO sessions (token_hash, user_id, created_at, expires_at, last_seen, user_agent) VALUES (?,?,?,?,?,?)",
        (sec.hash_token(token), user_id, now, now + cfg().session_days * 86400, now, request.headers.get("User-Agent", "")[:200]),
    )
    return token


def load_user():
    """The signed-in user for this request, or None. Sessions slide: active people stay signed in."""
    if "user" in g:
        return g.user
    g.user, g.session_hash, g.renew_token = None, None, None
    token = request.cookies.get(cookie_name())
    if token and len(token) < 200:
        db, now, h = get_db(), int(time.time()), sec.hash_token(token)
        row = db.execute(
            "SELECT u.id, u.email, u.display_name, u.created_at, s.expires_at, s.last_seen FROM sessions s "
            "JOIN users u ON u.id = s.user_id WHERE s.token_hash = ? AND s.expires_at > ?", (h, now)).fetchone()
        if row:
            g.user, g.session_hash = dict(row), h
            life = cfg().session_days * 86400
            if row["expires_at"] - now < life // 2:
                db.execute("UPDATE sessions SET expires_at=?, last_seen=? WHERE token_hash=?", (now + life, now, h))
                g.renew_token = token
            elif now - row["last_seen"] > 300:
                db.execute("UPDATE sessions SET last_seen=? WHERE token_hash=?", (now, h))
    return g.user


def login_required(view):
    from functools import wraps

    @wraps(view)
    def wrapper(*a, **kw):
        if not load_user():
            raise ApiError(401, "Please sign in.")
        return view(*a, **kw)
    return wrapper


@bp.after_app_request
def _renew_cookie(resp):
    token = g.get("renew_token")
    if token:
        _set_cookie(resp, token)
    return resp


def user_payload(db, user: dict) -> dict:
    row = db.execute("SELECT updated_at FROM avatars WHERE user_id=?", (user["id"],)).fetchone()
    return {"email": user["email"], "name": user["display_name"], "created_at": user["created_at"],
            "avatar": {"has": bool(row), "v": row["updated_at"] if row else 0}}


# ---- throttling (stored in the database so it holds across workers) ----
def _count(db, kind: str, key: str, window: int) -> int:
    return db.execute("SELECT COUNT(*) FROM auth_attempts WHERE kind=? AND key=? AND at>?",
                      (kind, key, int(time.time()) - window)).fetchone()[0]


def _record(db, kind: str, key: str) -> None:
    db.execute("INSERT INTO auth_attempts (kind, key, at) VALUES (?,?,?)", (kind, key, int(time.time())))
    if random.random() < 0.02:
        db.execute("DELETE FROM auth_attempts WHERE at < ?", (int(time.time()) - 86400,))


def _too_many():
    return ApiError(429, "Too many attempts. Wait a few minutes and try again.", {"Retry-After": str(cfg().throttle_window_s)})


def check_login_throttle(db, email: str) -> None:
    c, w, ip = cfg(), cfg().throttle_window_s, client_ip()
    if (_count(db, "login_pair", f"{ip}|{email}", w) >= c.login_pair_limit
            or _count(db, "login_email", email, w) >= c.login_email_limit
            or _count(db, "login_ip", ip, w) >= c.login_ip_limit):
        raise _too_many()


def record_login_failure(db, email: str) -> None:
    ip = client_ip()
    _record(db, "login_pair", f"{ip}|{email}")
    _record(db, "login_email", email)
    _record(db, "login_ip", ip)


def clear_login_failures(db, email: str) -> None:
    db.execute("DELETE FROM auth_attempts WHERE (kind='login_pair' AND key=?) OR (kind='login_email' AND key=?)",
               (f"{client_ip()}|{email}", email))


_dummy: dict = {}


def _dummy_hash() -> str:
    c = cfg()
    key = (c.scrypt_n, c.scrypt_r, c.scrypt_p)
    if key not in _dummy:
        _dummy[key] = sec.hash_password("not-a-real-password", *key)
    return _dummy[key]


def _check_password(db, user_id: int, email: str, password) -> bool:
    row = db.execute("SELECT password_hash FROM users WHERE id=?", (user_id,)).fetchone()
    return bool(row) and isinstance(password, str) and sec.verify_password(row["password_hash"], password)


# ---- routes ----
@bp.post("/api/auth/register")
def register():
    body, db, c = json_body(), get_db(), cfg()
    email = sec.normalize_email(body.get("email"))
    password = body.get("password")
    err = sec.email_error(email) or sec.password_error(password, email)
    if err:
        raise ApiError(422, err)
    if _count(db, "register", client_ip(), c.register_window_s) >= c.register_ip_limit:
        raise _too_many()
    _record(db, "register", client_ip())
    name = sec.clean_name(body.get("name", ""))
    pw_hash = sec.hash_password(password, c.scrypt_n, c.scrypt_r, c.scrypt_p)  # slow work stays outside the write lock
    now = int(time.time())
    with tx(db):
        if db.execute("SELECT 1 FROM users WHERE email=?", (email,)).fetchone():
            raise ApiError(409, "An account with this email already exists. Try signing in.")
        uid = db.execute("INSERT INTO users (email, password_hash, display_name, created_at, pw_changed_at) VALUES (?,?,?,?,?)",
                         (email, pw_hash, name, now, now)).lastrowid
        db.execute("INSERT INTO profiles (user_id, data) VALUES (?,?)", (uid, json.dumps({"intent": {}})))
        token = create_session(db, uid)
    current_app.logger.info("auth.register user=%s", uid)
    resp = jsonify(ok=True)
    resp.status_code = 201
    _set_cookie(resp, token)
    return resp


@bp.post("/api/auth/login")
def login():
    body, db, c = json_body(), get_db(), cfg()
    email, password = sec.normalize_email(body.get("email")), body.get("password")
    check_login_throttle(db, email)
    row = db.execute("SELECT id, password_hash FROM users WHERE email=?", (email,)).fetchone()
    ok = sec.verify_password(row["password_hash"] if row else _dummy_hash(), password if isinstance(password, str) else "")
    if not (row and ok):
        record_login_failure(db, email)
        current_app.logger.info("auth.login_failed ip=%s", client_ip())
        raise ApiError(401, "Email or password is incorrect.")
    clear_login_failures(db, email)
    if sec.needs_rehash(row["password_hash"], c.scrypt_n, c.scrypt_r, c.scrypt_p):
        db.execute("UPDATE users SET password_hash=? WHERE id=?", (sec.hash_password(password, c.scrypt_n, c.scrypt_r, c.scrypt_p), row["id"]))
    token = create_session(db, row["id"])
    current_app.logger.info("auth.login user=%s", row["id"])
    resp = jsonify(ok=True)
    _set_cookie(resp, token)
    return resp


@bp.post("/api/auth/logout")
def logout():
    if load_user():
        get_db().execute("DELETE FROM sessions WHERE token_hash=?", (g.session_hash,))
    g.renew_token = None
    resp = jsonify(ok=True)
    _clear_cookie(resp)
    return resp


@bp.post("/api/auth/logout-all")
@login_required
def logout_all():
    get_db().execute("DELETE FROM sessions WHERE user_id=?", (g.user["id"],))
    g.renew_token = None
    resp = jsonify(ok=True)
    _clear_cookie(resp)
    return resp


@bp.get("/api/auth/me")
@login_required
def me():
    return jsonify(user=user_payload(get_db(), g.user))


@bp.post("/api/auth/change-password")
@login_required
def change_password():
    body, db, c = json_body(), get_db(), cfg()
    u = g.user
    check_login_throttle(db, u["email"])
    if not _check_password(db, u["id"], u["email"], body.get("current")):
        record_login_failure(db, u["email"])
        raise ApiError(403, "Your current password is incorrect.")
    err = sec.password_error(body.get("new"), u["email"])
    if err:
        raise ApiError(422, err)
    new_hash = sec.hash_password(body["new"], c.scrypt_n, c.scrypt_r, c.scrypt_p)
    with tx(db):
        db.execute("UPDATE users SET password_hash=?, pw_changed_at=? WHERE id=?", (new_hash, int(time.time()), u["id"]))
        db.execute("DELETE FROM sessions WHERE user_id=? AND token_hash<>?", (u["id"], g.session_hash))
    current_app.logger.info("auth.password_changed user=%s", u["id"])
    return jsonify(ok=True)


@bp.delete("/api/account")
@login_required
def delete_account():
    """Permanent. Needs the password, and everything the person owns is removed in one transaction."""
    body, db = json_body(), get_db()
    u = g.user
    check_login_throttle(db, u["email"])
    if not _check_password(db, u["id"], u["email"], body.get("password")):
        record_login_failure(db, u["email"])
        raise ApiError(403, "Password is incorrect.")
    with tx(db):
        db.execute("DELETE FROM users WHERE id=?", (u["id"],))  # cascades to sessions, challenges, profile, avatar
        db.execute("DELETE FROM auth_attempts WHERE key=? OR key LIKE ?", (u["email"], f"%|{u['email']}"))
    db.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    current_app.logger.info("auth.account_deleted user=%s", u["id"])
    g.renew_token = None
    resp = jsonify(ok=True)
    _clear_cookie(resp)
    return resp


# ---- forgotten password ----
GENERIC_FORGOT = "If an account exists for that email, a reset link is on its way. It works for one hour."


def _reset_base() -> str | None:
    """Links are built from GRIT_PUBLIC_URL, never from the Host header, which an attacker controls."""
    c = cfg()
    return c.public_url or (request.host_url.rstrip("/") if c.env != "production" else None)


@bp.post("/api/auth/forgot")
def forgot_password():
    body, db, c = json_body(), get_db(), cfg()
    email = sec.normalize_email(body.get("email"))
    if sec.email_error(email):
        raise ApiError(422, "Enter a valid email address.")
    if _count(db, "forgot_ip", client_ip(), c.register_window_s) >= 20 or _count(db, "forgot_email", email, c.register_window_s) >= 3:
        raise _too_many()
    _record(db, "forgot_ip", client_ip())
    _record(db, "forgot_email", email)
    row = db.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()
    base = _reset_base()
    if row and base:
        token, now = sec.new_token(), int(time.time())
        with tx(db):
            db.execute("DELETE FROM password_resets WHERE user_id=? OR expires_at<?", (row["id"], now))
            db.execute("INSERT INTO password_resets (token_hash, user_id, expires_at) VALUES (?,?,?)",
                       (sec.hash_token(token), row["id"], now + c.reset_minutes * 60))
        current_app.extensions["grit_mail"](
            email, "Reset your Habit Tracker password",
            f"Someone asked to reset the password for your Habit Tracker account.\n\nChoose a new one here (valid for {c.reset_minutes} minutes):\n"
            f"{base}/auth.html#reset={token}\n\nIf this was not you, ignore this email. Your password has not changed.")
    elif row:
        current_app.logger.error("password reset requested but GRIT_PUBLIC_URL is not set; no email sent")
    return jsonify(ok=True, message=GENERIC_FORGOT)


@bp.post("/api/auth/reset")
def reset_password():
    body, db, c = json_body(), get_db(), cfg()
    if _count(db, "reset_ip", client_ip(), c.throttle_window_s) >= 20:
        raise _too_many()
    token = body.get("token")
    row = None
    if isinstance(token, str) and 20 <= len(token) <= 100:
        row = db.execute("SELECT r.user_id, u.email FROM password_resets r JOIN users u ON u.id=r.user_id "
                         "WHERE r.token_hash=? AND r.expires_at>?", (sec.hash_token(token), int(time.time()))).fetchone()
    if not row:
        _record(db, "reset_ip", client_ip())
        raise ApiError(400, "This reset link is invalid or has expired. Request a new one.")
    err = sec.password_error(body.get("new"), row["email"])
    if err:
        raise ApiError(422, err)  # the link stays valid so they can try again
    new_hash = sec.hash_password(body["new"], c.scrypt_n, c.scrypt_r, c.scrypt_p)
    with tx(db):
        if not db.execute("DELETE FROM password_resets WHERE token_hash=?", (sec.hash_token(token),)).rowcount:
            raise ApiError(400, "This reset link is invalid or has expired. Request a new one.")  # lost a race: single use
        db.execute("UPDATE users SET password_hash=?, pw_changed_at=? WHERE id=?", (new_hash, int(time.time()), row["user_id"]))
        db.execute("DELETE FROM sessions WHERE user_id=?", (row["user_id"],))
        db.execute("DELETE FROM password_resets WHERE user_id=?", (row["user_id"],))
        db.execute("DELETE FROM auth_attempts WHERE (kind='login_email' AND key=?) OR (kind='login_pair' AND key LIKE ?)", (row["email"], f"%|{row['email']}"))
    current_app.logger.info("auth.password_reset user=%s", row["user_id"])
    return jsonify(ok=True)
