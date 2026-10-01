#!/usr/bin/env python3
"""test_precommit_export_safety.py — WB1-D13 behavioural tests for the
pre-commit export safety contract implemented by
`tools/export/generate_all.py --precommit` and `tools/hooks/pre-commit`.

The defect these cover
----------------------
The pre-commit hook ran the export pipeline on every commit, in place, and
then `git add`-ed any export path that looked dirty. Two things followed:

  * `tools/export/generate_hcp.py` carried a large uncommitted rewrite for
    weeks. Every unrelated commit executed that unreviewed source, and the
    projections it produced were committed while the source that produced
    them was not — the committed exports could not be regenerated from the
    committed code.

  * The hook could not distinguish "this run just regenerated it" from "the
    author has uncommitted work here". A hand-edited export file would be
    silently overwritten and the replacement folded into an unrelated commit.

Approach
--------
Each test builds a throwaway git repository containing real copies of the
real generators (tools/export/*.py, tools/state/canonical_state.py,
config/*.yaml) so that `REPO_ROOT` resolves inside the sandbox, and runs the
real pipeline against the real spine DB read-only (`CIS_SPINE_PATH`, same
convention as test_generate_hcp_current_state.py). Nothing in the actual
repository is written to.

Safety assertions are made on a full hash census of the sandbox tree taken
before and after each refusal, so "fails closed before destructive mutation"
is proven over every file, not just the one a test happens to look at.

Run:
    python3 tools/export/tests/test_precommit_export_safety.py
"""
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
PROD_DB = os.environ.get("CIS_SPINE_PATH", os.path.join(REPO_ROOT, "data", "cis_memory.db"))

EXIT_DIRTY_SOURCE = 3
EXIT_DIRTY_OUTPUT = 4

STAMP_RE = re.compile(r"^Generated: .* \| Run: .*$", re.MULTILINE)

results = []


def check(label, cond, detail=""):
    results.append(f"{label}: PASS" if cond else f"{label}: FAIL — {detail}")


# ── sandbox ────────────────────────────────────────────────────────────────

def git(sandbox, *args):
    return subprocess.run(["git", *args], cwd=sandbox, capture_output=True, text=True)


def make_sandbox():
    """A real git repo holding real generator sources, with no exports yet."""
    sandbox = tempfile.mkdtemp(prefix="d13-")
    for rel in ("tools/export", "tools/state", "config"):
        shutil.copytree(os.path.join(REPO_ROOT, rel), os.path.join(sandbox, rel),
                        ignore=shutil.ignore_patterns("__pycache__", "tests"))
    os.makedirs(os.path.join(sandbox, "docs"), exist_ok=True)
    os.makedirs(os.path.join(sandbox, "runtime", "manifests"), exist_ok=True)
    git(sandbox, "init", "-q")
    git(sandbox, "config", "user.email", "d13@test.local")
    git(sandbox, "config", "user.name", "D13 Test")
    git(sandbox, "add", "-A")
    git(sandbox, "commit", "-qm", "sandbox: generator sources")
    return sandbox


def run_pipeline(sandbox, extra=()):
    """Run the real generate_all.py inside the sandbox. Returns (rc, output, stage_list)."""
    stage_list = os.path.join(sandbox, ".stage-list")
    if os.path.exists(stage_list):
        os.remove(stage_list)
    r = subprocess.run(
        ["python3", os.path.join(sandbox, "tools", "export", "generate_all.py"),
         "--db", PROD_DB, "--precommit", "--stage-list", stage_list, *extra],
        cwd=sandbox, capture_output=True, text=True, timeout=300,
    )
    produced = None
    if os.path.exists(stage_list):
        with open(stage_list) as f:
            produced = [ln for ln in f.read().split("\n") if ln]
    return r.returncode, r.stdout + r.stderr, produced


def census(sandbox):
    """sha256 of every file in the sandbox, excluding .git and scratch state."""
    out = {}
    for root, dirs, files in os.walk(sandbox):
        dirs[:] = [d for d in dirs if d not in (".git", "__pycache__")]
        for fn in files:
            if fn == ".stage-list":
                continue
            p = os.path.join(root, fn)
            rel = os.path.relpath(p, sandbox)
            with open(p, "rb") as f:
                out[rel] = hashlib.sha256(f.read()).hexdigest()
    return out


