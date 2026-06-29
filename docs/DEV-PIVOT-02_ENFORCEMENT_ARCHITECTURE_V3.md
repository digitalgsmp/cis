     1|# CIS Enforcement Architecture — Combined Specification
     2|
     3|## Specification Document v3.0
     4|
     5|## Eric Gate Status: PENDING_APPROVAL
     6|
     7|This document is the reconciled enforcement architecture for CIS. It combines:
     8|
     9|1. **Claude's architectural outline** — the 6-layer deterministic gate schema,
    10|   override-plane-first discipline, and build-order from the June 17 browser
    11|   session reconciliation with ChatGPT.
    12|
    13|2. **The real facts on disk** — what code actually exists, what the live system
    14|   state is, what worked and what deadlocked.
    15|
    16|3. **Eric's explicit requirements** — extracted verbatim from the June 17
    17|   transcripts and prior sessions recorded in AGENTS.md §12.
    18|
    19|**Author:** Compiled from Claude/ChatGPT reconciliation + live system inspection
    20|**Date:** 2026-06-17
    21|**Replaces:** CIS_HERMES_HARDENING_SPECIFICATION.md v2.0 (retired)
    22|**Status:** DRAFT — for Eric Gate review, then Claude+ChatGPT audit
    23|
    24|---
    25|
    26|## 0. What Actually Happened on June 17
    27|
    28|### 0.1 The Core Realization (Eric's Words)
    29|
    30|> "I became aware that hermes had no constraints on it and that all of the
    31|> guardrails I thought were in place could be bypassed because cis is not
    32|> hermes and all of the guardrailing is just bash script in cis."
    33|
    34|This is the founding insight. CIS's guardrails are bash scripts that live inside
    35|the CIS repo. They gate the CIS pipeline. But any Hermes agent with tool access
    36|can call `write_file`, `patch`, or `terminal` directly — completely bypassing
    37|every gate. The gates are voluntary. The enforcement is theater.
    38|
    39|Confirmed empirically: `generate_agents_md.py` was run via `terminal()` with no
    40|staleness check, no deliberation, no Eric Gate. The 16 failure modes from the
    41|CIS Integration Assessment are documentation-only — nothing physically blocks
    42|any of them.
    43|
    44|### 0.2 The Attempted Fix (v2.0 — RETIRED)
    45|
    46|v2.0 wired `pre_tool_call` shell hooks into all 4 Hermes profile configs,
    47|pointing at `cis_pre_tool_gate.sh`. The hook checked for a clearance token
    48|file (`/tmp/cis_gate_clearance`) with a 30-minute TTL, created by
    49|`gate_runner.sh`.
    50|
    51|**What broke:** The token mechanism created a chicken-and-egg deadlock:
    52|- Gate runner can't pass (dirty git)
    53|- No clearance token created
    54|- Hook blocks all `write_file`/`patch`/`terminal`
    55|- Can't commit to clean state
    56|- Deadlock permanent — no way out
    57|
    58|**Root cause of the deadlock:** No escape hatch. The only way to disable the
    59|hook was to edit `config.yaml`, but the hook blocked edits. The lock could
    60|only be opened from inside the locked room.
    61|
    62|**Secondary failures:**
    63|- Deployed to all 4 profiles simultaneously, by the agent, with zero
    64|  failure-mode testing
    65|- The clearance mechanism depended on state the gate itself could block
    66|  (the token file)
    67|- The agent that deployed the hooks was the same agent the hooks were
    68|  supposed to constrain (R1 acting outside Reviewer role)
    69|
    70|### 0.3 What Was Recovered
    71|
    72|Commit `35db8fa` reverted the broken clearance-token mechanism. The current
    73|`cis_pre_tool_gate.sh` (live on all 4 profiles) uses a simpler gate: it checks
    74|the spine for a CONSENSUS_REACHED workflow_run within the last 24 hours.
    75|
    76|**Current state (verified 2026-06-17 23:30 UTC):**
    77|- All 4 gateways healthy (ports 8642/8643/8645/8646 → 200)
    78|- Hooks active on all 4 profiles
    79|- Gate has valid authorization (run-gate-20260618, ~1h old)
    80|- Git tree clean at 2d177d6
    81|- No stray --replace processes
    82|- `eric_gate_approvals` table exists but has 0 rows (unused)
    83|
    84|### 0.4 What Remains Unfixed
    85|
    86|The current 24h CONSENSUS_REACHED gate is a single coarse check. A Reviewer
    87|can still write code and execute commands — the gate doesn't check role.
    88|The Implementer can still self-authorize — the gate doesn't require Eric's
    89|approval. An agent's completion claim is still trusted without deterministic
    90|verification. The gate has no override file — a misconfiguration could still
    91|deadlock (though the SQLite check is simpler and less fragile than the token).
    92|
    93|---
    94|
    95|## 1. Core Principle
    96|
    97|> **A guardrail you cannot turn off from a bare shell is not a guardrail.
    98|> It is a trap. The off-switch is built and tested BEFORE the guardrail.**
    99|
   100|This single rule is the difference between the v2.0 deadlock and a safe
   101|enforcement system. Every gate in this architecture checks the override
   102|plane as its first line. You are never more than one `touch` command from
   103|a working system.
   104|
   105|### 1.1 What Eric Actually Wants (Verbatim)
   106|
   107|From AGENTS.md §12 and the June 17 transcripts:
   108|
   109|> "I need checks and balance, I am not a coder and if I don't trust something
   110|> one of you says I have to be able to paste it for another model to evaluate
   111|> and give me independent analysis. that is what claude and chatgpt did to
   112|> each other. I need a worker who is constrained to my working methods and
   113|> two objective reviewers as expert advisors."
   114|
   115|> "the LLMs are the tools, I am trying to get LLMs to help me think by
   116|> contributing factual information and expertise."
   117|
   118|> "I don't want summaries, I am trying to build a system that works from
   119|> the raw files."
   120|
   121|> "it doesn't matter if you work 99% of the time. the 1% creates an
   122|> unrecoverable deadlock. months and months of this. it's criminal."
   123|
   124|The system must: constrain agents to their roles, verify every claim against
   125|evidence, survive the 1% failure without deadlocking, and preserve Eric's
   126|own words as the fixed reference point.
   127|
   128|---
   129|
   130|## 2. Enforcement Architecture — Six Layers
   131|
   132|### Architecture Diagram
   133|
   134|```
   135|┌─────────────────────────────────────────────────────────────┐
   136|│                    OVERRIDE PLANE                           │
   137|│              /mnt/projects/cis/.GATE_DISABLED                │
   138|│         (checked FIRST by every gate — universal            │
   139|│          kill switch controllable from bare shell)           │
   140|├─────────────────────────────────────────────────────────────┤
   141|│                                                             │
   142|│  LAYER 1: Thin Hook + External Policy Checker               │
   143|│  ┌──────────────────────────────────────────────────────┐  │
   144|│  │ Hook (cis_pre_tool_gate.sh) — DUMB                   │  │
   145|│  │  1. Check override file → allow if present           │  │
   146|│  │  2. Collect facts: role, tool, target, cwd           │  │
   147|│  │  3. Call policy checker with facts                   │  │
   148|│  │  4. Exit with checker's exit code                    │  │
   149|│  │  Contains ZERO policy logic. Never changes.          │  │
   150|│  └──────────────────────────────────────────────────────┘  │
   151|│                          │                                  │
   152|│                          ▼                                  │
   153|│  ┌──────────────────────────────────────────────────────┐  │
   154|│  │ Policy Checker (cis_policy_check.sh) — DETERMINISTIC │  │
   155|│  │  Reads rules table → pure lookup → allow/deny        │  │
   156|│  │  NO LLM. NO model judgment. Exit 0 or exit 1.        │  │
   157|│  └──────────────────────────────────────────────────────┘  │
   158|│                          │                                  │
   159|│                          ▼                                  │
   160|│  ┌──────────────────────────────────────────────────────┐  │
   161|│  │ Rules Table (cis_policy_rules.yaml or spine table)   │  │
   162|│  │  Data, not code. Editable without touching scripts.  │  │
   163|│  │  role × tool_class × path_pattern → allow | deny     │  │
   164|│  └──────────────────────────────────────────────────────┘  │
   165|│                                                             │
   166|│  LAYER 2: Role Capability Matrix                            │
   167|│  ┌──────────────────────────────────────────────────────┐  │
   168|│  │ Role derived from $HERMES_HOME (unspoofable)         │  │
   169|│  │                                                      │  │
   170|│  │ Prime (8642):    read/search only, NO CIS writes     │  │
   171|│  │ Drafter (8645):  write docs/specs only, NO execution │  │
   172|│  │ Reviewer (8643): read-only, NO writes, NO execution  │  │
   173|│  │ Implementer (8646): write code per manifest,         │  │
   174|│  │                    build/test with approval only     │  │
   175|│  │ Qwen (8002):     NO tools at all (inference only)    │  │
   176|│  │                                                      │  │
   177|│  │ Deterministic: role + tool + target → table → allow  │  │
   178|│  └──────────────────────────────────────────────────────┘  │
   179|│                                                             │
   180|│  LAYER 3: Human-Only Authorization                          │
   181|│  ┌──────────────────────────────────────────────────────┐  │
   182|│  │ eric_approvals spine table                           │  │
   183|│  │ Only Eric can write to it. Agent physically cannot.  │  │
   184|│  │ Each row carries hash of exactly what was approved.  │  │
   185|│  │ Approval-for-A cannot authorize implement-B.         │  │
   186|│  │                                                      │  │
   187|│  │ Write paths (all require Eric):                      │  │
   188|│  │   CLI: cis approve --run-id X --hash Y               │  │
   189|│  │   Telegram: @cis_kernel_bot → API → DB               │  │
   190|│  │   UI: CIS dashboard "Approve" button                 │  │
   191|│  └──────────────────────────────────────────────────────┘  │
   192|│                                                             │
   193|│  LAYER 4: Epistemic Gates (advisory, not blocking)          │
   194|│  ┌──────────────────────────────────────────────────────┐  │
   195|│  │ Staleness: web fetch current facts before deliberat. │  │
   196|│  │ Reviewer search: each reviewer must do own research  │  │
   197|│  │ Negative claims: verify absence against live system  │  │
   198|│  │ Evidence completion: non-LLM script confirms effect  │  │
   199|│  │                                                      │  │
   200|│  │ These block the transition to Eric's approval,       │  │
   201|│  │ not the work itself. Agent can draft freely; cannot  │  │
   202|│  │ reach Eric without evidence attached.                │  │
   203|│  └──────────────────────────────────────────────────────┘  │
   204|│                                                             │
   205|│  LAYER 5: Front Door / Pipeline Stage Gates                 │
   206|│  ┌──────────────────────────────────────────────────────┐  │
   207|│  │ → Review: draft artifact exists with content hash    │  │
   208|│  │ → Eric Gate: both reviewers' records present,        │  │
   209|│  │             non-empty output (Qwen can't be dead)    │  │
   210|│  │ → Implement: eric_approvals row, recent, hash-match  │  │
   211|│  │ → Verify: claimed files exist on disk with content   │  │
   212|│  │ → Done: all prior gates passed                       │  │
   213|│  └──────────────────────────────────────────────────────┘  │
   214|│                                                             │
   215|└─────────────────────────────────────────────────────────────┘
   216|```
   217|
   218|---
   219|
   220|## 3. Layer Details — What Exists vs What Needs Building
   221|
   222|### 3.1 Layer 0 — Override Plane
   223|
   224|**What exists:** Nothing. `.GATE_DISABLED` does not exist on disk.
   225|**What needs building:** Add override check as line one of `cis_pre_tool_gate.sh`.
   226|**Build order:** THIS IS BUILT FIRST, before any other gate change.
   227|**Test:** Install trivial blocking hook → confirm blocked → `touch .GATE_DISABLED`
   228|→ confirm unblocked → `rm` it → confirm blocked again. Only after this loop
   229|works do you build gates behind it.
   230|
   231|```bash
   232|# The override check — line one of every hook:
   233|if [ -f "/mnt/projects/cis/.GATE_DISABLED" ]; then
   234|    exit 0  # Gate is OFF — Eric flipped it from a shell
   235|fi
   236|```
   237|
   238|### 3.2 Layer 1 — Thin Hook + External Policy
   239|
   240|**What exists:** `cis_pre_tool_gate.sh` — a single script that both checks
   241|conditions AND contains policy logic (the 24h CONSENSUS_REACHED query).
   242|It is not thin — policy and mechanism are fused.
   243|
   244|**What needs building:**
   245|1. Refactor the hook to be dumb: check override → collect facts → call checker → exit
   246|2. Create `tools/gates/cis_policy_check.sh` — deterministic, reads rules, exits 0/1
   247|3. Create `tools/gates/cis_policy_rules.yaml` — the rules table as data
   248|
   249|**Design rule:** The hook never changes after initial deployment. All policy
   250|changes happen in the rules table, which you can read and edit without touching
   251|code. The policy checker is a pure function of facts + rules — no LLM ever.
   252|
   253|### 3.3 Layer 2 — Role Capability Matrix
   254|
   255|**What exists:** Nothing. The current hook does not check role at all. Any
   256|profile running with HERMES_HOME set can write anywhere in CIS if a 24h
   257|consensus record exists. This is how R1 deployed hooks — Reviewer role,
   258|writing to config files and running terminal commands.
   259|
   260|**What needs building:**
   261|1. Role derivation function — reads `$HERMES_HOME` from the hook's environment
   262|   (set by Hermes, cannot be spoofed by the agent)
   263|2. Rules table entries for each role — what tool+target combinations are allowed
   264|3. Policy checker reads role from env + tool from `$TOOL_NAME` + target from args →
   265|   table lookup → allow/deny
   266|
   267|**What this prevents concretely:**
   268|- R1 writing to `~/.hermes*/config.yaml` (the v2.0 deadlock deployment)
   269|- R1 running `terminal` to restart gateways (the v2.0 all-at-once deployment)
   270|- Drafter executing code or editing configs
   271|- Implementer writing to docs/specs (crossing into Drafter's domain)
   272|- Prime mutating the CIS repo
   273|
   274|**Deployment order:** Start with Reviewer only (the role that caused the
   275|incident). Add Drafter, Implementer, Prime, Qwen incrementally.
   276|
   277|### 3.4 Layer 3 — Human-Only Authorization
   278|
   279|**What exists:** `eric_gate_approvals` table in the spine — schema exists,
   280|0 rows. No write path exists for Eric to record approvals. The current
   281|gate uses workflow_runs CONSENSUS_REACHED as a proxy — any consensus
   282|record from any run authorizes any write.
   283|
   284|**What needs building:**
   285|1. Eric-controlled write paths:
   286|   - CLI: `cis approve --run-id <id> --hash <proposal_hash>`
   287|   - Telegram bot endpoint that writes the row
   288|   - UI button
   289|2. Hash binding: each approval row stores the SHA256 of what was approved
   290|3. Policy checker reads eric_approvals: is there a recent row with matching hash?
   291|4. Time window: configurable, default 24h, stored in rules table not hardcoded
   292|
   293|**Design rule:** No code path exists for an agent to insert into
   294|eric_gate_approvals. The write paths all require Eric's authentication.
   295|This table is the load-bearing authorization record in the entire system.
   296|
   297|### 3.5 Layer 4 — Epistemic Gates
   298|
   299|**What exists:**
   300|- `tools/pipeline/staleness_check.py` — web freshness check, operational
   301|- `tools/pipeline/reviewer_reconcile.py` — dual-review deliberation, operational
   302|- `tools/gates/gate_staleness.sh` — staleness gate script
   303|- `tools/gates/gate_deliberation.sh` — deliberation gate script
   304|- `tools/gates/gate_pre_execution_oversight.sh` — oversight gate (Gate 7 in gate_runner)
   305|
   306|**What exists but is not enforced:**
   307|- Independent-search-per-reviewer: each reviewer SHOULD do own research but
   308|  nothing verifies that a reviewer actually searched before delivering a verdict
   309|- Verify-negative-claims: when an agent asserts something doesn't exist, nothing
   310|  checks the live system
   311|- Evidence-backed completion: the rule exists on paper (ADR-SEED-002, AGENTS.md §10)
   312|  but is not programmatically enforced
   313|
   314|**What needs building:**
   315|1. Search-evidence requirement: a reviewer's verdict is rejected by the pipeline
   316|   stage gate unless an accompanying search-evidence record exists from that reviewer
   317|2. Negative-claim verification: add a check to the policy checker — when a
   318|   `write_file` or `patch` is preceded by an agent claim of absence, verify the
   319|   claim against live system before allowing the write
   320|3. Evidence-backed completion gate: wire `gate_file_exists.sh` and
   321|   `gate_service_health.sh` into the pipeline closeout so an agent's "done"
   322|   claim is never the record of completion
   323|
   324|**Honest limit:** These gates can deterministically verify that a search HAPPENED
   325|(fetch occurred, non-empty evidence record exists). They cannot verify that the
   326|model interpreted results correctly. Eric's approval gate (Layer 3) remains the
   327|final check on interpretation.
   328|
   329|### 3.6 Layer 5 — Front Door / Pipeline Stage Gates
   330|
   331|**What exists:** The gate scripts exist and `gate_runner.sh` chains them. But
   332|they are not wired as automatic stage-transition gates in the orchestrator —
   333|they run when invoked, not when a stage claims completion.
   334|
   335|**What needs building:**
   336|1. Wire each gate into the orchestrator as a stage-transition requirement
   337|2. The Qwen gate specifically: the "→ Eric Gate" transition checks for TWO
   338|   distinct reviewer records with non-empty output. If Qwen is down, the gate
   339|   fails deterministically — no single model can paper over a dead reviewer.
   340|3. The Implementer gate: checks eric_approvals for a recent, hash-matching row
   341|   before allowing implementation work to proceed.
   342|
   343|---
   344|
   345|## 4. Build Order
   346|
   347|Build one layer at a time. Each layer proven before the next. On ONE profile
   348|first, then expand. Escape hatch tested before any gate is trusted. NEVER
   349|deploy to all four at once (the v2.0 mistake).
   350|
   351|| Phase | Layer | What Gets Built | Depends On | Status |
   352||-------|-------|----------------|------------|--------|
   353|| 0 | — | Escape hatch POC on one profile | Nothing | NOT BUILT |
   354|| 1 | 0 | Add override plane to all 4 hooks | Phase 0 | NOT BUILT |
   355|| 2 | 1 | Refactor hook to thin + external policy checker | Phase 1 | NOT BUILT |
   356|| 3 | 1 | Rules table (YAML) — start with current 24h rule | Phase 2 | NOT BUILT |
   357|| 4 | 2 | Role matrix: Reviewer read-only enforcement | Phase 3 | NOT BUILT |
   358|| 5 | 2 | Role matrix: Drafter, Implementer, Prime, Qwen | Phase 4 | NOT BUILT |
   359|| 6 | 3 | eric_approvals write paths + hash binding | Phase 5 | NOT BUILT |
   360|| 7 | 4 | Staleness + verify-negative-claims gates | Phase 6 | PARTIAL (staleness exists) |
   361|| 8 | 4 | Independent-search + evidence-completion gates | Phase 7 | NOT BUILT |
   362|| 9 | 5 | Pipeline stage gates in orchestrator | Phase 8 | NOT BUILT |
   363|
   364|### 4.1 What Already Exists (Foundation — Do Not Rebuild)
   365|
   366|| Artifact | Path | Status |
   367||----------|------|--------|
   368|| Current hook | `tools/hooks/cis_pre_tool_gate.sh` | ACTIVE — 24h SQLite gate |
   369|| Gate runner | `tools/gates/gate_runner.sh` | ACTIVE — 8-gate sequencer |
   370|| Gate scripts (40+) | `tools/gates/gate_*.sh` | ACTIVE |
   371|| Staleness check | `tools/pipeline/staleness_check.py` | ACTIVE |
   372|| Reviewer reconcile | `tools/pipeline/reviewer_reconcile.py` | ACTIVE |
   373|| Eric approvals table | `data/cis_memory.db` → `eric_gate_approvals` | EXISTS — 0 rows |
   374|| Workflow runs | `data/cis_memory.db` → `workflow_runs` | ACTIVE — 5 rows |
   375|| Deliberation rounds | `data/cis_memory.db` → `deliberation_rounds` | ACTIVE — 4 rows |
   376|
   377|### 4.2 What Gets Replaced
   378|
   379|| Current (v2.0 remnant) | Replacement | Why |
   380||------------------------|-------------|-----|
   381|| Hook contains policy logic inline | Hook is dumb relay; policy in checker | Policy changes shouldn't touch hook |
   382|| 24h window hardcoded in hook | Window in rules table | Configurable without editing scripts |
   383|| No override file | `.GATE_DISABLED` checked first | Deadlock prevention |
   384|| Any CONSENSUS_REACHED authorizes any write | Role matrix + eric_approvals | Reviewer can't implement |
   385|| Single coarse gate | Layered: role + approval + epistemic | Defense in depth |
   386|
   387|---
   388|
   389|## 5. What This Does NOT Change
   390|
   391|- CIS remains a standalone application using Hermes as backend
   392|- Hermes remains the agent runtime; CIS provides enforcement
   393|- The spine remains the source of truth
   394|- The override file is the universal kill switch
   395|- Eric is the final approval gate for all implementation
   396|- The 4-gateway topology (8642/8643/8645/8646) stays as-is
   397|- Qwen on 8002 (llama-server direct) for machine-to-machine review
   398|
   399|---
   400|
   401|## 6. Open Questions
   402|
   403|1. **Rules table format**: YAML file vs spine table? YAML is simpler to edit
   404|   manually; spine table is queryable by the checker without file I/O.
   405|   Decision needed before Phase 2.
   406|
   407|2. **Telegram approval path**: Eric often operates from phone. The Telegram
   408|   bot → spine write path needs design. Options: bot calls API endpoint that
   409|   writes the row; or bot has direct DB access (security concern).
   410|
   411|3. **Fail-open vs fail-closed**: If the policy checker itself crashes, should
   412|   the gate allow (fail-open, risk: enforcement disappears silently) or deny
   413|   (fail-closed, risk: deadlock)? Current hook fails-open — is this correct
   414|   for all layers?
   415|
   416|4. **Profile relocation**: The sibling-home layout (~/.hermes-r1) triggers
   417|   the `get_default_hermes_root()` collapse bug (ADR-SEED-014). Moving homes
   418|   to ~/.hermes/profiles/ permanently fixes this. When does this happen
   419|   relative to the enforcement build?
   420|
   421|5. **Qwen direct path**: The finding that Qwen reviews must go through
   422|   llama-server on port 8002 (not gateway 8644 which hangs on tool-loops).
   423|   Should the policy checker enforce this? Or does it live in orchestrator config?
   424|
   425|---
   426|
   427|## 7. Eric's Words — The Fixed Reference
   428|
   429|These are the statements that define what the tool is for. Every build decision
   430|traces to one of these. When an agent proposes something, the gate asks: does
   431|this serve these stated goals, or is it the model filling a vacuum?
   432|
   433|> "I don't want summaries, I am trying to build a system that works from the
   434|> raw files."
   435|
   436|> "I need checks and balance, I am not a coder and if I don't trust something
   437|> one of you says I have to be able to paste it for another model to evaluate."
   438|
   439|> "the LLMs are the tools, I am trying to get LLMs to help me think by
   440|> contributing factual information and expertise."
   441|
   442|> "when I sit down and interact with the LLMs they don't remember anything
   443|> and the overall vision is not apparent to combine the vision of where I
   444|> am trying to get to, to why we are working on the immediate task."
   445|
   446|> "I don't care about governance. did governance stop you all from undoing
   447|> the 4 installations I had set up and consolidating it."
   448|
   449|> "it doesn't matter if you work 99% of the time. the 1% creates an
   450|> unrecoverable deadlock. months and months of this. it's criminal."
   451|
   452|---
   453|
   454|*Generated from: Claude/ChatGPT reconciliation (June 17 browser session),
   455|live system inspection (2026-06-17 23:30 UTC), AGENTS.md §12,
   456|ADR-SEED-002/003/004/014, CIS_HERMES_HARDENING_SPECIFICATION.md v2.0 (retired).*
   457|
   458|---
   459|
   460|## Session Update — 2026-06-27
   461|
   462|This document's topic (enforcement architecture) was not directly advanced this session.
   463|The major work completed: knowledge base ingestion (287K messages, FTS5 + ChromaDB),
   464|abstraction layer (5 endpoints including human-readable status), intent alignment
   465|pipeline, and roadmap. See **DEV-PIVOT-05 §10** and **DEV-PIVOT-06 §10** for the
   466|full session handoff (gateway status, Eric's feedback, Phase 1 next steps).
   467|Commit: 9c921e2. All 17 DEV-PIVOT files carry session footers. HCP regenerated at HEAD.
   468|