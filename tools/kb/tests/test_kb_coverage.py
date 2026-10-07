#!/usr/bin/env python3
"""test_kb_coverage.py — the KB source-coverage gate, against temporary spines.

Every case here is one of the failures the gate exists to catch. None of them
touch the production spine: each builds its own knowledge_messages table and its
own source tree, so a pass means the LOGIC is right rather than that today's
corpus happens to be clean.

Plain-python, no pytest — the convention tools/export/tests uses, and pytest is
not installed on either interpreter here.

  python3 tools/kb/tests/test_kb_coverage.py
"""
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(os.path.dirname(HERE))
REPO = os.path.dirname(TOOLS)
sys.path.insert(0, TOOLS)

from kb import source_policy as sp          # noqa: E402
from kb import ingest_files                 # noqa: E402

GATE = os.path.join(TOOLS, "gates/gate_kb_source_coverage.py")

results = []


def check(label, cond, detail=""):
    results.append(f"{label}: PASS" if cond else f"{label}: FAIL — {detail}")


# ------------------------------------------------------------- fixtures ----

def make_spine(path, rows=()):
    """A minimal knowledge_messages, matching the production columns we read."""
    conn = sqlite3.connect(path)
    conn.execute("""CREATE TABLE knowledge_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT, role TEXT NOT NULL,
        content TEXT NOT NULL, source TEXT NOT NULL, source_key TEXT,
        timestamp TEXT, created_at TEXT DEFAULT (datetime('now')))""")
    conn.executemany(
        "INSERT INTO knowledge_messages (role, content, source, source_key, created_at) "
        "VALUES ('document', 'body', ?, ?, ?)", rows)
    conn.commit()
    conn.close()
    return path


def write_tree(root, files):
    for rel, body in files.items():
        full = os.path.join(root, rel)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w") as fh:
            fh.write(body)
    return root


def policy_for(tmp, root, **overrides):
    fam = {
        "kb_source": "testdocs",
        "root": root,
        "key_style": "path_colon_index",
        "include": ["**/*.md"],
        "required": True,
        "freshness": "current",
        "min_coverage": 1.0,
        "authority_class": "evidence",
    }
    fam.update(overrides)
    path = os.path.join(tmp, "policy.yaml")
    with open(path, "w") as fh:
        yaml.safe_dump({"version": 1, "families": {"docs": fam}}, fh)
    return path


def run_gate(policy, db, manifest=None, closeout=False):
    cmd = [sys.executable, GATE, "--json", "--policy", policy, "--db", db]
    if closeout:
        cmd.append("--closeout")
    # Always an explicit manifest, even when the case is about its absence: the
    # default is the production receipt file, and a test must never read it.
    cmd += ["--manifest", manifest or os.path.join(os.path.dirname(db), "absent.json")]
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO)
    payload = json.loads(proc.stdout) if proc.stdout.strip().startswith("{") else {}
    return proc.returncode, payload, proc.stderr


def only(payload):
    return payload["families"][0]


class sandbox:
    def __enter__(self):
        self.dir = tempfile.mkdtemp(prefix="kbcov-")
        return self.dir

    def __exit__(self, *exc):
        shutil.rmtree(self.dir, ignore_errors=True)


# ------------------------------------------------------------- the cases ----

def test_current_source_passes():
    """A declared source that is present and unchanged is a clean pass."""
    with sandbox() as tmp:
        root = write_tree(os.path.join(tmp, "src"), {"a.md": "alpha body text"})
        db = make_spine(os.path.join(tmp, "s.db"),
                        [("testdocs", "a.md:0", "2026-01-01")])
        mani = os.path.join(tmp, "m.json")
        with open(mani, "w") as fh:
            json.dump({"families": {"docs": {"files": {
                "a.md": {"sha256": sp.sha256_file(os.path.join(root, "a.md"))}}}}}, fh)

        code, payload, _ = run_gate(policy_for(tmp, root), db, mani)
        rec = only(payload)
        check("current source passes",
              code == 0 and rec["coverage"] == 1.0 and not rec["violations"],
              f"code={code} rec={rec}")


