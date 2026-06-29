# Proposal: CIS Governance Reset — Move Governance Into the Application

**Author:** V4 Drafter (deepseek-v4-pro), per Eric's direction
**Date:** 2026-06-18
**Status:** DRAFT — awaiting Eric Gate review
**Replaces:** No prior proposal. This is a development-posture change, not a new tier.

---

## 1. Diagnosis

The current HCP and AGENTS.md files overuse governance language as an operator-facing process. Every session re-litigates:

- Drafter/Reviewer/Prime role theater
- Multi-step deliberation ceremony
- Non-bypassability claims that bash scripts cannot enforce
- "Do not start" lists that prevent building the app needed to enforce the rules
- Pipeline-lane descriptions that describe a finished-app discipline the app is not yet carrying

The files describe a finished application's discipline, but in practice that discipline is being applied to Hermes manually while the app is not yet carrying the burden. That reverses the point of CIS.

Confirmed empirically: `generate_agents_md.py` was run via `terminal()` with no staleness check, no deliberation, no Eric Gate. The 16 failure modes from the CIS Integration Assessment are documentation-only — nothing physically blocks any of them. The governance layer is ahead of the usable application layer.

This is not an "anti-governance" position. It is an accurate diagnosis.

---

## 2. New Development Principle

**Governance is a product feature, not the development workflow.**

During development, the priority is to produce a functioning CIS application that reduces Eric's manual burden. Rules, gates, classifier authority, staged promotion, reviewer loops, and Eric approval must be implemented as software affordances: database constraints, UI queues, write-path restrictions, tests, and clear buttons. They should not be repeated as advisory warnings that block forward progress without enforcing anything.

The replacement sentence that replaces all governance ceremony in operator-facing context:

> *These governance concepts describe intended finished-system behavior. During development, prioritize building the smallest working UI/database path that makes the behavior enforceable.*

---

## 3. Development Rules (Only These Stay)

Three rules replace all governance ceremony during development:

1. **Do not destroy files or data.** Use git and backups before risky edits.
2. **Do not claim completion without evidence.** Command output, file evidence, test output, or UI verification required.
3. **Build the smallest working application path that reduces Eric's manual burden.** Prefer small working vertical slices over abstract architecture documents. When a rule is important, implement it in the app instead of repeating it in prompts.

Everything else — Eric Gate, reviewer loops, staged promotion, classifier authority, role routing — belongs in the app specification, database constraints, UI workflow, and tests. Not in repeated conversation instructions.

---

## 4. What Gets Stripped from HCP/AGENTS.md

The following content is removed or quarantined from operator-facing context:

| Content to strip | Current location | Why |
|---|---|---|
| "Do Not Start" list (11 items) | AGENTS.md §2, HCP_01 §Do Not Start, HCP_05 §Do Not Start | Prevents building the app needed to enforce the rules |
| Pipeline lane ceremony (TRIAGE→RESEARCH→DRAFT→REVIEW↔LOOP→CONSENSUS→ERIC_GATE→IMPLEMENT→VERIFY→STATE_WRITE→EXPORT→DONE) | HCP_01 (lines 80-98), HCP_02 (lines 71-89), HCP_06 (lines 48-57) | Describes finished-app discipline; app can't enforce it yet |
| "Eric Gate is not bypassable" and similar non-bypassability claims | AGENTS.md §4 (ADR-SEED-004), HCP_01 (line 91), HCP_06 §Pipeline Protocol | Bash scripts cannot enforce this; claim is theater without app enforcement |
| Role identity ceremony (HERMES_HOME-derived role, READ_ONLY_STANDING_BY, terminal session must print HERMES_HOME before FINAL_DIRECTIVE) | AGENTS.md §11, HCP_06 (lines 6-26) | Hermes-manual ceremony; belongs in app routing, not in prompts |
| Multi-step deliberation protocol (2-3 rounds typical before CONSENSUS_REACHED, Reviewer emits OBJECTIONS or CONSENSUS_REACHED) | HCP_06 (lines 48-57), HCP_02 (lines 71-89) | Depends on Eric manually transporting messages; app should automate |
| Exact-Format Instruction Rule (COMMAND: / OUTPUT: / FINAL:) | HCP_06 (lines 90-114) | Evidence rule #2 above covers this; the ceremonial format is over-specified |
| Escalation Advisor Integration Protocol (P0-P6 packet format, trigger conditions, response lifecycle) | HCP_06 (lines 125-171) | Manual copy-paste protocol; belongs in app implementation, not operator-facing docs |
| "Pipeline is operational" / "All four V4 Pro gateways healthy" claims without usable UI path | HCP_01 (opening), AGENTS.md §1 | The gateways are running but the app path from Eric's perspective is broken — governance claims about operational state misrepresent reality |
| "Do not infer from older files if this pack conflicts" / "Do not reopen decisions marked complete" | HCP_00 (lines 29-30) | Governance tone that assumes finished-app authority |
| Verification-Hardening Rule (full 7-point evidence list) | AGENTS.md §10, HCP_01 (lines 104-122), HCP_06 (lines 64-88) | Collapsed into development rule #2 (three sentences, not a page) |

