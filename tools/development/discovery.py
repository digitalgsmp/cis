#!/usr/bin/env python3
"""discovery.py — deterministic discovered-work capture and stage-closeout
gate (CARD 3), built entirely on top of the existing dev_continuity_events
mechanism in continuity_store.py.

WHY NO SCHEMA CHANGE. Migration 0039 (already live on production, see
CARD 2) constrains dev_continuity_events.kind with
CHECK(kind IN ('proposal','decision','verified_result','unfinished_work',
'contradiction','user_instruction','reconciliation')) — it does not include
a 'discovery' kind. Adding one would mean recreating the table (SQLite has
no ALTER TABLE ... MODIFY CHECK), which Card 3's own instruction forbids:
"If schema changes beyond 0039 are required, stop and produce a separate
migration card rather than silently altering production schema." So a
discovered-work record is instead an ordinary kind='unfinished_work' event
whose JSON body is tagged {"_record_type": "discovery", ...} — the tag is
this module's own concern, not the database's, and existing generic
(non-discovery) unfinished_work/contradiction events are left exactly as
they already worked in R1/R2, untouched and still checked by the closeout
gate on their own terms.

Resolving a BEFORE_STAGE_CLOSEOUT discovery reuses continuity_store's
existing record_reconciliation() (kind='reconciliation', against_revision
naming the discovery's own revision) — the exact mechanism WB.1C-R1/R2
already built, tested, and had independently reviewed. Nothing new is
invented for "how does an open item get marked resolved."
"""
import json
import os

from . import continuity_store as cs

# Status tokens this project's cards use that claim a task is finished/
# accepted-pending-review — the ones a consumer should NOT trust merely
# because the file says so.
_COMPLETION_CLAIM_STATUSES = {
    "READY_FOR_CHATGPT_REVIEW", "READY_FOR_VERIFICATION", "DONE", "VERIFIED",
    "PASS", "COMPLETE",
}

DISPOSITIONS = {"RESOLVED_NOW", "BEFORE_STAGE_CLOSEOUT", "EXPLICITLY_DEFERRED"}
_RECORD_TYPE = "discovery"


class DiscoveryValidationError(cs.ContinuityError):
    """A discovery record was malformed or incomplete. Raised, never a
    silent warning — the card's explicit 'reject, do not merely warn'
    requirement."""


def _validate(disposition, fields):
    if disposition not in DISPOSITIONS:
        raise DiscoveryValidationError(
            f"unknown disposition {disposition!r}; must be one of {sorted(DISPOSITIONS)}"
        )
    if disposition == "RESOLVED_NOW":
        if not fields.get("resolution_result"):
            raise DiscoveryValidationError(
                "RESOLVED_NOW requires resolution_result (the resolution/evidence itself)"
            )
    elif disposition == "BEFORE_STAGE_CLOSEOUT":
        if not fields.get("originating_stage"):
            raise DiscoveryValidationError(
                "BEFORE_STAGE_CLOSEOUT requires originating_stage"
            )
        if fields.get("blocking") is None:
            raise DiscoveryValidationError(
                "BEFORE_STAGE_CLOSEOUT requires an explicit blocking classification (true/false)"
            )
    elif disposition == "EXPLICITLY_DEFERRED":
        if not fields.get("reason"):
            raise DiscoveryValidationError("EXPLICITLY_DEFERRED requires reason")
        if not fields.get("destination"):
            raise DiscoveryValidationError("EXPLICITLY_DEFERRED requires destination")
        if not fields.get("trigger"):
            raise DiscoveryValidationError(
                "EXPLICITLY_DEFERRED requires a trigger/dependency for reconsideration"
            )
        if fields.get("blocking") is None:
            raise DiscoveryValidationError(
                "EXPLICITLY_DEFERRED requires an explicit blocking classification (true/false)"
            )


