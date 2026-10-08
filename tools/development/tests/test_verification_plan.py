#!/usr/bin/env python3
"""test_verification_plan.py — XDEV-VERIFY-01 acceptance tests.

Covers the card's eight named scenarios plus the module's own safety
properties. Uses the project's existing test style (temporary SQLite
fixtures, a real throwaway git repository, explicit PASS/FAIL lines, no
pytest dependency) rather than introducing a second test framework.

Every scenario that needs a repository builds a REAL one in a temp dir and
commits into it, because the whole mechanism rests on git-derived changed
scope and a mocked git would prove nothing about it. Two clearly marked
read-only observations run against the live repository and report their
outcome honestly, including FAIL.

Run: python3 tools/development/tests/test_verification_plan.py
"""
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from tools.development import continuity_store as cs  # noqa: E402
from tools.development import packet as packet_mod  # noqa: E402
from tools.development import verification_plan as vplan  # noqa: E402

results = []


def check(label, cond, detail=""):
    results.append(f"{label}: {'PASS' if cond else 'FAIL — ' + str(detail)}")
    print(results[-1])


# ── fixtures ─────────────────────────────────────────────────────────────

def _git(root, *args):
    r = subprocess.run(["git", "-C", root, *args], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"git {args}: {r.stderr}")
    return r.stdout.strip()


def make_repo():
    """A throwaway repository whose layout mirrors the real one closely
    enough to exercise the derived test mapping: component dirs that own
    `tests/`, a repo-root `tests/`, docs, config and a migrations dir."""
    root = tempfile.mkdtemp(prefix="xdev_verify_repo_")
    _git(root, "init", "-q", "-b", "master")
    _git(root, "config", "user.email", "t@example.invalid")
    _git(root, "config", "user.name", "test")

    layout = {
        "tools/alpha/core.py": "ALPHA = 1\n",
        "tools/alpha/tests/test_alpha.py": "def test(): assert True\n",
        "tools/beta/core.py": "BETA = 1\n",
        "tools/beta/tests/test_beta.py": "def test(): assert True\n",
        "tests/test_repo_wide.py": "def test(): assert True\n",
        "docs/NOTES.md": "notes\n",
        "config/settings.yaml": "a: 1\n",
        "runtime/schema/migrations/0001_init.sql": "SELECT 1;\n",
        "loose_helper.py": "X = 1\n",  # no owning component, on purpose
    }
    for rel, body in layout.items():
        path = os.path.join(root, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(body)
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "base")
    return root, _git(root, "rev-parse", "HEAD")