def test_missing_source_detected():
    """A document on disk that was never ingested fails the gate."""
    with sandbox() as tmp:
        root = write_tree(os.path.join(tmp, "src"), {"a.md": "alpha", "b.md": "bravo"})
        db = make_spine(os.path.join(tmp, "s.db"),
                        [("testdocs", "a.md:0", "2026-01-01")])
        code, payload, _ = run_gate(policy_for(tmp, root), db)
        rec = only(payload)
        check("missing source detected",
              code == 1 and rec["missing"] == 1 and rec["missing_files"] == ["b.md"]
              and any("never ingested" in v for v in rec["violations"]),
              str(rec))


def test_stale_source_detected_by_hash():
    """Ingested, then edited: the sha256 no longer matches the receipt."""
    with sandbox() as tmp:
        root = write_tree(os.path.join(tmp, "src"), {"a.md": "original"})
        mani = os.path.join(tmp, "m.json")
        with open(mani, "w") as fh:
            json.dump({"families": {"docs": {"files": {
                "a.md": {"sha256": sp.sha256_file(os.path.join(root, "a.md"))}}}}}, fh)
        with open(os.path.join(root, "a.md"), "w") as fh:
            fh.write("edited after ingestion")
        db = make_spine(os.path.join(tmp, "s.db"),
                        [("testdocs", "a.md:0", "2026-01-01")])

        code, payload, _ = run_gate(policy_for(tmp, root), db, mani)
        rec = only(payload)
        check("stale source detected",
              code == 1 and rec["coverage"] == 1.0
              and rec["changed_since_ingest"] == ["a.md"]
              and any("changed without re-ingestion" in v for v in rec["violations"]),
              str(rec))


def test_provenance_missing_is_a_violation():
    """Present with no receipt: we cannot say the copy matches, so we do not."""
    with sandbox() as tmp:
        root = write_tree(os.path.join(tmp, "src"), {"a.md": "alpha"})
        db = make_spine(os.path.join(tmp, "s.db"),
                        [("testdocs", "a.md:0", "2026-01-01")])
        code, payload, _ = run_gate(
            policy_for(tmp, root, require_provenance=True), db)
        rec = only(payload)
        check("provenance missing detected",
              code == 1 and rec["provenance_missing"] == ["a.md"]
              and any("no provenance record" in v for v in rec["violations"]),
              str(rec))


def test_optional_family_creates_no_false_failure():
    """An excluded family with nothing ingested must not fail the gate."""
    with sandbox() as tmp:
        root = write_tree(os.path.join(tmp, "src"), {"a.md": "alpha"})
        db = make_spine(os.path.join(tmp, "s.db"))
        code, payload, _ = run_gate(policy_for(tmp, root, required=False), db)
        rec = only(payload)
        check("optional family no false failure",
              code == 0 and rec["status"] == "NOT REQUIRED" and not rec["violations"],
              str(rec))


def test_grace_window_excuses_only_a_brand_new_source():
    """A transcript being written right now is not yet a failure; a three-day-old
    one is. Grace is a write window, not an amnesty."""
    with sandbox() as tmp:
        root = write_tree(os.path.join(tmp, "src"), {"new.md": "just created"})
        db = make_spine(os.path.join(tmp, "s.db"))
        pol = policy_for(tmp, root, grace_hours=24, require_provenance=False)
        code_new, payload_new, _ = run_gate(pol, db)

        old = time.time() - 3 * 86400
        os.utime(os.path.join(root, "new.md"), (old, old))
        code_old, payload_old, _ = run_gate(pol, db)

        check("grace excuses new source",
              code_new == 0 and only(payload_new)["in_grace"] == 1
              and only(payload_new)["missing"] == 0, str(only(payload_new)))
        check("grace does not excuse old source",
              code_old == 1 and only(payload_old)["missing"] == 1,
              str(only(payload_old)))


def test_min_bytes_excludes_trivial_files():
    """A 0-byte capture is not missing knowledge; it is an empty file. Without
    this, two empty stderr files hold the gate red and everyone learns to ignore it."""
    with sandbox() as tmp:
        root = write_tree(os.path.join(tmp, "src"), {"a.md": "", "b.md": "x" * 200})
        db = make_spine(os.path.join(tmp, "s.db"),
                        [("testdocs", "b.md:0", "2026-01-01")])
        code, payload, _ = run_gate(
            policy_for(tmp, root, min_bytes=64, require_provenance=False), db)
        check("min_bytes excludes trivial files",
              code == 0 and only(payload)["total_eligible"] == 1,
              str(only(payload)))


