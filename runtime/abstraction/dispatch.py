"""
dispatch.py — CIS Abstraction Layer: Profile Dispatch & Health

Maps CIS role names to Hermes profiles, gateway ports, and capabilities.
One source of truth for "which port is the Drafter on."

Per DEV-PIVOT-05 §5: When Hermes updates and ports change, only this file changes.
"""

import urllib.request
import json
import time
from typing import Dict, Optional, List, Tuple

# ═══════════════════════════════════════════════════════════════════════
#  PROFILE DISPATCH MAP (canonical — update here when ports change)
# ═══════════════════════════════════════════════════════════════════════

PROFILES: Dict[str, dict] = {
    "drafter": {
        "role": "drafter",
        "hermes_profile": "hermes-v4pro",
        "port": 8645,
        "model": "deepseek-v4-pro",
        "description": "V4 Drafter — authors proposals, designs, plans",
        "capabilities": ["draft", "design", "plan", "research", "write"],
    },
    "reviewer": {
        "role": "reviewer",
        "hermes_profile": "hermes-r1",
        "port": 8643,
        "model": "deepseek-v4-pro",
        "description": "V4 Reviewer — adversarial critique, verification",
        "capabilities": ["review", "critique", "verify", "challenge", "audit"],
    },
    "implementer": {
        "role": "implementer",
        "hermes_profile": "hermes-v4impl",
        "port": 8646,
        "model": "deepseek-v4-pro",
        "description": "V4 Implementer — builds code, executes plans",
        "capabilities": ["implement", "build", "execute", "test", "deploy"],
    },
    "prime": {
        "role": "prime",
        "hermes_profile": "hermes-prime",
        "port": 8642,
        "model": "deepseek-v4-flash",
        "description": "Prime/Research — fast lookups, web search",
        "capabilities": ["research", "search", "fact-check", "summarize"],
    },
    "qwen": {
        "role": "qwen",
        "hermes_profile": "hermes-qwen",
        "port": 8644,
        "model": "qwen3-vl-30b",
        "description": "Qwen Reviewer — second opinion, local GPU",
        "capabilities": ["review", "analyze", "vision"],
    },
}

# Role aliases (what users/agents might call them)
ROLE_ALIASES = {
    "drafter": "drafter",
    "v4_drafter": "drafter",
    "v4pro": "drafter",
    "hermes-v4pro": "drafter",
    "reviewer": "reviewer",
    "v4_reviewer": "reviewer",
    "r1": "reviewer",
    "hermes-r1": "reviewer",
    "implementer": "implementer",
    "v4_implementer": "implementer",
    "v4impl": "implementer",
    "hermes-v4impl": "implementer",
    "prime": "prime",
    "research": "prime",
    "fast": "prime",
    "hermes-prime": "prime",
    "qwen": "qwen",
    "hermes-qwen": "qwen",
}

# ═══════════════════════════════════════════════════════════════════════
#  HEALTH CHECKS
# ═══════════════════════════════════════════════════════════════════════

BASE_URL = "http://127.0.0.1"
HEALTH_TIMEOUT = 5  # seconds


def check_gateway(port: int) -> Tuple[bool, Optional[str], float]:
    """Check if a Hermes gateway is healthy on the given port.

    Returns (healthy, error_message, response_time_seconds).
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
        # Any response (even error) means the gateway is alive
        return True, None, round(elapsed, 3)
    except urllib.error.HTTPError as e:
        elapsed = time.time() - start
        body = e.read().decode("utf-8", errors="replace")[:200]
        return True, f"HTTP {e.code}: {body}", round(elapsed, 3)
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
            "profile": profile["hermes_profile"],
            "port": profile["port"],
            "model": profile["model"],
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
            "port": p["port"],
            "model": p["model"],
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
