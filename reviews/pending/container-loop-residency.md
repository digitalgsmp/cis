---
card: container-loop-residency
version: 2
status: REFINED (reviewer objections folded in)
author: drafter (host)
created: 2026-09-13
---

> VERSION 2 — CHANGES: folded dual-reviewer objections (2026-09-13, advisor 8649 +
> evaluator 8650, both OBJECTIONS/RIGHT_WORK). Additions: (1) R3 now fixes
> pause_notify.py `REPO` (line 42) and the `/mnt/projects/cis/secrets.env` fallback
> (line 349); (2) R6 verifies the `where_are_we.py` import in-container; (3) mode
> flag renamed `CIS_CONTAINER_MODE` → `CIS_IN_CONTAINER` (avoids collision with the
> existing `CIS_CONTAINER` name var); (4) port range corrected to 8643–8650;
> (5) flagged that the DB-default strings live inside Python heredocs, not shell.

# Container Loop Residency — move the review loop driver off the host

## GOAL_ALIGNMENT

Verbatim Eric directive (2026-09-13):

> "replicate all of that structure into the container. create a card that will
> replicate the needed functionality into the container in detail and hand it to
> the reviewers to refine the card so that menter can execute."

And the correction that frames *why*:

> "pause notify was not suppose to be built on the host in the first place. why
> build on retiring infrastructure."

Source session: this Telegram session, 2026-09-13 (verbatim; not yet indexed in
the KB — reviewers could not verify against the spine, directionally consistent
with km_300336 / km_300214 / km_887666).

Seed intents (verbatim, from spine):

1. "I don't want summaries, I am trying to build a system that works from the raw files."
2. "the LLMs are the tools, I am trying to get LLMs to help me think by contributing factual information and expertise."
3. "I need checks and balance, I am not a coder and if I don't trust something one of you says I have to be able to paste it for another model to evaluate."

## FRAME

The review loop — the code that builds packets, hashes them, calls the two advisor
lineages (advisor 8649 + evaluator 8650), writes `deliberation_rounds`, emits
artifacts, and manages the pause/notify path — **executes on the host**. It
resolves host paths and `docker exec`s into the container only to reach the LLM
gateways.

The host is being retired. This card moves the **execution context** of the loop
driver into the container so the host becomes a pure mount point. The files are
already inside the container via the read-write bind mount — what must move is
path resolution, gateway reach, invocation, and the notify path.

This is the advisor's Block 3, expressed as an executable card.

## CURRENT STATE (evidence-backed)

- Container bind-mounts the repo read-write: `/mnt/projects/cis -> /workspace/cis`
  (`docker inspect` Mounts). There is no separate copy — same files, two paths.
- The loop driver and notify files are already present inside the container:
  - `/workspace/cis/tools/advisor_review.sh` (54171 bytes)
  - `/workspace/cis/tools/pause_notify.py` (15992 bytes)
  - `/workspace/cis/data/cis_memory.db`
- The container has `python3` (with `sqlite3` module), `curl`, `sqlite3`.
  It has **no `docker` binary** — so `docker exec` cannot run inside it.
- `tools/advisor_review.sh` (host-resident) does the following host-bound things:
  - `CONTAINER="${CIS_CONTAINER:-cis-pipeline}"` (line 131)
  - reaches gateways via `docker exec -i -u worker "$CONTAINER" curl ...`
    at three call sites: lines **498, 705, 838**
  - DB default hardcoded to host path in three places (lines **212, 570, 942**):
    `os.environ.get("CIS_SPINE_PATH", "/mnt/projects/cis/data/cis_memory.db")`
  - notify via `python3 "$REPO_ROOT/tools/pause_notify.py" "$ID" "$1"` (line 294)
- `tools/pause_notify.py` hardcodes host paths: DB `/mnt/projects/cis/data/cis_memory.db`
  and env file `/home/eric/.hermes/.env`. Inside the container neither exists.
- entrypoint.sh already starts, inside the container:
  8 gateways (ports 8644, 8645, 8643, 8647, 8646, 8648, 8649, 8650 — note 8643 is
  review1, out of sequence), the Flask pipeline API (port 5000), and the TG2
  two-way `reply_consumer.py`.
- `tools/reply_consumer.py` is already container-resident and pushes via
  `CIS_TG_NOTIFY_TOKEN` (present in container env, verified).

## WORK ITEMS (Menter execution spec)

### R1 — Container path resolution in advisor_review.sh

Change the three DB-default strings (lines 212, 570, 942) from the host path to
the container path:

```
os.environ.get("CIS_SPINE_PATH", "/workspace/cis/data/cis_memory.db")
```

**IMPORTANT (from advisor):** these three strings are inside Python **heredocs**
(`python3 - <<'PY' ... PY`), not shell assignments. Menter must patch the Python
inside the heredoc, not attempt a shell `sed` on the line — the syntax is Python
`os.environ.get`, not bash.

Default, not mandatory: the container path is deterministic; default to
`/workspace/cis/data/cis_memory.db` rather than fail-fast. The R4 wrapper sets it
explicitly anyway.

`REPO_ROOT` resolves correctly when invoked from the container path
(`/workspace/cis/tools/advisor_review.sh` → `/workspace/cis`) — confirm and leave
unchanged; it is the host invocation that poisons it, not the logic.

### R2 — Direct gateway reach (remove docker exec)

Replace the three `docker exec -i -u worker "$CONTAINER" curl ...` call sites
(lines 498, 705, 838) with direct `curl http://127.0.0.1:$port/v1/chat/completions`
— the gateways are local inside the container.

Add a mode guard so the transition window stays safe:

