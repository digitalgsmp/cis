# CIS Build — Working Scratchpad

**Started:** 2026-05-14
**Purpose:** Brain dump and partial todo list for the CIS build conversation
**Status:** ACTIVE — add items as they come up

---

## Open Questions & Things To Figure Out

- What tools does the creative director need in reach?
- What routines does the system perform automatically vs on-demand?
- What's the rhythm of a work session — how does material flow in, get processed, and come back useful?
- Cloudflare Tunnel for field access: Access is active on api.creative-intelligence-system.com for Eric only. Next question is whether mobile/field login works reliably in practice.
- Client list: free-text client_name is temporary — when does it become a managed list with its own table?

## Ideas That Came Up

- Hermes as primary tool — tracks thoughts, keeps user on path, reminds what was done and what's next
- Other tools: hardware, other models (Claude/ChatGPT), agents, stored materials needing extraction/categorization/normalization
- Competing interests for time/attention: home, body, mind, work, partner, family, projects in development, CIS philosophy, CIS infrastructure, revenue streams, business
- Everything in life needs to be managed into a virtuous cycle
- **Start with:** understanding where the infrastructure is and what remains to be completed
- **Triangulation workflow (confirmed):** manual copy-paste into Claude and ChatGPT for review angles, then paste into Hermes to execute. This is the viable method. The burden removed is coding, not the cross-referencing.
- Security in decisions comes from reviewing ideas from enough angles — the human director is the hub, not the bottleneck
- **WIAS spreadsheet** is the analogue to CIS — it encodes project objects, workflow states, schedule slots, tool registry, taxonomies, all as a repeating production operating system. CIS needs to run life like that — not strict timeline, but certain domains need regular review/update/completion.
- Tools will always be changing — swapping in/out. First project setup is broad because multiple agendas are trying to catch up.
- **The tracking problem:** I need a simple file (last/now/next/files touched) that I update so you can see what's happening. But Claude/ChatGPT took this need and built ADRs, contracts, round tracking — the infrastructure of memory instead of the thing itself.
- **The extraction files are the accumulated experience.** 416 CIS files + 1,092 SWA files. We solved problems getting here. Those solutions need to be reusable, not lost in scattered chats.
- **Next step for CIS:** Index the extraction files so they're searchable — vectorize them, then query during build work to find existing solutions. But need to research methods first.
- **The web search problem** — came up in a previous chat, got lost. Part of the larger memory problem.
- **The user is currently functioning as the persistent memory.** That cognitive load needs to transfer to the system.
- **Project map (flowchart) idea:** A large visual flowchart of the entire project showing current position, branches, decisions made. Each node clickable to see the narrative of why that branch happened. Would show the dynamic working across all projects.
- **Current Branch card** should be a button that opens an overlay or page with the full narrative + a flowchart snippet of the branch context.

## Decisions Made

- CIS and SWA are separate projects — treat them independently
- The extraction files are the accumulated solutions — index them for search rather than re-read manually
- First project is CIS — the creative studio operating system

## Things To Build / Do

- [x] Single-click desktop button for CIS Workbench (cis_kernel_v3.html)
- [x] Session Record page (mod_session.html)
- [x] Auto-pipeline: upload → vision model → describe
- [x] Project flowchart map (Mermaid.js, Map tab)
- [x] **Set up React Flow as the UI foundation**
  - Vite + React Flow project at `/mnt/projects/cis/runtime/ui/`
  - Interactive node graph with clickable narrative overlays
  - **Node creation** — "+ New Node" button or double-click canvas opens a form (label, narrative, status picker)
  - New nodes save to both the graph and the drafts API
  - Edge connections draggable between nodes, deletable with Delete key
  - Desktop shortcut: `/home/eric/Desktop/CIS_ReactFlow.desktop`
  - Flask serves compiled bundle at `/ui/`
  - **Next:** Branch proposal governance cards, status change buttons, export to session log

---

## 2026-05-24 — Post-Reboot Recovery & Smoke Test

### Post-Reboot Advisor Chat Recovery (HHR-FIX-003, COMPLETE)

**Issue:** After server reboot, Advisor Chat UI loaded but all model panels failed.

**Root causes:**
1. `hermes-gateway.service` had `HERMES_HOME=/home/eric/.hermes-r1` — port 8642 dead
2. `hermes-gateway-r1.service` blocked — port 8643 hijacked by misconfigured service
3. `llama-vision.service` running with stale `--ctx-size 8192`, blocking port 8002
4. `llama-server-qwen.service` (ctx-size 32768) couldn't bind port 8002

**Fixes:**
1. Restored `hermes-gateway.service` to `HERMES_HOME=/home/eric/.hermes`, removed `--replace`
2. Restarted R1 gateway — claimed port 8643
3. Disabled `llama-vision.service`, started `llama-server-qwen.service` (32768 ctx)
4. All four agents verified through Flask /api/advisor/chat: PRIME_OK, V4PRO_OK, R1_OK, QWEN_OK

**Autostart verified:** All six required services enabled. No reboot gaps remain.

### Advisor Chat Browser Smoke Test (HHR-UI-006, PASS)

| UI Check | Expected | Actual | Pass/Fail |
|---|---|---|---|
| Prime panel response | PRIME_UI_OK | PRIME_UI_OK | PASS |
| V4-Pro panel response | V4PRO_UI_OK | V4PRO_UI_OK | PASS |
| R1 panel response | R1_UI_OK | R1_UI_OK | PASS |
| Qwen panel response | QWEN_UI_OK | QWEN_UI_OK | PASS |
| Parallel/Deliberate mode | R1 + V4-Pro both respond | [not tested in smoke] | — |

**UI friction observed (design, not bugs):**
- Prime in bottom-left corner — not ideal for primary first-engagement chat location
- Layout should reflect engagement flow (Prime first, then deliberation, then execution)
- Ultrawide monitor accommodates current 2x2 grid; single-monitor and mobile usability are concerns
- Subjective/aesthetic only — all panels functionally operational

---

## 2026-05-24 — Pre-Pass-5 Backups (CIS-BACKUP-001/002)

### Backup Tier Status

