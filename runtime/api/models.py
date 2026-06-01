"""
api/models.py
CIS Model Registry — ADR-024 / ADR-025

Manages the model roster used by the intelligence routing layer.
Serves the Intel sidebar local/remote/agent tabs in the dashboard.

Registry design:
  - All models stored in the `models` table in cis_memory.db
  - Models carry a lifecycle status: discovered → installed → testing →
    benchmarked → active | archived
  - Models are typed by runtime (ollama, comfyui, transformers, api_remote)
    and capability (visual_extraction, image_generation, text_generation, etc.)
  - GET /api/models returns filtered views by tier (local/remote/agent)
    and optionally by status and capability
  - POST /api/models registers a new model entry
  - PATCH /api/models/<id> updates status, notes, or benchmark data
  - DELETE /api/models/<id> archives a model (no hard deletes)
  - POST /api/models/sync/ollama live-syncs the Ollama roster into the registry

This module is the ground truth for route_task.py (Phase 1).
When the router needs to know what models are available for a given
capability and tier, it queries this registry — not a hardcoded list.

ADR-024: Model registry API endpoint and schema
ADR-025: Intel sidebar tabs wired to live model roster
Next ADR: ADR-030
"""

import json
import requests
from datetime import datetime, timezone
from flask import Blueprint, jsonify, request

from db.connection import db_connect
from utils.helpers import ts

models_bp = Blueprint("models", __name__)

OLLAMA_BASE = "http://localhost:11434"

# ---------------------------------------------------------------------------
# Table bootstrap
# Called from db/connection.py ensure_tables() — add this call there.
# ---------------------------------------------------------------------------

