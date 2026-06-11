#!/usr/bin/env python3
"""
build_briefing.py — Eric Gate Briefing Builder (Component 3)

Assembles a four-section provenance briefing from SQLite spine data
for a given workflow run. Computes a deterministic SHA256 briefing hash
per the canonicalization rules in Section 5 of the Component 3 design.

Usage:
    python3 tools/eric_gate/build_briefing.py --workflow-run-id <RUN_ID>
    python3 tools/eric_gate/build_briefing.py --workflow-run-id <RUN_ID> --json
    python3 tools/eric_gate/build_briefing.py --workflow-run-id <RUN_ID> --markdown
    python3 tools/eric_gate/build_briefing.py --workflow-run-id <RUN_ID> --write
"""

import argparse
import hashlib
import json
import os
import sqlite3
import subprocess
import sys
import unicodedata
from datetime import datetime, timezone

# ── Constants ──────────────────────────────────────────────────────

BRIEFING_SCHEMA_VERSION = "1.0.0"
SPINE_PATH = os.environ.get(
    "CIS_SPINE_PATH",
    "/mnt/projects/cis/data/cis_memory.db",
)
BRIEFING_DIR = os.environ.get(
    "CIS_ERIC_GATE_BRIEFING_DIR",
    "/mnt/projects/cis/runtime/eric_gate/briefings",
)


# ── Helpers ────────────────────────────────────────────────────────

