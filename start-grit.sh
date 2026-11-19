#!/usr/bin/env bash
# Local development: creates a virtual environment, installs dependencies and starts Habit Tracker.
set -e
cd "$(dirname "$0")"
[ -d .venv ] || python3 -m venv .venv
. .venv/bin/activate
pip install -q -r requirements.txt
python run.py