def seed_exports(sandbox):
    """Generate a first full export set and commit it, leaving a clean tree."""
    rc, out, produced = run_pipeline(sandbox)
    assert rc == 0, f"seeding failed: {out}"
    git(sandbox, "add", "-A")
    git(sandbox, "commit", "-qm", "sandbox: baseline exports")
    return produced


def read(sandbox, rel):
    with open(os.path.join(sandbox, rel), encoding="utf-8") as f:
        return f.read()


def write(sandbox, rel, text):
    with open(os.path.join(sandbox, rel), "w", encoding="utf-8") as f:
        f.write(text)


SAMPLE_OUTPUT = "PROJECT_CONTEXT_PACK_UPLOAD/HCP_03_DECISIONS_LOG.md"


# ── 1. clean generator + clean output: generates normally ──────────────────

def test_clean_tree_generates_normally():
    sandbox = make_sandbox()
    try:
        rc, out, produced = run_pipeline(sandbox)
        check("clean generator + no pre-existing export dirt generates normally",
              rc == 0, f"rc={rc}\n{out}")
        check("a normal run reports the export set it produced",
              produced and SAMPLE_OUTPUT in produced and "AGENTS.md" in produced,
              f"produced={produced}")
        check("a normal run actually writes the exports it reports",
              os.path.exists(os.path.join(sandbox, SAMPLE_OUTPUT)),
              "sample export missing from disk")
        check("a normal run writes the export manifest",
              os.path.exists(os.path.join(sandbox, "runtime/manifests/EXPORT_MANIFEST.json")),
              "manifest missing")
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)


# ── 2. dirty generator cannot contaminate an unrelated commit ──────────────

def test_unstaged_generator_source_blocks_before_any_write():
    sandbox = make_sandbox()
    try:
        seed_exports(sandbox)
        # An unrelated commit is in progress; the generator happens to be dirty.
        write(sandbox, "unrelated.txt", "the commit the author actually wants\n")
        git(sandbox, "add", "unrelated.txt")
        with open(os.path.join(sandbox, "tools/export/generate_hcp.py"), "a") as f:
            f.write("\n# unreviewed working-tree change\n")

        before = census(sandbox)
        rc, out, produced = run_pipeline(sandbox)
        after = census(sandbox)

        check("unstaged generator source refuses the run",
              rc == EXIT_DIRTY_SOURCE, f"rc={rc}\n{out}")
        check("the refusal names the offending generator",
              "tools/export/generate_hcp.py" in out, out[-600:])
        check("a generator-source refusal writes no stage list",
              produced is None, f"produced={produced}")
        check("a generator-source refusal mutates no file anywhere in the tree",
              before == after,
              f"changed={sorted(set(before) ^ set(after)) or [k for k in before if before[k] != after.get(k)]}")

        st = git(sandbox, "status", "--short").stdout
        check("the author's unrelated staged file is still staged and untouched",
              "A  unrelated.txt" in st, st)
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)


def test_staged_generator_source_is_accepted():
    """The contract's escape is review, not a flag: staging the generator change
    is the author explicitly presenting it for this commit."""
    sandbox = make_sandbox()
    try:
        seed_exports(sandbox)
        with open(os.path.join(sandbox, "tools/export/generate_hcp.py"), "a") as f:
            f.write("\n# deliberate, staged generator change\n")
        git(sandbox, "add", "tools/export/generate_hcp.py")
        rc, out, produced = run_pipeline(sandbox)
        check("a staged (explicitly offered) generator change is allowed to run",
              rc == 0, f"rc={rc}\n{out[-800:]}")
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)


# ── 3. pre-existing dirty export file is not overwritten or auto-staged ────

