# CIS handoff — new Codex session, 2026-10-27

You are the orchestrator for the CIS clean-room rebuild, queue item 4.37 (Brain, B6-A2
series). Do not reconstruct history from old sessions. This is the current state.

## Where the work actually stands

Live tree: `/mnt/projects/cis-clean`, branch `wip/queue-4.37-controller-integration-2026-10-20`.
Reference tree `/mnt/projects/cis` is read-only evidence — do not write to it.

Done and working:
- The Brain sign-in stack is complete and promoted: credential broker, profile projection,
  session layer, Codex thread-resume adapter, turn-runner, sign-in controller, browser
  authorization + callback parser, loopback listener, token exchange, ID-token/JWKS
  validation (PyJWT), composed live transport, `POST /brain/profiles/sign-in`, and runtime
  assembly in `cis serve`.
- First real account sign-in succeeded 2026-10-24 09:43. Profile `primary` is registered and
  READY at `~/.config/cis-clean/chatgpt-plan/credentials/primary.json` (mode 0600 in a 0700
  directory).
- `cis verify` passes: 46/46 modules.

## Open problems, highest first

1. **Nothing is committed.** Last commit Oct 21 17:27. Since then ~20,400 lines across 140
   untracked files, plus 838 changed lines in tracked files — the entire sign-in stack. Not
   pushed. Disposable candidate copies under `/tmp` are the only other copies. Commit and
   push before any new implementation work.

2. **8 tests fail, not 3.** The "same 3 pre-existing baseline failures" line in old session
   notes is stale. Live tree: 8 failures of 1,353 tests. Five are new regressions from the
   sign-in work:
   - `test_the_slice_depends_on_the_standard_library_only` — PyJWT is now a real dependency
   - `test_the_test_suite_itself_needs_no_third_party_package` — ID-token test imports `jwt`
   - `test_no_module_imports_a_network_or_model_library` — new files import `urllib`/`socket`
   - `test_the_provider_l3_boundary_pins_the_openai_exception` — the L3 allowlist was narrowed
     to exactly two files; `chatgpt_plan_browser.py`, `chatgpt_plan_loopback.py`,
     `chatgpt_plan_token_exchange.py` and `chatgpt_plan_id_token.py` were added later and
     never admitted
   - `test_no_source_file_writes_a_path_under_the_reference_environment` —
     `menter_delivery.py` names `/mnt/projects/cis` in its own `PROTECTED_ROOTS` constant
   Pre-existing: two stale README counts (says 38 contracts / 554 tests; actual 46 / 1,353)
   and the OpenRouter/Hermes foreign-backend name.
   Root cause: every card passed its own focused tests and its own Qwen review, but nobody
   re-ran the repository's cross-cutting architecture guards as the file set grew.

3. **PyJWT floor unmet.** `pyproject.toml` declares `PyJWT[crypto]>=2.8,<3`. The interpreter
   running `cis serve` resolves PyJWT **2.7.0** from system packages. No venv. The
   security-critical ID-token validator is below its own declared floor and no test checks it.

4. **Authority record is 4 days behind.** `dev_continuity_events` for 4.37 ends at revision 52
   (Oct 23 00:11). Unrecorded: roughly fifteen promoted cards, the whole sign-in stack, and
   the first live credential. Queue item 4.37 still reads `OPEN`.

5. **The offline demo is no longer offline.** `src/cis/__main__.py` imports the Brain runtime
   at module load, so every command including `cis demo` hard-requires PyJWT. Make it lazy.

6. **Promotion gate still doesn't require the semantic review** (revisions 51/52). Every
   promotion so far was protected by a human-driven Qwen step, not by the pipeline. Acceptable
   while the Workbench is being built; not acceptable once Card Factory output can self-promote.

## Not built yet — keep expectations honest

- Automatic token refresh is **not** implemented. The stored credential will go stale.
- No Brain turn has run through app-server with the real token.
- No chat surface. Today it is a loopback JSON console with a sign-in route. Images and voice
  do not exist. A second person's subscription is supported by the design (separate opaque
  profiles, no merging on email) but there is no picker UI.

## Operating rules — these failed repeatedly, do not relearn them

- **One file plus its test per card.** The nine-file card on Oct 27 did not complete. Raising
  the timeout from 180s to 600s did not fix it and will not; the card size is the problem.
- **Deliver through `cis menter-run`** (64 KiB limit, SHA-256 binding, workspace checks).
- **Poll the receipt file with a shell command, not a model turn.** On Oct 27 the orchestrator
  spent a ~181k-token model call every 30 seconds asking an empty pipe whether it was done.
  That burned half a 5-hour rate-limit window and produced nothing.
- **Compact rarely.** The previous session reached 140 MB and 20 compactions; it degraded
  badly and kept re-deriving settled facts.

## Environment

- Menter worker: systemd user unit `cis-clean-menter.service`, `Restart=always`, socket
  `~/.config/cis-clean/menter/menter.sock`, per-request wall time 600s, $5 cap. Killing the
  PID only bounces it.
- Workbench: `python3 -m cis serve --host 127.0.0.1 --port 8077` is running.
- **Account: Plus plan, premium credit balance 0.** `gpt-5.6-sol` at high reasoning effort is
  configured in `~/.codex/config.toml`. Turns are being refused at entitlement check before
  any inference runs. Add credits or lower the model/effort, or this session fails on its
  first message exactly as the last one did.

## Recommended order

1. Commit and push the whole tree.
2. Fix the five red guards; refresh the README counts to 46 contracts / 1,353 tests.
3. Install PyJWT >= 2.8 for the interpreter that runs `cis serve`, or lower the declared floor.
4. Make the Brain runtime a lazy import so `cis demo` is offline again.
5. Record revisions 53+ : the A2b-A2g series, the promotions, and the first live sign-in.
6. Then resume building: automatic token refresh -> one real Brain turn through app-server ->
   the Workbench chat surface.
