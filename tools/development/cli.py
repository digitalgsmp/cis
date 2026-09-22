#!/usr/bin/env python3
"""cli.py — host CLI for WB.1C development continuity.

    python3 -m tools.development.cli prepare  <task> --actor NAME [--query Q ...] [--kb-id N ...] [--out DIR]
    python3 -m tools.development.cli check     <handoff.json> [--db PATH]
    python3 -m tools.development.cli publish   <task> --kind K --status S --actor NAME --summary S
                                                --expect-revision N [--body B] [--request-id ID]
                                                [--evidence-ref R ...] [--source-ref R ...]
    python3 -m tools.development.cli reconcile <task> --against-revision N --disposition D --note N
                                                --actor NAME --expect-revision N [--request-id ID]
    python3 -m tools.development.cli events    <task>
    python3 -m tools.development.cli import-transcript <task> <session_file.jsonl> --actor NAME
                                                [--select IDX ...]
    python3 -m tools.development.cli discover  <executable_name>
    python3 -m tools.development.cli init-dev-schema --db PATH   # refuses production path
    python3 -m tools.development.cli handoff  <task> {claude|codex} --actor NAME --out DIR
                                                [--query Q ...] [--kb-id N ...] [--execute
                                                --directive-file PATH --authorization-revision N
                                                [--authorization-request-hash H]]
                                                # Dry-run by default: builds and previews a
                                                # CONTEXT-ONLY packet, sends nothing.
                                                # --execute requires BOTH --directive-file (a
                                                # file containing the explicit execution prose)
                                                # and --authorization-revision (the exact
                                                # dev_continuity_events revision, of
                                                # kind='user_instruction', that authorizes this
                                                # send) — re-validated live against the database;
                                                # missing/wrong-kind/hash-mismatched/superseded
                                                # authorization is refused (exit 2), nothing is
                                                # sent. Directive prose renders BEFORE the
                                                # labeled reference packet in what is actually
                                                # sent, via that tool's real CLI contract
                                                # (stdin), never as a positional file path. A
                                                # subprocess launching and returning 0 is
                                                # reported as transport-only (see
                                                # completion_status in the output) — never as
                                                # completed/accepted work.
    python3 -m tools.development.cli discovery-record <task> --actor NAME --summary S
                                                --disposition {RESOLVED_NOW|BEFORE_STAGE_CLOSEOUT|EXPLICITLY_DEFERRED}
                                                --expect-revision N [disposition-specific flags]
    python3 -m tools.development.cli discovery-resolve <task> --discovery-revision N --actor NAME
                                                --resolution-result R --expect-revision N
    python3 -m tools.development.cli discoveries <task> [--all]   # unresolved-only by default
    python3 -m tools.development.cli closeout-check <task>   # exit 0 iff ready_to_close

--db defaults to $CIS_SPINE_PATH or the production spine for READS (prepare,
check, events). Commands that WRITE dev_continuity_* (publish, reconcile,
import-transcript) also default there, but init-dev-schema refuses to create
the schema on that path — so against an unstaged production spine, publish/
reconcile/import-transcript fail fast with NotInitializedError rather than
silently no-op'ing. That failure is the intended behavior until 0039 is
reviewed and deliberately applied.
"""
import argparse
import json
import sys

from . import card_contract
from . import continuity_store as cs
from . import discovery
from . import kb_read  # noqa: F401  (re-exported for callers/tests)
from . import launcher
from . import packet as packet_mod
from . import transcript_import


def _cmd_prepare(a):
    conn = cs.connect(a.db)
    pkt = packet_mod.prepare_packet(
        conn, task=a.task, actor=a.actor, concept_queries=a.query or [],
        kb_ids=a.kb_id or [],
    )
    if a.out:
        path, _ = launcher.build_handoff(
            conn, task=a.task, actor=a.actor, out_dir=a.out,
            concept_queries=a.query or [], kb_ids=a.kb_id or [],
        )
        print(f"wrote {path}")
    print(json.dumps(pkt, indent=2))
    return 0 if pkt.get("ok") else 1


def _cmd_check(a):
    with open(a.handoff, encoding="utf-8") as f:
        handoff = json.load(f)
    conn = cs.connect(a.db)
    fresh = packet_mod.check_freshness(conn, handoff["packet"])
    print(json.dumps(fresh, indent=2))
    return 1 if fresh["stale"] else 0


