"""The browser and the server each compute the grit score. Prove they agree on random data."""
import json
import random
import shutil
import subprocess
import tempfile
import unittest
from datetime import date, timedelta

from server.scoring import analyze


@unittest.skipUnless(shutil.which("node"), "node not installed")
class ScoreParity(unittest.TestCase):
    def test_js_and_python_scores_match_on_400_random_datasets(self):
        rnd = random.Random(2026)
        cases = []
        for _ in range(400):
            today = date(2026, 1, 1) + timedelta(days=rnd.randrange(0, 700))
            items = []
            for i in range(rnd.randrange(0, 6)):
                days = rnd.choice([1, 7, 21, 41, 90, 180, 365])
                start = today + timedelta(days=rnd.randrange(-400, 30))
                density = rnd.choice([0, 0.2, 0.5, 0.9, 1.0])
                ticks = {str(d): True for d in range(days) if rnd.random() < density}
                notes = {str(d): " ".join("w" * rnd.randrange(1, 5) for _ in range(rnd.randrange(1, 9))) for d in range(days) if rnd.random() < 0.15}
                items.append({"id": f"c{i}", "name": "x", "days": days, "start": start.isoformat(), "created": i, "ticks": ticks, "notes": notes})
            cases.append({"today": today.isoformat(), "items": items})
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(cases, f)
        out = json.loads(subprocess.run(["node", "tests/parity.mjs", f.name], capture_output=True, text=True, check=True).stdout)
        self.assertEqual(len(out), 400)
        for case, js in zip(cases, out):
            py = analyze(case["items"], date.fromisoformat(case["today"]))
            got = {"score": py["score"], "tier": py["tier"], "current": py["current_streak"], "longest": py["longest_streak"],
                   "daysKept": py["days_kept"], "ticks": py["ticks"], "elapsed": py["elapsed"], "notes": py["notes"], "completed": py["completed"],
                   "idle": py["idle_days"], "pts": py["points"]}
            want = {k: js[k] for k in got}
            self.assertEqual(got, want, case["today"])
            self.assertAlmostEqual(py["rate"], js["rate"], places=3)
            self.assertAlmostEqual(py["consistency"], js["cons"], places=3)
            self.assertAlmostEqual(py["recency"], js["rec"], places=3)
