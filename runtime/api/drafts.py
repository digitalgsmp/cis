"""
api/drafts.py — ADR-048 Staged Draft Intake Layer
Blueprint: /api/drafts/
ADR: ADR-048
"""

import hashlib
from datetime import datetime, timezone

from flask import Blueprint, request, jsonify
from db.connection import db_connect, ensure_drafts_tables

drafts_bp = Blueprint('drafts', __name__, url_prefix='/api/drafts')

VALID_DRAFT_TYPES = {
    'adr', 'knowledge_record', 'session_field',
    'conflict', 'manifest', 'primer_update', 'config_patch'
}

VALID_FORMATS = {'json', 'markdown', 'text', 'structured'}

VALID_MODELS = {'claude', 'chatgpt', 'gemini', 'local', 'human'}

# Zone/status legal combinations at staging boundary.
# Expanded when approve/commit routes are built.
LEGAL_ENTRY_STATES = {
    ('inbox', 'inbox'),
}


def _now():
    return datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')


def _compute_checksum(payload: str) -> str:
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()


def _validate_transition(zone: str, status: str) -> tuple[bool, str]:
    """
    Validate zone/status combination at staging boundary.
    canonical zone is only reachable via committed status.
    Expanded as approve/commit routes are added.
    """
    if zone == 'canonical' and status != 'committed':
        return False, "zone='canonical' requires status='committed'"
    if status == 'committed' and zone != 'canonical':
        return False, "status='committed' requires zone='canonical'"
    return True, ''


def _validate_supersession(conn, supersedes_id: int, new_draft_id_placeholder) -> tuple[bool, str]:
    """
    Validate supersession legality before marking old draft superseded.
    Rules:
      - Target must exist
      - Target must not already be superseded
      - Target must not be committed
      - Self-supersession is impossible (new draft not yet inserted, checked by caller)
    """
    target = conn.execute(
        'SELECT id, status FROM drafts WHERE id = ?', (supersedes_id,)
    ).fetchone()

    if not target:
        return False, f'supersedes_id {supersedes_id} does not exist'
    if target['status'] == 'superseded':
        return False, f'Draft {supersedes_id} is already superseded and cannot be replaced again'
    if target['status'] == 'committed':
        return False, f'Draft {supersedes_id} is committed and cannot be superseded'
    return True, ''


@drafts_bp.before_app_request
def init_drafts():
    """Ensure drafts table exists. Transitional — acceptable for Phase 1."""
    conn = db_connect()
    ensure_drafts_tables(conn)
    conn.close()


