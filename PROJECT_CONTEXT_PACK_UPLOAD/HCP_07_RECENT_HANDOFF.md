# Recent Handoff — Tier 5.4 COMPLETE
Date: 2026-07-08
Session: Tier 5.4 generate_hcp.py implementation

HEAD: `a6f88a1`

Generated: 2026-07-08 18:57 UTC | Run: run-2029dcbc41ed
Source: SQLite spine + config/hcp_static.yaml + config/agents_static.yaml
DO NOT MANUALLY EDIT — regenerate with tools/export/generate_hcp.py

## Tier 5.4 — generate_hcp.py (this session)
- `config/hcp_static.yaml` — new: HCP-specific Layer B static config
- `tools/export/generate_hcp.py` — new: reads spine + static + git, writes 10 HCP files
- All 10 HCP_ files regenerated from spine, replacing manual maintenance
- Manual HCP files backed up to PROJECT_CONTEXT_PACK_UPLOAD/backups/ before overwrite

## Tier 2 — Kanban Coordination Layer (`2989c5b`)
- `HERMES_KANBAN_DB` and `HERMES_KANBAN_HOME` added to all 5 profile .env files
- Shared `cis-pipeline` board created; Tier 3 smoke test completed
- `runtime/config/systemd/` — service templates backed up
- ENV_MANIFEST.md — all env vars documented

## Tier 4.4 — Context Export State Tables (`b2e6c98`)
- `runtime/schema/migrations/0001_context_export_state.sql` — 4 new tables
- `runtime/db/database.py` — extended (+4 constants, +4 insert functions, +migration check)
- `tools/gates/gate_db_state.py` — extended (+4 tables, +12 columns)
- DB-only (no commit): 6 decisions, 3 questions, 7 actions, 4 blockers

## Tier 5.1 — AGENTS.md Generator (`ee8eb25`)
- `tools/export/generate_agents_md.py` — reads spine + static config
- `config/agents_static.yaml` — Layer B static content
- AGENTS.md generated at 8,384 bytes (limit 20,000)

## Tier 5.2 — AGENTS.md Canary
- TERMINAL_CWD=/mnt/projects/cis set in all 5 .env files
- HERMES_CIS_BRIEFING_PATH commented out for canary testing
- 3/3 V4 gateways passed initially (8642 was down due to service misconfiguration)
- After repair: 4/4 PASS

## Tier 5.2E — Gateway Topology Repair (`353cef5`)
- hermes-gateway.service was auto-overwritten to use r1 profile (HERMES_HOME=/home/eric/.hermes-r1)
- Restored from repo backup: HERMES_HOME=/home/eric/.hermes, port 8642 (Flash/Research)
- hermes-gateway-r1.service now binds 8643 correctly
- Root cause (gateway auto-update of service file) unmitigated — BLK-SEED-005

## Tier 5.3 — HERMES_CIS_BRIEFING_PATH Retirement (`80f934c`)
- Permanently removed from all 5 profile .env files
- TERMINAL_CWD=/mnt/projects/cis retained in all .env files for gateway AGENTS.md discovery
- All 4 active gateways pass AGENTS.md canary
- Service template backups updated

## Docker Containment PROVEN on creative-vm (2026-06-19)

**Stage 1 — Docker install:**
- Docker 29.6.0 installed successfully
- Qwen/llama.cpp on host port 8002 remained healthy (PID 1611, 4002MiB GPU)
- Hermes configs were not changed

**Stage 2 — Hermes r1 CLI containment proof:**
- Kernel-enforced read-only mounts blocked writes to:
  /mnt/archive, /mnt/projects/cis, /mnt/projects/swa
- Writable catalog mount succeeded: /mnt/cache/catalog
- Direct docker run proof passed
- Hermes-through-Docker r1 CLI proof passed
- Host cross-check confirmed no forbidden source-root files were created
- r1 config restored to local backend after proof
- Qwen/llama.cpp still healthy after proof

**Framing correction — the 16 failure modes should use four pillars, not a 16-item checklist:**
1. Containment — execution boundary (PROVEN on r1 CLI)
2. Spine-gates — authority and state transition enforcement
3. Cognition — verifier, deliberation, evidence, staleness, cross-model review
4. Eric veto — human final authority and residual judgment

Progress measured by pillars proven, not by claiming all 16 failures are individually "solved."
Containment proven on r1 CLI. Not yet extended to gateway path or implementer path.
Cognition failures are mitigated by design, not completed forever.

**Next actions:**
1. Extend containment proof from CLI to gateway path and to scrape profile
2. Spine-gate pillar audit (READ ONLY) — identify which gates exist, run, and reject bad input
3. Drafter writes spec from audit findings → Reviewer challenges → Claude+ChatGPT reconcile → Eric approves → implement
4. ARCHITECTURE — Per-project container as standing workflow (DESIGN DIRECTION)
5. ARCHITECTURE — Scope-authorization gates paired with per-project containers (DESIGN DIRECTION)

**Open / unverified (do not assume):**
- Gateway-with-Docker-backend is unproven (only CLI proof passed)
- v4impl pre_tool_call hook behavior inside container is unknown
- Correct scrape container image is undecided (bare ubuntu insufficient)
- Verifier Registry (DEV-PIVOT-16) is specified but build/commit status unverified
- Docker group refresh may still be required for gateway non-sudo access
- /mnt/cache/catalog exists and is the intended writable catalog root
- docs/DOCKER_CONTAINMENT_PROPOSAL.md committed this session

- runtime/config/systemd/live_backups/ untracked in git

## Exact Next Action


Enforcement — Container Isolation (ADR-015/016).

## Eric Gate Approval Status

- Decision: APPROVE
- Workflow run: run-892e86ca512a0056-1783535751
- Decided at: 2026-07-08T18:42:08.742831+00:00
- Goal reference: None
- Briefing hash: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
