"""
api/adapter.py — CIS Abstraction Layer API

Flask blueprint exposing the dispatch boundary between the CIS control plane
and the Hermes backend. This is the adapter layer from DEV-PIVOT-05 §5.

Routes:
    GET  /api/adapter/health        — health check all profiles
    GET  /api/adapter/profiles      — list all profiles with capabilities
    POST /api/adapter/dispatch      — classify intent + dispatch to profile
    POST /api/adapter/chat          — forward a message to a specific profile
"""

from flask import Blueprint, jsonify, request
import json
import uuid
import urllib.request
import urllib.error

from abstraction.dispatch import (
    PROFILES,
    ROLE_ALIASES,
    resolve_role,
    get_profile,
    get_gateway_url,
    health_all,
    health_human,
    dispatch_summary,
)

# Import the existing router for intent classification
from api.router import classify_route

adapter_bp = Blueprint("adapter", __name__)

# ═══════════════════════════════════════════════════════════════════════
#  HEALTH
# ═══════════════════════════════════════════════════════════════════════


@adapter_bp.route("/api/adapter/health", methods=["GET"])
def adapter_health():
    """Check health of all Hermes gateway profiles.

    Returns per-profile: healthy (bool), port, model, response_time, error.
    """
    results = health_all()
    all_healthy = all(r["healthy"] for r in results.values())
    return jsonify({
        "all_healthy": all_healthy,
        "profiles": results,
        "profile_count": len(results),
    })


@adapter_bp.route("/api/adapter/status", methods=["GET"])
def adapter_status():
    """Return a human-readable system status summary.

    Plain English. No checkboxes. No JSON that requires interpretation.
    Explains what was tested, what the results mean, and what to do if
    something is wrong.
    """
    result = health_human()
    return jsonify(result)


# ═══════════════════════════════════════════════════════════════════════
#  PROFILES
# ═══════════════════════════════════════════════════════════════════════


@adapter_bp.route("/api/adapter/profiles", methods=["GET"])
def adapter_profiles():
    """List all available profiles with capabilities and gateway URLs."""
    summary = dispatch_summary()
    # Add gateway URLs
    for role in summary:
        summary[role]["gateway_url"] = get_gateway_url(role)
        summary[role]["aliases"] = [
            alias for alias, target in ROLE_ALIASES.items()
            if target == role and alias != role
        ]
    return jsonify({
        "profiles": summary,
        "role_count": len(summary),
    })


# ═══════════════════════════════════════════════════════════════════════
#  DISPATCH — classify intent and return route
# ═══════════════════════════════════════════════════════════════════════


@adapter_bp.route("/api/adapter/dispatch", methods=["POST"])
def adapter_dispatch():
    """Classify an intent and return the dispatch decision.

    Request body:
        {
            "message": "I need a plan for the knowledge base schema",
            "override": null,          // optional: force a specific route
            "classify_only": false      // if true, don't check gateway health
        }

    Returns:
        {
            "dispatch_id": "uuid",
            "route": "v4_drafter",
            "role": "drafter",
            "profile": "hermes-v4pro",
            "port": 8645,
            "gateway_url": "http://127.0.0.1:8645/v1/chat/completions",
            "confidence": "high",
            "reason": "Architecture/proposal intent detected",
            "signals_matched": ["design", "plan"],
            "healthy": true,
            "next_suggested_action": "Send to Review1 for adversarial critique"
        }
    """
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or data.get("intent") or "").strip()
    override = data.get("override")
    classify_only = data.get("classify_only", False)

    if not message:
        return jsonify({"error": "message or intent is required"}), 400

    # Step 1: Classify the intent using the existing router
    classification = classify_route(message, override=override)

    # Step 2: Map the router's route to our profile dispatch
    route = classification.get("route", "v4_drafter")

    # Map router route names to abstraction layer roles
    ROUTE_TO_ROLE = {
        "draft": "draft",
        "v4_drafter": "draft",
        "review1": "review1",
        "v4_reviewer": "review1",
        "review2": "review2",
        "brain": "brain",
        "fast": "brain",
        "menter": "menter",
        "v4_implementer": "menter",
        "verify": "verify",
        "blocked": None,
        "multihop": "brain",  # multihop starts with research
    }
    role = ROUTE_TO_ROLE.get(route)
    profile = get_profile(role) if role else None

    # Step 3: Check gateway health (unless classify_only)
    healthy = None
    if profile and not classify_only:
        from abstraction.dispatch import check_gateway
        healthy, _, _ = check_gateway(profile["port"])

    # Step 4: Build the dispatch result
    dispatch_id = str(uuid.uuid4())
    result = {
        "dispatch_id": dispatch_id,
        "message": message,
        "route": route,
        "role": role,
        "profile": profile["hermes_profile"] if profile else None,
        "port": profile["port"] if profile else None,
        "gateway_url": get_gateway_url(role) if role else None,
        "confidence": classification.get("confidence", "unknown"),
        "reason": classification.get("reason", ""),
        "signals_matched": classification.get("signals_matched", []),
        "multihop": classification.get("multihop", False),
        "qwen_blocked": classification.get("qwen_blocked", False),
        "healthy": healthy,
        "next_suggested_action": _get_next_action(route, classification),
    }

    # Handle blocked/Qwen gate
    if route == "blocked":
        result["qwen_block_reason"] = classification.get("qwen_block_reason", "")

    return jsonify(result)