@drafts_bp.route('/stage', methods=['POST'])
def stage_draft():
    """
    Stage an AI-proposed draft into the intake buffer.

    Required fields:
        draft_type      — one of seven ADR-048 draft types
        payload         — the proposed content (string)

    Optional fields:
        payload_format  — default 'json'
        source_model    — model that produced this draft
        source_session  — CIS Live session ID or label
        filename        — originating filename if applicable
        imported_by     — human operator identifier
        proposed_target — intended commit destination
        supersedes_id   — draft ID this replaces (integer)
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'Request body must be JSON'}), 400

    draft_type = data.get('draft_type', '').strip()
    payload = data.get('payload', '')

    if draft_type not in VALID_DRAFT_TYPES:
        return jsonify({
            'error': f'Invalid draft_type. Must be one of: {sorted(VALID_DRAFT_TYPES)}'
        }), 400

    if not payload or not isinstance(payload, str) or not payload.strip():
        return jsonify({'error': 'payload is required and must be a non-empty string'}), 400

    payload_format = data.get('payload_format', 'json')
    if payload_format not in VALID_FORMATS:
        return jsonify({
            'error': f'Invalid payload_format. Must be one of: {sorted(VALID_FORMATS)}'
        }), 400

    source_model = data.get('source_model')
    if source_model and source_model not in VALID_MODELS:
        return jsonify({
            'error': f'Invalid source_model. Must be one of: {sorted(VALID_MODELS)}'
        }), 400

    # Staging entry point always starts at inbox/inbox
    zone, status = 'inbox', 'inbox'
    valid, reason = _validate_transition(zone, status)
    if not valid:
        return jsonify({'error': f'Transition validation failed: {reason}'}), 400

    checksum = _compute_checksum(payload)
    now = _now()
    supersedes_id = data.get('supersedes_id')

    # Validate supersedes_id type if provided
    if supersedes_id is not None:
        if not isinstance(supersedes_id, int):
            return jsonify({'error': 'supersedes_id must be an integer'}), 400

    conn = db_connect()
    try:
        # Duplicate detection
        existing = conn.execute(
            'SELECT id, status, zone FROM drafts WHERE checksum = ?', (checksum,)
        ).fetchone()
        if existing:
            return jsonify({
                'status': 'duplicate',
                'message': 'An identical draft already exists in the intake buffer.',
                'existing_draft_id': existing['id'],
                'existing_status': existing['status'],
                'existing_zone': existing['zone']
            }), 409

        # Supersession legality validation before insert
        if supersedes_id is not None:
            valid, reason = _validate_supersession(conn, supersedes_id, None)
            if not valid:
                return jsonify({'error': f'Supersession validation failed: {reason}'}), 400

        cursor = conn.execute("""
            INSERT INTO drafts (
                draft_type, payload_format, schema_version,
                zone, status,
                source_model, source_session, filename,
                imported_by, checksum,
                payload, proposed_target,
                supersedes_id,
                created_at, updated_at
            ) VALUES (
                ?, ?, '1.0',
                'inbox', 'inbox',
                ?, ?, ?,
                ?, ?,
                ?, ?,
                ?,
                ?, ?
            )
        """, (
            draft_type, payload_format,
            source_model,
            data.get('source_session'),
            data.get('filename'),
            data.get('imported_by'),
            checksum,
            payload,
            data.get('proposed_target'),
            supersedes_id,
            now, now
        ))
        conn.commit()
        draft_id = cursor.lastrowid

        # Mark superseded draft — legality already confirmed above
        if supersedes_id is not None:
            conn.execute("""
                UPDATE drafts
                SET superseded_by = ?, status = 'superseded', updated_at = ?
                WHERE id = ?
            """, (draft_id, now, supersedes_id))
            conn.commit()

        return jsonify({
            'status': 'staged',
            'draft_id': draft_id,
            'zone': 'inbox',
            'checksum': checksum,
            'created_at': now
        }), 201

    except Exception as e:
        conn.rollback()
        return jsonify({'error': 'Staging failed — see server log'}), 500
    finally:
        conn.close()
        

@drafts_bp.route('/list', methods=['GET'])
def list_drafts():
    """Return all non-archived drafts for dashboard display."""
    conn = db_connect()
    try:
        rows = conn.execute("""
            SELECT id, draft_type, status, zone, source_model,
                   source_session, proposed_target, created_at, updated_at
            FROM drafts
            WHERE status != 'archived'
            ORDER BY created_at DESC
        """).fetchall()
        return jsonify([dict(r) for r in rows]), 200
    finally:
        conn.close()


@drafts_bp.route('/<int:draft_id>/action', methods=['POST'])
def draft_action(draft_id):
    """
    Apply a human governance action to a staged draft.
    Actions: approve, reject, supersede, archive
    Commit is a future route — approval and commit are distinct.
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'Request body must be JSON'}), 400

    action = data.get('action', '').strip()
    operator = data.get('operator', '').strip()

    VALID_ACTIONS = {'approve', 'reject', 'supersede', 'archive'}
    if action not in VALID_ACTIONS:
        return jsonify({'error': f'Invalid action. Must be one of: {sorted(VALID_ACTIONS)}'}), 400
    if not operator:
        return jsonify({'error': 'operator is required'}), 400

    now = _now()
    conn = db_connect()
    try:
        draft = conn.execute(
            'SELECT id, status, zone FROM drafts WHERE id = ?', (draft_id,)
        ).fetchone()
        if not draft:
            return jsonify({'error': f'Draft {draft_id} not found'}), 404

        current_status = draft['status']

        # Zone/status transition guard
        if current_status in ('committed', 'archived'):
            return jsonify({
                'error': f'Draft is {current_status} and cannot be actioned'
            }), 409

        if action == 'approve':
            conn.execute("""
                UPDATE drafts SET status='approved', zone='staging',
                approved_by=?, approved_at=?, updated_at=? WHERE id=?
            """, (operator, now, now, draft_id))

        elif action == 'reject':
            reason = data.get('reason', '').strip()
            conn.execute("""
                UPDATE drafts SET status='rejected',
                rejected_by=?, rejected_at=?, rejection_reason=?, updated_at=? WHERE id=?
            """, (operator, now, reason or None, now, draft_id))

        elif action == 'supersede':
            replacement_id = data.get('replacement_id')
            if not replacement_id:
                return jsonify({'error': 'replacement_id required for supersede action'}), 400
            valid, reason = _validate_supersession(conn, draft_id, replacement_id)
            if not valid:
                return jsonify({'error': f'Supersession validation failed: {reason}'}), 400
            conn.execute("""
                UPDATE drafts SET status='superseded', superseded_by=?, updated_at=? WHERE id=?
            """, (replacement_id, now, draft_id))

        elif action == 'archive':
            conn.execute("""
                UPDATE drafts SET status='archived', updated_at=? WHERE id=?
            """, (now, draft_id))

        conn.commit()
        updated = conn.execute(
            'SELECT id, status, zone, updated_at FROM drafts WHERE id=?', (draft_id,)
        ).fetchone()
        return jsonify(dict(updated)), 200

    except Exception as e:
        conn.rollback()
        return jsonify({'error': 'Action failed — see server log'}), 500
    finally:
        conn.close()