def test_preexisting_authored_export_edit_is_preserved():
    sandbox = make_sandbox()
    try:
        seed_exports(sandbox)
        authored = read(sandbox, SAMPLE_OUTPUT) + "\nAUTHORED, UNCOMMITTED, NOT A GENERATOR PRODUCT\n"
        write(sandbox, SAMPLE_OUTPUT, authored)

        before = census(sandbox)
        rc, out, produced = run_pipeline(sandbox)
        after = census(sandbox)

        check("pre-existing authored work in a generated file refuses the run",
              rc == EXIT_DIRTY_OUTPUT, f"rc={rc}\n{out}")
        check("the refusal names the path it would have overwritten",
              SAMPLE_OUTPUT in out, out[-600:])
        check("the author's bytes survive byte-for-byte",
              read(sandbox, SAMPLE_OUTPUT) == authored, "content changed")
        check("a dirty-output refusal mutates no other export either",
              before == after,
              f"changed={[k for k in before if before[k] != after.get(k)]}")
        check("a dirty-output refusal stages nothing",
              produced is None, f"produced={produced}")

        st = git(sandbox, "status", "--short").stdout
        check("the dirty export file is left unstaged, not absorbed",
              f" M {SAMPLE_OUTPUT}" in st, st)
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)


def test_stamp_only_dirt_is_reconciled_not_refused():
    """The real-world condition WB1-D13 found: the old hook regenerated
    HCP_10/DEV-PIVOT_STATUS.md every run but never staged them, so they sat
    permanently dirty by their generation stamp alone. Stamp-only drift is
    the generator's own non-determinism, not authored work — reconciling it
    loses nothing, so it is produced and reported rather than refused."""
    sandbox = make_sandbox()
    try:
        seed_exports(sandbox)
        churned = STAMP_RE.sub("Generated: 1999-01-01 00:00 UTC | Run: run-oldoldoldol",
                               read(sandbox, SAMPLE_OUTPUT), count=1)
        write(sandbox, SAMPLE_OUTPUT, churned)

        rc, out, produced = run_pipeline(sandbox)
        check("stamp-only pre-existing dirt does not refuse the run",
              rc == 0, f"rc={rc}\n{out[-800:]}")
        check("stamp-only dirt is reconciled and reported as produced",
              produced and SAMPLE_OUTPUT in produced, f"produced={produced}")
        check("the reconciled file no longer carries the stale stamp",
              "run-oldoldoldol" not in read(sandbox, SAMPLE_OUTPUT), "stale stamp survived")
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)


# ── 4. generated files belonging to the current operation are deterministic ─

def test_generation_is_deterministic_apart_from_its_stamp():
    sandbox = make_sandbox()
    try:
        seed_exports(sandbox)
        first = {rel: read(sandbox, rel) for rel in
                 (SAMPLE_OUTPUT, "AGENTS.md", "PROJECT_CONTEXT_PACK_UPLOAD/HCP_05_NEXT_ACTIONS.md")}
        rc, out, produced = run_pipeline(sandbox)
        check("a repeat run over unchanged inputs succeeds", rc == 0, f"rc={rc}\n{out[-400:]}")
        for rel, old in first.items():
            check(f"{rel} regenerates identically apart from its generation stamp",
                  STAMP_RE.sub("", read(sandbox, rel)) == STAMP_RE.sub("", old),
                  "substantive content differed between two runs")
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)


# ── 5. unrelated work stays outside export scope ───────────────────────────

def test_unrelated_staged_and_dirty_files_stay_out_of_scope():
    sandbox = make_sandbox()
    try:
        seed_exports(sandbox)
        write(sandbox, "unrelated_tracked.txt", "v1\n")
        git(sandbox, "add", "unrelated_tracked.txt")
        git(sandbox, "commit", "-qm", "sandbox: unrelated tracked file")

        write(sandbox, "unrelated_tracked.txt", "v2 — uncommitted author work\n")
        write(sandbox, "staged_for_this_commit.txt", "deliberately staged\n")
        git(sandbox, "add", "staged_for_this_commit.txt")

        rc, out, produced = run_pipeline(sandbox)
        check("the pipeline runs with unrelated staged and dirty files present",
              rc == 0, f"rc={rc}\n{out[-800:]}")
        check("no unrelated path appears in the produced set",
              produced is not None and not any(
                  p.endswith(".txt") for p in produced), f"produced={produced}")
        check("unrelated dirty file is not rewritten by the export run",
              read(sandbox, "unrelated_tracked.txt") == "v2 — uncommitted author work\n",
              "unrelated dirty file changed")
        st = git(sandbox, "status", "--short").stdout
        check("unrelated staged file remains staged",
              "A  staged_for_this_commit.txt" in st, st)
        check("unrelated dirty file remains unstaged",
              " M unrelated_tracked.txt" in st, st)
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)