def commit(root, changes, message):
    for rel, body in changes.items():
        path = os.path.join(root, rel)
        os.makedirs(os.path.dirname(path) or root, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(body)
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", message)
    return _git(root, "rev-parse", "HEAD")


def make_spine(baseline_sha, *, evidence=None, independently_verified=True,
                verification_source=None, superseded=False, pushed_sha=None):
    """A temp spine carrying project_state + the dev continuity schema, with
    one external_dev_checkpoint row shaped like the production one."""
    path = os.path.join(tempfile.mkdtemp(prefix="xdev_verify_db_"), "spine.db")
    conn = cs.connect(path)
    conn.executescript(
        "CREATE TABLE project_state (id INTEGER PRIMARY KEY, key TEXT NOT NULL, "
        "value TEXT NOT NULL, source TEXT NOT NULL, created_at TEXT NOT NULL, "
        "superseded_at TEXT, superseded_by INTEGER);"
    )
    cs.init_schema(conn, db_path=path)
    packet = {
        "lifecycle_state": "REMOTE_VERIFIED" if independently_verified else "PUSHED",
        "latest_local_sha": baseline_sha,
        "latest_pushed_sha": pushed_sha or baseline_sha,
        "latest_remote_verified_sha": baseline_sha,
        "independently_verified": independently_verified,
        "verification_source": (
            verification_source if verification_source is not None else
            "Independent ChatGPT reviewer reading the GitHub remote at this SHA."
        ),
        "pushed_by": "Claude Code, CIS implementation agent (NOT an independent reviewer)",
        "evidence_at_this_sha": evidence if evidence is not None else
            "test_alpha.py 10/10; test_beta.py 8/8; gate_export_agreement.sh PASS",
        "remote_ref": "origin/master",
        "authority": "ADR-XDEV-001",
    }
    conn.execute(
        "INSERT INTO project_state (key, value, source, created_at, superseded_at) "
        "VALUES (?,?,?,?,?)",
        ("external_dev_checkpoint", json.dumps(packet), "test",
         "2026-10-06T00:00:00+00:00", "2026-10-06T01:00:00+00:00" if superseded else None),
    )
    return path, conn


def plan_for(root, conn, task=None):
    return vplan.build_plan(conn, task=task, repo_root=root, include_worktree=True)


def names(items):
    return sorted(i.get("name") for i in items)


def required_scopes(plan):
    return sorted(r["scope"] for r in plan["required_new_evidence"])


# ── derived test mapping (card section 7) ────────────────────────────────

def test_test_map_is_derived_not_registered():
    root, _ = make_repo()
    try:
        tm = vplan.derive_test_map(root)
        check("test map derived from the repository's own layout",
              tm["ok"] and set(tm["components"]) == {"tools/alpha", "tools/beta"},
              tm)
        check("a repo-root tests/ dir is a repository-wide suite, NOT a component "
              "that silently covers every file",
              tm["repo_wide_suites"] == ["tests"] and "" not in tm["components"],
              tm)
        check("component_for resolves a changed file to its nearest owning component",
              vplan.component_for("tools/alpha/core.py", tm) == "tools/alpha",
              vplan.component_for("tools/alpha/core.py", tm))
        check("component_for returns None rather than guessing a parent",
              vplan.component_for("loose_helper.py", tm) is None,
              vplan.component_for("loose_helper.py", tm))
    finally:
        shutil.rmtree(root, ignore_errors=True)


# ── Scenario A — unrelated (documentation) change ────────────────────────

def test_scenario_a_documentation_change_triggers_no_unrelated_tests():
    root, base = make_repo()
    db, conn = make_spine(base)
    try:
        commit(root, {"docs/NOTES.md": "notes, revised\n"}, "docs only")
        plan = plan_for(root, conn, task="T")
        scope = plan["changed_scope"]
        check("A: documentation-only change is recognized as such",
              scope["determinable"] and scope["documentation_only"], scope)
        check("A: no component test suite is required for a documentation change",
              required_scopes(plan) == [], required_scopes(plan))
        check("A: impact is still fully determined (a doc file with no owning "
              "component is not an unknown dependency)",
              scope["impact_fully_determined"], scope["reason"])
        check("A: mandatory gates still run regardless",
              {g["id"] for g in plan["mandatory_gates"]} == vplan.MANDATORY_CHECK_IDS,
              plan["mandatory_gates"])
        check("A: unrelated component evidence survives the documentation change",
              names(plan["reusable_evidence"]) == ["test_alpha.py", "test_beta.py"],
              names(plan["reusable_evidence"]))
    finally:
        conn.close()
        shutil.rmtree(root, ignore_errors=True)
        shutil.rmtree(os.path.dirname(db), ignore_errors=True)


# ── Scenario B — changed dependency ──────────────────────────────────────

def test_scenario_b_changed_component_invalidates_only_its_own_evidence():
    root, base = make_repo()
    db, conn = make_spine(base)
    try:
        commit(root, {"tools/alpha/core.py": "ALPHA = 2\n"}, "change alpha")
        plan = plan_for(root, conn, task="T")
        check("B: the changed component's suite is required",
              "tools/alpha" in required_scopes(plan), required_scopes(plan))
        check("B: the changed component's prior evidence is invalidated",
              "test_alpha.py" in names(plan["invalidated_evidence"]),
              names(plan["invalidated_evidence"]))
        check("B: the invalidation names condition 4, not merely 'the SHA moved'",
              any("condition 4" in i["invalidation_reason"]
                  for i in plan["invalidated_evidence"] if i["name"] == "test_alpha.py"),
              [i["invalidation_reason"] for i in plan["invalidated_evidence"]])
        check("B: the UNAFFECTED component's evidence is still reused — a changed "
              "SHA does not invalidate everything",
              names(plan["reusable_evidence"]) == ["test_beta.py"],
              names(plan["reusable_evidence"]))
        check("B: the unaffected component's suite is NOT required",
              "tools/beta" not in required_scopes(plan), required_scopes(plan))
    finally:
        conn.close()
        shutil.rmtree(root, ignore_errors=True)
        shutil.rmtree(os.path.dirname(db), ignore_errors=True)


# ── Scenario C — unknown dependency ──────────────────────────────────────

def test_scenario_c_unknown_impact_never_assumes_validity():
    root, base = make_repo()
    db, conn = make_spine(base)
    try:
        commit(root, {"loose_helper.py": "X = 2\n"}, "change a file with no owner")
        plan = plan_for(root, conn, task="T")
        scope = plan["changed_scope"]
        check("C: a changed file with no derivable owner is reported as "
              "undetermined impact",
              scope["undetermined_files"] == ["loose_helper.py"], scope)
        check("C: impact_fully_determined is False",
              not scope["impact_fully_determined"], scope)
        check("C: NOTHING is reused when impact cannot be established",
              plan["reusable_evidence"] == [],
              names(plan["reusable_evidence"]))
        check("C: broader (repository-wide) verification is required instead",
              "repository" in required_scopes(plan), required_scopes(plan))
        check("C: the limitation is stated outright, not inferred from silence",
              any("no derivable owning component" in l for l in plan["limitations"]),
              plan["limitations"])
    finally:
        conn.close()
        shutil.rmtree(root, ignore_errors=True)
        shutil.rmtree(os.path.dirname(db), ignore_errors=True)


def test_scenario_c_unresolvable_baseline_blocks_all_reuse():
    """The other unknown: the accepted baseline is not in this checkout, so
    no diff can be taken at all."""
    root, base = make_repo()
    db, conn = make_spine("deadbeefdeadbeefdeadbeefdeadbeefdeadbeef")
    try:
        plan = plan_for(root, conn, task="T")
        check("C: an unresolvable accepted baseline makes scope undeterminable",
              not plan["changed_scope"]["determinable"], plan["changed_scope"])
        check("C: unresolvable baseline reuses nothing and requires the "
              "repository-wide suites",
              plan["reusable_evidence"] == [] and
              required_scopes(plan) == ["repository"],
              (names(plan["reusable_evidence"]), required_scopes(plan)))
    finally:
        conn.close()
        shutil.rmtree(root, ignore_errors=True)
        shutil.rmtree(os.path.dirname(db), ignore_errors=True)


def test_no_baseline_at_all_requires_full_verification():
    root, _ = make_repo()
    path = os.path.join(tempfile.mkdtemp(prefix="xdev_verify_db_"), "empty.db")
    conn = cs.connect(path)
    cs.init_schema(conn, db_path=path)
    try:
        plan = vplan.build_plan(conn, task="T", repo_root=root)
        check("no accepted baseline recorded -> no reuse, full verification, "
              "independent review required",
              plan["reusable_evidence"] == [] and
              required_scopes(plan) == ["repository"] and
              plan["independent_review"]["required"] and
              plan["independent_review"]["state"] == "NO_ACCEPTED_BASELINE_RECORDED",
              plan["independent_review"])
    finally:
        conn.close()
        shutil.rmtree(root, ignore_errors=True)
        shutil.rmtree(os.path.dirname(path), ignore_errors=True)


# ── Scenario D — security-sensitive change ───────────────────────────────

def test_scenario_d_security_sensitive_change_retains_required_depth():
    root, base = make_repo()
    db, conn = make_spine(base)
    try:
        commit(root, {"runtime/schema/migrations/0002_add.sql": "SELECT 2;\n"},
               "add a migration")
        plan = plan_for(root, conn, task="T")
        scope = plan["changed_scope"]
        check("D: a migration is classified security-sensitive",
              "schema_migration" in scope["security_labels"], scope["security_labels"])
        check("D: required depth for that label is demanded explicitly",
              "schema_migration" in required_scopes(plan), required_scopes(plan))
        check("D: no evidence is reused while a security-sensitive change is present",
              plan["reusable_evidence"] == [], names(plan["reusable_evidence"]))
        check("D: the refusal cites condition 5 (mandatory policy), not condition 4",
              all(any("condition 5" in i["invalidation_reason"]
                      for i in [itm]) for itm in plan["invalidated_evidence"]),
              [i["invalidation_reason"] for i in plan["invalidated_evidence"]])
    finally:
        conn.close()
        shutil.rmtree(root, ignore_errors=True)
        shutil.rmtree(os.path.dirname(db), ignore_errors=True)


def test_scenario_d_every_security_class_the_card_names_is_covered():
    cases = {
        "runtime/schema/migrations/0005_x.sql": "schema_migration",
        "runtime/auth/oidc_login.py": "authentication",
        "tools/secrets_loader.py": "credential_handling",
        "tools/gates/gate_x.sh": "enforcement_gate",
        "tools/queue/purge_items.py": "destructive_write_path",
        "tools/development/continuity_store.py": "authority_boundary",
    }
    missing = {p: vplan.security_labels_for(p) for p, want in cases.items()
               if want not in vplan.security_labels_for(p)}
    check("D: security-sensitive, destructive, migration, authentication and "
          "authority-boundary changes are all classified",
          not missing, missing)


def test_mandatory_gates_are_never_reusable():
    root, base = make_repo()
    db, conn = make_spine(base, evidence="gate_export_agreement.sh PASS; test_alpha.py 10/10")
    try:
        plan = plan_for(root, conn, task="T")
        gate_items = [i for i in plan["reusable_evidence"] if i["kind"] == "gate"]
        check("mandatory gates are never promoted into reusable evidence",
              gate_items == [], gate_items)
        check("every mandatory gate is reported with reuse_permitted False",
              all(not g["reuse_permitted"] for g in plan["mandatory_gates"]),
              plan["mandatory_gates"])
        check("the KB source-coverage gate stays mandatory, so the separate "
              "pending evidence-classification correction cannot be weakened here",
              any(g["id"] == "kb_source_coverage_closeout" and
                  g["status"] == "REQUIRED" and not g["reuse_permitted"]
                  for g in plan["mandatory_gates"]),
              plan["mandatory_gates"])
    finally:
        conn.close()
        shutil.rmtree(root, ignore_errors=True)
        shutil.rmtree(os.path.dirname(db), ignore_errors=True)


# ── Scenario E — reuse creates no duplicate record ───────────────────────

def test_scenario_e_reuse_generates_no_duplicate_result_record():
    root, base = make_repo()
    db, conn = make_spine(base)
    try:
        commit(root, {"docs/NOTES.md": "x\n"}, "docs")
        before_events = cs.latest_revision(conn, "T")
        before_state = conn.execute("SELECT COUNT(*) FROM project_state").fetchone()[0]
        p1 = plan_for(root, conn, task="T")
        p2 = plan_for(root, conn, task="T")
        after_events = cs.latest_revision(conn, "T")
        after_state = conn.execute("SELECT COUNT(*) FROM project_state").fetchone()[0]
        check("E: previously accepted evidence IS reused",
              p1["reusable_evidence"], names(p1["reusable_evidence"]))
        check("E: building the plan twice writes no dev_continuity_events row",
              before_events == after_events, (before_events, after_events))
        check("E: building the plan twice writes no project_state row",
              before_state == after_state, (before_state, after_state))
        check("E: the plan declares that it records nothing",
              p1["records_nothing"] is True and p2["records_nothing"] is True)
        check("E: reused evidence is carried BY REFERENCE to the record that "
              "holds it, not copied as a new result",
              all(i["source"].startswith("project_state.external_dev_checkpoint")
                  for i in p1["reusable_evidence"]),
              [i["source"] for i in p1["reusable_evidence"]])
    finally:
        conn.close()
        shutil.rmtree(root, ignore_errors=True)
        shutil.rmtree(os.path.dirname(db), ignore_errors=True)


def test_superseded_checkpoint_fails_condition_three():
    root, base = make_repo()
    db, conn = make_spine(base, superseded=True)
    try:
        plan = plan_for(root, conn, task="T")
        check("a superseded checkpoint's evidence is not reused (condition 3)",
              plan["reusable_evidence"] == [] and
              any("condition 3" in i["invalidation_reason"]
                  for i in plan["invalidated_evidence"]),
              [i["invalidation_reason"] for i in plan["invalidated_evidence"]])
    finally:
        conn.close()
        shutil.rmtree(root, ignore_errors=True)
        shutil.rmtree(os.path.dirname(db), ignore_errors=True)


# ── Scenario F — a push is not an acceptance ─────────────────────────────

def test_scenario_f_pushed_commit_is_not_promoted_to_accepted():
    root, base = make_repo()
    db, conn = make_spine(base)
    try:
        head = commit(root, {"tools/alpha/core.py": "ALPHA = 3\n"}, "alpha change")
        plan = plan_for(root, conn, task="T")
        review = plan["independent_review"]
        check("F: a new commit beyond the accepted baseline is PENDING review",
              review["state"] == "PENDING_INDEPENDENT_REVIEW" and review["required"],
              review)
        check("F: the pushed SHA is reported, and it is not the accepted one",
              review["observed_head"] == head and
              review["accepted_baseline_sha"] == base, review)
        check("F: may_claim_acceptance is False",
              review["may_claim_acceptance"] is False, review)
        handoff = vplan.review_handoff(conn, task="T", repo_root=root, plan=plan)
        check("F: the review handoff also refuses to assert acceptance",
              handoff["may_claim_acceptance"] is False and
              handoff["independent_review_status"] == "PENDING_INDEPENDENT_REVIEW",
              handoff["independent_review_status"])
    finally:
        conn.close()
        shutil.rmtree(root, ignore_errors=True)
        shutil.rmtree(os.path.dirname(db), ignore_errors=True)


def test_scenario_f_self_verification_is_never_independent_authority():
    """A checkpoint that claims independent verification but names the
    pushing agent as the source is the implementing developer's own
    verification, and must be labeled as such."""
    root, base = make_repo()
    db, conn = make_spine(
        base, independently_verified=True,
        verification_source="Claude Code, CIS implementation agent re-ran the suite",
    )
    try:
        plan = plan_for(root, conn, task="T")
        items = plan["reusable_evidence"] + plan["invalidated_evidence"]
        check("F: self-named verification is authority 'implementing_developer'",
              items and all(i["authority"] == "implementing_developer" for i in items),
              [(i["name"], i["authority"]) for i in items])
        check("F: self-named verification is never independent acceptance",
              all(i["is_independent_acceptance"] is False for i in items),
              [(i["name"], i["is_independent_acceptance"]) for i in items])
    finally:
        conn.close()
        shutil.rmtree(root, ignore_errors=True)
        shutil.rmtree(os.path.dirname(db), ignore_errors=True)


def test_continuity_recorded_results_are_developer_evidence_only():
    root, base = make_repo()
    db, conn = make_spine(base)
    try:
        cs.publish_event(
            conn, task="T", kind="verified_result", status="VERIFIED",
            actor="claude_code", summary="test_beta.py 8/8 PASS at " + base,
            expected_prev_revision=0,
        )
        plan = plan_for(root, conn, task="T")
        items = [i for i in plan["reusable_evidence"] + plan["invalidated_evidence"]
                 if i["source"].startswith("dev_continuity_events")]
        check("a continuity verified_result is carried as developer evidence",
              items and all(i["authority"] == "implementing_developer" and
                            i["is_independent_acceptance"] is False for i in items),
              [(i["id"], i["authority"]) for i in items])
    finally:
        conn.close()
        shutil.rmtree(root, ignore_errors=True)
        shutil.rmtree(os.path.dirname(db), ignore_errors=True)


def test_evidence_with_no_tested_commit_identity_is_not_reused():
    root, base = make_repo()
    db, conn = make_spine(base)
    try:
        cs.publish_event(
            conn, task="T", kind="verified_result", status="VERIFIED",
            actor="claude_code", summary="test_beta.py 8/8 PASS",  # no SHA
            expected_prev_revision=0,
        )
        plan = plan_for(root, conn, task="T")
        bad = [i for i in plan["invalidated_evidence"]
               if i["source"].startswith("dev_continuity_events")]
        check("evidence with no tested commit identity fails condition 2",
              bad and all("condition 2" in i["invalidation_reason"] for i in bad),
              [i["invalidation_reason"] for i in bad])
    finally:
        conn.close()
        shutil.rmtree(root, ignore_errors=True)
        shutil.rmtree(os.path.dirname(db), ignore_errors=True)


# ── Scenario G — recovery supplies the baseline ──────────────────────────

def test_scenario_g_recovery_path_supplies_baseline_and_pending_review():
    """The recovery packet is the project's designated recovery view (HCP_05
    defers to it by name). After a fresh session it must hand over the
    verification baseline and the pending-review state."""
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "state"))
    import recovery_packet as rp  # noqa: PLC0415 — path set up just above

    pkt = rp.build_recovery_packet()
    vb = pkt.get("verification_baseline")
    check("G: the recovery packet carries a verification_baseline section",
          isinstance(vb, dict) and "accepted_baseline_sha" in vb, vb)
    check("G: it names the accepted baseline SHA from the checkpoint authority",
          bool(vb.get("accepted_baseline_sha")), vb.get("accepted_baseline_sha"))
    check("G: it states the independent-review state explicitly",
          vb.get("independent_review_state") in (
              "ACCEPTED_AT_THIS_COMMIT", "PENDING_INDEPENDENT_REVIEW",
              "NO_ACCEPTED_BASELINE_RECORDED", "UNKNOWN_LOCAL_STATE"),
          vb.get("independent_review_state"))
    check("G: it cannot be read as an acceptance",
          vb.get("may_claim_acceptance") is False, vb.get("may_claim_acceptance"))
    check("G: it points at how to re-derive the live plan rather than "
          "shipping a stale one",
          "verification-plan" in (vb.get("how_to_get_the_current_plan") or ""),
          vb.get("how_to_get_the_current_plan"))
    check("G: it is present regardless of issue focus",
          isinstance(rp.build_recovery_packet(issue="closeout")
                     .get("verification_baseline"), dict))


