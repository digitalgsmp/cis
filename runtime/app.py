#!/usr/bin/env python3
"""
DEPRECATED — DO NOT RUN. This file was the pre-container host-side Flask app.
It shadows the Docker container's port 5000 mapping (127.0.0.1:5000 beats
0.0.0.0:5000 on Linux), causing all container API requests to be intercepted
by this process instead of the container. Use the container instead:

    cd /mnt/projects/cis/enforcement/mwl-proof-v2
    ./run_container.sh -d

If you need to run this for debugging, bind to a different port:
    python3 runtime/app.py  # DO NOT — use port 5001 instead, edit below

This file is preserved for reference only. The production entry point is
container_app.py inside the cis-hermes:pipeline Docker container.
"""
import sys
print("ERROR: runtime/app.py is deprecated. Use the Docker container instead.", file=sys.stderr)
print("  cd /mnt/projects/cis/enforcement/mwl-proof-v2 && ./run_container.sh -d", file=sys.stderr)
sys.exit(1)

# TODO: Legacy inline pipeline relay code at lines 794-917 (PIPELINE_RUNS dict,
# portal_pipeline_start, portal_pipeline_status) should be consolidated into
# api/relay.py or removed — the production relay blueprint at api/relay.py
# already handles intent submission, status polling, gates, and verification.

from flask import Flask, jsonify, send_from_directory, request
from datetime import datetime, timezone
import os
import sys

# Ensure runtime dir is in path for config and API blueprints
RUNTIME_DIR = os.path.dirname(os.path.abspath(__file__))
if RUNTIME_DIR not in sys.path:
    sys.path.insert(0, RUNTIME_DIR)

from config import RUNTIME_DIR

# ── Blueprint imports ──────────────────────────────────────────────────────────
from api.system          import system_bp
from api.projects        import projects_bp
from api.session         import session_bp
from api.tasks           import tasks_bp
from api.pipeline        import pipeline_bp
from api.records         import records_bp
from api.captures        import captures_bp
from api.decisions       import decisions_bp
from api.extraction_runs import extraction_runs_bp
from api.live            import live_bp
from api.models          import models_bp
from api.operator        import operator_bp          # ADR-044
from api.queue           import queue_bp             # ADR-045
from api.drafts import drafts_bp
from api.gpt import gpt_bp
from api.spines_api import spines_bp
from api.ingest_spines import ingest_spines_bp
from api.idea_uploads import idea_uploads_bp
from api.app_api import app_bp
from api.lms_api import lms_bp
from api.collab import collab_bp
from api.collab_rounds import collab_rounds_bp
from api.advisor import advisor_bp
from api.reconciliation import reconciliation_bp
from api.idea_drafts import idea_drafts_bp
from api.advisor_external import advisor_external_bp
from api.intent import intent_bp
from api.adapter import adapter_bp
from api.dam import dam_bp
from api.pipeline_views import pipeline_views_bp
from api.relay import relay_bp
from api.dashboard_api import dashboard_bp
from cis_ingest import create_api_blueprint


# ── Worker import ──────────────────────────────────────────────────────────────
from queue_worker import start_worker, worker_status  # ADR-045

# ── Memory system ─────────────────────────────────────────────────────────────
from memory.memory_store import MemoryStore
memory_store = MemoryStore()
memory_store.ensure_tables()

# ── Initialize app database ────────────────────────────────────────────────────
from cis_db import init_db
init_db()


# ── App init ───────────────────────────────────────────────────────────────────
app = Flask(__name__, static_folder=None)

CIS_API_KEY = os.environ.get("CIS_API_KEY", "ff239b9b04b514b8bc57f166f0eebd8a6a67022575f7886c027b27728e53e6fd")

@app.before_request
def check_api_key():
    if request.path.startswith("/api/"):
        if request.remote_addr in ("127.0.0.1", "::1"):
            return None
        key = request.headers.get("X-CIS-API-Key")
        if key == CIS_API_KEY:
            return None
        return jsonify({"error": "Unauthorized"}), 401
    return None

# ── Register blueprints ────────────────────────────────────────────────────────
app.register_blueprint(system_bp)
app.register_blueprint(projects_bp)
app.register_blueprint(session_bp)
app.register_blueprint(tasks_bp)
app.register_blueprint(pipeline_bp)
app.register_blueprint(records_bp)
app.register_blueprint(captures_bp)
app.register_blueprint(decisions_bp)
app.register_blueprint(extraction_runs_bp)
app.register_blueprint(live_bp)
app.register_blueprint(models_bp)
app.register_blueprint(operator_bp)                 # ADR-044
app.register_blueprint(queue_bp)                    # ADR-045
app.register_blueprint(drafts_bp)
app.register_blueprint(gpt_bp)
app.register_blueprint(spines_bp)
app.register_blueprint(ingest_spines_bp)
app.register_blueprint(idea_uploads_bp)
app.register_blueprint(app_bp)
app.register_blueprint(lms_bp)
app.register_blueprint(collab_bp)
app.register_blueprint(collab_rounds_bp)

# ── Ingestion API ─────────────────────────────────────────────────────────
ingest_bp = create_api_blueprint()
app.register_blueprint(ingest_bp)
app.register_blueprint(advisor_bp)
app.register_blueprint(reconciliation_bp)
app.register_blueprint(idea_drafts_bp)
app.register_blueprint(advisor_external_bp)
app.register_blueprint(intent_bp)
app.register_blueprint(adapter_bp)
app.register_blueprint(dam_bp)
app.register_blueprint(pipeline_views_bp)          # Tier 10 — CIS UI
app.register_blueprint(relay_bp)                # Pipeline relay API (production)
app.register_blueprint(dashboard_bp)              # Tier 11A — Dashboard

