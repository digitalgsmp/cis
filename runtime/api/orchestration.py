"""
orchestration.py — Lifecycle state machine, dispatch logging, evidence scaffolding.

Owns all lifecycle state transitions, dispatch logging, and evidence scaffolding.
No other module may write directly to lifecycle_events, dispatch_log,
dispatch_events, or verification_evidence except through functions defined here.

ALLOV1-BE-001: Advisor Loop Lifecycle Observability — Backend, Database, and Enforcement
Spec: ADVISOR_LOOP_LIFECYCLE_OBSERVABILITY_v1.1 (approved 2026-06-01)
"""

import uuid
import hashlib
from datetime import datetime


# ──────────────────────────────────────────────
#  ALLOWED TRANSITIONS (Section 5 of approved spec)
# ──────────────────────────────────────────────

ALLOWED_TRANSITIONS = {
    ('IDLE',                'ROUTING'),
    ('ROUTING',             'RESEARCH_ACTIVE'),
    ('ROUTING',             'DRAFTING'),
    ('ROUTING',             'ERROR'),
    ('RESEARCH_ACTIVE',     'RESEARCH_COMPLETE'),
    ('RESEARCH_ACTIVE',     'ABORTED'),
    ('RESEARCH_ACTIVE',     'ERROR'),
    ('RESEARCH_COMPLETE',   'RESEARCH_HANDOFF'),
    ('RESEARCH_COMPLETE',   'IDLE'),
    ('RESEARCH_HANDOFF',    'DRAFTING'),
    ('RESEARCH_HANDOFF',    'ERROR'),
    ('DRAFTING',            'DRAFT_READY'),
    ('DRAFTING',            'ABORTED'),
    ('DRAFTING',            'ERROR'),
    ('DRAFT_READY',         'REVIEW_PENDING'),
    ('DRAFT_READY',         'DRAFTING'),
    ('DRAFT_READY',         'ERIC_APPROVAL_GATE'),
    ('DRAFT_READY',         'IDLE'),
    ('REVIEW_PENDING',      'REVIEWING'),
    ('REVIEW_PENDING',      'ERROR'),
    ('REVIEWING',           'REVIEW_COMPLETE'),
    ('REVIEWING',           'ABORTED'),
    ('REVIEWING',           'ERROR'),
    ('REVIEW_COMPLETE',     'REVISE_REQUESTED'),
    ('REVIEW_COMPLETE',     'REJECTED'),
    ('REVIEW_COMPLETE',     'ERIC_APPROVAL_GATE'),
    ('REVISE_REQUESTED',    'DRAFTING'),
    ('REJECTED',            'IDLE'),
    ('ERIC_APPROVAL_GATE',  'DIRECTIVE_DRAFTING'),
    ('ERIC_APPROVAL_GATE',  'IDLE'),
    ('DIRECTIVE_DRAFTING',  'DIRECTIVE_AUTHORED'),
    ('DIRECTIVE_DRAFTING',  'ABORTED'),
    ('DIRECTIVE_DRAFTING',  'ERROR'),
    ('DIRECTIVE_AUTHORED',  'DIRECTIVE_READY'),
    ('DIRECTIVE_AUTHORED',  'DIRECTIVE_DRAFTING'),
    ('DIRECTIVE_READY',     'EXECUTING'),
    ('DIRECTIVE_READY',     'DIRECTIVE_DRAFTING'),
    ('EXECUTING',           'EXECUTION_COMPLETE'),
    ('EXECUTING',           'ABORTED'),
    ('EXECUTING',           'ERROR'),
    ('EXECUTION_COMPLETE',  'VERIFICATION'),
    ('VERIFICATION',        'PASS'),
    ('VERIFICATION',        'FAIL'),
    ('VERIFICATION',        'UNVERIFIED'),
    ('PASS',                'IDLE'),
    ('FAIL',                'IDLE'),
    ('UNVERIFIED',          'VERIFICATION'),
    ('UNVERIFIED',          'IDLE'),
}

# Universal transitions — allowed from any active state
UNIVERSAL_TO_ABORTED = {
    'RESEARCH_ACTIVE', 'DRAFTING', 'DIRECTIVE_DRAFTING',
    'REVIEWING', 'EXECUTING', 'RESEARCH_HANDOFF',
    'REVIEW_PENDING', 'VERIFICATION'
}
UNIVERSAL_TO_ERROR = {
    'ROUTING', 'RESEARCH_ACTIVE', 'RESEARCH_HANDOFF',
    'DRAFTING', 'DIRECTIVE_DRAFTING', 'REVIEW_PENDING',
    'REVIEWING', 'EXECUTING'
}


# ──────────────────────────────────────────────
#  EXCEPTIONS
# ──────────────────────────────────────────────

class LifecycleStateError(Exception):
    """Raised when a lifecycle state assertion fails."""
    pass


class LifecycleTransitionError(Exception):
    """Raised when a transition is not in the allowed set."""
    pass


class DirectiveHashMismatchError(Exception):
    """Raised when directive text hash does not match frozen hash."""
    pass


class UnauthorizedDispatchError(Exception):
    """Raised when a dispatch is not authorized by the source actor."""
    pass