# ── Scenario H — no repeated manual instruction ──────────────────────────

def test_scenario_h_prepare_carries_the_plan_with_no_special_request():
    """An ordinary task's first step is `prepare`. It must come back with the
    plan without anyone naming this card, passing a flag, or running an
    extra command."""
    root, base = make_repo()
    db, conn = make_spine(base)
    try:
        conn.executescript(
            "CREATE TABLE queue_items (item_num TEXT PRIMARY KEY, title TEXT, "
            "body_md TEXT, need_status TEXT, status_changed_at TEXT, source_sha TEXT);"
            "CREATE TABLE queue_item_events (id INTEGER PRIMARY KEY, item_num TEXT);"
        )
        conn.execute(
            "INSERT INTO queue_items VALUES ('9.1','ordinary task','do the thing',"
            "'OPEN','2026-10-07T00:00:00Z','abc')"
        )
        commit(root, {"docs/NOTES.md": "y\n"}, "docs")
        pkt = packet_mod.prepare_packet(conn, task="9.1", actor="claude_code")
        plan = pkt.get("verification_plan")
        check("H: prepare() returns a verification_plan with no flag or mention "
              "of this card",
              isinstance(plan, dict) and plan.get("plan_kind") == vplan.PLAN_KIND,
              plan if not isinstance(plan, dict) else plan.get("plan_kind"))
        check("H: the carried plan has the five answers the card requires",
              isinstance(plan, dict) and all(
                  k in plan for k in ("reusable_evidence", "required_new_evidence",
                                       "mandatory_gates", "invalidated_evidence",
                                       "independent_review")),
              sorted(plan) if isinstance(plan, dict) else plan)
        check("H: carrying the plan does not make the packet stale — it is "
              "deliberately outside the fingerprint",
              "verification_plan" not in pkt["fingerprint"] and
              not packet_mod.check_freshness(conn, pkt)["stale"],
              packet_mod.check_freshness(conn, pkt)["reasons"])
    finally:
        conn.close()
        shutil.rmtree(root, ignore_errors=True)
        shutil.rmtree(os.path.dirname(db), ignore_errors=True)


