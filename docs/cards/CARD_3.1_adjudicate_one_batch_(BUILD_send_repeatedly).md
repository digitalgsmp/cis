## CARD 3.1 — adjudicate one batch (BUILD — send repeatedly)

```
Take the next 200 PENDING rows by id. That is batch N.

READ EACH ONE. Every row gets a verdict:
  TASK             -> set task_title, one plain sentence
  ALREADY_IN_LIST  -> set existing_item; VERIFY by grep, paste the grep
  ALREADY_BUILT    -> set verdict_reason to a file:line you OPENED
  NOT_A_TASK       -> set verdict_reason; "unclear" is a valid reason
  DUPLICATE        -> set verdict_reason to the other candidate's id

Not optional:
  - no row skipped
  - ALREADY_BUILT requires a file you actually read
  - do not merge, summarise, or judge by how often something appears. A task
    raised once is not less real than one raised twenty times.

VM vs container:
  Most development history is the VM pipeline, which is structurally different
  from the container. A finding about VM structure is not automatically a
  container defect. For any structural finding — agent config, model assignment,
  wiring, paths — state which pipeline it describes and verify against the
  container before marking TASK. If it cannot be determined, that is a valid
  verdict and the row stays TASK flagged as needing container verification.

  Worked example: a VM-era finding that the drafter and one reviewer shared a
  model is FALSE in the container — review1 qwen/qwen3.7-max, review2
  z-ai/glm-5.2, draft deepseek-v4-pro, verified 2026-08-31 from each agent's own
  config.yaml.

  File presence in the container is NOT evidence the code runs there. The repo
  is mounted whole at /workspace/cis, so every VM file is visible inside — but
  container_app.py registers only relay_bp plus health/UI routes. An
  ALREADY_BUILT verdict in a container context needs the route or the import
  path, not the file.

Three enforcement layers, easily confused:
  CIS has three separate enforcement layers. Name which one a finding describes
  BEFORE verifying it. Finding one of them wired is not evidence another is.

  1. container_gate_runner.py — the pre_tool_call hook. FIRES on every tool
     call. Dangerous commands, secrets, forbidden write paths, loop guards.
  2. The 51 scripts in /opt/cis-gates/ — DEAD. Nothing invokes them. The only
     reference in the running code is container_app.py:332, a health check that
     confirms they are root-owned and read-only — that they are sealed, not
     that they run.
  3. pipeline_relay's own L1 guardrails via run_guardrails() — FIRE, but only
     in the verification phase, after all the work is done.

  Worked error, 2026-08-31: a finding that layer 2 is dead code was nearly
  marked refuted because run_guardrails() (layer 3) was found imported and
  called at pipeline_relay.py:2503 and 2662. Wrong layer. Layer 2 is still
  dead — 57 files in /opt/cis-gates/, zero call sites.

PROOF: paste
  select status, count(*) from mining_candidates where batch = N group by status
  select count(*) from mining_candidates where status='PENDING'
EXPECT: 200 adjudicated, PENDING down by exactly 200. Then STOP.
```
