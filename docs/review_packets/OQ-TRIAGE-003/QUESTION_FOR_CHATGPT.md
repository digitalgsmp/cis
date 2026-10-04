# Question for independent review — OQ-TRIAGE-003, the `scope` recovery design

**You are being asked to choose a design, not to verify a commit.** Nothing has been
implemented yet. No code in this area has been changed.

You can read the current source yourself from the GitHub remote:

- repo `digitalgsmp/cis`, branch `master`, at SHA `58cb461b05433ed955dc1e0caf44a6405682f6c6`
- `tools/queue/extract_queue_items.py` — the recovery parser (`extract_scope()` is the subject)
- `tools/queue/render_build_list.py` — the projection generator (`rewrite_scope()` is the subject)
- `tools/queue/queue_set.py` — the only sanctioned classification write path
- `docs/UNIFIED_BUILD_LIST.md` — the canonical projection, 4,123 lines

---

## 1. The architecture you are designing inside

`queue_items` (a SQLite table, 132 rows) is the **authority** for the build queue.
`docs/UNIFIED_BUILD_LIST.md` is a **generated projection** of it, rendered by
`render_build_list.py` and committed on every change so the history is readable.
`extract_queue_items.py --force` is the **documented recovery path**: it rebuilds
the table from that markdown if the database is lost.

Three columns are the authoritative *classification* of an item: `item_num`,
`scope`, `need_status`. The required invariant is that the cycle

```
authority DB  ->  canonical projection  ->  forced recovery  ->  recovered DB
```

preserves all three exactly, **including NULL**.

A prior repair (ADR-PIPE-008) already made this true for `need_status`, and the
mechanism it used is the relevant precedent: the renderer **writes** a canonical
marker `**Need: <STATUS>.**`, and the parser **reads only that marker**. Absence
of a marker recovers as NULL and is legitimate. A marker that is present but
unreadable fails the entire recovery run and imports nothing. Prose is never
consulted.

`scope` has no such marker. It is recovered by reading human prose, and that is
the defect under review.

## 2. What was measured (reproduced on a copy of production; production never written)

Rendering the 132 authoritative rows to the canonical projection and recovering
that projection into a fresh database returns **9 of 132 `scope` values wrong**.
`need_status` mismatches: 0. UNPARSED: 0.

`extract_scope()` has two regexes, tried in order:

```python
shape 1:  \*\*Scope:?\*\*[:\s]*([^\n]+)      -> returns the capture
shape 2:  \*\*Scope[^*]*\*\*\s*([^\n]*)      -> returns the WHOLE match
```

Complete inventory of all 132 item bodies:

| class | count | items | round-trips? |
|---|---|---|---|
| no `**Scope` marker at all, `scope` NULL | 63 | — | yes, correctly NULL |
| matches shape 1, `scope` non-NULL | 61 | — | **58 yes, 3 no** |
| matches shape 1, `scope` **NULL** | 6 | 4.20, 4.28, 4.29, 4.30, 4.31, 4.32 | **no — scope is fabricated** |
| matches only shape 2, `scope` non-NULL | 2 | 1.20, WB.1 | yes, but see §4 |

**All nine failures go through shape 1 — an explicit `**Scope:**` marker.** The
original problem record blamed shape 2's prose fallback. That was wrong, and it
matters, because it means tightening or deleting shape 2 does not fix this.

### The six fabrications

Each of those six bodies contains a `**Scope:**` label that begins a **wrapped
prose paragraph**. Shape 1's `[^\n]+` stops at the first line break, so an
arbitrary line-wrap boundary becomes a classification:

```
**Scope:** Full spec:
`data/agent_handoffs/CIS_WORKBENCH_RECOVERY_CARDS/CARD_01_SINGLE_AUTHORITY_CONTRACT.md`.
Inventory existing DB-backed authority (queue/discovery/decision/closeout
```
→ recovered `scope = "Full spec:"` (items 4.29, 4.30, 4.31, 4.32)

```
**Scope:** An independent reviewer (Codex, matching the WB.1B-2A/2B/3
pattern) reads WB.1A's, WB.1B-1's, and WB.1B-2's own cards, evidence.md and
```
→ recovered `scope = "An independent reviewer (Codex, matching the WB.1B-2A/2B/3"` (item 4.28)

```
**Scope:** CONTAINED PIPELINE — everything below is about the in-container
system, not the host-side tooling that already exists and is out of scope
```
→ recovered `scope = "CONTAINED PIPELINE — everything below is about the in-container"` (item 4.20)

The authority holds **NULL** on all six, because a human correctly declined to
read a prose paragraph as a classification. The read models compute
"partially classified" and "fully classified" from `scope IS NOT NULL`, so a
recovery that invents scope on these six **manufactures false triage completion**.

### The other three

3.29, 3.30 and 3.31 hold a *cleaned or condensed* value in the table while the
projection carries the original, fuller prose line. 3.29 differs by one trailing
period. 3.30 and 3.31 drop parentheticals the prose keeps:

```
authority : runtime/schema/migrations; tools/advisor_review.sh; runtime/orchestrator.py; runtime/mcp_bridge/spine.py
projection: **Scope:** runtime/schema/migrations (new numbered migration for prompt_tokens/completion_tokens); tools/advisor_review.sh (write output + tokens, append-only, unique run_id per invocation); runtime/orchestrator.py:306 (INSERT OR REPLACE → append); runtime/mcp_bridge/spine.py:312 (cis_search_sessions sc.create …
```

**The projection does not represent their authoritative scope at all**, so no
parser, however written, can recover it. These were written by direct SQL before
`queue_set.py` existed; there is no `queue_item_events` row with `field='scope'`
for any item, so `render_build_list.py`'s `rewrite_scope()` — which is gated on
such an event — has never run in production even once.