def ensure_models_table():
    """
    Create the models table if it does not exist.
    Safe to call on every startup — no-op if table already exists.

    Schema notes:
      id            — stable slug, e.g. "llava-latest", "claude-sonnet-4-6"
      name          — human display name
      runtime       — where/how the model runs:
                        ollama | comfyui | transformers | api_remote | vllm
      capability    — comma-separated capability tags:
                        visual_extraction | image_generation | text_generation |
                        multimodal | code | 3d_generation | audio_generation |
                        embedding
      tier          — sidebar tab assignment: local | remote | agent
      status        — lifecycle state:
                        discovered | installed | testing | benchmarked |
                        active | archived
      size_params   — parameter count label, e.g. "7B", "32B"
      quantization  — precision label, e.g. "Q4_0", "bfloat16", "4bit", "fp8"
      context_window— token context window if known
      vram_required — estimated VRAM in GB (nullable)
      benchmark_score — free-form benchmark summary (nullable)
      notes         — free text: observed strengths, weaknesses, use cases
      source_url    — HuggingFace / model card URL (nullable)
      installed_at  — ISO timestamp when first registered
      updated_at    — ISO timestamp of last update
    """
    conn = db_connect()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS models (
            id              TEXT PRIMARY KEY,
            name            TEXT NOT NULL,
            runtime         TEXT NOT NULL,
            capability      TEXT NOT NULL,
            tier            TEXT NOT NULL,
            status          TEXT NOT NULL DEFAULT 'installed',
            size_params     TEXT,
            quantization    TEXT,
            context_window  INTEGER,
            vram_required   REAL,
            benchmark_score TEXT,
            notes           TEXT,
            source_url      TEXT,
            installed_at    TEXT NOT NULL,
            updated_at      TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Seed data
# Run once via POST /api/models/seed to populate known baseline entries.
# After seeding, use POST /api/models and PATCH /api/models/<id> for changes.
# ---------------------------------------------------------------------------

SEED_MODELS = [
    # --- LOCAL: Ollama models (confirmed present via curl /api/tags) ---
    {
        "id": "llava-latest",
        "name": "LLaVA 7B (Ollama)",
        "runtime": "ollama",
        "capability": "visual_extraction,multimodal",
        "tier": "local",
        "status": "active",
        "size_params": "7B",
        "quantization": "Q4_0",
        "context_window": 4096,
        "vram_required": 5.0,
        "notes": (
            "Multimodal vision-language model. Current visual extraction "
            "baseline via Ollama. Confirmed present on system."
        ),
        "source_url": "https://ollama.com/library/llava",
    },
    {
        "id": "llama3-latest",
        "name": "Llama 3 8B (Ollama)",
        "runtime": "ollama",
        "capability": "text_generation,code",
        "tier": "local",
        "status": "active",
        "size_params": "8.0B",
        "quantization": "Q4_0",
        "context_window": 8192,
        "vram_required": 5.0,
        "notes": (
            "General text generation and code. Confirmed present on system."
        ),
        "source_url": "https://ollama.com/library/llama3",
    },
    # --- LOCAL: Transformers / GPU models ---
    {
        "id": "qwen25-vl-32b-4bit",
        "name": "Qwen2.5-VL 32B Instruct (4-bit)",
        "runtime": "transformers",
        "capability": "visual_extraction,multimodal,text_generation",
        "tier": "local",
        "status": "testing",
        "size_params": "32B",
        "quantization": "4bit",
        "context_window": 32768,
        "vram_required": 20.0,
        "notes": (
            "Primary extraction model per ADR-001/ADR-009. "
            "Runs via transformers + bitsandbytes in gpu-test env. "
            "Requires PYTORCH_ALLOC_CONF flag. "
            "Weights path unconfirmed — locate before marking active. "
            "ADR-008: full bfloat16 cannot load on RTX 4090."
        ),
        "source_url": (
            "https://huggingface.co/Qwen/Qwen2.5-VL-32B-Instruct"
        ),
    },
    # --- REMOTE: Frontier API models ---
    {
        "id": "claude-sonnet-4-6",
        "name": "Claude Sonnet 4.6 (Anthropic API)",
        "runtime": "api_remote",
        "capability": "text_generation,code,multimodal,visual_extraction",
        "tier": "remote",
        "status": "active",
        "size_params": None,
        "quantization": None,
        "context_window": 200000,
        "vram_required": None,
        "notes": (
            "Primary frontier model for reasoning, synthesis, implementation "
            "work, and complex extraction tasks. Manual API key required."
        ),
        "source_url": "https://docs.anthropic.com",
    },
    {
        "id": "gemini-25-pro",
        "name": "Gemini 2.5 Pro (Google API)",
        "runtime": "api_remote",
        "capability": "text_generation,multimodal,visual_extraction",
        "tier": "remote",
        "status": "active",
        "size_params": None,
        "quantization": None,
        "context_window": 1000000,
        "vram_required": None,
        "notes": (
            "Architecture thinking and long-context tasks per CIS role "
            "assignments. Manual API key required."
        ),
        "source_url": "https://ai.google.dev",
    },
    {
        "id": "gpt-4o",
        "name": "GPT-4o (OpenAI API)",
        "runtime": "api_remote",
        "capability": "text_generation,multimodal,visual_extraction,code",
        "tier": "remote",
        "status": "active",
        "size_params": None,
        "quantization": None,
        "context_window": 128000,
        "vram_required": None,
        "notes": (
            "Adversarial review role per CIS role assignments. "
            "Manual API key required."
        ),
        "source_url": "https://platform.openai.com",
    },
    # --- AGENT: Phase 4 roles (not yet implemented) ---
    {
        "id": "agent-librarian",
        "name": "Librarian",
        "runtime": "agent",
        "capability": "retrieval",
        "tier": "agent",
        "status": "discovered",
        "size_params": None,
        "quantization": None,
        "context_window": None,
        "vram_required": None,
        "notes": (
            "Phase 4. Searches vector index, retrieves approved knowledge "
            "records, presents with relevance explanation. "
            "Operates only on approved/locked records. "
            "Model assignment: TBD at Phase 4 build."
        ),
        "source_url": None,
    },
    {
        "id": "agent-researcher",
        "name": "Researcher",
        "runtime": "agent",
        "capability": "retrieval,text_generation",
        "tier": "agent",
        "status": "discovered",
        "size_params": None,
        "quantization": None,
        "context_window": None,
        "vram_required": None,
        "notes": (
            "Phase 4. Synthesizes Librarian retrieval results into structured "
            "summaries. Surfaces knowledge gaps. Outputs are proposals only. "
            "Model assignment: TBD at Phase 4 build."
        ),
        "source_url": None,
    },
    {
        "id": "agent-teacher",
        "name": "Teacher",
        "runtime": "agent",
        "capability": "text_generation",
        "tier": "agent",
        "status": "discovered",
        "size_params": None,
        "quantization": None,
        "context_window": None,
        "vram_required": None,
        "notes": (
            "Phase 4. Takes an approved knowledge record (typically a "
            "learning/tutorial record) and guides the user through applying "
            "it. Quality is proportional to source record quality. "
            "Model assignment: TBD at Phase 4 build."
        ),
        "source_url": None,
    },
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _row_to_dict(row):
    """Convert a sqlite3.Row to a plain dict."""
    return dict(row)


def _get_ollama_status(model_id):
    """
    Check if a model is currently loaded in Ollama memory.
    Returns: 'loaded' | 'available' | 'unavailable'
    """
    try:
        # /api/ps lists models currently loaded in GPU memory
        r = requests.get(f"{OLLAMA_BASE}/api/ps", timeout=2)
        if r.status_code == 200:
            loaded = [m.get("name", "") for m in r.json().get("models", [])]
            # Normalize: "llava:latest" -> "llava-latest" for comparison
            loaded_slugs = [n.replace(":", "-") for n in loaded]
            if model_id in loaded_slugs:
                return "loaded"
            return "available"
    except Exception:
        pass
    return "unavailable"


def _enrich_local_status(model):
    """
    For local models, augment the registry status with live runtime state.
    Adds a `runtime_status` field without modifying the lifecycle `status`.

    runtime_status values:
      loaded      — model is currently in GPU memory (Ollama only)
      available   — installed and callable but not currently loaded
      unavailable — runtime not reachable or weights not confirmed
    """
    runtime = model.get("runtime")
    if runtime == "ollama":
        model["runtime_status"] = _get_ollama_status(model["id"])
    elif runtime == "transformers":
        # Transformers models: available means weights confirmed on disk.
        # Weight path confirmation happens via /api/models/sync/transformers
        # (not yet built). For now, reflect the DB status literally.
        model["runtime_status"] = (
            "available" if model["status"] in ("active", "testing", "benchmarked")
            else "unavailable"
        )
    elif runtime == "api_remote":
        model["runtime_status"] = "manual"  # no live check without API key
    elif runtime == "agent":
        model["runtime_status"] = "not_implemented"
    else:
        model["runtime_status"] = "unknown"
    return model


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@models_bp.route("/api/models", methods=["GET"])
def get_models():
    """
    Return the model roster, optionally filtered.

    Query params:
      tier        filter by tier: local | remote | agent
      status      filter by lifecycle status (comma-separated ok)
      capability  filter by capability tag (partial match)
      all         if "true", return flat list instead of grouped-by-tier

    Default response: models grouped by tier, active + testing + benchmarked
    only (excludes discovered/archived from routing view).

    The Intel sidebar uses: /api/models?tier=local etc.
    The route_task.py router uses: /api/models?tier=local&status=active&capability=visual_extraction
    The admin registry view uses: /api/models?all=true
    """
    tier = request.args.get("tier")
    status_filter = request.args.get("status")
    capability_filter = request.args.get("capability")
    return_all = request.args.get("all", "false").lower() == "true"

    conn = db_connect()
    conn.row_factory = __import__("sqlite3").Row
    cur = conn.cursor()

    query = "SELECT * FROM models WHERE 1=1"
    params = []

    if tier:
        query += " AND tier = ?"
        params.append(tier)

    if status_filter:
        statuses = [s.strip() for s in status_filter.split(",")]
        placeholders = ",".join("?" * len(statuses))
        query += f" AND status IN ({placeholders})"
        params.extend(statuses)
    elif not return_all:
        # Default: exclude discovered and archived from operational views
        query += " AND status NOT IN ('discovered', 'archived')"

    query += " ORDER BY tier, name"

    rows = cur.execute(query, params).fetchall()
    conn.close()

    models = [_row_to_dict(r) for r in rows]

    # Enrich with live runtime state
    models = [_enrich_local_status(m) for m in models]

    # Apply capability filter after enrichment (capability is a CSV string)
    if capability_filter:
        models = [
            m for m in models
            if capability_filter in m.get("capability", "")
        ]

    if return_all or tier:
        return jsonify({"models": models, "count": len(models)})

    # Default: group by tier for sidebar consumption
    grouped = {"local": [], "remote": [], "agent": []}
    for m in models:
        t = m.get("tier", "local")
        if t in grouped:
            grouped[t].append(m)

    return jsonify({
        "models": grouped,
        "counts": {k: len(v) for k, v in grouped.items()},
    })


@models_bp.route("/api/models/<model_id>", methods=["GET"])
def get_model(model_id):
    """Return a single model record by id."""
    conn = db_connect()
    conn.row_factory = __import__("sqlite3").Row
    row = conn.execute(
        "SELECT * FROM models WHERE id = ?", (model_id,)
    ).fetchone()
    conn.close()

    if not row:
        return jsonify({"error": f"Model '{model_id}' not found"}), 404

    model = _enrich_local_status(_row_to_dict(row))
    return jsonify(model)


@models_bp.route("/api/models", methods=["POST"])
def register_model():
    """
    Register a new model in the registry.

    Required fields: id, name, runtime, capability, tier
    Optional: status, size_params, quantization, context_window,
              vram_required, notes, source_url

    Default status: 'installed'
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON body provided"}), 400

    required = ["id", "name", "runtime", "capability", "tier"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing required fields: {missing}"}), 400

    valid_runtimes = {"ollama", "comfyui", "transformers", "api_remote", "vllm", "agent"}
    if data["runtime"] not in valid_runtimes:
        return jsonify({"error": f"Invalid runtime. Must be one of: {valid_runtimes}"}), 400

    valid_tiers = {"local", "remote", "agent"}
    if data["tier"] not in valid_tiers:
        return jsonify({"error": f"Invalid tier. Must be one of: {valid_tiers}"}), 400

    valid_statuses = {"discovered", "installed", "testing", "benchmarked", "active", "archived"}
    status = data.get("status", "installed")
    if status not in valid_statuses:
        return jsonify({"error": f"Invalid status. Must be one of: {valid_statuses}"}), 400

    now = ts()
    conn = db_connect()
    try:
        conn.execute("""
            INSERT INTO models (
                id, name, runtime, capability, tier, status,
                size_params, quantization, context_window, vram_required,
                benchmark_score, notes, source_url, installed_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data["id"],
            data["name"],
            data["runtime"],
            data["capability"],
            data["tier"],
            status,
            data.get("size_params"),
            data.get("quantization"),
            data.get("context_window"),
            data.get("vram_required"),
            data.get("benchmark_score"),
            data.get("notes"),
            data.get("source_url"),
            now, now,
        ))
        conn.commit()
    except Exception as e:
        conn.close()
        if "UNIQUE constraint" in str(e):
            return jsonify({"error": f"Model id '{data['id']}' already exists. Use PATCH to update."}), 409
        return jsonify({"error": str(e)}), 500
    conn.close()
    return jsonify({"registered": data["id"], "status": status}), 201


@models_bp.route("/api/models/<model_id>", methods=["PATCH"])
def update_model(model_id):
    """
    Update mutable fields on an existing model.

    Mutable fields: status, notes, benchmark_score, capability,
                    context_window, vram_required, source_url,
                    size_params, quantization

    Immutable: id, runtime, tier, installed_at

    To archive a model: PATCH with {"status": "archived"}
    Hard deletes are not permitted.
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON body provided"}), 400

    mutable = {
        "status", "notes", "benchmark_score", "capability",
        "context_window", "vram_required", "source_url",
        "size_params", "quantization", "name",
    }
    updates = {k: v for k, v in data.items() if k in mutable}
    if not updates:
        return jsonify({"error": "No mutable fields provided"}), 400

    if "status" in updates:
        valid_statuses = {"discovered", "installed", "testing", "benchmarked", "active", "archived"}
        if updates["status"] not in valid_statuses:
            return jsonify({"error": f"Invalid status: {updates['status']}"}), 400

    updates["updated_at"] = ts()
    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [model_id]

    conn = db_connect()
    cur = conn.execute(
        f"UPDATE models SET {set_clause} WHERE id = ?", values
    )
    conn.commit()
    conn.close()

    if cur.rowcount == 0:
        return jsonify({"error": f"Model '{model_id}' not found"}), 404

    return jsonify({"updated": model_id, "fields": list(updates.keys())})


@models_bp.route("/api/models/<model_id>", methods=["DELETE"])
def archive_model(model_id):
    """
    Archive a model. No hard deletes — archived models stay in the DB
    for audit and benchmark history but are excluded from routing views.
    """
    now = ts()
    conn = db_connect()
    cur = conn.execute(
        "UPDATE models SET status = 'archived', updated_at = ? WHERE id = ?",
        (now, model_id)
    )
    conn.commit()
    conn.close()

    if cur.rowcount == 0:
        return jsonify({"error": f"Model '{model_id}' not found"}), 404

    return jsonify({"archived": model_id})


@models_bp.route("/api/models/sync/ollama", methods=["POST"])
def sync_ollama():
    """
    Live-sync the Ollama model roster into the registry.

    For each model returned by Ollama /api/tags:
      - If the model is not in the registry: insert as status='installed'
      - If it exists: update size/quantization if they have changed

    Does not archive models that were removed from Ollama — that is a
    manual decision (use PATCH to archive).

    Returns a summary of what was inserted vs updated vs unchanged.
    """
    try:
        r = requests.get(f"{OLLAMA_BASE}/api/tags", timeout=5)
        r.raise_for_status()
    except Exception as e:
        return jsonify({"error": f"Ollama unreachable: {e}"}), 503

    ollama_models = r.json().get("models", [])
    now = ts()
    conn = db_connect()
    conn.row_factory = __import__("sqlite3").Row

    inserted = []
    updated = []
    unchanged = []

    for om in ollama_models:
        raw_name = om.get("name", "")
        model_id = raw_name.replace(":", "-")
        details = om.get("details", {})
        size_params = details.get("parameter_size")
        quantization = details.get("quantization_level")
        family = details.get("family", "")

        # Derive capability from family heuristic
        families = details.get("families", [family])
        capability = "text_generation"
        if "clip" in families or "llava" in raw_name.lower():
            capability = "visual_extraction,multimodal"

        existing = conn.execute(
            "SELECT * FROM models WHERE id = ?", (model_id,)
        ).fetchone()

        if existing is None:
            conn.execute("""
                INSERT INTO models (
                    id, name, runtime, capability, tier, status,
                    size_params, quantization, installed_at, updated_at
                ) VALUES (?, ?, 'ollama', ?, 'local', 'installed', ?, ?, ?, ?)
            """, (
                model_id, raw_name, capability,
                size_params, quantization, now, now,
            ))
            inserted.append(model_id)
        else:
            ex = dict(existing)
            changed = (
                ex.get("size_params") != size_params or
                ex.get("quantization") != quantization
            )
            if changed:
                conn.execute("""
                    UPDATE models SET size_params=?, quantization=?, updated_at=?
                    WHERE id=?
                """, (size_params, quantization, now, model_id))
                updated.append(model_id)
            else:
                unchanged.append(model_id)

    conn.commit()
    conn.close()

    return jsonify({
        "sync": "ollama",
        "inserted": inserted,
        "updated": updated,
        "unchanged": unchanged,
        "total_from_ollama": len(ollama_models),
    })


@models_bp.route("/api/models/seed", methods=["POST"])
def seed_models():
    """
    Seed the registry with the known baseline model entries.
    Safe to call multiple times — skips models that already exist.
    Use PATCH to update seeded entries after the fact.
    """
    now = ts()
    conn = db_connect()
    inserted = []
    skipped = []

    for m in SEED_MODELS:
        existing = conn.execute(
            "SELECT id FROM models WHERE id = ?", (m["id"],)
        ).fetchone()
        if existing:
            skipped.append(m["id"])
            continue
        conn.execute("""
            INSERT INTO models (
                id, name, runtime, capability, tier, status,
                size_params, quantization, context_window, vram_required,
                notes, source_url, installed_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            m["id"], m["name"], m["runtime"], m["capability"],
            m["tier"], m.get("status", "installed"),
            m.get("size_params"), m.get("quantization"),
            m.get("context_window"), m.get("vram_required"),
            m.get("notes"), m.get("source_url"),
            now, now,
        ))
        inserted.append(m["id"])

    conn.commit()
    conn.close()

    return jsonify({
        "seeded": inserted,
        "skipped": skipped,
        "total": len(SEED_MODELS),
    })
