# Tier 3 Guardrail Implementation

**Commit:** `2f57391` (2026-07-10)
**Module:** `runtime/abstraction/guardrails.py` (lines ~1716-2518)
**Total guardrails:** 10 (3 BLOCK, 7 ADVISORY)
**Combined total:** 30 guardrails across all tiers (9 BLOCK, 21 ADVISORY)

## Guardrail Inventory

### BLOCK Guardrails (hard stop on FAIL)

| # | Name | Catches | Implementation |
|---|------|--------|----------------|
| 21 | Intent Compliance Checker (§2.11) | Stub implementations, syntax errors | AST parse + body analysis: `pass`-only, `return None`, `return {}`, `return []` |
| 27 | Evidence Hash Chain (§1.4) | Fabricated completion narratives | `git rev-parse HEAD` before/after + `git diff --name-only` + file mtime freshness |
| 28 | Context Injection Gate (§1.5) | Missing context in agent prompts | Required markers: `ROLE_OVERLAY`, `PROJECT_BRIEF`, `KB_CONTEXT` + 500 char minimum |

### ADVISORY Guardrails (log warnings, pipeline continues)

| # | Name | Catches | Implementation |
|---|------|--------|----------------|
| 22 | Semantic Spot Check (§2.7) | Alignment faking, evaluator gaming | Verify claimed functions exist in claimed files via `re.search(r'\bdef\s+{func_name}\s*\(')` |
| 23 | Consensus Independence Check (§2.17) | False consensus from shared blind spots | Reasoning keyword Jaccard overlap + shared evidence citation detection |
| 24 | Hardcode Detector (§2.22) | Hardcoded values instead of logic | AST: `ast.Assign` with `ast.Constant` values matching key/secret/token/port/timeout patterns |
| 25 | Error Handling Checker (§2.23) | Missing error handling | AST: functions with external calls (`.get()`, `.post()`, `open()`, `.execute()`) but no `ast.Try` |
| 26 | Position Randomizer (§2.6) | Positional bias in option ordering | Regex detection of multi-option prompts (Option A/B, Choice 1/2, A) B)) |
| 29 | Raw Source Preservation (§1.10) | Summarization losing details | Query `deliberation_rounds` columns for length < 50 or ending with `...` |
| 30 | Bias Drift Detector (§1.1) | Enterprise bias creeping in | Keyword scan for 30+ enterprise/legacy terms (microservice, kubernetes, CQRS, etc.) not in intent |

## Key Techniques

### AST-Based Code Analysis (Guardrails 21, 24, 25)

All three use Python's `ast` module to parse code blocks extracted from agent output:

```python
import ast as _ast

code_blocks = re.findall(r'```python\n(.*?)```', agent_output, re.DOTALL)
for code in code_blocks:
    try:
        tree = _ast.parse(code)
    except SyntaxError:  # NOT _ast.SyntaxError — see pitfall below
        issues.append(f"SyntaxError: {e.msg}")
        continue
    for node in _ast.walk(tree):
        # Analyze: FunctionDef, Assign, Return, Call, Try, ExceptHandler
```

**Stub detection** (Guardrail 21): After stripping docstrings (`body[0]` is `ast.Expr` with `ast.Constant` string), check if function body is a single `ast.Pass`, `ast.Return` with `None`, or `ast.Return` with empty `ast.Dict`/`ast.List`.

**Hardcode detection** (Guardrail 24): Walk for `ast.Assign` where target name matches `(?:key|secret|token|password|url|host|port)` regex and value is `ast.Constant` with len > 20 (strings) or in range 1-65536 (ints matching port/timeout patterns).

**Error handling** (Guardrail 25): Walk for `ast.FunctionDef` containing `ast.Call` nodes with attribute names matching `(get|post|put|delete|fetch|read|write|execute|connect|open|request)` — these are external calls. If the function has no `ast.Try` descendant, flag it.

### Evidence Hash Chain (Guardrail 27)

```python
pre_head = subprocess.run(["git", "rev-parse", "HEAD"], ...).stdout.strip()
# ... after agent runs ...
current_head, _ = _run_cmd(["git", "rev-parse", "HEAD"], cwd=project_root)
diff_output, _ = _run_cmd(["git", "diff", "--name-only", pre_head], cwd=project_root)
```

Checks three things:
1. **Files changed** — `git diff --name-only` returns empty = no work done (fabrication)
2. **File freshness** — `os.path.getmtime()` within 1 hour = recent work
3. **HEAD movement** — optional post_exec_head comparison for commit verification

### Consensus Independence (Guardrail 23)

