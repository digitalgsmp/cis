#!/usr/bin/env python3
"""test_agents_md_size_guard.py — WB1-D18 behavioural tests for the
AGENTS.md size guard and its diagnostics.

The defect these cover
----------------------
`tools/export/generate_agents_md.py` has a hard 20,000-character guard and
it works: it refuses to write an oversized projection. What it did not do
was say anything about size while succeeding. Section 1 of AGENTS.md is
nothing but the two spine values `project_state.build_phase` and
`current_direction`, an honest correction to them is routinely longer than
the prose it replaces, and the first visible symptom of crossing the limit
was the D13 pre-commit suite failing at its *seeding* step — an assertion
with no apparent connection to "your state text is too long". Revision 72
measured the live margin at ~559 characters with nothing warning about it.

The invariant
-------------
Every successful generation makes the current size and the remaining safety
margin observable; every oversized generation still fails closed, writing
nothing, with actionable information about the size violation. Neither
behaviour may alter authoritative content to satisfy the guard.

Approach
--------
Two layers. The arithmetic and section attribution are exercised directly
against the module's pure functions. The guard itself is exercised
end-to-end through the real generator and the real orchestrator:

  * against a purpose-built minimal spine, so the test can place the
    projection deliberately far below, just below, and above the limit
    without touching the 5.6 GB production database; and
  * once against the real spine, read-only (`CIS_SPINE_PATH`, the same
    convention as the sibling suites), so the numbers reported for the
    projection this repository actually commits are proven too.

Nothing in the actual repository is written to: every run is given its own
`--out` under a temporary directory.

Run:
    python3 tools/export/tests/test_agents_md_size_guard.py
"""
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
PROD_DB = os.environ.get("CIS_SPINE_PATH", os.path.join(REPO_ROOT, "data", "cis_memory.db"))
GENERATOR = os.path.join(REPO_ROOT, "tools", "export", "generate_agents_md.py")
GENERATE_ALL = os.path.join(REPO_ROOT, "tools", "export", "generate_all.py")  # sandboxed per test
AGENTS_CONFIG = os.path.join(REPO_ROOT, "config", "agents_static.yaml")

sys.path.insert(0, os.path.join(REPO_ROOT, "tools", "export"))
import generate_agents_md as gen  # noqa: E402

results = []


def check(label, cond, detail=""):
    results.append(f"{label}: PASS" if cond else f"{label}: FAIL — {detail}")


# ── minimal spine ──────────────────────────────────────────────────────────
#
# Only the tables generate_agents_md.query_spine() reads, with only the
# columns it selects. Deliberately small: the point is to control the size
# of section 1 exactly, which the production spine does not allow.

MINIMAL_SCHEMA = """
CREATE TABLE workflow_runs (
    id TEXT PRIMARY KEY, topic TEXT, result TEXT,
    rounds_completed INTEGER, created_at TEXT, completed_at TEXT);
CREATE TABLE project_decisions (
    id TEXT PRIMARY KEY, label TEXT, status TEXT, decided_at TEXT);
CREATE TABLE open_questions (
    id TEXT PRIMARY KEY, question TEXT, status TEXT, opened_at TEXT);
CREATE TABLE build_plan_nodes (
    id INTEGER PRIMARY KEY, project_id TEXT, node_label TEXT, tier TEXT,
    sequence INTEGER, status TEXT, blocked_reason TEXT);
CREATE TABLE next_actions (
    id TEXT PRIMARY KEY, tier TEXT, description TEXT, status TEXT,
    created_at TEXT);
CREATE TABLE active_blockers (
    id TEXT PRIMARY KEY, description TEXT, status TEXT, created_at TEXT);
CREATE TABLE project_state (
    id INTEGER PRIMARY KEY AUTOINCREMENT, key TEXT, value TEXT,
    superseded_at TEXT);
CREATE TABLE goal_references (
    id INTEGER PRIMARY KEY, goal_label TEXT);
CREATE TABLE eric_gate_approvals (
    id TEXT PRIMARY KEY, decision TEXT, decided_at TEXT,
    goal_reference_id INTEGER, workflow_run_id TEXT, is_current INTEGER);
CREATE TABLE session_handoffs (
    id INTEGER PRIMARY KEY, date TEXT, title TEXT, summary TEXT,
    decisions TEXT, next_actions TEXT, claude_context TEXT,
    eric_feedback TEXT, gateway_status TEXT, git_head TEXT,
    is_current INTEGER, created_at TEXT);
"""


