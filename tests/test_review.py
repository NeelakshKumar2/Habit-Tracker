import unittest
from datetime import date

from server.review import weekly_review
from server.scoring import analyze

TODAY = date(2026, 11, 18)


def review(challenges, intent=None):
    return weekly_review(analyze(challenges, TODAY), intent)


def ch(ticked, days=21, start="2026-11-10"):
    return [{"name": "Walk", "start": start, "days": days, "ticks": {str(i): True for i in ticked}, "notes": {}}]


class ReviewTests(unittest.TestCase):
    def test_empty_state_encourages_a_first_tick(self):
        r = review([])
        assert "first tick" in r["headline"].lower() and r["insights"]


    def test_uses_the_users_habit_and_cue(self):
        r = review(ch(range(9)), {"habit": "Walk 30 minutes", "when": "after coffee"})
        assert "Walk 30 minutes" in r["next_step"] and "after coffee" in r["next_step"]


    def test_streak_headline(self):
        assert "in a row" in review(ch(range(9)))["headline"]  # ticked through today


    def test_broken_chain_headline(self):
        assert "broken" in review(ch([0, 1, 2]))["headline"].lower()


    def test_low_consistency_suggests_a_smaller_habit(self):
        r = review(ch([0, 3, 8]))  # kept 3 of 9 days
        assert any("two-minute" in i for i in r["insights"])


    def test_never_returns_more_than_three_insights(self):
        assert len(review(ch([0, 4, 8]))["insights"]) <= 3