def test_prepare_degrades_loudly_if_the_plan_cannot_be_built():
    """A packet that silently omits the plan would read as 'nothing to
    verify'. Failure must be an explicit field."""
    root, base = make_repo()
    db, conn = make_spine(base)
    try:
        conn.executescript(
            "CREATE TABLE queue_items (item_num TEXT PRIMARY KEY, title TEXT, "
            "body_md TEXT, need_status TEXT, status_changed_at TEXT, source_sha TEXT);"
            "CREATE TABLE queue_item_events (id INTEGER PRIMARY KEY, item_num TEXT);"
        )
        conn.execute(
            "INSERT INTO queue_items VALUES ('9.1','t','b','OPEN','2026-10-07','a')"
        )
        real = vplan.build_plan
        vplan.build_plan = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom"))
        try:
            pkt = packet_mod.prepare_packet(conn, task="9.1", actor="claude_code")
        finally:
            vplan.build_plan = real
        plan = pkt["verification_plan"]
        check("a plan failure is reported as an explicit error, never omitted",
              plan.get("ok") is False and "boom" in plan.get("error", "") and
              "broader verification" in plan.get("effect", ""), plan)
    finally:
        conn.close()
        shutil.rmtree(root, ignore_errors=True)
        shutil.rmtree(os.path.dirname(db), ignore_errors=True)