Two-layer check:
1. **Reasoning keyword overlap** — both reviewers using the same reasoning patterns (`however`, `therefore`, `missing`, `suggest`) with Jaccard > 0.85 AND text similarity > 0.5 = shared blind spots
2. **Shared evidence citation** — both reviewers citing same `(?:line|file|function|page) \d+` references with > 80% overlap

### Bias Drift (Guardrail 30)

Maintains two sets:
- `_BIAS_KEYWORDS` — 30+ enterprise/legacy terms: `microservice`, `kubernetes`, `docker-compose`, `helm`, `istio`, `service mesh`, `cqrs`, `event sourcing`, `domain-driven design`, `spring boot`, `soap`, `wsdl`, etc.
- `_CIS_LEGITIMATE` — terms that are OK in CIS context even if they sound enterprise-y: `docker`, `container`, `flask`, `sqlite`, `pipeline`, `spine`, `relay`, `guardrail`, `schema`, etc.

Flags any bias keyword in output that is NOT in the intent AND NOT in the legitimate set.

## Critical Pitfall: `SyntaxError` vs `_ast.SyntaxError`

**`SyntaxError` is a Python builtin, not an `ast` module attribute.** The `ast` module is imported as `_ast` in guardrails.py. The following code FAILS at runtime:

```python
except _ast.SyntaxError as e:  # AttributeError: module 'ast' has no attribute 'SyntaxError'
```

The correct pattern:

```python
except SyntaxError as e:  # Works — SyntaxError is a builtin
```

This affected three guardrails (21, 24, 25) and was caught during unit testing before deployment. The Pyright type checker flagged it as a diagnostic but the lint check passed — only runtime testing caught it. **Always test guardrail functions with `execute_code` before wiring them into the pipeline.**

## Wiring into pipeline_relay.py

Tier 3 guardrails are dispatched by `run_guardrails()` based on role:

```python
# In run_guardrails() orchestrator (guardrails.py):

# Tier 3: Intent compliance (AST check for stubs) — Menter + Verify only
if role.lower() in ("menter", "verify"):
    report.results.append(guardrail_intent_compliance(agent_output, project_root))

# Tier 3: Semantic spot check — Menter + Verify only
if role.lower() in ("menter", "verify"):
    report.results.append(guardrail_semantic_spot_check(agent_output, project_root))

# Tier 3: Consensus independence — reviewers only
if role.lower() in ("review1", "review2") and other_reviewer_output:
    report.results.append(guardrail_consensus_independence(agent_output, other_reviewer_output))

# Tier 3: Hardcode + error handling — Menter only
if role.lower() == "menter":
    report.results.append(guardrail_hardcode_detector(agent_output, project_root))
    report.results.append(guardrail_error_handling(agent_output))

# Tier 3: Position randomizer + context injection — all roles (on prompt)
if prompt:
    report.results.append(guardrail_position_randomizer(prompt))
    report.results.append(guardrail_context_injection(prompt))

# Tier 3: Evidence hash chain — Menter + Verify (needs pre_exec_head)
if pre_exec_head and role.lower() in ("menter", "verify"):
    report.results.append(guardrail_evidence_hash_chain(pre_exec_head, project_root))

# Tier 3: Raw source preservation — all roles (needs DB)
if conn and run_id:
    report.results.append(guardrail_raw_source_preservation(conn, run_id))

# Tier 3: Bias drift — all roles
report.results.append(guardrail_bias_drift(agent_output, intent))
```

## Testing Pattern

Each guardrail was tested with `execute_code` using both a PASS case and a FAIL case:

```python
import sys
sys.path.insert(0, '/mnt/projects/cis/runtime')
from abstraction.guardrails import guardrail_intent_compliance

# FAIL: stub function
r = guardrail_intent_compliance('```python\ndef add(a, b):\n    pass\n```', '/mnt/projects/cis')
assert r.verdict == "FAIL"

# PASS: real function
r = guardrail_intent_compliance('```python\ndef add(a, b):\n    return a + b\n```', '/mnt/projects/cis')
assert r.verdict == "PASS"

# FAIL: syntax error
r = guardrail_intent_compliance('```python\ndef add(a, b)\n    return a + b\n```', '/mnt/projects/cis')
assert r.verdict == "FAIL"
```

## Container Verification

After wiring, the container was restarted (`docker restart cis-pipeline`) and the guardrails endpoint verified:

```
curl -s http://localhost:5000/api/relay/guardrails
{"count":0,"outcomes":[],"stats":{}}
```

The `count: 0` is expected — no pipeline runs have executed since the guardrails were wired. The first pipeline run will populate `gate_outcomes` with 30 results per phase × ~6 phases = ~180 rows per run.