_spine_seq = iter(range(1, 10000))


def make_spine(tmpdir, build_phase, current_direction="direction."):
    """A minimal spine whose section 1 is exactly the two values given.
    Each call gets its own file so a test can build several."""
    path = os.path.join(tmpdir, f"minimal-{next(_spine_seq)}.db")
    conn = sqlite3.connect(path)
    conn.executescript(MINIMAL_SCHEMA)
    conn.execute("INSERT INTO project_state (key, value) VALUES ('build_phase', ?)",
                 (build_phase,))
    conn.execute("INSERT INTO project_state (key, value) VALUES ('current_direction', ?)",
                 (current_direction,))
    conn.commit()
    conn.close()
    return path


def generate(db, out, extra=()):
    """Run the real generator. Returns (rc, combined output)."""
    r = subprocess.run(
        ["python3", GENERATOR, "--db", db, "--config", AGENTS_CONFIG,
         "--out", out, "--run-id", "run-aaaaaaaaaaaa", *extra],
        capture_output=True, text=True, timeout=120, cwd=REPO_ROOT,
    )
    return r.returncode, r.stdout + r.stderr


def parse_pass_line(output):
    """(chars, limit, margin) from the success summary, or None."""
    m = re.search(r"PASS: AGENTS\.md written to .* \((\d+) chars, "
                  r"limit (\d+), margin (-?\d+) chars\)", output)
    return tuple(int(g) for g in m.groups()) if m else None


def padding(n):
    """n characters of filler that cannot be mistaken for real authority."""
    return "X" * n


def size_for(db, out_dir):
    """The size the generator produces for `db`, via --dry-run so nothing
    is written. Used to calibrate a target size before asserting on it."""
    rc, out = generate(db, os.path.join(out_dir, "unused.md"), extra=("--dry-run",))
    assert rc == 0, out
    m = re.search(r"--- (\d+) chars \(limit (\d+), margin (-?\d+) chars\) ---", out)
    assert m, f"dry-run did not report size: {out[-400:]}"
    return int(m.group(1))


# ── 1. the arithmetic and attribution are reported, not guessed ────────────

def test_size_report_arithmetic():
    rendered = "header\n\n## 1. A\n" + padding(100) + "\n## 2. B\n" + padding(10)
    report = gen.size_report(rendered)
    check("size_report counts the characters it was given",
          report["char_count"] == len(rendered),
          f"{report['char_count']} != {len(rendered)}")
    check("size_report reports the guard's own limit",
          report["char_limit"] == gen.CHAR_LIMIT, str(report["char_limit"]))
    check("size_report's margin is limit minus size",
          report["char_margin"] == gen.CHAR_LIMIT - len(rendered),
          str(report["char_margin"]))
    names = [name for name, _ in report["sections"]]
    check("sections are attributed by heading, largest first",
          names[0] == "1. A" and "2. B" in names, str(report["sections"]))
    check("the file header above section 1 is attributed, not lost",
          sum(n for _, n in report["sections"]) == len(rendered),
          f"{sum(n for _, n in report['sections'])} != {len(rendered)}")


def test_size_report_margin_is_negative_exactly_when_oversized():
    check("margin is negative for an oversized projection",
          gen.size_report(padding(gen.CHAR_LIMIT + 1))["char_margin"] == -1,
          "oversized projection did not report a negative margin")
    check("margin is zero at exactly the limit",
          gen.size_report(padding(gen.CHAR_LIMIT))["char_margin"] == 0,
          "a projection exactly at the limit did not report zero margin")


