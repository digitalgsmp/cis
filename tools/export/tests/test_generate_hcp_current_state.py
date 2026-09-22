#!/usr/bin/env python3
"""test_generate_hcp_current_state.py — CARD_02_REVIEW_CORRECTION.md and
CARD_02_REVIEW_CORRECTION_R2.md (queue 4.29) behavioral tests proving
generate_hcp.py no longer independently derives current-state conclusions
that could diverge from tools/state/recovery_packet.py's.

R1 scope: DB-derived current-task/next-action/blocker/queue-order narrative
(HCP_00/01/04/05) is gone, replaced by a pointer to the recovery packet,
while durable/historical content is preserved.

R2 scope: HCP_01's "## Current System State" heading and its Advisor
Gateways table's "Status" column presented *static config* (agents_static.
yaml's hand-maintained, dated "Running -- verified 2026-07-07" text) under
live-sounding headings/columns -- a second class of competing current-state
claim distinct from R1's (config-as-live-status, not DB-as-live-status).
Fixed by renaming the heading, adding an explicit non-live disclaimer +
recovery-packet pointer, and removing the Status column entirely.

Approaches used:
- Synthetic-input tests render HCP_00/01/05 directly with two scenarios that
  differ only in which item is "current" (IN_PROGRESS/PENDING/ACTIVE), and
  prove the rendered current-state sections are byte-identical between them
  (mutable current-state can no longer leak into the text at all) while
  historical/settled content still renders.
- Real-spine tests run query_spine() + the renderers against the actual
  production DB (read-only) and prove specific live "current" rows (ACTIVE
  blocker, IN_PROGRESS/PENDING next_actions) are provably absent from the
  generated HCP text, while their RESOLVED/COMPLETE counterparts still
  appear as history.

Run:
    python3 tools/export/tests/test_generate_hcp_current_state.py
"""
import copy
import hashlib
import os
import sqlite3
import sys

REPO_ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "..")
sys.path.insert(0, os.path.join(REPO_ROOT, "tools", "export"))
sys.path.insert(0, os.path.join(REPO_ROOT, "tools", "state"))
import generate_hcp as ghcp  # noqa: E402
import canonical_state as cs  # noqa: E402
import recovery_packet as rp  # noqa: E402

PROD_DB = os.environ.get("CIS_SPINE_PATH", os.path.join(REPO_ROOT, "data", "cis_memory.db"))

# CARD_01_verification_PASS.json's reviewed hash for the actual canonical
# read-model logic file. Requirement 6: this card must not modify it without
# an independently justified hard defect.
#
# CARD 04 correction round (queue 4.32, dev_continuity_events id=34/35,
# discovery revision 10: "Packet-only external-advisor acceptance check
# overclaims coverage") updated this pin deliberately: canonical_state.py
# gained current_focus/active_blockers so a truncated recovery packet still
# lets a fresh reader identify the current task (4.32) and its OPEN status.
# See data/agent_handoffs/WB-RECOVERY-04-recovery-drill-closeout/
# correction-R1/completion.json for the justification and diff.
CARD_01_REVIEWED_CANONICAL_STATE_SHA256 = (
    "8320e956fdcff11b12faeb79e1cb62e611079fff33bf0fa2a4521cd9d39ac8af"
)
# recovery_packet.py's hash as accepted (untouched) by CARD_02_REVIEW_CORRECTION.md
# (R1) and required to stay untouched by CARD_02_REVIEW_CORRECTION_R2.md.
#
# CARD 04 (queue 4.32) updated this pin deliberately, twice:
# 1. get_workbench_state() gained port_identity (tools/development/
#    process_identity.py), resolving the BEFORE_STAGE_CLOSEOUT discovery
#    from Card 03 verification (host killed the cis-pipeline container's
#    main process, mistaking it for a standalone dev Flask process on this
#    same port). See .../WB-RECOVERY-04-recovery-drill-closeout/evidence.md.
# 2. The Card 04 correction round (discovery revision 10, same task) added
#    current_focus/active_blockers passthrough so a packet-only reader can
#    identify 4.32 even when queue_focus is truncated. See
#    .../WB-RECOVERY-04-recovery-drill-closeout/correction-R1/completion.json.
R1_REVIEWED_RECOVERY_PACKET_SHA256 = (
    "c0f9efebc9bcaf134ff953453f5c79c9f0ac6c1730e4a6e15dd2e557e449a83d"
)