---

## 5. Restructured HCP File Layout

The HCP files are regenerated by `tools/export/generate_hcp.py` from `config/hcp_static.yaml` + SQLite spine. The reset modifies the static config and generator to produce:

### HCP_00 — What CIS Is

Short identity statement. Not a governance document.

```
CIS is Eric's multi-agent pipeline system. It coordinates Hermes profiles
(Drafter, Reviewer, Implementer, Research) through a shared SQLite spine
and a Flask/React UI at port 5000.

Current development priority: Build the smallest working application path
that reduces Eric's manual burden — intake, categorization, wishlist, approval UI,
build-plan generation.
```

### HCP_01 — Current Usable State (Not Aspirational)

What actually works for Eric right now. Open questions about usability gaps are honest, not aspirational.

- Infrastructure facts (VM, storage, network)
- Gateway table (which services are running)
- What Eric can actually do (Telegram bots, UI at port 5000)
- Known gaps (q-003: "what does Eric see?", q-005: "escalation wiring?", q-006: "remaining gaps?")
- Spine DB state (row counts)

Removed: pipeline lane ceremony, "Do Not Start" list, verification-hardening rule long-form, Eric Gate non-bypassability claims.

### HCP_02 — Working Architecture Only

Only architecture that exists as running code:

- Gateway service table (systemd units, ports, models)
- Flask/React stack (runtime/app.py, runtime/ui/)
- SQLite spine schema (tables, row counts)
- Router (runtime/api/router.py — classify_route function)
- MCP bridge (runtime/mcp_bridge/)
- Hermes source patches (the 4 patches that exist)

Removed: pipeline lane diagram describing finished-app behavior, Kanban lanes, "bidirectional spine" architecture prose.

### HCP_03 — Decisions, Short Form

One-line decisions. No long-form ADR prose.

| Date | Decision | Status |
|------|----------|--------|
| 2026-06-16 | ADR-SEED-014: BLK-SEED-005 was false positive | DECIDED |
| 2026-06-09 | ADR-SEED-013: Kanban retired as pipeline transport | DECIDED |
| ... | ... | ... |

Removed: long-form decision reasoning. The spine holds the full text; HCP is the index.

### HCP_04 — Open Questions

Unchanged in structure. Already honest.

### HCP_05 — Immediate Build Task

The one thing to build next. Not a "Do Not Start" list.

The current build direction:

```
Build the functional intake path:

1. Inventory available VM files, old Hermes sessions, CIS docs, SWA docs,
   WIASW workflow resources, build plans, scratchpads, and handoffs.
2. Extract Eric's verbatim intent descriptions with source provenance.
3. Categorize into CIS infrastructure, SWA field-work (including WIASW creative workflow),
   mixed, or unknown.
4. Stage extracted desires/features into a wishlist/backlog table.
5. Add a simple UI for Eric to approve, reject, merge, or prioritize wishlist items.
6. Convert approved wishlist items into proposed build-plan nodes.
7. Only then generate the next build plan.

Target: file/session corpus → verbatim intent extraction → domain categorization
→ wishlist → Eric review UI → proposed build plan → implementation.
```

