# intent-bridge-verify — the clarify→confirm→gate→route artifact

## Claim under verification

Commit `3f7359c` added `tools/intent_bridge.py`. It is claimed to be the
deterministic gate + route of the front door, with these specific behaviors:

1. **It refuses to fire without `--confirm`.** Running it against a valid
   direction (`next`) but no confirmation must print "NOT CONFIRMED" and exit
   non-zero (2), and must NOT write an intent_map row or dispatch anything.

2. **It refuses `implement` outright.** Even WITH `--confirm`, direction
   `implement` must print that it requires Eric Gate approval and exit 2,
   and must NOT dispatch to the implementer.

3. **It records a confirmed intent before routing.** With `--confirm` on a
   non-implement direction, it writes an `intent_map` row with
   `review_decision='CONFIRMED'` and a populated `eric_confirmed_at`, then
   routes to the controlled-vocabulary entry point.

## Evidence reviewed

See the attached evidence file: the two refusal reproductions (live command
output with exit codes) plus `git show 3f7359c --stat` proving the file was
added in that commit.