results = []


def check(label, cond, detail=""):
    if cond:
        results.append(f"{label}: PASS")
    else:
        results.append(f"{label}: FAIL — {detail}")


def load_static():
    hcp_static = ghcp.load_yaml(os.path.join(REPO_ROOT, "config", "hcp_static.yaml"))
    agents_static = ghcp.load_yaml(os.path.join(REPO_ROOT, "config", "agents_static.yaml"))
    return hcp_static, agents_static


def base_scenario():
    """Minimal synthetic query_spine()-shaped data: one resolved/complete
    item per table (kept as history) and no current item yet -- callers add
    a distinct "current" item per scenario."""
    return {
        "decisions": [],
        "questions": [
            {"id": "Q-HIST", "question": "a settled question", "status": "RESOLVED",
             "resolution": "answered", "opened_at": "2026-01-01"},
        ],
        "actions": [
            {"id": "NA-HIST", "description": "a completed action", "status": "COMPLETE",
             "tier": "1", "created_at": "2026-01-01"},
        ],
        "blockers": [
            {"id": "BLK-HIST", "description": "a resolved blocker", "status": "RESOLVED",
             "created_at": "2026-01-01"},
        ],
        "build_plan_nodes": [
            {"id": 1, "node_label": "Historical Node", "status": "COMPLETE", "tier": "1",
             "sequence": 1, "unmet_hard_deps": 0},
        ],
        "row_counts": {"workflow_runs": 0, "deliberation_rounds": 0, "project_decisions": 0,
                        "open_questions": 1, "next_actions": 1, "active_blockers": 1},
        "build_state": {"build_phase": "test phase", "current_direction": "test direction"},
    }


def scenario_with_current(marker):
    """A scenario whose only difference from another marker's scenario is
    which distinct 'current' item is IN_PROGRESS/PENDING/ACTIVE."""
    data = base_scenario()
    data["actions"] = data["actions"] + [
        {"id": f"NA-CUR-{marker}", "description": f"CURRENT-ACTION-MARKER-{marker}",
         "status": "IN_PROGRESS", "tier": "5", "created_at": "2026-09-01"},
    ]
    data["blockers"] = data["blockers"] + [
        {"id": f"BLK-CUR-{marker}", "description": f"CURRENT-BLOCKER-MARKER-{marker}",
         "status": "ACTIVE", "created_at": "2026-09-01"},
    ]
    data["build_plan_nodes"] = data["build_plan_nodes"] + [
        {"id": 2, "node_label": f"CURRENT-NODE-MARKER-{marker}", "status": "IN_PROGRESS",
         "tier": "5", "sequence": 2, "unmet_hard_deps": 0},
    ]
    return data


def render_all(hcp_static, agents_static, data, state_revision="deadbeef00000000"):
    stamp = ghcp.generation_stamp("test")
    hcp00 = ghcp.render_hcp_00(stamp, hcp_static, agents_static, "abc1234",
                                data["actions"], state_revision=state_revision)
    hcp01 = ghcp.render_hcp_01(stamp, hcp_static, agents_static, data["decisions"],
                                data["questions"], data["actions"], data["blockers"],
                                [], None, data["row_counts"], data["build_state"],
                                data["build_plan_nodes"], state_revision=state_revision)
    hcp05 = ghcp.render_hcp_05(stamp, hcp_static, agents_static, data["actions"],
                                data["blockers"], data["build_plan_nodes"])
    return hcp00, hcp01, hcp05