def test_gate_fails_closed_when_spine_unreadable():
    """Coverage that cannot be established is not coverage."""
    with sandbox() as tmp:
        root = write_tree(os.path.join(tmp, "src"), {"a.md": "alpha"})
        code, _, err = run_gate(policy_for(tmp, root),
                                os.path.join(tmp, "does-not-exist.db"))
        check("fails closed on unreadable spine",
              code == 2 and "spine unreadable" in err, f"code={code} err={err[:200]}")


def test_gate_fails_closed_when_policy_unreadable():
    with sandbox() as tmp:
        db = make_spine(os.path.join(tmp, "s.db"))
        code, _, err = run_gate(os.path.join(tmp, "no-policy.yaml"), db)
        check("fails closed on unreadable policy",
              code == 2 and "policy unreadable" in err, f"code={code} err={err[:200]}")


def test_unmeasurable_required_family_reports_missing_path():
    """No denominator is reported as unmeasurable, never as 0% and never as a pass."""
    with sandbox() as tmp:
        path = os.path.join(tmp, "p.yaml")
        with open(path, "w") as fh:
            yaml.safe_dump({"version": 1, "families": {"chat": {
                "required": True, "measurable": False,
                "ingestion_path": "MISSING", "authority_class": "evidence",
                "note": "manual export only"}}}, fh)
        db = make_spine(os.path.join(tmp, "s.db"))
        code, payload, _ = run_gate(path, db)
        rec = only(payload)
        check("unmeasurable family reports missing path",
              code == 1 and rec["coverage"] is None
              and "NOT CURRENTLY MEASURABLE" in rec["status"]
              and any("INGESTION PATH MISSING" in v for v in rec["violations"]),
              str(rec))


def test_required_family_with_no_eligible_sources_fails():
    """0/0 must never read as complete — an expected family that discovers
    nothing is a configuration failure."""
    with sandbox() as tmp:
        root = os.path.join(tmp, "empty")
        os.makedirs(root)
        db = make_spine(os.path.join(tmp, "s.db"))
        code, payload, _ = run_gate(policy_for(tmp, root), db)
        check("empty required family fails",
              code == 1 and any("no eligible sources" in v
                                for v in only(payload)["violations"]),
              str(only(payload)))


# ------------------------------------------------- identity / dedup rules ----

def test_doc_identity_survives_both_key_conventions():
    """'x.md:12' is the original loader's key; 'x.md:12#r0' is the same row after
    tools/rechunk_for_embedding.py split it. Both name one source file."""
    cases = [("DEV-PIVOT-17.md:0", "DEV-PIVOT-17.md"),
             ("DEV-PIVOT-17.md:12#r0", "DEV-PIVOT-17.md"),
             ("sub/dir/a.md:3", "sub/dir/a.md")]
    bad = [(k, sp.identity_of(k, "path_colon_index")) for k, e in cases
           if sp.identity_of(k, "path_colon_index") != e]
    check("doc identity survives both key conventions", not bad, str(bad))


def test_kernel_identity_survives_a_hash_in_the_filename():
    """cis_kernel really holds '# CIS HANDOFF ….md'. Splitting on the first '#'
    reduced its key to the directory and reported six ingested files as absent."""
    fam = {"root": "cis_kernel"}
    key = "cis_kernel/source/vision/# CIS HANDOFF — Phase D.md#r2"
    got = sp.identity_of(key, "path_hash_index", fam)
    check("kernel identity survives '#' in filename",
          got == "source/vision/# CIS HANDOFF — Phase D.md", got)


def test_session_identity_ignores_the_directory_it_sat_in():
    """A delegated run's transcript lives under subagents/, not the project dir."""
    a = sp.identity_of("claude_code/-home-eric/abc-123/4.0", "session_triplet")
    b = sp.identity_of("claude_code/subagents/agent-ff01/0.0", "session_triplet")
    c = sp.path_identity({"key_style": "session_triplet"},
                         "-home-eric/d1/subagents/agent-ff01.jsonl")
    check("session identity ignores directory",
          a == "abc-123" and b == "agent-ff01" and c == "agent-ff01",
          f"{a} {b} {c}")


