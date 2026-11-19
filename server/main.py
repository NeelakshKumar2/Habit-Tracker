"""Habit Tracker server: accounts, private data per user, and the web app itself."""
from __future__ import annotations

import logging
from pathlib import Path
from urllib.parse import urlparse

from flask import Flask, Response, abort, jsonify, request, send_from_directory
from werkzeug.middleware.proxy_fix import ProxyFix

from . import api, auth
from .mail import default_mailer
from .config import Settings
from .db import close_db, migrate
from .errors import ApiError, register_error_handlers

WEB = Path(__file__).resolve().parent.parent / "web"
CSP = ("default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
       "font-src https://fonts.gstatic.com; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; "
       "base-uri 'none'; form-action 'self'; object-src 'none'")


def create_app(overrides: dict | None = None) -> Flask:
    settings = Settings.from_env(**(overrides or {}))
    app = Flask(__name__, static_folder=None)
    app.extensions["grit"] = settings
    app.extensions["grit_mail"] = default_mailer(app)
    app.config.update(MAX_CONTENT_LENGTH=settings.avatar_max_bytes + 512 * 1024, SEND_FILE_MAX_AGE_DEFAULT=None)
    app.json.sort_keys = False
    if settings.trust_proxy:
        n = settings.trust_proxy
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=n, x_proto=n, x_host=n)
    if not app.logger.handlers:
        logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    migrate(settings.db_path)
    app.teardown_appcontext(close_db)
    register_error_handlers(app)
    app.register_blueprint(auth.bp)
    app.register_blueprint(api.bp)

    @app.before_request
    def guard():
        """Cross-site request forgery: unsafe methods need our header and a same-site Origin."""
        if request.path.startswith("/api/") and request.method not in ("GET", "HEAD", "OPTIONS"):
            if request.headers.get("X-Requested-With") != "grit":
                raise ApiError(403, "Request blocked.")
            origin = request.headers.get("Origin")
            if origin and urlparse(origin).netloc != request.host:
                raise ApiError(403, "Request blocked.")

    @app.after_request
    def headers(resp: Response):
        resp.headers.setdefault("Content-Security-Policy", CSP)
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        resp.headers["X-Frame-Options"] = "DENY"
        resp.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        if settings.secure_cookies:
            resp.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
        if request.path.startswith("/api/"):
            resp.headers.setdefault("Cache-Control", "no-store")
        return resp

    @app.get("/robots.txt")
    def robots():
        return Response(f"User-agent: *\nAllow: /\nDisallow: /app.html\nDisallow: /api/\nSitemap: {request.host_url}sitemap.xml\n", mimetype="text/plain")

    @app.get("/sitemap.xml")
    def sitemap():
        base = request.host_url
        xml = ('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
               f"  <url><loc>{base}</loc></url>\n</urlset>\n")
        return Response(xml, mimetype="application/xml")

    @app.get("/")
    def home():
        return send_from_directory(WEB, "index.html")

    @app.get("/<path:name>")
    def static_files(name: str):
        if name.startswith("api/") or any(part.startswith(".") for part in name.split("/")):
            abort(404)
        return send_from_directory(WEB, name)

    return app