def _cmd_publish(a):
    conn = cs.connect(a.db)
    try:
        row = cs.publish_event(
            conn, task=a.task, kind=a.kind, status=a.status, actor=a.actor,
            summary=a.summary, body=a.body or "",
            evidence_refs=a.evidence_ref or [], source_refs=a.source_ref or [],
            expected_prev_revision=a.expect_revision, request_id=a.request_id,
        )
    except cs.ContinuityError as e:
        print(f"BLOCKED: {e}", file=sys.stderr)
        return 2
    print(json.dumps(row, indent=2))
    return 0


def _cmd_reconcile(a):
    conn = cs.connect(a.db)
    try:
        row = cs.record_reconciliation(
            conn, task=a.task, actor=a.actor, against_revision=a.against_revision,
            disposition=a.disposition, note=a.note,
            evidence_refs=a.evidence_ref or [], source_refs=a.source_ref or [],
            expected_prev_revision=a.expect_revision, request_id=a.request_id,
        )
    except cs.ContinuityError as e:
        print(f"BLOCKED: {e}", file=sys.stderr)
        return 2
    print(json.dumps(row, indent=2))
    return 0


def _cmd_events(a):
    conn = cs.connect(a.db)
    try:
        rows = cs.list_events(conn, a.task)
    except cs.ContinuityError as e:
        print(f"BLOCKED: {e}", file=sys.stderr)
        return 2
    print(json.dumps(rows, indent=2))
    return 0


