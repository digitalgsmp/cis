# CIS Tier 6.2 — gate_closeout_complete.sh v2 Design

Date: 2026-06-07
Status: PROPOSED — not yet committed
Tier: 6.2 (Pipeline Integration — design artifact)
Dependencies: Tier 6.1 design approved; Tier 0-5, gate_runner.sh v1 exist

---

## 1. What v2 Is

`gate_closeout_complete.sh v2` is the deterministic closeout orchestrator. It
replaces `gate_runner.sh` v1 (Tier 2.7) as the master gate script. Where v1
chains Tier 1 gates and exits, v2 runs the full two-phase gate sequence defined
in the Tier 6.1 design, invokes STATE_WRITE between phases, regenerates exports,
and triggers closeout on full success.

v1 remains in place as a lighter-weight pre-commit check. v2 is the closeout
path. Both can coexist.

**What v2 does:**

1. Runs Phase 1 gates (pre-STATE_WRITE verification)
2. Collects all gate results into a structured record
3. If Phase 1 passes: invokes `state_write.py`, passing gate results
4. If STATE_WRITE passes: regenerates exports via `generate_all.py`
5. Runs Phase 2 gates (post-STATE_WRITE verification)
6. If Phase 2 passes: invokes `closeout.sh`
7. Reports final status and exit code

**What v2 does NOT do:**

