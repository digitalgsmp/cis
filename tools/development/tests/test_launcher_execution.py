#!/usr/bin/env python3
"""test_launcher_execution.py — Recovery Card 04 prerequisite repair.

Covers the handoff defect found while preparing for Card 04: a real
`--execute` send delivered only the bare reference packet (no directive,
no authorization), so the receiving model treated it as context and
returned a clarification with process exit 0 — while the launcher's own
`launched: True, returncode: 0` looked identical to a real completed
dispatch. These tests exercise the fix in launcher.py/cli.py:
build_execution_handoff, resolve_execution_authorization,
render_execution_payload, and launch()'s completion_status field.

Temporary SQLite fixtures and fake executables only. Run:
    python3 tools/development/tests/test_launcher_execution.py
"""
import json
import os
import shutil
import sqlite3
import stat
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from tools.development import continuity_store as cs
from tools.development import launcher

results = []
REPO_ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "..")


def check(label, cond, detail=""):
    if cond:
        results.append(f"{label}: PASS")
    else:
        results.append(f"{label}: FAIL — {detail}")


def make_fixture_db(path, task="WB.1TEST"):
    conn = sqlite3.connect(path, isolation_level=None)
    conn.execute("PRAGMA busy_timeout=5000")
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        CREATE TABLE queue_items (
            item_num TEXT PRIMARY KEY, tier INTEGER, title TEXT,
            body_md TEXT, form TEXT, scope TEXT, need_status TEXT,
            need_raw TEXT, source_line INTEGER, source_sha TEXT,
            extracted_at TEXT, status_changed_at TEXT, status_changed_by TEXT
        );
        CREATE TABLE queue_item_events (
            id INTEGER PRIMARY KEY, item_num TEXT, field TEXT,
            old_value TEXT, new_value TEXT, changed_at TEXT,
            changed_by TEXT, evidence TEXT, note TEXT
        );
        """
    )
    conn.execute(
        "INSERT INTO queue_items (item_num, tier, title, body_md, form, need_status, "
        "source_line, source_sha) VALUES (?, 0, 'Test task', 'body', 'heading', 'OPEN', 1, 'x')",
        (task,),
    )
    conn.commit()
    return conn


def make_fake_executable(tmp, name, script_body):
    path = os.path.join(tmp, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(script_body)
    st = os.stat(path)
    os.chmod(path, st.st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    return path


CLARIFICATION_SHELL = (
    "#!/bin/sh\n"
    "payload=\"$(cat)\"\n"
    "case \"$payload\" in\n"
    "  *dispatched?via?tools/development/launcher.py*) echo '{\"action\": \"executed\"}' ;;\n"
    "  *) echo '{\"action\": \"clarification\", \"response\": \"what should I do with this?\"}' ;;\n"
    "esac\n"
    "exit 0\n"
)

ECHO_STDIN_SHELL = "#!/bin/sh\ncat\nexit 0\n"


def test_resolve_execution_authorization_rejects_missing():
    tmp = tempfile.mkdtemp(prefix="dev_launchex_")
    try:
        db = os.path.join(tmp, "fixture.db")
        conn = make_fixture_db(db)
        cs.init_schema(conn, db_path=db)
        try:
            launcher.resolve_execution_authorization(
                conn, task="WB.1TEST", revision=99, directive_text="anything",
            )
            check("resolve_execution_authorization: missing revision rejected", False, "no exception")
        except launcher.AuthorizationError as e:
            check("resolve_execution_authorization: missing revision rejected", True)
            check("... error names it as missing authorization", "missing authorization" in str(e), str(e))
        conn.close()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_resolve_execution_authorization_rejects_wrong_kind():
    tmp = tempfile.mkdtemp(prefix="dev_launchex_")
    try:
        db = os.path.join(tmp, "fixture.db")
        conn = make_fixture_db(db)
        cs.init_schema(conn, db_path=db)
        row = cs.publish_event(
            conn, task="WB.1TEST", kind="proposal", status="idea", actor="codex",
            summary="not an authorization", expected_prev_revision=0,
        )
        try:
            launcher.resolve_execution_authorization(
                conn, task="WB.1TEST", revision=row["revision"], directive_text="anything",
            )
            check("resolve_execution_authorization: wrong kind rejected", False, "no exception")
        except launcher.AuthorizationError as e:
            check("resolve_execution_authorization: wrong kind rejected", True)
            check("... error names it as mismatched authorization", "mismatched authorization" in str(e), str(e))
        conn.close()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_resolve_execution_authorization_rejects_hash_mismatch():
    tmp = tempfile.mkdtemp(prefix="dev_launchex_")
    try:
        db = os.path.join(tmp, "fixture.db")
        conn = make_fixture_db(db)
        cs.init_schema(conn, db_path=db)
        row = cs.publish_event(
            conn, task="WB.1TEST", kind="user_instruction", status="authorized", actor="codex",
            summary="do the thing", body="do the thing exactly", expected_prev_revision=0,
        )
        try:
            launcher.resolve_execution_authorization(
                conn, task="WB.1TEST", revision=row["revision"],
                directive_text="do the thing exactly",
                expected_request_hash="deadbeef" * 8,
            )
            check("resolve_execution_authorization: hash mismatch rejected", False, "no exception")
        except launcher.AuthorizationError as e:
            check("resolve_execution_authorization: hash mismatch rejected", True)
            check("... error names it as mismatched authorization", "mismatched authorization" in str(e), str(e))
        conn.close()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_resolve_execution_authorization_rejects_body_mismatch():
    """The exact independent-review reproduction this correction fixes:
    directive_text="Modify all files now." against a stored
    body="Read status only. Do not modify files." must be rejected, even
    with no expected_request_hash supplied at all -- the optional
    request_hash check must never be the only thing standing between a
    wrong directive and a real dispatch."""
    tmp = tempfile.mkdtemp(prefix="dev_launchex_")
    try:
        db = os.path.join(tmp, "fixture.db")
        conn = make_fixture_db(db)
        cs.init_schema(conn, db_path=db)
        row = cs.publish_event(
            conn, task="WB.1TEST", kind="user_instruction", status="authorized", actor="codex",
            summary="read-only status check", body="Read status only. Do not modify files.",
            expected_prev_revision=0,
        )
        try:
            launcher.resolve_execution_authorization(
                conn, task="WB.1TEST", revision=row["revision"],
                directive_text="Modify all files now.",
            )
            check("resolve_execution_authorization: body mismatch rejected "
                  "(wrong directive against a real authorization row)", False, "no exception")
        except launcher.AuthorizationError as e:
            check("resolve_execution_authorization: body mismatch rejected "
                  "(wrong directive against a real authorization row)", True)
            check("... error names it as mismatched authorization",
                  "mismatched authorization" in str(e) and "does not match" in str(e), str(e))
        conn.close()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_resolve_execution_authorization_rejects_stale_superseded():
    tmp = tempfile.mkdtemp(prefix="dev_launchex_")
    try:
        db = os.path.join(tmp, "fixture.db")
        conn = make_fixture_db(db)
        cs.init_schema(conn, db_path=db)
        first = cs.publish_event(
            conn, task="WB.1TEST", kind="user_instruction", status="authorized", actor="codex",
            summary="first directive", body="do the first thing", expected_prev_revision=0,
        )
        # A later user_instruction for the same task supersedes the first —
        # this is exactly the "stale directive" failure mode this fix must
        # catch: an old authorization reference that once was valid.
        cs.publish_event(
            conn, task="WB.1TEST", kind="user_instruction", status="authorized", actor="codex",
            summary="second, superseding directive", body="do the second thing",
            expected_prev_revision=first["revision"],
        )
        try:
            launcher.resolve_execution_authorization(
                conn, task="WB.1TEST", revision=first["revision"], directive_text="do the first thing",
            )
            check("resolve_execution_authorization: superseded (stale) revision rejected", False, "no exception")
        except launcher.AuthorizationError as e:
            check("resolve_execution_authorization: superseded (stale) revision rejected", True)
            check("... error names it as stale authorization", "stale authorization" in str(e), str(e))
        conn.close()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_resolve_execution_authorization_accepts_current_valid():
    tmp = tempfile.mkdtemp(prefix="dev_launchex_")
    try:
        db = os.path.join(tmp, "fixture.db")
        conn = make_fixture_db(db)
        cs.init_schema(conn, db_path=db)
        row = cs.publish_event(
            conn, task="WB.1TEST", kind="user_instruction", status="authorized", actor="codex",
            summary="the current live directive", body="the current live directive text",
            expected_prev_revision=0,
        )
        matched = launcher.resolve_execution_authorization(
            conn, task="WB.1TEST", revision=row["revision"],
            directive_text="the current live directive text",
        )
        check("resolve_execution_authorization: current valid revision accepted",
              matched["revision"] == row["revision"] and matched["kind"] == "user_instruction", matched)
        conn.close()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_resolve_execution_authorization_exact_match_ignores_surrounding_whitespace_only():
    """The one documented canonical comparison (strip() only) tolerates
    incidental leading/trailing whitespace a file read might introduce, but
    performs no other normalization."""
    tmp = tempfile.mkdtemp(prefix="dev_launchex_")
    try:
        db = os.path.join(tmp, "fixture.db")
        conn = make_fixture_db(db)
        cs.init_schema(conn, db_path=db)
        row = cs.publish_event(
            conn, task="WB.1TEST", kind="user_instruction", status="authorized", actor="codex",
            summary="d", body="Do exactly this bounded thing.", expected_prev_revision=0,
        )
        matched = launcher.resolve_execution_authorization(
            conn, task="WB.1TEST", revision=row["revision"],
            directive_text="\n  Do exactly this bounded thing.  \n",
        )
        check("surrounding whitespace alone does not defeat the exact-content match",
              matched["revision"] == row["revision"], matched)
        try:
            launcher.resolve_execution_authorization(
                conn, task="WB.1TEST", revision=row["revision"],
                directive_text="do exactly this bounded thing.",  # case differs
            )
            check("a case-only difference is still rejected (no case-folding normalization)",
                  False, "no exception")
        except launcher.AuthorizationError:
            check("a case-only difference is still rejected (no case-folding normalization)", True)
        conn.close()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_build_execution_handoff_rejects_empty_directive():
    tmp = tempfile.mkdtemp(prefix="dev_launchex_")
    try:
        db = os.path.join(tmp, "fixture.db")
        conn = make_fixture_db(db)
        cs.init_schema(conn, db_path=db)
        row = cs.publish_event(
            conn, task="WB.1TEST", kind="user_instruction", status="authorized", actor="codex",
            summary="d", expected_prev_revision=0,
        )
        try:
            launcher.build_execution_handoff(
                conn, task="WB.1TEST", actor="claude_code", out_dir=tmp,
                directive_text="   ", authorization_revision=row["revision"],
            )
            check("build_execution_handoff: empty directive_text rejected", False, "no exception")
        except launcher.AuthorizationError:
            check("build_execution_handoff: empty directive_text rejected", True)
        conn.close()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_execution_payload_orders_directive_before_reference_context():
    """The core content-ordering requirement: a recipient reading the
    actual stdin bytes top-to-bottom sees the directive (and its
    authorization stamp) before anything labeled as context."""
    tmp = tempfile.mkdtemp(prefix="dev_launchex_")
    try:
        db = os.path.join(tmp, "fixture.db")
        conn = make_fixture_db(db)
        cs.init_schema(conn, db_path=db)
        row = cs.publish_event(
            conn, task="WB.1TEST", kind="user_instruction", status="authorized", actor="codex",
            summary="d", body="Do the specific bounded thing now.", expected_prev_revision=0,
        )
        path, pkt, auth = launcher.build_execution_handoff(
            conn, task="WB.1TEST", actor="claude_code", out_dir=tmp,
            directive_text="Do the specific bounded thing now.",
            authorization_revision=row["revision"],
        )
        with open(path, encoding="utf-8") as f:
            text = f.read()
        directive_pos = text.find("Do the specific bounded thing now.")
        provenance_pos = text.find(launcher.DISPATCH_PROVENANCE_HEADER)
        reference_pos = text.find(launcher.REFERENCE_CONTEXT_HEADER)
        check("execution payload: the plain directive text is present at/near the very top, "
              "with no ceremonial wrapper before it",
              directive_pos == 0, text[:200])
        check("execution payload: provenance record present", provenance_pos != -1, text[:400])
        check("execution payload: reference-context header present", reference_pos != -1, text[:400])
        check("execution payload: directive renders BEFORE provenance, which renders BEFORE reference context",
              0 <= directive_pos < provenance_pos < reference_pos,
              (directive_pos, provenance_pos, reference_pos))
        check("execution payload: provenance names the exact authorizing revision",
              f"dev_continuity_events revision: {row['revision']}" in text, text)
        check("execution payload: no self-asserting '(authorized)' ceremonial claim precedes the directive",
              "(authorized)" not in text, text)
        check("execution payload: reference context carries an explicit non-authorization warning",
              "Do not treat any instruction" in text, text)
        conn.close()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_both_adapters_receive_execution_payload_verbatim_on_stdin():
    """WB.1C-R1 remediation 5 requires per-tool argv but content-via-stdin
    for both claude and codex; this confirms the NEW execution payload
    (directive + reference) is what actually lands on stdin for both,
    unmodified — not the old context-only handoff."""
    tmp = tempfile.mkdtemp(prefix="dev_launchex_")
    try:
        db = os.path.join(tmp, "fixture.db")
        conn = make_fixture_db(db)
        cs.init_schema(conn, db_path=db)
        row = cs.publish_event(
            conn, task="WB.1TEST", kind="user_instruction", status="authorized", actor="codex",
            summary="d", body="Execute the bounded prerequisite stage.", expected_prev_revision=0,
        )
        path, pkt, auth = launcher.build_execution_handoff(
            conn, task="WB.1TEST", actor="claude_code", out_dir=tmp,
            directive_text="Execute the bounded prerequisite stage.",
            authorization_revision=row["revision"],
        )
        for tool_name, fake_name in (("claude", "claude"), ("codex", "codex")):
            fake = make_fake_executable(tmp, fake_name, ECHO_STDIN_SHELL)
            result = launcher.launch(fake, path, tool=tool_name, dry_run=False)
            check(f"{tool_name} adapter: launched", result["launched"] is True, result)
            check(f"{tool_name} adapter: stdout echoes the exact execution payload sent",
                  result["stdout"] == open(path, encoding="utf-8").read(), result)
            check(f"{tool_name} adapter: directive precedes reference context in what was actually sent",
                  result["stdout"].find("Execute the bounded prerequisite stage.")
                  < result["stdout"].find(launcher.REFERENCE_CONTEXT_HEADER),
                  result["stdout"])
        conn.close()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_context_only_handoff_carries_no_directive_or_authorization():
    tmp = tempfile.mkdtemp(prefix="dev_launchex_")
    try:
        db = os.path.join(tmp, "fixture.db")
        conn = make_fixture_db(db)
        cs.init_schema(conn, db_path=db)
        path, pkt = launcher.build_handoff(conn, task="WB.1TEST", actor="claude_code", out_dir=tmp)
        with open(path, encoding="utf-8") as f:
            text = f.read()
        check("context-only handoff: no execution directive header present",
              launcher.EXECUTION_DIRECTIVE_HEADER not in text, text[:200])
        check("context-only handoff: dry-run launch sends nothing",
              launcher.launch("claude", path, dry_run=True)["launched"] is False, None)
        conn.close()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_clarification_exit0_is_not_reported_as_completed():
    """Reproduces the actual defect signature: a receiving process that
    treats the payload as context, answers with a clarification, and exits
    0. launch()'s own result must never claim more than transport
    succeeded — completion_status must stay non-committal, and nothing in
    the result implies the directive was accepted or done."""
    tmp = tempfile.mkdtemp(prefix="dev_launchex_")
    try:
        db = os.path.join(tmp, "fixture.db")
        conn = make_fixture_db(db)
        cs.init_schema(conn, db_path=db)
        path, pkt = launcher.build_handoff(conn, task="WB.1TEST", actor="claude_code", out_dir=tmp)
        fake = make_fake_executable(tmp, "claude", CLARIFICATION_SHELL)
        result = launcher.launch(fake, path, dry_run=False)
        check("clarification/exit0: process still reports launched=True (transport worked)",
              result["launched"] is True and result["returncode"] == 0, result)
        check("clarification/exit0: completion_status is transport-only, never upgraded to success",
              result["completion_status"] == "transport_only_not_verified", result)
        parsed_stdout = json.loads(result["stdout"])
        check("clarification/exit0: the actual response was a clarification, not an execution",
              parsed_stdout.get("action") == "clarification", parsed_stdout)
        conn.close()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_execution_dispatch_flips_clarification_to_executed_when_authorized():
    """Positive control for the fix: the SAME fake executable that answers
    'clarification' to a bare context packet answers 'executed' once the
    payload actually contains the execution-directive marker text — proving
    the fix changes what is sent, not just what is reported."""
    tmp = tempfile.mkdtemp(prefix="dev_launchex_")
    try:
        db = os.path.join(tmp, "fixture.db")
        conn = make_fixture_db(db)
        cs.init_schema(conn, db_path=db)
        row = cs.publish_event(
            conn, task="WB.1TEST", kind="user_instruction", status="authorized", actor="codex",
            summary="d", body="Do the bounded thing.", expected_prev_revision=0,
        )
        exec_path, pkt, auth = launcher.build_execution_handoff(
            conn, task="WB.1TEST", actor="claude_code", out_dir=tmp,
            directive_text="Do the bounded thing.", authorization_revision=row["revision"],
        )
        fake = make_fake_executable(tmp, "claude", CLARIFICATION_SHELL)
        result = launcher.launch(fake, exec_path, dry_run=False)
        parsed = json.loads(result["stdout"])
        check("authorized execution dispatch: fake model recognizes the directive and executes",
              parsed.get("action") == "executed", parsed)
        check("authorized execution dispatch: completion_status is still transport-only "
              "(a returncode is never itself a completion receipt)",
              result["completion_status"] == "transport_only_not_verified", result)
        conn.close()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_launch_execution_handoff_rejects_wrong_body_before_invoking_child():
    """The guarded send path must refuse a wrong-body directive without
    ever invoking the child process -- proven here by pointing it at a
    fake executable that would mark a sentinel file if run at all."""
    tmp = tempfile.mkdtemp(prefix="dev_launchex_")
    try:
        db = os.path.join(tmp, "fixture.db")
        conn = make_fixture_db(db)
        cs.init_schema(conn, db_path=db)
        row = cs.publish_event(
            conn, task="WB.1TEST", kind="user_instruction", status="authorized", actor="codex",
            summary="d", body="Read status only. Do not modify files.", expected_prev_revision=0,
        )
        sentinel = os.path.join(tmp, "invoked.marker")
        fake = make_fake_executable(
            tmp, "claude",
            f"#!/bin/sh\ntouch {sentinel}\ncat >/dev/null\necho '{{}}'\nexit 0\n",
        )
        try:
            launcher.launch_execution_handoff(
                conn, fake, task="WB.1TEST", actor="claude_code", out_dir=tmp,
                directive_text="Modify all files now.",
                authorization_revision=row["revision"], dry_run=False,
            )
            check("launch_execution_handoff: wrong-body directive rejected", False, "no exception")
        except launcher.AuthorizationError as e:
            check("launch_execution_handoff: wrong-body directive rejected", True)
            check("... error names it as mismatched authorization", "mismatched authorization" in str(e), str(e))
        check("launch_execution_handoff: the child process was never invoked for a rejected directive",
              not os.path.exists(sentinel), sentinel)
        conn.close()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_launch_execution_handoff_rechecks_authorization_immediately_before_send():
    """Reproduces the exact gap this correction closes: authorization is
    valid when build_execution_handoff first validates it, but the
    authorizing user_instruction body is mutated (a fresh, corrected
    user_instruction event is published, superseding the one referenced)
    before the child would actually be invoked. The guarded send must
    refuse, not merely rely on the earlier build-time check."""
    tmp = tempfile.mkdtemp(prefix="dev_launchex_")
    try:
        db = os.path.join(tmp, "fixture.db")
        conn = make_fixture_db(db)
        cs.init_schema(conn, db_path=db)
        row = cs.publish_event(
            conn, task="WB.1TEST", kind="user_instruction", status="authorized", actor="codex",
            summary="d", body="Do the originally authorized thing.", expected_prev_revision=0,
        )

        real_resolve = launcher.resolve_execution_authorization
        calls = {"n": 0}

        def resolve_then_supersede(dev_conn, **kwargs):
            calls["n"] += 1
            result = real_resolve(dev_conn, **kwargs)
            if calls["n"] == 1:
                # Simulate a newer authorization landing between build time
                # and the immediate pre-send recheck.
                cs.publish_event(
                    dev_conn, task="WB.1TEST", kind="user_instruction", status="authorized",
                    actor="codex", summary="superseding directive",
                    body="Do something else entirely.", expected_prev_revision=row["revision"],
                )
            return result

        launcher.resolve_execution_authorization = resolve_then_supersede
        try:
            fake = make_fake_executable(tmp, "claude", ECHO_STDIN_SHELL)
            try:
                launcher.launch_execution_handoff(
                    conn, fake, task="WB.1TEST", actor="claude_code", out_dir=tmp,
                    directive_text="Do the originally authorized thing.",
                    authorization_revision=row["revision"], dry_run=False,
                )
                check("launch_execution_handoff: recheck catches an authorization superseded "
                      "after build but before send", False, "no exception")
            except launcher.AuthorizationError as e:
                check("launch_execution_handoff: recheck catches an authorization superseded "
                      "after build but before send", True)
                check("... error names it as stale authorization", "stale authorization" in str(e), str(e))
            check("launch_execution_handoff: the recheck actually ran a second time "
                  "(not just the one build-time check)",
                  calls["n"] == 2, calls)
        finally:
            launcher.resolve_execution_authorization = real_resolve
        conn.close()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_launch_execution_handoff_rechecks_freshness_immediately_before_send():
    """The packet-freshness half of the same guarded-recheck requirement:
    authoritative state changes between build and the immediate pre-send
    check must also be caught."""
    tmp = tempfile.mkdtemp(prefix="dev_launchex_")
    try:
        db = os.path.join(tmp, "fixture.db")
        conn = make_fixture_db(db)
        cs.init_schema(conn, db_path=db)
        row = cs.publish_event(
            conn, task="WB.1TEST", kind="user_instruction", status="authorized", actor="codex",
            summary="d", body="Do the bounded thing.", expected_prev_revision=0,
        )

        real_resolve = launcher.resolve_execution_authorization
        calls = {"n": 0}

        def resolve_then_mutate_state(dev_conn, **kwargs):
            calls["n"] += 1
            result = real_resolve(dev_conn, **kwargs)
            if calls["n"] == 2:
                # Call 1 is build_execution_handoff's own build-time check,
                # BEFORE the packet is fingerprinted -- mutating there would
                # pollute that same build's packet, not simulate a race.
                # Call 2 is launch_execution_handoff's own guarded recheck,
                # AFTER the packet already exists; mutate right after it
                # returns and before this function's own freshness check
                # runs, landing the state change exactly in that gap.
                conn.execute(
                    "UPDATE queue_items SET title='changed after build' WHERE item_num=?",
                    ("WB.1TEST",),
                )
                conn.commit()
            return result

        launcher.resolve_execution_authorization = resolve_then_mutate_state
        try:
            fake = make_fake_executable(tmp, "claude", ECHO_STDIN_SHELL)
            result = launcher.launch_execution_handoff(
                conn, fake, task="WB.1TEST", actor="claude_code", out_dir=tmp,
                directive_text="Do the bounded thing.",
                authorization_revision=row["revision"], dry_run=False,
            )
            check("launch_execution_handoff: a packet gone stale between build and the "
                  "immediate pre-send recheck is refused, not sent",
                  result["launched"] is False and result.get("freshness", {}).get("stale") is True,
                  result)
        finally:
            launcher.resolve_execution_authorization = real_resolve
        conn.close()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_launch_execution_handoff_valid_exact_directive_works_for_both_adapters():
    tmp = tempfile.mkdtemp(prefix="dev_launchex_")
    try:
        db = os.path.join(tmp, "fixture.db")
        conn = make_fixture_db(db)
        cs.init_schema(conn, db_path=db)
        row = cs.publish_event(
            conn, task="WB.1TEST", kind="user_instruction", status="authorized", actor="codex",
            summary="d", body="Execute the exact authorized directive.", expected_prev_revision=0,
        )
        for tool_name in ("claude", "codex"):
            out = os.path.join(tmp, tool_name)
            os.makedirs(out, exist_ok=True)
            fake = make_fake_executable(out, tool_name, ECHO_STDIN_SHELL)
            result = launcher.launch_execution_handoff(
                conn, fake, task="WB.1TEST", actor="claude_code", out_dir=out,
                directive_text="Execute the exact authorized directive.",
                authorization_revision=row["revision"], tool=tool_name, dry_run=False,
            )
            check(f"{tool_name}: valid exact directive dispatches successfully via the guarded path",
                  result["launched"] is True
                  and "Execute the exact authorized directive." in result["stdout"],
                  result)
            check(f"{tool_name}: completion_status stays transport-only even for a real, valid dispatch",
                  result["completion_status"] == "transport_only_not_verified", result)
        conn.close()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_cli_handoff_execute_requires_directive_and_authorization():
    tmp = tempfile.mkdtemp(prefix="dev_launchex_")
    try:
        db = os.path.join(tmp, "fixture.db")
        conn = make_fixture_db(db)
        cs.init_schema(conn, db_path=db)
        conn.close()

        def run(*args):
            return subprocess.run(
                [sys.executable, "-m", "tools.development.cli", "--db", db, *args],
                cwd=REPO_ROOT, capture_output=True, text=True,
            )

        p = run("handoff", "WB.1TEST", "claude", "--actor", "claude_code",
                 "--out", tmp, "--execute")
        check("cli handoff --execute with no directive/authorization: refused (exit 2)",
              p.returncode == 2 and "BLOCKED" in p.stderr, p.stdout + p.stderr)

        directive_file = os.path.join(tmp, "directive.txt")
        with open(directive_file, "w") as f:
            f.write("Execute the bounded prerequisite stage now.")

        p2 = run("handoff", "WB.1TEST", "claude", "--actor", "claude_code",
                  "--out", tmp, "--execute", "--directive-file", directive_file,
                  "--authorization-revision", "99")
        check("cli handoff --execute with unresolvable authorization revision: refused (exit 2)",
              p2.returncode == 2 and "BLOCKED" in p2.stderr, p2.stdout + p2.stderr)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def run():
    test_resolve_execution_authorization_rejects_missing()
    test_resolve_execution_authorization_rejects_wrong_kind()
    test_resolve_execution_authorization_rejects_hash_mismatch()
    test_resolve_execution_authorization_rejects_body_mismatch()
    test_resolve_execution_authorization_rejects_stale_superseded()
    test_resolve_execution_authorization_accepts_current_valid()
    test_resolve_execution_authorization_exact_match_ignores_surrounding_whitespace_only()
    test_build_execution_handoff_rejects_empty_directive()
    test_execution_payload_orders_directive_before_reference_context()
    test_both_adapters_receive_execution_payload_verbatim_on_stdin()
    test_context_only_handoff_carries_no_directive_or_authorization()
    test_clarification_exit0_is_not_reported_as_completed()
    test_execution_dispatch_flips_clarification_to_executed_when_authorized()
    test_launch_execution_handoff_rejects_wrong_body_before_invoking_child()
    test_launch_execution_handoff_rechecks_authorization_immediately_before_send()
    test_launch_execution_handoff_rechecks_freshness_immediately_before_send()
    test_launch_execution_handoff_valid_exact_directive_works_for_both_adapters()
    test_cli_handoff_execute_requires_directive_and_authorization()

    for r in results:
        print(r)
    failed = [r for r in results if ": FAIL" in r]
    print(f"\n{len(results) - len(failed)}/{len(results)} passed.")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    run()