def test_duplicate_ingestion_is_a_no_op():
    """Running the ingester twice must not duplicate a document. That defect in
    tools/catalog/convert_to_knowledge.py is why docs/ had no safe top-up path."""
    with sandbox() as tmp:
        root = write_tree(os.path.join(tmp, "src"), {"a.md": "alpha " * 100})
        db = os.path.join(tmp, "s.db")
        make_spine(db)
        fam = yaml.safe_load(open(policy_for(tmp, root)))["families"]["docs"]
        manifest, mpath = {"families": {}}, os.path.join(tmp, "m.json")
        conn = sqlite3.connect(db)
        first = ingest_files.ingest("docs", fam, conn, manifest, embed=False,
                                    manifest_path=mpath)
        second = ingest_files.ingest("docs", fam, conn, manifest, embed=False,
                                     manifest_path=mpath)
        total = conn.execute("SELECT COUNT(*) FROM knowledge_messages").fetchone()[0]
        conn.close()
        check("duplicate ingestion is a no-op",
              first > 0 and second == 0 and total == first,
              f"first={first} second={second} total={total}")


def test_changed_file_supersedes_rather_than_stacks():
    """Two versions of one document in one corpus is the stale-outranks-current
    failure wearing a document costume. The old chunks must go."""
    with sandbox() as tmp:
        root = write_tree(os.path.join(tmp, "src"),
                          {"a.md": "the original claim. " * 40})
        db = os.path.join(tmp, "s.db")
        make_spine(db)
        fam = yaml.safe_load(open(policy_for(tmp, root)))["families"]["docs"]
        manifest, mpath = {"families": {}}, os.path.join(tmp, "m.json")
        conn = sqlite3.connect(db)
        ingest_files.ingest("docs", fam, conn, manifest, embed=False,
                            manifest_path=mpath)
        with open(os.path.join(root, "a.md"), "w") as fh:
            fh.write("the corrected claim. " * 40)
        ingest_files.ingest("docs", fam, conn, manifest, embed=False,
                            manifest_path=mpath)
        bodies = [r[0] for r in conn.execute("SELECT content FROM knowledge_messages")]
        conn.close()
        check("changed file supersedes rather than stacks",
              any("corrected" in b for b in bodies)
              and not any("original" in b for b in bodies),
              f"{len(bodies)} chunk(s)")


def test_historical_evidence_cannot_masquerade_as_authority():
    """Ingestion must not confer authority. Every family carries an explicit
    authority_class, and no filesystem family may declare itself 'authority'."""
    policy = sp.load_policy()
    classes = {n: (f or {}).get("authority_class")
               for n, f in policy["families"].items()}
    unclassified = [n for n, c in classes.items() if not c]
    # A family discovered from the filesystem is evidence, projection or mixed —
    # never authority. Authority lives in the spine tables, which this policy
    # explicitly declines to measure.
    wrong = [n for n, f in policy["families"].items()
             if (f or {}).get("root") and (f or {}).get("authority_class") == "authority"]
    check("every family declares an authority class", not unclassified,
          str(unclassified))
    check("no filesystem family claims authority", not wrong, str(wrong))


def test_production_policy_is_internally_consistent():
    """The shipped policy must load, and every required family must declare
    either a measurable root or a stated reason it is not measurable."""
    try:
        policy = sp.load_policy()
    except Exception as exc:
        check("production policy loads", False, str(exc))
        return
    problems = []
    for name, fam in policy["families"].items():
        fam = fam or {}
        if not fam.get("required"):
            continue
        if fam.get("measurable", True):
            if not (fam.get("root") and fam.get("kb_source")):
                problems.append(f"{name}: required+measurable, no root/kb_source")
        elif not fam.get("note"):
            problems.append(f"{name}: unmeasurable with no explanation")
    check("production policy internally consistent", not problems, str(problems))