class AuthFailureError(Exception):
    """Raised on HTTP 401/403 from target gateway."""
    pass


# ──────────────────────────────────────────────
#  CORE FUNCTIONS
# ──────────────────────────────────────────────

def generate_proposal_id() -> str:
    """Generate a new UUID proposal ID."""
    return str(uuid.uuid4())


def get_current_state(proposal_id: str, db) -> str | None:
    """Return the current lifecycle state for a proposal.

    Current state = most recent to_state in lifecycle_events
    for this proposal_id. Returns None if no events exist.
    """
    row = db.execute(
        "SELECT to_state FROM lifecycle_events "
        "WHERE proposal_id = ? ORDER BY id DESC LIMIT 1",
        (proposal_id,)
    ).fetchone()
    return row['to_state'] if row else None


def transition_state(proposal_id, session_id, from_state,
                     to_state, initiated_by, gate_type=None,
                     dispatch_ref=None, evidence_ref=None,
                     reviewer_message_id=None,
                     directive_hash=None, eric_approved=0,
                     eric_bypass=0, revision_count=0,
                     notes=None, db=None) -> int:
    """Execute a lifecycle state transition.

    Validates the transition against ALLOWED_TRANSITIONS and
    universal transition sets. Appends a new row to lifecycle_events.

    Returns the row ID of the inserted lifecycle event.
    """
    current = get_current_state(proposal_id, db)
    # Allow IDLE start when no state exists yet
    effective_current = current if current is not None else 'IDLE'
    if effective_current != from_state:
        raise LifecycleStateError(
            f"State mismatch for proposal {proposal_id}: "
            f"expected '{from_state}', current is "
            f"'{effective_current}'."
        )
    # Check universal transitions first
    if to_state == 'ABORTED' and from_state in UNIVERSAL_TO_ABORTED:
        pass  # allowed
    elif to_state == 'ERROR' and from_state in UNIVERSAL_TO_ERROR:
        pass  # allowed
    elif (from_state, to_state) not in ALLOWED_TRANSITIONS:
        raise LifecycleTransitionError(
            f"Transition '{from_state}' → '{to_state}' is not "
            f"an allowed lifecycle transition."
        )
    cursor = db.execute(
        """INSERT INTO lifecycle_events
           (proposal_id, session_id, from_state, to_state,
            gate_type, initiated_by, timestamp, dispatch_ref,
            evidence_ref, reviewer_message_id, directive_hash,
            eric_approved, eric_bypass, revision_count, notes)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (proposal_id, session_id, from_state, to_state,
         gate_type, initiated_by, datetime.utcnow().isoformat(),
         dispatch_ref, evidence_ref, reviewer_message_id,
         directive_hash, eric_approved, eric_bypass,
         revision_count, notes)
    )
    db.commit()
    return cursor.lastrowid


# ──────────────────────────────────────────────
#  DISPATCH LOGGING
# ──────────────────────────────────────────────

def create_dispatch(proposal_id, source_actor, target_agent,
                    target_endpoint, lifecycle_state_at, payload,
                    initiated_by, eric_approved=0,
                    directive_hash=None, db=None) -> str:
    """Create a new dispatch record and its PENDING event.

    Returns the dispatch_id.
    """
    dispatch_id = str(uuid.uuid4())
    payload_bytes = payload.encode('utf-8') if isinstance(
        payload, str) else str(payload).encode('utf-8')
    payload_hash = hashlib.sha256(payload_bytes).hexdigest()
    payload_summary = (payload[:500] if isinstance(payload, str)
                       else str(payload)[:500])
    db.execute(
        """INSERT INTO dispatch_log
           (dispatch_id, proposal_id, source_actor, target_agent,
            target_endpoint, lifecycle_state_at, payload_hash,
            payload_summary, initiated_by, eric_approved,
            timestamp_initiated, current_status, directive_hash)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (dispatch_id, proposal_id, source_actor, target_agent,
         target_endpoint, lifecycle_state_at, payload_hash,
         payload_summary, initiated_by, eric_approved,
         datetime.utcnow().isoformat(), 'PENDING', directive_hash)
    )
    db.execute(
        """INSERT INTO dispatch_events
           (dispatch_id, event_type, timestamp)
           VALUES (?,?,?)""",
        (dispatch_id, 'PENDING', datetime.utcnow().isoformat())
    )
    db.commit()
    return dispatch_id


def update_dispatch_inflight(dispatch_id, db) -> None:
    """Mark a dispatch as IN_FLIGHT and log the event."""
    db.execute(
        "UPDATE dispatch_log SET current_status='IN_FLIGHT' "
        "WHERE dispatch_id=?", (dispatch_id,)
    )
    db.execute(
        """INSERT INTO dispatch_events
           (dispatch_id, event_type, timestamp)
           VALUES (?,?,?)""",
        (dispatch_id, 'IN_FLIGHT', datetime.utcnow().isoformat())
    )
    db.commit()