# ── git correctness (card section 6) ─────────────────────────────────────

def test_push_confirmation_required_for_a_new_push_and_not_repeated_otherwise():
    root, base = make_repo()
    db, conn = make_spine(base)
    try:
        # No new commit, and the checkpoint already records this SHA as pushed,
        # but there is no upstream ref in this throwaway repo — so the fact is
        # NOT established and the check is still required. Absence of proof is
        # not proof.
        plan = plan_for(root, conn, task="T")
        gate = [g for g in plan["mandatory_gates"] if g["id"] == "git_push_confirmation"][0]
        check("section 6: push confirmation is REQUIRED when the durable record "
              "does not establish it for the observed HEAD",
              gate["status"] == "REQUIRED", gate)

        # Now simulate the established case: the durable record names this
        # exact SHA as pushed AND the observed upstream ref agrees.
        git_state = {"head": base, "upstream_sha": base, "upstream_ref": "origin/master"}
        baseline = vplan.accepted_baseline(conn)
        gates = vplan.mandatory_gates(baseline, git_state)
        gate = [g for g in gates if g["id"] == "git_push_confirmation"][0]
        check("section 6: it is NOT repeated when the durable result already "
              "establishes the same fact for the same commit",
              gate["status"] == "ESTABLISHED_BY_DURABLE_RECORD" and
              "no new push has occurred" in gate["why_not_repeated"], gate)

        # A new commit must flip it straight back to required.
        new_head = commit(root, {"tools/beta/core.py": "BETA = 9\n"}, "beta")
        gates = vplan.mandatory_gates(
            baseline, {"head": new_head, "upstream_sha": base,
                       "upstream_ref": "origin/master"})
        gate = [g for g in gates if g["id"] == "git_push_confirmation"][0]
        check("section 6: a new commit makes push confirmation required again",
              gate["status"] == "REQUIRED", gate)
    finally:
        conn.close()
        shutil.rmtree(root, ignore_errors=True)
        shutil.rmtree(os.path.dirname(db), ignore_errors=True)