def test_production_gate_runs_against_the_real_spine():
    """The gate must execute end to end on the live corpus. It may legitimately
    report violations; what is not acceptable is crashing or failing closed on a
    readable spine."""
    proc = subprocess.run([sys.executable, GATE, "--json"],
                          capture_output=True, text=True, cwd=REPO)
    ok = proc.returncode in (0, 1) and proc.stdout.strip().startswith("{")
    detail = f"code={proc.returncode} err={proc.stderr[:200]}"
    check("gate runs against the real spine", ok, detail)
    if ok:
        payload = json.loads(proc.stdout)
        named = {f["family"] for f in payload["families"]}
        check("real run reports every declared family",
              named == set(sp.load_policy()["families"]),
              str(named ^ set(sp.load_policy()["families"])))


# ------------------------------------------- closeout mode (2026-10-07) ----
# The requirement these four cases encode: a stage closeout must fail on a
# knowledge hole it could have filled, and must NOT become permanently red on a
# family with no supported ingestion path. A gate that can never go green is a
# gate people learn to ignore, which is worse than no gate.

def _unmeasurable_policy(tmp, extra_measurable_family=None):
    """A required family with no ingestion path, optionally beside a measurable
    one — the exact shape of the production chatgpt/claude_ai conflict."""
    fams = {"chat": {"required": True, "measurable": False,
                     "ingestion_path": "MISSING", "authority_class": "evidence",
                     "note": "manual export only"}}
    if extra_measurable_family:
        fams["docs"] = extra_measurable_family
    path = os.path.join(tmp, "p.yaml")
    with open(path, "w") as fh:
        yaml.safe_dump({"version": 1, "families": fams}, fh)
    return path


def test_closeout_mode_does_not_fail_on_an_impossible_family():
    """chatgpt/claude_ai shape: required, no ingestion path. Default mode fails;
    --closeout reports POLICY UNDECIDED and exits 0."""
    with sandbox() as tmp:
        db = make_spine(os.path.join(tmp, "s.db"))
        policy = _unmeasurable_policy(tmp)

        full_code, full_payload, _ = run_gate(policy, db)
        co_code, co_payload, _ = run_gate(policy, db, closeout=True)

        check("default mode still fails on an impossible family",
              full_code == 1 and full_payload["mode"] == "full",
              f"code={full_code} payload={full_payload.get('mode')}")
        check("closeout mode does not fail on an impossible family",
              co_code == 0 and co_payload["policy_undecided"] == ["chat"],
              f"code={co_code} undecided={co_payload.get('policy_undecided')}")
        # The violation is REPORTED in both modes — narrowing the exit code must
        # not silence the finding, or the undecided policy becomes invisible.
        check("closeout mode still reports the undecided family's violation",
              any("INGESTION PATH MISSING" in v
                  for v in only(co_payload)["violations"]),
              str(only(co_payload)))


def test_closeout_mode_still_fails_on_a_real_hole():
    """A measurable required family with an un-ingested document blocks closeout
    even when an impossible family sits beside it."""
    with sandbox() as tmp:
        root = write_tree(os.path.join(tmp, "src"),
                          {"a.md": "alpha body text long enough to count"})
        os.utime(os.path.join(root, "a.md"), (time.time() - 86400 * 30,) * 2)
        db = make_spine(os.path.join(tmp, "s.db"))     # nothing ingested
        policy = _unmeasurable_policy(tmp, extra_measurable_family={
            "kb_source": "testdocs", "root": root,
            "key_style": "path_colon_index", "include": ["**/*.md"],
            "required": True, "freshness": "current", "min_coverage": 1.0,
            "authority_class": "evidence"})

        code, payload, _ = run_gate(policy, db, closeout=True)
        docs = [f for f in payload["families"] if f["family"] == "docs"][0]
        check("closeout mode still fails on a real measurable hole",
              code == 1 and docs["violations"]
              and payload["policy_undecided"] == ["chat"],
              f"code={code} docs={docs} undecided={payload.get('policy_undecided')}")


