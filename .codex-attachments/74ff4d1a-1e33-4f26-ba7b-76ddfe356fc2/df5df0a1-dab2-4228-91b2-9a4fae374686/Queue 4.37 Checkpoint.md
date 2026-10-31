CIS clean-room rebuild · queue item 4.37 · Brain B6-A2

# Queue 4.37 Checkpoint

In the last two days the sign-in stack for Brain was built end to end, one small card at a time, and this morning it worked for real: **profile `primary` is registered and READY** against your ChatGPT account. The build itself is in good shape. The record around it is not — nothing is committed, five architecture guards are red, and CIS's own authority log stopped two days ago.

Report 2026-10-24 Window Oct 22 19:00 → Oct 24 09:44 CDT Tree /mnt/projects/cis-clean

Where things actually stand

## Independently re-checked, not quoted

First live sign-in READY Profile `primary`, stored 09:43 today, owner-only

cis verify 46 / 46 modules Blueprint and all module contracts valid

Test suite 8 failing of 1,353 Reported as 3 — five are new since Thursday

Committed 0 of \~20,400 lines Last commit Oct 21 17:27 · nothing pushed

Authority record rev 52 Last written Oct 23 00:11 · \~15 cards unrecorded

What was built — in dependency order, because each unit needed the one before it

## From credential store to a real account

Every unit below went through the same four steps: Claude/Menter implemented it in a disposable copy under `/tmp`, a deterministic run proved the tests, Qwen read the finished code, and only then were the exact reviewed bytes copied into the live tree under a hash check. Nothing was promoted on a failing review.

1. 01

   Wed evening → Thu morning

   ### Credentials, profiles and sessions
   - **Protected credential broker** — per-account records with their own opaque profile ID, owner-only files, atomic replace, one-use token leases, serialized refresh. Two people's subscriptions can never merge, even on the same email. chatgpt_plan_credentials.py
   - **Workbench profile picker projection** — a list surface that exposes labels and readiness only, never a token. Qwen caught two `BaseException` catches swallowing Ctrl+C; corrected.
   - **Brain session layer** — turns serialized per session, different sessions concurrent, clean close, turn/close races covered. session.py
2. 02

   Thursday midday → evening

   ### Codex turn plumbing
   - **Thread-resume adapter** — resumes an existing Codex app-server thread inside containment. codex_thread_resume.py
   - **Brain turn-runner and factory wiring** — the layer that will actually run a Brain turn once a token is available.
3. 03

   Thursday night → Friday 09:16

   ### The sign-in machinery, in nine small pieces
   - **Deterministic sign-in controller** — mints state, nonce and PKCE per attempt, one explicit profile, no "last used" anywhere. chatgpt_plan_sign_in.py
   - **Authorization URL and callback parser** — fixed identity `CIS Workbench`, immutable callback object. chatgpt_plan_browser.py
   - **Loopback listener** — binds before the browser opens, validates the callback, one request only. chatgpt_plan_loopback.py
   - **System-browser orchestration** — listener first, browser once, typed secret-safe failures. chatgpt_plan_authorization.py
   - **Code-for-token exchange** — exact OpenAI token endpoint and form, correct `invalid_grant` handling. chatgpt_plan_token_exchange.py
   - **ID-token and JWKS validation** — signature, issuer, audience, expiry, subject and nonce, all inside maintained PyJWT; no handwritten crypto. Missing `chatgpt.tokens.use.direct` holds sign-in rather than silently degrading. chatgpt_plan_id_token.py
   - **Composed live transport** — browser → exchange → validation → registration, joined in one place. chatgpt_plan_live_transport.py
   - **Workbench endpoint** — `POST /brain/profiles/sign-in` with explicit `profile_id`, secure runtime entropy, safe fields only in the response.
   - **Runtime assembly in `cis serve`** — real broker, credential directory, stable host ID, callback port 1455, loopback-only binding. Qwen found two genuine host-ID race defects *despite green tests* (a symlink swap window and an empty partially-written file); both fixed with `O_NOFOLLOW` reads and atomic publication. chatgpt_plan_runtime.py
4. 04

   Friday 09:32 → 09:44

   ### First real account sign-in
   - Workbench started on `127.0.0.1:8077`; host ID written 09:32; one sign-in attempt for profile `primary`.
   - First attempt failed cleanly — the system browser opened nothing visible, then a later Firefox approval came back after the 180-second listener had closed. Nothing was stored, and the stale code was correctly discarded rather than reused.
   - Second attempt completed. `~/.config/cis-clean/chatgpt-plan/credentials/primary.json` exists at mode `0600` inside a `0700` directory. I confirmed the file and its permissions; I did not open it.

What needs your attention

## Findings, worst first

Critical

### Two days of work exists in one working tree and nowhere else

The last commit on `wip/queue-4.37-controller-integration-2026-10-20` is **Oct 21 17:27**. Since then: **140 untracked files, about 20,400 lines**, plus 838 changed lines in tracked files — the entire Brain sign-in stack, its contracts and its tests. None of it is committed and none is pushed. The only other copies are eleven disposable candidate trees under `/tmp`, which a reboot deletes. One bad `git clean`, one full disk, one wrong promotion script and Wednesday-to-Friday is gone.

High

### Eight tests fail, not three — and five are new

Each card was reported against "the same three pre-existing baseline failures." That line is now stale: the live tree fails **eight** of 1,353. Three are the known ones; five are regressions introduced by this week's own work. Every individual card passed its own focused tests and its own Qwen review — nobody re-ran the repository's cross-cutting architecture guards as the set of files grew. This is precisely the class of defect a per-card review cannot see.

