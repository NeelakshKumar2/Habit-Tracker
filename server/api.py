"""Everything a signed-in person can do with their own data."""
from __future__ import annotations

import json
import time

from flask import Blueprint, Response, current_app, g, jsonify, request

from . import scoring, validators
from .auth import cfg, login_required, user_payload
from .avatar import AvatarError, process_avatar
from .db import get_db, tx
from .errors import ApiError, json_body
from .review import weekly_review

bp = Blueprint("api", __name__, url_prefix="/api")


def _challenges(db, uid: int) -> list[dict]:
    rows = db.execute("SELECT id, data FROM challenges WHERE user_id=? ORDER BY created DESC, id", (uid,)).fetchall()
    return [{"id": r["id"], **json.loads(r["data"])} for r in rows]


def _profile(db, uid: int) -> dict:
    row = db.execute("SELECT data FROM profiles WHERE user_id=?", (uid,)).fetchone()
    return json.loads(row["data"]) if row else {"intent": {}}


@bp.get("/health")
def health():
    return jsonify(app="grit", status="ok")


@bp.get("/ready")
def ready():
    try:
        get_db().execute("SELECT 1").fetchone()
    except Exception:
        return jsonify(status="unavailable"), 503
    return jsonify(status="ready")


@bp.get("/state")
@login_required
def state():
    db, u = get_db(), g.user
    payload = user_payload(db, u)
    return jsonify(user=payload, challenges=_challenges(db, u["id"]),
                   profile={"name": u["display_name"], "intent": _profile(db, u["id"]).get("intent", {}), "avatar": payload["avatar"]})


@bp.put("/challenges/<cid>")
@login_required
def put_challenge(cid: str):
    validators.challenge_id(cid)
    data = validators.challenge(json_body(400_000))
    blob, db, uid, c = json.dumps(data, separators=(",", ":")), get_db(), g.user["id"], cfg()
    with tx(db):
        count, used = db.execute("SELECT COUNT(*), COALESCE(SUM(LENGTH(data)),0) FROM challenges WHERE user_id=? AND id<>?", (uid, cid)).fetchone()
        exists = db.execute("SELECT 1 FROM challenges WHERE user_id=? AND id=?", (uid, cid)).fetchone()
        if not exists and count >= c.max_challenges:
            raise ApiError(409, f"You can keep up to {c.max_challenges} challenges. Delete one to add another.")
        if used + len(blob) > c.max_user_bytes:
            raise ApiError(413, "Your account has reached its storage limit. Delete old challenges to free space.")
        db.execute("INSERT INTO challenges (user_id, id, data, created) VALUES (?,?,?,?) "
                   "ON CONFLICT(user_id, id) DO UPDATE SET data=excluded.data, created=excluded.created",
                   (uid, cid, blob, data["created"]))
    return jsonify(id=cid)


@bp.delete("/challenges/<cid>")
@login_required
def delete_challenge(cid: str):
    get_db().execute("DELETE FROM challenges WHERE user_id=? AND id=?", (g.user["id"], validators.challenge_id(cid)))
    return Response(status=204)


@bp.put("/profile")
@login_required
def put_profile():
    patch, db, uid = validators.profile(json_body()), get_db(), g.user["id"]
    with tx(db):
        if "name" in patch:
            db.execute("UPDATE users SET display_name=? WHERE id=?", (patch["name"], uid))
        if "intent" in patch:
            db.execute("UPDATE profiles SET data=? WHERE user_id=?", (json.dumps({"intent": patch["intent"]}), uid))
    return jsonify(ok=True)


# ---- profile picture ----
@bp.put("/me/avatar")
@login_required
def put_avatar():
    upload = request.files.get("file")
    if upload is None:
        raise ApiError(422, "Choose an image to upload.")
    raw = upload.stream.read(cfg().avatar_max_bytes + 1)
    if len(raw) > cfg().avatar_max_bytes:
        raise ApiError(413, "That image is over 2 MB. Choose a smaller one.")
    try:
        webp = process_avatar(raw)
    except AvatarError as e:
        raise ApiError(415, str(e))
    now = int(time.time() * 1000)
    get_db().execute("INSERT INTO avatars (user_id, mime, data, updated_at) VALUES (?,?,?,?) "
                     "ON CONFLICT(user_id) DO UPDATE SET mime=excluded.mime, data=excluded.data, updated_at=excluded.updated_at",
                     (g.user["id"], "image/webp", webp, now))
    return jsonify(avatar={"has": True, "v": now})


@bp.delete("/me/avatar")
@login_required
def delete_avatar():
    get_db().execute("DELETE FROM avatars WHERE user_id=?", (g.user["id"],))
    return jsonify(avatar={"has": False, "v": 0})


@bp.get("/me/avatar")
@login_required
def get_avatar():
    row = get_db().execute("SELECT mime, data, updated_at FROM avatars WHERE user_id=?", (g.user["id"],)).fetchone()
    if not row:
        raise ApiError(404, "No profile picture.")
    etag = f'"{row["updated_at"]}"'
    if request.headers.get("If-None-Match") == etag:
        return Response(status=304, headers={"ETag": etag})
    return Response(row["data"], mimetype=row["mime"], headers={
        "ETag": etag, "Cache-Control": "private, max-age=86400", "Vary": "Cookie",
        "Content-Security-Policy": "default-src 'none'; sandbox", "Content-Disposition": "inline; filename=avatar.webp"})


# ---- insights ----
@bp.get("/score")
@login_required
def score():
    on = request.args.get("on")
    try:
        from datetime import date
        day = date.fromisoformat(on) if on else None
    except ValueError:
        raise ApiError(422, "on must be a date like 2026-11-18.")
    return jsonify(scoring.analyze(_challenges(get_db(), g.user["id"]), day))


@bp.get("/review")
@login_required
def review():
    db, uid = get_db(), g.user["id"]
    return jsonify(weekly_review(scoring.analyze(_challenges(db, uid)), _profile(db, uid).get("intent")))


@bp.get("/account/export")
@login_required
def export():
    db, u = get_db(), g.user
    doc = {"app": "grit", "version": 2, "exported": int(time.time()), "account": {"email": u["email"], "name": u["display_name"], "created_at": u["created_at"]},
           "profile": {"name": u["display_name"], "intent": _profile(db, u["id"]).get("intent", {})}, "challenges": _challenges(db, u["id"])}
    return Response(json.dumps(doc, indent=2), mimetype="application/json",
                    headers={"Content-Disposition": "attachment; filename=grit-export.json"})