def test_closeout_verdict_classifies_every_production_family():
    """The function closeout-check consumes must sort every declared family into
    exactly one bucket — a family that falls through is a family nobody checks."""
    verdict = sp.closeout_verdict()
    buckets = (verdict["blocking"] + verdict["policy_undecided"]
               + verdict["unmeasurable"] + verdict["ok"])
    named = [b["family"] for b in buckets]
    declared = set(sp.load_policy()["families"])
    check("closeout verdict classifies every production family",
          set(named) == declared and len(named) == len(declared),
          f"missing={declared - set(named)} dupes={len(named)}!={len(declared)}")
    # The two browser families are the only required-but-unmeasurable ones in
    # production today. If that changes, this test should be the thing that says so.
    check("production's undecided families are exactly the browser histories",
          {b["family"] for b in verdict["policy_undecided"]}
          == {"chatgpt_sessions", "claude_ai_sessions"},
          str([b["family"] for b in verdict["policy_undecided"]]))


def test_closeout_verdict_fails_closed_when_unmeasurable():
    """Coverage that cannot be established is not coverage: an unreadable spine
    is a blocker, not a pass."""
    verdict = sp.closeout_verdict(db_path=os.path.join(tempfile.gettempdir(),
                                                       "kbcov-no-such-spine.db"))
    check("closeout verdict fails closed on an unreadable spine",
          verdict["blocking"] and not verdict["ready"],
          str(verdict["blocking"]))


def test_closeout_check_consumes_the_verdict():
    """tools/development/cli.py closeout-check reports the KB check it ran, so a
    closeout cannot pass while silently skipping coverage."""
    sys.path.insert(0, REPO)
    from tools.development import discovery
    blockers = discovery._kb_coverage_blockers()
    check("closeout-check reads coverage from the shared verdict",
          isinstance(blockers, list)
          and all(b["type"] == "kb_source_coverage" for b in blockers),
          str(blockers))
    # Production is clean on every measurable required family right now, so the
    # honest expectation is zero blockers. A non-empty list here means a real hole.
    check("production measurable families contribute no closeout blocker",
          blockers == [], str(blockers))


def test_closeout_check_skips_coverage_on_a_scratch_spine():
    """Exercising closeout mechanics against a temp database must not measure
    the production KB — and the skip must be VISIBLE, not look like a pass."""
    sys.path.insert(0, REPO)
    from tools.development import discovery
    with sandbox() as tmp:
        scratch = sqlite3.connect(os.path.join(tmp, "scratch.db"))
        try:
            check("scratch spine contributes no KB blocker",
                  discovery._kb_coverage_blockers(scratch) == [], "")
            check("scratch spine reports the coverage check as not run",
                  discovery._kb_coverage_measured(scratch) is False, "")
        finally:
            scratch.close()
    prod = sqlite3.connect(f"file:{sp.DB_PATH}?mode=ro", uri=True)
    try:
        check("production spine reports the coverage check as run",
              discovery._kb_coverage_measured(prod) is True, "")
    finally:
        prod.close()


def run():
    test_current_source_passes()
    test_missing_source_detected()
    test_stale_source_detected_by_hash()
    test_provenance_missing_is_a_violation()
    test_optional_family_creates_no_false_failure()
    test_grace_window_excuses_only_a_brand_new_source()
    test_min_bytes_excludes_trivial_files()
    test_gate_fails_closed_when_spine_unreadable()
    test_gate_fails_closed_when_policy_unreadable()
    test_unmeasurable_required_family_reports_missing_path()
    test_required_family_with_no_eligible_sources_fails()
    test_doc_identity_survives_both_key_conventions()
    test_kernel_identity_survives_a_hash_in_the_filename()
    test_session_identity_ignores_the_directory_it_sat_in()
    test_duplicate_ingestion_is_a_no_op()
    test_changed_file_supersedes_rather_than_stacks()
    test_historical_evidence_cannot_masquerade_as_authority()
    test_production_policy_is_internally_consistent()
    test_production_gate_runs_against_the_real_spine()
    test_closeout_mode_does_not_fail_on_an_impossible_family()
    test_closeout_mode_still_fails_on_a_real_hole()
    test_closeout_verdict_classifies_every_production_family()
    test_closeout_verdict_fails_closed_when_unmeasurable()
    test_closeout_check_consumes_the_verdict()
    test_closeout_check_skips_coverage_on_a_scratch_spine()

    for r in results:
        print(r)
    failed = [r for r in results if ": FAIL" in r]
    print(f"\n{len(results) - len(failed)}/{len(results)} passed.")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    run()