# ═══════════════════════════════════════════════════════════════════════
#  CHAT — forward a message to a profile's gateway
# ═══════════════════════════════════════════════════════════════════════


@adapter_bp.route("/api/adapter/chat", methods=["POST"])
def adapter_chat():
    """Forward a message to a specific Hermes profile's chat gateway.

    Request body:
        {
            "role": "drafter",         // or "reviewer", "implementer", etc.
            "message": "Design a schema for X",
            "thread_id": "optional-thread-id",
            "system_prompt": "optional system prompt override"
        }

    Returns the gateway's raw chat completion response.
    """
    data = request.get_json(silent=True) or {}
    role_name = (data.get("role") or "").strip().lower()
    message = (data.get("message") or "").strip()
    thread_id = data.get("thread_id") or str(uuid.uuid4())
    system_prompt = data.get("system_prompt", "").strip()

    if not role_name or not message:
        return jsonify({"error": "role and message are required"}), 400

    # Resolve the role
    role = resolve_role(role_name)
    if not role:
        return jsonify({
            "error": f"Unknown role '{role_name}'. Available: {list(ROLE_ALIASES.keys())}",
            "available_roles": list(PROFILES.keys()),
        }), 400

    gateway_url = get_gateway_url(role)
    if not gateway_url:
        return jsonify({"error": f"No gateway configured for role '{role}'"}), 500

    profile = get_profile(role)

    # Build messages array
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": message})

    # Forward to the gateway
    payload = json.dumps({
        "model": profile.get("hermes_profile", ""),
        "messages": messages,
        "max_tokens": 4096,
    }).encode("utf-8")

    try:
        import os as _os
        _key = _os.environ.get("CIS_" + role.upper() + "_API_KEY", "")
        _hdrs = {"Content-Type": "application/json"}
        if _key:
            _hdrs["Authorization"] = "Bearer " + _key
        req = urllib.request.Request(
            gateway_url,
            data=payload,
            headers=_hdrs,
        )
        resp = urllib.request.urlopen(req, timeout=300)
        body = json.loads(resp.read().decode("utf-8"))
        return jsonify({
            "dispatch_id": str(uuid.uuid4()),
            "role": role,
            "profile": profile["hermes_profile"],
            "port": profile["port"],
            "thread_id": thread_id,
            "response": body,
        })
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:500]
        return jsonify({
            "error": f"Gateway error: HTTP {e.code}",
            "detail": body,
            "role": role,
            "port": profile["port"],
        }), 502
    except urllib.error.URLError as e:
        return jsonify({
            "error": f"Gateway unreachable: {e.reason}",
            "role": role,
            "port": profile["port"],
        }), 503
    except Exception as e:
        return jsonify({
            "error": str(e),
            "role": role,
            "port": profile["port"],
        }), 500


# ═══════════════════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════════════════


def _get_next_action(route: str, classification: dict) -> str:
    """Get the suggested next action based on the route."""
    if classification.get("qwen_blocked"):
        return "Use Draft to generate a properly formatted directive first"

    actions = {
        "fast": "Evidence returned — forward to Draft for proposal",
        "v4_drafter": "Send to Review1 for adversarial critique",
        "draft": "Send to Review1 for adversarial critique",
        "v4_reviewer": "Incorporate critique, escalate or approve via Eric Gate",
        "review1": "Incorporate critique, escalate or approve via Eric Gate",
        "review2": "Incorporate critique, escalate or approve via Eric Gate",
        "qwen": "Review VERDICT / ACTION / EVIDENCE output",
        "blocked": "Reformat as FINAL_DIRECTIVE or JUDGE_REQUEST",
    }
    if classification.get("multihop"):
        return "Research preflight complete — auto-forwarding to Draft"
    return actions.get(route, "Review classification and decide next step")
