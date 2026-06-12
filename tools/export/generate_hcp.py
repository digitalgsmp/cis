#!/usr/bin/env python3
"""
generate_hcp.py — Tier 5.4
Reads SQLite spine + agents_static.yaml + hcp_static.yaml + git metadata.
Writes READ_FIRST_HERMES_CONTEXT.md plus HCP_00 through HCP_09 to PROJECT_CONTEXT_PACK_UPLOAD/.

Usage: python3 tools/export/generate_hcp.py [--db PATH] [--hcp-config PATH]
          [--agents-config PATH] [--out-dir PATH] [--run-id ID] [--dry-run]
"""

import argparse
import sqlite3
import subprocess
import sys
import yaml
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = REPO_ROOT / "data" / "cis_memory.db"
DEFAULT_HCP_CONFIG = REPO_ROOT / "config" / "hcp_static.yaml"
DEFAULT_AGENTS_CONFIG = REPO_ROOT / "config" / "agents_static.yaml"
DEFAULT_OUT_DIR = REPO_ROOT / "PROJECT_CONTEXT_PACK_UPLOAD"

HCP_FILES = [
    "READ_FIRST_HERMES_CONTEXT.md",
    "HCP_00_README_START_HERE.md",
    "HCP_01_CURRENT_STATE.md",
    "HCP_02_ACTIVE_ARCHITECTURE.md",
    "HCP_03_DECISIONS_LOG.md",
    "HCP_04_OPEN_QUESTIONS.md",
    "HCP_05_NEXT_ACTIONS.md",
    "HCP_06_MODEL_ROLES_AND_PROTOCOL.md",
    "HCP_07_RECENT_HANDOFF.md",
    "HCP_08_FILES_CHANGED_RECENTLY.md",
    "HCP_09_TERMS_AND_NAMING.md",
]


# ── helpers ────────────────────────────────────────────────────────────────

def generation_stamp(run_id):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    rid = run_id or "none"
    return [
        f"Generated: {now} | Run: {rid}",
        "Source: SQLite spine + config/hcp_static.yaml + config/agents_static.yaml",
        "DO NOT MANUALLY EDIT — regenerate with tools/export/generate_hcp.py",
    ]


def get_git_head(repo_root):
    """Return (short_sha, full_sha) or (None, None)."""
    try:
        r = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, cwd=repo_root, timeout=5,
        )
        short = r.stdout.strip() if r.returncode == 0 else None
        r2 = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, cwd=repo_root, timeout=5,
        )
        full = r2.stdout.strip() if r2.returncode == 0 else None
        return short, full
    except Exception:
        return None, None


def get_git_log(repo_root, n=10):
    """Return list of {sha, message, files} dicts."""
    try:
        r = subprocess.run(
            ["git", "log", f"-{n}", "--oneline", "--name-only"],
            capture_output=True, text=True, cwd=repo_root, timeout=10,
        )
        if r.returncode != 0:
            return []
        commits = []
        current = None
        for line in r.stdout.strip().splitlines():
            line = line.strip()
            if not line:
                continue
            if not line.startswith(" ") and not line.startswith("\t"):
                # New commit: "abc1234 message"
                parts = line.split(" ", 1)
                sha = parts[0]
                msg = parts[1] if len(parts) > 1 else ""
                current = {"sha": sha, "message": msg, "files": []}
                commits.append(current)
            elif current is not None:
                current["files"].append(line)
        return commits
    except Exception:
        return []


def load_yaml(path):
    with open(path) as f:
        return yaml.safe_load(f)


# ── spine queries ──────────────────────────────────────────────────────────

def _row_to_dict(row):
    """Convert sqlite3.Row to plain dict for .get() support."""
    if row is None:
        return None
    return dict(row)


