import os
import re
from urllib.parse import unquote, urlsplit

from flask import request, jsonify


ALLOWED_ROUTES = {
    ("GET", "/api/status"),
    ("GET", "/api/models"),
    ("GET", "/api/projects"),
    ("GET", "/api/tasks"),
    ("GET", "/api/decisions"),
    ("GET", "/api/live/sessions"),
    ("GET", "/api/session/recent"),
    ("GET", "/api/session/verification-status"),
    ("GET", "/api/drafts/list"),

    ("POST", "/api/live/sessions"),
    ("POST", "/api/live/push"),
    ("POST", "/api/captures"),
    ("POST", "/api/tasks"),
    ("POST", "/api/decisions"),
}

DYNAMIC_ALLOWED_ROUTES = [
    ("POST", re.compile(r"^/api/live/sessions/[A-Za-z0-9_-]+/rounds$")),
]


def _unauthorized():
    return jsonify({"error": "unauthorized"}), 401


def _route_not_allowed():
    return jsonify({"error": "route_not_allowed"}), 403


def _normalize_gpt_path(raw_path):
    if not isinstance(raw_path, str):
        return None

    if not raw_path.startswith("/api/"):
        return None

    parsed = urlsplit(raw_path)
    path = parsed.path
    decoded = unquote(path)

    lowered_raw = raw_path.lower()
    lowered_decoded = decoded.lower()

    blocked = [
        "..",
        "\\",
        "//",
        "%2e",
        "%2f",
        "%5c",
        "\x00",
    ]

    if any(x in lowered_raw for x in blocked):
        return None

    if any(x in lowered_decoded for x in blocked):
        return None

    if not decoded.startswith("/api/"):
        return None

    return decoded


def _is_allowed(method, path):
    method = method.upper()

    if (method, path) in ALLOWED_ROUTES:
        return True

    for allowed_method, pattern in DYNAMIC_ALLOWED_ROUTES:
        if method == allowed_method and pattern.match(path):
            return True

    return False


def register_gpt_gateway(app):
    @app.route("/gpt/request", methods=["POST"])
    def gpt_request():
        expected_key = os.getenv("CIS_API_KEY")
        provided_key = request.headers.get("X-CIS-API-Key")

        if not expected_key or provided_key != expected_key:
            return _unauthorized()

        payload = request.get_json(silent=True) or {}

        method = str(payload.get("method", "")).upper()
        raw_path = payload.get("path")
        body = payload.get("body") or {}

        if method not in {"GET", "POST"}:
            return _route_not_allowed()

        path = _normalize_gpt_path(raw_path)
        if not path:
            return _route_not_allowed()

        if not _is_allowed(method, path):
            return _route_not_allowed()

        with app.test_client() as client:
            headers = {"Content-Type": "application/json"}

            if method == "GET":
                proxied = client.get(path, headers=headers)
            else:
                proxied = client.post(path, json=body, headers=headers)

        response_json = proxied.get_json(silent=True)

        if response_json is None:
            response_json = {
                "error": "non_json_response",
                "status_code": proxied.status_code,
                "body": proxied.get_data(as_text=True),
            }

        return jsonify(response_json), proxied.status_code