# ── Worker status route ────────────────────────────────────────────────────────

@app.route("/api/queue/worker-status")
def api_worker_status():
    """Return current queue worker state. Used by dashboard polling."""
    return jsonify(worker_status())

# ── Health check endpoint ──────────────────────────────────────────────────────

@app.route("/api/health")
def api_health():
    """Return service health status — no database dependency."""
    return jsonify({
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

# ── Archive file server (before SPA catch-all) ─────────────────────────────────

import mimetypes as _mime
import os as _os
from flask import send_file as _send_file

ARCHIVE_ROOTS = ["/mnt/archive", "/mnt/projects"]

@app.route("/api/archive-file")
def serve_archive_file():
    file_path = request.args.get("path", "")
    if not file_path:
        return jsonify({"error": "path required"}), 400
    resolved = _os.path.abspath(file_path)
    allowed = any(resolved.startswith(_os.path.abspath(r)) for r in ARCHIVE_ROOTS)
    if not allowed:
        return jsonify({"error": "Access denied"}), 403
    if not _os.path.isfile(resolved):
        return jsonify({"error": "Not found"}), 404
    mtype, _ = _mime.guess_type(resolved)
    return _send_file(resolved, mimetype=mtype or "application/octet-stream")

# ── CIS Control Portal ──────────────────────────────────────────────────

@app.route("/portal")
def cis_portal():
    """Serve the CIS Control Portal — standalone control plane UI."""
    portal_path = RUNTIME_DIR / "ui" / "public" / "portal.html"
    if portal_path.exists():
        return portal_path.read_text(encoding="utf-8"), 200, {"Content-Type": "text/html; charset=utf-8"}
    return "Portal not found", 404


@app.route("/monitor-test")
def monitor_test():
    """Simple standalone monitor test page."""
    test_path = RUNTIME_DIR / "ui" / "public" / "monitor-test.html"
    if test_path.exists():
        return test_path.read_text(encoding="utf-8"), 200, {"Content-Type": "text/html; charset=utf-8"}
    return "Test page not found", 404


@app.route("/roadmap-live")
def roadmap_live():
    """Standalone roadmap page with live monitor — bypasses portal CSS issues."""
    rl_path = RUNTIME_DIR / "ui" / "public" / "roadmap-live.html"
    if rl_path.exists():
        return rl_path.read_text(encoding="utf-8"), 200, {"Content-Type": "text/html; charset=utf-8"}
    return "Roadmap page not found", 404


@app.route("/api/portal/submit-intent", methods=["POST"])
def portal_submit_intent():
    """Portal intent submission — bypasses API key auth (internal page)."""
    import json as _json
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or data.get("intent") or "").strip()
    if not message:
        return _json.dumps({"error": "No intent provided"}), 400, {"Content-Type": "application/json"}

    # Build a sub-request to /api/advisor/route with the CIS API key
    from flask import current_app
    cis_key = os.environ.get("CIS_API_KEY",
        "ff239b9b04b514b8bc57f166f0eebd8a6a67022575f7886c027b27728e53e6fd")
    import urllib.request as _ur
    import urllib.error as _ue

    payload = _json.dumps({
        "message": message,
        "source_actor": "eric",
        "classify_only": False,
    }).encode("utf-8")

    # Call the advisor route internally (same process, via http so we get the full response)
    try:
        req = _ur.Request(
            "http://127.0.0.1:5000/api/advisor/route",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "X-CIS-API-Key": cis_key,
            },
        )
        resp = _ur.urlopen(req, timeout=300)
        body = _json.loads(resp.read().decode("utf-8"))
        return _json.dumps(body), 200, {"Content-Type": "application/json"}
    except _ue.HTTPError as e:
        err = e.read().decode("utf-8", errors="replace")
        return _json.dumps({"error": f"Pipeline error: {err[:500]}"}), 500, {"Content-Type": "application/json"}
    except Exception as e:
        return _json.dumps({"error": str(e)}), 500, {"Content-Type": "application/json"}