def test_accepted_at_this_commit_requires_no_new_review():
    root, base = make_repo()
    db, conn = make_spine(base)
    try:
        plan = plan_for(root, conn, task="T")
        review = plan["independent_review"]
        check("HEAD equal to the accepted baseline needs no new acceptance",
              review["state"] == "ACCEPTED_AT_THIS_COMMIT" and
              review["required"] is False, review)
        check("even then, acceptance may not be CLAIMED by the developer",
              review["may_claim_acceptance"] is False, review)
    finally:
        conn.close()
        shutil.rmtree(root, ignore_errors=True)
        shutil.rmtree(os.path.dirname(db), ignore_errors=True)


def test_awkward_paths_are_not_silently_misclassified():
    """git quotes and octal-escapes paths with spaces or non-ASCII bytes by
    default. A mangled path resolves to no component and would be reported as
    unknown impact — honest but wrong. The -z readers must prevent it."""
    root, base = make_repo()
    db, conn = make_spine(base)
    try:
        commit(root, {"tools/alpha/a file with spaces.py": "Z = 1\n"}, "spacey")
        plan = plan_for(root, conn, task="T")
        scope = plan["changed_scope"]
        check("a path with spaces is read verbatim and resolved to its component",
              "tools/alpha/a file with spaces.py" in scope["changed_files"] and
              "tools/alpha" in scope["components"] and
              not scope["undetermined_files"], scope)
    finally:
        conn.close()
        shutil.rmtree(root, ignore_errors=True)
        shutil.rmtree(os.path.dirname(db), ignore_errors=True)


