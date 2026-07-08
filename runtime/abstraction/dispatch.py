"""
dispatch.py — CIS Abstraction Layer: Profile Dispatch & Health

Maps CIS role names to Hermes profiles, gateway ports, and capabilities.
One source of truth for "which port is Draft on."

Per DEV-PIVOT-05 §5: When Hermes updates and ports change, only this file changes.
Role names are model-agnostic — they describe function, not provider.
Model/provider details live in agents_static.yaml and enforcement profile configs.
"""

import urllib.request
import json
import time
from typing import Dict, Optional, List, Tuple

# ═══════════════════════════════════════════════════════════════════════
#  PROFILE DISPATCH MAP (canonical — update here when ports change)
#  Role keys are model-agnostic. hermes_profile is the filesystem path,
#  not an identity. Model fields are for gateway calls only.
# ═══════════════════════════════════════════════════════════════════════

PROFILES: Dict[str, dict] = {
    "brain": {
        "role": "brain",
        "label": "Brain",
        "hermes_profile": "hermes-brainstorm",
        "port": 8644,
        "description": "Brain — lateral exploration, challenges assumptions, surfaces possibilities",
        "capabilities": ["brainstorm", "explore", "diverge", "challenge", "question"],
    },
    "draft": {
        "role": "draft",
        "label": "Draft",
        "hermes_profile": "hermes-v4pro",
        "port": 8645,
        "description": "Draft — authors proposals, designs, plans",
        "capabilities": ["draft", "design", "plan", "research", "write"],
    },
    "review1": {
        "role": "review1",
        "label": "Review1",
        "hermes_profile": "hermes-r1",
        "port": 8643,
        "description": "Review1 — adversarial critique, first independent reviewer",
        "capabilities": ["review", "critique", "verify", "challenge", "audit"],
    },
    "review2": {
        "role": "review2",
        "label": "Review2",
        "hermes_profile": "hermes-glm-reviewer",
        "port": 8647,
        "description": "Review2 — second independent reviewer, different training distribution",
        "capabilities": ["review", "critique", "verify", "challenge", "audit"],
    },
    "menter": {
        "role": "menter",
        "label": "Menter",
        "hermes_profile": "hermes-v4impl",
        "port": 8646,
        "description": "Menter — builds code, executes plans",
        "capabilities": ["implement", "build", "execute", "test", "deploy"],
    },
    "verify": {
        "role": "verify",
        "label": "Verify",
        "hermes_profile": "hermes-glm-verifier",
        "port": 8648,
        "description": "Verify — independent evidence verification gate",
        "capabilities": ["verify", "audit", "validate", "check", "confirm"],
    },
}

# Role aliases (what users/agents might call them — includes legacy names)
ROLE_ALIASES = {
    "brain": "brain",
    "brainstorm": "brain",
    "v4_brainstorm": "brain",
    "hermes-brainstorm": "brain",
    "draft": "draft",
    "drafter": "draft",
    "v4_drafter": "draft",
    "v4pro": "draft",
    "hermes-v4pro": "draft",
    "review1": "review1",
    "reviewer1": "review1",
    "v4_reviewer": "review1",
    "reviewer": "review1",
    "r1": "review1",
    "hermes-r1": "review1",
    "review2": "review2",
    "reviewer2": "review2",
    "glm_reviewer": "review2",
    "hermes-glm-reviewer": "review2",
    "menter": "menter",
    "implementer": "menter",
    "v4_implementer": "menter",
    "v4impl": "menter",
    "hermes-v4impl": "menter",
    "verify": "verify",
    "verifier": "verify",
    "glm_verifier": "verify",
    "hermes-glm-verifier": "verify",
    # Legacy aliases — keep for backward compatibility, route to review1
    "qwen": "review1",
    "hermes-qwen": "review1",
    "prime": "brain",  # legacy: prime research now maps to brain for research
    "research": "brain",
    "fast": "brain",
    "hermes-prime": "brain",
}