@app.route("/api/portal/run-deliberation", methods=["POST"])
def portal_run_deliberation():
    """Run the reviewer reconciliation engine and return results."""
    import json as _json
    import subprocess, tempfile

    data = request.get_json(silent=True) or {}
    proposal = (data.get("proposal") or "").strip()
    run_id = (data.get("run_id") or "").strip()

    if not proposal:
        return _json.dumps({"error": "No proposal provided"}), 400, {"Content-Type": "application/json"}

    # Write proposal to temp file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write(proposal)
        tmp_path = f.name

    try:
        env = os.environ.copy()
        env.setdefault("CIS_SPINE_PATH", "/mnt/projects/cis/data/cis_memory.db")
        # Source runtime.env for API keys
        runtime_env = "/mnt/projects/cis/runtime/config/runtime.env"
        if os.path.exists(runtime_env):
            with open(runtime_env) as ef:
                for line in ef:
                    line = line.strip()
                    if line.startswith("export ") and "=" in line:
                        k, v = line[7:].split("=", 1)
                        env[k] = v.strip('"').strip("'")
        result = subprocess.run(
            ["python3", "tools/pipeline/reviewer_reconcile.py",
             "--proposal-file", tmp_path, "--max-rounds", "2", "--no-escalate"],
            capture_output=True, text=True, timeout=300,
            cwd="/mnt/projects/cis", env=env,
        )
        stdout = result.stdout
        stderr = result.stderr

        # Parse the JSON from the last JSON object in output
        try:
            # Find the FINAL RESULT JSON block
            lines = stdout.split("\n")
            json_start = None
            for i, line in enumerate(lines):
                if "═══ FINAL RESULT ═══" in line:
                    json_start = i + 1
                    break
            if json_start:
                final_json = _json.loads("\n".join(lines[json_start:]))
            else:
                final_json = {"status": "ERROR", "output": stdout[-2000:]}
        except Exception:
            final_json = {"status": "ERROR", "output": stdout[-1000:]}

        # Extract reviewer responses from the verbose output
        reviewers = {}
        current_reviewer = None
        for line in stdout.split("\n"):
            if "verdict:" in line.lower() and ":" in line:
                parts = line.split("verdict:", 1)
                reviewer_name = parts[0].strip().lower()
                verdict = parts[1].strip()
                if "r1" in reviewer_name:
                    reviewers["r1_resp"] = {"verdict": {"status": verdict}}
                elif "qwen" in reviewer_name:
                    reviewers["qwen_resp"] = {"verdict": {"status": verdict}}
                elif "glm" in reviewer_name:
                    reviewers["glm_resp"] = {"verdict": {"status": verdict}}
                elif "deepseek" in reviewer_name or "reasoner" in reviewer_name:
                    reviewers["dsr1_resp"] = {"verdict": {"status": verdict}}

        final_json["reviewers"] = reviewers
        if stderr and "Traceback" not in stderr:
            final_json["warnings"] = stderr[:500]
        return _json.dumps(final_json), 200, {"Content-Type": "application/json"}

    except subprocess.TimeoutExpired:
        return _json.dumps({"status": "TIMEOUT", "error": "Deliberation timed out after 5 minutes"}), 504, {"Content-Type": "application/json"}
    except Exception as e:
        return _json.dumps({"status": "ERROR", "error": str(e)}), 500, {"Content-Type": "application/json"}
    finally:
        import os as _os
        try: _os.unlink(tmp_path)
        except: pass


@app.route("/api/portal/chat", methods=["POST"])
def portal_chat():
    """Chat with Hermes gateway — pipeline-aware.

    Prepends pipeline-awareness context. Scans response for engagement signal.
    Returns pipeline_action when the model detects intent requiring the pipeline.
    """
    import json as _json, uuid, urllib.request as _ur, urllib.error as _ue, re

    data = request.get_json(silent=True) or {}
    agent = (data.get("agent") or "").strip()
    message = (data.get("message") or "").strip()
    thread_id = data.get("thread_id") or str(uuid.uuid4())

    if not agent or not message:
        return _json.dumps({"error": "agent and message required"}), 400, {"Content-Type": "application/json"}

    cis_key = os.environ.get("CIS_API_KEY",
        "ff239b9b04b514b8bc57f166f0eebd8a6a67022575f7886c027b27728e53e6fd")

    # Pipeline-awareness context — only on first message of a new conversation
    pipeline_ctx = ""
    if not thread_id:
        pipeline_ctx = (
            "[CIS Portal: Pipeline is available. When Eric describes a task requiring "
            "design, planning, building, implementation, review, or research-backed decisions, "
            "FIRST restate what you understand, then ask if he wants to engage the pipeline. "
            "If Eric confirms, include EXACTLY '||PIPELINE_ENGAGE||' in your response.]\n\n"
        )
    augmented_message = pipeline_ctx + message

    payload = _json.dumps({
        "agent": agent,
        "thread_id": thread_id,
        "content": augmented_message,
    }).encode("utf-8")

    try:
        req = _ur.Request(
            "http://127.0.0.1:5000/api/advisor/chat",
            data=payload,
            headers={"Content-Type": "application/json", "X-CIS-API-Key": cis_key},
        )
        resp = _ur.urlopen(req, timeout=300)
        body = _json.loads(resp.read().decode("utf-8"))

        # Check for pipeline engagement signal
        raw_response = body.get("content") or body.get("response") or ""
        pipeline_action = None
        if "||PIPELINE_ENGAGE||" in raw_response:
            pipeline_action = "engage"
            raw_response = raw_response.replace("||PIPELINE_ENGAGE||", "")

        result = {
            "thread_id": thread_id,
            "response": raw_response,
            "pipeline_action": pipeline_action,
        }

        # Context usage: estimate from augmented message + known history size
        try:
            import sqlite3 as _sql, traceback
            _db = _sql.connect("/mnt/projects/cis/runtime/db/cis_memory.db")
            _rows = _db.execute(
                "SELECT SUM(LENGTH(content)) FROM advisor_messages WHERE thread_id=?",
                (thread_id,)
            ).fetchone()
            _total = (_rows[0] or 0) + len(augmented_message)
            _db.close()
            _limit = {
                "hermes-v4pro":  1048576,  # DeepSeek V4 Pro: 1M
                "hermes-r1":      163840,  # DeepSeek R1: 160K
                "hermes-v4impl": 1048576,  # DeepSeek V4 Pro: 1M
                "hermes-prime":  1048576,  # DeepSeek V4 Flash: 1M
                "hermes-qwen":     32768,  # Qwen local: 32K
            }.get(agent, 128000)
            result["context_chars"] = _total
            result["context_limit"] = _limit
            result["context_pct"] = round(min(100, _total / _limit * 100), 1)
        except Exception as e:
            result["context_error"] = str(e)[:100]

        return _json.dumps(result), 200, {"Content-Type": "application/json"}
    except _ue.HTTPError as e:
        err = e.read().decode("utf-8", errors="replace")
        return _json.dumps({"error": f"Chat error: {err[:500]}", "thread_id": thread_id}), 500, {"Content-Type": "application/json"}
    except Exception as e:
        return _json.dumps({"error": str(e), "thread_id": thread_id}), 500, {"Content-Type": "application/json"}