def record_discovery(conn, *, task, actor, summary, disposition, expected_prev_revision,
                      request_id=None, evidence_refs=None, source_refs=None,
                      reason=None, destination=None, blocking=None, trigger=None,
                      originating_stage=None, resolution_result=None,
                      resolution_evidence=None, note=None):
    """Record one consequential discovered-work item with an explicit,
    validated disposition. Raises DiscoveryValidationError for a malformed
    or incomplete record before anything is written — invalid input never
    reaches the database as a 'recorded' row."""
    fields = {
        "reason": reason, "destination": destination, "blocking": blocking,
        "trigger": trigger, "originating_stage": originating_stage,
        "resolution_result": resolution_result, "resolution_evidence": resolution_evidence,
    }
    _validate(disposition, fields)
    payload = {
        "_record_type": _RECORD_TYPE,
        "disposition": disposition,
        **{k: v for k, v in fields.items() if v is not None},
    }
    if note:
        payload["note"] = note
    return cs.publish_event(
        conn, task=task, kind="unfinished_work", status=disposition, actor=actor,
        summary=summary, body=json.dumps(payload, sort_keys=True),
        evidence_refs=evidence_refs, source_refs=source_refs,
        expected_prev_revision=expected_prev_revision, request_id=request_id,
    )


def resolve_discovery(conn, *, task, actor, discovery_revision, resolution_result,
                       expected_prev_revision, request_id=None, resolution_evidence=None):
    """Mark a BEFORE_STAGE_CLOSEOUT discovery (identified by its own
    revision) resolved. Requires resolution_result — a bare 'it's done' with
    no stated result is rejected, matching RESOLVED_NOW's own bar."""
    if not resolution_result:
        raise DiscoveryValidationError(
            "resolving a discovery requires resolution_result"
        )
    note = json.dumps({
        "_record_type": _RECORD_TYPE, "resolution_result": resolution_result,
        "resolution_evidence": resolution_evidence,
    }, sort_keys=True)
    return cs.record_reconciliation(
        conn, task=task, actor=actor, against_revision=discovery_revision,
        disposition="resolved", note=note,
        expected_prev_revision=expected_prev_revision, request_id=request_id,
    )


def _parse_discovery_payload(event):
    try:
        payload = json.loads(event.get("body") or "{}")
    except (TypeError, ValueError):
        return None
    if not isinstance(payload, dict) or payload.get("_record_type") != _RECORD_TYPE:
        return None
    return payload


def list_discoveries(conn, task):
    """Every discovery record for `task`, each annotated with whether it
    is malformed (disposition invalid or required fields missing — checked
    against the SAME validator record_discovery() itself enforces, so a row
    that somehow reached the database in a broken state, e.g. through a
    future caller bypassing this module, is still caught here) and whether
    it has since been resolved via a reconciliation event naming its
    revision."""
    events = cs.list_events(conn, task)
    reconciled_revisions = {
        e["against_revision"] for e in events
        if e["kind"] == "reconciliation" and e.get("against_revision") is not None
    }
    discoveries = []
    for e in events:
        if e["kind"] != "unfinished_work":
            continue
        payload = _parse_discovery_payload(e)
        if payload is None:
            continue
        disposition = payload.get("disposition")
        malformed = False
        try:
            _validate(disposition, payload)
        except DiscoveryValidationError:
            malformed = True
        discoveries.append({
            "revision": e["revision"], "actor": e["actor"], "summary": e["summary"],
            "disposition": disposition, "malformed": malformed,
            "resolved": e["revision"] in reconciled_revisions,
            "fields": payload, "created_at": e["created_at"],
        })
    return discoveries


def unresolved_discoveries(conn, task):
    """Discoveries that must be visible before this task can validly
    close: anything malformed (undispositioned, in effect), and any
    BEFORE_STAGE_CLOSEOUT item not yet resolved. RESOLVED_NOW items are
    complete at creation time (their resolution_result was required and
    validated then) and never appear here. Validly-formed
    EXPLICITLY_DEFERRED items never block THIS task's closeout — deferral
    to elsewhere is exactly the point of that disposition."""
    return [
        d for d in list_discoveries(conn, task)
        if not d["resolved"] and (d["malformed"] or d["disposition"] == "BEFORE_STAGE_CLOSEOUT")
    ]