def test_uncommitted_work_is_in_scope_and_said_to_be_uncommitted():
    root, base = make_repo()
    db, conn = make_spine(base)
    try:
        with open(os.path.join(root, "tools/beta/core.py"), "w", encoding="utf-8") as f:
            f.write("BETA = 77\n")
        plan = plan_for(root, conn, task="T")
        check("uncommitted changes count as changed scope",
              "tools/beta" in plan["changed_scope"]["components"],
              plan["changed_scope"]["components"])
        check("and the plan says they are not in any commit yet",
              any("uncommitted" in l for l in plan["limitations"]),
              plan["limitations"])
    finally:
        conn.close()
        shutil.rmtree(root, ignore_errors=True)
        shutil.rmtree(os.path.dirname(db), ignore_errors=True)


# ── the handoff and return packet (card sections 8 and 9) ────────────────

def test_review_handoff_identifies_everything_section_nine_requires():
    root, base = make_repo()
    db, conn = make_spine(base)
    try:
        commit(root, {"tools/alpha/core.py": "ALPHA = 4\n",
                      "runtime/schema/migrations/0003_x.sql": "SELECT 3;\n"},
               "alpha + migration")
        handoff = vplan.review_handoff(conn, task="T", repo_root=root,
                                        question="Is the migration reversible?")
        required = [
            "pushed_sha", "accepted_baseline_sha", "changed_files",
            "components_and_dependencies", "required_new_evidence",
            "reused_evidence", "mandatory_gates", "security_sensitive_changes",
            "question_requiring_independent_judgment",
        ]
        missing = [k for k in required if k not in handoff]
        check("section 9: the handoff carries every field the card enumerates",
              not missing, missing)
        check("section 9: security-sensitive changes are called out",
              handoff["security_labels"] and handoff["security_sensitive_changes"],
              handoff["security_labels"])
        check("section 9: the developer's question is carried verbatim",
              handoff["question_requiring_independent_judgment"]
              == "Is the migration reversible?" and
              handoff["question_supplied_by_developer"], handoff)
        check("section 9: with no question supplied, the default is stated and "
              "flagged as not developer-supplied",
              vplan.review_handoff(conn, task="T", repo_root=root)
              ["question_supplied_by_developer"] is False)
    finally:
        conn.close()
        shutil.rmtree(root, ignore_errors=True)
        shutil.rmtree(os.path.dirname(db), ignore_errors=True)


def test_return_packet_has_the_eight_sections_and_stays_short():
    root, base = make_repo()
    db, conn = make_spine(base)
    try:
        commit(root, {"tools/alpha/core.py": "ALPHA = 5\n"}, "alpha")
        handoff = vplan.review_handoff(conn, task="T", repo_root=root)
        text = vplan.render_return_packet(
            handoff, status="IMPLEMENTED, PUSHED, AWAITING REVIEW",
            what_changed="one constant in tools/alpha",
            next_action="independent review of the pushed SHA")
        headings = ["1. STATUS", "2. SHAs", "3. WHAT CHANGED",
                    "4. NEW VERIFICATION REQUIRED", "5. REUSED EVIDENCE",
                    "6. EXCEPTIONS", "7. INDEPENDENT REVIEW",
                    "8. EXACT NEXT ACTION"]
        missing = [h for h in headings if h not in text]
        check("section 8: all eight sections are present, in order", not missing, missing)
        check("section 8: reused evidence appears as a reference to its record, "
              "not as a copy of the record",
              "project_state.external_dev_checkpoint" in text, text[:400])
        check("section 8: the packet is short (a projection, not a report)",
              len(text) < 4000, len(text))
        check("section 8: it never claims acceptance",
              "acceptance may NOT be claimed" in text, text)
    finally:
        conn.close()
        shutil.rmtree(root, ignore_errors=True)
        shutil.rmtree(os.path.dirname(db), ignore_errors=True)


# ── CLI surface ──────────────────────────────────────────────────────────

def _cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "tools.development.cli", *args],
        capture_output=True, text=True,
        cwd=os.path.join(os.path.dirname(__file__), "..", "..", ".."),
    )