| Tier | Location | Status | Protection Scope |
|------|----------|--------|------------------|
| 1 — Local VM | `/mnt/archive/cis_backup_20260524_112430.tar.gz` | ✅ COMPLETE | VM-level: file loss, accidental deletion, bad config edit, botched migration |
| 2 — Proxmox host | *not yet copied* | ⏳ OPTIONAL | Same-site: VM corruption, VM deletion. Does NOT protect against host/storage/hardware failure |
| 3 — Cloud/offsite | Google Drive | ✅ COMPLETE | Off-machine: host failure, storage failure, hardware loss, site disaster |

**Tier 1 details:**
- Archive: `/mnt/archive/cis_backup_20260524_112430.tar.gz` (120MB, 2,749 files)
- SHA256: `/mnt/archive/cis_backup_20260524_112430.sha256` — verified OK
- Contents: full CIS project tree, all 3 databases, audit reports, scratchpad, all 7 systemd service files, core backend + frontend source
- Excluded: API keys (cis-flask.env, ~/.hermes*/.env), build artifacts, sessions, logs

**Tier 3:** Eric confirmed manual copy of archive + SHA256 to Google Drive. Off-machine backup exists.

### Gates

| Gate | Status |
|------|--------|
| Pass 5 **planning** | ✅ May proceed — local + cloud backups exist |
| Pass 5 **implementation** (schema changes, migrations, data promotion) | 🚫 GATED — requires Eric explicit approval to begin implementation |
| Proxmox snapshot issue | 🔴 OPEN — Google Drive backup mitigates loss risk but snapshots remain the preferred host-level recovery path |

---

## 2026-05-26 — Schedule/Todo Page Rebuild

**Summary:** Pulled forward the Schedule page from the CIS Foundation build plan (Phase 3) for immediate usability. Rebuilt as a calendar-first task/status system at `/ui/schedule` using FullCalendar v6.

### What was built

