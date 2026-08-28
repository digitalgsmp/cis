# Gateway Stale Process Diagnosis

## The Problem

When a Hermes gateway systemd service crashes (OOM, segfault, config error),
the old PID can keep serving on the port. The gateway appears "healthy" because
the port accepts connections, but every API call returns an empty string.

This is a **recurring pattern** on creative-vm — it has happened to:
- Review1 (8643, `hermes-gateway-r1.service`) — 2026-07-08
- Verify (8648, `hermes-gateway-glm-verifier.service`) — 2026-07-08 (2 days prior)
- Menter (8646, `hermes-v4impl` service) — 2026-07-08

## Symptoms

1. Agent trajectories show `output_text=""` (empty string, not NULL)
2. `systemctl --user status <service>` shows `Active: failed (failed)`
3. `ss -tlnp | grep <port>` shows the port is still LISTEN with an old PID
4. `curl` to the gateway returns empty 200 response
5. Pipeline logs show "review incomplete" or "returned empty output" (post-fix)

## Root Cause Fix (commit bafca21)

The pipeline now **detects and refuses to use** zombie gateways:

### `check_gateway()` — content validation
```python
# Parses JSON response, validates choices array exists,
# checks content/reasoning_content is non-empty.
# 401 = healthy (auth required, process alive)
# Empty 200 = unhealthy (zombie)
# Other HTTP errors = unhealthy
```

### `_call_agent()` — raises on empty response
```python
if not choices:
    _breaker_record_failure(role)
    raise ConnectionError("no choices — zombie process")
if not content.strip():
    _breaker_record_failure(role)
    raise ConnectionError("empty content — model backend not working")
_breaker_record_success(role)  # only after content validated
```

### `_call_reviewers_parallel()` — retry on empty
```python
# Retries once on empty/ambiguous output before returning
# If still empty after retry, returns with error set
# Caller escalates as "incomplete" — not objection, not consensus
```

The circuit breaker now properly trips after 3 consecutive broken responses
(was: never tripped because successes were recorded on empty responses).

## Manual Diagnosis (when pipeline escalates with "incomplete")

```bash
# 1. Check if the service is actually running
systemctl --user status hermes-gateway-r1.service

# 2. Check if the port is still serving (stale PID)
ss -tlnp | grep 8643

# 3. Compare: service "failed" + port LISTEN = stale process

# 4. Test the gateway directly
API_KEY=$(grep API_SERVER_KEY ~/.hermes-r1/.env | cut -d= -f2)
curl -s -X POST http://127.0.0.1:8643/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{"model":"ping","messages":[{"role":"user","content":"ping"}],"max_tokens":5}' \
  --max-time 15
# Empty response = stale process confirmed
```

## Manual Fix

```bash
kill $(lsof -ti :8643)
sleep 2
systemctl --user restart hermes-gateway-r1.service
sleep 3
# Verify with actual content call (not just port check)
API_KEY=$(grep API_SERVER_KEY ~/.hermes-r1/.env | cut -d= -f2)
curl -s -X POST http://127.0.0.1:8643/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{"model":"ping","messages":[{"role":"user","content":"Say hello"}],"max_tokens":10}' \
  --max-time 30
```

## Service Name Mapping

| Role | Port | Service Name | Hermes Home |
|------|------|-------------|-------------|
| Brain | 8644 | `hermes-gateway-brainstorm.service` | `~/.hermes-brainstorm` |
| Draft | 8645 | `hermes-gateway-v4pro.service` | `~/.hermes-v4pro` |
| Review1 | 8643 | `hermes-gateway-r1.service` | `~/.hermes-r1` |
| Review2 | 8647 | `hermes-gateway-glm-reviewer.service` | `~/.hermes-glm-reviewer` |
| Menter | 8646 | `hermes-gateway-v4impl.service` | `~/.hermes-v4impl` |
| Verify | 8648 | `hermes-gateway-glm-verifier.service` | `~/.hermes-glm-verifier` |

## What the Pipeline Can't Fix

The systemd issue itself — stale processes holding ports after service crash.
That needs either:
- `ExecStartPre` in the service file that kills anything on the port before start
- Or `KillMode=control-group` so systemd kills all children on stop

But the pipeline now **detects** the problem and refuses to use a broken gateway,
escalating to Eric instead of silently producing garbage.
