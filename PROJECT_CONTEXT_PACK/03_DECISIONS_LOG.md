# Decisions Log — Hermes Harness / CIS
Last updated: 2026-05-29

| Date | Decision | Reason | Status | Evidence |
|------|----------|--------|--------|----------|
| 2026-05-28 | CIS-INFRA-STORAGE-001: Proxmox snapshot script deployed | Passthrough drives blocked snapshots | COMPLETE | cis-snapshot on root@wander, test snapshot verified |
| 2026-05-28 | ADR-050: 4-tier execution harness | Prime brainstorm → R1+V4-Pro deliberation → Claude/ChatGPT escalation → Qwen execution | COMPLETE | Logged to /api/decisions |
| 2026-05-29 | INFRA-002: Prime HERMES_HOME corrected | Single-line service file fix resolved Prime misrouting and R1 crash loop | COMPLETE | hermes-gateway.service, port 8642 active |
| 2026-05-29 | INFRA-003: Phase 2 complete — gateways behaviorally distinct | Same-prompt test confirmed all three models different | COMPLETE | Behavioral verification output |
| 2026-05-29 | Phase 3 reframed as Phase 3A — Context Loader + Seed Intent | Generic context loading is insufficient; Eric's actual words must orient sessions | DECIDED | This session |
| 2026-05-29 | Seed intent excerpts from raw Hermes archive scan must be included in context orientation | Prevents model summaries from replacing Eric's actual intent | DECIDED | SEED_INTENT_EXCERPTS.md |
| 2026-05-29 | Prime, R1, and Qwen must share the same loaded context | Adversarial loop requires common ground truth | DECIDED | This session |
| 2026-05-29 | Phase 3B should automate Hermes-to-Hermes continuation | Structured handoff format enables cold-session handoff without Eric | DECIDED | HANDOFF format defined |
| 2026-05-29 | Structured handoff format: HANDOFF_YYYYMMDD_HHMM_<phase>.md | Standardized continuation format for Phase 3B automation | DECIDED | /mnt/projects/cis/session_handoffs/ |
| 2026-05-29 | CIS scope preserved as broad creative assistant | Writing, image, motion, sound, web, research, tutorials, treatments, scripts, finished production | REAFFIRMED | This session |
| 2026-05-29 | Claude/ChatGPT paid API access for pass/fail review — design phase only | Tier 3 escalation sparing use; capture design for unified memory | RECORDED | Scratchpad |
| 2026-05-29 | Hermes capabilities audit needed | Exhaustive research into skills, tools, config for optimal use | RECORDED | Scratchpad |
| 2026-05-29 | SQLite and VDB remain fundamental later layers — not abandoned | Phase 3A documentation only; implementation deferred | DECIDED | This session |
| 2026-05-29 | Claude and ChatGPT: external consultants, not primary daily advisors | Live Hermes agents (Prime+R1+Qwen) are daily loop; Claude/ChatGPT are periodic reviewers | REAFFIRMED | ADR-050 |
| 2026-05-19 | Isolated Hermes profiles for multi-agent architecture | Independent config.yaml, .env, sessions per agent | COMPLETE | HHR-017B |
| 2026-05-19 | Gateway port assignment: Prime=8642, R1=8643, Qwen=8644 | Non-overlapping | COMPLETE | HHR-017C |
| 2026-05-19 | Agent registry pattern: agent_instances table + advisor routing | Single source of truth for available agents | COMPLETE | HHR-017D |
| 2026-05-18 | Hermes Harness infrastructure phase-complete | Full lifecycle: capture → exchange → directive → handoff | COMPLETE | HHR-001 through HHR-015B |