# ── 6. end-to-end through the tracked hook ─────────────────────────────────

def install_hook(sandbox):
    dest = os.path.join(sandbox, ".git", "hooks", "pre-commit")
    shutil.copyfile(os.path.join(REPO_ROOT, "tools", "hooks", "pre-commit"), dest)
    os.chmod(dest, 0o755)


def test_hook_stages_only_what_the_run_produced():
    sandbox = make_sandbox()
    try:
        seed_exports(sandbox)
        install_hook(sandbox)
        os.makedirs(os.path.join(sandbox, "data"), exist_ok=True)
        os.symlink(PROD_DB, os.path.join(sandbox, "data", "cis_memory.db"))

        write(sandbox, "feature.txt", "an unrelated change the author is committing\n")
        git(sandbox, "add", "feature.txt")
        # Unrelated uncommitted work that must survive the commit untouched.
        write(sandbox, "scratch.txt", "not mine to touch\n")

        r = git(sandbox, "commit", "-m", "unrelated: a normal commit")
        check("the tracked hook permits a normal unrelated commit",
              r.returncode == 0, r.stdout + r.stderr)

        show = git(sandbox, "show", "--name-only", "--format=", "HEAD").stdout.split()
        check("the commit contains the author's file",
              "feature.txt" in show, str(show))
        check("the commit absorbed no untracked unrelated work",
              "scratch.txt" not in show, str(show))
        check("unrelated uncommitted work survived the hook byte-for-byte",
              read(sandbox, "scratch.txt") == "not mine to touch\n", "scratch.txt changed")
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)


def test_hook_blocks_commit_when_generator_is_dirty():
    sandbox = make_sandbox()
    try:
        seed_exports(sandbox)
        install_hook(sandbox)
        os.makedirs(os.path.join(sandbox, "data"), exist_ok=True)
        os.symlink(PROD_DB, os.path.join(sandbox, "data", "cis_memory.db"))

        write(sandbox, "feature.txt", "unrelated change\n")
        git(sandbox, "add", "feature.txt")
        with open(os.path.join(sandbox, "tools/export/generate_hcp.py"), "a") as f:
            f.write("\n# unreviewed\n")

        head_before = git(sandbox, "rev-parse", "HEAD").stdout.strip()
        before = census(sandbox)
        r = git(sandbox, "commit", "-m", "unrelated: should be blocked")
        after = census(sandbox)

        check("the tracked hook blocks a commit driven by a dirty generator",
              r.returncode != 0, r.stdout + r.stderr)
        check("the blocked commit did not land",
              git(sandbox, "rev-parse", "HEAD").stdout.strip() == head_before, "HEAD moved")
        check("the blocked commit mutated nothing on disk",
              before == after,
              f"changed={[k for k in before if before[k] != after.get(k)]}")
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)


def run():
    if not os.path.exists(PROD_DB):
        print(f"SKIP: spine DB not found at {PROD_DB} (set CIS_SPINE_PATH)")
        sys.exit(0)

    test_clean_tree_generates_normally()
    test_unstaged_generator_source_blocks_before_any_write()
    test_staged_generator_source_is_accepted()
    test_preexisting_authored_export_edit_is_preserved()
    test_stamp_only_dirt_is_reconciled_not_refused()
    test_generation_is_deterministic_apart_from_its_stamp()
    test_unrelated_staged_and_dirty_files_stay_out_of_scope()
    test_hook_stages_only_what_the_run_produced()
    test_hook_blocks_commit_when_generator_is_dirty()

    for r in results:
        print(r)
    failed = [r for r in results if ": FAIL" in r]
    print(f"\n{len(results) - len(failed)}/{len(results)} passed.")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    run()