def get_git_head():
    """Return full 40-char git HEAD or 'UNKNOWN'."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, cwd="/mnt/projects/cis",
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return "UNKNOWN"


def normalize_timestamp(ts):
    """Normalize timestamp to UTC ISO-8601: YYYY-MM-DDTHH:MM:SSZ."""
    if not ts:
        return None
    # Strip sub-second precision and timezone variants, append Z
    ts = ts.replace("Z", "+00:00")
    try:
        # Handle various incoming formats
        for fmt in [
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%S.%f%z",
            "%Y-%m-%d %H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
        ]:
            try:
                dt = datetime.strptime(ts, fmt)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            except ValueError:
                continue
    except Exception:
        pass
    return ts  # fallback


def canonicalize(payload):
    """Produce deterministic JSON string for hashing."""
    raw = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    return unicodedata.normalize("NFC", raw)


def compute_briefing_hash(payload):
    """Compute SHA256 hash excluding volatile fields."""
    hash_payload = {
        k: v for k, v in payload.items()
        if k not in ("generated_at", "rationale")
    }
    canonical = canonicalize(hash_payload)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def dict_from_row(conn, query, params=()):
    """Execute a query and return first row as dict, or None."""
    row = conn.execute(query, params).fetchone()
    if row is None:
        return None
    cols = [d[0] for d in row.keys()] if hasattr(row, 'keys') else []
    if not cols:
        # Fallback — get column names from description
        cursor = conn.execute(query, params)
        cols = [d[0] for d in cursor.description]
        row = cursor.fetchone()
        if row is None:
            return None
    return dict(zip(cols, row))


# ── Briefing Section Builders ──────────────────────────────────────

def build_action_summary(conn, run_id):
    """Build action summary from workflow_runs + decision_trails."""
    run = dict_from_row(conn, "SELECT * FROM workflow_runs WHERE id = ?", (run_id,))
    if run is None:
        return None

    trails = conn.execute(
        """SELECT problem_statement, proposed_action, round_count, consensus_signal
           FROM decision_trails
           WHERE workflow_run_id = ?
           ORDER BY trail_sequence""",
        (run_id,),
    ).fetchall()

    if trails:
        trail = dict(zip(
            ["problem_statement", "proposed_action", "round_count", "consensus_signal"],
            trails[-1],
        ))
        summary = trail.get("proposed_action", run.get("topic", "No summary available"))
    else:
        summary = run.get("topic", "No summary available")

    return {
        "plain_language_summary": summary,
        "files_expected_to_change": [],
        "reversibility": "UNKNOWN",
    }


def build_goal_trace(conn, run_id):
    """Build goal trace from goal_references."""
    goals = conn.execute(
        """SELECT id, goal_label, dependency_node, tier_advanced,
                  advancement_type
           FROM goal_references
           WHERE workflow_run_id = ?
           ORDER BY id""",
        (run_id,),
    ).fetchall()

    if not goals:
        return {
            "project_goal": "No goal reference found",
            "goal_reference_id": None,
            "dependency_graph_node": "UNKNOWN",
            "tier_advanced": "UNKNOWN",
            "why_this_action_closes_or_advances_node": "No goal trace available",
        }

    goal = dict(zip(
        ["id", "goal_label", "dependency_node", "tier_advanced", "advancement_type"],
        goals[0],
    ))

    why = f"Advances {goal.get('tier_advanced', 'UNKNOWN')} "
    why += f"via {goal.get('advancement_type', 'UNKNOWN')} "

    return {
        "project_goal": goal.get("goal_label", "No goal label"),
        "goal_reference_id": goal.get("id"),
        "dependency_graph_node": goal.get("dependency_node", "UNKNOWN"),
        "tier_advanced": goal.get("tier_advanced", "UNKNOWN"),
        "why_this_action_closes_or_advances_node": why,
    }


def build_decision_trail(conn, run_id):
    """Build decision trail from decision_trails + deliberation_rounds
       + rejection_rationale (joined via decision_trails)."""
    run = dict_from_row(conn, "SELECT * FROM workflow_runs WHERE id = ?", (run_id,))

    # Deliberation rounds
    rounds = conn.execute(
        """SELECT round_number, drafter_output, reviewer_signal,
                  objections_json
           FROM deliberation_rounds
           WHERE run_id = ?
           ORDER BY round_number""",
        (run_id,),
    ).fetchall()

    # Decision trails
    trails = conn.execute(
        """SELECT id, trail_sequence, problem_statement, proposed_action,
                  round_count, consensus_signal, draft_summary, review_summary
           FROM decision_trails
           WHERE workflow_run_id = ?
           ORDER BY trail_sequence""",
        (run_id,),
    ).fetchall()

    # Rejection rationale joined through decision_trails
    rejections = conn.execute(
        """SELECT rr.id, rr.rejected_option_label, rr.rejected_option_summary,
                  rr.rejection_reason, rr.rejection_detail, rr.rejected_by,
                  dt.trail_sequence
           FROM rejection_rationale rr
           JOIN decision_trails dt ON rr.decision_trail_id = dt.id
           WHERE dt.workflow_run_id = ?
             AND rr.workflow_run_id = dt.workflow_run_id
           ORDER BY dt.trail_sequence, rr.id""",
        (run_id,),
    ).fetchall()

    problem = "No problem statement available"
    resolution = "No deliberation history"
    objections = []
    path = []

    if trails:
        trail_cols = ["id", "trail_sequence", "problem_statement",
                      "proposed_action", "round_count", "consensus_signal",
                      "draft_summary", "review_summary"]
        for t in trails:
            t_dict = dict(zip(trail_cols, t))
            problem = t_dict.get("problem_statement", problem)
            path.append({
                "sequence": t_dict.get("trail_sequence"),
                "problem": t_dict.get("problem_statement"),
                "proposal": t_dict.get("proposed_action"),
                "consensus": t_dict.get("consensus_signal"),
            })

    if rounds:
        objections = [
            f"Round {r[0]}: {r[3] or 'No signal'}"
            for r in rounds if r[3]
        ]
        resolution = f"Consensus reached after {len(rounds)} deliberation round(s)"

    if run and run.get("final_objections_json"):
        try:
            final_obj = json.loads(run["final_objections_json"])
            if isinstance(final_obj, list) and final_obj:
                objections = final_obj
                resolution = "Final objections documented"
        except (json.JSONDecodeError, TypeError):
            pass

    return {
        "problem": problem,
        "deliberation_path": path,
        "key_objections": objections,
        "resolution_summary": resolution,
    }


def build_drift_indicators(conn, run_id):
    """Build drift indicators section."""
    drift_rows = conn.execute(
        """SELECT id, indicator_type, description, status,
                  resolution_note, raised_at
           FROM drift_indicators
           WHERE workflow_run_id = ?
              OR workflow_run_id IS NULL
           ORDER BY
              CASE status
                  WHEN 'RAISED' THEN 0
                  WHEN 'ACKNOWLEDGED' THEN 1
                  WHEN 'ESCALATED' THEN 2
                  ELSE 3
              END,
              raised_at""",
        (run_id,),
    ).fetchall()

    drift_cols = ["id", "indicator_type", "description", "status",
                  "resolution_note", "raised_at"]

    blocking = []
    warnings = []
    flags = {
        "temporary_dependency_without_retirement_trigger": False,
        "diverges_from_dependency_graph": False,
        "objection_dismissed_without_resolution": False,
        "component_patched_more_than_once_without_root_cause_fix": False,
    }

    for d in drift_rows:
        item = dict(zip(drift_cols, d))
        status = item.get("status", "")
        indicator_type = item.get("indicator_type", "")

        # Set flags
        if indicator_type == "TEMPORARY_DEPENDENCY_NO_RETIREMENT":
            flags["temporary_dependency_without_retirement_trigger"] = True
        elif indicator_type == "ACTION_DIVERGES_FROM_DEPENDENCY_GRAPH":
            flags["diverges_from_dependency_graph"] = True
        elif indicator_type == "OBJECTION_DISMISSED_WITHOUT_RESOLUTION":
            flags["objection_dismissed_without_resolution"] = True
        elif indicator_type == "COMPONENT_PATCHED_WITHOUT_ROOT_CAUSE":
            flags["component_patched_more_than_once_without_root_cause_fix"] = True

        if status in ("RAISED", "ACKNOWLEDGED", "ESCALATED"):
            blocking.append({
                "id": item.get("id"),
                "type": indicator_type,
                "description": item.get("description", ""),
                "status": status,
            })
        else:
            warnings.append({
                "id": item.get("id"),
                "type": indicator_type,
                "description": item.get("description", ""),
                "status": status,
                "resolution": item.get("resolution_note", ""),
            })

    # Check active blockers
    blockers = conn.execute(
        """SELECT id, description FROM active_blockers
           WHERE status = 'ACTIVE'""",
    ).fetchall()
    for b in blockers:
        warnings.append({
            "source": "active_blocker",
            "id": b[0],
            "description": b[1],
        })

    return {
        "open_drift_count": len(blocking),
        "blocking_drift": blocking,
        "warnings": warnings,
        "flags": flags,
    }


# ── Main Builder ───────────────────────────────────────────────────

def build_briefing(conn, run_id):
    """Assemble full briefing payload for a workflow run."""
    git_head = get_git_head()

    # Fetch source state
    run = dict_from_row(conn, "SELECT * FROM workflow_runs WHERE id = ?", (run_id,))
    if run is None:
        print(f"ERROR: Workflow run '{run_id}' not found", file=sys.stderr)
        sys.exit(1)

    # Latest IDs for fingerprint
    latest_dr = conn.execute(
        "SELECT MAX(id) FROM deliberation_rounds WHERE run_id = ?", (run_id,)
    ).fetchone()[0]
    latest_di = conn.execute(
        "SELECT MAX(id) FROM drift_indicators WHERE workflow_run_id = ?", (run_id,)
    ).fetchone()[0]
    goal_ref = conn.execute(
        "SELECT id FROM goal_references WHERE workflow_run_id = ? ORDER BY id LIMIT 1",
        (run_id,),
    ).fetchone()
    goal_ref_id = goal_ref[0] if goal_ref else None

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Build briefing sections
    action_summary = build_action_summary(conn, run_id)
    goal_trace = build_goal_trace(conn, run_id)
    decision_trail = build_decision_trail(conn, run_id)
    drift_indicators = build_drift_indicators(conn, run_id)

    payload = {
        "briefing_schema_version": BRIEFING_SCHEMA_VERSION,
        "workflow_run_id": run_id,
        "generated_at": generated_at,
        "source_fingerprint": {
            "git_head": git_head,
            "workflow_run_updated_at": normalize_timestamp(
                run.get("updated_at", "")
            ),
            "latest_deliberation_round_id": latest_dr,
            "latest_drift_indicator_id": latest_di,
            "goal_reference_id": goal_ref_id,
        },
        "briefing": {
            "action_summary": action_summary,
            "goal_trace": goal_trace,
            "decision_trail": decision_trail,
            "drift_indicators": drift_indicators,
            "approved_file_manifest": {
                "status": "NOT_YET_IMPLEMENTED",
                "files": [],
                "enforcement": "PENDING_OQ_SEED_005",
            },
        },
    }

    payload["briefing_hash"] = compute_briefing_hash(payload)

    return payload


# ── Output Formatters ──────────────────────────────────────────────

def format_markdown(payload):
    """Render briefing as markdown."""
    b = payload["briefing"]
    goal = b.get("goal_trace", {})
    drift = b.get("drift_indicators", {})
    dt = b.get("decision_trail", {})
    action = b.get("action_summary", {})

    md = f"""# Eric Gate Briefing
