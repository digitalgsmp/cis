#!/usr/bin/env python3
"""test_recovery_packet.py — CARD 02 (queue 4.29) behavioral tests for
tools/state/recovery_packet.py.

Runs entirely against scratch temp SQLite databases built with the same
minimal schema subset as test_canonical_state.py (imported from it, not
duplicated) -- never against production for anything that could mutate.

Run:
    python3 tools/state/tests/test_recovery_packet.py
"""
import json
import os
import shutil
import sys

REPO_ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "..")
sys.path.insert(0, os.path.join(REPO_ROOT, "tools", "state"))
sys.path.insert(0, os.path.dirname(__file__))
import canonical_state as cs  # noqa: E402
import recovery_packet as rp  # noqa: E402
from test_canonical_state import make_scratch_db, table_counts  # noqa: E402

results = []


def check(label, cond, detail=""):
    if cond:
        results.append(f"{label}: PASS")
    else:
        results.append(f"{label}: FAIL — {detail}")


def test_packet_changes_with_authoritative_state():
    tmp, path, conn = make_scratch_db()
    try:
        before = rp.build_recovery_packet(db_path=path)
        conn.execute(
            "INSERT INTO queue_items (item_num, tier, title, body_md, form, "
            "need_status, source_line, source_sha) VALUES "
            "('9.1', 9, 'test item', '### 9.1 test item', 'heading', 'OPEN', 1, 'x')"
        )
        conn.commit()
        after = rp.build_recovery_packet(db_path=path)
        check("packet's state_revision changes when authoritative DB state changes",
              before["state_revision"] != after["state_revision"],
              f"before={before['state_revision']} after={after['state_revision']}")
        check("packet's queue_focus reflects the new row",
              after["queue_focus"] != before["queue_focus"], "queue_focus did not change")
    finally:
        conn.close()
        shutil.rmtree(tmp, ignore_errors=True)


def test_stale_revision_marker_detectable():
    tmp, path, conn = make_scratch_db()
    try:
        declared = rp.build_recovery_packet(db_path=path)["state_revision"]
        conn.execute(
            "INSERT INTO project_decisions (id, label, decision, decided_at) "
            "VALUES ('D1', 'test', 'test decision', datetime('now'))"
        )
        conn.commit()
        current = rp.build_recovery_packet(db_path=path)["state_revision"]
        check("a declared packet revision no longer matching current state is detectable as stale",
              declared != current, f"declared={declared} current={current}")
    finally:
        conn.close()
        shutil.rmtree(tmp, ignore_errors=True)


def test_generation_succeeds_with_pipeline_and_gateways_down():
    """No gateway/Braingate/Card Factory/Card Runner process is running in
    this test environment -- exactly the condition this generator must
    tolerate. Building the packet must not raise, and every observed
    health flag must come back as a plain bool, never an exception path."""
    tmp, path, conn = make_scratch_db()
    try:
        try:
            packet = rp.build_recovery_packet(db_path=path)
            raised = None
        except Exception as e:  # noqa: BLE001
            packet, raised = None, e
        check("full packet builds successfully with no pipeline/gateway processes running",
              raised is None, str(raised))
        if packet:
            gw = packet["observed_runtime_health"]["gateways"]
            check("every gateway health observation is a plain bool, not an error",
                  all(isinstance(v["listening"], bool) for v in gw.values()), gw)
            check("workbench_state.listening is a plain bool, not an error",
                  isinstance(packet["workbench_state"]["listening"], bool),
                  packet["workbench_state"])
    finally:
        conn.close()
        shutil.rmtree(tmp, ignore_errors=True)


def test_workbench_port_identity_present_and_never_raises():
    """CARD 04 / queue 4.32 discovery: workbench_state must carry
    host-verifiable process/container identity evidence for its port, and
    a failure inside the identity check must degrade to an error field
    rather than ever taking down packet generation (matching every other
    observed-health check in this module)."""
    tmp, path, conn = make_scratch_db()
    try:
        packet = rp.build_recovery_packet(db_path=path)
        pident = packet["workbench_state"]["port_identity"]
        check("workbench_state carries a port_identity block",
              isinstance(pident, dict) and pident.get("port") == rp.WORKBENCH_PORT, pident)
        check("port_identity reports listening as a plain bool or None, never missing",
              "listening" in pident, pident)

        def boom(port):
            raise RuntimeError("simulated ss/docker failure")
        orig = rp.pident.classify_port
        rp.pident.classify_port = boom
        try:
            packet2 = rp.build_recovery_packet(db_path=path)
            raised = None
        except Exception as e:  # noqa: BLE001
            packet2, raised = None, e
        finally:
            rp.pident.classify_port = orig
        check("a failing identity check degrades to an error field, never crashes packet generation",
              raised is None and packet2 is not None
              and packet2["workbench_state"]["port_identity"].get("error"),
              str(raised) if raised else packet2["workbench_state"]["port_identity"])
    finally:
        conn.close()
        shutil.rmtree(tmp, ignore_errors=True)


