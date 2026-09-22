#!/usr/bin/env python3
"""recovery_packet.py — external-advisor recovery packet generator
(queue 4.29 / CARD_02_EXTERNAL_RECOVERY_PACKET.md).

Produces a bounded, deterministic packet for an external advisor (a
ChatGPT/Claude subscription used as fallback) to diagnose or repair this
VM when internal CIS pipeline/container components are unavailable, or
whenever Eric wants an external advisor looking at the system.

Contract:
- Draws exclusively from tools/state/canonical_state.get_canonical_state().
  This module never independently queries or reconstructs project truth --
  if the canonical read model's answer changes, this module's output
  changes with it and nothing here needs separate upkeep.
- Read-only. Nothing in this module writes to the database or to any
  generated artifact.
- Bounded: every list from the canonical state is capped at _CAP items
  before serialization, so the packet stays safe to paste into a
  subscription model's context window. Truncation is always reported
  (an "items"/"truncated" wrapper), never silent.
- Works without Braingate, Card Factory, Card Runner, pipeline agent
  gateways, or containerized worker health -- it needs only the host
  filesystem and the spine database, because its purpose is helping
  repair those higher layers when they are down. The one addition beyond
  canonical_state's own observed_runtime_health is a Workbench Flask
  listener check (port 5000, see runtime/cis_workbench.sh) -- kept here
  rather than in canonical_state.py so Card 01's independently reviewed
  and hash-pinned file (see data/agent_handoffs/WB-RECOVERY-01-single-
  authority/CARD_01_verification_PASS.json) stays untouched. Like
  canonical_state's own gateway checks, this is an observed live fact,
  never persisted or treated as authoritative.

Usage:
    python3 tools/state/recovery_packet.py                    # full packet, JSON
    python3 tools/state/recovery_packet.py --issue workbench  # focused packet
    python3 tools/state/recovery_packet.py --issue database --db PATH
"""
import argparse
import json
import socket
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(REPO_ROOT))
import canonical_state as cs  # noqa: E402
from tools.development import process_identity as pident  # noqa: E402

_CAP = 25  # max list items kept per section before truncation is reported

WORKBENCH_PORT = 5000

# Which canonical_state sections a focused packet includes beyond the
# global context (state revision, freshness, authority statement) that
# every packet carries regardless of focus.
ISSUE_AREAS = {
    "workbench": ["queue_focus", "open_blocked_deferred"],
    "gateway": ["observed_runtime_health"],
    "braingate": ["observed_runtime_health"],
    "queue": ["queue_focus", "open_blocked_deferred", "recent_verified_closed"],
    "closeout": ["open_blocked_deferred", "recent_verified_closed"],
    "card_factory": ["queue_focus", "open_blocked_deferred"],
    "container": ["observed_runtime_health"],
    "runtime": ["observed_runtime_health"],
    "database": ["source_table_freshness", "generated_artifact_freshness"],
    "ui": ["queue_focus", "open_blocked_deferred"],
}

FULL_SECTIONS = [
    "queue_focus", "open_blocked_deferred", "recent_verified_closed",
    "active_decisions", "open_questions", "discoveries_requiring_attention",
    "observed_runtime_health",
]

AUTHORITY_STATEMENT = (
    "The SQLite spine database (data/cis_memory.db, read only through "
    "tools/state/canonical_state.py) is the sole authoritative source of "
    "CIS project state. AGENTS.md, the HCP packet, docs/UNIFIED_BUILD_LIST.md, "
    "DEV-PIVOT_STATUS.md, and this recovery packet are all generated "
    "projections of that same state, never independent truth. If this "
    "packet conflicts with any of those files, trust this packet's "
    "state_revision/freshness fields over their prose, and regenerate "
    "those files rather than hand-editing them."
)

RECOVERY_INSTRUCTIONS = (
    "This packet is for an external advisor (ChatGPT/Claude subscription "
    "fallback) diagnosing or repairing this VM when internal pipeline/"
    "container components are unresponsive, or whenever Eric wants an "
    "external second opinion. Do not propose a second state store or a new "
    "'current state' document -- extend or query the existing spine/read "
    "model instead. Treat observed_runtime_health and workbench_state as "
    "live, non-authoritative snapshots taken at generation time only; they "
    "are never written back as fact. After making a fix, regenerate this "
    "packet and confirm state_revision changed the way you expect."
)