# ── 2. a successful generation makes size, limit and margin observable ─────

def test_successful_generation_reports_size_limit_and_margin():
    tmp = tempfile.mkdtemp(prefix="d18-")
    try:
        db = make_spine(tmp, "Phase under test.")
        out = os.path.join(tmp, "AGENTS.md")
        rc, output = generate(db, out)
        check("a projection below the limit generates successfully",
              rc == 0, f"rc={rc}\n{output}")
        parsed = parse_pass_line(output)
        check("the success summary reports size, limit and margin together",
              parsed is not None, output[-400:])
        if parsed:
            chars, limit, margin = parsed
            with open(out, encoding="utf-8") as f:
                written = f.read()
            check("the reported size is the size actually written",
                  chars == len(written), f"reported {chars}, wrote {len(written)}")
            check("the reported limit is the guard's limit",
                  limit == gen.CHAR_LIMIT, str(limit))
            check("the reported margin is limit minus the size written",
                  margin == gen.CHAR_LIMIT - len(written), str(margin))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_comfortable_margin_does_not_warn():
    tmp = tempfile.mkdtemp(prefix="d18-")
    try:
        db = make_spine(tmp, "Short phase.")
        rc, output = generate(db, os.path.join(tmp, "AGENTS.md"))
        parsed = parse_pass_line(output)
        check("a comfortable margin still succeeds", rc == 0, output[-300:])
        check("a comfortable margin is reported without a warning",
              parsed and parsed[2] > gen.MARGIN_WARN_CHARS and "WARN:" not in output,
              f"parsed={parsed}\n{output[-300:]}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_thin_margin_warns_but_still_succeeds():
    """The condition revision 72 found and nothing announced: under the
    limit, but a correction away from it."""
    tmp = tempfile.mkdtemp(prefix="d18-")
    try:
        base = size_for(make_spine(tmp, ""), tmp)
        target = gen.CHAR_LIMIT - (gen.MARGIN_WARN_CHARS // 2)
        db = make_spine(tmp, padding(target - base))
        out = os.path.join(tmp, "AGENTS.md")
        rc, output = generate(db, out)
        parsed = parse_pass_line(output)
        check("a thin margin does not fail the generation",
              rc == 0 and os.path.exists(out), f"rc={rc}\n{output[-400:]}")
        check("a thin margin is warned about before the guard ever fires",
              "WARN:" in output and "margin" in output, output[-400:])
        check("the warning names the limit being approached",
              str(gen.CHAR_LIMIT) in output, output[-400:])
        check("the thin-margin run is genuinely under the limit",
              parsed and 0 < parsed[2] <= gen.MARGIN_WARN_CHARS, f"parsed={parsed}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ── 3. over the limit still fails closed, now legibly ──────────────────────

def test_oversized_generation_fails_closed_with_actionable_diagnostics():
    tmp = tempfile.mkdtemp(prefix="d18-")
    try:
        base = size_for(make_spine(tmp, ""), tmp)
        db = make_spine(tmp, padding(gen.CHAR_LIMIT - base + 500))
        out = os.path.join(tmp, "AGENTS.md")
        rc, output = generate(db, out)
        check("an oversized projection is refused",
              rc == 1, f"rc={rc}\n{output[-400:]}")
        check("an oversized projection writes nothing",
              not os.path.exists(out), "output file was written anyway")
        check("the refusal states the size and the limit",
              re.search(rf"Output is \d+ chars, exceeds {gen.CHAR_LIMIT} limit",
                        output) is not None, output[-500:])
        check("the refusal states the overage, not just that there is one",
              re.search(r"by \d+ chars", output) is not None, output[-500:])
        check("the refusal names the sections that account for the size",
              "largest sections:" in output and "1. Current Build Phase" in output,
              output[-600:])
        check("the refusal names the two spine values that own section 1",
              "build_phase" in output and "current_direction" in output,
              output[-600:])
        check("the refusal says not to raise the limit or truncate authority",
              "do not raise the limit" in output and "truncate" in output,
              output[-600:])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_oversized_generation_leaves_an_existing_projection_intact():
    """Fail-closed means the previous projection survives, not that a
    half-written one replaces it."""
    tmp = tempfile.mkdtemp(prefix="d18-")
    try:
        base = size_for(make_spine(tmp, ""), tmp)
        out = os.path.join(tmp, "AGENTS.md")
        rc, _ = generate(make_spine(tmp, "Fits easily."), out)
        assert rc == 0
        with open(out, encoding="utf-8") as f:
            good = f.read()
        rc, output = generate(make_spine(tmp, padding(gen.CHAR_LIMIT - base + 500)), out)
        with open(out, encoding="utf-8") as f:
            after = f.read()
        check("a refused oversized run leaves the prior projection byte-identical",
              rc == 1 and after == good, f"rc={rc}; content changed={after != good}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ── 4. the diagnostics never edit authority to fit ─────────────────────────

def test_diagnostics_do_not_alter_authoritative_content():
    tmp = tempfile.mkdtemp(prefix="d18-")
    try:
        base = size_for(make_spine(tmp, ""), tmp)
        phase = "PHASE AUTHORITY " + padding(
            gen.CHAR_LIMIT - base - (gen.MARGIN_WARN_CHARS // 2) - 16)
        direction = "DIRECTION AUTHORITY, every character of it."
        out = os.path.join(tmp, "AGENTS.md")
        rc, output = generate(make_spine(tmp, phase, direction), out)
        with open(out, encoding="utf-8") as f:
            written = f.read()
        check("the warned-about run still succeeded", rc == 0, output[-300:])
        check("a warning does not shorten build_phase in the projection",
              phase in written, "build_phase value was not reproduced verbatim")
        check("a warning does not shorten current_direction in the projection",
              f"Direction: {direction}" in written,
              "current_direction value was not reproduced verbatim")
        check("no truncation marker was introduced",
              "..." not in written.split("## 2.")[0], "section 1 looks truncated")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_generation_remains_deterministic():
    tmp = tempfile.mkdtemp(prefix="d18-")
    try:
        db = make_spine(tmp, "Deterministic phase.")
        first, second = os.path.join(tmp, "a.md"), os.path.join(tmp, "b.md")
        rc1, _ = generate(db, first)
        rc2, _ = generate(db, second)
        with open(first, encoding="utf-8") as f:
            a = f.read()
        with open(second, encoding="utf-8") as f:
            b = f.read()
        check("two runs over identical inputs produce identical projections",
              rc1 == 0 and rc2 == 0 and a == b, "projections differed")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ── 5. the orchestrator the closeout path runs carries the numbers ─────────

def make_sandbox():
    """A throwaway git repo holding real generator sources, so generate_all's
    REPO_ROOT resolves inside it and nothing in the real repository is
    written. Same construction as the D13 suite."""
    sandbox = tempfile.mkdtemp(prefix="d18-all-")
    # runtime/db is in this list because the generators' real dependency set
    # grew on 2026-10-09: generate_agents_md and generate_hcp now resolve
    # project_state through runtime/db/state_authority.py instead of each
    # running its own `superseded_at IS NULL AND id = MAX(id)` query. A
    # sandbox without it is no longer a complete copy of "real generator
    # sources", and the generator correctly fails rather than falling back
    # to a newest-row-wins read.
    for rel in ("tools/export", "tools/state", "runtime/db", "config"):
        shutil.copytree(os.path.join(REPO_ROOT, rel), os.path.join(sandbox, rel),
                        ignore=shutil.ignore_patterns("__pycache__", "tests", "*.db",
                                                      "cis_memory_db"))
    os.makedirs(os.path.join(sandbox, "docs"), exist_ok=True)
    os.makedirs(os.path.join(sandbox, "runtime", "manifests"), exist_ok=True)
    for args in (("init", "-q"), ("config", "user.email", "d18@test.local"),
                 ("config", "user.name", "D18 Test"), ("add", "-A"),
                 ("commit", "-qm", "sandbox: generator sources")):
        subprocess.run(["git", *args], cwd=sandbox, capture_output=True, text=True)
    return sandbox


def test_manifest_records_limit_and_margin():
    """`hermes closeout` runs generate_all.py, not the generator directly.
    The margin has to survive that hop — printed in its output and recorded
    in the manifest it writes."""
    tmp = make_sandbox()
    try:
        r = subprocess.run(
            ["python3", os.path.join(tmp, "tools", "export", "generate_all.py"),
             "--db", PROD_DB, "--precommit",
             "--stage-list", os.path.join(tmp, "stage-list")],
            capture_output=True, text=True, timeout=300, cwd=tmp,
        )
        output = r.stdout + r.stderr
        check("generate_all runs the full export pipeline",
              r.returncode == 0, f"rc={r.returncode}\n{output[-800:]}")
        check("generate_all surfaces the generator's size summary",
              re.search(r"chars, limit \d+, margin -?\d+ chars", output) is not None,
              output[-800:])

        manifest_path = os.path.join(tmp, "runtime", "manifests",
                                     "EXPORT_MANIFEST.json")
        with open(manifest_path, encoding="utf-8") as f:
            manifest = json.load(f)
        entry = next((a for a in manifest["artifacts"] if a["path"] == "AGENTS.md"), None)
        check("the manifest has an AGENTS.md artifact entry",
              entry is not None, str(manifest.get("artifacts"))[:300])
        if entry:
            check("the manifest records the limit the guard enforces",
                  entry.get("char_limit") == gen.CHAR_LIMIT, str(entry.get("char_limit")))
            check("the manifest records the remaining margin",
                  entry.get("char_margin") == gen.CHAR_LIMIT - entry["char_count"],
                  f"margin={entry.get('char_margin')} count={entry['char_count']}")
            check("the recorded margin is positive — the committed projection fits",
                  entry.get("char_margin", -1) > 0, str(entry.get("char_margin")))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ── 6. the projection this repository actually commits ─────────────────────

def test_real_spine_projection_reports_its_own_margin():
    tmp = tempfile.mkdtemp(prefix="d18-prod-")
    try:
        out = os.path.join(tmp, "AGENTS.md")
        rc, output = generate(PROD_DB, out)
        parsed = parse_pass_line(output)
        check("the real spine generates a projection within the limit",
              rc == 0, f"rc={rc}\n{output[-500:]}")
        check("the real projection reports its size, limit and margin",
              parsed is not None, output[-400:])
        if parsed:
            chars, limit, margin = parsed
            check("the real projection's reported margin is consistent and positive",
                  margin == limit - chars and margin > 0,
                  f"chars={chars} limit={limit} margin={margin}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def run():
    if not os.path.exists(PROD_DB):
        print(f"SKIP: spine DB not found at {PROD_DB} (set CIS_SPINE_PATH)")
        sys.exit(0)

    test_size_report_arithmetic()
    test_size_report_margin_is_negative_exactly_when_oversized()
    test_successful_generation_reports_size_limit_and_margin()
    test_comfortable_margin_does_not_warn()
    test_thin_margin_warns_but_still_succeeds()
    test_oversized_generation_fails_closed_with_actionable_diagnostics()
    test_oversized_generation_leaves_an_existing_projection_intact()
    test_diagnostics_do_not_alter_authoritative_content()
    test_generation_remains_deterministic()
    test_manifest_records_limit_and_margin()
    test_real_spine_projection_reports_its_own_margin()

    for r in results:
        print(r)
    failed = [r for r in results if ": FAIL" in r]
    print(f"\n{len(results) - len(failed)}/{len(results)} passed.")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    run()