def test_cli_subcommands_work_and_exit_honestly():
    root, base = make_repo()
    db, conn = make_spine(base)
    conn.close()
    try:
        r = _cli("--db", db, "verification-plan", "--task", "T")
        try:
            payload = json.loads(r.stdout)
        except json.JSONDecodeError:
            payload = None
        check("cli verification-plan prints a JSON plan",
              payload is not None and payload["plan_kind"] == vplan.PLAN_KIND,
              (r.returncode, r.stdout[:200], r.stderr[:300]))
        # The plan is built against the REAL repo (cwd), whose baseline differs
        # from this fixture's, so limitations exist and the exit must say so.
        check("cli verification-plan exits nonzero when the plan has limitations",
              (r.returncode == 0) == (not payload["limitations"]),
              (r.returncode, payload["limitations"] if payload else None))

        r = _cli("--db", db, "review-handoff", "T", "--format", "text")
        check("cli review-handoff --format text prints the return packet",
              "8. EXACT NEXT ACTION" in r.stdout, (r.returncode, r.stderr[:300]))
        check("cli review-handoff exits nonzero while review is outstanding, so "
              "no caller can read a produced handoff as an accepted one",
              r.returncode == 1, r.returncode)
    finally:
        shutil.rmtree(root, ignore_errors=True)
        shutil.rmtree(os.path.dirname(db), ignore_errors=True)


# ── read-only observations against the live repository ───────────────────

def test_live_repository_observations():
    """Marked read-only, reported honestly including FAIL. These assert the
    module works against the REAL repository layout and checkpoint, not only
    against a fixture that happens to match its assumptions."""
    tm = vplan.derive_test_map()
    check("live (read-only): the real repository's test map derives components",
          tm["ok"] and {"tools/development", "tools/state", "tools/export",
                        "tools/kb", "tools/queue", "runtime"} <= set(tm["components"]),
          sorted(tm["components"])[:15] if tm["ok"] else tm["error"])
    check("live (read-only): the repo-root tests/ dir is a repository-wide "
          "suite, not a component",
          "tests" in tm["repo_wide_suites"] and "" not in tm["components"],
          tm["repo_wide_suites"])

    conn = cs.connect(None)
    try:
        baseline = vplan.accepted_baseline(conn)
        check("live (read-only): the production checkpoint parses and names an "
              "accepted baseline SHA",
              baseline["present"] and bool(baseline["accepted_baseline_sha"]),
              baseline.get("note") or baseline.get("error"))
        git_state = vplan.observed_git()
        review = vplan.independent_review_status(baseline, git_state)
        check("live (read-only): the real state is reported as one of the "
              "defined review states, and never as a claimable acceptance",
              review["state"] in ("ACCEPTED_AT_THIS_COMMIT",
                                   "PENDING_INDEPENDENT_REVIEW",
                                   "NO_ACCEPTED_BASELINE_RECORDED",
                                   "UNKNOWN_LOCAL_STATE") and
              review["may_claim_acceptance"] is False,
              review["state"])
        check("live (read-only): a plan builds against the real repository and "
              "writes nothing",
              vplan.build_plan(conn, task="WB.1")["records_nothing"] is True)
    finally:
        conn.close()


def run():
    test_test_map_is_derived_not_registered()
    test_scenario_a_documentation_change_triggers_no_unrelated_tests()
    test_scenario_b_changed_component_invalidates_only_its_own_evidence()
    test_scenario_c_unknown_impact_never_assumes_validity()
    test_scenario_c_unresolvable_baseline_blocks_all_reuse()
    test_no_baseline_at_all_requires_full_verification()
    test_scenario_d_security_sensitive_change_retains_required_depth()
    test_scenario_d_every_security_class_the_card_names_is_covered()
    test_mandatory_gates_are_never_reusable()
    test_scenario_e_reuse_generates_no_duplicate_result_record()
    test_superseded_checkpoint_fails_condition_three()
    test_scenario_f_pushed_commit_is_not_promoted_to_accepted()
    test_scenario_f_self_verification_is_never_independent_authority()
    test_continuity_recorded_results_are_developer_evidence_only()
    test_evidence_with_no_tested_commit_identity_is_not_reused()
    test_scenario_g_recovery_path_supplies_baseline_and_pending_review()
    test_scenario_h_prepare_carries_the_plan_with_no_special_request()
    test_prepare_degrades_loudly_if_the_plan_cannot_be_built()
    test_push_confirmation_required_for_a_new_push_and_not_repeated_otherwise()
    test_accepted_at_this_commit_requires_no_new_review()
    test_awkward_paths_are_not_silently_misclassified()
    test_uncommitted_work_is_in_scope_and_said_to_be_uncommitted()
    test_review_handoff_identifies_everything_section_nine_requires()
    test_return_packet_has_the_eight_sections_and_stays_short()
    test_cli_subcommands_work_and_exit_honestly()
    test_live_repository_observations()

    failures = [r for r in results if "FAIL" in r]
    print(f"\n{len(results) - len(failures)}/{len(results)} passed.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(run())
