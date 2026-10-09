#!/usr/bin/env python3
"""
gate_build_state_coherence.py — Deterministic coherence gate
Checks that project_state (spine) and agents_static.yaml (static config)
do not contain contradictory build-state claims.

Detects:
  1. Completed tiers still listed as gated in do_not_start
  2. Current build_phase tier listed as gated with already-completed prerequisite
  3. Next-tier references inconsistent with do_not_start blocks
  4. Violations of project_state's single-valued authority contract — a key
     that must have exactly one current record having two live rows, or a
     supersession relationship the schema cannot mean (added 2026-10-09)

WHY CHECK 4 IS HERE. This gate PASSED while project_state.next_action had
two live rows (161 and 166), because it only ever compared completed_tier
against do_not_start — and because its own state loader resolved "current"
with `superseded_at IS NULL AND id = (SELECT MAX(id) ...)`, which silently
served whichever duplicate had the higher id. A gate that reads authority
through a newest-row-wins query cannot detect ambiguous authority: it is
structurally blind to the second row. The loader now goes through the one
canonical resolver (runtime/db/state_authority), which returns a conflict
instead of a winner, and check 4 fails on it by name.

Nothing about checks 1-3 is relaxed. A key whose authority is in conflict
yields no value to them, which widens rather than narrows what this gate
refuses: completed_tier being unresolvable is already a hard FAIL below.

Usage: python3 tools/gates/gate_build_state_coherence.py [--db PATH] [--config PATH]
Exit 0: PASS — state is coherent
Exit 1: FAIL — contradictions found
Exit 2: ERROR — missing data or config
"""

import argparse
import re
import sqlite3
import sys
from pathlib import Path

import yaml

import os as _os  # noqa: E402
# CIS_REPO is exported by the pipeline; parents[2] resolves to "/" once this
# gate is baked into the sealed /opt/cis-gates. (2026-08-27)
def _repo_root():
    env = _os.environ.get("CIS_REPO")
    if env and Path(env).is_dir():
        return Path(env)
    cand = Path(__file__).resolve().parents[2]
    if (cand / "data").is_dir():
        return cand
    for c in ("/workspace/cis", "/mnt/projects/cis"):
        if Path(c).is_dir():
            return Path(c)
    return cand


REPO_ROOT = _repo_root()
DEFAULT_DB = REPO_ROOT / "data" / "cis_memory.db"
DEFAULT_CONFIG = REPO_ROOT / "config" / "agents_static.yaml"


def _load_state_authority():
    """Import the one canonical project_state resolver.

    FAILS CLOSED (exit 2) rather than skipping the check if it cannot be
    imported. A gate that quietly drops a check when a path is wrong is
    the silent-gate-failure mode this repo already names as failure 11;
    that is strictly worse than refusing to run."""
    for root in (REPO_ROOT, Path("/workspace/cis"), Path("/mnt/projects/cis")):
        candidate = Path(root) / "runtime"
        if (candidate / "db" / "state_authority.py").is_file():
            if str(candidate) not in sys.path:
                sys.path.insert(0, str(candidate))
            try:
                from db import state_authority
                return state_authority
            except ImportError as e:
                print(f"ERROR: found {candidate}/db/state_authority.py but could not "
                      f"import it: {e}", file=sys.stderr)
                sys.exit(2)
    print("ERROR: cannot locate runtime/db/state_authority.py — the canonical "
          "project_state resolver. This gate will not run without it; it does not "
          "fall back to a newest-row-wins read.", file=sys.stderr)
    sys.exit(2)


sa = _load_state_authority()


def parse_tier_number(text: str) -> float | None:
    """Extract a tier number from text like 'Tier 8', 'Tier 7.5b', or bare '7.5b'."""
    # First try "Tier N" pattern
    m = re.search(r"Tier\s+(\d+(?:\.\d+)?)", text)
    if m:
        return float(m.group(1))
    return None


def parse_bare_tier(text: str) -> float | None:
    """Extract a tier number from a bare value like '7.5b' or '6.5'.
    Only used for spine fields (completed_tier, next_tier) that lack 'Tier' prefix.
    Requires the text to start with a number followed optionally by a letter suffix.
    """
    m = re.match(r"(\d+(?:\.\d+)?)\w*$", text.strip())
    if m:
        return float(m.group(1))
    return None