Removed: "Do Not Start" list, 40-item build order table.

### HCP_06 — Model/Tool Usage (Minimal)

Which models and tools are available. No role ceremony.

```
Available profiles:
- hermes-prime (8642, via NeMo 8800): Research, evidence search
- hermes-v4pro (8645): Drafting, analysis
- hermes-r1 (8643): Review, adversarial challenge
- hermes-v4impl (8646): Implementation, file edits
- hermes-qwen (8644): Second reviewer

Recommended usage: Eric talks to whichever profile is appropriate for the task.
The app will eventually route automatically; during development, Eric routes manually.

Development rules:
1. Do not destroy files or data.
2. Do not claim completion without evidence.
3. Build the smallest working application path.

Governance concepts (Eric Gate, reviewer loops, staged promotion, classifier authority,
role routing) describe intended finished-system behavior. During development, prioritize
building the smallest working UI/database path that makes the behavior enforceable.
```

Removed: role identity rule, READ_ONLY_STANDING_BY protocol, pipeline protocol, verification-hardening rule long-form, exact-format instruction rule, escalation advisor integration protocol.

### HCP_07 — Recent Handoff

Unchanged in structure. Session summary, HEAD, what was done.

### HCP_08 — Files Changed

Unchanged in structure. Recent commits and files.

### HCP_09 — Terms

Short glossary. Removed: pipeline lane definitions, architecture theory terms. Keep: file paths, service names, DB table names.

---

## 6. AGENTS.md Restructuring

AGENTS.md serves Hermes-native internal context. Same reset principles apply:

