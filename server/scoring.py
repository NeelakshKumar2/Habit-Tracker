"""Grit score engine. Pure functions, no I/O, easy to test.

The browser app (web/js/core/domain.js) uses the same formula so the score is
identical online and offline. Keep the two in step if you change either.

Score (0 to 1000):
  points = 3 per day kept
         + 1.5 per day of every finished challenge
         + 2 per day of the longest streak
         + 2 per written note
  score  = 1000 * (1 - exp(-points * consistency * recency / 1200))
  consistency = 0.5 + 0.5 * (days kept / days that have passed)
  recency     = 1 - min(0.15, 0.01 * max(0, idle days - 7))
"""
from __future__ import annotations

import math
from datetime import date, timedelta
from typing import Any, Iterable, Mapping

TIERS = [
    (0, "Spark"),
    (100, "Builder"),
    (250, "Steady"),
    (400, "Confident Self"),
    (650, "Relentless"),
    (850, "Unshakeable"),
]
CONFIDENT_SELF = 400


def _day(value: Any) -> date:
    return value if isinstance(value, date) else date.fromisoformat(str(value))


def _round_half_up(x: float) -> int:
    return int(math.floor(x + 0.5))  # matches JavaScript Math.round for positives


def tier_index(score: int) -> int:
    idx = 0
    for i, (minimum, _) in enumerate(TIERS):
        if score >= minimum:
            idx = i
    return idx


def analyze(challenges: Iterable[Mapping[str, Any]], today: date | None = None) -> dict:
    today = today or date.today()
    ticked: dict[date, int] = {}
    ticks = elapsed = notes = words = completed = active = upcoming = 0
    bonus = 0.0

    for c in challenges:
        start, days = _day(c["start"]), int(c["days"])
        t = (today - start).days
        marks = {int(i) for i, v in (c.get("ticks") or {}).items() if v}
        done = len(marks)
        ticks += done
        elapsed += max(0, min(days, t + 1))
        for i in marks:
            d = start + timedelta(days=i)
            ticked[d] = ticked.get(d, 0) + 1
        for text in (c.get("notes") or {}).values():
            if text:
                notes += 1
                words += len(str(text).split())
        if done >= days:
            completed += 1
            bonus += days * 1.5
        elif t < 0:
            upcoming += 1
        elif t < days:
            active += 1

    keys = sorted(ticked)
    longest = run = 0
    prev: date | None = None
    for k in keys:
        run = run + 1 if prev is not None and (k - prev).days == 1 else 1
        longest = max(longest, run)
        prev = k

    cursor = today if today in ticked else today - timedelta(days=1)
    current = 0
    while cursor in ticked:
        current += 1
        cursor -= timedelta(days=1)

    last = keys[-1] if keys else None
    idle = max(0, (today - last).days) if last else 0
    rate = min(1.0, ticks / elapsed) if elapsed else 0.0
    consistency = 0.5 + 0.5 * rate if elapsed else 1.0
    recency = 1 - min(0.15, max(0, idle - 7) * 0.01) if last else 1.0
    points = {"show": ticks * 3, "finish": _round_half_up(bonus), "streak": longest * 2, "reflect": notes * 2}
    raw = sum(points.values())
    score = _round_half_up(1000 * (1 - math.exp(-raw * consistency * recency / 1200)))
    ti = tier_index(score)
    nxt = TIERS[ti + 1] if ti + 1 < len(TIERS) else None

    weekday = [0] * 7  # Monday first
    for k, n in ticked.items():
        weekday[k.weekday()] += 1

    return {
        "score": score,
        "tier": ti,
        "tier_name": TIERS[ti][1],
        "next_tier": nxt[1] if nxt else None,
        "points_to_next": (nxt[0] - score) if nxt else 0,
        "confident_self": score >= CONFIDENT_SELF,
        "current_streak": current,
        "longest_streak": longest,
        "days_kept": len(keys),
        "ticks": ticks,
        "elapsed": elapsed,
        "rate": round(rate, 4),
        "consistency": round(consistency, 4),
        "recency": round(recency, 4),
        "idle_days": idle,
        "points": points,
        "completed": completed,
        "active": active,
        "upcoming": upcoming,
        "notes": notes,
        "words": words,
        "weekday": weekday,
    }