def check_closeout(conn, task, dev_conn=None):
    """Deterministic ready-to-close check for `task`. Never raises for a
    task with no events at all (an untouched task is trivially ready).
    Blocking conditions checked, per Card 3's explicit list:
      - dev_continuity schema not initialized (a required activation not
        completed, machine-readable);
      - malformed discoveries (undispositioned consequential work);
      - unresolved BEFORE_STAGE_CLOSEOUT discoveries;
      - unresolved plain (non-discovery) unfinished_work events;
      - unresolved contradiction events.
    Task-scoped throughout (cs.list_events already filters by task), so an
    unrelated task's own open items never appear here."""
    dev_conn = dev_conn or conn
    if not cs.is_initialized(dev_conn):
        return {
            "task": task, "ready_to_close": False,
            "blockers": [{"type": "dev_continuity_not_initialized",
                          "detail": "required activation (migration 0039) not completed on this database"}],
            "evidence_checked": {"total_events": 0, "discoveries_checked": 0},
        }

    events = cs.list_events(dev_conn, task)
    reconciled_revisions = {
        e["against_revision"] for e in events
        if e["kind"] == "reconciliation" and e.get("against_revision") is not None
    }
    discoveries = list_discoveries(dev_conn, task)
    discovery_revisions = {d["revision"] for d in discoveries}

    blockers = []
    for d in discoveries:
        if d["resolved"]:
            continue
        if d["malformed"]:
            blockers.append({"type": "malformed_deferral_or_discovery", "revision": d["revision"],
                              "summary": d["summary"]})
        elif d["disposition"] == "BEFORE_STAGE_CLOSEOUT":
            blockers.append({"type": "unresolved_before_stage_closeout", "revision": d["revision"],
                              "summary": d["summary"]})

    for e in events:
        if e["revision"] in reconciled_revisions or e["revision"] in discovery_revisions:
            continue
        if e["kind"] == "unfinished_work":
            blockers.append({"type": "unresolved_unfinished_work", "revision": e["revision"],
                              "summary": e["summary"]})
        elif e["kind"] == "contradiction":
            blockers.append({"type": "unresolved_contradiction", "revision": e["revision"],
                              "summary": e["summary"]})

    return {
        "task": task,
        "ready_to_close": len(blockers) == 0,
        "blockers": blockers,
        "evidence_checked": {
            "total_events": len(events),
            "discoveries_checked": len(discoveries),
        },
    }


# ── Sanctioned closeout path (CARD 4, Part 1) ────────────────────────────
# Enforcement level achieved: LEVEL 2 (refuse completion) for any caller
# that routes through close_task() instead of hand-writing a completion
# claim — it always calls check_closeout() first and raises, writing
# nothing, if any blocker exists. It cannot reach LEVEL 1 (prevent action)
# because nothing host-side can intercept an external model writing its own
# completion.json by hand outside this CLI; that residual gap is named
# explicitly, not hidden, in this card's evidence.

class CloseoutBlockedError(cs.ContinuityError):
    def __init__(self, result):
        self.result = result
        blockers = "; ".join(
            f"{b['type']}(rev {b.get('revision', '-')})" for b in result["blockers"]
        )
        super().__init__(f"closeout blocked for task {result['task']!r}: {blockers}")


def close_task(conn, *, task, actor, expected_prev_revision, dev_conn=None, request_id=None):
    """The sanctioned closeout path. Refuses (raises CloseoutBlockedError,
    writes nothing) if check_closeout() reports any blocker. On success,
    records a durable 'stage_closed' decision event carrying the exact
    check_closeout() result as evidence — so a later, independent party can
    verify closeout was actually checked and clean (see verify_closeout),
    not merely claimed in prose."""
    dev_conn = dev_conn or conn
    result = check_closeout(conn, task, dev_conn=dev_conn)
    if not result["ready_to_close"]:
        raise CloseoutBlockedError(result)
    return cs.publish_event(
        dev_conn, task=task, kind="decision", status="stage_closed", actor=actor,
        summary=(
            f"Stage closeout validated: {result['evidence_checked']['total_events']} events, "
            f"{result['evidence_checked']['discoveries_checked']} discoveries, 0 blockers."
        ),
        body=json.dumps(result, sort_keys=True),
        expected_prev_revision=expected_prev_revision, request_id=request_id,
    )