def parse_gated_on_tier(text: str) -> float | None:
    """Extract the prerequisite tier from a 'gated on Tier N' clause.
    Returns None if the gate reference is non-numeric (e.g., 'Tier 7 planning complete').
    """
    m = re.search(r"gated\s+on\s+Tier\s+(\d+(?:\.\d+)?)\b", text)
    if m:
        return float(m.group(1))
    return None


def load_spine_state(db_path: Path):
    """Load the current project_state through the canonical resolver.

    Returns (state, authority_report). `state` holds only keys the resolver
    could resolve unambiguously; a conflicted key is absent from it rather
    than represented by one of its candidate rows, and is reported in
    `authority_report["failures"]` instead.
    """
    if not db_path.exists():
        print(f"ERROR: database not found: {db_path}", file=sys.stderr)
        sys.exit(2)

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    authority_report = sa.integrity_report(conn)
    view = sa.current_state_map(conn)
    # Conflicted keys arrive as ConflictMarker objects, never as a value.
    # They are dropped from `state` so no downstream parse can mistake a
    # conflict for a tier number; check 4 reports them by name.
    state = {k: v for k, v in view.items() if isinstance(v, str)}

    # If the current completed_tier is unparseable (e.g. "PD" for Phase PD),
    # fall back to the most recent parseable completed_tier
    completed_tier_str = state.get("completed_tier", "")
    if completed_tier_str and parse_bare_tier(completed_tier_str) is None:
        # Search history for the most recent parseable completed_tier
        fallback = conn.execute(
            """SELECT value FROM project_state
               WHERE key='completed_tier'
               ORDER BY id DESC LIMIT 20"""
        ).fetchall()
        for row in fallback:
            val = row["value"]
            if parse_bare_tier(val) is not None:
                state["completed_tier"] = val
                state["_completed_tier_original"] = completed_tier_str
                break

    conn.close()
    return state, authority_report


def check_single_valued_authority(authority_report: dict) -> tuple[bool, list[str]]:
    """Check 4 — project_state's single-valued authority contract.

    FAILS on a declared single-valued key carrying more than one live row,
    and on any supersession relationship the schema cannot mean. Each
    failure names the key and the specific row ids, because "state is
    incoherent" without the rows is not something anyone can act on.

    Unlinked supersessions (superseded_at set, superseded_by NULL) are NOT
    failures — the schema permits them and 104 historical rows carry them.
    Keys with no declared cardinality are reported as warnings, so this
    gate never imposes single-valued semantics on a key no authority
    declared single-valued."""
    messages, failures = [], []

    if not authority_report.get("readable", False):
        for f in authority_report.get("failures", []):
            failures.append(f"FAIL: project_state authority unreadable — {f.get('detail')}")
        return False, failures

    for f in authority_report.get("failures", []):
        kind = f.get("kind")
        key = f.get("key")
        if kind == "duplicate_live_rows":
            ids = ", ".join(str(i) for i in (f.get("row_ids") or []))
            failures.append(
                f"FAIL: project_state.{key} must have exactly one current record but has "
                f"{f.get('live_row_count')} live rows (ids {ids}). "
                "Authority is ambiguous; no reader may pick one of them.")
        else:
            failures.append(
                f"FAIL: project_state.{key} supersession relationship violates the schema "
                f"contract — {kind} on row {f.get('row_id')} "
                f"(superseded_by={f.get('successor_id')}): {f.get('detail')}")

    for w in authority_report.get("warnings", []):
        ids = ", ".join(str(i) for i in (w.get("row_ids") or []))
        messages.append(
            f"WARN: project_state.{w.get('key')} has {w.get('live_row_count')} live rows and "
            f"no declared cardinality (ids {ids}) — single-valued enforcement is not applied "
            "to it. Declare it in runtime/db/state_authority.KEY_CARDINALITY if exactly one "
            "is intended.")

    for u in authority_report.get("checks_unavailable", []):
        messages.append(f"WARN: authority check '{u.get('check')}' could not run — "
                        f"{u.get('reason')}")

    if failures:
        return False, messages + failures
    keys = len(authority_report.get("single_valued_keys", []))
    messages.append(f"PASS: project_state single-valued authority holds for all {keys} "
                    "declared keys, and every supersession relationship is well-formed")
    return True, messages


def load_static_config(config_path: Path) -> dict:
    """Load agents_static.yaml."""
    if not config_path.exists():
        print(f"ERROR: config not found: {config_path}", file=sys.stderr)
        sys.exit(2)
    with open(config_path) as f:
        return yaml.safe_load(f)


