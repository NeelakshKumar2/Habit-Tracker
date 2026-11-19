"""Run Habit Tracker on your own computer for development:  python run.py  ->  http://localhost:8765
For a real deployment use Docker or gunicorn (see README)."""
import os
import threading
import webbrowser

os.environ.setdefault("GRIT_ENV", "development")  # plain-HTTP cookies so it works on localhost

from server.main import create_app  # noqa: E402

PORT = int(os.getenv("PORT", "8765"))

if __name__ == "__main__":
    app = create_app()
    threading.Timer(1.0, lambda: webbrowser.open(f"http://localhost:{PORT}/")).start()
    app.run(host="127.0.0.1", port=PORT, threaded=True)
