# Brain Chat & Backchannel Interjection Pattern (2026-07-11)

## Eric's Interaction Model

Eric's explicit correction — do NOT design checkpoint-based interaction:

> "I'm not looking for it to have checkpoints either, I don't want to
> micromanage. I want to do what I said, passively observe sometimes, then
> when inspired to interject a thought or observation. I don't want to
> stop the flow, I want it to be able to be able to incorporate my input."

> "I was disappointed when I looked at the apps ui, I envisioned talking
> to brain, explaining my idea and the pipeline would start, I would get
> to watch the deliberation and verification. what I got is something
> that is not that."

**The model**: Pipeline runs continuously. Eric observes passively by
default. When inspired, he types into the observation chat (backchannel).
His messages are stored and consumed by the next phase automatically.
No pausing, no blocking, no approval gates at every step.

**What NOT to build**:
- Checkpoints at every phase boundary (Eric explicitly rejected this)
- Mandatory approval at each phase (that's micromanagement)
- Stop-and-wait patterns (breaks the flow)

**What TO build**:
- Live observation feed (phases appear as they happen)
- Always-available chat box (backchannel input, never blocks)
- Interjections consumed automatically by downstream phases
- Brain as conversational pre-pipeline interface (not a form)

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    CIS Control Panel UI                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │  Brain Chat   │  │ Pipeline Live│  │  Runs List   │       │
│  │ (pre-pipeline)│  │ (observation)│  │  (history)   │       │
│  │               │  │              │  │              │       │
│  │ Chat with     │  │ Phase feed   │  │ Recent runs  │       │
│  │ Brain + KB    │  │ + backchannel│  │ click→observe│       │
│  │               │  │ input box    │  │              │       │
│  └──────┬────────┘  └──────┬───────┘  └──────────────┘       │
│         │                  │                                  │
└─────────┼──────────────────┼──────────────────────────────────┘
          │                  │
          ▼                  ▼
    POST /api/relay/    POST /api/relay/<run_id>/interject
    brain/chat          (stored in pipeline_interjections)
    brain/start              │
                              │ consumed by
                              ▼
                    _consume_interjections() in _pre_discovery()
                    → injected into next phase's prompt
```

## Database Schema (Migration 0028)

```sql
-- Pre-pipeline brain conversations
CREATE TABLE brain_chats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,       -- groups messages in one conversation
    role TEXT NOT NULL,             -- 'user' or 'brain'
    content TEXT NOT NULL,
    kb_context TEXT,                -- KB context injected (for audit)
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Mid-pipeline interjections (backchannel)
CREATE TABLE pipeline_interjections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    message TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    consumed_by_phase TEXT,         -- which phase consumed it
    consumed_at TEXT
);
```

## API Endpoints

### Brain Chat (pre-pipeline)

- `POST /api/relay/brain/chat` — talk to Brain with KB context
  - Body: `{message, session_id?}` → returns `{session_id, brain_response, kb_context, ready}`
  - Brain searches KB FTS5 for context, builds conversation history
  - When Brain says "READY TO PROCEED", UI shows "Start Pipeline" button
  - Does NOT start a pipeline run — this is exploration

- `GET /api/relay/brain/history/<session_id>` — get conversation history

- `POST /api/relay/brain/start` — start pipeline from brain conversation
  - Body: `{session_id}` → returns `{run_id, status}`
  - Builds enriched intent from full conversation history
  - Enriched intent includes all Eric-Brain exchanges as context

### Interjection (mid-pipeline backchannel)

- `POST /api/relay/<run_id>/interject` — add interjection (does NOT stop pipeline)
  - Body: `{message}` → stored in `pipeline_interjections`
  - Consumed by next phase's `_pre_discovery()`

- `GET /api/relay/<run_id>/interjections` — list interjections + consumption status

### Live Feed

- `GET /api/relay/<run_id>/feed` — all phase outputs, gate results, interjections
  - Returns: `{phases, gates, interjections, trajectories, status, background}`
  - UI polls this every 2 seconds for live observation

## Interjection Consumption Mechanism

The `_consume_interjections()` function in `pipeline_relay.py` is called
from within `_pre_discovery()` — the function that runs before every agent
call to gather context. It:

1. Queries `pipeline_interjections` for unconsumed messages for this run
2. Formats them as `## ERIC INTERJECTION (backchannel — consider this)`
3. Marks them as consumed by the current phase
4. Returns formatted string that gets appended to the pre-discovery output

```python
def _consume_interjections(conn, run_id, phase):
    rows = conn.execute(
        "SELECT id, message FROM pipeline_interjections "
        "WHERE run_id = ? AND consumed_by_phase IS NULL "
        "ORDER BY id ASC", (run_id,)).fetchall()
    if not rows:
        return ""
    parts = ["\n\n## ERIC INTERJECTION (backchannel — consider this)\n"]
    for ij_id, message in rows:
        parts.append(f"> {message}\n")
        conn.execute(
            "UPDATE pipeline_interjections "
            "SET consumed_by_phase = ?, consumed_at = datetime('now') "
            "WHERE id = ?", (phase, ij_id))
    conn.commit()
    return "\n".join(parts) + "\n"
```