def test_focused_packet_shares_global_revision_with_full_packet():
    tmp, path, conn = make_scratch_db()
    try:
        full = rp.build_recovery_packet(db_path=path)
        for issue in sorted(rp.ISSUE_AREAS):
            focused = rp.build_recovery_packet(issue=issue, db_path=path)
            check(f"focused packet ({issue}) carries the same state_revision as the full packet",
                  focused["state_revision"] == full["state_revision"],
                  f"full={full['state_revision']} {issue}={focused['state_revision']}")
            check(f"focused packet ({issue}) still carries global freshness/authority context",
                  focused["source_table_freshness"] == full["source_table_freshness"]
                  and focused["authority_statement"] == full["authority_statement"],
                  "focused packet dropped global context")
    finally:
        conn.close()
        shutil.rmtree(tmp, ignore_errors=True)


def test_unknown_issue_area_rejected():
    tmp, path, conn = make_scratch_db()
    try:
        try:
            rp.build_recovery_packet(issue="not_a_real_area", db_path=path)
            raised = False
        except ValueError:
            raised = True
        check("an unrecognized issue area is rejected rather than silently producing a global packet",
              raised, "no ValueError raised")
    finally:
        conn.close()
        shutil.rmtree(tmp, ignore_errors=True)


def test_packet_generation_does_not_mutate_authoritative_state():
    tmp, path, conn = make_scratch_db()
    try:
        conn.execute(
            "INSERT INTO queue_items (item_num, tier, title, body_md, form, "
            "need_status, source_line, source_sha) VALUES "
            "('9.2', 9, 'mutation guard', '### 9.2 x', 'heading', 'OPEN', 1, 'x')"
        )
        conn.commit()
        before_counts = table_counts(conn)
        before_rev = cs.compute_state_revision(conn)

        rp.build_recovery_packet(db_path=path)
        rp.build_recovery_packet(issue="queue", db_path=path)

        after_counts = table_counts(conn)
        after_rev = cs.compute_state_revision(conn)
        check("no authority table row count changed after generating full + focused packets",
              before_counts == after_counts, f"before={before_counts} after={after_counts}")
        check("state revision is unchanged by the act of generating a packet",
              before_rev == after_rev, f"before={before_rev} after={after_rev}")
    finally:
        conn.close()
        shutil.rmtree(tmp, ignore_errors=True)


def test_output_is_bounded_for_context_window_copying():
    tmp, path, conn = make_scratch_db()
    try:
        for i in range(60):
            conn.execute(
                "INSERT INTO queue_items (item_num, tier, title, body_md, form, "
                "need_status, source_line, source_sha) VALUES "
                f"('9.{i}', 9, 'bulk item {i}', '### 9.{i} x', 'heading', 'OPEN', 1, 'x')"
            )
        conn.commit()
        packet = rp.build_recovery_packet(db_path=path)
        open_items = packet["queue_focus"]["open_items"]
        check("a section with more than the cap is wrapped with an explicit truncation count "
              "instead of being emitted unbounded",
              isinstance(open_items, dict) and open_items.get("truncated") == 60 - rp._CAP,
              open_items if not isinstance(open_items, dict) else open_items.get("truncated"))
        check("the capped section keeps exactly _CAP items, not the full 60",
              isinstance(open_items, dict) and len(open_items["items"]) == rp._CAP,
              open_items)
        size = len(json.dumps(packet))
        check("serialized packet stays well under a sane context-window budget (200KB) even with 60 rows",
              size < 200_000, f"{size} bytes")
    finally:
        conn.close()
        shutil.rmtree(tmp, ignore_errors=True)


def test_end_to_end_against_real_spine_readonly():
    """Smoke test against the real production spine, read-only, to prove
    this actually works against live data shaped like the real schema (the
    scratch tests above prove the logic; this proves it isn't only correct
    against a toy schema)."""
    prod_db = os.environ.get("CIS_SPINE_PATH", os.path.join(REPO_ROOT, "data", "cis_memory.db"))
    if not os.path.exists(prod_db):
        check("real spine smoke test skipped (no production DB present in this environment)", True)
        return
    try:
        packet = rp.build_recovery_packet(db_path=prod_db)
        raised = None
    except Exception as e:  # noqa: BLE001
        packet, raised = None, e
    check("full packet builds successfully against the real production spine",
          raised is None, str(raised))
    if packet:
        required = {
            "packet_kind", "generated_at", "state_revision", "authority_statement",
            "recovery_instructions", "project_identity", "source_table_freshness",
            "generated_artifact_freshness", "dirty_git_state", "workbench_state",
            "relevant_paths",
        }
        check("required fields are present in the real-spine packet",
              required.issubset(packet.keys()), sorted(required - packet.keys()))