| Current section | Change |
|---|---|
| §1 Current Build Phase | Keep: tier status, HEAD. Remove: pipeline operational claims. |
| §2 Do Not Start | **Remove entirely.** Replaced by: "Build the smallest working application path. No work is blocked; governance concepts are app features, not development restrictions." |
| §3 Active Architecture | Keep: infrastructure facts, gateway table, source patches. Remove: role descriptions, pipeline architecture prose. |
| §4 Active Decisions | Compress to one-line entries (match HCP_03). |
| §5 Open Questions | Keep. |
| §6 Next Actions | Replace with immediate build task (match HCP_05). |
| §7 Active Blockers | Remove (governance theater — nothing is actually blocked). Keep only BLK-SEED-004 (Google Drive backup unverified) as a factual note. |
| §8 Recent Pipeline Runs | Keep (factual data). |
| §9 Eric Gate Status | Remove (governance concept, not a development fact). |
| §10 Verification Hardening Rule | **Remove.** Replaced by development rule #2 (three sentences). |
| §11 Role Identity Rule | **Remove.** Replaced by: "Profile identity is determined by HERMES_HOME. App routing will enforce role boundaries when built." |
| §11.5 READ_ONLY_STANDING_BY | **Remove.** Replaced by: "On fresh session start, confirm HEAD and dirty status before acting. Ask Eric before modifying files." |
| §12 Seed Intent | Keep verbatim (Eric's own words). |
| §13 Evidence-Backed Response Rule | **Remove.** Replaced by development rule #2 (three sentences). |

---

## 7. Immediate Build Direction

Stop expanding governance documents. Build the functional intake path:

1. **Inventory the corpus.** All available VM files, old Hermes sessions, CIS docs, SWA docs, WIASW workflow resources, build plans, scratchpads, and handoffs.
2. **Extract verbatim intent.** Pull Eric's exact words describing what he wants, with source file provenance. No summaries.
3. **Categorize.** Sort into: CIS infrastructure, SWA field-work app (including WIASW creative workflow), mixed, or unknown.
4. **Stage into wishlist.** A `wishlist` table in the spine: description, source provenance, category, status (pending/approved/rejected/merged), priority.
5. **Build approval UI.** Simple UI at port 5000 for Eric to approve, reject, merge, or prioritize wishlist items. One page. Buttons that work.
6. **Convert to build-plan nodes.** Approved wishlist items → proposed `build_plan_nodes` rows.
7. **Generate next build plan.** Only after wishlist is populated and Eric has approved items.

Target: `corpus → intent extraction → categorization → wishlist → Eric review UI → build plan → implementation`

---

## 8. Implementation Plan for the Reset

### Phase A: Static Config Changes (no code changes, safe)

1. Edit `config/hcp_static.yaml`:
   - Replace HCP_01 static content (remove pipeline ceremony, Do Not Start, long-form rules)
   - Replace HCP_02 static content (remove pipeline lanes, keep only working architecture)
   - Replace HCP_05 static content (remove Do Not Start, add intake path build direction)
   - Replace HCP_06 static content (remove role ceremony, protocol, escalation wiring; add 3 development rules + replacement sentence)
   - Compress HCP_03 static content (ADR decisions to one-line)
   - Simplify HCP_09 static content (remove architecture theory terms)
   - HCP_00, HCP_04, HCP_07, HCP_08: minimal changes

2. Edit `config/agents_static.yaml`:
   - Remove §2 Do Not Start content
   - Remove §10 Verification Hardening Rule content
   - Remove §11 Role Identity Rule content
   - Remove §11.5 READ_ONLY_STANDING_BY content
   - Remove §13 Evidence-Backed Response Rule content
   - Remove §7 Active Blockers content (except BLK-SEED-004 as factual note)
   - Remove §9 Eric Gate Status content
   - Add replacement development rules
   - Add replacement sentence

### Phase B: Regenerate and Verify

3. Run `generate_all.py` to regenerate AGENTS.md and all HCP files from new static configs.
4. Run `gate_export_agreement.sh` to verify hashes match manifest.
5. Run AGENTS.md canary test across all 4 active profiles.
6. Git commit the static config changes + regenerated outputs.

### Phase C: Quarantine (Optional)

7. Move stripped governance content into a `docs/archive/governance_ceremony_2026-06-18.md` reference document (not loaded by any gateway). This preserves the design intent without burdening active sessions.

---

## 9. What Governance Becomes in the Finished App

Not deleted — relocated. Governance is implemented as working product behavior:

| Governance concept | App implementation (future) |
|---|---|
| Eric Gate | Visible approval button in UI. Write-path blocked until clicked. |
| Reviewer loops | Automated Drafter→Reviewer deliberation via orchestrator.py. Eric sees results in UI. |
| Staged promotion | Staging tables. Proposed rows vs. authoritative rows. Promotion requires UI approval. |
| Classifier authority | Router classifies and routes, but output is a suggestion in a queue, not direct state write. |
| Role routing | API-level routing. Profiles cannot self-assign roles. |
| Build-plan approval | build_plan_nodes require explicit approval in UI before implementation. |
| Evidence panels | UI panels showing what changed, where it came from, how it was verified. |
| Conflict detection | Spine query that surfaces contradictions instead of silently overwriting state. |
| Do Not Start | Database constraint: node cannot enter IN_PROGRESS unless dependencies are COMPLETE. |

---

## 10. Final Rule

If a governance rule matters, build it into CIS.

If it only exists as repeated advisor language, remove it from the development context.

That is the reset.

---

## Session Update — 2026-06-27

This document's topic (governance reset) was not directly advanced this session.
The major work completed: knowledge base ingestion (287K messages, FTS5 + ChromaDB),
abstraction layer (5 endpoints including human-readable status), intent alignment
pipeline, and roadmap. See **DEV-PIVOT-05 §10** and **DEV-PIVOT-06 §10** for the
full session handoff (gateway status, Eric's feedback, Phase 1 next steps).
Commit: 70e73bd.
