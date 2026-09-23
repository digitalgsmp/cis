# Content in commit `9e0a749` that REQUIRES NEW INDEPENDENT REVIEW

The Card 03 independent PASS does **not** cover the three files below. They are
committed because a fresh checkout would otherwise not build or not expose the
System Context surface, but nothing here should be treated as already reviewed.

---

## 1. `runtime/ui/src/SystemContext.jsx` — `bdab848f…f8b0fb50f`

**Card 03 PASS hash:** `0036ba16…c7c80daf967d` — **does not match.**

**Why it differs.** Card 04's correction round R1 modified this component to
render the `current_focus` field that R1 added to
`tools/state/canonical_state.py::get_current_focus()`. The committed content is
byte-identical to R1's recorded post-image in
`data/agent_handoffs/WB-RECOVERY-04-recovery-drill-closeout/correction-R1/postimage_hashes_round2.txt`.

**Review status.** Card 04 R1's own `completion.json` records
`status: READY_FOR_CODEX_REVIEW`. That review has not returned. The preceding
`CODEX_REVIEW.json` returned `NEEDS_CORRECTION` and did not list this file in
`reviewed_code_hashes` at all. **This content has never been independently
reviewed.**

**No earlier copy exists.** The Card 03-era file was overwritten in place and is
not preserved in any backup directory — see `SOURCE_EVIDENCE_MAP.md`. It was not
reconstructed, because inventing content and labelling it with a historical PASS
would be false.

---

## 2. `runtime/ui/src/SystemContext.test.jsx` — `d30f4b06…5dd42960a2`

**Card 03 PASS hash:** `7c9aa1fa…e6451c2598c474` — **does not match.**

Same cause and same status as above: the R1 post-image, covering the added
`current_focus` rendering. Card 03 recorded 7 tests in this file; R1 recorded 8.
The committed tree runs 8. Treat the eighth test, and any R1-era changes to the
other seven, as unreviewed.

---

## 3. `runtime/container_app.py` — `51029675…572c4314cd`

**Card 03 PASS hash:** `71ca874d…6c03bef24ebadb27` — **does not match, deliberately.**

**Why it differs.** Card 03 hashed the whole working-tree file, and at that
moment the file already carried an unrelated in-flight change from a separate
stream (`data/agent_handoffs/container-kb-health-20260917`): the embedded-Chroma
health check, which imports the still-uncommitted `runtime/chroma_health.py`.
The Card 03 PASS hash therefore cannot be reproduced without also committing
that third stream.

**What was committed instead.** Only the System Context blueprint registration —
an 8-line insertion after the existing `relay_bp` registration. The baseline
curl-based ChromaDB check is left exactly as it was at `3537387`. This was
verified to hash to `51029675…` and to import cleanly with no reference to
`chroma_health`.

**What a reviewer must check.** That this 8-line registration is correct and
sufficient on its own. It is a configuration of `container_app.py` that has
never existed on disk and has never been reviewed, even though both of its
ingredients have been.

**Known consequence.** The live container's `_system_health()` Chroma probe
differs between this committed file and the developer working tree. The Chroma
integration and `runtime/chroma_health.py` remain uncommitted and out of scope.

---

## Summary for the reviewer

| File | Card 03 PASS | Committed | Status |
|---|---|---|---|
| `runtime/api/system_context.py` | `5f7f8662…` | `5f7f8662…` | reviewed |
| `runtime/tests/test_system_context_api.py` | `13ea50af…` | `13ea50af…` | reviewed |
| `runtime/ui/src/App.jsx` | `4abe5594…` | `4abe5594…` | reviewed |
| `runtime/ui/src/api.js` | `e2d767a3…` | `e2d767a3…` | reviewed |
| `runtime/ui/src/index.css` | `d2fcc851…` | `d2fcc851…` | reviewed |
| `runtime/ui/src/SystemContext.jsx` | `0036ba16…` | `bdab848f…` | **NEW REVIEW REQUIRED** |
| `runtime/ui/src/SystemContext.test.jsx` | `7c9aa1fa…` | `d30f4b06…` | **NEW REVIEW REQUIRED** |
| `runtime/container_app.py` | `71ca874d…` | `51029675…` | **NEW REVIEW REQUIRED** |
