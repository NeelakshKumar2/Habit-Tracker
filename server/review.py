"""Weekly review: plain rules over your own numbers. Instant, private and works offline."""
from __future__ import annotations

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def _next_step(intent: dict, empty: bool = False) -> str:
    habit, when = (intent.get("habit") or "").strip(), (intent.get("when") or "").strip()
    if habit:
        return f"Do your one habit now: {habit}" + (f" ({when})." if when else ".")
    if empty:
        return "Open the Habit page and write down your one habit and when you will do it."
    return "Set your one habit and its cue on the Habit page so tomorrow is already decided."


def weekly_review(a: dict, intent: dict | None = None) -> dict:
    """a is the output of scoring.analyze."""
    intent = intent or {}
    if a["days_kept"] == 0:
        return {
            "headline": "Your first tick is the hardest. Make it small.",
            "insights": ["Start a challenge and tick today. One kept day beats a perfect plan."],
            "next_step": _next_step(intent, empty=True),
        }

    if a["current_streak"] >= 3:
        headline = f"{a['current_streak']} days in a row. Protect the chain."
    elif a["current_streak"] == 0:
        headline = "Your chain is broken. Restart today, not tomorrow."
    else:
        headline = f"{a['tier_name']} tier, grit score {a['score']}. Keep building."

    insights: list[str] = []
    if a["elapsed"] and a["rate"] < 0.7:
        insights.append(
            f"You kept {round(a['rate'] * 100)}% of the days that have passed. "
            "Shrink the habit to its two-minute version until you reach 80%."
        )
    elif a["elapsed"]:
        insights.append(f"You kept {round(a['rate'] * 100)}% of the days that have passed. That is solid consistency.")

    wd = a["weekday"]
    if sum(wd) >= 7:
        best, worst = max(range(7), key=wd.__getitem__), min(range(7), key=wd.__getitem__)
        if wd[worst] < wd[best]:
            insights.append(
                f"{DAYS[worst]} is your weakest day ({wd[worst]} kept against {wd[best]} on {DAYS[best]}). "
                "Move the habit earlier on that day."
            )

    if a["ticks"] and a["notes"] < a["ticks"] * 0.25:
        insights.append(
            f"You wrote notes on {a['notes']} of {a['ticks']} kept days. "
            "Thirty words a day shows what works and adds to your score."
        )

    if a["next_tier"]:
        insights.append(f"{a['points_to_next']} points to {a['next_tier']}. Each kept day is worth at least 3.")
    else:
        insights.append("You are in the top tier. Hold it, and stay consistent.")

    return {"headline": headline, "insights": insights[:3], "next_step": _next_step(intent)}
