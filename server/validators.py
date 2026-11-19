"""Hand-written validation for request bodies. Nothing reaches the database unchecked."""
from __future__ import annotations

import re
from datetime import date

from .errors import ApiError
from .security import clean_name

ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,40}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
INTENT_KEYS = {"dest": 200, "who": 80, "habit": 80, "when": 100, "min": 100}


def bad(message: str):
    raise ApiError(422, message)


def challenge_id(cid: str) -> str:
    if not ID_RE.match(cid):
        bad("Invalid challenge id.")
    return cid


def challenge(body: dict) -> dict:
    name = body.get("name")
    if not isinstance(name, str) or not 1 <= len(name.strip()) <= 80:
        bad("Name must be 1 to 80 characters.")
    days = body.get("days")
    if isinstance(days, bool) or not isinstance(days, int) or not 1 <= days <= 730:
        bad("Days must be a whole number from 1 to 730.")
    start = body.get("start")
    if not isinstance(start, str) or not DATE_RE.match(start):
        bad("Start must be a date like 2026-11-18.")
    try:
        date.fromisoformat(start)
    except ValueError:
        bad("Start must be a real date.")
    created = body.get("created", 0)
    if isinstance(created, bool) or not isinstance(created, int) or not 0 <= created <= 4_102_444_800_000:
        bad("Invalid created time.")

    def day_map(field: str) -> dict:
        raw = body.get(field) or {}
        if not isinstance(raw, dict) or len(raw) > days:
            bad(f"Invalid {field}.")
        out = {}
        for k, v in raw.items():
            if not (isinstance(k, str) and k.isascii() and k.isdigit() and int(k) < days):
                bad(f"{field.capitalize()} must use day numbers inside the challenge.")
            out[str(int(k))] = v
        return out

    raw_ticks = day_map("ticks")
    if any(not isinstance(v, bool) for v in raw_ticks.values()):
        bad("Ticks must be true or false.")
    ticks = {k: True for k, v in raw_ticks.items() if v}
    notes = day_map("notes")
    for text in notes.values():
        if not isinstance(text, str) or len(text) > 400:
            bad("A note can be at most 400 characters.")
    notes = {k: v for k, v in notes.items() if v.strip()}
    return {"name": name.strip(), "days": days, "start": start, "created": created, "ticks": ticks, "notes": notes}


def profile(body: dict) -> dict:
    out: dict = {}
    if "name" in body:
        if not isinstance(body["name"], str):
            bad("Name must be text.")
        out["name"] = clean_name(body["name"])
    if "intent" in body:
        raw = body["intent"]
        if not isinstance(raw, dict):
            bad("Intent must be an object.")
        intent = {}
        for key, limit in INTENT_KEYS.items():
            val = raw.get(key, "")
            if not isinstance(val, str) or len(val) > limit:
                bad(f"{key} must be text up to {limit} characters.")
            intent[key] = val.strip()
        out["intent"] = intent
    return out
