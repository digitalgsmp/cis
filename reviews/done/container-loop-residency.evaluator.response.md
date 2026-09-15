# Advisor review — container-loop-residency

- packet: `reviews/pending/container-loop-residency.md`
- advisor: evaluator on port 8650
- run tag: container-loop-residency @ 2026-09-13T11:31:53-05:00
- at: 2026-09-13T11:35:58
- prompt_tokens: 190975
- completion_tokens: 7307
- total_tokens: 198282
- token source: gateway response usage
- model turns: (see gateway agent.log for the per-turn tool-use breakdown)
- finish_reason: stop

---

Here is my verified review.

---

## EVIDENCE VERIFICATION

All line-number claims in the card check out:

- `docker exec` call sites at lines 498, 705, 838 — VERIFIED (cis_search_files, pattern "docker exec").
- `CIS_SPINE_PATH` host-path defaults at lines 212, 570, 942 — VERIFIED (cis_search_files, pattern "CIS_SPINE_PATH").
- `CONTAINER` variable at line 131: `CONTAINER="${CIS_CONTAINER:-cis-pipeline}"` — VERIFIED.
- `pause_notify.py` line 41: DB default `/mnt/projects/cis/data/cis_memory.db` — VERIFIED.
- `pause_notify.py` line 43: `ENV_FILE` default `/home/eric/.hermes/.env` — VERIFIED.
- `REPO_ROOT` at advisor_review.sh line 130 uses `$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)` — relative resolution, so it self-corrects when invoked from `/workspace/cis/tools/`. Card's claim is CORRECT.
- entrypoint.sh starts 8 profiles (brain/draft/review1/review2/menter/verify/advisor/evaluator) on ports 8644/8645/8643/8647/8646/8648/8649/8650 — VERIFIED. Advisor is 8649, evaluator is 8650.
- `tools/reply_consumer.py` exists (8380 bytes), entrypoint.sh lines 211-220 start it as a restart-on-exit loop polling `CIS_TG_NOTIFY_TOKEN` — VERIFIED.
- Advisor review.sh calls `pause_notify.py` at line 294 — VERIFIED.

---

## TWO GAPS THE CARD MISSES

**Gap 1: `REPO` in `pause_notify.py` (line 42)**

R3 addresses DB and token resolution but ignores the hardcoded `REPO = "/mnt/projects/cis"` at line 42. This variable is used in three functions: `resolve_for()` (line 134), `card_ask()` (line 214), and `build_context()` (line 249 — dynamic import of `where_are_we.py`). All three will silently produce empty results or import failures when run inside the container, because `/mnt/projects/cis` does not exist there. R3 must also fix REPO to resolve from the container path (e.g., `os.environ.get("CIS_REPO_PATH", "/workspace/cis")`).

**Gap 2: `secrets.env` fallback in `send()` (line 349)**

`pause_notify.py` line 348-349 falls back to `read_env("/mnt/projects/cis/secrets.env")`. This is a host path that won't exist in the container. The `read_env` function swallows `OSError` silently, so this won't crash — but it means the token resolution chain has a dead rung in container mode. The card's R3 should explicitly address this: either remove the fallback (since `CIS_TG_NOTIFY_TOKEN` is already in the container env per entrypoint.sh sourcing `/workspace/secrets.env`) or repoint it to `/workspace/secrets.env`.

---

## ANSWERS TO THE REVIEWER QUESTIONS

**Q1 — Mode guard or delete outright?**
Mode guard is correct. The host driver is the only working path today. Deleting outright before the container path is proven end-to-end risks a full outage of the review loop with no rollback. The guard is three lines of cheap insurance. The card's R5 already commits to retiring the host path after R6 proves the container path — that sequencing is sound.

**Q2 — Mandatory or default?**
Default to `/workspace/cis/data/cis_memory.db` is correct. The container path is deterministic — there is exactly one correct value. Making it mandatory adds friction without adding safety. The wrapper script (R4) sets it explicitly anyway, so the default is only hit if someone invokes the script bare-handed, at which point the correct default is better than a cryptic error.

**Q3 — On-demand or watcher?**
On-demand is correct. The entire CIS architecture is pull-only. The entrypoint.sh already demonstrates this: it starts services but never triggers work. A watcher would be a new autonomous process, contradicting the project's operator-pull principle. Eric starts each session — the card correctly preserves this contract.

**Q4 — Anything missed?**
Yes, the two gaps above (REPO variable and secrets.env fallback). Additionally, one minor naming concern: the card proposes `CIS_CONTAINER_MODE` as the mode flag, but the existing code already uses `CIS_CONTAINER` as the container-name variable (line 131). These are different env vars, but the similar names will cause confusion. Recommend renaming the mode flag to `CIS_REVIEW_MODE` or `CIS_IN_CONTAINER` to avoid ambiguity.

---

## MINOR CORRECTION

The card says "8 gateways (8644–8650)." The actual port assignment is 8644, 8645, 8643, 8647, 8646, 8648, 8649, 8650 — port 8643 falls outside that range. This doesn't affect the review loop (which only uses 8649 and 8650), but the summary is technically imprecise. Cosmetic, not blocking.

---

## VERDICT

The card is sound in structure and correctly scoped. Two real gaps (REPO variable, secrets.env fallback) need to be added to R3 before handing to Menter. The mode guard, default path, and on-demand invocation are all correct choices. Approve with those two additions.
