import multiprocessing
import os

bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"
workers = int(os.getenv("WEB_CONCURRENCY", min(multiprocessing.cpu_count() * 2 + 1, 9)))
threads = 2
timeout = 30
graceful_timeout = 20
keepalive = 5
max_requests = 2000          # recycle workers to cap slow memory growth
max_requests_jitter = 200
preload_app = True           # run migrations once, then fork
accesslog = "-"
errorlog = "-"
