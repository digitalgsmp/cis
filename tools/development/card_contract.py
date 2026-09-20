#!/usr/bin/env python3
"""card_contract.py — bounded, machine-readable card-contract fields
(CARD 4, Part 2).

A card contract is an ordinary dev_continuity_events row, kind=
'user_instruction' (an existing, already-reviewed kind — matching CARD 3's
own no-new-schema precedent), JSON-tagged {"_record_type": "card_contract",
...}. Recording one, and validating that all required fields are present
and well-typed, is what this module does.

Deliberately narrow: this records and validates the DECLARED contract
fields only. It does NOT verify actual changed files against declared
scope, and does not enforce forbidden_areas against a real git diff — that
requires comparing live filesystem/git state to the contract, a materially
bigger feature (deterministic scope verification) explicitly named as
future contained-pipeline work and deferred rather than built here.
"""
import json

from . import continuity_store as cs

_RECORD_TYPE = "card_contract"
REQUIRED_FIELDS = (
    "task_id", "allowed_scope", "forbidden_areas", "required_checks",
    "required_evidence", "stage_closeout_required", "next_return_point",
)


class CardContractValidationError(cs.ContinuityError):
    pass


def _validate(fields):
    missing = [f for f in REQUIRED_FIELDS if fields.get(f) is None]
    if missing:
        raise CardContractValidationError(
            f"card contract missing required field(s): {missing}"
        )
    if not isinstance(fields["allowed_scope"], list) or not fields["allowed_scope"]:
        raise CardContractValidationError("allowed_scope must be a non-empty list")
    if not isinstance(fields["forbidden_areas"], list):
        raise CardContractValidationError("forbidden_areas must be a list (may be empty)")
    if not isinstance(fields["required_checks"], list) or not fields["required_checks"]:
        raise CardContractValidationError("required_checks must be a non-empty list")
    if not isinstance(fields["required_evidence"], list) or not fields["required_evidence"]:
        raise CardContractValidationError("required_evidence must be a non-empty list")
    if not isinstance(fields["stage_closeout_required"], bool):
        raise CardContractValidationError("stage_closeout_required must be a boolean")
    if not isinstance(fields["next_return_point"], str) or not fields["next_return_point"].strip():
        raise CardContractValidationError("next_return_point must be a non-empty string")


def record_card_contract(conn, *, task, actor, task_id, allowed_scope, forbidden_areas,
                          required_checks, required_evidence, stage_closeout_required,
                          next_return_point, expected_prev_revision, request_id=None):
    """Record one card contract. Raises CardContractValidationError for a
    malformed/incomplete contract before anything is written."""
    fields = {
        "task_id": task_id, "allowed_scope": allowed_scope, "forbidden_areas": forbidden_areas,
        "required_checks": required_checks, "required_evidence": required_evidence,
        "stage_closeout_required": stage_closeout_required, "next_return_point": next_return_point,
    }
    _validate(fields)
    payload = {"_record_type": _RECORD_TYPE, **fields}
    return cs.publish_event(
        conn, task=task, kind="user_instruction", status="card_contract", actor=actor,
        summary=f"Card contract for {task_id}", body=json.dumps(payload, sort_keys=True),
        expected_prev_revision=expected_prev_revision, request_id=request_id,
    )


def get_card_contract(conn, task):
    """The most recent VALID card_contract event for `task`, or None. A
    malformed contract event (if one somehow exists) is skipped, not
    returned as if it were usable."""
    events = cs.list_events(conn, task)
    for e in reversed(events):
        if e["kind"] != "user_instruction":
            continue
        try:
            payload = json.loads(e.get("body") or "{}")
        except (TypeError, ValueError):
            continue
        if not isinstance(payload, dict) or payload.get("_record_type") != _RECORD_TYPE:
            continue
        try:
            _validate(payload)
        except CardContractValidationError:
            continue
        return {"revision": e["revision"], "actor": e["actor"], "created_at": e["created_at"],
                "fields": payload}
    return None