- FullCalendar page with month/week/day views, events colored by domain
- schedule_items table in `/mnt/projects/cis/memory/cis_app.db` (replaced old schedule_slots)
- Item types: task, deadline, appointment, attention_item
- Date model: presented_date (NOT NULL), due_date (nullable), scheduled_date (nullable)
- Calendar display priority: scheduled_date → due_date → presented_date
- Statuses: open (Noted), scheduled (Not Started), in_progress (Started), waiting (Waiting), blocked (Blocked), done (Done)
- Human-readable status labels with clickable badges, tooltip, status dropdown in edit modal
- started_at auto-set when status→in_progress (COALESCE preserves existing)
- completed_at auto-set when status→done, cleared when moved from done
- Outcome field for result/resolution
- Companion list sidebar: TODAY, OVERDUE, UPCOMING, DONE — all use display_date, exclude done
- Conditional form fields per item_type (appointment shows time dropdowns, deadline requires due_date, attention_item has no due/scheduled)
- Start/end time are dropdown selectors (hour 00-23, minute 00/15/30/45)
- Local timezone date helper (getFullYear/getMonth/getDate) — fixed UTC rollover bug
- Domain filters: All | Personal | Work | Clients
- capture_notes table created separately (note #1 saved)

### Final verification state

After the local-date fix:

* TODAY: 3
* OVERDUE: 0
* UPCOMING: 1
* DONE: 0

Status: usable for live testing, not final. Next action is Eric entering real Personal / Work / Client items and reporting bugs/usability blockers only.

Captured note:

* capture_notes #1: "attention_item promotion to task/deadline — add to edit modal after current implementation"

### Files changed
- `/mnt/projects/cis/runtime/cis_db.py` — new CRUD functions (create/get/update/delete_schedule_item)
- `/mnt/projects/cis/runtime/api/app_api.py` — updated schedule routes
- `/mnt/projects/cis/runtime/ui/src/api.js` — renamed functions
- `/mnt/projects/cis/runtime/ui/src/pages/SchedulePage.jsx` — complete rewrite (~778 lines)
- `/mnt/projects/cis/runtime/ui/src/pages/SchedulePage.css` — FullCalendar dark theme + new styles (~357 lines)
- `/mnt/projects/cis/memory/cis_app.db` — 3 schema migrations (schedule_slots→schedule_items, date→3-date model, added blocked)

### Open schedule items (do not start unless approved)

1. Field access via Cloudflare Tunnel — SECURITY GATE CLOSED. Cloudflare Access is active on `api.creative-intelligence-system.com` (Eric only). Schedule page no longer publicly exposed. Next: verify mobile/field login works reliably in practice.

2. Client list selector — replace free-text client_name with a managed client list. Do not create a clients table until approved.

3. Recurring appointments — design phase only, not yet started.

4. Attention item promotion UI workflow — edit modal path from attention_item to task/deadline without losing original presented_date.

5. DONE tab search/filter.

6. Quick Capture integration — connect capture_notes to schedule_items while keeping tables separate.

### Boundaries

Original CIS Foundation build plan — gateway config, KB wiring, advisor personalities, UI reorganization — remains paused. Do not resume until Eric explicitly returns to it.

The Schedule page is usable for live testing, not final. Future Schedule work must be explicitly approved and should prioritize:

1. real-world field use testing
2. client selector/list design
3. authenticated remote access review
4. only then broader dashboard integration

### Schedule Field-Use Extension — Progress Notes, Mileage, and DAP Support

**Purpose:** Extend the Schedule/Todo page into a field-work evidence capture system that helps Eric keep up with daily work obligations, progress notes, billing documentation, and mileage tracking.

**Current real-world inputs:**
- Proton Mail emails
- Proton Calendar / .ics calendar records
- Android phone calls
- Android text messages accessed through Microsoft Phone Link
- manual notes
- client-specific tasks/deadlines
- travel mileage for billing

**Intended workflow:**
communications + calendar + calls/texts + manual notes + mileage + client context
→ structured activity record
→ selected evidence
→ DAP draft support
→ final reviewed progress note / billing support

**Design principle:** Do not overload schedule_items. schedule_items remains the calendar/task/status shell.

**Proposed future linked tables:**

| Table | Purpose |
|---|---|
| schedule_items | calendar/task shell, unchanged |
| activity_logs | one record per client contact, visit, session, phone call, admin action, or field activity |
| communication_evidence | raw pasted/source evidence (email snippets, texts, call notes, calendar import notes), linked to activity_log |
| mileage_logs | manual mileage and optional check-in/check-out location records, linked to activity_log or schedule_item |
| dap_drafts | later generated draft notes from selected evidence only |
| clients | future managed client list, not approved yet |

**Build order for future session:**
1. Schema inspection only — no implementation.
2. Propose minimal activity_logs table + Add Session Notes panel.
3. Add mileage_logs with manual mileage entry first.
4. Add browser geolocation/check-in/check-out only as optional enhancement.
5. Add communication_evidence paste lanes.
6. Do not build DAP draft generator until at least one week of real activity_logs exist.
7. Before DAP generator, design anonymization/token strategy and field-selection workflow.

**DAP rule:** DAP drafts must use only explicitly selected evidence fields. Never auto-select all evidence. Never infer facts. Never generate from hidden context. Eric must choose which evidence fields are included before generation.

**Privacy/PHI rule:** Do not send client-identifiable note content to cloud models by default. Any DAP drafting with client-identifiable data should be designed for local processing or anonymized/tokenized processing unless Eric explicitly approves another route.

**Mileage rule:** Manual mileage is authoritative. Browser geolocation may support check-in/check-out later, but it must remain optional and reviewable.

**Next-session fork:** A future session may choose one of two paths:
- **Path A:** Continue Schedule Field-Use Extension, starting with schema inspection for activity_logs design.
- **Path B:** Return to BUILD_PLAN_CIS_FOUNDATION.md Phase 1 Pre-Step.

Do not do both in one session unless Eric explicitly changes focus.

### Approved Schedule Field-Use Build Order — HARD GATE

This order supersedes any looser notes in the Schedule Field-Use Extension section.

1. Schema inspection only. No table creation, migration, endpoint creation, UI implementation, or data model change.
2. After schema inspection is reported and reviewed, propose a minimal activity_logs table and a simple Add Session Notes panel.
3. After that proposal is approved, build activity_logs and Add Session Notes as the first implementation step.
4. After activity_logs is working with real manual notes, propose mileage_logs with manual mileage entry only.
5. Browser geolocation, check-in/check-out, and automatic location support are optional later enhancements. Do not build them during the manual mileage step.
6. After activity_logs and manual mileage are stable, propose communication_evidence paste lanes attached to an activity_log.
7. Do not build any DAP draft generator until at least one week of real activity_logs exists.
8. Before any DAP generator work, design and review an anonymization/token strategy.
9. DAP drafts may use only explicitly selected evidence fields. Never auto-select all evidence. Never infer facts. Never generate from hidden context.
10. Client-identifiable note content must not be sent to cloud models by default.

---

## 2026-05-26 — Cloudflare Access Gate for Schedule Field Use

Security gate status: **CLOSED.**

### Background

The Schedule page at `/ui/schedule` was temporarily found to be exposed through:

```
api.creative-intelligence-system.com/ui/schedule
```

Initial verification showed:

- `api.creative-intelligence-system.com/ui/schedule` returned `200 OK` with no Cloudflare Access challenge
- `mcp.creative-intelligence-system.com` was already protected by Cloudflare Access
- Flask has no app-level login
- Schedule page may contain personal/work/client data

### Action Taken

Cloudflare Access application was created in the Cloudflare dashboard:

- **CIS API** → `api.creative-intelligence-system.com` → policy: Eric only
- **CIS MCP** → `mcp.creative-intelligence-system.com` → policy: MCP Service Token

### Final Verification (2026-05-27)

| Check | Result |
|---|---|
| `api.creative-intelligence-system.com/ui/schedule` | `HTTP/2 302` → redirect to Cloudflare Access login |
| API route Access protection | `www-authenticate: Cloudflare-Access` — YES |
| `mcp.creative-intelligence-system.com` | `HTTP/2 403` with `cf-access-domain` / `cf-access-aud` headers |
| `http://127.0.0.1:5000/ui/schedule` (local) | `HTTP/1.1 200 OK` — Werkzeug, LAN access intact |
| Tunnel ingress | restored: `api. → localhost:5000`, `mcp. → localhost:8888` |

### Verdict

Security gate **CLOSED.** Schedule page is no longer publicly accessible without Cloudflare Access authentication. Field-use testing may proceed through `api.creative-intelligence-system.com` only after successful Access login by Eric.

### Remaining Caution

Do not add more users or service tokens to CIS API Access without Eric approval.

---

## 2026-05-26 — CIS Foundation Documents Created

Three foundation documents were created, reviewed by Claude and ChatGPT, and approved by Eric. These replace the HCP files as primary orientation documents for all CIS sessions.

Files:

* /mnt/projects/cis/docs/CIS_CORE_BOUNDARY.md
* /mnt/projects/cis/docs/CIS_CONTEXT_CONTRACT.md
* /mnt/projects/cis/docs/CIS_CURRENT_STATE.md

Purpose:

* CIS_CORE_BOUNDARY.md — defines what CIS is for, five core capabilities, what it will never do, and the definition of done
* CIS_CONTEXT_CONTRACT.md — defines session briefing rules, source authority hierarchy, side-quest stop rule, verification rules
* CIS_CURRENT_STATE.md — live state document, current objective, blockers, decisions, open questions, execution order

These three files must be read at the start of every CIS session before any build work begins. They are the shared truth surface for Claude, ChatGPT, Hermes, and Eric.

Status: APPROVED — do not modify without Eric's explicit instruction.

---

## 2026-05-26 — CIS Foundation Build Plan Status

File: /mnt/projects/cis/docs/BUILD_PLAN_CIS_FOUNDATION.md
Version: 1.4
Status: APPROVED by Claude and ChatGPT — ready to execute

The plan is not just paused — it is fully reviewed and approved. Execution begins at Phase 1 Pre-Step, schema/config verification, when Eric returns to the foundation build.

Phase order:

* Phase 0: DEFERRED — Proxmox/backup safety net. Google Drive backup integrity unverified; Eric accepted risk.
* Phase 1: Gateway configuration — ready to start.
* Phase 2: Knowledge base wiring.
* Phase 3: UI reorganization.

Do not resume until Eric explicitly returns to this plan. Current priority is Schedule page field use and client list design.

---

## 2026-05-28 — Storage Blocker Resolved (CIS-INFRA-STORAGE-001)

### What was completed

- `/usr/local/bin/cis-snapshot` deployed on `root@wander`
- Script detaches passthrough drives virtio2/3/5/6, snapshots VM 100 on local-lvm, reattaches and verifies exact match
- Config backup dir: `/root/cis-vm100-config-backups`
- Test snapshot `cis-storage-script-test-20260528` created and verified — 3 LVM-thin volumes (virtio0, virtio1, efidisk0), snapshot chain now 4 entries
- All four passthrough drives verified exact-match after reattach (virtio2, virtio3, virtio5, virtio6: MATCH)
- VM 100 restarted afterward — CIS functioning
- LVM thin-pool at 45% — normal overprovisioning, no action needed

### Decisions logged

- INFRA-001: CIS-INFRA-STORAGE-001 Complete (logged via /api/decisions, response: {"success":true})
- ADR-050: CIS Execution Harness Model Hierarchy and Memory Architecture (logged via /api/decisions, response: {"success":true})
  - Tier 1: Prime (V4-Pro Fast) — brainstorm companion
  - Tier 2: R1 + V4-Pro Reasoner — adversarial deliberation pair
  - Tier 3: Claude + ChatGPT — escalation-only, cost-gated
  - Tier 4: Qwen local — execution worker

### Deferred

- CIS-INFRA-STORAGE-002 — Design host-side snapshot trigger/control plane (logged to collab_next_actions, status: DEFERRED)
  - Executor must live outside VM 100 (safe default requires VM shutdown)
  - Do not build UI, add Flask-to-host SSH, or implement

### Next session priority

Phase 2 — read-only gateway verification and repair:
- Inspect service files, HERMES_HOME values, port bindings
- Confirm Prime / Reasoner / R1 / Qwen current behavior
- Repair one item at a time, only after verification

### Boundary

Do not resume Schedule field-use, VDB, Telegram/Discord, Briefing Center UI, Notes DB, snapshot trigger work, or harness executor work unless Eric explicitly changes focus.

### Proxmox snapshot no longer blocked

The passthrough drive obstacle is resolved. Snapshot orchestration must live outside VM 100.

---

## 2026-05-29 — Phase 2 Gateway Verification & Repair (COMPLETE)

### What was completed

- Read-only inspection of all 5 user-level Hermes systemd services
- Config file comparison across .hermes, .hermes-r1, .hermes-qwen
- Root cause identified: hermes-gateway.service (Prime) had HERMES_HOME=/home/eric/.hermes-r1 — same config as R1
- Both services read the same config → port collision → R1 crash loop (223 restarts, exit code 1)
- Repair: single-line change — Prime HERMES_HOME from /home/eric/.hermes-r1 → /home/eric/.hermes
- Backup: hermes-gateway.service.bak.20260529_133352
- After repair: Prime on 8642 (.hermes, deepseek-v4-pro), R1 on 8643 (.hermes-r1, deepseek-reasoner), Qwen on 8644 (.hermes-qwen, local qwen3-vl)
- Behavioral verification: same prompt to all three gateways — all returned distinct responses confirming different models

### Current gateway state

| Gateway | Port | HERMES_HOME | Model | Status |
|---------|------|-------------|-------|--------|
| Prime   | 8642 | /home/eric/.hermes | deepseek-v4-pro | Running, collaboration-governance persona |
| R1      | 8643 | /home/eric/.hermes-r1 | deepseek-reasoner | Running, chain-of-thought reasoning |
| Qwen    | 8644 | /home/eric/.hermes-qwen | qwen3-vl-30b (local) | Running, generic assistant |
| llama   | 8002 | — | qwen3-vl-30b (Q4) | Running |

### Decisions logged

- INFRA-002: Phase 2 Repair 1 — Prime gateway HERMES_HOME corrected (API: success)
- INFRA-003: Phase 2 Complete — Gateway behavioral verification passed (API: success)

### Remaining gaps (context-loading, not gateway config)

- R1 role description stale — describes itself as executor, not deliberation partner
- Qwen lacks CIS-specific context injection — expected for local model with no skills/memory
- Reasoner gateway/service from ADR-050 remains separate follow-up scope

### Next session priority

Phase 3 — session-start context loading: Layer 1 briefing auto-load, Layer 2 retrieval design, notes capture command.

### Boundary

Do not resume Schedule field-use, VDB, Telegram/Discord, Briefing Center UI, Notes DB, snapshot trigger work, harness executor work, or CIS Foundation Build Plan Phases 1–3 unless Eric explicitly changes focus. Reasoner gateway/service is a separate follow-up, not Phase 3A scope.

---

## 2026-05-29 — Phase 3A Reframe (CANONICAL UPDATE)

### What was completed

- Phase 3 reframed as Phase 3A: Automatic Context Loader v0.1 + Seed Intent Orientation + Structured Handoff Format
- Seed intent corpus created from raw Hermes session archive
  - 1,367 session files scanned for vision signal phrases
  - 120 candidates, top 5 excerpted — Eric's exact words preserved
  - /mnt/projects/cis/seed_intent_corpus/SEED_INTENT_EXCERPTS.md
  - /mnt/projects/cis/seed_intent_corpus/SESSION_ORIENTATION_PROMPT.md
- /mnt/projects/cis/session_handoffs/ created
- Structured handoff format: HANDOFF_YYYYMMDD_HHMM_<phase>.md
- All canonical files updated to Phase 3A
- Fresh handoff generated for Claude/ChatGPT pass-forward

### Core architectural statement

These are not competing paths — they are sequential layers:
automatic context loading → seed intent corpus → Prime/V4-Pro coordination → R1 adversarial critique → Qwen local worker → SQLite deterministic memory → VDB/Chroma semantic search → raw session archive → CIS as broad creative assistant

### Phase 3A failure conditions documented

- Eric still manually pastes handoff
- Briefing lacks seed intent
- Only Prime gets context (R1/Qwen blind)
- Hermes builds infra instead of loader
- Raw intent replaced by model summary
- No structured handoff format for Phase 3B

### New decisions recorded

- Seed intent excerpts from raw archive scan must be in context orientation
- Prime, R1, Qwen must share same loaded context for adversarial loop
- Phase 3B automates Hermes-to-Hermes continuation via structured handoff
- SQLite and VDB remain fundamental later layers — not abandoned
- CIS scope preserved as broad creative assistant
- Claude/ChatGPT paid API access for pass/fail review (design phase)
- Hermes capabilities audit needed (skills/tools/config)

### Next session priority

Phase 3B — Automated Session Continuation. Wire the Phase 3A context briefing
generator into actual session startup so Eric is removed from the context loop.

### Boundary

Do not build Chroma, SQLite schema, dashboard, or governance. Do not start broad archive ingestion. Do not implement the full loader yet — document the architecture first.

### Files changed this session

- /home/eric/.config/systemd/user/hermes-gateway.service (HERMES_HOME line)
- /mnt/projects/cis/docs/CIS_CURRENT_STATE.md (v1.0 → v1.1 → v1.2 → v1.3)
- /mnt/projects/cis/cis_kernel/build/CIS_SCRATCHPAD.md (Phase 2 + Phase 3A + Phase 3A closeout)
- /mnt/projects/cis/PROJECT_CONTEXT_PACK/07_RECENT_HANDOFF.md
- /mnt/projects/cis/PROJECT_CONTEXT_PACK_UPLOAD/HCP_07_RECENT_HANDOFF.md
- /mnt/projects/cis/tools/generate_context_briefing.py (created)
- /mnt/projects/cis/session_handoffs/CURRENT_CONTEXT_BRIEFING.md (created)
- /mnt/projects/cis/docs/BUILD_PLAN_CIS_FOUNDATION.md (one-line note)

---

## 2026-05-29 — Phase 3A v0.1 Closeout (IMPLEMENTATION PASS)

### What was implemented

- `/mnt/projects/cis/tools/generate_context_briefing.py` — 210 lines, Python stdlib only
- Single command: `python3 /mnt/projects/cis/tools/generate_context_briefing.py --write`
- Generates `/mnt/projects/cis/session_handoffs/CURRENT_CONTEXT_BRIEFING.md` (260 lines)
- 10 briefing sections including seed intent (16 raw Eric blockquotes)
- Zero new dependencies, zero Flask routes, zero Chroma/VDB/SQLite/UI changes

### Verification

- Phase 3A: 8 matches
- Seed intent: 15 matches
- Prime/R1/Qwen: 14 matches
- Do-not-start boundaries: 10 matches
- Layer 2 status: 2 matches
- Structured handoff / Phase 3B: 5 matches

### Current state after closeout

- Phase 3A: COMPLETE — single-command context briefing generation works
- Phase 3B: CURRENT — automated Hermes-to-Hermes continuation
- CIS_CURRENT_STATE.md: v1.3
- Eric no longer has to manually assemble the handoff

### Active next priority

Resolve OQ-010 first (generator source hierarchy vs Project Context Pack),
then OQ-009 (hermes-gateway.service HERMES_HOME anomaly), then scope Phase 4B.

Phase 4B candidate: General deterministic verification jobs layer
(verification_jobs table, verifier script library, Flask trigger endpoint,
standard exit-code capture, later Qwen/R1 review routing).

Phase 3B — PASS (2026-05-29): briefing auto-loads via ~/.hermes/.env +
run_agent.py injection. Eric fully removed from manual paste loop.

Phase 4A standalone verifier — PASS (2026-05-29):
/mnt/projects/cis/tools/verify_context_briefing_freshness.py
9/9 tests passed. Exit-code convention documented.

Phase 4A Integration — PASS (2026-05-29):
/home/eric/.local/bin/hermes wrapper now runs the deterministic freshness
verifier before every interactive Hermes command. Fail-closed: missing
verifier, stale context after failed regeneration, or hard failures all
block Hermes startup. 7/7 tests passed. Eric no longer manually checks,
regenerates, exports, or pastes context before starting Hermes.

OQ-009: hermes-gateway.service HERMES_HOME anomaly (OPEN).
OQ-010: generator vs Project Context Pack source hierarchy (OPEN).

SQLite, VDB/Chroma, and raw archive ingestion remain future required layers.
CIS remains broad creative assistant infrastructure.

---

## 2026-05-30 — V4-Pro Verification Gate + State File Reconciliation

### V4-Pro verification of CIS_CURRENT_STATE.md v1.3

V4-Pro reviewed the state file against session activity and found 6 discrepancies:

1. Prime model role — CIS_CURRENT_STATE.md didn't reflect the governed role split
   (brainstorm vs design/build vs verify vs execute)
2. V4-Pro had no operational role in the state file
3. Execution Order section contradicted Current Objective section
4. Version string still read v1.3 after content was updated
5. Phase 4A undocumented despite being completed
6. Generator 8-source update not reflected in state file

All 6 resolved in CIS_CURRENT_STATE.md v1.4.

### Model role governance established

| Role | Function | Boundaries |
|------|----------|------------|
| Prime (v4-pro) | Brainstorm, propose, discuss | No file writes, no code, no terminal, no patches |
| R1 (deepseek-reasoner) | Verify everything, challenge Prime | No execution, no code generation |
| Qwen (local) | Execute after deliberation converges | No deliberation, no design decisions |

### Files changed

- /mnt/projects/cis/docs/CIS_CURRENT_STATE.md (v1.3 → v1.4 — all 6 discrepancies fixed)
- Added Model Roles table, Phase 3B/4A completion entries, V4-Pro verification gate,
  Google Drive connection status, Deliberate button blocker, OQ-010 resolved,
  role enforcement subtask, corrected Execution Order section

### Next

Regenerate context briefing with corrected state file. All 8 source files aligned.

---

## 2026-05-30 — Gates 2-6A: V4-Pro Gateway, NeMo Guardrails, Tavily

### Gate 2 — V4-Pro Thinking Gateway (PASS)
- Created `~/.hermes-v4pro/` profile with deepseek-v4-pro, reasoning_effort xhigh
- Patched `run_agent.py` `_supports_reasoning_extra_body()` for api.deepseek.com
- Patched `plugins/model-providers/deepseek/__init__.py` with `DeepSeekProfile.build_api_kwargs_extras()`
- Direct DeepSeek API call now sends `thinking: {"type":"enabled"}` and `reasoning_effort`
- Response includes `reasoning_content` and `completion_tokens_details.reasoning_tokens`

### Gate 3 — Wire Four Roles (PASS)
- R1 upgraded from deepseek-reasoner to deepseek-v4-pro with thinking (port 8643)
- V4-Pro gateway corrected from 8642 to 8645
- DB `agent_instances` updated: hermes-r1→deepseek-v4-pro, hermes-v4pro→8645
- AdvisorChat.jsx labels updated: Fast, V4-Pro R1, V4-Pro R2/Critic, Qwen Worker/Judge
- Frontend rebuilt. All four panels verified through Flask API

### Gate 4A — Persist V4-Pro Gateway (PASS)
- `hermes-gateway-v4pro.service` created at `~/.config/systemd/user/`
- `HERMES_HOME=/home/eric/.hermes-v4pro`, port 8645
- Survival test: restart succeeded, new PID, curl returns reasoning

### Gate 5A-RC — Native NeMo Root Cause (PASS)
- Two bugs found in `cis_fast` config:
  1. `actions.py` functions need `@action()` decorator for NeMo discovery
  2. `config.yml` must not have `rails: config: cis_fast` (validator crash)
- Custom proxy `cis_fast_proxy.py` preserved at `/mnt/projects/cis/runtime/rails/`

### Gate 5B — Replace Proxy with Native NeMo (PASS)
- NeMo server on port 8800 with `--default-config-id cis_fast`
- Local evidence action with `@action()` decorator
- Pass-through to deepseek-v4-flash on 8642 for normal questions
- DB + port scan for system/config questions
- NeMo utils.py patched for reasoning_content passthrough (Gate 5C fix: removed broken `usage` access)

### Gate 5C — NeMo Incompatibility with Reasoning (BLOCKED)
- NeMo's `llmrails.py:generate_async()` extracts only `role, content, tool_calls, events` from raw LLM response
- `reasoning_content` extracted from guardrail events, not raw response
- `GenerationResponse` has no `usage` field (patched incorrect `usage=response.usage`)
- Verdict: V4-Pro R1 and R2/Critic stay direct (not through NeMo)

### Gate 6A — Tavily Web Evidence Preflight (PASS)
- `verify_web_evidence_action` added to `cis_fast` with `@action()` decorator
- Colang flow triggers on current model/API/version/package/pricing questions
- Tavily search with `search_depth=advanced, max_results=5, include_answer=True`
- Missing key returns `NEEDS_TAVILY_API_KEY` — never answers from training data
- Local evidence (`verify_local_routing_action`) still works
- To enable: `export TAVILY_API_KEY=your_key` before starting NeMo

### Files changed this session (Gates 2-6A)
- `/home/eric/.hermes-v4pro/` (new profile directory)
- `/home/eric/.hermes-v4pro/config.yaml` (new)
- `/home/eric/.hermes-v4pro/.env` (new)
- `/home/eric/.config/systemd/user/hermes-gateway-v4pro.service` (new)
- `/home/eric/.hermes-r1/config.yaml` (model + reasoning_effort)
- `/mnt/projects/cis/runtime/db/cis_memory.db` (agent_instances updates)
- `/mnt/projects/cis/runtime/ui/src/pages/infra/AdvisorChat.jsx` (AGENTS array)
- `/home/eric/.hermes/hermes-agent/run_agent.py` (2 patches)
- `/home/eric/.hermes/hermes-agent/plugins/model-providers/deepseek/__init__.py`
- `/home/eric/.hermes/hermes-agent/gateway/platforms/api_server.py` (2 patches)
- `/home/eric/.hermes/hermes-agent/agent/usage_pricing.py`
- `/mnt/projects/cis/runtime/rails/.venv/` (NeMo + tavily-python install)
- `/mnt/projects/cis/runtime/rails/configs/cis_fast/config.yml`
- `/mnt/projects/cis/runtime/rails/configs/cis_fast/actions.py`
- `/mnt/projects/cis/runtime/rails/configs/cis_fast/rails/main.co`
- `/mnt/projects/cis/runtime/rails/configs/cis_v4pro_r1/` (created, not activated)
- `/mnt/projects/cis/runtime/rails/native_test/` (root cause test configs)
- `/mnt/projects/cis/runtime/rails/cis_fast_proxy.py` (preserved, not active)
- `/mnt/projects/cis/runtime/rails/.venv/lib/python3.12/site-packages/nemoguardrails/server/schemas/utils.py` (patched)
- `/mnt/projects/cis/docs/CIS_CURRENT_STATE.md` (v1.4 → v2.0)

---

## 2026-05-31 — Gate 6B: NeMo Persistent + Tavily Key (PASS)

### What was completed

- Created `nemo-fast.service` at `~/.config/systemd/user/nemo-fast.service`
- NeMo now runs as a persistent systemd service (survives reboots, Restart=always)
- TAVILY_API_KEY loaded from `/home/eric/.config/cis-rails.env` via `EnvironmentFile=`
- Key never appears in the service file, `systemctl show`, or any log
- Verified: Tavily web evidence returns real results (5 sources, AI summary)
- Verified: local evidence action (DB + port scan) still works

### Issues discovered (not blocking Gate 6B)

- Execution-claim blocking documented in briefing but NOT implemented in Colang flow
  (main.co only defines system-config and external-facts flows)
- "current external facts" pattern matching is too greedy — "what is 2+2" triggers
  a Tavily search instead of passing through to deepseek-v4-flash

### Files changed

- `/home/eric/.config/systemd/user/nemo-fast.service` (new — 750 bytes)
- `/mnt/projects/cis/docs/CIS_CURRENT_STATE.md` (v2.0 → v2.1)

---

## 2026-05-31 — Gate 6C: Fix Fast NeMo Rail Precision + Execution-Claim Blocking (PASS)

### What was completed

- Added execution-claim blocking via `block_execution_claim` action
- Added `pass_through_query` action for general/creative prompts (calls Fast directly)
- Added two new Colang intents: `user ask general question` and `user ask creative question`
- These fire BEFORE the guarded flows, preventing semantic over-matching
- All 6 Gate 6C tests PASS

### Root cause discovered

NeMo uses semantic (embedding-based) intent matching — not exact pattern matching.
"brainstorm names" matched execution patterns semantically. "what is 2+2" matched
external-facts patterns semantically. The fix: higher-priority pass-through intents
with patterns that are semantically closer to these query types.

### Accepted limitation

When new query categories appear that NeMo's classifier incorrectly routes to a
guarded flow, a new pass-through intent must be added with example patterns that
are closer to the query than the guarded flow's patterns.

### Files changed

- `/mnt/projects/cis/runtime/rails/configs/cis_fast/rails/main.co` (5 intents, 5 flows)
- `/mnt/projects/cis/runtime/rails/configs/cis_fast/actions.py` (+pass_through_query action)
- `/mnt/projects/cis/docs/CIS_CURRENT_STATE.md` (v2.1 → v2.2)

---

## 2026-05-31 — Gate 7: Advisor Loop Routing Overhaul (PASS)

### Gate 7A — V4-Pro Preflight Evidence Injection
- Added `run_fast_preflight()` to advisor.py: sends prompts to NeMo:8800 before V4-Pro
- Added `_call_gateway_with_reasoning()`: preserves reasoning_content/tokens from V4-Pro
- V4-Pro chat() and parallel() now: preflight → check block/evidence → inject system msg → call direct
- Role prompts added: V4PRO_R1_ROLE (proposal author) and V4PRO_R2_CRITIC_ROLE (adversarial reviewer)
- All 5 tests PASS (web evidence, local evidence, execution block, normal proposal, critic)

### Gate 7B — Qwen Worker/Judge Gate
- Added `validate_qwen_input()`: only accepts FINAL_DIRECTIVE or JUDGE_REQUEST packets
- Qwen chat() now blocks casual/proposal prompts with QWEN_GATE_BLOCKED
- Execute route updated to send tagged FINAL_DIRECTIVE with evidence requirements
- Qwen system prompt enforces structured VERDICT/ACTION/EVIDENCE/MISSING PROOF/NEXT REPAIR
- All 5 tests PASS (casual block, proposal block, FINAL_DIRECTIVE, JUDGE_REQUEST, execute route)

### Gate 7C — Mixed Prompt Classification Tuning
- Added 8 combined patterns to external-facts intent (creative + current/latest/API keywords)
- Mixed "draft a proposal using the current NeMo syntax" now correctly triggers Tavily
- All 5 tests PASS (mixed proposal, creative proposal, pure fact, arithmetic, local routing)

### Gate 7D — Full Advisor Loop Smoke Test
- End-to-end verified: Fast → V4-Pro R1 → V4-Pro R2 → V4-Pro R1 → Qwen Worker → Qwen Judge
- Rail misfires fixed: added directive-drafting and critique/review patterns to creative intent
- All 6 steps PASS

### Files changed across Gate 7A-7D
- `runtime/api/advisor.py` — preflight, reasoning capture, Qwen gate, execute route
- `runtime/rails/configs/cis_fast/rails/main.co` — 5 Colang intents, mixed/directive/critique patterns
- `runtime/rails/configs/cis_fast/actions.py` — block_execution_claim, pass_through_query
- `docs/CIS_CURRENT_STATE.md` — v2.2 → v2.3

### Route table (final)
- hermes-prime / Fast → 8800 NeMo → 8642 deepseek-v4-flash
- hermes-v4pro / V4-Pro R1 → 8645 direct deepseek-v4-pro thinking
- hermes-r1 / V4-Pro R2-Critic → 8643 direct deepseek-v4-pro thinking
- hermes-qwen / Qwen Worker-Judge → 8644 direct local Qwen

---

## 2026-05-31 — Router v0.1: AdvisorChat Input Router (COMPLETE)

### What was completed

- classify_route() 8-pass classifier in advisor.py
  - RESEARCH_SIGNALS, DRAFTER_SIGNALS, REVIEWER_SIGNALS word lists
  - QWEN_PREFIXES = ("FINAL_DIRECTIVE", "JUDGE_REQUEST") for deterministic gating
  - 8 passes: Qwen det. gate → Qwen override block → manual override → Reviewer → Research → multihop → Drafter → ambiguous default
- POST /api/advisor/route endpoint (auth-gated, X-CIS-API-Key)
- routing_decisions SQLite table created in cis_memory.db
- classify_only=true mode for non-destructive testing
- All 7 classify_route tests PASS + DB persistence test PASS

### V4 Implementer (New)
- Profile: /home/eric/.hermes-v4impl/ — deepseek-v4-pro, reasoning_effort xhigh
- Service: hermes-gateway-v4impl.service on port 8646
- Receives FINAL_DIRECTIVE prefix (deterministic routing)
- NeMo preflight for evidence → direct call on 8646
- reasoning_content preserved and displayed (collapsible in UI)
- Alias: hermes-implementer in ~/.bashrc

### AdvisorChat.jsx
- Shared input textarea + override select + routing banner
- 4-panel layout: Research/Evidence, V4 Drafter, V4 Reviewer, V4 Implementer
- Qwen panel removed from main UI
- Thread ID state maintained across sends

### Qwen Status
- Removed from main AdvisorChat UI and routing flow
- Stays active on port 8644
- JUDGE_REQUEST remains backend-capable but not exposed in main UI
- Possible future role: judge/evaluator for NeMo or verification

### Files changed this session
- /mnt/projects/cis/runtime/api/advisor.py (classify_route, routing_decisions, /route)
- /mnt/projects/cis/runtime/ui/src/pages/infra/AdvisorChat.jsx (shared input, 4-panel)
- /home/eric/.hermes-v4impl/config.yaml (new)
- /home/eric/.hermes-v4impl/.env (new)
- /home/eric/.config/systemd/user/hermes-gateway-v4impl.service (new)
- ~/.bashrc (hermes-implementer alias)
- SQLite: routing_decisions table in cis_memory.db

### Route table (Router v0.1)
- hermes-prime / Research/Evidence → 8800 NeMo → 8642 deepseek-v4-flash
- hermes-v4pro / V4 Drafter → 8645 direct deepseek-v4-pro thinking
- hermes-r1 / V4 Reviewer → 8643 direct deepseek-v4-pro thinking
- hermes-v4impl / V4 Implementer → 8646 direct deepseek-v4-pro thinking (xhigh)
- hermes-qwen / Qwen → 8644 direct local Qwen (deferred from UI)

### Next session (corrected order — 2026-05-31)
Do not proceed directly to Phase 4B. The AdvisorChat.jsx truncation event
exposed a critical rollback/recovery gap. Corrected queue:
1. GitHub/git versioning — protect CIS source files before further edits
2. AdvisorChat UI layout/readability improvements
3. Router usability validation — confirm one-input workflow for ChatGPT/Claude/Eric
4. Reinforcement: Archon-style verifier DAG planning and implementation
5. Phase 4B — knowledge base extraction from Google Drive transcripts (deferred)
6. OQ-009 — hermes-gateway.service HERMES_HOME anomaly


---
## Gate 7E Closeout — AdvisorChat Input Router v0.1 — 2026-05-31

- classify_route() 8-pass classifier added to advisor.py
- POST /api/advisor/route implemented and auth-gated (X-CIS-API-Key)
- routing_decisions table created in cis_memory.db
- V4 Implementer profile live: hermes-v4impl, port 8646, deepseek-v4-pro, xhigh reasoning
- FINAL_DIRECTIVE prefix routes deterministically to v4_implementer
- JUDGE_REQUEST prefix routes deterministically to qwen (backend only)
- NeMo preflight → direct 8646 for V4 Implementer (reasoning_content preserved)
- Research + Drafter signals trigger multihop: fast preflight → v4_drafter final
- Shared input + routing banner + 4-panel UI live in AdvisorChat.jsx
- Qwen removed from main AdvisorChat UI and routing; deferred to judge/evaluator only
- Backend tests: 10/10 pass. UI tests: 7/7 pass.
- Startup note: hermes-gateway-v4impl.service had port 8642 conflict on first
  start (HERMES_HOME pointed at /home/eric/.hermes). Recovered on restart.
  Log as open question alongside OQ-009.

---
## Verification-Hardening Rule — 2026-05-31

**Rule:** V4 Implementer self-report is not a source of truth. Completion is
accepted only after deterministic evidence verifies the result.

**Accepted evidence sources:**
1. Git diff / file system state
2. Build and test command output
3. Database queries
4. Endpoint/curl responses
5. Service health checks
6. Browser/UI verification
7. Independent reviewer/verifier pass/fail

**Post-implementation workflow:**
1. V4 Implementer executes approved directive.
2. V4 Implementer reports claimed files changed and tests run.
3. A separate verification gate checks deterministic evidence.
4. Completion is marked PASS only if evidence matches directive scope.
5. Missing/ambiguous/self-reported evidence → UNVERIFIED.

**Updated next-session queue (2026-05-31):**
1. GitHub/git versioning (blocking)
2. Post-implementation verification gate design
3. UI layout/readability improvements
4. Router usability validation
5. Archon-style verifier DAG
6. Phase 4B (deferred until infrastructure stable)
7. OQ-009

---

## Patch Failure Recovery Rule — 2026-05-31

**Rule:** If V4 Implementer receives a patch/tool error, it must not blindly
retry the same patch.

**Required behavior:**
1. Classify the error:
   - old_string not found → target text changed or stale instruction
   - multiple matches → patch target too broad
   - file line count drops unexpectedly → possible truncation/corruption
   - permission error → stop and report
   - timeout/stream drop → check service/log status before retrying
2. Inspect current file state before retrying.
3. Use grep/search to locate current target text.
4. If replacement is risky or ambiguous, append a new dated section instead of
   replacing text.
5. After two failed patch attempts, stop and ask for operator approval.
6. Never rewrite a full source file from memory.
7. Never use partial file reads for full-file rewrites.
8. Always report: exact tool error, suspected cause, files touched, files not
   touched, safest recovery option.

**Reference incident:** The AdvisorChat.jsx truncation event (2026-05-31)
proved why this rule exists.

---

## 2026-05-31 — Phase 0 Recovery: Git Versioning + Gateway Repair + Context Injection

### What was completed

- Git versioning: `.gitignore` created (629 source files tracked, 74GB excluded),
  initial commit `b1bcf7d`, private GitHub repo at https://github.com/digitalgsmp/cis
- GitHub CLI installed and authenticated (digitalgsmp, token-based HTTPS)
- Context briefing injection extended to all gateway profiles:
  `HERMES_CIS_BRIEFING_PATH` added to `.hermes-v4pro/.env`, `.hermes-r1/.env`,
  `.hermes-v4impl/.env`, `.hermes-qwen/.env`
- All three active V4 gateways verified context-aware via one-shot test
- Stale r1 process (PID 249591) killed, r1 service restarted successfully
- All three V4 Pro gateways verified: healthy, correct model (deepseek-v4-pro),
  reasoning xhigh, context briefing loaded
- Architecture clarified: Judge = deterministic NeMo/Python checklist (not a
  reasoning model), Orchestrator = backend state machine (not Flash)
- Qwen confirmed paused / out of active implementation
- R1/DeepSeek Reasoner confirmed retired from active assumptions
- `hermes-gateway-r1` is a stale service name only; actual role is V4 Reviewer

### Corrected Architecture

| Role | Port | Model | Reasoning | NeMo? |
|------|------|-------|-----------|-------|
| Flash/Research | 8642→8800 | deepseek-v4-flash | — | Yes |
| V4 Drafter | 8645 | deepseek-v4-pro | xhigh | No |
| V4 Reviewer | 8643 | deepseek-v4-pro | xhigh | No |
| V4 Implementer | 8646 | deepseek-v4-pro | xhigh | No |
| Judge | NeMo 8800 | no model | none | IS NeMo |
| Orchestrator | orchestrator.py | no model | none | No |
| Qwen | 8644 | (paused) | — | — |

### Canonical docs updated
- docs/CIS_CURRENT_STATE.md (v2.4 → v2.5)
- cis_kernel/build/CIS_SCRATCHPAD.md (this entry)
- PROJECT_CONTEXT_PACK/01, 05, 07, 08

### Next session
Minimal orchestrator scaffold (orchestrator.py state machine with
Drafter→Reviewer deliberation loop only). No Judge, no Verifier, no UI.