# ── Direct Chat (no Hermes gateway) ──────────────────────────────────────
#
# Models that bypass Hermes entirely:
#   qwen       → llama-server on port 8002 (OpenAI-compatible API)
#   glm        → OpenRouter API (model: z-ai/glm-5.2-128k)
#   ds-reasoner→ DeepSeek API (model: deepseek-reasoner, reasoning enabled)

DIRECT_CHAT_CONFIG = {
    "qwen": {
        "url": "http://127.0.0.1:8002/v1/chat/completions",
        "model": "qwen3-vl-30b-a3b-instruct-q4_k_m.gguf",
        "label": "Qwen (local, no Hermes)",
        "key_env": None,
        "max_tokens": 2000,
        "api_type": "openai",
    },
    "glm": {
        "url": "http://127.0.0.1:8003/v1/chat/completions",
        "model": "GLM-4.7-Flash-Q4_K_M.gguf",
        "label": "GLM 4.7 Flash (local)",
        "key_env": None,
        "max_tokens": 4000,
        "api_type": "openai",
    },
    "ds-reasoner": {
        "url": "https://api.deepseek.com/v1/chat/completions",
        "model": "deepseek-reasoner",
        "label": "DeepSeek Reasoner (API)",
        "key_env": "DEEPSEEK_API_KEY",
        "max_tokens": 4000,
        "api_type": "deepseek",
    },
    "qwen-max": {
        "url": "https://openrouter.ai/api/v1/chat/completions",
        "model": "qwen/qwen3.6-max-preview",
        "label": "Qwen3.6 Max (OpenRouter)",
        "key_env": "OPENROUTER_API_KEY",
        "max_tokens": 4000,
        "api_type": "openrouter",
    },
    "claude-opus": {
        "url": "https://api.anthropic.com/v1/messages",
        "model": "claude-opus-4-8",
        "label": "Claude Opus 4.8 (Anthropic API)",
        "key_env": "ANTHROPIC_API_KEY",
        "max_tokens": 4000,
        "api_type": "anthropic",
    },
    "glm-5.2": {
        "url": "https://openrouter.ai/api/v1/chat/completions",
        "model": "z-ai/glm-5.2",
        "label": "GLM 5.2 (OpenRouter)",
        "key_env": "OPENROUTER_API_KEY",
        "max_tokens": 4000,
        "api_type": "openrouter",
    },
    # ── Free models via OpenRouter (for bulk tagging/inference) ──────────
    "qwen3-next-80b": {
        "url": "https://openrouter.ai/api/v1/chat/completions",
        "model": "qwen/qwen3-next-80b-a3b-instruct:free",
        "label": "Qwen3 Next 80B (OpenRouter, free)",
        "key_env": "OPENROUTER_API_KEY",
        "max_tokens": 8000,
        "api_type": "openrouter",
    },
    "hermes-405b": {
        "url": "https://openrouter.ai/api/v1/chat/completions",
        "model": "nousresearch/hermes-3-llama-3.1-405b:free",
        "label": "Hermes 3 405B (OpenRouter, free)",
        "key_env": "OPENROUTER_API_KEY",
        "max_tokens": 8000,
        "api_type": "openrouter",
    },
    "llama-70b": {
        "url": "https://openrouter.ai/api/v1/chat/completions",
        "model": "meta-llama/llama-3.3-70b-instruct:free",
        "label": "Llama 3.3 70B (OpenRouter, free)",
        "key_env": "OPENROUTER_API_KEY",
        "max_tokens": 8000,
        "api_type": "openrouter",
    },
    "gemma-31b": {
        "url": "https://openrouter.ai/api/v1/chat/completions",
        "model": "google/gemma-4-31b-it:free",
        "label": "Gemma 4 31B (OpenRouter, free)",
        "key_env": "OPENROUTER_API_KEY",
        "max_tokens": 8000,
        "api_type": "openrouter",
    },
    "mistral-large": {
        "url": "https://openrouter.ai/api/v1/chat/completions",
        "model": "mistralai/mistral-large-2512",
        "label": "Mistral Large 3 (OpenRouter)",
        "key_env": "OPENROUTER_API_KEY",
        "max_tokens": 4000,
        "api_type": "openrouter",
    },
}


