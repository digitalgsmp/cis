# Gateway API Key Discovery

## Problem

pipeline_relay.py's `_call_agent()` originally used `os.environ.get(f"CIS_{role.upper()}_API_KEY")` to find gateway auth keys. These env vars are never set in the runtime environment. Result: every gateway call returns `401 Unauthorized`.

## Where Gateway Keys Actually Live

Each Hermes gateway stores its API server key in **two** possible locations:

1. **`~/.{hermes_profile}/.env`** — contains `API_SERVER_KEY=<key>` (primary source, always present)
2. **`config.yaml` `api_server.api_key`** field — sometimes set, sometimes not

### Key locations per profile (verified 2026-07-08)

| Role | Profile | Port | Key Location | Key Prefix |
|------|---------|------|-------------|------------|
| brain | hermes-brainstorm | 8644 | .env + config.yaml | `6b7aab08...` |
| draft | hermes-v4pro | 8645 | .env + config.yaml | `6b7aab08...` |
| review1 | hermes-r1 | 8643 | .env + config.yaml | `f0a78f4d...` |
| review2 | hermes-glm-reviewer | 8647 | .env + config.yaml | `f0a78f4d...` |
| menter | hermes-v4impl | 8646 | .env ONLY (not in config.yaml) | `j3cY50CQ...` |
| verify | hermes-glm-verifier | 8648 | .env + config.yaml | `f0a78f4d...` |

**Menter (8646) is the outlier** — its `config.yaml` has no `api_key` field under `api_server`, only the `.env` file has the key.

## The `_resolve_api_key()` Solution

Added to `pipeline_relay.py` before `_call_agent()`:

```python
def _resolve_api_key(role: str) -> str:
    """Priority:
    1. CIS_{ROLE}_API_KEY env var (explicit override)
    2. API_SERVER_KEY from ~/.{hermes_profile}/.env
    3. api_key from ~/.{hermes_profile}/config.yaml api_server section
    4. Empty string (auth disabled)
    """
    # 1. Explicit env var
    env_key = os.environ.get(f"CIS_{role.upper()}_API_KEY", "")
    if env_key:
        return env_key

    # 2. Read from gateway .env file
    profile = PROFILES.get(role, {})
    hermes_profile = profile.get("hermes_profile", "")
    if hermes_profile:
        env_path = os.path.expanduser(f"~/.{hermes_profile}/.env")
        if os.path.exists(env_path):
            try:
                with open(env_path) as f:
                    for line in f:
                        if line.strip().startswith("API_SERVER_KEY="):
                            return line.split("=", 1)[1].strip()
            except Exception:
                pass

        # 3. Read from config.yaml
        cfg_path = os.path.expanduser(f"~/.{hermes_profile}/config.yaml")
        if os.path.exists(cfg_path):
            try:
                import yaml
                with open(cfg_path) as f:
                    cfg = yaml.safe_load(f) or {}
                key = cfg.get("api_server", {}).get("api_key", "")
                if key:
                    return key
            except Exception:
                pass

    return ""
```

## How Hermes Gateway Auth Works

From `/home/eric/.hermes/hermes-agent/gateway/platforms/api_server.py`:

- `self._api_key = extra.get("key", os.getenv("API_SERVER_KEY", ""))` (line 750)
- The `extra` dict comes from `PlatformConfig.extra` which is populated from `platforms.api_server.extra` in config.yaml
- The `_apply_env_overrides()` function in `gateway/config.py` (line 1652) sets `config.platforms[Platform.API_SERVER].extra["key"]` from `API_SERVER_KEY` env var
- If no key is set, `connect()` refuses to start the API server (line 4223)
- Auth check: `hmac.compare_digest(token, self._api_key)` — constant-time comparison

## Verifying Gateway Auth

```bash
# Quick check — all 6 gateways
for port in 8643 8644 8645 8646 8647 8648; do
  echo -n "Port $port: "
  curl -s --connect-timeout 2 http://127.0.0.1:$port/v1/models \
    -H "Authorization: Bearer <key>" | head -c 80
  echo
done
```

A successful auth returns `{"data": [...]}` (possibly empty data array).
A failed auth returns `{"error": {"message": "Invalid API key", ...}}`.