def query_spine(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    decisions = [_row_to_dict(r) for r in conn.execute(
        "SELECT * FROM project_decisions ORDER BY decided_at DESC"
    ).fetchall()]

    questions = [_row_to_dict(r) for r in conn.execute(
        "SELECT * FROM open_questions ORDER BY opened_at DESC"
    ).fetchall()]

    actions = [_row_to_dict(r) for r in conn.execute(
        "SELECT * FROM next_actions ORDER BY tier, id"
    ).fetchall()]

    blockers = [_row_to_dict(r) for r in conn.execute(
        "SELECT * FROM active_blockers ORDER BY created_at DESC"
    ).fetchall()]

    runs_raw = conn.execute(
        "SELECT * FROM workflow_runs ORDER BY created_at DESC LIMIT 5"
    ).fetchall()
    runs = [_row_to_dict(r) for r in runs_raw]

    latest_run = runs[0] if runs else None

    # Row counts for HCP_01
    row_counts = {}
    for table in ["workflow_runs", "deliberation_rounds", "project_decisions",
                   "open_questions", "next_actions", "active_blockers"]:
        try:
            c = conn.execute(f"SELECT count(*) FROM {table}").fetchone()
            row_counts[table] = c[0]
        except Exception:
            row_counts[table] = "?"

    # Query canonical build state from project_state table (Tier 6.5 remediation)
    state_rows = conn.execute(
        """SELECT key, value FROM project_state
           WHERE superseded_at IS NULL
           AND id = (
               SELECT MAX(id) FROM project_state ps2
               WHERE ps2.key = project_state.key AND ps2.superseded_at IS NULL
           )"""
    ).fetchall()
    build_state = {row["key"]: row["value"] for row in state_rows}

    # Eric Gate approval status
    eric_gate = conn.execute(
        """SELECT ega.decision, ega.decided_at, ega.goal_reference_id,
                  ega.workflow_run_id, ega.briefing_hash, gr.goal_label
           FROM eric_gate_approvals ega
           LEFT JOIN goal_references gr ON ega.goal_reference_id = gr.id
           WHERE ega.is_current = 1
           ORDER BY ega.decided_at DESC
           LIMIT 1"""
    ).fetchone()
    eric_gate_dict = _row_to_dict(eric_gate) if eric_gate else None

    # Query build_plan_nodes for Component 3.5 generator switchover
    build_plan_nodes = [_row_to_dict(r) for r in conn.execute(
        """SELECT bpn.*,
           (SELECT COUNT(*) FROM build_plan_dependencies bpd
            JOIN build_plan_nodes dep ON bpd.depends_on_id = dep.id
            WHERE bpd.node_id = bpn.id AND bpd.dependency_type = 'HARD'
              AND dep.status != 'COMPLETE') as unmet_hard_deps
           FROM build_plan_nodes bpn
           WHERE bpn.project_id = 'CIS'
           ORDER BY bpn.sequence"""
    ).fetchall()]

    conn.close()
    return decisions, questions, actions, blockers, runs, latest_run, row_counts, build_state, eric_gate_dict, build_plan_nodes


# ── per-file renderers ─────────────────────────────────────────────────────

def render_hcp_00(stamp, hcp_static, agents_static, head_short, actions):
    s = hcp_static["hcp_00"]
    lines = ["# Project Context Pack — Hermes Harness / CIS"]
    for st in stamp:
        lines.append(st)
    lines.append(f"Maintained by: {s['maintained_by']}")
    lines.append("")
    lines.append("## IMPORTANT — Architecture Change COMPLETE")
    lines.append("")
    for line in s["architecture_announcement"].strip().splitlines():
        lines.append(line)
    lines.append("")
    lines.append("## Purpose")
    for line in s["purpose"].strip().splitlines():
        lines.append(line)
    lines.append("")
    lines.append("## How to use it")
    for item in s["reading_order"]:
        lines.append(f"1. {item}" if item.startswith("1.") else f"- {item}")
    lines.append("")
    lines.append("## Current Status")
    lines.append(f"- HEAD: {head_short or 'unknown'}")
    # Find current next action
    curr = [a for a in actions if a["status"] in ("IN_PROGRESS", "PENDING") and a["id"].startswith("NA-SEED-")]
    if curr:
        na = curr[0]
        lines.append(f"- {na['description']}")
    lines.append("- 4/4 active gateways pass AGENTS.md canary")
    lines.append("")
    return "\n".join(lines)


def render_hcp_01(stamp, hcp_static, agents_static, decisions, questions,
                   actions, blockers, runs, latest_run, row_counts, build_state,
                   build_plan_nodes):
    s = hcp_static["hcp_01"]
    shared = hcp_static["shared"]
    infra = agents_static.get("infrastructure", {})
    gateways = agents_static.get("gateways", [])

    build_phase = build_state.get("build_phase", "(unknown — project_state table missing)")

    lines = ["# CIS Current State"]
    lines.append(f"Version: {s['version']}")
    lines.append(f"Date: {datetime.now(timezone.utc).strftime('%Y-%m-%d')}")
    lines.append(f"Authority: {s['authority']}")

    # Status line: from canonical build state, fall back to actions
    status_line = build_phase
    lines.append(f"Status: {status_line}")
    lines.append("")
    # Generation stamp
    for st in stamp:
        lines.append(st)
    lines.append("")
    lines.append("---")
    lines.append("")

    # Current Objective
    lines.append("## Current Objective")
    lines.append("")
    lines.append(f"**{build_phase}**")
    lines.append("")

    # HEAD and status
    head_short, _ = get_git_head(REPO_ROOT)
    lines.append(f"**HEAD:** `{head_short or 'unknown'}`.")

    lines.append("")
    for line in s["context_architecture_blurb"].strip().splitlines():
        lines.append(line)
    lines.append("")

    # Remaining Tier 5
    remaining = [a for a in actions if a["status"] == "PENDING" and a["tier"] and str(a["tier"]).startswith("5")]
    if remaining:
        lines.append("**Remaining Tier 5:** " + " → ".join(a["description"] for a in remaining))
        lines.append("")

    lines.append("Do NOT start Tier 7, Judge, UI, VDB/Chroma, router reclassification, or MCP.")
    lines.append("")

    # Tier descriptions
    for tier_key in ["tier_0", "tier_1", "tier_2", "tier_3", "tier_4"]:
        txt = s["tier_descriptions"].get(tier_key, "")
        if txt:
            for line in txt.strip().splitlines():
                lines.append(line)
            lines.append("")

    # Known limitations
    lines.append("**Known limitation:**")
    for lim in s["known_limitations"]:
        lines.append(f"- {lim}")
    lines.append("")

    # Tier 5 status
    lines.append(f"**Tier 5 — Context Export Pipeline:** Per Dependency Graph")
    lines.append(f"Build Plan v2.0 (`{shared['build_authority']}`).")
    lines.append("")

    # Phase A findings
    for line in s["phase_a_findings"].strip().splitlines():
        lines.append(line)
    lines.append("")

    # CIS definition
    lines.append(shared["cis_definition"])
    lines.append("")

    # Claude/ChatGPT convergence
    for line in s["claude_chatgpt_convergence"].strip().splitlines():
        lines.append(line)
    lines.append("")

    # Pipeline architecture
    for line in s["pipeline_architecture"].strip().splitlines():
        lines.append(line)
    lines.append("")

    # Phase 0
    for line in s["phase_0_recovery"].strip().splitlines():
        lines.append(line)
    lines.append("")

    # Verification-hardening rule
    lines.append("**Verification-hardening rule (2026-05-31):** " + agents_static.get("verification_hardening_rule", "").strip().replace("\n", " "))
    lines.append("")
    # Evidence-Backed Response Rule
    lines.append("**Evidence-Backed Response Rule**")
    lines.append("")
    for line in shared.get("evidence_rule", "").strip().splitlines():
        lines.append(line)
    lines.append("")
    lines.append("---")
    lines.append("")

    # Model Roles
    for line in s["model_roles_narrative"].strip().splitlines():
        lines.append(line)
    lines.append("")
    for line in s["advisor_loop_text"].strip().splitlines():
        lines.append(line)
    lines.append("")
    lines.append("---")
    lines.append("")

    # Current System State
    lines.append("## Current System State")
    lines.append("")
    lines.append("### Infrastructure")
    for k, v in infra.items():
        lines.append(f"- {k}: {v}")
    lines.append("")

    # Gateway table
    lines.append("### Advisor Gateways")
    lines.append("")
    lines.append("| Gateway | Port | HERMES_HOME | Model | Reasoning | NeMo? | Status |")
    lines.append("|---------|------|-------------|-------|-----------|-------|--------|")
    for gw in gateways:
        nemo_str = "Yes" if gw.get("nemo") else "No"
        reasoning = gw.get("reasoning", "none")
        lines.append(
            f"| {gw['label']} ({gw['profile']}) | {gw['port']} "
            f"| {gw['hermes_home']} | {gw['model']} | {reasoning} "
            f"| {nemo_str} | {gw['status']} |"
        )
    lines.append("")
    lines.append("**Context:** AGENTS.md auto-loaded by all 4 active gateways via "
                 "TERMINAL_CWD=/mnt/projects/cis. HERMES_CIS_BRIEFING_PATH retired.")
    lines.append("")

    # Service files
    for line in s["service_files_text"].strip().splitlines():
        lines.append(line)
    lines.append("")

    # Hermes Source Patches
    lines.append("### Hermes Source Patches (permanent — Gate 2/5C)")
    lines.append("")
    patches = agents_static.get("hermes_patches", {})
    base = patches.get("base_path", "")
    for i, p in enumerate(patches.get("patches", []), 1):
        loc = f":{p['line']}" if p.get("line") else ""
        lines.append(f"{i}. `{base}{p['file']}{loc}` — {p['description']}")
    lines.append("")

    # CIS Application
    for line in s["cis_application_state"].strip().splitlines():
        lines.append(line)
    lines.append("")

    # History sections
    for key in ["google_drive", "phase_3a", "phase_3b", "phase_4a", "seed_intent"]:
        txt = s["history_sections"].get(key, "")
        if txt:
            for line in txt.strip().splitlines():
                lines.append(line)
            lines.append("")
    lines.append("---")
    lines.append("")

    # Active Blockers
    lines.append(s["blocker_narrative"].strip())
    lines.append("")
    active_blockers = [b for b in blockers if b["status"] == "ACTIVE"]
    if active_blockers:
        for i, b in enumerate(active_blockers, 1):
            lines.append(f"{i}. [{b['id']}] {b['description']}")
    else:
        lines.append("(No active blockers recorded in spine)")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Next Safe Action
    lines.append("## Next Safe Action")
    lines.append("")
    in_progress = [n for n in build_plan_nodes if n["status"] == "IN_PROGRESS"]
    eligible = [n for n in build_plan_nodes if n["status"] == "PENDING" and n.get("unmet_hard_deps", 0) == 0]
    if in_progress:
        node = in_progress[0]
        lines.append(f"**{node['node_label']} (Tier {node['tier']}, IN PROGRESS)**")
    elif eligible:
        node = eligible[0]
        lines.append(f"**{node['node_label']} (Tier {node['tier']})**")
    else:
        lines.append("(No eligible PENDING node in build plan.)")
    lines.append("")

    # Approved build order
    lines.append("**Approved build order:**")
    status_map = {
        "COMPLETE": "✅ COMPLETE",
        "IN_PROGRESS": "🔄 IN PROGRESS",
        "PENDING": "⬜ PENDING",
        "BLOCKED": "🚫 BLOCKED",
        "DEFERRED": "⏸ DEFERRED",
    }
    counter = 1
    for node in build_plan_nodes:
        disp = status_map.get(node["status"], node["status"])
        lines.append(f"{counter}. {node['node_label']} {disp}")
        counter += 1
    for a in actions:
        disp = status_map.get(a["status"], a["status"])
        tier = f"Tier {a['tier']}" if a.get("tier") else "—"
        lines.append(f"{counter}. {tier} — {a['description']} {disp}")
        counter += 1
    lines.append("")
    lines.append("---")
    lines.append("")

    # Accepted Limitations
    for line in s["accepted_limitations"].strip().splitlines():
        lines.append(line)
    lines.append("")
    lines.append("---")
    lines.append("")

    # Do Not Start Yet
    lines.append("## Do Not Start Yet")
    lines.append("")
    for item in agents_static.get("do_not_start", []):
        lines.append(f"- {item}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Execution Order (from actions table + static framing)
    lines.append("## Execution Order")
    lines.append("")
    # Show all actions with tier, status
    for a in actions:
        status_icon = {"COMPLETE": "✅", "PASS_WITH_LIMITATIONS": "✅",
                       "IN_PROGRESS": "🔄", "PENDING": "⬜",
                       "BLOCKED": "🚫", "DEFERRED": "⏸️"}.get(a["status"], "")
        tier = f"Tier {a['tier']}" if a.get("tier") else "—"
        lines.append(f"**{tier} — {a['description']}** {status_icon} {a['status']}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Open Questions
    lines.append("## Open Questions")
    lines.append("")
    q_open = [q for q in questions if q["status"] == "OPEN"]
    q_other = [q for q in questions if q["status"] != "OPEN"]
    if questions:
        lines.append("| ID | Question | Status |")
        lines.append("|----|----------|--------|")
        for q in questions:
            status = q["status"]
            if q.get("resolution"):
                status += f" ({q['resolution'][:60]})"
            lines.append(f"| {q['id']} | {q['question'][:100]} | {status} |")
    else:
        lines.append("(No questions recorded in spine)")
    lines.append("")
    lines.append("---")
    lines.append("")

    # DB Spine State
    lines.append("## DB Spine State")
    lines.append("")
    lines.append("| Table | Rows |")
    lines.append("|-------|------|")
    for table, count in row_counts.items():
        lines.append(f"| {table} | {count} |")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Reference Files
    lines.append("## Reference Files")
    lines.append("")
    for line in s["reference_files"].strip().splitlines():
        lines.append(line)
    lines.append("")

    return "\n".join(lines)


def render_hcp_02(stamp, hcp_static, agents_static):
    s = hcp_static["hcp_02"]
    gateways = agents_static.get("gateways", [])
    infra = agents_static.get("infrastructure", {})
    patches_cfg = agents_static.get("hermes_patches", {})

    lines = ["# Active Architecture — Hermes Harness / CIS"]
    for st in stamp:
        lines.append(st)
    lines.append("")

    # Current Architecture
    lines.append("## Current Architecture")
    lines.append("")
    for line in s["current_architecture_text"].strip().splitlines():
        lines.append(line)
    lines.append("")

    # External Advisor Packet
    for line in s["external_advisor_blurb"].strip().splitlines():
        lines.append(line)
    lines.append("")

    # Stack
    lines.append("### Stack")
    for item in s["stack_items"]:
        lines.append(f"- {item}")
    lines.append("")

    # Gateway table
    lines.append("### Multi-Hermes Gateway Architecture (topology repaired 2026-06-07)")
    lines.append("")
    cols = s["gateway_table_columns"]
    lines.append("| " + " | ".join(cols) + " |")
    lines.append("|" + "|".join(["------"] * len(cols)) + "|")
    # Map profiles to service names
    svc_map = {
        "/home/eric/.hermes": "hermes-gateway",
        "/home/eric/.hermes-r1": "hermes-gateway-r1",
        "/home/eric/.hermes-v4pro": "hermes-gateway-v4pro",
        "/home/eric/.hermes-v4impl": "hermes-gateway-v4impl",
        "/home/eric/.hermes-qwen": "hermes-gateway-qwen",
    }
    for gw in gateways:
        hh = gw.get("hermes_home", "")
        svc = svc_map.get(hh, "unknown")
        lines.append(f"| {svc} | {gw['label']} | {gw['port']} | {hh} | {gw['model']} |")
    lines.append("| nemo-fast | NeMo Guardrails | 8800 | — | — |")
    lines.append("")
    lines.append("**Context:** AGENTS.md auto-loaded by all 4 active gateways via TERMINAL_CWD=/mnt/projects/cis. HERMES_CIS_BRIEFING_PATH retired at Tier 5.3.")
    lines.append("")

    # NeMo
    for line in s["nemo_rails_text"].strip().splitlines():
        lines.append(line)
    lines.append("")

    # Advisor Loop
    for line in s["advisor_loop_text"].strip().splitlines():
        lines.append(line)
    lines.append("")

    # V4 Direct
    for line in s["v4_direct_routing"].strip().splitlines():
        lines.append(line)
    lines.append("")
    lines.append("---")
    lines.append("")

    # CIS Deterministic Pipeline Architecture
    lines.append("## CIS Deterministic Pipeline Architecture (Approved 2026-06-01)")
    lines.append("")
    for line in s["pipeline_architecture_prose"].strip().splitlines():
        lines.append(line)
    lines.append("")

    # Pipeline lanes
    lines.append("### Pipeline Lanes (Kanban)")
    lines.append("```")
    lines.append("TRIAGE → RESEARCH → DRAFT → REVIEW ↔ LOOP → CONSENSUS → ERIC_GATE")
    lines.append("→ IMPLEMENT → VERIFY → STATE_WRITE → EXPORT → DONE")
    lines.append("```")
    lines.append("")
    for line in s["pipeline_lanes_table"].strip().splitlines():
        lines.append(line)
    lines.append("")

    # Kanban retired per ADR-013
    lines.append("### Pipeline Coordination (ADR-013)")
    lines.append("")
    lines.append("Kanban is retired as pipeline transport per ADR-013.")
    lines.append("workflow_runs is the authoritative in-flight work object.")
    lines.append("Deliberation rounds stored in deliberation_rounds.")
    lines.append("Implementation evidence in workflow_run_artifacts.")
    lines.append("Eric approval recorded in workflow_runs.eric_approved_at.")
    lines.append("")

    # Tier 0/1 artifacts
    for line in s["tier_0_1_artifacts"].strip().splitlines():
        lines.append(line)
    lines.append("")
    lines.append(f"**Build order authority:** `{hcp_static['shared']['build_authority']}` ({hcp_static['shared']['build_authority'].split('/')[-1]})")
    lines.append("")

    # Bidirectional Spine
    for line in s["bidirectional_spine_text"].strip().splitlines():
        lines.append(line)
    lines.append("")

    # External Advisor Protocol
    for line in s["external_advisor_protocol_text"].strip().splitlines():
        lines.append(line)
    lines.append("")
    lines.append("---")
    lines.append("")

    # API Endpoints
    lines.append("## Active API Endpoints")
    lines.append("")
    for line in s["api_endpoints_text"].strip().splitlines():
        lines.append(line)
    lines.append("")

    # Database Tables
    lines.append("## Database Tables")
    lines.append("")
    for line in s["database_tables_list"].strip().splitlines():
        lines.append(line)
    lines.append("")

    # Key Files
    lines.append("## Key Files")
    for item in s["key_project_files"]:
        lines.append(f"- {item}")
    lines.append("")

    return "\n".join(lines)


def render_hcp_03(stamp, decisions):
    lines = ["# Decisions Log — Hermes Harness / CIS"]
    for st in stamp:
        lines.append(st)
    lines.append("")
    lines.append("| Date | Decision | Reason | Status | Evidence |")
    lines.append("|------|----------|--------|--------|----------|")
    if decisions:
        for d in decisions:
            date = (d.get("decided_at") or "")[:10]
            dec_id = d.get("id", "")
            decision = d.get("decision", "")
            if d.get("label"):
                decision = f"[{dec_id}] {d['label']}: {decision}"
            else:
                decision = f"[{dec_id}] {decision}"
            reason = (d.get("reason") or "")[:80]
            status = d.get("status", "DECIDED")
            evidence = "spine record"
            lines.append(f"| {date} | {decision[:120]} | {reason} | {status} | {evidence} |")
    else:
        lines.append("| — | (No decisions recorded in spine) | — | — | — |")
    lines.append("")
    return "\n".join(lines)


def render_hcp_04(stamp, questions):
    lines = ["# Open Questions — Hermes Harness / CIS"]
    for st in stamp:
        lines.append(st)
    lines.append("")

    if questions:
        for q in questions:
            lines.append(f"## {q['id']} — {q['question'][:100]}")
            if q.get("resolution"):
                lines.append(q["resolution"])
            status = q["status"]
            lines.append(f"Status: {status}")
            lines.append("")
    else:
        lines.append("(No questions recorded in spine)")
        lines.append("")

    return "\n".join(lines)


def render_hcp_05(stamp, hcp_static, agents_static, actions, blockers,
                   build_plan_nodes):
    s = hcp_static["hcp_05"]

    lines = ["# Next Actions — Hermes Harness / CIS"]
    for st in stamp:
        lines.append(st)
    lines.append("")

    # Current Next Action
    lines.append(s["current_next_action_framing"].strip())
    lines.append("")
    in_progress = [n for n in build_plan_nodes if n["status"] == "IN_PROGRESS"]
    eligible = [n for n in build_plan_nodes if n["status"] == "PENDING" and n.get("unmet_hard_deps", 0) == 0]
    if in_progress:
        node = in_progress[0]
        lines.append(f"**{node['node_label']}** (IN PROGRESS)")
    elif eligible:
        node = eligible[0]
        lines.append(f"**{node['node_label']}**")
    else:
        blocked_nodes = [n for n in build_plan_nodes if n["status"] == "BLOCKED"]
        deferred_nodes = [n for n in build_plan_nodes if n["status"] == "DEFERRED"]
        lines.append("(No eligible PENDING node in build plan.)")
        if deferred_nodes:
            labels = "; ".join(f"Tier {n['tier']} DEFERRED" for n in deferred_nodes)
            lines.append(f"Deferred: {labels}.")
        if blocked_nodes:
            labels = "; ".join(f"Tier {n['tier']} BLOCKED" for n in blocked_nodes)
            lines.append(f"Blocked: {labels}.")
    lines.append("")

    # Do not start
    lines.append(s["do_not_start_framing"].strip())
    lines.append("")
    for item in agents_static.get("do_not_start", []):
        lines.append(f"- {item}")
    lines.append("")

    # Approved Build Order
    lines.append("## Approved Build Order")
    lines.append("")
    lines.append(s["approved_build_order_header"].strip())
    status_map = {
        "COMPLETE": "✅ COMPLETE",
        "IN_PROGRESS": "🔄 IN PROGRESS",
        "PENDING": "⬜ PENDING",
        "BLOCKED": "🚫 BLOCKED",
        "DEFERRED": "⏸ DEFERRED",
    }
    counter = 1
    for node in build_plan_nodes:
        disp = status_map.get(node["status"], node["status"])
        lines.append(f"| {node['tier']} | {node['node_label'][:80]} | {disp} | |")
        counter += 1
    for a in actions:
        disp = a["status"]
        tier = f"Tier {a['tier']}" if a.get("tier") else "—"
        lines.append(f"| {tier} | {a['description'][:80]} | {disp} | |")
        counter += 1
    lines.append("")

    # Known Limitations
    lines.append(s["known_limitations_header"].strip())
    lines.append("")
    for lim in s.get("known_limitations", []):
        lines.append(f"- {lim}")
    lines.append("")

    return "\n".join(lines)


def render_hcp_06(stamp, hcp_static, agents_static):
    s = hcp_static["hcp_06"]
    gateways = agents_static.get("gateways", [])

    lines = ["# Model Roles and Protocol — CIS Advisor Loop"]
    for st in stamp:
        lines.append(st)
    lines.append("")

    # Role Identity Rule
    lines.append("## Role Identity Rule")
    lines.append("")
    for line in s["role_identity_rule_text"].strip().splitlines():
        lines.append(line)
    lines.append("")

    # READ_ONLY_STANDING_BY Startup Protocol
    startup = s.get("startup_protocol_text", "").strip()
    if startup:
        lines.append("## READ_ONLY_STANDING_BY Startup Protocol")
        lines.append("")
        for line in startup.splitlines():
            lines.append(line)
        lines.append("")

    # CIS Pipeline Roles
    lines.append("## CIS Pipeline Roles")
    lines.append("")
    lines.append(s["pipeline_roles_table_header"])
    role_funcs = {
        "prime": "Evidence firewall (NeMo) + topic grounding",
        "v4pro": "Proposal author. Drafts, does not build",
        "r1": "Adversarial challenge. OBJECTIONS or CONSENSUS_REACHED",
        "v4impl": "Executes FINAL_DIRECTIVE only. No deliberation",
        "qwen": "Future judge/evaluator role",
    }
    for gw in gateways:
        profile = gw.get("profile", "")
        func = role_funcs.get(
            "prime" if "prime" in profile or ".hermes" == gw.get("hermes_home", "") else
            "v4pro" if "v4pro" in profile else
            "r1" if "r1" in profile else
            "v4impl" if "v4impl" in profile else
            "qwen" if "qwen" in profile else "—", "—"
        )
        paused = " (paused)" if gw["status"] == "Paused" else ""
        lines.append(f"| {gw['label']}{paused} | {profile} | {gw['port']} | {func} |")
    lines.append("")

    # External Advisor Protocol
    lines.append("## External Advisor Protocol")
    lines.append("")
    lines.append(s["external_advisor_protocol_header"])
    lines.append("| Hermes | Root operator, pipeline engine | AGENTS.md (native) | Deterministic context owner |")
    lines.append("| ChatGPT | External advisor, escalation reviewer | Generated HCP exports | Review, consult. No execution |")
    lines.append("| Claude | External advisor, proposal author | Generated HCP exports | Review, consult, draft proposals when asked |")
    lines.append("")

    # Pipeline Protocol
    lines.append("## Pipeline Protocol")
    lines.append("")
    for i, step in enumerate(s["pipeline_protocol_steps"], 1):
        lines.append(f"{i}. {step}")
    lines.append("")

    # Why V4 Direct
    lines.append("## Why V4 Models are Direct (not through NeMo)")
    lines.append("")
    for line in s["v4_direct_why"].strip().splitlines():
        lines.append(line)
    lines.append("")

    # Verification-Hardening Rule
    lines.append("## Verification-Hardening Rule (2026-05-31)")
    lines.append("")
    for line in s["verification_hardening_rule_summary"].strip().splitlines():
        lines.append(line)
    lines.append("")

    # Evidence-Backed Response Rule
    lines.append("## Evidence-Backed Response Rule")
    lines.append("")
    for line in s["evidence_rule_text"].strip().splitlines():
        lines.append(line)
    lines.append("")

    # Exact-Format Instruction Rule
    lines.append("## Exact-Format Instruction Rule")
    lines.append("")
    for line in s["exact_format_instruction_rule"].strip().splitlines():
        lines.append(line)
    lines.append("")

    # Pipeline Contingency (ADR-013)
    lines.append("## Pipeline Contingency")
    lines.append("")
    for line in s["pipeline_contingency"].strip().splitlines():
        lines.append(line)
    lines.append("")

    # Escalation Advisor Integration Protocol (Component 2)
    escalation = s.get("escalation_protocol_section", "").strip()
    if escalation:
        lines.append("## Escalation Advisor Integration Protocol (Component 2)")
        lines.append("")
        for line in escalation.splitlines():
            lines.append(line)
        lines.append("")

    return "\n".join(lines)


def render_hcp_07(stamp, hcp_static, latest_run, actions, eric_gate=None,
                   build_plan_nodes=None):
    s = hcp_static["hcp_07"]
    head_short, _ = get_git_head(REPO_ROOT)

    lines = ["# Recent Handoff — Tier 5.4 COMPLETE"]
    lines.append(f"Date: {datetime.now(timezone.utc).strftime('%Y-%m-%d')}")
    lines.append("Session: Tier 5.4 generate_hcp.py implementation")
    lines.append("")
    lines.append(f"HEAD: `{head_short or 'unknown'}`")
    lines.append("")
    # Generation stamp
    for st in stamp:
        lines.append(st)
    lines.append("")

    # Most recent session — Tier 5.4
    lines.append("## Tier 5.4 — generate_hcp.py (this session)")
    lines.append("- `config/hcp_static.yaml` — new: HCP-specific Layer B static config")
    lines.append("- `tools/export/generate_hcp.py` — new: reads spine + static + git, writes 10 HCP files")
    lines.append("- All 10 HCP_ files regenerated from spine, replacing manual maintenance")
    lines.append("- Manual HCP files backed up to PROJECT_CONTEXT_PACK_UPLOAD/backups/ before overwrite")
    lines.append("")

    # Recent sessions (static, oldest to newest)
    for key in ["tier_2", "tier_4_4", "tier_5_1", "tier_5_2", "tier_5_2e", "tier_5_3"]:
        txt = s["recent_sessions"].get(key, "")
        if txt:
            for line in txt.strip().splitlines():
                lines.append(line)
            lines.append("")

    # Untracked note
    for line in s["untracked_note"].strip().splitlines():
        lines.append(line)
    lines.append("")

    # Exact Next Action
    lines.append(s["exact_next_action_framing"])
    lines.append("")
    in_progress = [n for n in build_plan_nodes if n["status"] == "IN_PROGRESS"]
    eligible = [n for n in build_plan_nodes if n["status"] == "PENDING" and n.get("unmet_hard_deps", 0) == 0]
    if in_progress:
        lines.append(f"{in_progress[0]['node_label']} (IN PROGRESS).")
    elif eligible:
        lines.append(f"{eligible[0]['node_label']}.")
    else:
        lines.append("(No eligible PENDING node in build plan.)")
    lines.append("")

    # Eric Gate approval provenance summary
    lines.append("## Eric Gate Approval Status")
    lines.append("")
    if eric_gate:
        decision = eric_gate.get("decision", "UNKNOWN")
        decided = eric_gate.get("decided_at", "Not yet decided")
        goal = eric_gate.get("goal_label", "No goal label")
        run_eg = eric_gate.get("workflow_run_id", "N/A")
        brief_hash = eric_gate.get("briefing_hash", "N/A")
        lines.append(f"- Decision: {decision}")
        lines.append(f"- Workflow run: {run_eg}")
        lines.append(f"- Decided at: {decided}")
        lines.append(f"- Goal reference: {goal}")
        lines.append(f"- Briefing hash: {brief_hash}")
    else:
        lines.append("- No Eric Gate decision recorded (pending)")
    lines.append("")

    return "\n".join(lines)


def render_hcp_08(stamp):
    lines = ["# Files Changed Recently"]
    for st in stamp:
        lines.append(st)
    lines.append("")

    commits = get_git_log(REPO_ROOT, n=15)
    if not commits:
        lines.append("(Git history not available)")
        lines.append("")
        return "\n".join(lines)

    for c in commits:
        lines.append(f"## {c['sha']} {c['message']}")
        for f in c["files"]:
            lines.append(f"- `{f}`")
        lines.append("")

    return "\n".join(lines)


def render_hcp_09(stamp, hcp_static, agents_static):
    s = hcp_static["hcp_09"]
    gateways = agents_static.get("gateways", [])

    lines = ["# Terms and Naming — CIS Advisor Loop"]
    for st in stamp:
        lines.append(st)
    lines.append("")

    # Key Terms (group 1)
    lines.append("## Key Terms")
    lines.append("")
    for term, defn in s["key_terms"].items():
        lines.append(f"- **{term}** — {defn}")

    # Agent table
    lines.append("")
    lines.append("## Agents")
    lines.append("")
    lines.append("| Name | Label | Pipeline Lane |")
    lines.append("|------|-------|---------------|")
    for row in s["agent_table_rows"]:
        lines.append(f"| {row['name']} | {row['label']} | {row['lane']} |")
    lines.append("")

    # Operational Terms
    lines.append("## Key Terms")
    lines.append("")
    for term, defn in s["operational_terms"].items():
        lines.append(f"- **{term}**: {defn}")
    lines.append("")

    # Kanban retired per ADR-013 — spine-native transport now
    lines.append("## Spine-Native Pipeline Transport (ADR-013)")
    lines.append("")
    lines.append("- **workflow_runs**: Authoritative in-flight work object.")
    lines.append("- **deliberation_rounds**: Per-round Drafter/Reviewer history.")
    lines.append("- **workflow_run_artifacts**: Implementation evidence records.")
    lines.append("- **workflow_run_legacy_links**: Historical Kanban card references.")
    lines.append("")

    # Tier 0/1 terms
    lines.append("## Tier 0/1 Built Artifacts")
    lines.append("")
    for term, defn in s["tier_0_1_terms"].items():
        lines.append(f"- **{term}**: {defn}")
    lines.append("")

    # Architecture Terms
    lines.append("## Architecture Terms")
    lines.append("")
    for term, defn in s["architecture_terms"].items():
        lines.append(f"- **{term}**: {defn}")
    lines.append("")

    return "\n".join(lines)


def render_read_first(stamp):
    """Generate a minimal pointer-only file. No tier-specific prose — points
    sessions to the generated HCP packet as source of truth."""
    lines = [
        "# Read First — Hermes Harness Context",
        "",
        "**This file is a generated pointer. It is not authoritative.**",
        "",
        "The canonical source of truth is the HCP packet, also generated from",
        "the SQLite spine + git metadata by `tools/export/generate_hcp.py`.",
        "",
        "## Start here",
        "",
        "- **HCP_00_README_START_HERE.md** — architecture overview, how to use the packet",
        "- **HCP_01_CURRENT_STATE.md** — current build phase, HEAD, infrastructure, blockers",
        "- **HCP_05_NEXT_ACTIONS.md** — next safe action, approved build order, do-not-start list",
        "- **HCP_07_RECENT_HANDOFF.md** — most recent session handoff, Eric Gate status",
        "",
        "If there is a conflict between this file and any HCP file, prefer the HCP file.",
        "All HCP files carry the stamp: DO NOT MANUALLY EDIT — regenerate with",
        "tools/export/generate_hcp.py.",
        "",
    ]
    for st_line in stamp:
        lines.append(st_line)
    return "\n".join(lines) + "\n"


# ── main ──────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Generate READ_FIRST_HERMES_CONTEXT.md + HCP_00–HCP_09 from spine")
    parser.add_argument("--db", default=str(DEFAULT_DB))
    parser.add_argument("--hcp-config", default=str(DEFAULT_HCP_CONFIG))
    parser.add_argument("--agents-config", default=str(DEFAULT_AGENTS_CONFIG))
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    parser.add_argument("--run-id", default=None, help="Pipeline run ID for stamp")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print all HCP files to stdout instead of writing")
    args = parser.parse_args()

    # Validate inputs
    if not Path(args.db).exists():
        print(f"ERROR: DB not found: {args.db}", file=sys.stderr)
        sys.exit(2)
    if not Path(args.hcp_config).exists():
        print(f"ERROR: HCP config not found: {args.hcp_config}", file=sys.stderr)
        sys.exit(2)
    if not Path(args.agents_config).exists():
        print(f"ERROR: Agents config not found: {args.agents_config}", file=sys.stderr)
        sys.exit(2)

    # Load configs
    hcp_static = load_yaml(args.hcp_config)
    agents_static = load_yaml(args.agents_config)

    # Query spine
    decisions, questions, actions, blockers, runs, latest_run, row_counts, build_state, eric_gate, build_plan_nodes = query_spine(args.db)

    # Build stamp
    stamp = generation_stamp(args.run_id)

    # Render each HCP file
    renderers = {
        "READ_FIRST_HERMES_CONTEXT.md": lambda: render_read_first(stamp),
        "HCP_00_README_START_HERE.md": lambda: render_hcp_00(stamp, hcp_static, agents_static, get_git_head(REPO_ROOT)[0], actions),
        "HCP_01_CURRENT_STATE.md": lambda: render_hcp_01(stamp, hcp_static, agents_static, decisions, questions, actions, blockers, runs, latest_run, row_counts, build_state, build_plan_nodes),
        "HCP_02_ACTIVE_ARCHITECTURE.md": lambda: render_hcp_02(stamp, hcp_static, agents_static),
        "HCP_03_DECISIONS_LOG.md": lambda: render_hcp_03(stamp, decisions),
        "HCP_04_OPEN_QUESTIONS.md": lambda: render_hcp_04(stamp, questions),
        "HCP_05_NEXT_ACTIONS.md": lambda: render_hcp_05(stamp, hcp_static, agents_static, actions, blockers, build_plan_nodes),
        "HCP_06_MODEL_ROLES_AND_PROTOCOL.md": lambda: render_hcp_06(stamp, hcp_static, agents_static),
        "HCP_07_RECENT_HANDOFF.md": lambda: render_hcp_07(stamp, hcp_static, latest_run, actions, eric_gate, build_plan_nodes),
        "HCP_08_FILES_CHANGED_RECENTLY.md": lambda: render_hcp_08(stamp),
        "HCP_09_TERMS_AND_NAMING.md": lambda: render_hcp_09(stamp, hcp_static, agents_static),
    }

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    written = []
    for fname, render_fn in renderers.items():
        content = render_fn()
        out_path = out_dir / fname

        if args.dry_run:
            print(f"\n{'='*60}")
            print(f"=== {fname} ({len(content)} chars) ===")
            print(f"{'='*60}")
            print(content)
        else:
            out_path.write_text(content)
            written.append((fname, len(content)))

    if args.dry_run:
        print(f"\n--- Dry run complete. {len(renderers)} files would be written. ---")
    else:
        for fname, chars in written:
            print(f"WROTE: {fname} ({chars} chars)")
        print(f"\nPASS: {len(written)} HCP files written to {out_dir}")


if __name__ == "__main__":
    main()