**Workflow Run:** `{payload['workflow_run_id']}`
**Generated:** {payload['generated_at']}
**Briefing Hash:** `{payload.get('briefing_hash', 'N/A')}`
**Git HEAD:** `{payload['source_fingerprint']['git_head']}`

---

## 1. Action Summary

{action.get('plain_language_summary', 'No summary available')}

- **Reversibility:** {action.get('reversibility', 'UNKNOWN')}

## 2. Goal Trace

- **Project Goal:** {goal.get('project_goal', 'UNKNOWN')}
- **Dependency Node:** {goal.get('dependency_graph_node', 'UNKNOWN')}
- **Tier Advanced:** {goal.get('tier_advanced', 'UNKNOWN')}
- **Why:** {goal.get('why_this_action_closes_or_advances_node', '')}

## 3. Decision Trail

**Problem:** {dt.get('problem', 'No problem statement')}

**Resolution:** {dt.get('resolution_summary', 'No resolution')}

**Key Objections:**
"""
    for obj in dt.get("key_objections", []):
        md += f"- {obj}\n"

    md += f"""
## 4. Drift Indicators

**Open Blocking Drift:** {drift.get('open_drift_count', 0)}

"""
    flags = drift.get("flags", {})
    if any(flags.values()):
        md += "| Flag | Active |\n|------|--------|\n"
        for k, v in flags.items():
            md += f"| {k} | {'YES' if v else 'no'} |\n"
    else:
        md += "No drift indicators active.\n"

    return md


# ── CLI ────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Eric Gate Briefing Builder (Component 3)"
    )
    parser.add_argument(
        "--workflow-run-id", required=True,
        help="Workflow run ID to build briefing for",
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output canonical JSON to stdout",
    )
    parser.add_argument(
        "--markdown", action="store_true",
        help="Output markdown-formatted briefing to stdout",
    )
    parser.add_argument(
        "--write", action="store_true",
        help="Write briefing JSON to runtime/eric_gate/briefings/<RUN_ID>.json",
    )
    parser.add_argument(
        "--db", default=SPINE_PATH,
        help=f"Database path (default: {SPINE_PATH})",
    )

    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row

    try:
        payload = build_briefing(conn, args.workflow_run_id)
    finally:
        conn.close()

    # Output
    canonical = canonicalize(payload)

    if args.markdown:
        print(format_markdown(payload))
    elif args.json:
        print(canonical)
    elif args.write:
        os.makedirs(BRIEFING_DIR, exist_ok=True)
        path = os.path.join(BRIEFING_DIR, f"{args.workflow_run_id}.json")
        with open(path, "w") as f:
            f.write(canonical + "\n")
        print(f"Briefing written: {path}")
        print(f"Hash: {payload.get('briefing_hash', 'N/A')}")
    else:
        # Default: compact output
        print(json.dumps({
            "workflow_run_id": payload["workflow_run_id"],
            "briefing_hash": payload.get("briefing_hash"),
            "sections": list(payload["briefing"].keys()),
            "drift_open": payload["briefing"]["drift_indicators"]["open_drift_count"],
        }, indent=2))


if __name__ == "__main__":
    main()
