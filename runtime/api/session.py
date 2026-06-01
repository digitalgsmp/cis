"""
api/session.py — Session start, close, and recent history endpoints.
Routes:
    POST /api/session/start
    POST /api/session/close
    GET  /api/session/recent
"""

from datetime import datetime, timezone
from pathlib import Path
from flask import Blueprint, jsonify, request
from config import (
    HARNESS_PATH, VAULT_DIR, PROJECTS_ROOT, PROJECTS_DIR,
    RECORDS_ROOT, RUNTIME_DIR, LOG_DIR, VERIFICATION_MANIFEST_DIR
)
from db.connection import db_connect, ensure_tables
from utils.helpers import ts, today, run_command

session_bp = Blueprint("session", __name__)


@session_bp.route("/api/session/start", methods=["POST"])
def api_session_start():
    result = run_command(f"python3 {HARNESS_PATH}", timeout=30)
    return jsonify(result)


@session_bp.route("/api/session/close", methods=["POST"])
def api_session_close():
    data       = request.get_json()
    focus      = data.get("focus", "").strip()
    completed  = data.get("completed", "").strip()
    next_steps = data.get("next_steps", "").strip()
    notes      = data.get("notes", "").strip()
    project_id = data.get("project_id", "").strip() or None
    verification_status       = data.get("verification_status", "").strip()
    architectural_state       = data.get("architectural_state", "").strip()
    transitional_notes        = data.get("transitional_notes", "").strip()
    conflict_register_updates = data.get("conflict_register_updates", "").strip()
    intake_status             = data.get("intake_status", "").strip()

    if not focus or not completed or not next_steps:
        return jsonify({
            "success": False,
            "error": "focus, completed, and next_steps are required"
        }), 400

    results  = {}
    step_log = []

    conn = db_connect()
    ensure_tables(conn)

    # ── Step 1: Log session to DB ──────────────────────────────────────────────
    try:
        conn.execute(
            "INSERT INTO session_log (session_date, focus, completed, next_steps, notes, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (today(), focus, completed, next_steps, notes, ts())
        )
        conn.commit()
        results["session_logged"] = True
        step_log.append("✓ Session logged to database")
    except Exception as e:
        results["session_logged"] = False
        results["session_error"] = str(e)
        step_log.append(f"✗ Session log failed: {e}")

    # ── Step 2: Regenerate ADRs.md ────────────────────────────────────────────
    try:
        rows = conn.execute(
            "SELECT decision_number, title, description, rationale, status, created_at "
            "FROM decisions ORDER BY id ASC"
        ).fetchall()
        adrs_lines = [
            "# CIS Architecture Decision Records",
            f"Last updated: {today()}",
            "---",
        ]
        for r in rows:
            adrs_lines += [
                f"## {r['decision_number']} — {r['title']}",
                f"**Status:** {r['status'].capitalize()}",
                f"**Decision:** {r['description']}",
                f"**Rationale:** {r['rationale']}",
                "---",
            ]
        adrs_path = VAULT_DIR / "Phase_PD" / "ADRs.md"
        adrs_path.write_text("\n".join(adrs_lines), encoding="utf-8")
        results["adrs_regenerated"] = True
        step_log.append(f"✓ ADRs.md regenerated ({len(rows)} decisions)")
    except Exception as e:
        results["adrs_error"] = str(e)
        step_log.append(f"✗ ADRs.md failed: {e}")

    conn.close()

    # ── Step 3: Sync knowledge records to vault ───────────────────────────────
    try:
        kr_vault = VAULT_DIR / "knowledge_records"
        kr_vault.mkdir(exist_ok=True)
        result = run_command(f"cp -r {RECORDS_ROOT}/. {kr_vault}/", timeout=30)
        step_log.append("✓ Knowledge records synced" if result["success"]
                        else f"✗ Knowledge records sync failed: {result['stderr']}")
    except Exception as e:
        step_log.append(f"✗ Knowledge records sync error: {e}")

    # ── Step 4: Sync projects folder to vault ─────────────────────────────────
    try:
        proj_vault = VAULT_DIR / "projects"
        proj_vault.mkdir(exist_ok=True)
        result = run_command(f"cp -r {PROJECTS_DIR}/. {proj_vault}/", timeout=30)
        step_log.append("✓ Projects folder synced" if result["success"]
                        else f"✗ Projects sync failed: {result['stderr']}")
    except Exception as e:
        step_log.append(f"✗ Projects sync error: {e}")

    # ── Step 5: Sync runtime scripts to vault ─────────────────────────────────
    try:
        mem_vault = VAULT_DIR / "runtime_scripts" / "memory"
        run_vault = VAULT_DIR / "runtime_scripts" / "runtime"
        mem_vault.mkdir(parents=True, exist_ok=True)
        run_vault.mkdir(parents=True, exist_ok=True)
        scripts = [
            (PROJECTS_ROOT / "memory" / "cis_harness.py",   mem_vault),
            (PROJECTS_ROOT / "memory" / "cis_log.py",       mem_vault),
            (PROJECTS_ROOT / "memory" / "create_db.py",     mem_vault),
            (RUNTIME_DIR   / "cis_intake.py",                run_vault),
            (RUNTIME_DIR   / "cis_classify.py",              run_vault),
            (RUNTIME_DIR   / "cis_preprocess.py",            run_vault),
            (RUNTIME_DIR   / "cis_extract.py",               run_vault),
            (RUNTIME_DIR   / "cis_normalize.py",             run_vault),
            (RUNTIME_DIR   / "cis_review.py",                run_vault),
            (RUNTIME_DIR   / "cis_dashboard.py",             run_vault),
            (RUNTIME_DIR   / "cis_dashboard.html",           run_vault),
        ]
        for src, dst in scripts:
            run_command(f"cp {src} {dst}/", timeout=15)
        step_log.append("✓ Runtime scripts synced to vault")
    except Exception as e:
        step_log.append(f"✗ Runtime scripts sync error: {e}")

    # ── Step 6: Append to system_log.md ──────────────────────────────────────
    try:
        system_log_path = LOG_DIR / "system_log.md"
        entry = (
            f"\n## {ts()[:16].replace('T', ' ')} UTC — SESSION CLOSE\n"
            f"- Focus: {focus}\n"
            f"- Completed: {completed[:120]}{'...' if len(completed) > 120 else ''}\n"
            f"- Next: {next_steps[:120]}{'...' if len(next_steps) > 120 else ''}\n"
        )
        with open(system_log_path, "a", encoding="utf-8") as f:
            f.write(entry)
        step_log.append("✓ system_log.md updated")
    except Exception as e:
        step_log.append(f"✗ system_log.md failed: {e}")

    # ── Step 7: Write handoff markdown ────────────────────────────────────────
    timestamp        = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M")
    handoff_filename = f"CIS_Handoff_{timestamp}.md"

    handoff_content = f"""# CIS Session Handoff
## Date: {today()}
## Time: {timestamp[11:]} UTC

## Claude's Duty at Session Start

At the start of every session Claude must:

1. Read the handoff file and 2_CIS_REORIENTATION.md
2. Confirm the current build target from Next Steps
3. Instruct the human to open a CIS Live session before any build work begins:
   - Topic = current build target
   - Problem = where we are, what we are about to build, and the expected
     return point to the main path if this is a branch
4. Keep that Live session referenced throughout — log unexpected insights
   or architectural decisions as rounds
5. Remind the human to resolve the Live session before closing

Claude must not begin build work until the Live session is open.

---

## Claude's Duty at Session End

At the end of every session — when the human signals the session is ending —
Claude must:

1. Confirm the CIS Live session has been resolved (or note it as open in Notes)
2. Generate the four session close fields for pasting into the dashboard

Claude generates these fields once, at the exact moment the session ends.
If additional work happens after fields are generated, Claude must say:
"Those fields are now outdated — here are the updated ones:" and regenerate
before anything is pasted.

Field 1 — Session Focus: One sentence. The primary objective of this session.
Field 2 — Completed: Specific past-tense list of what was built, fixed, or decided.
Field 3 — Next Steps: Prioritized list of what the next session does first.
Field 4 — Notes: Decisions discussed but not locked. Warnings or gotchas. Mid-thought or
partially built work. Anything deferred that is not a next step. Omit if nothing qualifies.

---

## Session Focus
{focus}

## Completed
{completed}

## Next Steps
{next_steps}

## Notes
{notes or '—'}

## Verification Status
{verification_status or '— Not recorded'}

## Architectural State
Capture important non-implemented realizations that materially affect future decisions.
{architectural_state or '— No architectural state notes this session.'}

## Active Transitional Implementations
Temporary operational patterns that must not be mistaken for final architecture.
{transitional_notes or '— See 11_TRANSITIONAL_IMPLEMENTATIONS.md for current list.'}

## Conflict Register Updates
{conflict_register_updates or '— No conflict register changes this session.'}

## Intake / Draft Layer Status
ADR-048 Staged Draft Intake: {intake_status or 'PRE-DRAFT — not yet built. Human copy-paste still operational reality.'}

## Sync Status
{chr(10).join(step_log)}

## How to start next session
Run on Ubuntu VM:
```
cis-start
```
Paste output as first message in new chat, then attach this file.
"""

    handoff_path = VAULT_DIR / "Phase_PD" / handoff_filename
    try:
        handoff_path.write_text(handoff_content, encoding="utf-8")
        step_log.append("✓ Handoff written to vault")
    except Exception as e:
        step_log.append(f"✗ Handoff vault write failed: {e}")

    if project_id:
        project_dir = PROJECTS_DIR / project_id
        if project_dir.exists():
            try:
                (project_dir / handoff_filename).write_text(handoff_content, encoding="utf-8")
                step_log.append("✓ Handoff written to project folder")
            except Exception as e:
                step_log.append(f"✗ Handoff project write failed: {e}")

    # ── Also write to centralized handoff folder ──────────────────────────────
    handoff_folder = Path("/mnt/projects/cis/handoff")
    try:
        handoff_folder.mkdir(exist_ok=True)
        (handoff_folder / handoff_filename).write_text(handoff_content, encoding="utf-8")
        step_log.append("✓ Handoff written to /mnt/projects/cis/handoff/")
    except Exception as e:
        step_log.append(f"✗ Handoff centralized write failed: {e}")

    results["handoff_written"] = str(handoff_path)
    results["handoff_content"] = handoff_content

    # ── Step 8: Git commit and push ───────────────────────────────────────────
    git_cmd = (
        f"cd {VAULT_DIR} && git add -A && "
        f"git commit -m 'Session close: {focus}'"
    )
    git_result = run_command(git_cmd, timeout=60)
    results["git"] = git_result

    if git_result["success"]:
        step_log.append("✓ Git committed and pushed")
    elif "nothing to commit" in git_result["stdout"] + git_result["stderr"]:
        step_log.append("✓ Git — nothing new to commit")
        results["git"]["success"] = True
    else:
        step_log.append(f"✗ Git failed: {git_result['stderr']}")

    results["step_log"] = step_log
    results["success"]  = True
    return jsonify(results)