```
if [ "${CIS_IN_CONTAINER:-0}" = "1" ]; then
  # direct local curl
else
  # legacy docker exec path (host invocation)
fi
```

Container mode = direct curl only. Host mode = existing docker exec. The host
path is retained **only** until the container path is proven end-to-end, then
removed (see R5).

NOTE (from evaluator): the flag was originally named `CIS_CONTAINER_MODE`; renamed
to `CIS_IN_CONTAINER` because `CIS_CONTAINER` is already the container-name variable
(line 131) and the near-identical names would collide.

### R3 — Container-aware notify (single push path)

Fix `pause_notify.py` to resolve all three host-bound paths:

1. `REPO` (line 42) — currently hardcoded `/mnt/projects/cis`; change to
   `os.environ.get("CIS_REPO_ROOT", "/workspace/cis")` (same pattern
   `reply_consumer.py` already uses). This is used by `resolve_for()`, `card_ask()`,
   and `build_context()` — all three break in-container without this fix.
2. DB — from `CIS_SPINE_PATH` (default `/workspace/cis/data/cis_memory.db`).
3. Token — from `CIS_TG_NOTIFY_TOKEN` env (already in container). **Also remove or
   repoint the `/mnt/projects/cis/secrets.env` fallback in `send()` (line 349)** —
   that host path doesn't exist in-container; the env var is already set by
   entrypoint.sh sourcing `/workspace/secrets.env`, so the fallback is a dead rung.
   (`read_env` swallows `OSError` silently, so it won't crash — it just won't work.)

Remove the `/home/eric/.hermes/.env` dependency entirely.

Eric's directive is explicit: **one** notify path, container-resident. Do NOT
build a host mirror. `reply_consumer.py` already owns the two-way release; this
card makes `pause_notify.py`'s `send()` the single push path, both resolving the
same container env.

### R4 — Container-side invocation

Add a loop-driver entry point inside the container. Recommendation: **on-demand
invocation, not a self-starting watcher** — CIS is pull-only and never self-starting
(Eric starts each session; nothing fires on its own). Concretely:

- A container-side wrapper, e.g. `/workspace/cis/tools/run_review.sh`, that sets
  `CIS_CONTAINER_MODE=1`, `CIS_SPINE_PATH=/workspace/cis/data/cis_memory.db`,
  and invokes `/workspace/cis/tools/advisor_review.sh "$@"`.
- Document the invocation contract (how Eric or the relay triggers it from inside
  the container). Do NOT auto-loop.

### R5 — Retire host driver

After the container path is proven (R6), reduce the host
`/mnt/projects/cis/tools/advisor_review.sh` to a thin shim:

```
sg docker -c "docker exec -i -u worker cis-pipeline \
  /workspace/cis/tools/run_review.sh \"\$@\""
```

Or delete the host driver entirely. Eric's directive is to retire host execution,
not maintain two drivers. The shim exists only as a one-line bridge until the
container invocation contract is Eric's habit, then it goes.

### R6 — Deterministic verification

Run one card end-to-end **initiated from inside the container**:

1. Packet build from `/workspace/cis/reviews/pending/<id>.md`.
2. advisor (8649) + evaluator (8650) reached via direct local curl (no docker exec).
3. `deliberation_rounds` row written to `/workspace/cis/data/cis_memory.db`.
4. Artifact emitted to `/workspace/cis/reviews/done/<id>.<profile>.response.md`.
5. Notify reaches phone via `CIS_TG_NOTIFY_TOKEN`.
6. `reply_consumer.py` flips the pause row PENDING → CONSENSUS_REACHED.
7. **Verify `where_are_we.py` import works in-container** (from evaluator gap):
   `pause_notify.py`'s `build_context()` does `from where_are_we import latest_slate`
   with `sys.path.insert(0, os.path.join(REPO, "tools"))`. Once REPO is fixed to
   `/workspace/cis`, confirm the import resolves against
   `/workspace/cis/tools/where_are_we.py` (present via bind mount — assert, don't
   assume).

## ACCEPTANCE CRITERIA (deterministic, not self-report)

- A `grep -c 'docker exec'` inside the container against the container-mode code
  path returns 0 for the gateway call sites (no docker exec in container mode).
- One review completes with: a `deliberation_rounds` row + an artifact under
  `/workspace/cis/reviews/done/`, and the review was initiated from inside the
  container (log line shows `127.0.0.1:8649` / `127.0.0.1:8650` reach).
- `pause_notify.py` resolves `/workspace` paths and `CIS_TG_NOTIFY_TOKEN`; no
  `/home/eric` reference remains in the executed path.
- The host no longer executes the loop body (shim or deleted).

## OUT OF SCOPE (separate cards — do not fold in)

- Menter dispatch after ERIC_GATE (advisor Block 1) — `menter-reviewer-connection.md`
- Claude sandbox integration into the relay (advisor Block 2) — `sandbox-claude-code.md`
- TG2 "advance" contract — what "next round" means after a phone release
- The 11 stale non-pause PENDING `deliberation_rounds` (data-consistency item)

## REQUEST TO REVIEWERS

Refine this card for Menter execution. Specifically adjudicate:

1. Is the mode-guard (R2) the right transition mechanism, or should the docker exec
   path be deleted outright with no guard?
2. Should `CIS_SPINE_PATH` be mandatory in container mode, or default to
   `/workspace/cis/data/cis_memory.db`?
3. Is on-demand invocation (R4) correct, or does the loop need a watcher? (Memory
   says pull-only / never self-starting — confirm or correct.)
4. Anything the host loop does today that this card's six work items miss?
