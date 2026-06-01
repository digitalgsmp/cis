import sys, os, sqlite3, uuid
sys.path.insert(0, os.path.join(
    os.path.dirname(__file__), '..'))

from api.orchestration import (
    transition_state, get_current_state,
    LifecycleTransitionError, LifecycleStateError
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
    session_id = 'smoke-test'
    results = []

    # a. IDLE → ROUTING
    try:
        transition_state(proposal_id, session_id,
            'IDLE', 'ROUTING', 'eric',
            gate_type='human', db=db)
        results.append('a. IDLE → ROUTING: PASS')
    except Exception as e:
        results.append(f'a. IDLE → ROUTING: FAIL — {e}')

    # b. ROUTING → RESEARCH_ACTIVE
    try:
        transition_state(proposal_id, session_id,
            'ROUTING', 'RESEARCH_ACTIVE', 'orchestrator',
            gate_type='automatic', db=db)
        results.append('b. ROUTING → RESEARCH_ACTIVE: PASS')
    except Exception as e:
        results.append(
            f'b. ROUTING → RESEARCH_ACTIVE: FAIL — {e}')

    # c. ROUTING → EXECUTING (disallowed — must raise)
    p2 = str(uuid.uuid4())
    try:
        transition_state(p2, session_id,
            'IDLE', 'ROUTING', 'eric', db=db)
        transition_state(p2, session_id,
            'ROUTING', 'EXECUTING', 'orchestrator', db=db)
        results.append(
            'c. ROUTING → EXECUTING (disallowed): FAIL '
            '— no exception raised')
    except LifecycleTransitionError:
        results.append(
            'c. ROUTING → EXECUTING (disallowed): PASS '
            '— LifecycleTransitionError raised correctly')
    except Exception as e:
        results.append(
            f'c. ROUTING → EXECUTING (disallowed): FAIL '
            f'— wrong exception: {e}')

    # d. RESEARCH_ACTIVE → RESEARCH_COMPLETE
    try:
        transition_state(proposal_id, session_id,
            'RESEARCH_ACTIVE', 'RESEARCH_COMPLETE',
            'orchestrator', gate_type='automatic', db=db)
        results.append(
            'd. RESEARCH_ACTIVE → RESEARCH_COMPLETE: PASS')
    except Exception as e:
        results.append(
            f'd. RESEARCH_ACTIVE → RESEARCH_COMPLETE: '
            f'FAIL — {e}')

    # e. get_current_state returns RESEARCH_COMPLETE
    state = get_current_state(proposal_id, db)
    if state == 'RESEARCH_COMPLETE':
        results.append(
            'e. get_current_state = RESEARCH_COMPLETE: PASS')
    else:
        results.append(
            f'e. get_current_state: FAIL — got {state}')

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
