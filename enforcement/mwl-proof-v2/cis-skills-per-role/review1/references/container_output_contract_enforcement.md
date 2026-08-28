# Container Output Contract Enforcement

## Problem

The pipeline had 7 enforcement gaps where agents could produce output
without the required FINAL_JSON format, and the pipeline would immediately
escalate without attempting a repair. The container was detecting
non-compliance but not enforcing compliance.

Eric's framing (2026-07-11):
> "the container is meant to ensure it cooperates. why does it have an option."

## Pattern

Per ADR-SEED-012: if FINAL_JSON is missing or malformed, the orchestrator
issues ONE repair prompt, then escalates if still invalid.

### Guardrail Block vs Format Violation

Two distinct failure modes were incorrectly merged into single `if` conditions:

- **Guardrail block** (policy violation: sycophancy, path violation, loop)
  → escalate immediately. No repair — the agent violated policy, not format.
- **Format violation** (missing/wrong FINAL_JSON status)
  → issue repair prompt. The agent completed its task but didn't follow
  output format. Give it one chance to fix the format.

### The `_enforce_output_contract()` Helper

```python
async def _enforce_output_contract(
    role: str, output: str, expected_statuses: list,
    run_id: str, file_path: str = "",
) -> tuple:
    """If output missing FINAL_JSON, issue ONE repair prompt.
    Returns (output, parsed_dict_or_None)."""
```

- Parses output with `_parse_final_json()`
- If valid status found → return immediately
- If invalid → constructs repair prompt with the expected format template
- Sends repair prompt to same agent via `_call_agent()`
- If repair succeeds → return repaired output + parsed dict
- If repair fails → return original output + None (caller escalates)

## The 7 Fixed Sites (commit c63a5aa)

| Phase | Role | Expected Statuses | Notes |
|-------|------|--------------------|-------|
| Brain | brain | READY, NEEDS_CLARIFICATION | |
| Drafter | draft | PROPOSAL_READY, REVISION_READY | Guardrail block separated |
| Pattern Catalog | brain | READY | |
| Code Review Consensus | review1 | APPROVED, CHANGES_REQUESTED | |
| Menter Code Review | menter | CHUNK_READY | Uses `_call_agent_with_retry` (2 attempts) |
| Menter Execution | menter | CONSENSUS_REACHED, DONE, COMPLETE | Guardrail block separated |
| Verify | verify | PASS, FAIL | Guardrail block separated |

## Wiring Pattern

Each site follows the same 3-block structure:

```python
# 1. Guardrail block — escalate immediately (policy, not format)
if gr_report.any_blocked:
    # ... escalate, return

# 2. Format violation — attempt repair
if not parsed or parsed.get("status") not in expected_statuses:
    output, parsed = await _enforce_output_contract(
        role, output, expected_statuses, run_id)
    _record_trajectory(conn, run_id, role, phase, "REPAIR_PROMPT", output, ...)

# 3. Repair failed — escalate
if not parsed or parsed.get("status") not in expected_statuses:
    # ... escalate, return
```

## Design Principle

The container is an enforcement layer, not just a detection layer.
Detection without enforcement is advisory — the agent can ignore it.
Enforcement means: the agent does not have the option to skip the contract.
The repair prompt is the enforcement mechanism: one chance to comply,
then escalate. The agent never has the option to produce unstructured output
and have it accepted.
