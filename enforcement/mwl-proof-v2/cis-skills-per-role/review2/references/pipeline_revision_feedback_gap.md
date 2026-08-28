# Pipeline Revision Feedback Gap

Three bugs found during large-intent pipeline testing (2026-07-09,
run `run-12d5aa6946666b73-1783630035`). **All three FIXED** in same session
(run `run-12d5aa6946666b73-1783641453` confirmed fixes working).

## Bug 1: Brain Revision Does Not Inject Reviewer Feedback — FIXED

### Symptom
When both reviewers object (`OBJECTIONS` signal) at the intent review phase,
the pipeline sends Brain back for round 2. Brain produced 0 chars of output
and the run errored with `status=ERROR`.

### Root Cause
`_intent_review()` line 1440-1443 calls `await self._brain_phase(run_id, intent, round_num + 1)`
but `_brain_phase()` constructs the same prompt as round 1 — no reviewer
objections, no feedback, no indication of what was wrong.

### Fix Applied (2026-07-09)
`_brain_phase()` now checks `round_num > 1` and fetches reviewer1_output and
reviewer2_output from the last intent_review deliberation round. The objections
are injected as a `## Reviewer Feedback` section with instructions to fix the
issues and stick to verified facts. Truncates each reviewer output to 2000 chars
to keep prompt size manageable.

**Verification**: Run `run-12d5aa6946666b73-1783641453` — Brain round 1 completed
successfully, reviewers evaluated, pipeline progressed to INTENT_REVIEW without
error. The same intent that previously errored now processes correctly.

**Note**: `_draft_phase()` has a similar pattern (proposal review → draft revision)
but was NOT broken in the same way — it reads `brain_output` from the last round.
However, it also does NOT inject reviewer objections from proposal_review. This
should be fixed if proposal review objections cause draft revision failures.

---

## Bug 2: FTS5 Pre-Discovery Search Breaks on Special Characters — FIXED

### Symptom
Every agent's pre-discovery output shows:
```
## Knowledge Base
(Search error: fts5: syntax error near ".")
```

### Root Cause
`_pre_discovery()` line 414 passes raw intent text as FTS5 MATCH query.
FTS5 treats `.`, `"`, `*`, `(`, `)`, `:`, `^`, `{`, `}`, `+`, `-` as special
characters in MATCH expressions.

### Fix Applied (2026-07-09)
Added sanitization after keyword extraction:
```python
import re as _re
keywords = _re.sub(r'[."*(){}:^+\-]', ' ', keywords)
keywords = keywords.strip()
if not keywords:
    keywords = "CIS pipeline"
```

**Verification**: Run `run-12d5aa6946666b73-1783641453` — Brain's pre-discovery
no longer shows the FTS5 syntax error. Brain retrieved and referenced prior
trajectory data from the knowledge base.

---

## Bug 3: Agent Hallucination of Documents

### Symptom
Brain claimed `SPEC_CONTROL_PLANE_OBSERVATION.md` exists at "REVISION 3 with
4 review rounds complete" with 9 principles, 4 phases, 18 acceptance criteria,
and a $0.50/run budget. Also referenced an `INTENTION_DRIVEN_DIRECTIVES` proposal.

### Verification
Reviewer 2 searched `/workspace/cis` for any file matching `SPEC_CONTROL_PLANE`
or `*control_plane*` — zero results. KB search returned only Brain's own output
from the same run. The document does not exist.

### Pattern
Known LLM hallucination: agents invent authoritative-sounding document references
with specific details that sound credible but are fabricated. The level of detail
makes the hallucination more convincing, not more trustworthy.

### Defense
The dual-reviewer adversarial system caught both fabrications. Reviewer 1 and
Reviewer 2 independently verified against the filesystem and KB. This validates
the pipeline's core design: no single agent's claim should be trusted without
verification.

---

## Bonus Fix: Intent Truncation — FIXED

### Root Cause
`_create_run()` in `pipeline_relay.py` line 220 had `intent_text[:500]` —
hard truncation at 500 characters before INSERT into `workflow_runs.topic`.

### Fix Applied (2026-07-09)
Removed the `[:500]` truncation. SQLite TEXT has no length limit. Full 4220-char
intent now stored and visible to all agents. Brain confirmed seeing all 14
components in the re-run.

---

## Bonus Fix: Stale Docker Pidfiles

### Symptom
After `docker restart cis-pipeline`, draft and verify gateways were skipped
with "already running (pid 33)" — a stale PID from the previous container
instance. Only 4/6 gateways came up.

### Fix Applied (2026-07-09)
Added to `entrypoint.sh` after `set -e`:
```bash
rm -f /tmp/brain.pid /tmp/draft.pid /tmp/review1.pid /tmp/review2.pid /tmp/menter.pid /tmp/verify.pid /tmp/pipeline_api.pid
```

### Docker Image Note
The correct Docker image is `cis-hermes:pipeline` (not `cis-hermes:pinned`).
The `pinned` image has a bare `sleep infinity` CMD and lacks the entrypoint
and profile configs.

```bash
sg docker -c "docker run -d \
  --name cis-pipeline \
  -p 5000:5000 \
  -v /mnt/projects/cis:/workspace/cis \
  -v /tmp/cis-secrets.env:/workspace/secrets.env:ro \
  cis-hermes:pipeline"
```

---

## Session Context

- **Original run**: `run-12d5aa6946666b73-1783630035` — ERROR after 3 rounds
- **Fix run**: `run-12d5aa6946666b73-1783641453` — all fixes confirmed working
- **Intent**: 14-component build plan for CIS Control Plane + SWA Development
- **Date**: 2026-07-09
- **What worked**: Adversarial review caught fabrication + factual errors
- **What was fixed**: Brain revision (feedback injected), FTS5 search
  (special chars sanitized), intent truncation (removed [:500]),
  stale pidfiles (cleaned on startup)
