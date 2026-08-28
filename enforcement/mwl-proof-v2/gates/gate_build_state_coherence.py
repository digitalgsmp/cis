#!/usr/bin/env python3
"""
gate_build_state_coherence.py — Deterministic coherence gate
Checks that project_state (spine) and agents_static.yaml (static config)
do not contain contradictory build-state claims.

Detects:
  1. Completed tiers still listed as gated in do_not_start
  2. Current build_phase tier listed as gated with already-completed prerequisite
  3. Next-tier references inconsistent with do_not_start blocks

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


def load_spine_state(db_path: Path) -> dict:
    """Load current (non-superseded) project_state rows."""
    if not db_path.exists():
        print(f"ERROR: database not found: {db_path}", file=sys.stderr)
        sys.exit(2)

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    # Get the most recent non-superseded row per key
    rows = conn.execute(
        """SELECT key, value FROM project_state
           WHERE superseded_at IS NULL
           AND id = (
               SELECT MAX(id) FROM project_state ps2
               WHERE ps2.key = project_state.key AND ps2.superseded_at IS NULL
           )"""
    ).fetchall()
    state = {row["key"]: row["value"] for row in rows}

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
    return state


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

    state = load_spine_state(Path(args.db))
    static = load_static_config(Path(args.config))
    do_not_start = static.get("do_not_start", [])

    if not state:
        print("ERROR: project_state table is empty", file=sys.stderr)
        sys.exit(2)
    if not do_not_start:
        print("ERROR: do_not_start list is empty in config", file=sys.stderr)
        sys.exit(2)

    passed, messages = check_coherence(state, do_not_start)

    for msg in messages:
        print(msg)

    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
