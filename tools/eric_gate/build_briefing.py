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
import re
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
    # sqlite3.Row.keys() already returns column NAMES. The old code did
    # [d[0] for d in row.keys()], which takes the first CHARACTER of each name —
    # so every row became {'i':..., 't':..., 's':...} with colliding keys, and
    # every lookup by real column name silently returned nothing. The connection
    # sets row_factory = sqlite3.Row, so this path is the one that always ran:
    # it is why the entire Eric Gate briefing rendered as "No X available".
    cols = list(row.keys()) if hasattr(row, 'keys') else []
    if not cols:
        # Fallback — get column names from description
        cursor = conn.execute(query, params)
        cols = [d[0] for d in cursor.description]
        row = cursor.fetchone()
        if row is None:
            return None
    return dict(zip(cols, row))


# ── Briefing Section Builders ──────────────────────────────────────

_PATH_RE = re.compile(
    r"(?:/workspace/cis/|/mnt/projects/cis/)?"
    r"[A-Za-z0-9_./-]+\."
    r"(?:md|py|sh|ya?ml|json|sql|txt|db)\b"
)
_CREATE_RE = re.compile(r"\b(creat|new file|write one|add(?:ing)? (?:a )?(?:new )?file)", re.I)
_MUTATE_RE = re.compile(r"\b(modif|edit|overwrit|replac|delet|remov|rename|drop)", re.I)


def _latest_draft_output(conn, run_id):
    """Most recent draft output for this run, or ''.

    The Eric Gate briefing used to read decision_trails — but that table is only
    written by the approval handler in runtime/api/relay.py, i.e. AFTER Eric
    decides. So every field was empty at the moment he was asked to decide.
    These fall back to what actually exists at gate time: the draft's own output.
    """
    row = conn.execute(
        "SELECT output_text FROM agent_trajectories "
        "WHERE run_id = ? AND phase = 'draft' AND output_text IS NOT NULL "
        "ORDER BY id DESC LIMIT 1",
        (run_id,),
    ).fetchone()
    return row[0] if row and row[0] else ""


def _final_json_summary(text):
    """Pull the 'summary' field out of a FINAL_JSON block, or ''."""
    idx = max(text.rfind("FINAL_JSON"), text.rfind("```json"))
    if idx < 0:
        return ""
    brace = text.find("{", idx)
    if brace < 0:
        return ""
    depth, in_str, esc = 0, False, False
    for i in range(brace, len(text)):
        ch = text[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
        elif ch == '"':
            in_str = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[brace:i + 1]).get("summary", "") or ""
                except Exception:
                    return ""
    return ""


def build_action_summary(conn, run_id):
    """Build action summary from workflow_runs + decision_trails.

    Falls back to the draft's own output when decision_trails is empty, which is
    always the case before approval.
    """
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

    summary = ""
    if trails:
        trail = dict(zip(
            ["problem_statement", "proposed_action", "round_count", "consensus_signal"],
            trails[-1],
        ))
        summary = trail.get("proposed_action") or ""

    draft_text = _latest_draft_output(conn, run_id)
    if not summary:
        summary = _final_json_summary(draft_text)
    if not summary:
        summary = run.get("topic") or "No summary available"

    # Files the proposal names. Scan the SUMMARY only — scanning the whole draft
    # output sweeps in every path the agent merely inspected, which would list
    # files the change does not touch under a heading that says it does.
    files = sorted({
        p for p in _PATH_RE.findall(summary)
        if not p.endswith(".bak") and len(p) > 4
    })

    # Judge intent from what the proposal says it WILL do. A naive keyword scan
    # reads "no edits to live module" as an edit — the negation flips the verdict
    # to the dangerous side, which is the worst direction for a field Eric uses
    # to decide whether a change can be undone. Drop the non-goals section and
    # explicit negations before matching.
    scope = re.sub(r"\bnon-?goals?\b.*$", "", summary, flags=re.I | re.S)
    scope = re.sub(
        r"\bno\s+(?:other\s+|further\s+)?"
        r"(?:edits?|changes?|modifications?|deletions?|renames?|overwrites?)\b",
        " ", scope, flags=re.I,
    )
    mutates = bool(_MUTATE_RE.search(scope))
    creates = bool(_CREATE_RE.search(scope))
    if mutates:
        reversibility = "REVIEW REQUIRED — proposal changes or removes existing content"
    elif creates:
        reversibility = "REVERSIBLE — proposal only adds new file(s); undo by deleting them"
    else:
        reversibility = "UNKNOWN — proposal does not state whether it adds or changes"

    return {
        "plain_language_summary": summary,
        "files_expected_to_change": files[:25],
        "reversibility": reversibility,
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

    # Before approval decision_trails is empty, so fall back to the run's topic.
    if problem == "No problem statement available" and run and run.get("topic"):
        problem = run["topic"]

    if rounds:
        # objections_json holds the reviewers' actual objections. It used to be
        # interpolated raw into a string, which rendered as unreadable JSON — so
        # the one field telling Eric what the reviewers pushed back on was noise.
        for r in rounds:
            raw = r[3]
            if not raw:
                continue
            try:
                parsed = json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                objections.append(f"Round {r[0]}: {str(raw)[:300]}")
                continue
            items = parsed if isinstance(parsed, list) else [parsed]
            for item in items:
                if isinstance(item, dict):
                    text = (item.get("objection") or item.get("issue")
                            or item.get("summary") or item.get("text")
                            or json.dumps(item))
                else:
                    text = str(item)
                text = " ".join(str(text).split())
                if text:
                    objections.append(f"Round {r[0]}: {text[:300]}")
        resolution = f"Consensus reached after {len(rounds)} deliberation round(s)"
        if not objections:
            resolution += " — no objections were recorded against the proposal"

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
- **Files named in the proposal:** {', '.join(action.get('files_expected_to_change') or []) or 'none stated'}

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