def _call_direct_chat(model_key, messages, max_tokens=None):
    """Call a model directly — no Hermes gateway interception.

    Handles three API types:
      - openai/openrouter/deepseek: OpenAI-compatible chat/completions
      - anthropic: Anthropic Messages API (different request/response format)
    """
    import json as _json, urllib.request as _ur, urllib.error as _ue

    cfg = DIRECT_CHAT_CONFIG.get(model_key)
    if not cfg:
        raise ValueError(f"Unknown direct model: {model_key}")

    api_type = cfg.get("api_type", "openai")
    api_key = None

    if cfg["key_env"]:
        api_key = os.environ.get(cfg["key_env"])
        if not api_key:
            runtime_env = "/mnt/projects/cis/runtime/config/runtime.env"
            if os.path.exists(runtime_env):
                with open(runtime_env) as ef:
                    for line in ef:
                        line = line.strip()
                        if line.startswith("export ") and "=" in line:
                            k, v = line[7:].split("=", 1)
                            if k == cfg["key_env"]:
                                api_key = v.strip('"').strip("'")
                                break
        if not api_key:
            raise ValueError(f"API key {cfg['key_env']} not found for {model_key}")

    # ── Anthropic Messages API ──────────────────────────────────────
    if api_type == "anthropic":
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        # Convert OpenAI-format messages to Anthropic format
        anthropic_messages = []
        system_content = ""
        for m in messages:
            role = m.get("role", "user")
            content = m.get("content", "")
            if role == "system":
                system_content += content + "\n"
            else:
                anthropic_messages.append({"role": role, "content": content})

        body = {
            "model": cfg["model"],
            "max_tokens": max_tokens or cfg["max_tokens"],
            "messages": anthropic_messages,
        }
        if system_content.strip():
            body["system"] = system_content.strip()

        req = _ur.Request(cfg["url"], data=_json.dumps(body).encode("utf-8"), headers=headers)

        try:
            resp = _ur.urlopen(req, timeout=300)
            raw = _json.loads(resp.read().decode("utf-8"))
        except _ue.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Claude HTTP {e.code}: {err_body[:500]}")

        # Anthropic response: content is an array of blocks
        content_blocks = raw.get("content", [])
        text = ""
        for block in content_blocks:
            if block.get("type") == "text":
                text += block.get("text", "")
        # Thinking blocks (extended thinking)
        reasoning = ""
        for block in content_blocks:
            if block.get("type") == "thinking":
                reasoning += block.get("thinking", "")

        return {
            "content": text,
            "reasoning": reasoning,
            "model": raw.get("model", cfg["model"]),
            "usage": raw.get("usage", {}),
        }

    # ── OpenAI-compatible APIs (OpenRouter, DeepSeek, local Qwen) ───
    headers = {"Content-Type": "application/json"}
    if api_key:
        if api_type == "openrouter":
            headers["Authorization"] = f"Bearer {api_key}"
            headers["HTTP-Referer"] = "http://127.0.0.1:5000/portal"
            headers["X-Title"] = "CIS Portal Direct Chat"
        else:
            headers["Authorization"] = f"Bearer {api_key}"

    body = {
        "model": cfg["model"],
        "messages": messages,
        "max_tokens": max_tokens or cfg["max_tokens"],
        "temperature": 0.7,
    }

    if api_type == "deepseek":
        body["thinking"] = {"type": "enabled"}

    if api_type == "openai" and api_key is None:
        # Local llama-server — no auth header needed
        pass

    req = _ur.Request(cfg["url"], data=_json.dumps(body).encode("utf-8"), headers=headers)

    try:
        resp = _ur.urlopen(req, timeout=300)
        raw = _json.loads(resp.read().decode("utf-8"))
    except _ue.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Direct chat HTTP {e.code}: {err_body[:500]}")

    choices = raw.get("choices", [])
    if not choices:
        raise RuntimeError(f"No choices in response: {_json.dumps(raw)[:500]}")

    msg = choices[0].get("message", {})
    content = msg.get("content", "") or ""
    reasoning = msg.get("reasoning_content", "") or msg.get("reasoning", "") or ""

    return {
        "content": content,
        "reasoning": reasoning,
        "model": raw.get("model", cfg["model"]),
        "usage": raw.get("usage", {}),
    }


@app.route("/api/portal/chat-direct", methods=["POST"])
def portal_chat_direct():
    """Direct chat with models OUTSIDE Hermes gateways — Qwen, GLM, DeepSeek Reasoner."""
    import json as _json, uuid

    data = request.get_json(silent=True) or {}
    model_key = (data.get("model") or "").strip()
    message = (data.get("message") or "").strip()
    thread_id = data.get("thread_id") or str(uuid.uuid4())
    history = data.get("history") or []  # [{role, content}, ...]

    if not model_key or not message:
        return _json.dumps({"error": "model and message required"}), 400, {"Content-Type": "application/json"}

    if model_key not in DIRECT_CHAT_CONFIG:
        return _json.dumps({"error": f"Unknown model: {model_key}. Use: qwen, glm, ds-reasoner"}), 400, {"Content-Type": "application/json"}

    # Build messages: history + current user message
    messages = list(history)
    messages.append({"role": "user", "content": message})

    try:
        result = _call_direct_chat(model_key, messages)
        return _json.dumps({
            "thread_id": thread_id,
            "model": model_key,
            "label": DIRECT_CHAT_CONFIG[model_key]["label"],
            "response": result["content"],
            "reasoning": result["reasoning"],
        }), 200, {"Content-Type": "application/json"}
    except Exception as e:
        return _json.dumps({"error": str(e), "thread_id": thread_id}), 500, {"Content-Type": "application/json"}