def test_current_state_invariant_to_which_item_is_current():
    """Requirement 1 & 2: two scenarios differing ONLY in which item is
    IN_PROGRESS/PENDING/ACTIVE must render byte-identical current-state
    sections -- neither scenario's marker may leak into the output, so no
    stale/dormant/current mutable-table content can ever cause HCP to state
    a 'current next action' that could diverge from the recovery packet
    (which HCP no longer competes with at all)."""
    hcp_static, agents_static = load_static()
    data_a = scenario_with_current("A")
    data_b = scenario_with_current("B")

    hcp00_a, hcp01_a, hcp05_a = render_all(hcp_static, agents_static, data_a)
    hcp00_b, hcp01_b, hcp05_b = render_all(hcp_static, agents_static, data_b)

    check("HCP_00 output is identical regardless of which item is current",
          hcp00_a == hcp00_b, "HCP_00 differed between scenario A and B")
    check("HCP_01 output is identical regardless of which item is current",
          hcp01_a == hcp01_b, "HCP_01 differed between scenario A and B")
    check("HCP_05 output is identical regardless of which item is current",
          hcp05_a == hcp05_b, "HCP_05 differed between scenario A and B")

    for marker, hcp01, hcp05 in (("A", hcp01_a, hcp05_a), ("B", hcp01_b, hcp05_b)):
        leaked = (f"CURRENT-ACTION-MARKER-{marker}" in hcp01
                  or f"CURRENT-BLOCKER-MARKER-{marker}" in hcp01
                  or f"CURRENT-NODE-MARKER-{marker}" in hcp01
                  or f"CURRENT-ACTION-MARKER-{marker}" in hcp05
                  or f"CURRENT-NODE-MARKER-{marker}" in hcp05)
        check(f"scenario {marker}'s current-item marker text does not leak into HCP_01/HCP_05",
              not leaked, f"marker for scenario {marker} was found in generated output")

    for hcp01 in (hcp01_a, hcp01_b):
        check("historical/settled item ('a resolved blocker') still renders in HCP_01",
              "a resolved blocker" in hcp01, "history dropped, not just current-state")
        check("historical/settled question ('a settled question') still renders in HCP_01",
              "a settled question" in hcp01, "history dropped, not just current-state")


def test_forbidden_legacy_current_state_headings_absent():
    hcp_static, agents_static = load_static()
    data = scenario_with_current("X")
    hcp00, hcp01, hcp05 = render_all(hcp_static, agents_static, data)

    forbidden = [
        "## Next Safe Action", "## Execution Order", "**Approved build order:**",
        "## Approved Build Order", "## Current Objective", "## Current Status",
    ]
    for marker in forbidden:
        check(f"forbidden legacy current-state heading {marker!r} does not appear in HCP_00/01/05",
              marker not in hcp00 and marker not in hcp01 and marker not in hcp05,
              f"{marker!r} still present")

    check("HCP_00 points at the recovery packet for current operational state",
          "tools/state/recovery_packet.py" in hcp00, hcp00)
    check("HCP_01 points at the recovery packet for current operational state",
          "tools/state/recovery_packet.py" in hcp01, "pointer missing from HCP_01")
    check("HCP_05 points at the recovery packet for current next action",
          "tools/state/recovery_packet.py" in hcp05, "pointer missing from HCP_05")


def test_static_priority_next_actions_no_longer_rendered():
    """The hcp_05.next_actions/open_unverified-style static-config current-
    state list must not be rendered as current-state text anymore."""
    hcp_static, agents_static = load_static()
    static_next_actions = hcp_static["hcp_05"].get("next_actions", [])
    check("fixture assumption holds: config/hcp_static.yaml still has a "
          "hand-maintained hcp_05.next_actions list to guard against",
          len(static_next_actions) > 0, "no next_actions in static config -- test no longer meaningful")

    data = scenario_with_current("Y")
    _, _, hcp05 = render_all(hcp_static, agents_static, data)
    for item in static_next_actions:
        check(f"static hcp_05.next_actions item not rendered as current state: {item[:40]!r}...",
              item not in hcp05, "static config current-state text leaked into HCP_05")