def _cmd_import_transcript(a):
    conn = cs.connect(a.db)
    try:
        result = transcript_import.import_transcript(
            conn, task=a.task, session_file=a.session_file, actor=a.actor,
            source=a.source, select=a.select,
        )
    except (cs.ContinuityError, transcript_import.UnsupportedFormatError) as e:
        print(f"BLOCKED: {e}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2))
    return 0


def _cmd_discover(a):
    print(json.dumps(launcher.discover_executable(a.executable), indent=2))
    return 0


def _cmd_discovery_record(a):
    """CARD 3: record one consequential discovered-work item with a
    validated disposition. Malformed/incomplete input is rejected (exit 2),
    never silently accepted."""
    conn = cs.connect(a.db)
    try:
        row = discovery.record_discovery(
            conn, task=a.task, actor=a.actor, summary=a.summary,
            disposition=a.disposition, expected_prev_revision=a.expect_revision,
            request_id=a.request_id, evidence_refs=a.evidence_ref or [],
            source_refs=a.source_ref or [], reason=a.reason, destination=a.destination,
            blocking=a.blocking, trigger=a.trigger, originating_stage=a.originating_stage,
            resolution_result=a.resolution_result, resolution_evidence=a.resolution_evidence,
            note=a.note,
        )
    except (cs.ContinuityError, discovery.DiscoveryValidationError) as e:
        print(f"BLOCKED: {e}", file=sys.stderr)
        return 2
    print(json.dumps(row, indent=2))
    return 0


def _cmd_discovery_resolve(a):
    conn = cs.connect(a.db)
    try:
        row = discovery.resolve_discovery(
            conn, task=a.task, actor=a.actor, discovery_revision=a.discovery_revision,
            resolution_result=a.resolution_result, expected_prev_revision=a.expect_revision,
            request_id=a.request_id, resolution_evidence=a.resolution_evidence,
        )
    except (cs.ContinuityError, discovery.DiscoveryValidationError) as e:
        print(f"BLOCKED: {e}", file=sys.stderr)
        return 2
    print(json.dumps(row, indent=2))
    return 0


def _cmd_discoveries(a):
    """List unresolved discovered work for a task — CARD 3's
    'development discoveries --task WB.1' equivalent."""
    conn = cs.connect(a.db)
    items = discovery.list_discoveries(conn, a.task) if a.all else discovery.unresolved_discoveries(conn, a.task)
    print(json.dumps(items, indent=2))
    return 0


def _cmd_closeout_check(a):
    """CARD 3's enforcement-mode closeout gate — 'development
    closeout-check --task WB.1' equivalent. Machine-readable JSON on
    stdout always; nonzero exit whenever blocking conditions exist, so
    this can be used directly as an enforcement command, never a
    report-only mechanism that exits 0 regardless."""
    conn = cs.connect(a.db)
    result = discovery.check_closeout(conn, a.task)
    print(json.dumps(result, indent=2))
    return 0 if result["ready_to_close"] else 1


def _cmd_close_task(a):
    """CARD 4 Part 1: the sanctioned closeout path. Always calls
    check_closeout() first; refuses (exit 2, writes nothing) on any
    blocker. This is the enforcement point every WB.1 stage should route
    through instead of hand-writing a completion claim."""
    conn = cs.connect(a.db)
    try:
        row = discovery.close_task(
            conn, task=a.task, actor=a.actor,
            expected_prev_revision=a.expect_revision, request_id=a.request_id,
        )
    except discovery.CloseoutBlockedError as e:
        print(json.dumps(e.result, indent=2))
        print(f"BLOCKED: {e}", file=sys.stderr)
        return 2
    except cs.ContinuityError as e:
        print(f"BLOCKED: {e}", file=sys.stderr)
        return 2
    print(json.dumps(row, indent=2))
    return 0


def _cmd_verify_closeout(a):
    """CARD 4 Part 1, Level 3: independently re-derive whether a task's
    closeout was actually validated and is still clean now, rather than
    trusting a self-report. Exit 0 iff verified."""
    conn = cs.connect(a.db)
    result = discovery.verify_closeout(conn, a.task)
    print(json.dumps(result, indent=2))
    return 0 if result["verified"] else 1


def _cmd_card_contract_record(a):
    conn = cs.connect(a.db)
    try:
        row = card_contract.record_card_contract(
            conn, task=a.task, actor=a.actor, task_id=a.task_id,
            allowed_scope=a.allowed_scope or [], forbidden_areas=a.forbidden_area or [],
            required_checks=a.required_check or [], required_evidence=a.required_evidence or [],
            stage_closeout_required=a.stage_closeout_required, next_return_point=a.next_return_point,
            expected_prev_revision=a.expect_revision, request_id=a.request_id,
        )
    except (cs.ContinuityError, card_contract.CardContractValidationError) as e:
        print(f"BLOCKED: {e}", file=sys.stderr)
        return 2
    print(json.dumps(row, indent=2))
    return 0


def _cmd_card_contract_show(a):
    conn = cs.connect(a.db)
    result = card_contract.get_card_contract(conn, a.task)
    print(json.dumps(result, indent=2))
    return 0 if result is not None else 1


def _cmd_verify_completion(a):
    """CARD 5 / WB.1C-R1 addendum item B: never trust a completion.json
    merely because it exists. Cross-checks its claimed status against
    host-validated closeout state. Exit 0 iff trustworthy."""
    conn = cs.connect(a.db)
    result = discovery.verify_completion_artifact(conn, a.completion_file, expected_task=a.task)
    print(json.dumps(result, indent=2))
    return 0 if result["trustworthy"] else 1


def _cmd_handoff(a):
    """Build a handoff for `tool`. Dry-run (default) builds a CONTEXT-ONLY
    packet and previews the derived tool-specific invocation, sending
    nothing (WB.1C-R1 remediation 5). --execute is a real dispatch and
    requires explicit directive prose (--directive-file) plus a live
    authorization reference (--authorization-revision) — see
    launcher.build_execution_handoff / resolve_execution_authorization for
    what is validated. Never falls back to the context-only packet for a
    real send; a caller that omits either flag with --execute is refused
    (exit 2), not silently downgraded to a context-only dispatch."""
    conn = cs.connect(a.db)
    if a.execute:
        if not a.directive_file or a.authorization_revision is None:
            print(
                "BLOCKED: --execute requires --directive-file and "
                "--authorization-revision (explicit directive prose + a "
                "live user_instruction authorization reference); refusing "
                "to send a bare context packet as if it were a directive.",
                file=sys.stderr,
            )
            return 2
        with open(a.directive_file, encoding="utf-8") as f:
            directive_text = f.read()
        try:
            # launch_execution_handoff is the one guarded path: it builds
            # the packet/payload AND rechecks authorization + freshness
            # immediately before the subprocess is invoked, rather than
            # this CLI calling build + launch as two separate,
            # uncoordinated steps with a validation-to-send gap between
            # them.
            result = launcher.launch_execution_handoff(
                conn, a.tool, task=a.task, actor=a.actor, out_dir=a.out,
                directive_text=directive_text,
                authorization_revision=a.authorization_revision,
                concept_queries=a.query or [], kb_ids=a.kb_id or [],
                expected_request_hash=a.authorization_request_hash,
                dry_run=False, timeout=a.timeout,
            )
        except launcher.AuthorizationError as e:
            print(f"BLOCKED: {e}", file=sys.stderr)
            return 2
    else:
        path, pkt = launcher.build_handoff(
            conn, task=a.task, actor=a.actor, out_dir=a.out,
            concept_queries=a.query or [], kb_ids=a.kb_id or [],
        )
        result = launcher.launch(a.tool, path, dry_run=True, timeout=a.timeout)
        result["handoff_path"] = path
    print(json.dumps(result, indent=2))
    return 0 if (result.get("dry_run") or result.get("launched")) else 1


def _cmd_init_dev_schema(a):
    conn = cs.connect(a.db)
    try:
        cs.init_schema(conn, db_path=a.db, allow_prod_init=a.allow_prod_init)
    except cs.ProductionGuardError as e:
        print(f"BLOCKED: {e}", file=sys.stderr)
        return 2
    print(f"dev_continuity_* schema present on {a.db!r}")
    return 0


def build_parser():
    p = argparse.ArgumentParser(prog="tools.development.cli")
    p.add_argument("--db", default=None, help="defaults to $CIS_SPINE_PATH or the production spine")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("prepare")
    sp.add_argument("task")
    sp.add_argument("--actor", required=True)
    sp.add_argument("--query", action="append")
    sp.add_argument("--kb-id", action="append", type=int)
    sp.add_argument("--out", default=None)
    sp.set_defaults(func=_cmd_prepare)

    sp = sub.add_parser("check")
    sp.add_argument("handoff")
    sp.set_defaults(func=_cmd_check)

    sp = sub.add_parser("publish")
    sp.add_argument("task")
    sp.add_argument("--kind", required=True)
    sp.add_argument("--status", required=True)
    sp.add_argument("--actor", required=True)
    sp.add_argument("--summary", required=True)
    sp.add_argument("--body", default="")
    sp.add_argument("--expect-revision", required=True, type=int)
    sp.add_argument("--request-id", default=None)
    sp.add_argument("--evidence-ref", action="append")
    sp.add_argument("--source-ref", action="append")
    sp.set_defaults(func=_cmd_publish)

    sp = sub.add_parser("reconcile")
    sp.add_argument("task")
    sp.add_argument("--against-revision", required=True, type=int)
    sp.add_argument("--disposition", required=True)
    sp.add_argument("--note", required=True)
    sp.add_argument("--actor", required=True)
    sp.add_argument("--expect-revision", required=True, type=int)
    sp.add_argument("--request-id", default=None)
    sp.add_argument("--evidence-ref", action="append")
    sp.add_argument("--source-ref", action="append")
    sp.set_defaults(func=_cmd_reconcile)

    sp = sub.add_parser("events")
    sp.add_argument("task")
    sp.set_defaults(func=_cmd_events)

    sp = sub.add_parser("import-transcript")
    sp.add_argument("task")
    sp.add_argument("session_file")
    sp.add_argument("--actor", required=True)
    sp.add_argument("--source", default="claude_code")
    sp.add_argument("--select", action="append", type=int)
    sp.set_defaults(func=_cmd_import_transcript)

    sp = sub.add_parser("discover")
    sp.add_argument("executable")
    sp.set_defaults(func=_cmd_discover)

    sp = sub.add_parser(
        "handoff",
        help="Build a packet and hand it to claude/codex via its real CLI "
             "contract. Dry-run by default (shows the derived invocation, "
             "sends nothing); pass --execute for a real send.",
    )
    sp.add_argument("task")
    sp.add_argument("tool", choices=["claude", "codex"])
    sp.add_argument("--actor", required=True)
    sp.add_argument("--query", action="append")
    sp.add_argument("--kb-id", action="append", type=int)
    sp.add_argument("--out", required=True)
    sp.add_argument("--execute", action="store_true",
                     help="Actually run the tool (default: dry-run only). "
                          "Requires --directive-file and --authorization-revision.")
    sp.add_argument("--directive-file", default=None,
                     help="Path to a file containing explicit execution directive prose. "
                          "Required with --execute.")
    sp.add_argument("--authorization-revision", type=int, default=None,
                     help="dev_continuity_events revision (kind='user_instruction') that "
                          "authorizes this execution. Required with --execute; re-validated "
                          "live against the database (missing/wrong-kind/stale is refused).")
    sp.add_argument("--authorization-request-hash", default=None,
                     help="Optional: also require the authorization row's request_hash to "
                          "match exactly, binding the directive to a specific request.")
    sp.add_argument("--timeout", type=int, default=30)
    sp.set_defaults(func=_cmd_handoff)

    sp = sub.add_parser("init-dev-schema")
    sp.add_argument("--allow-prod-init", action="store_true")
    sp.set_defaults(func=_cmd_init_dev_schema)

    sp = sub.add_parser("discovery-record", help="Record a consequential discovered-work item (CARD 3).")
    sp.add_argument("task")
    sp.add_argument("--actor", required=True)
    sp.add_argument("--summary", required=True)
    sp.add_argument("--disposition", required=True, choices=sorted(discovery.DISPOSITIONS))
    sp.add_argument("--expect-revision", required=True, type=int)
    sp.add_argument("--request-id", default=None)
    sp.add_argument("--evidence-ref", action="append")
    sp.add_argument("--source-ref", action="append")
    sp.add_argument("--reason", default=None, help="EXPLICITLY_DEFERRED")
    sp.add_argument("--destination", default=None, help="EXPLICITLY_DEFERRED")
    sp.add_argument("--trigger", default=None, help="EXPLICITLY_DEFERRED")
    sp.add_argument("--originating-stage", default=None, help="BEFORE_STAGE_CLOSEOUT")
    sp.add_argument("--blocking", type=lambda s: s.strip().lower() in ("1", "true", "yes"),
                     default=None, help="BEFORE_STAGE_CLOSEOUT / EXPLICITLY_DEFERRED (true/false)")
    sp.add_argument("--resolution-result", default=None, help="RESOLVED_NOW")
    sp.add_argument("--resolution-evidence", default=None)
    sp.add_argument("--note", default=None)
    sp.set_defaults(func=_cmd_discovery_record)

    sp = sub.add_parser("discovery-resolve", help="Mark a BEFORE_STAGE_CLOSEOUT discovery resolved (CARD 3).")
    sp.add_argument("task")
    sp.add_argument("--discovery-revision", required=True, type=int)
    sp.add_argument("--actor", required=True)
    sp.add_argument("--resolution-result", required=True)
    sp.add_argument("--resolution-evidence", default=None)
    sp.add_argument("--expect-revision", required=True, type=int)
    sp.add_argument("--request-id", default=None)
    sp.set_defaults(func=_cmd_discovery_resolve)

    sp = sub.add_parser("discoveries", help="List discovered-work items for a task (CARD 3).")
    sp.add_argument("task")
    sp.add_argument("--all", action="store_true", help="Include resolved/RESOLVED_NOW/validly-deferred items too (default: unresolved-only).")
    sp.set_defaults(func=_cmd_discoveries)

    sp = sub.add_parser("closeout-check", help="Deterministic ready-to-close gate (CARD 3). Nonzero exit when blocked.")
    sp.add_argument("task")
    sp.set_defaults(func=_cmd_closeout_check)

    sp = sub.add_parser("close-task", help="Sanctioned closeout path (CARD 4): refuses on any blocker, records a durable stage_closed event on success.")
    sp.add_argument("task")
    sp.add_argument("--actor", required=True)
    sp.add_argument("--expect-revision", required=True, type=int)
    sp.add_argument("--request-id", default=None)
    sp.set_defaults(func=_cmd_close_task)

    sp = sub.add_parser("verify-closeout", help="Independently re-derive whether a task's closeout was validated and is still clean (CARD 4, Level 3).")
    sp.add_argument("task")
    sp.set_defaults(func=_cmd_verify_closeout)

    sp = sub.add_parser("card-contract-record", help="Record a machine-readable card contract (CARD 4 Part 2).")
    sp.add_argument("task")
    sp.add_argument("--actor", required=True)
    sp.add_argument("--task-id", required=True)
    sp.add_argument("--allowed-scope", action="append", required=True)
    sp.add_argument("--forbidden-area", action="append", default=[])
    sp.add_argument("--required-check", action="append", required=True)
    sp.add_argument("--required-evidence", action="append", required=True)
    sp.add_argument("--stage-closeout-required",
                     type=lambda s: s.strip().lower() in ("1", "true", "yes"), required=True)
    sp.add_argument("--next-return-point", required=True)
    sp.add_argument("--expect-revision", required=True, type=int)
    sp.add_argument("--request-id", default=None)
    sp.set_defaults(func=_cmd_card_contract_record)

    sp = sub.add_parser("card-contract-show", help="Show the current card contract for a task (CARD 4 Part 2).")
    sp.add_argument("task")
    sp.set_defaults(func=_cmd_card_contract_show)

    sp = sub.add_parser("verify-completion", help="Cross-check a completion.json's claim against host-validated closeout state (CARD 5). Never trusts the file alone.")
    sp.add_argument("task")
    sp.add_argument("completion_file")
    sp.set_defaults(func=_cmd_verify_completion)

    return p


def main(argv=None):
    parser = build_parser()
    a = parser.parse_args(argv)
    return a.func(a)


if __name__ == "__main__":
    sys.exit(main())