def _bound(value):
    """Recursively cap lists inside a canonical_state section, reporting
    how many items were dropped instead of silently truncating."""
    if isinstance(value, list):
        if len(value) <= _CAP:
            return [_bound(v) for v in value]
        kept = [_bound(v) for v in value[:_CAP]]
        return {"items": kept, "truncated": len(value) - _CAP}
    if isinstance(value, dict):
        return {k: _bound(v) for k, v in value.items()}
    return value


def get_port_identity(port):
    """Observed, non-authoritative: whose process(es) hold `port`, per
    tools/development/process_identity.py (queue 4.32 BEFORE_STAGE_CLOSEOUT
    discovery -- the Card 03 incident where the host killed the
    cis-pipeline container's main process, mistaking it for a standalone
    dev Flask process on this same port). Never crashes the packet: any
    failure degrades to an explicit error field, same as every other
    observed-health check in this module."""
    try:
        return pident.classify_port(port)
    except Exception as e:  # noqa: BLE001 -- observed health must degrade, not raise
        return {"port": port, "listening": None, "processes": [],
                "error": f"{type(e).__name__}: {e}"}


def get_workbench_state():
    """Observed, non-authoritative: is the Workbench Flask app's port
    listening, and -- per the Card 03 incident -- whose process actually
    holds it (host-standalone vs. the cis-pipeline container, which
    bind-mounts this same repo and can look identical by name/pid/cwd
    alone). Never persisted -- mirrors canonical_state's own gateway
    check (see module docstring for why this lives here, not there)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.3)
    try:
        s.connect(("127.0.0.1", WORKBENCH_PORT))
        listening = True
    except OSError:
        listening = False
    finally:
        s.close()
    return {
        "_note": "observed live at call time -- not authoritative, not persisted",
        "port": WORKBENCH_PORT,
        "listening": listening,
        "port_identity": get_port_identity(WORKBENCH_PORT),
    }


def build_recovery_packet(issue=None, db_path=None):
    if issue and issue not in ISSUE_AREAS:
        raise ValueError(f"unknown issue area {issue!r}; known: {sorted(ISSUE_AREAS)}")

    state = cs.get_canonical_state(db_path)

    packet = {
        "packet_kind": "cis_external_recovery_packet",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "state_revision": state["revision"],
        "state_computed_at": state["computed_at"],
        "authority_statement": AUTHORITY_STATEMENT,
        "recovery_instructions": RECOVERY_INSTRUCTIONS,
        "project_identity": {
            "repo_root": str(REPO_ROOT),
            "spine_db": state["source"],
        },
        "issue_focus": issue,
        # Always present regardless of focus, so a focused packet can never
        # mislead an advisor about how fresh/authoritative the rest is, or
        # about where current work actually stands (Card 04 R1 correction:
        # a truncated full packet previously lost 4.32 among 38 items with
        # no current_queue_item pointer at all).
        "current_focus": _bound(state["current_focus"]),
        "active_blockers": _bound(state["active_blockers"]),
        "source_table_freshness": state["source_table_freshness"],
        "generated_artifact_freshness": state["generated_artifact_freshness"],
        "dirty_git_state": {
            "repo_dirty": state["observed_runtime_health"]["repo_dirty"],
            "dirty_file_count": state["observed_runtime_health"]["dirty_file_count"],
        },
        "workbench_state": get_workbench_state(),
        "relevant_paths": {
            "spine_db": state["source"],
            "canonical_read_model": "tools/state/canonical_state.py",
            "this_generator": "tools/state/recovery_packet.py",
            "hcp_packet_dir": "PROJECT_CONTEXT_PACK_UPLOAD/",
            "unified_build_list": "docs/UNIFIED_BUILD_LIST.md",
        },
    }

    for name in (ISSUE_AREAS[issue] if issue else FULL_SECTIONS):
        packet[name] = _bound(state[name])

    return packet


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--issue", choices=sorted(ISSUE_AREAS), default=None,
                     help="focused packet for one problem area")
    ap.add_argument("--db", default=None)
    args = ap.parse_args()
    print(json.dumps(build_recovery_packet(args.issue, args.db), indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