# ═══════════════════════════════════════════════════════════════════════
#  HEALTH CHECKS
# ═══════════════════════════════════════════════════════════════════════

BASE_URL = "http://127.0.0.1"
HEALTH_TIMEOUT = 5  # seconds


def check_gateway(port: int) -> Tuple[bool, Optional[str], float]:
    """Check if a Hermes gateway is healthy on the given port.

    Returns (healthy, error_message, response_time_seconds).

    A gateway is healthy only if:
    1. The port accepts connections (process is running)
    2. The response contains valid JSON with a choices array (model backend works)

    A stale/zombie process that accepts connections but returns empty
    or malformed responses is NOT healthy — it can't serve model calls.
    """
    url = f"{BASE_URL}:{port}/v1/chat/completions"
    payload = json.dumps({
        "model": "ping",
        "messages": [{"role": "user", "content": "ping"}],
        "max_tokens": 1,
    }).encode("utf-8")

    start = time.time()
    try:
        req = urllib.request.Request(
            url, data=payload,
            headers={"Content-Type": "application/json"},
        )
        resp = urllib.request.urlopen(req, timeout=HEALTH_TIMEOUT)
        elapsed = time.time() - start
        body = resp.read().decode("utf-8", errors="replace")

        # Validate the response has actual content — not just a 200 with empty body
        try:
            data = json.loads(body)
            choices = data.get("choices", [])
            if not choices:
                return False, "Response has no choices array — gateway may be a zombie", round(elapsed, 3)
            content = choices[0].get("message", {}).get("content", "")
            if not content and not data.get("error"):
                # Empty content with no error means the model backend isn't working
                # (Some gateways return reasoning_content but empty content — that's OK)
                reasoning = choices[0].get("message", {}).get("reasoning_content", "")
                if not reasoning:
                    return False, "Response has empty content and no reasoning — model backend not working", round(elapsed, 3)
        except (json.JSONDecodeError, KeyError):
            return False, f"Response is not valid JSON: {body[:200]}", round(elapsed, 3)

        return True, None, round(elapsed, 3)
    except urllib.error.HTTPError as e:
        elapsed = time.time() - start
        body = e.read().decode("utf-8", errors="replace")[:200]
        # 401 means the gateway is alive but requires auth — that's healthy
        if e.code == 401:
            return True, f"HTTP 401 (auth required — gateway alive)", round(elapsed, 3)
        # Other HTTP errors mean the gateway is misconfigured or broken
        return False, f"HTTP {e.code}: {body}", round(elapsed, 3)
    except urllib.error.URLError as e:
        elapsed = time.time() - start
        return False, str(e.reason), round(elapsed, 3)
    except Exception as e:
        elapsed = time.time() - start
        return False, str(e), round(elapsed, 3)


def health_all() -> Dict[str, dict]:
    """Check health of all profiles. Returns {role: {healthy, port, error, response_time}}."""
    results = {}
    for role, profile in PROFILES.items():
        healthy, error, rt = check_gateway(profile["port"])
        results[role] = {
            "role": role,
            "label": profile.get("label", role),
            "profile": profile["hermes_profile"],
            "port": profile["port"],
            "healthy": healthy,
            "error": error,
            "response_time": rt,
        }
    return results


# ═══════════════════════════════════════════════════════════════════════
#  RESOLVE & DISPATCH
# ═══════════════════════════════════════════════════════════════════════


def resolve_role(name: str) -> Optional[str]:
    """Resolve a name or alias to a canonical role key. Returns None if unrecognized."""
    return ROLE_ALIASES.get(name.lower().strip())


def get_profile(role: str) -> Optional[dict]:
    """Get the full profile dict for a canonical role. Returns None if not found."""
    return PROFILES.get(role)