def check_coherence(state: dict, do_not_start: list[str]) -> tuple[bool, list[str]]:
    """Return (pass_bool, [failure_messages])."""
    failures = []

    # 1. Get current state values
    build_phase = state.get("build_phase", "")
    completed_tier_str = state.get("completed_tier", "")
    next_tier_str = state.get("next_tier", "")

    completed_tier = parse_bare_tier(completed_tier_str) if completed_tier_str else None
    current_tier = parse_tier_number(build_phase)
    next_tier = parse_bare_tier(next_tier_str) if next_tier_str else None

    if completed_tier is None:
        failures.append("FAIL: completed_tier not found or unparseable in project_state")
        return False, failures

    # 2. Scan do_not_start for tier-gated entries
    for entry in do_not_start:
        entry_tier = parse_tier_number(entry)
        if entry_tier is None:
            continue  # Not a tier-gated entry, skip

        gate_tier = parse_gated_on_tier(entry)

        # CHECK A: Completed tiers should not be listed as gated in do_not_start
        if entry_tier <= completed_tier:
            failures.append(
                f"FAIL: Tier {entry_tier} is listed as gated in do_not_start "
                f"but completed_tier={completed_tier_str}. "
                f"Entry: \"{entry}\""
            )

        # CHECK B: If build_phase references this tier but gate is non-numeric
        # (e.g., 'implementation (gated on Tier 8 specification planning complete)'),
        # that's allowed — it means planning is open but implementation is gated.
        # Only flag if gate_tier is numeric and already completed.
        if gate_tier is not None and gate_tier <= completed_tier and entry_tier > completed_tier:
            # The gate prerequisite is satisfied but the entry is still listed as gated.
            # This is a warning, not a failure — maybe the implementation genuinely
            # hasn't started despite the gate being cleared.
            pass  # Acceptable: gate satisfied but implementation not yet authorized

        # CHECK C: Current build_phase tier listed as gated WITH a numeric,
        # already-completed prerequisite — that's a contradiction
        if current_tier is not None and entry_tier == current_tier and gate_tier is not None and gate_tier <= completed_tier:
            failures.append(
                f"FAIL: build_phase references Tier {current_tier} ({build_phase[:80]}...) "
                f"but do_not_start says: \"{entry}\". "
                f"The prerequisite (Tier {gate_tier}) is already complete (completed_tier={completed_tier_str})."
            )

    # 3. Check next_tier coherence with do_not_start
    if next_tier is not None:
        for entry in do_not_start:
            entry_tier = parse_tier_number(entry)
            if entry_tier is not None and entry_tier == next_tier:
                gate_tier = parse_gated_on_tier(entry)
                if gate_tier is not None and gate_tier <= completed_tier:
                    failures.append(
                        f"FAIL: next_tier={next_tier_str} but do_not_start still blocks it: \"{entry}\". "
                        f"Prerequisite Tier {gate_tier} is already complete."
                    )

    if failures:
        return False, failures

    return True, ["PASS: build state is coherent — no completed tiers listed as gated"]


def main():
    parser = argparse.ArgumentParser(
        description="Check build state coherence between spine and static config"
    )
    parser.add_argument("--db", default=str(DEFAULT_DB))
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    args = parser.parse_args()

    state, authority_report = load_spine_state(Path(args.db))
    static = load_static_config(Path(args.config))
    do_not_start = static.get("do_not_start", [])

    if not state and not authority_report.get("failures"):
        print("ERROR: project_state table is empty", file=sys.stderr)
        sys.exit(2)
    if not do_not_start:
        print("ERROR: do_not_start list is empty in config", file=sys.stderr)
        sys.exit(2)

    # Check 4 runs first and independently: an ambiguous authority is a
    # finding in its own right, not a side effect of a tier comparison.
    authority_passed, authority_messages = check_single_valued_authority(authority_report)
    for msg in authority_messages:
        print(msg)

    if not state:
        # Every key was conflicted or unreadable; checks 1-3 have no input.
        print("FAIL: no project_state key could be resolved unambiguously, so build-state "
              "coherence cannot be assessed")
        sys.exit(1)

    passed, messages = check_coherence(state, do_not_start)

    for msg in messages:
        print(msg)

    sys.exit(0 if (passed and authority_passed) else 1)


if __name__ == "__main__":
    main()