def test_hcp00_and_hcp01_cite_the_same_state_revision():
    """Requirement 3: HCP's current-state pointer must cite the same
    revision the recovery packet/canonical_state would report for identical
    DB content -- proven by passing canonical_state's own live revision
    through and asserting it's the exact string embedded in both files."""
    hcp_static, agents_static = load_static()
    if not os.path.exists(PROD_DB):
        check("revision-citation test skipped (no production DB present in this environment)", True)
        return
    conn = sqlite3.connect(PROD_DB)
    conn.row_factory = sqlite3.Row
    try:
        live_revision = cs.compute_state_revision(conn)
    finally:
        conn.close()
    packet_revision = rp.build_recovery_packet(db_path=PROD_DB)["state_revision"]
    check("canonical_state's live revision matches the recovery packet's state_revision",
          live_revision == packet_revision, f"{live_revision} != {packet_revision}")

    data = scenario_with_current("Z")
    hcp00, hcp01, _ = render_all(hcp_static, agents_static, data, state_revision=live_revision)
    check("HCP_00 cites the exact same revision string as the recovery packet",
          f"`{packet_revision}`" in hcp00, hcp00)
    check("HCP_01 cites the exact same revision string as the recovery packet",
          f"`{packet_revision}`" in hcp01, hcp01)


def test_real_spine_current_rows_absent_from_generated_hcp():
    """Cross-check against the real production spine: a live ACTIVE blocker
    and live IN_PROGRESS/PENDING next_actions must not appear in generated
    HCP_01/HCP_05 text, while a live RESOLVED/COMPLETE counterpart does --
    proving in the real system (not just synthetic data) that HCP cannot
    present a different 'current next action' than the recovery packet,
    because it no longer presents one at all."""
    if not os.path.exists(PROD_DB):
        check("real-spine current-state test skipped (no production DB present)", True)
        return
    hcp_static, agents_static = load_static()
    (decisions, questions, actions, blockers, runs, latest_run, row_counts,
     build_state, eric_gate, build_plan_nodes, dev_pivot) = ghcp.query_spine(PROD_DB)

    conn = sqlite3.connect(PROD_DB)
    conn.row_factory = sqlite3.Row
    try:
        revision = cs.compute_state_revision(conn)
    finally:
        conn.close()

    stamp = ghcp.generation_stamp("test")
    hcp01 = ghcp.render_hcp_01(stamp, hcp_static, agents_static, decisions, questions,
                                actions, blockers, runs, latest_run, row_counts, build_state,
                                build_plan_nodes, state_revision=revision)
    hcp05 = ghcp.render_hcp_05(stamp, hcp_static, agents_static, actions, blockers, build_plan_nodes)

    active_blockers = [b for b in blockers if b["status"] == "ACTIVE"]
    resolved_blockers = [b for b in blockers if b["status"] != "ACTIVE"]
    current_actions = [a for a in actions if a["status"] in ("PENDING", "IN_PROGRESS")]

    for b in active_blockers:
        snippet = b["description"][:60]
        check(f"live ACTIVE blocker [{b['id']}] is not rendered as current in HCP_01",
              snippet not in hcp01, f"{snippet!r} found in HCP_01")
    if resolved_blockers:
        snippet = resolved_blockers[0]["description"][:60]
        check("a live resolved blocker still renders as history in HCP_01",
              snippet in hcp01, f"{snippet!r} missing from HCP_01 history")

    for a in current_actions:
        snippet = a["description"][:60]
        check(f"live current (PENDING/IN_PROGRESS) action [{a['id']}] is not rendered "
              "as current-next-action text in HCP_01 or HCP_05",
              snippet not in hcp01 and snippet not in hcp05, f"{snippet!r} found")


