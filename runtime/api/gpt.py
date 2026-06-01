import os
import re
from urllib.parse import unquote, urlsplit
from flask import Blueprint, request, jsonify

gpt_bp = Blueprint('gpt', __name__)

ALLOWED_ROUTES = {
    ("GET",  "/api/status"),
    ("GET",  "/api/models"),
    ("GET",  "/api/projects"),
    ("GET",  "/api/tasks"),
    ("GET",  "/api/decisions"),
    ("GET",  "/api/live/sessions"),
    ("GET",  "/api/session/recent"),
    ("GET",  "/api/session/verification-status"),
    ("GET",  "/api/drafts/list"),
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

def _normalize_path(raw_path):
    if not isinstance(raw_path, str):
        return None
    if not raw_path.startswith("/api/"):
        return None
    parsed = urlsplit(raw_path)
    path = parsed.path
    decoded = unquote(path)
    blocked = ["..", "\\", "//", "%2e", "%2f", "%5c", "\x00"]
    if any(x in raw_path.lower() for x in blocked):
        return None
    if any(x in decoded.lower() for x in blocked):
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

def _require_api_key():
    valid_key = os.environ.get("CIS_API_KEY", "")
    provided_key = request.headers.get("X-CIS-API-Key", "")
    if not valid_key or provided_key != valid_key:
        return _unauthorized()
    return None

@gpt_bp.route("/gpt/status", methods=["GET"])
def gpt_status():
    auth_error = _require_api_key()
    if auth_error:
        return auth_error
    return jsonify({"status": "ok", "system": "CIS Creative Intelligence System", "version": "1.0"}), 200

@gpt_bp.route("/gpt/request", methods=["POST"])
def gpt_request():
    auth_error = _require_api_key()
    if auth_error:
        return auth_error
    payload = request.get_json(silent=True) or {}
    method = str(payload.get("method", "")).upper()
    raw_path = payload.get("path")
    body = payload.get("body") or {}
    if method not in {"GET", "POST"}:
        return _route_not_allowed()
    path = _normalize_path(raw_path)
    if not path:
        return _route_not_allowed()
    if not _is_allowed(method, path):
        return _route_not_allowed()
    from flask import current_app
    with current_app.test_client() as client:
        headers = {"Content-Type": "application/json"}
        if method == "GET":
            proxied = client.get(path, headers=headers)
        else:
            proxied = client.post(path, json=body, headers=headers)
    response_json = proxied.get_json(silent=True)
    if response_json is None:
        response_json = {"error": "non_json_response", "status_code": proxied.status_code, "body": proxied.get_data(as_text=True)}
    return jsonify(response_json), proxied.status_code
