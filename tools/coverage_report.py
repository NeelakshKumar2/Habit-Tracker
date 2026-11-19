"""Line coverage of server/ using only the standard library.  python tools/coverage_report.py --min 90
(The stdlib `trace` module ignores files whose bare name matches a stdlib module, e.g. errors.py, so this uses sys.settrace directly.)"""
from __future__ import annotations

import argparse
import logging
import sys
import threading
import trace
import unittest
import warnings
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
PREFIX = str(ROOT / "server")
HITS: dict[str, set[int]] = defaultdict(set)


def tracer(frame, event, arg):
    fn = frame.f_code.co_filename
    if not fn.startswith(PREFIX):
        return None
    HITS[fn].add(frame.f_lineno)

    def local(frame, event, arg):
        if event == "line":
            HITS[fn].add(frame.f_lineno)
        return local
    return local


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--min", type=float, default=0)
    args = ap.parse_args()
    warnings.simplefilter("ignore")
    logging.disable(logging.CRITICAL)
    threading.settrace(tracer)
    sys.settrace(tracer)
    try:
        suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), top_level_dir=str(ROOT))
        passed = unittest.TextTestRunner(verbosity=0, stream=open("/dev/null", "w")).run(suite).wasSuccessful()
    finally:
        sys.settrace(None)
        threading.settrace(None)
    total = covered = 0
    print(f"{'file':26} {'lines':>6} {'hit':>5} {'cover':>7}")
    for path in sorted((ROOT / "server").glob("*.py")):
        executable = set(trace._find_executable_linenos(str(path)))
        hit = HITS.get(str(path), set()) & executable
        total, covered = total + len(executable), covered + len(hit)
        missed = sorted(executable - hit)
        print(f"server/{path.name:19} {len(executable):6} {len(hit):5} {100 * len(hit) / max(1, len(executable)):6.1f}%" + (f"   missed: {missed[:10]}" if missed else ""))
    pct = 100 * covered / max(1, total)
    print(f"{'TOTAL':26} {total:6} {covered:5} {pct:6.1f}%   (all tests passed: {passed})")
    return 0 if passed and pct >= args.min else 1


if __name__ == "__main__":
    sys.exit(main())