## 3. Why this cannot be fixed by a better heuristic

`**Scope:**` is **overloaded in this document**: it is used both as a
classification marker and as an ordinary prose paragraph label.

The obvious distinguisher — "a real marker's value is complete on its own line" —
**fails on the real data**. Twelve items with *legitimate, correct, non-NULL*
scope (0.6, 1.25, 1.26, 1.27, 2.33, 2.40, 2.41, 3.21, 3.26, 3.28, 4.17, 4.18)
also carry a `**Scope:**` paragraph that wraps across lines, structurally
identical to the six that must stay NULL. There is no syntactic property that
separates them; the only thing that separates them is a human judgement already
recorded in the `scope` column.

Constraint: this card **may not change the meaning of any existing `scope`
value**, so "clean the nine rows" is not available as the fix. The mechanism has
to be fixed, not the data.

## 4. One further constraint found while sizing the work

Item **1.20's stored `scope` contains an embedded newline** and is itself a
300-character shape-2 truncation artefact:

```
**Scope — REPOINTED 2026-09-07. It is `evaluator` on 8650, not review1 on 8643.**\nThis item was written 2026-09-02, when review1 was the only Qwen in the system and
```

It round-trips today only because shape 2 regenerates the same garbage. Any
single-line canonical marker must therefore **escape newlines** to carry it
exactly, and this card may not clean the value. Item WB.1 is the other shape-2
item: its stored scope is a clean `CONTAINER`, while the only `**Scope`-ish line
in its body is unrelated prose (`**Scope rule:** Complete one connected slice at
a time…`), so shape 2 recovers it only by coincidence of truncation.

Also: `queue_set.py` already refuses a scope containing a newline or over 300
characters on **write**, so only legacy rows can hold such values.

## 5. The proposed design, for you to accept, reject or improve

Apply the `need_status` precedent to `scope`:

1. `render_build_list.py` emits, for **every** item with non-NULL `scope`, a
   **canonical marker whose spelling the document's prose does not already use** —
   proposed `**Queue scope:** <value>` — with `\` and newline escaped so any
   value the column can hold round-trips byte-exactly.
2. Where an existing `**Scope:**` line's value **already equals** the stored
   scope, that line is **relabelled in place** rather than duplicated, so no
   prose is destroyed and ~58 items see only a label change. Where the stored
   value **differs** from the prose (3.29, 3.30, 3.31) or the prose is not a
   scope line at all (1.20, WB.1), the canonical marker is **inserted** and the
   author's prose is left untouched — a reviewer then sees both, which is correct,
   because the prose and the authority genuinely disagree.
3. `extract_queue_items.py` reads scope **only** from the canonical marker.
   Legacy shapes 1 and 2 stop being classification sources entirely. Therefore:
   prose can never create a scope; the six NULL items recover as NULL with their
   prose untouched; no marker means NULL and that is legitimate; two markers in
   one item, or a marker with an empty value or an invalid escape, is
   "present but unreadable" and **fails the whole recovery run before mutating
   anything**, exactly as an unknown `**Need:` token already does.

Known cost: two assertions in `tools/queue/tests/test_queue_set_scope.py` pin the
literal string `**Scope:** …`. Their *claims* (marker inserted, not duplicated,
placed above the item's trailing `---` rule, round-trips) are unchanged; only the
expected spelling moves.

## 6. What we need from you

1. **Is the distinct-spelling canonical marker the right answer**, or is there a
   deterministic way to keep `**Scope:**` itself as the marker that we have
   missed given the 12 legitimate wrapped-paragraph scopes?
2. **Is `**Queue scope:**` the right spelling?** It must be unambiguous against
   this document's existing prose, readable to a human auditing the markdown, and
   able to carry values containing `*` characters (6 values do, e.g.
   `profiles/*.yaml`), which rules out putting the value inside a bold span.
3. **Visible marker or HTML comment?** A `<!-- scope: … -->` line would add zero
   visual noise and matches the file's existing `<!-- state_revision: … -->`
   convention, but it hides the authoritative classification from a human reading
   the document — and prose silently disagreeing with the authority is precisely
   how 3.29/3.30/3.31 drifted. Which risk is worse here?
4. **Relabel-in-place vs always-insert.** Relabelling keeps the document clean but
   means the renderer must still compute the legacy prose value to decide
   equality. Always inserting is simpler but visibly duplicates the scope on ~58
   items. Which do you prefer, and why?
5. **Is escaping the right way to carry 1.20's embedded newline**, or should a
   legacy value that cannot be represented on one line be treated as a
   recovery-integrity failure that must be escalated rather than silently carried?
6. **Does any of this weaken the accepted `need_status` contract** (ADR-PIPE-008),
   which must be preserved exactly: all nine stored statuses round-trip,
   `NO_CHECK_WRITTEN` recovers as three words, unknown token → UNPARSED, UNPARSED
   > 0 fails the run, duplicate markers fail, a failed run mutates zero rows,
   and `queue_set.py`'s recoverability guard fails closed?

## 7. What is explicitly NOT being asked

This is a design review of the `scope` recovery mechanism only. It is **not**
repository-checkpoint verification, **not** approval to run formal Queue Triage
(the prepared 56-item pass remains unapplied), and **not** a request to review
the separate item-identity half of OQ-TRIAGE-003, where the architect has already
decided: the parser gains the `WB.1` heading shape and the
`- **4.10 TITLE.**` bullet shape, and queue item **4.10** — silently lost by the
original extraction, absent from the authority, its content glued inside 4.8's
`body_md`, yet cross-referenced as a real item by eight other items and filling
the only gap in the 4.1–4.19 sequence — is to be recovered into the authority
with `scope` and `need_status` left NULL.