@app.route("/api/portal/chat-group", methods=["POST"])
def portal_chat_group():
    """Group chat with adversarial observer pattern.

    Flow:
    1. Primary model receives user message → responds
    2. Observer models receive [user message + primary response] → challenge/verify
    3. All responses returned together
    """
    import json as _json, uuid, urllib.request as _ur, urllib.error as _ue

    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    primary = (data.get("primary") or "").strip()       # model_key or agent
    observers = data.get("observers") or []              # list of model_keys or agents
    mode = (data.get("mode") or "observer").strip()      # "observer" or "parallel"

    if not message or not primary:
        return _json.dumps({"error": "message and primary required"}), 400, {"Content-Type": "application/json"}

    results = {}

    # ── Step 1: Primary responds ──────────────────────────────────────
    primary_direct = primary in DIRECT_CHAT_CONFIG

    if primary_direct:
        try:
            r = _call_direct_chat(primary, [{"role": "user", "content": message}])
            results["primary"] = {
                "model": primary,
                "label": DIRECT_CHAT_CONFIG[primary]["label"],
                "response": r["content"],
                "reasoning": r.get("reasoning", ""),
                "direct": True,
            }
        except Exception as e:
            results["primary"] = {"model": primary, "error": str(e), "direct": True}
    else:
        # Hermes gateway model
        cis_key = os.environ.get("CIS_API_KEY",
            "ff239b9b04b514b8bc57f166f0eebd8a6a67022575f7886c027b27728e53e6fd")
        try:
            payload = _json.dumps({
                "agent": primary,
                "thread_id": str(uuid.uuid4()),
                "content": message,
            }).encode("utf-8")
            req = _ur.Request(
                "http://127.0.0.1:5000/api/advisor/chat",
                data=payload,
                headers={"Content-Type": "application/json", "X-CIS-API-Key": cis_key},
            )
            resp = _ur.urlopen(req, timeout=300)
            body = _json.loads(resp.read().decode("utf-8"))
            results["primary"] = {
                "model": primary,
                "label": primary,
                "response": body.get("content") or body.get("response") or str(body),
                "direct": False,
            }
        except Exception as e:
            results["primary"] = {"model": primary, "error": str(e), "direct": False}

    primary_response = results["primary"].get("response", "")

    # ── Step 2: If parallel mode, send to observers with ORIGINAL message only ──
    #    If observer mode, send to observers with original message + primary response

    if mode == "parallel":
        observer_prompt = message
    else:
        observer_prompt = (
            f"USER MESSAGE:\n{message}\n\n"
            f"PRIMARY MODEL ({primary}) RESPONDED:\n{primary_response}\n\n"
            f"You are an ADVERSARIAL OBSERVER. Review the primary model's response critically. "
            f"Do you see errors, omissions, questionable claims, or violations of CIS conventions? "
            f"If the response is correct, say so concisely. If you find issues, state them clearly."
        )

    for obs in (observers or []):
        obs_direct = obs in DIRECT_CHAT_CONFIG

        if obs_direct:
            try:
                r = _call_direct_chat(obs, [{"role": "user", "content": observer_prompt}])
                results[obs] = {
                    "model": obs,
                    "label": DIRECT_CHAT_CONFIG[obs]["label"],
                    "response": r["content"],
                    "reasoning": r.get("reasoning", ""),
                    "direct": True,
                    "role": "observer",
                }
            except Exception as e:
                results[obs] = {"model": obs, "error": str(e), "direct": True, "role": "observer"}
        else:
            cis_key = os.environ.get("CIS_API_KEY",
                "ff239b9b04b514b8bc57f166f0eebd8a6a67022575f7886c027b27728e53e6fd")
            try:
                payload = _json.dumps({
                    "agent": obs,
                    "thread_id": str(uuid.uuid4()),
                    "content": observer_prompt,
                }).encode("utf-8")
                req = _ur.Request(
                    "http://127.0.0.1:5000/api/advisor/chat",
                    data=payload,
                    headers={"Content-Type": "application/json", "X-CIS-API-Key": cis_key},
                )
                resp = _ur.urlopen(req, timeout=300)
                body = _json.loads(resp.read().decode("utf-8"))
                results[obs] = {
                    "model": obs,
                    "label": obs,
                    "response": body.get("content") or body.get("response") or str(body),
                    "direct": False,
                    "role": "observer",
                }
            except Exception as e:
                results[obs] = {"model": obs, "error": str(e), "direct": False, "role": "observer"}

    return _json.dumps({"mode": mode, "primary": primary, "results": results}), 200, {"Content-Type": "application/json"}


# ── Pipeline Trigger Endpoints ──────────────────────────────────────────

PIPELINE_RUNS = {}  # run_id → {status, stages, ...} — in-memory for now


@app.route("/api/portal/pipeline/start", methods=["POST"])
def portal_pipeline_start():
    """Trigger the CIS pipeline from the portal with the conversation context.

    Creates workflow_run via drafter_start.py, fires pipeline_dispatch.sh,
    returns run_id for status polling.
    """
    import json as _json, subprocess, tempfile, threading

    data = request.get_json(silent=True) or {}
    intent = (data.get("intent") or "").strip()
    topic = (data.get("topic") or intent or "").strip()

    if not intent:
        return _json.dumps({"error": "intent required"}), 400, {"Content-Type": "application/json"}

    # Phase 1: Create workflow_run via drafter_start.py
    try:
        result = subprocess.run(
            ["python3", "tools/pipeline/drafter_start.py", topic, "--intent", intent],
            capture_output=True, text=True, timeout=30,
            cwd="/mnt/projects/cis",
        )
        stdout = result.stdout
        # Parse run_id from output
        run_id = None
        for line in stdout.split("\n"):
            if line.startswith("workflow_run_id:"):
                run_id = line.split(":", 1)[1].strip()
                break

        if not run_id:
            return _json.dumps({
                "error": "Failed to create workflow_run",
                "detail": stdout[-500:],
            }), 500, {"Content-Type": "application/json"}

        PIPELINE_RUNS[run_id] = {
            "status": "CREATED",
            "stages": {
                "staleness": "pending",
                "deliberation": "pending",
                "gates": "pending",
            },
            "proposal": intent[:200],
        }

    except Exception as e:
        return _json.dumps({"error": f"drafter_start.py failed: {str(e)}"}), 500, {"Content-Type": "application/json"}

    # Phase 2: Fire pipeline_dispatch.sh in background
    def _run_pipeline(run_id, topic, intent):
        import tempfile as _tmp
        proposal_file = None
        try:
            # Write proposal to temp file
            with _tmp.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
                f.write(f"{topic}\n\nIntent: {intent}")
                proposal_file = f.name

            PIPELINE_RUNS[run_id]["status"] = "RUNNING"
            PIPELINE_RUNS[run_id]["stages"]["staleness"] = "running"

            result = subprocess.run(
                ["bash", "tools/pipeline/pipeline_dispatch.sh", "--proposal", proposal_file],
                capture_output=True, text=True, timeout=300,
                cwd="/mnt/projects/cis",
            )

            # Parse results
            stdout = result.stdout
            if "CONSENSUS_REACHED" in stdout and "RESULT: BLOCKED" not in stdout:
                PIPELINE_RUNS[run_id]["status"] = "CONSENSUS_REACHED"
            elif "ESCALATE" in stdout:
                PIPELINE_RUNS[run_id]["status"] = "ESCALATE"
            else:
                PIPELINE_RUNS[run_id]["status"] = "BLOCKED"

            PIPELINE_RUNS[run_id]["stages"]["staleness"] = "FRESH" if "FRESH" in stdout else "unknown"
            PIPELINE_RUNS[run_id]["stages"]["deliberation"] = "done"
            PIPELINE_RUNS[run_id]["stdout"] = stdout[-3000:]
            PIPELINE_RUNS[run_id]["stderr"] = result.stderr[-1000:]

        except subprocess.TimeoutExpired:
            PIPELINE_RUNS[run_id]["status"] = "TIMEOUT"
        except Exception as e:
            PIPELINE_RUNS[run_id]["status"] = "ERROR"
            PIPELINE_RUNS[run_id]["error"] = str(e)
        finally:
            try:
                import os as _os
                if proposal_file:
                    _os.unlink(proposal_file)
            except:
                pass

    thread = threading.Thread(target=_run_pipeline, args=(run_id, topic, intent), daemon=True)
    thread.start()

    return _json.dumps({
        "run_id": run_id,
        "status": "RUNNING",
        "message": "Pipeline started. Poll /api/portal/pipeline/status for results.",
    }), 200, {"Content-Type": "application/json"}