def verify_closeout(conn, task):
    """LEVEL 3 (fail verification): independently re-derive whether a
    task's closeout was ever actually validated and is STILL clean now —
    never trusts a self-report. If closeout was validated in the past but a
    new blocker has appeared since, this reports verified=False with the
    current blockers, not the stale past success."""
    events = cs.list_events(conn, task)
    closures = [e for e in events if e["kind"] == "decision" and e["status"] == "stage_closed"]
    if not closures:
        return {"verified": False, "reason": "no stage_closed event found for this task"}
    latest = closures[-1]
    current = check_closeout(conn, task)
    if not current["ready_to_close"]:
        return {
            "verified": False,
            "reason": "closeout was validated in the past but new blockers exist now",
            "closed_at_revision": latest["revision"], "current_blockers": current["blockers"],
        }
    return {"verified": True, "closed_at_revision": latest["revision"], "closed_at": latest["created_at"]}


# ── Completion-artifact consumer (CARD 5, WB.1C-R1 addendum item B) ──────
# A hand-written completion.json becoming "authoritative" merely because a
# file exists is exactly the bypass this exists to catch. This is a
# CONSUMER-side check, not a preventer: it cannot stop an external process
# from writing an arbitrary file outside this CLI (that residual Level-1
# gap is named, not hidden — see CARD 4's own evidence). What it DOES do:
# give anyone a deterministic way to ask "is this specific completion
# claim actually backed by a validated closeout?" before trusting it.

def verify_completion_artifact(conn, path, expected_task=None):
    """Read a completion.json-shaped file and cross-check its claim
    against verify_closeout()'s real answer. Never trusts the file's own
    status string. Returns a dict with `trustworthy: bool` and `reasons`
    explaining any mismatch — never raises for a malformed file (that IS
    the finding, reported as untrustworthy, not an exception a caller must
    remember to catch)."""
    if not os.path.isfile(path):
        return {"trustworthy": False, "reasons": [f"completion artifact not found: {path}"]}
    try:
        with open(path, encoding="utf-8") as f:
            artifact = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        return {"trustworthy": False, "reasons": [f"could not parse as JSON: {type(e).__name__}: {e}"]}
    if not isinstance(artifact, dict):
        return {"trustworthy": False, "reasons": ["completion artifact is not a JSON object"]}

    claimed_status = artifact.get("status")
    claimed_task = artifact.get("card_id") or artifact.get("task_id") or artifact.get("task")
    reasons = []

    if claimed_status is None:
        reasons.append("artifact has no 'status' field")
    if expected_task is not None and claimed_task is not None and claimed_task != expected_task:
        reasons.append(
            f"artifact claims task/card_id {claimed_task!r}, caller expected {expected_task!r}"
        )

    task_for_verification = expected_task or claimed_task
    if task_for_verification is None:
        reasons.append("no task identity available to verify against (neither expected_task "
                       "nor a card_id/task_id/task field in the artifact)")
        return {"trustworthy": False, "reasons": reasons, "claimed_status": claimed_status}

    verification = verify_closeout(conn, task_for_verification)
    claims_completion = isinstance(claimed_status, str) and claimed_status.upper() in _COMPLETION_CLAIM_STATUSES

    if claims_completion and not verification["verified"]:
        reasons.append(
            f"artifact claims {claimed_status!r} but host-validated closeout for "
            f"{task_for_verification!r} is NOT verified: {verification.get('reason')}"
        )
    if claimed_status is not None and str(claimed_status).upper() in ("VERIFIED", "PASS"):
        reasons.append(
            "artifact self-labels VERIFIED/PASS — this project's own convention is that no "
            "card may self-label VERIFIED; treated as an additional trust concern, not "
            "just an unmet closeout"
        )

    trustworthy = claims_completion and verification["verified"] and not reasons
    return {
        "trustworthy": trustworthy,
        "reasons": reasons,
        "claimed_status": claimed_status,
        "claimed_task": claimed_task,
        "task_verified_against": task_for_verification,
        "closeout_verification": verification,
    }