- Write spine rows (that's state_write.py)
- Write the closeout manifest (that's state_write.py)
- Write the CLOSEOUT_*.md file (that's closeout.sh)
- Decide which gates to run dynamically (configuration is explicit)
- Guess about export regeneration (deterministic timestamp comparison)

---

## 2. Interface

### CLI arguments

```
gate_closeout_complete.sh v2 --run-id <id> --kanban-card-id <id> --node-id <id> [--node-description <text>] [--skip-export]
```

| Argument | Required | Description |
|----------|----------|-------------|
| `--run-id` | Yes | Unique run identifier. Passed to state_write.py, closeout.sh, and generate_all.py. |
| `--kanban-card-id` | Yes | Kanban card ID for pipeline-transition gate marker checks. |
| `--node-id` | Yes | Dependency graph node identifier (e.g., `Tier 6.2`). Used in manifest. |
| `--node-description` | No | Human-readable node description. Defaults to node-id if omitted. |
| `--skip-export` | No | Skip generate_all.py and gate_export_agreement. For nodes that don't change exports. |

### Environment variables

Phase 1 and Phase 2 gate sets are controlled by env vars. A gate is enabled
when its env var is set to a non-empty value.

**Phase 1 gates (pre-STATE_WRITE):**

| Env var | Gate script | Notes |
|---------|-------------|-------|
| (always runs) | gate_git_state.sh | No env var — always runs |
| (always runs) | gate_no_secrets.sh | No env var — always runs |
| `GATE_SERVICE_HEALTH_PORT` + `GATE_SERVICE_HEALTH_EXPECTED` | gate_service_health.sh | Both must be set |
| `GATE_ENDPOINT_URL` + `GATE_ENDPOINT_EXPECTED` | gate_endpoint.sh | Both must be set |
| `GATE_FILE_EXISTS_PATH` | gate_file_exists.sh | Optional `GATE_FILE_EXISTS_MINLINES` |
| `GATE_RESEARCH` | gate_research_artifact_present.sh | Set to any non-empty value |
| `GATE_PROPOSAL` | gate_proposal_schema_valid.sh | Set to any non-empty value |
| `GATE_REVIEW` | gate_review_round_valid.sh | Set to any non-empty value |
| `GATE_CONSENSUS` | gate_consensus_signal_valid.sh | Set to any non-empty value |
| `GATE_ERIC` | gate_eric_approval_present.sh | Set to any non-empty value |
| `GATE_IMPLEMENT` | gate_implementation_artifact_present.sh | Set to any non-empty value |

**Phase 2 gates (post-STATE_WRITE):**

| Env var | Gate script | Notes |
|---------|-------------|-------|
| `GATE_EXPORT_AGREEMENT` | gate_export_agreement.sh | Skipped if `--skip-export` |
| `GATE_DB_STATE` | gate_db_state.sh | Requires `GATE_DB_STATE_RUN_ID` |

**Closeout control:**

| Env var | Purpose | Default |
|---------|---------|---------|
| `STATE_WRITE_SCRIPT` | Path to state_write.py | `tools/state_write.py` |
| `CLOSEOUT_SCRIPT` | Path to closeout.sh | `tools/closeout.sh` |
| `GENERATE_ALL_SCRIPT` | Path to generate_all.py | `tools/export/generate_all.py` |
| `EXPORT_MANIFEST_PATH` | Path to EXPORT_MANIFEST.json | `runtime/manifests/EXPORT_MANIFEST.json` |
| `GATE_RESULTS_FILE` | Temp file for gate results JSON | `/tmp/gate_results_<run_id>.json` |

### Exit codes

| Code | Meaning |
|------|---------|
| 0 | All phases passed. STATE_WRITE completed. Closeout completed. |
| 1 | Phase 1 gate failure. STATE_WRITE not reached. |
| 2 | STATE_WRITE failure. Phase 2 not reached. |
| 3 | Phase 2 gate failure. STATE_WRITE succeeded but postcondition check failed. |
| 4 | Configuration error (missing required arg, invalid env). |

---

## 3. Two-Phase Execution

### Phase 1: Pre-STATE_WRITE

```
1. Validate CLI args (--run-id, --kanban-card-id, --node-id required)
2. Initialize gate_results.json with metadata (run_id, node_id, timestamp_started, git_head)
3. Run always-on gates:
   a. gate_git_state.sh → record result
   b. gate_no_secrets.sh → record result
4. Run configured optional gates (service_health, endpoint, file_exists):
   - If env var set → run gate, record result
   - If env var not set → record SKIP
5. Run configured pipeline-transition gates:
   - For each GATE_RESEARCH, GATE_PROPOSAL, GATE_REVIEW, GATE_CONSENSUS,
     GATE_ERIC, GATE_IMPLEMENT:
     - If env var set → run gate with --kanban-card-id, record result
     - If env var not set → record SKIP
6. If ANY gate FAILED → exit 1. Do not proceed to STATE_WRITE.
7. If ALL gates PASS or SKIP → proceed to STATE_WRITE.
```

Gate results are recorded per this structure for each gate:

```json
{
  "name": "gate_git_state.sh",
  "phase": "pre",
  "command": "tools/gates/gate_git_state.sh",
  "exit_code": 0,
  "status": "PASS",
  "output_excerpt": "PASS: git working tree clean"
}
```

### STATE_WRITE invocation

```
state_write.py \
  --run-id <run_id> \
  --node-id <node_id> \
  --node-description <node_description> \
  --gate-results <gate_results_file> \
  --git-head <git_head>
```

`state_write.py` receives the Phase 1 gate results file. It:
1. Inserts/updates workflow_runs and deliberation_rounds rows
2. Writes the closeout manifest to `runtime/manifests/CLOSEOUT_<run_id>.json`,
   populating the `gates` array from the results file plus recording its own
   `state_write` outcome
3. Exits 0 on success, non-zero on failure

If STATE_WRITE exits non-zero → v2 exits 2. Phase 2 not reached.

### Export regeneration (deterministic condition)

Per the 6.1 implementation note, `generate_all.py` is NOT run unconditionally:

```
if --skip-export flag is set:
    skip export regeneration, skip gate_export_agreement
else:
    compare EXPORT_MANIFEST.json mtime against STATE_WRITE completion timestamp
    if EXPORT_MANIFEST.json exists AND is newer than STATE_WRITE completion:
        skip generate_all.py (already regenerated)
    else if EXPORT_MANIFEST.json is missing OR older than STATE_WRITE completion:
        run generate_all.py --run-id <run_id>
```

The comparison uses `stat -c %Y` on both files. No guessing. If the filesystem
doesn't support mtime (edge case), run generate_all.py (fail-safe: regenerate).

### Phase 2: Post-STATE_WRITE

```
1. Run gate_export_agreement.sh (if not skipped) → record result
2. Run gate_db_state.sh with GATE_DB_STATE_RUN_ID → record result
3. If ANY gate FAILED → exit 3. Closeout not reached.
4. If ALL gates PASS or SKIP → proceed to closeout.
```

Phase 2 gates are appended to the same gate_results.json (with phase="post").

### Closeout invocation

```
closeout.sh \
  --run-id <run_id> \
  --node-id <node_id> \
  --node-description <node_description> \
  --manifest-path runtime/manifests/CLOSEOUT_<run_id>.json
```

`closeout.sh` reads the manifest, writes `CLOSEOUT_<date>_<node>.md`, and exits
0 on success.

v2 records closeout.sh's result as the final gate entry with phase="closeout",
then exits 0.

---

## 4. Gate Results File

Written to `/tmp/gate_results_<run_id>.json`. Passed to state_write.py which
populates the closeout manifest from it.

Structure:

```json
{
  "run_id": "run-20260607-...",
  "node_id": "Tier 6.2",
  "node_description": "gate_closeout_complete.sh v2",
  "timestamp_started": "2026-06-07T20:00:00Z",
  "git_head": "abc123def456...",
  "gates": [
    {
      "name": "gate_git_state.sh",
      "phase": "pre",
      "command": "tools/gates/gate_git_state.sh",
      "exit_code": 0,
      "status": "PASS",
      "output_excerpt": "PASS: git working tree clean"
    },
    {
      "name": "gate_research_artifact_present.sh",
      "phase": "pre",
      "command": "tools/gates/gate_research_artifact_present.sh --kanban-card-id abc123",
      "exit_code": 0,
      "status": "PASS",
      "output_excerpt": "PASS: Research Artifact heading present, content non-empty"
    }
  ]
}
```

v2 writes the `gates` array incrementally as each gate completes. state_write.py
reads this file, adds its own `state_write` block, adds Phase 2 gate results
(if v2 appends them before invoking closeout), and writes the final manifest.

---

## 5. How v2 Differs From gate_runner.sh v1

| Aspect | v1 (gate_runner.sh) | v2 (gate_closeout_complete.sh) |
|--------|---------------------|-------------------------------|
| Purpose | Pre-commit sanity check | Full closeout sequence |
| Phases | Single phase | Two phases with STATE_WRITE between |
| STATE_WRITE | Not invoked | Invoked between phases |
| Export regeneration | Not invoked | Invoked after STATE_WRITE (deterministic) |
| Closeout | Not invoked | Invoked after Phase 2 pass |
| Gate results | stdout only | Structured JSON passed to STATE_WRITE |
| Pipeline gates | None | 6 pipeline-transition gates (configurable) |
| Exit codes | Gate exit code (1, 2) | Distinct codes per phase (1-4) |
| CLI args | None (env only) | --run-id, --kanban-card-id, --node-id required |
| Coexistence | Remains available | Added alongside v1 |

v1 is NOT removed. It remains useful as a lightweight pre-commit check. v2 is
the closeout path invoked when a pipeline run completes and Eric approves.

---

## 6. Error Handling

| Failure point | Exit code | What happens |
|---------------|-----------|--------------|
| Missing required CLI arg | 4 | Print usage, exit |
| Phase 1 gate FAIL | 1 | STATE_WRITE not invoked. gate_results.json contains failing gate. |
| state_write.py FAIL | 2 | Phase 2 not invoked. No manifest written. |
| generate_all.py FAIL | 2 | Phase 2 not invoked. Export regeneration failed. |
| Phase 2 gate FAIL | 3 | Closeout not invoked. Spine rows exist but verification gap. |
| closeout.sh FAIL | 3 | Manifest written, CLOSEOUT_*.md not written. |

Exit code 2 indicates failure in the STATE_WRITE/export phase. Consumers must
inspect the structured results file or durable closeout manifest to distinguish
state_write.py failure from generate_all.py failure — the exit code alone does
not differentiate between them.

In all failure cases (exit 1, 2, 3), the Kanban card status should be set to
`blocked` with the failure reason. This is currently manual — Eric or v4impl
sets the status after seeing the exit code. Future Tier 6.3/6.4 may automate
this.

---

## 7. Example Invocation

Full closeout of a pipeline run:

```bash
GATE_RESEARCH=1 \
GATE_PROPOSAL=1 \
GATE_REVIEW=1 \
GATE_CONSENSUS=1 \
GATE_ERIC=1 \
GATE_IMPLEMENT=1 \
GATE_EXPORT_AGREEMENT=1 \
GATE_DB_STATE=1 \
GATE_DB_STATE_RUN_ID="run-abc123" \
  tools/gates/gate_closeout_complete.sh \
    --run-id "run-abc123" \
    --kanban-card-id "card-xyz789" \
    --node-id "Tier 6.4" \
    --node-description "End-to-end pipeline run"
```

Minimal closeout (git state + no secrets only, no pipeline gates, no exports):

```bash
tools/gates/gate_closeout_complete.sh \
  --run-id "run-minimal-001" \
  --kanban-card-id "card-minimal" \
  --node-id "Tier 6.2" \
  --skip-export
```

---

## 8. Dependencies for Implementation

v2 requires these to exist before it can be built:

| Dependency | Status | Needed for |
|------------|--------|------------|
| gate_git_state.sh | Exists (Tier 1.1) | Phase 1 always-on |
| gate_no_secrets.sh | Exists (Tier 1.4) | Phase 1 always-on |
| gate_service_health.sh | Exists (Tier 1.2) | Phase 1 optional |
| gate_endpoint.sh | Exists (Tier 1.3) | Phase 1 optional |
| gate_file_exists.sh | Exists (Tier 1.5) | Phase 1 optional |
| gate_export_agreement.sh | Exists (Tier 5.6) | Phase 2 |
| gate_db_state.sh | Exists (Tier 4.3) | Phase 2 |
| generate_all.py | Exists (Tier 5.5) | Export regeneration |
| state_write.py | Does NOT exist | STATE_WRITE between phases |
| closeout.sh | Does NOT exist | Final closeout step |
| Pipeline-transition gates (6.4) | Do NOT exist | Phase 1 pipeline markers |

v2 can be built and tested with always-on gates + optional Tier 1 gates. The
pipeline-transition gates (6.4), state_write.py, and closeout.sh are not
blockers — v2 invokes them by path and handles "file not found" as an error.
Implementation can proceed incrementally: build v2, test with existing gates,
add state_write.py, add closeout.sh, add pipeline-transition gates.

---

## 9. Explicitly Out of Scope

- Implementation of v2 code
- Implementation of state_write.py or closeout.sh
- Pipeline-transition gates (6.4)
- Orchestrator Kanban integration (6.3)
- End-to-end pipeline run (6.5)
- Spine schema changes
- ADR-SEED-009
- AGENTS.md/HCP generation changes