def test_packet_only_reader_identifies_current_focus_and_return_boundary():
    """Card 04 R1 correction: a fresh advisor reading ONLY the generated
    packet (never the DB, never queue prose elsewhere) must be able to tell
    (1) the current authoritative pointer, (2) that a specific recent task
    is OPEN, and (3) the recorded no-automatic-resumption boundary for that
    task -- all from real DB-backed records the packet carries, not from
    any inference this module performs."""
    tmp, path, conn = make_scratch_db()
    try:
        conn.execute(
            "INSERT INTO queue_items (item_num, tier, title, body_md, form, "
            "need_status, source_line, source_sha) VALUES "
            "('WB.1', 0, 'workbench priority', '### WB.1 workbench priority', "
            "'heading', 'OPEN', 1, 'x')"
        )
        conn.execute(
            "INSERT INTO queue_items (item_num, tier, title, body_md, form, "
            "need_status, source_line, source_sha) VALUES "
            "('4.32', 4, 'recovery drill', '### 4.32 recovery drill\\n\\n"
            "**Need: OPEN.**\\n\\nReturn point: after this closes, resuming "
            "feature work is not automatic.', 'heading', 'OPEN', 2, 'x')"
        )
        conn.execute(
            "INSERT INTO project_state (key, value, source, created_at) VALUES "
            "('current_queue_item', 'WB.1', 'manual', '2026-09-17T13:39:11Z')"
        )
        conn.execute(
            "INSERT INTO dev_continuity_events (task, revision, kind, status, actor, "
            "summary, body, created_at) VALUES ('4.32', 1, 'user_instruction', "
            "'authorized', 'codex', 'work the recovery drill', 'directive', "
            "'2026-09-22 15:00:00')"
        )
        conn.commit()
        packet = rp.build_recovery_packet(db_path=path)

        pointer = packet["current_focus"]["current_queue_item_pointer"]
        check("packet-only: current pointer identifiable as WB.1 from current_focus alone",
              pointer is not None and pointer["value"] == "WB.1", pointer)

        item_4_32 = packet["current_focus"]["recent_task_queue_items"].get("4.32")
        check("packet-only: 4.32 identifiable as OPEN from current_focus.recent_task_queue_items, "
              "surfaced purely by its own recent activity, not by being the pointer",
              item_4_32 is not None and item_4_32["need_status"] == "OPEN", item_4_32)
        check("packet-only: the recorded no-automatic-feature-resumption boundary is present "
              "verbatim in 4.32's own body_md, not paraphrased or inferred by this module",
              item_4_32 is not None and "not automatic" in item_4_32["body_md"], item_4_32)
    finally:
        conn.close()
        shutil.rmtree(tmp, ignore_errors=True)


def test_current_focus_and_active_blockers_always_present_regardless_of_issue_focus():
    tmp, path, conn = make_scratch_db()
    try:
        conn.execute(
            "INSERT INTO active_blockers (id, description, status, created_at) "
            "VALUES ('B1', 'test blocker', 'ACTIVE', datetime('now'))"
        )
        conn.commit()
        for issue in (None, "workbench", "database"):
            packet = rp.build_recovery_packet(issue=issue, db_path=path)
            check(f"current_focus present regardless of issue_focus={issue!r}",
                  "current_focus" in packet, packet.keys())
            check(f"active_blockers present regardless of issue_focus={issue!r}, includes the fixture row",
                  "active_blockers" in packet
                  and any(b["id"] == "B1" for b in packet["active_blockers"]),
                  packet.get("active_blockers"))
    finally:
        conn.close()
        shutil.rmtree(tmp, ignore_errors=True)


def run():
    test_packet_changes_with_authoritative_state()
    test_stale_revision_marker_detectable()
    test_generation_succeeds_with_pipeline_and_gateways_down()
    test_workbench_port_identity_present_and_never_raises()
    test_focused_packet_shares_global_revision_with_full_packet()
    test_unknown_issue_area_rejected()
    test_packet_generation_does_not_mutate_authoritative_state()
    test_output_is_bounded_for_context_window_copying()
    test_end_to_end_against_real_spine_readonly()
    test_packet_only_reader_identifies_current_focus_and_return_boundary()
    test_current_focus_and_active_blockers_always_present_regardless_of_issue_focus()

    for r in results:
        print(r)
    failed = [r for r in results if ": FAIL" in r]
    print(f"\n{len(results) - len(failed)}/{len(results)} passed.")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    run()