def complete_dispatch(dispatch_id, http_status_code,
                      response_body, db) -> str:
    """Mark a dispatch as SUCCESS and log the event.

    Returns the response_message_id.
    """
    response_message_id = str(uuid.uuid4())
    response_summary = (response_body[:500]
                        if isinstance(response_body, str)
                        else str(response_body)[:500])
    now = datetime.utcnow().isoformat()
    db.execute(
        """UPDATE dispatch_log SET
           current_status='SUCCESS', timestamp_completed=?,
           http_status_code=?, response_message_id=?,
           response_summary=?
           WHERE dispatch_id=?""",
        (now, http_status_code, response_message_id,
         response_summary, dispatch_id)
    )
    db.execute(
        """INSERT INTO dispatch_events
           (dispatch_id, event_type, timestamp,
            http_status_code, response_message_id)
           VALUES (?,?,?,?,?)""",
        (dispatch_id, 'SUCCESS', now,
         http_status_code, response_message_id)
    )
    db.commit()
    return response_message_id


def fail_dispatch(dispatch_id, http_status_code,
                  error_message, db) -> None:
    """Mark a dispatch as FAILED and log the event."""
    now = datetime.utcnow().isoformat()
    db.execute(
        """UPDATE dispatch_log SET
           current_status='FAILED', timestamp_completed=?,
           http_status_code=?, error_message=?
           WHERE dispatch_id=?""",
        (now, http_status_code, error_message, dispatch_id)
    )
    db.execute(
        """INSERT INTO dispatch_events
           (dispatch_id, event_type, timestamp,
            http_status_code, error_message)
           VALUES (?,?,?,?,?)""",
        (dispatch_id, 'FAILED', now,
         http_status_code, error_message)
    )
    db.commit()


def abort_dispatch(dispatch_id, db) -> None:
    """Mark a dispatch as ABORTED and log the event."""
    now = datetime.utcnow().isoformat()
    db.execute(
        """UPDATE dispatch_log SET
           current_status='ABORTED', timestamp_completed=?
           WHERE dispatch_id=?""",
        (now, dispatch_id)
    )
    db.execute(
        """INSERT INTO dispatch_events
           (dispatch_id, event_type, timestamp)
           VALUES (?,?,?)""",
        (dispatch_id, 'ABORTED', now)
    )
    db.commit()


# ──────────────────────────────────────────────
#  DIRECTIVE HASHING
# ──────────────────────────────────────────────

def freeze_directive(proposal_id, session_id,
                     directive_text, db) -> str:
    """Freeze a directive by hashing its text and transitioning state.

    Transitions from ERIC_APPROVAL_GATE to DIRECTIVE_AUTHORED
    and stores the directive_hash in lifecycle_events.

    Returns the directive_hash.
    """
    directive_hash = hashlib.sha256(
        directive_text.encode('utf-8')
    ).hexdigest()
    transition_state(
        proposal_id=proposal_id,
        session_id=session_id,
        from_state='ERIC_APPROVAL_GATE',
        to_state='DIRECTIVE_AUTHORED',
        initiated_by='orchestrator',
        gate_type='deterministic',
        directive_hash=directive_hash,
        db=db
    )
    return directive_hash


def validate_directive_hash(proposal_id,
                             directive_text, db) -> bool:
    """Validate that directive text matches the frozen hash.

    Returns True if the computed hash matches the most recent
    directive_hash in lifecycle_events for this proposal.
    """
    computed = hashlib.sha256(
        directive_text.encode('utf-8')
    ).hexdigest()
    row = db.execute(
        """SELECT directive_hash FROM lifecycle_events
           WHERE proposal_id=? AND directive_hash IS NOT NULL
           ORDER BY id DESC LIMIT 1""",
        (proposal_id,)
    ).fetchone()
    if not row:
        return False
    return computed == row['directive_hash']


# ──────────────────────────────────────────────
#  VERIFICATION EVIDENCE (MINIMAL SCAFFOLD)
# ──────────────────────────────────────────────

def record_verification_evidence(proposal_id, evidence_type,
                                  evidence_value, db,
                                  status='PRESENT',
                                  notes=None) -> None:
    """Record a piece of verification evidence.

    Minimal scaffold only — no automated verifier logic.
    Verifier behavior is Directive 3 scope.
    """
    db.execute(
        """INSERT INTO verification_evidence
           (proposal_id, evidence_type, evidence_value,
            status, timestamp, notes)
           VALUES (?,?,?,?,?,?)""",
        (proposal_id, evidence_type, evidence_value,
         status, datetime.utcnow().isoformat(), notes)
    )
    db.commit()


def evaluate_verification(proposal_id,
                           required_evidence_types, db) -> str:
    """Evaluate verification evidence for a proposal.

    Minimal scaffold only — no automated verifier logic.
    Returns PASS / FAIL / UNVERIFIED based on stored records.
    """
    rows = db.execute(
        """SELECT evidence_type, status FROM verification_evidence
           WHERE proposal_id=?""",
        (proposal_id,)
    ).fetchall()
    found = {r['evidence_type']: r['status'] for r in rows}
    for etype in required_evidence_types:
        if etype not in found:
            return 'UNVERIFIED'
        if found[etype] == 'FAIL':
            return 'FAIL'
    return 'PASS'
