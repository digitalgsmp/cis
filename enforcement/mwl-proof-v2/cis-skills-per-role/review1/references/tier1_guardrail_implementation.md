# Tier 1 Guardrail Implementation (2026-07-10)

Commit: `f6a9143` — 10 deterministic guardrails wired into all 6 pipeline phases.

## Architecture

`runtime/abstraction/guardrails.py` — 1008 lines. Each guardrail is a function returning a `GuardrailResult(name, verdict, evidence, summary, mode)`. Verdicts: PASS / FAIL / SKIP. Modes: BLOCK (halts pipeline) or ADVISORY (logs warning).

`run_guardrails()` is the orchestrator — called after each phase output, before storing to `deliberation_rounds`. Which guardrails fire depends on role:

| Role | Guardrails that fire |
|------|---------------------|
| All | output_schema_validator, content_specificity, honesty_reporter |
| brain, draft | + scope_compliance |
| menter | + claim_action_verifier, code_quality_precheck, path_contract_validator |
| review1, review2 | + sycophancy_detector (with other reviewer's output for false consensus check) |
| verify | + claim_action_verifier |
| All (if prompt passed) | tool_result_sandboxing |

## The 10 Guardrails

### BLOCK mode (hard stop on FAIL)

1. **Claim-Action Verifier** — extracts file paths from agent output via regex, checks `os.path.exists()`. Runs `git diff --name-only` against pre-exec HEAD. Catches fabricated files. Key regex patterns: `(?:created|modified|wrote|added)\s+(?:the\s+)?(?:file\s+)?([/\w\-\.]+\.\w{1,6})` and absolute paths `(?:^|[\s"'])(/[a-zA-Z0-9_\-/]+\.\w{1,6})`.

2. **Output Schema Validator** — hard FAIL on unparseable FINAL_JSON, invalid status for role, or missing required fields. Valid statuses per role: brain={READY, NEEDS_CLARIFICATION}, draft={PROPOSAL_READY, REVISION_READY}, reviewer={CONSENSUS_REACHED, OBJECTIONS, ESCALATE}, menter={CONSENSUS_REACHED, DONE, COMPLETE}, verify={PASS, FAIL}.

3. **Path Contract Validator** — checks all absolute paths in output are within `PROJECT_ROOT`. Catches containment violations (agent writing outside project).

### ADVISORY mode (log warning, pipeline continues)

4. **Sycophancy Detector** — keyword + negation-aware critique matching. See technique below.
5. **Scope Compliance Checker** — word overlap between intent and output. Flags scope drift.
6. **Code Quality Pre-Check** — scans code blocks for TODO, bare `except: pass`, hardcoded secrets, stub markers.
7. **Content Specificity Check** — project-specific term matching. Flags boilerplate.
8. **Honesty Reporter** — detects "all tests pass" without evidence patterns.
9. **Unverified Claim Propagator Block** — checks upstream claims are tagged before passing downstream.
10. **Tool Result Sandboxing** — checks prompts for unwrapped tool output (injection risk).

## Key Technique: Negation-Aware Sycophancy Detection

The naive approach counts critique keywords ("issue", "concern", "problem") in reviewer output. But "no issues" is sycophantic, not critical. The fix: for each critique keyword occurrence, check the 15 characters before it for negation patterns (`no `, `nothing `, `without `, `lacks `, `zero `). If negated, don't count as critique.

```python
for kw in _CRITIQUE_KEYWORDS:
    for m in re.finditer(re.escape(kw), output_lower):
        start = max(0, m.start() - 15)
        context = output_lower[start:m.start()]
        if re.search(r'\b(?:no|nothing|without|lacks?|zero)\s+$', context):
            continue  # Negated — don't count
        critique_hits += 1
```

Sycophancy is flagged when: consensus + sycophancy_hits >= 3 + critique_hits == 0, OR consensus + sycophancy_hits >= 2 + critique_hits == 0 + word_count < 50.

## Key Technique: Claim Path Extraction

Three regex patterns extract file paths from agent output:
1. Explicit claims: `(?:created|modified|wrote|added)\s+(?:the\s+)?(?:file\s+)?([/\w\-\.]+\.\w{1,6})` — handles "created the file X.py"
2. Label patterns: `(?:file|path):\s*([/\w\-\.]+\.\w{1,6})`
3. Absolute paths: `(?:^|[\s"'])(/[a-zA-Z0-9_\-/]+\.\w{1,6})` — must be preceded by whitespace/quote/start to avoid matching substrings of relative paths

The third pattern was initially `(/[a-zA-Z0-9_\-/]+\.\w{1,6})` without the preceding-character anchor. This caused false matches: "runtime/api/relay.py" would match "/api/relay.py" as an absolute path. The fix: require the path to be preceded by whitespace, quote, or start of line.

## Wiring Pattern in pipeline_relay.py

After each phase output is received (and trajectory recorded), before validation:

```python
gr_report = run_guardrails(
    phase="brain", role="brain", agent_output=output,
    intent=intent, project_root=PROJECT_ROOT, prompt=prompt,
)
print(gr_report.summary)
record_gate_outcomes(self.conn, run_id, gr_report)
if gr_report.any_blocked:
    # ESCALATE — guardrail caught a fabrication/malformation
    _set_run_status(self.conn, run_id, "ESCALATED")
    return
```

For reviewers, guardrails fire per-reviewer with the other reviewer's output for false consensus detection:

```python
for rrole, rout in (("review1", r1_out), ("review2", r2_out)):
    if rout.strip():
        gr = run_guardrails(
            phase="intent_review", role=rrole, agent_output=rout,
            other_reviewer_output=r2_out if rrole == "review1" else r1_out,
        )
        record_gate_outcomes(self.conn, run_id, gr)
```

## gate_outcomes Table (Migration 0026)

```sql
CREATE TABLE gate_outcomes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    phase TEXT NOT NULL,
    role TEXT NOT NULL,
    guardrail_name TEXT NOT NULL,
    verdict TEXT NOT NULL,        -- PASS, FAIL, SKIP
    mode TEXT DEFAULT 'ADVISORY', -- BLOCK or ADVISORY
    summary TEXT,
    evidence TEXT,
    timestamp TEXT NOT NULL,
    FOREIGN KEY (run_id) REFERENCES workflow_runs(id)
);
```

This is the training dataset for the self-evolving harness (Part 6 of the spec). After 20-30 pipeline runs, analyze false positive rates per guardrail per task type. Promote ADVISORY to BLOCK where FP rate is zero. Demote BLOCK to ADVISORY where FP rate is high.

## API Endpoint

`GET /api/relay/guardrails?run_id=<id>` — returns outcomes for a run (or last 200 if no run_id). Includes per-guardrail stats (PASS/FAIL/SKIP counts).