@app.route("/api/portal/pipeline/status", methods=["GET"])
def portal_pipeline_status():
    """Poll pipeline status for a given run_id."""
    import json as _json

    run_id = request.args.get("run_id", "").strip()
    if not run_id:
        return _json.dumps({"error": "run_id required"}), 400, {"Content-Type": "application/json"}

    if run_id not in PIPELINE_RUNS:
        return _json.dumps({"error": f"Unknown run_id: {run_id}"}), 404, {"Content-Type": "application/json"}

    return _json.dumps(PIPELINE_RUNS[run_id]), 200, {"Content-Type": "application/json"}


# ── Portal Monitor: Live Gateway Health ────────────────────────────────────

GATEWAY_MONITORS = {
    "prime":     {"port": 8642, "label": "Prime (Flash/Research)",  "profile": "hermes-prime",   "model": "DeepSeek V4 Flash", "context": "1M"},
    "v4pro":     {"port": 8645, "label": "Drafter (V4 Pro)",         "profile": "hermes-v4pro",   "model": "DeepSeek V4 Pro",   "context": "1M"},
    "r1":        {"port": 8643, "label": "Reviewer (R1)",           "profile": "hermes-r1",      "model": "DeepSeek R1",       "context": "160K"},
    "v4impl":    {"port": 8646, "label": "Implementer",             "profile": "hermes-v4impl",  "model": "DeepSeek V4 Pro",   "context": "1M"},
    "qwen":      {"port": 8644, "label": "Qwen Gateway",            "profile": "hermes-qwen",    "model": "Qwen3-VL-30B",      "context": "32K"},
}
EXTRA_SERVICES = {
    "qwen-local":  {"port": 8002, "label": "Qwen llama-server",     "url": "http://127.0.0.1:8002/health"},
    "glm-local":   {"port": 8003, "label": "GLM 4.7 Flash (local)", "url": "http://127.0.0.1:8003/health"},
    "cis-flask":   {"port": 5000, "label": "CIS Flask App",         "url": "http://127.0.0.1:5000/api/system/health"},
}


@app.route("/api/portal/monitor")
def portal_monitor():
    """Live gateway and service health — used by portal monitor panel."""
    import json as _json, urllib.request as _ur, urllib.error as _ue, time as _time

    results = {"gateways": {}, "services": {}, "blockers": [], "next_actions": [], "timestamp": _time.time()}

    # ── Check Hermes gateways ──────────────────────────────────
    for gw_id, cfg in GATEWAY_MONITORS.items():
        url = f"http://127.0.0.1:{cfg['port']}/health"
        try:
            req = _ur.Request(url)
            resp = _ur.urlopen(req, timeout=3)
            body = _json.loads(resp.read().decode("utf-8"))
            results["gateways"][gw_id] = {
                "status": "up",
                "port": cfg["port"],
                "label": cfg["label"],
                "profile": cfg["profile"],
                "model": cfg["model"],
                "context": cfg["context"],
                "health": body,
                "latency_ms": round((_time.time() - results["timestamp"]) * 1000, 1),
            }
        except Exception as e:
            results["gateways"][gw_id] = {
                "status": "down",
                "port": cfg["port"],
                "label": cfg["label"],
                "profile": cfg["profile"],
                "model": cfg["model"],
                "context": cfg["context"],
                "error": str(e)[:200],
            }

    # ── Check extra services ────────────────────────────────────
    for svc_id, cfg in EXTRA_SERVICES.items():
        try:
            req = _ur.Request(cfg["url"])
            resp = _ur.urlopen(req, timeout=3)
            body = _json.loads(resp.read().decode("utf-8"))
            results["services"][svc_id] = {
                "status": "up",
                "port": cfg["port"],
                "label": cfg["label"],
                "health": body,
            }
        except Exception as e:
            results["services"][svc_id] = {
                "status": "down",
                "port": cfg["port"],
                "label": cfg["label"],
                "error": str(e)[:200],
            }

    # ── Active blockers ─────────────────────────────────────────
    try:
        import sqlite3 as _sql
        db = _sql.connect("/mnt/projects/cis/data/cis_memory.db")
        db.row_factory = _sql.Row
        rows = db.execute(
            "SELECT id, description FROM active_blockers WHERE status = 'ACTIVE'"
        ).fetchall()
        db.close()
        results["blockers"] = [{"id": r["id"], "description": r["description"]} for r in rows]
    except Exception:
        pass

    # ── Next actions ────────────────────────────────────────────
    try:
        db = _sql.connect("/mnt/projects/cis/data/cis_memory.db")
        db.row_factory = _sql.Row
        rows = db.execute(
            "SELECT id, description FROM next_actions WHERE status = 'PENDING' ORDER BY id"
        ).fetchall()
        db.close()
        results["next_actions"] = [{"id": r["id"], "description": r["description"]} for r in rows]
    except Exception:
        pass

    # ── Build plan phase ────────────────────────────────────────
    try:
        from mcp_bridge.tools import handle_get_current_phase
        phase = handle_get_current_phase({})
        results["phase"] = phase
    except Exception:
        results["phase"] = {"build_phase": "unknown"}

    return _json.dumps(results), 200, {"Content-Type": "application/json"}