@session_bp.route("/api/session/verification-status")
def api_session_verification_status():
    """
    Returns auto-populated Field 5 data for session close.
    Reads verification_log.md for unresolved FAILs.
    Counts manifests written today in VERIFICATION_MANIFEST_DIR.
    """
    from datetime import date

    log_path      = LOG_DIR / "verification_log.md"
    manifest_dir  = VERIFICATION_MANIFEST_DIR
    today_str     = str(date.today())

    # Count unresolved FAILs in verification log
    unresolved_fails = 0
    verifications_run = 0
    log_lines = []
    try:
        text = log_path.read_text(encoding="utf-8")
        log_lines = text.splitlines()
        for line in log_lines:
            if "FAIL" in line:
                unresolved_fails += 1
            if line.strip().startswith("##") or "PASS" in line or "FAIL" in line:
                verifications_run += 1
    except Exception:
        pass

    # Count manifests written today
    manifests_today = 0
    try:
        if manifest_dir.exists():
            manifests_today = sum(
                1 for f in manifest_dir.iterdir()
                if f.is_file() and today_str in f.name
            )
    except Exception:
        pass

    fail_label   = "0 — clean" if unresolved_fails == 0 else str(unresolved_fails)
    status_line  = (
        f"Manifests produced: {manifests_today}\n"
        f"Verifications run: {verifications_run}\n"
        f"Unresolved FAILs: {fail_label}\n"
        f"Verification log: {log_path}"
    )

    return jsonify({
        "manifests_today":   manifests_today,
        "verifications_run": verifications_run,
        "unresolved_fails":  unresolved_fails,
        "log_path":          str(log_path),
        "status_line":       status_line,
        "clean":             unresolved_fails == 0
    })


@session_bp.route("/api/session/recent")
def api_session_recent():
    conn = db_connect()
    try:
        rows = conn.execute(
            "SELECT session_date, focus, completed, next_steps, notes, created_at "
            "FROM session_log ORDER BY id DESC LIMIT 5"
        ).fetchall()
        return jsonify([dict(r) for r in rows])
    except Exception:
        return jsonify([])
    finally:
        conn.close()
