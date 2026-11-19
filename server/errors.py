from __future__ import annotations

from flask import jsonify, request
from werkzeug.exceptions import HTTPException


class ApiError(Exception):
    def __init__(self, status: int, message: str, headers: dict | None = None):
        super().__init__(message)
        self.status, self.message, self.headers = status, message, headers or {}


def json_body(max_bytes: int = 64_000) -> dict:
    if request.content_length and request.content_length > max_bytes:
        raise ApiError(413, "That request is too large.")
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ApiError(400, "Send a JSON object.")
    return data


def register_error_handlers(app) -> None:
    @app.errorhandler(ApiError)
    def _api(e: ApiError):
        resp = jsonify(error=e.message)
        resp.status_code = e.status
        for k, v in e.headers.items():
            resp.headers[k] = v
        return resp

    @app.errorhandler(HTTPException)
    def _http(e: HTTPException):
        if request.path.startswith("/api/"):
            resp = jsonify(error={413: "That file is too large."}.get(e.code, e.description))
            resp.status_code = e.code or 500
            return resp
        return e

    @app.errorhandler(Exception)
    def _boom(e: Exception):
        app.logger.exception("unhandled error")
        resp = jsonify(error="Something went wrong on our side. Please try again.")
        resp.status_code = 500
        return resp