@app.route("/api/portal/build-status")
def portal_build_status():
    """Live build plan progress + gate status — used by portal Roadmap tab."""
    import json as _json, sqlite3 as _sql, os as _os

    results = {
        "build_plan": [],
        "phase": {},
        "gate_runs": [],
        "runs": [],
        "timestamp": __import__("time").time(),
    }

    db_path = "/mnt/projects/cis/data/cis_memory.db"

    # ── Build plan nodes ────────────────────────────────────────
    try:
        db = _sql.connect(db_path)
        db.row_factory = _sql.Row
        rows = db.execute(
            "SELECT node_label, tier, status, sequence, blocked_reason, "
            "completed_at, approved_at "
            "FROM build_plan_nodes "
            "WHERE project_id = 'CIS' "
            "ORDER BY sequence"
        ).fetchall()
        db.close()
        results["build_plan"] = [dict(r) for r in rows]
    except Exception:
        pass

    # ── Pipeline phase ──────────────────────────────────────────
    try:
        from mcp_bridge.tools import handle_get_current_phase
        results["phase"] = handle_get_current_phase({})
    except Exception:
        results["phase"] = {"build_phase": "unknown", "next_tier": "?"}

    # ── Eric gate approvals ─────────────────────────────────────
    try:
        db = _sql.connect(db_path)
        db.row_factory = _sql.Row
        rows = db.execute(
            "SELECT workflow_run_id, decision, rationale, decided_at "
            "FROM eric_gate_approvals "
            "ORDER BY decided_at DESC LIMIT 5"
        ).fetchall()
        db.close()
        results["gate_runs"] = [dict(r) for r in rows]
    except Exception:
        pass

    # ── Active workflow runs ────────────────────────────────────
    try:
        db = _sql.connect(db_path)
        db.row_factory = _sql.Row
        rows = db.execute(
            "SELECT id, topic, status, rounds_completed, created_at "
            "FROM workflow_runs "
            "WHERE status NOT IN ('COMPLETE', 'ERROR', 'ESCALATE') "
            "ORDER BY created_at DESC LIMIT 10"
        ).fetchall()
        db.close()
        results["runs"] = [dict(r) for r in rows]
    except Exception:
        pass

    return _json.dumps(results, default=str), 200, {"Content-Type": "application/json"}


# ── SPA catch-all — must be before more specific frontend routes ──────────

@app.route("/")
def root_redirect():
    """Redirect root to the CIS Control Portal."""
    from flask import redirect
    return redirect("/portal")


# ── Legacy frontend routes ─────────────────────────────────────────────────

@app.route("/project/<project_id>")
@app.route("/project/<project_id>/<panel>")
def project_view(project_id, panel="overview"):
    return send_from_directory(str(RUNTIME_DIR), "cis_dashboard.html")

# ── Kernel UI routes ──────────────────────────────────────────────────────

@app.route("/kernel")
def kernel_ui():
    return send_from_directory(str(RUNTIME_DIR / "ui_mockups"), "cis_kernel_v3.html")

@app.route("/kernel/components/<path:filename>")
def kernel_components(filename):
    return send_from_directory(str(RUNTIME_DIR / "ui_components"), filename)

@app.route("/workbench")
def workbench_ui():
    return send_from_directory(str(RUNTIME_DIR / "ui_mockups"), "cis_kernel_v3.html")

# ── React Flow UI routes ─────────────────────────────────────────────────

UI_DIR = RUNTIME_DIR / "ui" / "dist"

@app.route("/ui/")
@app.route("/ui/<path:filename>")
def reactflow_ui(filename="index.html"):
    # For client-side routing: if the file doesn't exist on disk, serve index.html
    ui_file = UI_DIR / filename
    if ui_file.exists() and ui_file.is_file():
        return send_from_directory(str(UI_DIR), filename)
    # SPA fallback with /ui basename
    index_html = (UI_DIR / "index.html").read_text(encoding="utf-8")
    index_html = index_html.replace(
        '<div id="root"></div>',
        '<script>window.__CIS_BASENAME__="/ui";</script><div id="root"></div>'
    )
    from flask import make_response
    resp = make_response(index_html)
    resp.headers["Content-Type"] = "text/html; charset=utf-8"
    return resp


# ── Run ────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("═" * 60)
    print("  CIS Dashboard — Modular Backend")
    print("  http://localhost:5000")
    print("═" * 60)
    start_worker()                                   # ADR-045 — queue worker
    app.run(host="0.0.0.0", port=5000, debug=False)
