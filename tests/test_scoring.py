import unittest
from datetime import date, timedelta

from server.scoring import CONFIDENT_SELF, analyze, tier_index

TODAY = date(2026, 11, 18)


def challenge(days, start_offset, ticked, notes=None):
    start = TODAY + timedelta(days=start_offset)
    return {"start": start.isoformat(), "days": days, "ticks": {str(i): True for i in ticked}, "notes": notes or {}}


class ScoringTests(unittest.TestCase):
    def test_empty_state_scores_zero(self):
        a = analyze([], TODAY)
        assert a["score"] == 0 and a["tier_name"] == "Spark"
        assert a["current_streak"] == 0 and a["longest_streak"] == 0


    def test_finished_21_day_challenge_is_worth_points(self):
        a = analyze([challenge(21, -30, range(21))], TODAY)
        assert a["completed"] == 1
        assert a["points"] == {"show": 63, "finish": 32, "streak": 42, "reflect": 0}
        assert a["recency"] == 0.97  # last tick was 10 days ago, so 3 percent is trimmed
        assert a["score"] == 105


    def test_notes_add_reflection_points(self):
        a = analyze([challenge(21, -30, range(21), {"0": "a", "5": "b b"})], TODAY)
        assert a["points"]["reflect"] == 4 and a["notes"] == 2 and a["words"] == 3


    def test_streak_counts_back_from_today_or_yesterday(self):
        a = analyze([challenge(30, -5, [2, 3, 4, 5])], TODAY)  # ticked 3 days ago .. today
        assert a["current_streak"] == 4
        b = analyze([challenge(30, -5, [1, 2, 3, 4])], TODAY)  # last tick yesterday: streak still alive
        assert b["current_streak"] == 4
        c = analyze([challenge(30, -5, [0, 1, 2])], TODAY)  # last tick 3 days ago: broken
        assert c["current_streak"] == 0 and c["longest_streak"] == 3


    def test_missing_days_lowers_consistency(self):
        full = analyze([challenge(10, -9, range(10))], TODAY)
        half = analyze([challenge(10, -9, range(0, 10, 2))], TODAY)
        assert full["consistency"] == 1.0 and half["consistency"] < 0.8
        assert half["score"] < full["score"]


    def test_recency_drops_after_a_week_idle(self):
        recent = analyze([challenge(40, -20, range(10, 20))], TODAY)
        idle = analyze([challenge(40, -20, range(0, 10))], TODAY)  # last tick 11 days ago
        assert recent["recency"] == 1.0 and idle["recency"] < 1.0


    def test_score_is_capped_below_1000(self):
        big = [challenge(365, -400, range(365), {str(i): "word" for i in range(365)})]
        assert analyze(big, TODAY)["score"] < 1000


    def test_tiers_and_confident_self_threshold(self):
        assert tier_index(0) == 0 and tier_index(99) == 0 and tier_index(100) == 1
        assert tier_index(CONFIDENT_SELF) == 3 and tier_index(850) == 5
        # a finished 90 day challenge with notes reaches Confident Self
        notes = {str(i): "kept going" for i in range(90)}
        a = analyze([challenge(90, -100, range(90), notes)], TODAY)
        assert a["confident_self"] and a["score"] >= CONFIDENT_SELF


    def test_weekday_counts_sum_to_days_kept(self):
        a = analyze([challenge(14, -13, range(14))], TODAY)
        assert sum(a["weekday"]) == a["days_kept"] == 14