def test_durable_sections_still_generate():
    """Requirement 4: durable mission/architecture/decisions/protocol/
    reference material must still render (this card must not have deleted
    it while removing current-state narrative)."""
    hcp_static, agents_static = load_static()
    data = scenario_with_current("D")
    hcp00, hcp01, hcp05 = render_all(hcp_static, agents_static, data)

    check("HCP_00 still carries the architecture-change announcement",
          "HERMES_CIS_BRIEFING_PATH is RETIRED" in hcp00, "durable architecture note missing")
    check("HCP_01 still carries its durable tier/architecture blurb",
          hcp_static["hcp_01"]["context_architecture_blurb"].strip().splitlines()[0] in hcp01,
          "durable architecture blurb missing")
    check("HCP_01 still carries the durable 'Do Not Start Yet' list",
          "## Do Not Start Yet" in hcp01, "durable do-not-start section missing")
    check("HCP_01 still carries durable Accepted Limitations",
          "Accepted Limitations" in "\n".join(hcp_static["hcp_01"]["accepted_limitations"].splitlines()[:1])
          or hcp_static["hcp_01"]["accepted_limitations"].strip().splitlines()[0] in hcp01,
          "accepted limitations missing")
    check("HCP_05 still carries durable Known Limitations",
          "## Known Limitations" in hcp05 or hcp_static["hcp_05"]["known_limitations_header"].strip() in hcp05,
          "known limitations header missing")
    check("HCP_05 still carries the durable Do Not Start list",
          "Do NOT start:" in hcp05, "do-not-start framing missing")


def test_canonical_state_py_unmodified():
    """Requirement 6: this correction must not modify canonical_state.py
    without an independently justified hard defect -- none was found or
    claimed, so its hash must still match Card 01's reviewed pin."""
    path = os.path.join(REPO_ROOT, "tools", "state", "canonical_state.py")
    live_hash = hashlib.sha256(open(path, "rb").read()).hexdigest()
    check("tools/state/canonical_state.py sha256 still matches Card 01's reviewed pin",
          live_hash == CARD_01_REVIEWED_CANONICAL_STATE_SHA256,
          f"live={live_hash} reviewed={CARD_01_REVIEWED_CANONICAL_STATE_SHA256}")


# ── R2: static-config-as-live-status (HCP_01 Reference System Configuration) ──

def test_r2_hcp01_no_current_system_state_heading():
    hcp_static, agents_static = load_static()
    data = scenario_with_current("R2A")
    _, hcp01, _ = render_all(hcp_static, agents_static, data)
    check("HCP_01 no longer contains the live-sounding '## Current System State' heading",
          "## Current System State" not in hcp01, "heading still present")
    check("HCP_01 uses the explicitly non-live 'Reference System Configuration' heading instead",
          "## Reference System Configuration" in hcp01, "replacement heading missing")


def test_r2_hcp01_gateway_table_has_no_status_column():
    hcp_static, agents_static = load_static()
    data = scenario_with_current("R2B")
    _, hcp01, _ = render_all(hcp_static, agents_static, data)
    idx = hcp01.find("### Advisor Gateways")
    check("HCP_01 contains an Advisor Gateways section", idx != -1, "section missing")
    table_slice = hcp01[idx:idx + 2000]
    check("Advisor Gateways table header has no 'Status' column",
          "Status" not in table_slice.split("\n\n")[0],
          "a Status column header is still present in the gateway table block")
    for gw in agents_static.get("gateways", []):
        status_value = gw.get("status", "")
        if status_value:
            check(f"gateway config status text {status_value[:40]!r}... is not rendered anywhere in HCP_01",
                  status_value not in hcp01, "static gateway status text leaked into HCP_01")