def get_gateway_url(role: str) -> Optional[str]:
    """Get the gateway chat completions URL for a canonical role."""
    profile = PROFILES.get(role)
    if profile:
        return f"{BASE_URL}:{profile['port']}/v1/chat/completions"
    return None


def list_roles() -> List[str]:
    """Return all canonical role names."""
    return list(PROFILES.keys())


def dispatch_summary() -> Dict:
    """Return a summary of all profiles with their capabilities for API consumers."""
    return {
        role: {
            "label": p.get("label", role),
            "port": p["port"],
            "description": p["description"],
            "capabilities": p["capabilities"],
        }
        for role, p in PROFILES.items()
    }


# ═══════════════════════════════════════════════════════════════════════
#  HUMAN-READABLE HEALTH EXPLANATIONS
# ═══════════════════════════════════════════════════════════════════════

HEALTH_CRITERIA = (
    "Each gateway is tested by sending a ping to its chat completions endpoint. "
    "The test checks: (1) the port accepts connections, (2) the Hermes gateway process "
    "responds, (3) the response arrives within 5 seconds. Any response — even an "
    "authentication error — means the gateway is alive and capable of serving requests. "
    "A gateway is only marked unhealthy if the port refuses connections (process is down) "
    "or the connection times out (process is hung)."
)


def explain_health(role_key: str, result: dict) -> str:
    """Return a plain-English explanation of one profile's health result."""
    profile = PROFILES.get(role_key, {})
    name = profile.get("description", role_key)
    port = result["port"]
    healthy = result["healthy"]
    rt = result.get("response_time", 0)
    error = result.get("error", "")

    if healthy and error and "401" in str(error):
        return (
            f"{name} (port {port}) is responding. It returned an authentication "
            f"error which is expected — the gateway is alive and ready, it just "
            f"requires an API key to serve chat requests. Response time: {rt}s."
        )
    elif healthy and error:
        return (
            f"{name} (port {port}) is responding but returned an unexpected error: "
            f"{error}. The gateway process is alive but may be misconfigured. "
            f"Response time: {rt}s."
        )
    elif healthy:
        return (
            f"{name} (port {port}) is responding normally. "
            f"Response time: {rt}s."
        )
    elif "Connection refused" in str(error) or "refused" in str(error).lower():
        return (
            f"{name} (port {port}) is NOT responding. The port refused the connection. "
            f"This means the Hermes gateway process is not running. "
            f"Start it with: systemctl --user start <service-name>"
        )
    elif "timeout" in str(error).lower():
        return (
            f"{name} (port {port}) is NOT responding. The connection timed out. "
            f"The Hermes gateway process may be hung or overloaded. "
            f"Check: systemctl --user status <service-name>"
        )
    else:
        return (
            f"{name} (port {port}) is NOT responding. Error: {error}. "
            f"The gateway process may be down or unreachable."
        )


def health_human() -> Dict:
    """Return health check results with plain-English explanations."""
    raw = health_all()
    all_healthy = all(r["healthy"] for r in raw.values())
    explanations = {
        role: explain_health(role, result)
        for role, result in raw.items()
    }

    up_count = sum(1 for r in raw.values() if r["healthy"])
    down_count = len(raw) - up_count

    if all_healthy:
        summary = (
            f"All {len(raw)} Hermes gateways are running and responding. "
            f"The system is ready for pipeline work."
        )
    elif up_count == 0:
        summary = (
            f"All {len(raw)} Hermes gateways are down. "
            f"The system cannot process any pipeline work. "
            f"Check gateway services with: systemctl --user list-units 'hermes-gateway*'"
        )
    else:
        summary = (
            f"{up_count} of {len(raw)} Hermes gateways are running. "
            f"{down_count} gateway(s) are down and need attention."
        )

    return {
        "summary": summary,
        "criteria": HEALTH_CRITERIA,
        "gateways_up": up_count,
        "gateways_down": down_count,
        "all_healthy": all_healthy,
        "details": explanations,
    }