| Failing guard | Age | Cause |
| --- | --- | --- |
| test_the_slice_depends_on_the_standard_library_only | New | PyJWT is now a real dependency; the guard still asserts stdlib-only. |
| test_the_test_suite_itself_needs_no_third_party_package | New | The ID-token test imports `jwt`. |
| test_no_module_imports_a_network_or_model_library | New | Four new files name `openai` hosts or import `urllib`/`socket`. |
| test_the_provider_l3_boundary_pins_the_openai_exception | New | The allowlist was narrowed to exactly two files; browser, loopback, token-exchange and id-token were added later and never admitted. |
| test_no_source_file_writes_a_path_under_the_reference_environment | New | `menter_delivery.py` names `/mnt/projects/cis` in its own `PROTECTED_ROOTS` guard — a safety constant tripping a safety test. |
| test_the_readme_counts_contracts_and_migrations_correctly | Pre-existing | README says 38 contracts; there are 46. |
| test_the_stated_test_count_is_the_real_test_count | Pre-existing | README says 554 tests; there are 1,353. |
| test_no_foreign_backend_is_named_anywhere_in_the_slice | Pre-existing | OpenRouter/Hermes names above the boundary; already recorded. |

High

### The crypto library in use is older than the version the project requires

`pyproject.toml` declares `PyJWT[crypto]>=2.8,<3` — the one deliberate exception to stdlib-only, chosen so ID-token verification is never handwritten. The interpreter that actually runs `cis serve` resolves **PyJWT 2.7.0** from the system packages, because there is no virtual environment and nothing was installed. The security-critical validator is running below its own declared floor, and no test checks the version.

Medium

### CIS's own record stops two days before the work does

The continuity log for 4.37 ends at **revision 52, written Oct 23 00:11** — the reconciliation of the reviewer-lineage proposal. Everything after it is unrecorded: roughly fifteen promoted cards, the whole sign-in stack, and the first live credential. Queue item 4.37 still reads `OPEN` with no status change. The system built to remember what it did has no entry for its most important two days.

Medium

### The offline demo is no longer offline-capable

`src/cis/__main__.py` imports the Brain runtime at module load, so *every* command — including `cis demo`, the deterministic offline showcase — now hard-requires PyJWT. On any machine without it, four demo-narration tests fail at import. A lazy import inside the `serve` path restores the separation.

Medium

### The promotion gate still doesn't require the review it depends on

Revisions 51 and 52 established this and it remains open: `promotion.py` can reach `PROMOTION_AUTHORIZED` without a bound post-implementation semantic review from an independent lineage. Every promotion in the last two days was protected by you and Codex driving Qwen *manually* — the pipeline itself would not have insisted. That's a reasonable deferral while the Workbench is being built; it stops being reasonable the moment Card Factory output can promote itself.

Process

### Card delivery wasted real time, and is now partly fixed

Roughly three in four cards failed to complete at some point this week for mechanical reasons: Claude stuck in plan mode, the sandbox refusing temporary directories, oversized cards exceeding a session, a 15-minute timeout cutting off work that was already done, and an OpenRouter 401 that blocked Qwen for part of Thursday. Two durable fixes landed: cards now run in `acceptEdits` mode, and `cis menter-run` gives card delivery a real CLI with a 64 KiB limit, SHA-256 binding and workspace checks. The size discipline is still a judgment call rather than an enforced rule.

Not built yet — so expectations stay honest

## What the sign-in does not get you

Automatic token refresh is **not implemented**. The broker has the machinery and the tests, but nothing is wired to refresh on expiry in the running Workbench, so the stored credential will go stale.

No Brain turn has run through the app server with this token yet — the thread-resume adapter and turn-runner exist and are tested, but the join is untested against a live account.

The chat surface you want — typing to Brain in the Workbench, dropping in images, talking to it — does not exist. What exists today is a JSON console on loopback with a sign-in route. Your coworker's separate subscription is *supported by the design* (separate opaque profiles, no shared state, no merging on email), but there is no picker UI to choose between them.

Recommended order

## What to do next

1. **Commit and push the whole tree before anything else.** A snapshot branch is enough. This is the only item that protects everything above it.
2. **Re-baseline the five red guards.** Admit the four new provider files to the L3 allowlist truthfully, resolve the `menter_delivery` protected-roots collision, and refresh the README's 46 contracts and 1,353 tests. Until that's done the suite can't be used as a gate, and "3 baseline failures" will keep hiding new breakage.
3. **Install PyJWT ≥ 2.8 in the interpreter that runs `cis serve`** — or lower the declared floor to what's actually there. Don't leave the validator below its own requirement.
4. **Make the Brain runtime a lazy import** so `cis demo` and the offline tests stop depending on a third-party package.
5. **Record revisions 53 onward:** the A2b → A2g series, the promotions, and the first live sign-in. The authority log is the asset; two days of silence in it is a bigger loss than any single card.
6. **Then resume the build:** automatic token refresh → one real Brain turn through app-server → the Workbench chat surface.

How this was checked

Facts above were re-derived from the repository and databases, not taken from the session logs. The sequence of cards, the review verdicts and the sign-in narrative come from the Codex orchestration transcript; counts, failures, permissions and record state come from these runs:

git -C /mnt/projects/cis-clean log / status / diff --shortstat PYTHONPATH=src python3 -m cis verify PYTHONPATH=src python3 -m unittest discover -s tests -t . python3 -c "import jwt; print(jwt.\_\_version\_\_)" sqlite3 /mnt/projects/cis/data/cis_memory.db (read-only: dev_continuity_events, queue_items, project_state)

The credential file was checked for existence, ownership and mode only. Its contents were not read.

Window reviewed: 2026-10-22 19:00 → 2026-10-24 09:44 America/Chicago · Live tree /mnt/projects/cis-clean at 588f4c9 plus uncommitted work · Reference tree /mnt/projects/cis untouched.