This is injected into `_pre_discovery()`'s return value:
```python
return (
    _build_soul_document(conn, role, intent, run_id)
    + "\n\n[PRE-DISCOVERY RESULTS — review before proceeding]\n\n"
    + "\n".join(results)
    + _consume_interjections(conn, run_id, phase)  # ← HERE
    + "\n\n[END PRE-DISCOVERY — now produce your output]"
)
```

Every phase (Brain, Intent Review, Draft, Proposal Review, Menter, Verify)
calls `_pre_discovery()`, so every phase picks up unconsumed interjections.

## UI Architecture

### Clean Slate Rebuild (2026-07-11)

The old UI had 15+ page components (DecisionsPage, SchedulePage,
LearningPage, RelayPage, ProjectDetail, ProjectsPage, RoadmapPage,
ChatConsole, InfraPage, DashboardPage, ReviewQueue, PipelinePage,
IngestionPage, DamPage, EricGatePage), standalone HTML portals
(portal.html, roadmap-live.html, monitor-test.html), a cis_kernel
directory with v1/v2/v3 HTML mockups, and a dist-standalone directory.

Eric's directive: "start a new UI in the container, that will be the
control panel for the application. I just need a clean with no previous
UI experiments."

Old UI archived to `runtime/ui_legacy_backup/`. New UI built from
scratch with 3 components only:

### Components

1. **BrainChat.jsx** — Conversational interface with Brain
   - Messages list (user/brain bubbles)
   - Input box with Send button
   - "Start Pipeline →" button appears when Brain says READY TO PROCEED
   - Session persists in localStorage
   - KB context shown alongside Brain responses

2. **PipelineLive.jsx** — Live observation feed
   - Phase cards (expandable/collapsible) showing each phase's output
   - Gate results per phase (PASS/FAIL/SKIP badges)
   - Interjection history (with consumption status)
   - Backchannel input box at bottom (always available, never blocks)
   - 2-second polling via `/api/relay/<run_id>/feed`
   - Manual run ID input when no active run

3. **RunsList.jsx** — Recent pipeline runs
   - Polls `/api/relay/runs` every 10 seconds
   - Click a run to observe it in PipelineLive

### Build

```bash
cd runtime/ui && npm run build
# Output: runtime/ui/dist/ (served by container_app.py at /ui/)
```

Container serves from `runtime/ui/dist/` via volume mount — no rebuild
needed for UI changes, just `npm run build` + container restart.

### Key Files

- `runtime/ui/src/App.jsx` — shell with 3 tabs (Brain, Pipeline, Runs)
- `runtime/ui/src/BrainChat.jsx` — Brain conversational interface
- `runtime/ui/src/PipelineLive.jsx` — live feed + backchannel
- `runtime/ui/src/RunsList.jsx` — run history
- `runtime/ui/src/api.js` — API client
- `runtime/ui/src/index.css` — dark theme styles
- `runtime/api/relay.py` — new API endpoints (brain/chat, interject, feed)
- `runtime/abstraction/pipeline_relay.py` — `_consume_interjections()`
- `runtime/schema/migrations/0028_brain_chat_interjections.sql` — DB tables

## Provenance vs Intent Alignment

Eric's concept of provenance is NOT about linking individual factual
claims to web sources. It's about **intent alignment** — ensuring the
pipeline produces what Eric asked for, tracing actions back to intent.

> "provenance somehow guiding the pipeline to actually produce what I
> ask for which is laid out in great detail throughout the KB. between
> the gates, provenance, tool restrictions and all the rest of the
> container guardrails, this is the ultimate behavior of the cis tool
> I am hoping to have."

The Brain chat + enriched intent is the first layer of intent alignment:
- Brain mines the KB for Eric's vision on the topic
- Conversation builds a rich intent document
- Enriched intent (full conversation) starts the pipeline
- Every phase receives the soul document + pre-discovery context

Next layers (NOW BUILT — see [Intent Provenance & Drift Detection](intent_provenance_drift.md)):
1. ✅ Intent document carried as first-class object through every phase
2. ✅ Drift detection at each phase boundary against the intent
3. ✅ Intent verification at the end (does the result match the intent?)

## Container Restart Required

New API endpoints are in `relay.py` (volume-mounted). The running Flask
process caches imported modules. After changes to relay.py:

```bash
sg docker -c "docker restart cis-pipeline"
```

Do NOT rebuild the image for volume-mounted Python file changes.
Only rebuild when Dockerfile or copied files (gates, plugin, config) change.
