"""
test_be002.py — ALLOV1-BE-002 Action Handler Tests
Uses Flask test client for all tests.
"""
import sys, os, sqlite3, uuid, json

sys.path.insert(0, '/mnt/projects/cis/runtime')

from app import app

DB_PATH = '/mnt/projects/cis/runtime/db/cis_memory.db'
API_KEY = 'ff239b9b04b514b8bc57f166f0eebd8a6a67022575f7886c027b27728e53e6fd'

client = app.test_client()
headers = {
    'X-CIS-API-Key': API_KEY,
    'Content-Type': 'application/json',
}


def get_db():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    return db


def post_action(action, extra=None):
    data = {
        'action': action,
        'proposal_id': proposal_id,
        'session_id': session_id,
        'source_actor': 'eric',
        'eric_approved': 1,
    }
    if extra:
        data.update(extra)
    return client.post('/api/advisor/route',
                       data=json.dumps(data),
                       headers=headers)


def assert_status(resp, expected, label, results):
    if resp.status_code == expected:
        results.append(f'{label}: PASS (status {expected})')
        return True
    else:
        results.append(
            f'{label}: FAIL — expected status {expected}, '
            f'got {resp.status_code}. Body: {resp.get_json()}')
        return False


def assert_body_contains(resp, field, label, results):
    body = resp.get_json() or {}
    if field in body:
        results.append(f'{label}: PASS ({field} present)')
        return True
    else:
        results.append(
            f'{label}: FAIL — {field} missing. Body: {body}')
        return False


def assert_body_value(resp, field, expected, label, results):
    body = resp.get_json() or {}
    val = body.get(field)
    if val == expected:
        results.append(f'{label}: PASS ({field}={expected})')
        return True
    else:
        results.append(
            f'{label}: FAIL — {field} expected={expected}, '
            f'got={val}. Body: {body}')
        return False


def run():
    global proposal_id, session_id
    results = []
    db = get_db()

    # ── T1: reviewer_dispatch — state conflict ──────────────────────────
    proposal_id = str(uuid.uuid4())
    session_id = 'be002-test'
    resp = post_action('reviewer_dispatch', {'payload': 'test proposal'})
    assert_status(resp, 409, 'T1', results)
    assert_body_contains(resp, 'status', 'T1b', results)
    body = resp.get_json() or {}
    if body.get('status') == 'STATE_CONFLICT':
        results.append('T1c: PASS (STATE_CONFLICT in body)')

    # ── T2: approve_draft_directive — state conflict ────────────────────
    proposal_id = str(uuid.uuid4())
    resp = post_action('approve_draft_directive')
    assert_status(resp, 409, 'T2', results)

    # ── T3: reject_proposal — state conflict ────────────────────────────
    proposal_id = str(uuid.uuid4())
    resp = post_action('reject_proposal')
    assert_status(resp, 409, 'T3', results)

    # ── T4: confirm_directive — state conflict ──────────────────────────
    proposal_id = str(uuid.uuid4())
    resp = post_action('confirm_directive',
                       {'directive_text': 'FINAL_DIRECTIVE test',
                        'directive_hash': 'abc123'})
    assert_status(resp, 409, 'T4', results)

    # ── T5: confirm_directive — hash mismatch ───────────────────────────
    # Advance proposal to DIRECTIVE_AUTHORED with a known hash
    proposal_id = str(uuid.uuid4())
    known_hash = ('e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca'
                  '495991b7852b855')  # SHA-256 of empty
    db.execute(
        """INSERT INTO lifecycle_events
           (proposal_id, session_id, from_state, to_state,
            gate_type, initiated_by, timestamp, directive_hash,
            eric_approved)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (proposal_id, session_id, 'IDLE', 'DIRECTIVE_AUTHORED',
         'human', 'eric', '2026-01-01T00:00:00', known_hash, 1))
    db.commit()
    resp = post_action('confirm_directive',
                       {'directive_text': 'WRONG TEXT',
                        'directive_hash': 'wrong_hash'})
    assert_status(resp, 409, 'T5', results)
    body = resp.get_json() or {}
    if 'hash' in str(body.get('error', '')).lower():
        results.append('T5b: PASS (hash mismatch in error)')

    # ── T6: revise_directive — state conflict ───────────────────────────
    proposal_id = str(uuid.uuid4())
    resp = post_action('revise_directive')
    assert_status(resp, 409, 'T6', results)

    # ── T7: execute_directive — unauthorized source_actor ───────────────
    proposal_id = str(uuid.uuid4())
    resp = client.post('/api/advisor/route',
                       data=json.dumps({
                           'action': 'execute_directive',
                           'proposal_id': proposal_id,
                           'session_id': 'test',
                           'source_actor': 'hermes-v4pro',
                           'eric_approved': 0,
                           'directive_text': 'FINAL_DIRECTIVE test',
                           'directive_hash': 'abc123',
                       }),
                       headers=headers)
    # T7: should return 403 (unauthorized)
    if resp.status_code == 403:
        results.append('T7: PASS (status 403)')
    else:
        results.append(
            f'T7: FAIL — expected 403, got {resp.status_code}. '
            f'Body: {resp.get_json()}')

    # ── T8: execute_directive — state conflict ──────────────────────────
    proposal_id = str(uuid.uuid4())
    resp = post_action('execute_directive',
                       {'directive_text': 'FINAL_DIRECTIVE test',
                        'directive_hash': 'abc123'})
    # T8: should return 403 or 409 (enforcement or state check)
    if resp.status_code in (403, 409):
        results.append(f'T8: PASS (status {resp.status_code})')
    else:
        results.append(
            f'T8: FAIL — expected 403 or 409, got {resp.status_code}. '
            f'Body: {resp.get_json()}')

    # ── T9: reject_proposal — valid state ───────────────────────────────
    proposal_id = str(uuid.uuid4())
    # Advance to DRAFT_READY via direct insert
    db.execute(
        """INSERT INTO lifecycle_events
           (proposal_id, session_id, from_state, to_state,
            gate_type, initiated_by, timestamp, eric_approved)
           VALUES (?,?,?,?,?,?,?,?)""",
        (proposal_id, session_id, 'IDLE', 'DRAFT_READY',
         'human', 'eric', '2026-01-01T00:00:00', 1))
    db.commit()
    resp = post_action('reject_proposal')
    assert_status(resp, 200, 'T9', results)
    body = resp.get_json() or {}
    if body.get('lifecycle_state') == 'IDLE':
        results.append('T9b: PASS (lifecycle_state=IDLE)')
    else:
        results.append(
            f'T9b: FAIL — lifecycle_state should be IDLE, '
            f'got {body.get("lifecycle_state")}')

    # ── T10: action dispatch routing — unknown action falls through ─────
    proposal_id = str(uuid.uuid4())
    resp = post_action('unknown_action_xyz')
    # Should NOT crash — falls through to classify_route
    if resp.status_code not in (404, 500):
        results.append(
            f'T10: PASS (status {resp.status_code} — no crash)')
    else:
        results.append(
            f'T10: FAIL — unexpected status {resp.status_code}. '
            f'Body: {resp.get_json()}')

    db.close()

    for r in results:
        print(r)
    failed = [r for r in results if 'FAIL' in r]
    print(f'\n{len(results) - len(failed)}/{len(results)} passed.')
    if failed:
        sys.exit(1)


if __name__ == '__main__':
    run()