def test_r2_hcp01_points_to_recovery_packet_for_live_health():
    hcp_static, agents_static = load_static()
    data = scenario_with_current("R2C")
    _, hcp01, _ = render_all(hcp_static, agents_static, data)
    check("HCP_01 explicitly points to the recovery packet for live gateway/runtime health",
          "Live service/gateway/infrastructure health is reported only by" in hcp01
          and "tools/state/recovery_packet.py" in hcp01,
          "no explicit live-health pointer found near Reference System Configuration")
    check("HCP_01 explicitly labels the section as static, not observed",
          "not observed runtime status" in hcp01, "no explicit non-live disclaimer found")


def test_r2_hcp01_invariant_to_gateway_status_config_changes():
    """Requirement 4: changing agents_static.yaml's gateway status values
    must not change HCP's live-health conclusion -- because HCP renders no
    live-health conclusion for gateways at all anymore."""
    hcp_static, agents_static_a = load_static()
    agents_static_b = copy.deepcopy(agents_static_a)
    for gw in agents_static_b.get("gateways", []):
        gw["status"] = f"DELIBERATELY-DIFFERENT-STATUS-{gw.get('port')}"

    data = scenario_with_current("R2D")
    _, hcp01_a, _ = render_all(hcp_static, agents_static_a, data)
    _, hcp01_b, _ = render_all(hcp_static, agents_static_b, data)
    check("HCP_01's Reference System Configuration section is unaffected by "
          "changing agents_static.yaml gateway status values",
          hcp01_a == hcp01_b, "HCP_01 output changed when only gateway 'status' config changed")


def test_r2_durable_gateway_configuration_still_renders():
    """Requirement 5: durable gateway architecture/configuration (labels,
    ports, model/profile mappings) must still render -- only the live-
    sounding Status column was removed, not the architecture."""
    hcp_static, agents_static = load_static()
    data = scenario_with_current("R2E")
    _, hcp01, _ = render_all(hcp_static, agents_static, data)
    for gw in agents_static.get("gateways", []):
        check(f"gateway {gw['label']}'s durable config (port {gw['port']}, model {gw['model']}) still renders",
              str(gw["port"]) in hcp01 and gw["model"] in hcp01 and gw["label"] in hcp01,
              "durable gateway config missing from HCP_01")


def test_r2_recovery_packet_py_unmodified():
    """Requirement 7: recovery_packet.py must remain unchanged by this
    correction, same as canonical_state.py."""
    path = os.path.join(REPO_ROOT, "tools", "state", "recovery_packet.py")
    live_hash = hashlib.sha256(open(path, "rb").read()).hexdigest()
    check("tools/state/recovery_packet.py sha256 still matches its R1-accepted pin",
          live_hash == R1_REVIEWED_RECOVERY_PACKET_SHA256,
          f"live={live_hash} reviewed={R1_REVIEWED_RECOVERY_PACKET_SHA256}")


def run():
    test_current_state_invariant_to_which_item_is_current()
    test_forbidden_legacy_current_state_headings_absent()
    test_static_priority_next_actions_no_longer_rendered()
    test_hcp00_and_hcp01_cite_the_same_state_revision()
    test_real_spine_current_rows_absent_from_generated_hcp()
    test_durable_sections_still_generate()
    test_canonical_state_py_unmodified()

    test_r2_hcp01_no_current_system_state_heading()
    test_r2_hcp01_gateway_table_has_no_status_column()
    test_r2_hcp01_points_to_recovery_packet_for_live_health()
    test_r2_hcp01_invariant_to_gateway_status_config_changes()
    test_r2_durable_gateway_configuration_still_renders()
    test_r2_recovery_packet_py_unmodified()

    for r in results:
        print(r)
    failed = [r for r in results if ": FAIL" in r]
    print(f"\n{len(results) - len(failed)}/{len(results)} passed.")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    run()
