import sys, os, sqlite3, uuid
sys.path.insert(0, os.path.join(
    os.path.dirname(__file__), '..'))

from api.orchestration import (
    create_dispatch, update_dispatch_inflight,
    complete_dispatch, fail_dispatch, abort_dispatch,
)

DB_PATH = os.path.join(
    os.path.dirname(__file__),
    '../db/cis_memory.db')

def get_db():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    return db

def run():
    db = get_db()
    proposal_id = str(uuid.uuid4())
    results = []

    # a. create_dispatch returns dispatch_id
    try:
        dispatch_id = create_dispatch(
            proposal_id=proposal_id,
            source_actor='orchestrator',
            target_agent='hermes-prime',
            target_endpoint='http://127.0.0.1:8800',
            lifecycle_state_at='ROUTING',
            payload='test payload',
            initiated_by='orchestrator',
            eric_approved=0,
            db=db
        )
        assert dispatch_id and len(dispatch_id) > 0
        results.append('a. create_dispatch: PASS')
    except Exception as e:
        results.append(f'a. create_dispatch: FAIL — {e}')
        db.close()
        for r in results:
            print(r)
        sys.exit(1)

    # b. update_dispatch_inflight adds IN_FLIGHT event
    try:
        update_dispatch_inflight(dispatch_id, db)
        row = db.execute(
            "SELECT event_type FROM dispatch_events "
            "WHERE dispatch_id=? AND event_type='IN_FLIGHT'",
            (dispatch_id,)
        ).fetchone()
        assert row is not None
        results.append('b. update_dispatch_inflight: PASS')
    except Exception as e:
        results.append(
            f'b. update_dispatch_inflight: FAIL — {e}')

    # c. complete_dispatch returns response_message_id
    try:
        rmid = complete_dispatch(
            dispatch_id, 200, 'test response body', db)
        assert rmid and len(rmid) > 0
        results.append('c. complete_dispatch: PASS')
    except Exception as e:
        results.append(f'c. complete_dispatch: FAIL — {e}')

    # d. dispatch_log current_status = SUCCESS
    try:
        row = db.execute(
            "SELECT current_status FROM dispatch_log "
            "WHERE dispatch_id=?",
            (dispatch_id,)
        ).fetchone()
        assert row['current_status'] == 'SUCCESS'
        results.append(
            'd. dispatch_log current_status = SUCCESS: PASS')
    except Exception as e:
        results.append(
            f'd. dispatch_log current_status: FAIL — {e}')

    # e. dispatch_events has PENDING, IN_FLIGHT, SUCCESS in order
    try:
        rows = db.execute(
            "SELECT event_type FROM dispatch_events "
            "WHERE dispatch_id=? ORDER BY id ASC",
            (dispatch_id,)
        ).fetchall()
        types = [r['event_type'] for r in rows]
        assert types == ['PENDING', 'IN_FLIGHT', 'SUCCESS'], \
            f"got {types}"
        results.append(
            'e. dispatch_events order PENDING/IN_FLIGHT/'
            'SUCCESS: PASS')
    except Exception as e:
        results.append(
            f'e. dispatch_events order: FAIL — {e}')

    db.close()
    for r in results:
        print(r)
    failed = [r for r in results if 'FAIL' in r]
    print(f'\n{len(results) - len(failed)}/{len(results)} '
          f'passed.')
    if failed:
        sys.exit(1)

if __name__ == '__main__':
    run()
