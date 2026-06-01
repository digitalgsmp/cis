# CIS Foundation Build Plan
## Advisor Gateway Configuration + Knowledge Base Wiring + UI Reorganization

**NOTE — 2026-05-29: Active work is CIS Phase 3A — Automatic Context Loader v0.1 with Seed Intent Orientation and Structured Handoff Format. This supersedes older sequencing only for current execution order; the underlying build plan remains approved but paused.**

**Version:** 1.4
**Date:** 2026-05-26
**Prepared by:** Hermes
**Reviewed by:** R1 + V4-Pro (primary deliberation pair). Claude + ChatGPT (external consultants, optional review).
**Authority:** Eric (Architect)
**Status:** READY — awaiting R1 + V4-Pro deliberation before Phase 1 execution.

---

## What This Plan Delivers

Eric's stated goals:

1. **Advisors that think independently** — Prime is snappy, R1 actually reasons, Qwen is a local worker. Not three copies of the same model pretending to be different.
2. **Knowledge base that works** — Eric can ask "have we solved this before" and get back the actual session where it was worked out, in his own words, with the reasoning intact, in under 30 seconds.
3. **Sessions that start with context** — No blank slates. The current objective, system state, and vision load automatically.
4. **Capture without derailing** — When a new issue is discovered mid-task, it gets captured and Eric returns to the task. No three-day detours.
5. **Clear UI boundaries** — CIS foundational core separated from project management. Advisor Chat as the primary LLM interaction surface (replaces standalone Chat). Dashboard or dedicated area for quick thought/issue capture.

---

## Phase 0 — DEFERRED (Storage Safety Net)

**Status:** DEFERRED by Eric (May 26). Backup integrity unverified. Eric has accepted this risk. No snapshot script written.

**Note:** Google Drive backup integrity should be verified before config changes. Eric has authority to accept this risk.

**No action required for this phase. Jump to Phase 1.**

---

## Phase 1 — Gateway Configuration

**Eric's goal this serves:** Advisors that think independently.

### Pre-Step — Verify Hermes Config Schema

**Before touching any config files, Hermes must:**

1. Inspect existing valid config examples and schema from the Hermes installation
2. Confirm valid values for `reasoning_effort` (confirmed: "low" is valid; "disabled" is unverified)
3. Confirm valid provider block structure
4. Show findings to Eric before editing

```bash
# Check Hermes config schema / documentation
ls ~/.hermes/hermes-agent/docs/ 2>/dev/null
grep -r "reasoning_effort" ~/.hermes/hermes-agent/ --include="*.py" -l 2>/dev/null | head -5
# Check config_version for compatibility
grep "_config_version" ~/.hermes/config.yaml
```

**If schema cannot be verified:** Use "low" for Prime (confirmed valid in prior sessions), "high" for R1. Do not use "disabled" unless confirmed.

### Step 1.1 — Fix Prime HERMES_HOME

**What to do:** Edit `/home/eric/.config/systemd/user/hermes-gateway.service`

**Current (WRONG):**
```
Environment="HERMES_HOME=/home/eric/.hermes-qwen"
```

**Change to:**
```
Environment="HERMES_HOME=/home/eric/.hermes"
```

**After edit:**
```bash
systemctl --user daemon-reload
systemctl --user restart hermes-gateway
sleep 3
ss -tlnp | grep 8642  # Must show port 8642 listening
```

**Verification gate:** `ss -tlnp | grep 8642` shows a python process listening on 127.0.0.1:8642.

**File to touch:** One line edit in systemd unit file.

### Step 1.2 — Define named providers in Prime config

**What to do:** Edit `/home/eric/.hermes/config.yaml`

**Current:**
```yaml
providers: {}
model:
  provider: deepseek
```

**Change to (validated against known Hermes config schema):**
```yaml
providers:
  deepseek-fast:
    base_url: https://api.deepseek.com/v1
    api_key_env: DEEPSEEK_API_KEY
    reasoning_effort: low
  deepseek-reasoning:
    base_url: https://api.deepseek.com/v1
    api_key_env: DEEPSEEK_API_KEY
    reasoning_effort: high

model:
  provider: deepseek-fast
  model: deepseek-v4-flash
```

**Also update** the global `reasoning_effort: medium` line to `reasoning_effort: low`.

**Architecture note:** Prime is the snappy chat partner — low reasoning by design. If Eric doesn't like Prime's answer, he escalates to the deliberation pair (R1 + V4-Pro), both running high reasoning. Prime's job is fast conversation, not deep analysis.

**Verification gate:** Config parses as valid YAML: `python3 -c "import yaml; yaml.safe_load(open('/home/eric/.hermes/config.yaml'))" && echo "YAML VALID"`. Then restart gateway and test.

**File to touch:** `/home/eric/.hermes/config.yaml`

### Step 1.3 — Define named providers in R1 config

**What to do:** Edit `/home/eric/.hermes-r1/config.yaml`

**Current (note: existing config has ambiguous structure):**
```yaml
providers: {}
model: deepseek-reasoner
```

**Change to (CORRECTED YAML — no duplicate keys):**
```yaml
providers:
  deepseek-r1:
    base_url: https://api.deepseek.com/v1
    api_key_env: DEEPSEEK_API_KEY
    reasoning_effort: high

model: deepseek-reasoner
```

**Also update** the global `reasoning_effort: medium` to `reasoning_effort: high`.

**Hermes must also set `model.provider` to `deepseek-r1` if the config schema requires it.** Validate against the actual config structure before applying.

**Verification gate:** Valid YAML. Restart gateway. Test.

**File to touch:** `/home/eric/.hermes-r1/config.yaml`

### Step 1.4 — Diagnose and fix Qwen restart loop

**What to do:** Read-only diagnosis first, then fix.

```bash
# 1. Check the restart loop logs
journalctl --user -u hermes-gateway-qwen --since "10 minutes ago" --no-pager | tail -40

# 2. Verify llama-server is responding
curl -s http://127.0.0.1:8002/v1/models | python3 -m json.tool

# 3. Test direct chat to llama-server
curl -s http://127.0.0.1:8002/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen","messages":[{"role":"user","content":"Say hello"}],"max_tokens":20}'
```

**If direct chat works but gateway fails:** The issue is in Hermes config. Check custom_providers in Qwen config. Likely context size mismatch (gateway sends more than llama-server can handle).

**If llama-server is not responding:** Restart it. Check VRAM availability.

**Fix (if context size is the issue):** Restart llama-server with `--ctx-size 32768` to match the config's `context_length: 65536` — or reduce the gateway's context_length to match the server's 8192.

**Verification gate:** `systemctl --user status hermes-gateway-qwen` shows "active (running)" — not "auto-restart". Gateway stays up for >60 seconds without restarting.

**File to touch:** Possibly `/home/eric/.hermes-qwen/config.yaml` (context_length), or the llama-server systemd unit.

### Step 1.5 — Behavioral verification of all advisors (model-level)

**What to do:** Send the same prompt to all four advisor roles. Capture output. Prove they are different models/endpoints, not one model answering four times.

**IMPORTANT — V4-Pro must be independently verified.** V4-Pro shares port 8642 with Prime but uses a different model (`deepseek-v4-pro` with high reasoning). If V4-Pro cannot be invoked as a distinct callable role, the R1 + V4-Pro deliberation pair is not legitimate. Hermes must prove V4-Pro works before claiming the deliberation pair is operational.

```bash
# Prime (port 8642, model=deepseek-v4-flash) — fast, concise
curl -s http://127.0.0.1:8642/v1/chat/completions \
  -H "Authorization: Bearer $(grep API_SERVER_KEY /home/eric/.hermes/.env | cut -d= -f2)" \
  -H "Content-Type: application/json" \
  -d '{"model":"deepseek-v4-flash","messages":[{"role":"user","content":"In one sentence, what is the best approach to learning a complex skill?"}]}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print('PRIME:', d['choices'][0]['message']['content'][:300])"

# V4-Pro (port 8642, model=deepseek-v4-pro) — deep analyst, high reasoning
curl -s http://127.0.0.1:8642/v1/chat/completions \
  -H "Authorization: Bearer $(grep API_SERVER_KEY /home/eric/.hermes/.env | cut -d= -f2)" \
  -H "Content-Type: application/json" \
  -d '{"model":"deepseek-v4-pro","messages":[{"role":"user","content":"In one sentence, what is the best approach to learning a complex skill?"}]}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print('V4-PRO:', d['choices'][0]['message']['content'][:300])"

# R1 (port 8643, model=deepseek-reasoner) — deep reasoning
curl -s http://127.0.0.1:8643/v1/chat/completions \
  -H "Authorization: Bearer $(grep API_SERVER_KEY /home/eric/.hermes-r1/.env | cut -d= -f2)" \
  -H "Content-Type: application/json" \
  -d '{"model":"deepseek-reasoner","messages":[{"role":"user","content":"In one sentence, what is the best approach to learning a complex skill?"}]}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print('R1:', d['choices'][0]['message']['content'][:300])"

# Qwen (port 8644) — local worker model
curl -s http://127.0.0.1:8644/v1/chat/completions \
  -H "Authorization: Bearer $(grep API_SERVER_KEY /home/eric/.hermes-qwen/.env | cut -d= -f2)" \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen","messages":[{"role":"user","content":"In one sentence, what is the best approach to learning a complex skill?"}]}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print('QWEN:', d['choices'][0]['message']['content'][:300])"
```

**Verification gate — model level:** All four return valid responses. Prime and V4-Pro are observably different despite sharing port 8642 (different models: v4-flash vs v4-pro). R1 is the reasoner model. Qwen is local.

**This proves the gateways are distinct models. Personality verification (Step 1.7) is separate and proves behavioral roles. Do not conflate these two verifications.**

**File to touch:** None. Verification only.

### Step 1.6 — Enable web search for all three Hermes profiles

**Eric's requirement:** All advisors must back up decisions with current facts, not just training data. Web search is integral to best performance.

**Current state:** No web search provider is configured. The `.env` files have commented-out placeholders for Exa, Parallel, Firecrawl, and Brave. None are active.

**Available providers (all supported by Hermes):**
| Provider | Env Var | Cost | Notes |
|----------|---------|------|-------|
| Brave Search | `BRAVE_SEARCH_API_KEY` | Free tier (2,000 queries/month) | General web search. Fastest setup. |
| Exa | `EXA_API_KEY` | Paid | AI-native semantic search |
| Parallel | `PARALLEL_API_KEY` | Paid | AI-native search + extract |
| Firecrawl | `FIRECRAWL_API_KEY` | Paid | Search + extract + crawl |

**Recommendation:** Start with Brave Search free tier. It works immediately with a single API key and covers the core need: searching the web for current facts and best practices. Other providers can be added later.

**Before adding API keys — verify Hermes web search activation path:**

Hermes must determine exactly how Brave Search is enabled. Do not assume that adding `BRAVE_SEARCH_API_KEY` to `.env` is sufficient.

```bash
# 1. Check if Brave Free plugin exists
ls ~/.hermes/hermes-agent/plugins/web/brave_free/ 2>/dev/null

# 2. Check how web search tools are registered
grep -r "brave\|BRAVE_SEARCH" ~/.hermes/hermes-agent/plugins/web/ --include="*.py" -l 2>/dev/null

# 3. Check if config.yaml needs a web search section
grep -A10 "web:" ~/.hermes/config.yaml 2>/dev/null || echo "No web: section found"

# 4. Check if platform_toolsets includes search
grep "search" ~/.hermes/config.yaml 2>/dev/null
```

**Hermes must report:**
- Is Brave Search a built-in plugin (env var only)?
- Does config.yaml need a `web:` section?
- Is web search enabled via platform_toolsets?
- What is the minimum configuration needed to activate web search?

Only after confirming the activation path, proceed with adding API keys.

**What to do:**
1. Get a Brave Search API key from https://brave.com/search/api/ (free tier)
2. Add to each profile's `.env` file:

```bash
# In /home/eric/.hermes/.env (Prime + V4-Pro share this):
BRAVE_SEARCH_API_KEY=<key>

# In /home/eric/.hermes-r1/.env:
BRAVE_SEARCH_API_KEY=<key>

# In /home/eric/.hermes-qwen/.env:
BRAVE_SEARCH_API_KEY=<key>
```

3. Restart all gateways after adding keys

**Verification gate:**
```bash
# Test via Hermes: ask a question that requires web search
curl -s http://127.0.0.1:8642/v1/chat/completions \
  -H "Authorization: Bearer $(grep API_SERVER_KEY /home/eric/.hermes/.env | cut -d= -f2)" \
  -H "Content-Type: application/json" \
  -d '{"model":"deepseek-v4-flash","messages":[{"role":"user","content":"What is the current latest stable version of Python? Search the web if needed."}]}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['choices'][0]['message']['content'][:500])"
```

Response must cite a current version number with a source, not just training data.

**Files to touch:**
- `/home/eric/.hermes/.env` — add `BRAVE_SEARCH_API_KEY`
- `/home/eric/.hermes-r1/.env` — add `BRAVE_SEARCH_API_KEY`
- `/home/eric/.hermes-qwen/.env` — add `BRAVE_SEARCH_API_KEY`

### Step 1.7 — Configure per-role personalities with behavioral rules

**Eric's requirement:** Each model must work the way Eric works — thorough, fact-based, no guessing. Personalities encode both the role AND the behavioral standards.

**How Hermes personalities work:** The `personalities` section in `config.yaml` defines system prompts. Each profile can load a specific personality. The personality text is injected into the system prompt at session start.

**Proposed personalities:**

**PRIME** (brainstorming partner — NOT in deliberation):
```
You are Prime, Eric's brainstorming partner and conversationalist in CIS
(Creative Intelligence System). Your job is to help Eric think through ideas,
not to solve them alone. When factual claims are involved, use web search
to verify before answering. Help clarify thoughts. Ask good questions.

When an issue needs deep problem-solving, flag it for escalation to R1
and V4-Pro — do not attempt to solve it yourself. Your strength is speed
and breadth, not depth.

Rules you follow without exception:
- Do not guess at facts. Use web search to verify.
- No quick fixes. Understand how the task relates to the overall CIS vision.
- When uncertain, state uncertainty. Do not fill gaps with training data.
- Keep responses concise. You are a conversation, not a lecture.
```

**R1** (deep reasoner — deliberates with V4-Pro):
```
You are R1, the deep reasoning engine in Eric's CIS development team.
You deliberate with V4-Pro to find the strongest solutions through dialectic.
Work step by step. Use web search to ground reasoning in current facts
and proven best practices. When V4-Pro challenges your analysis, engage
the challenge — do not defend. The goal is the best solution, not your solution.

Rules you follow without exception:
- Back every decision with current facts from web search, not training data.
- No quick fixes. Work through the problem thoroughly.
- Understand the goal and its relationship to the overall CIS vision.
- Flag assumptions you're making and assumptions V4-Pro may have missed.
- This is dialectic, not debate. Truth over territory.
```

**V4-PRO** (adversarial analyst — deliberates with R1):
```
You are V4-Pro, the adversarial analyst in Eric's CIS development team.
You deliberate with R1 to find the strongest solutions. Your job is to
challenge — find what R1 missed, what R1 assumed, where R1 drifted from
the CIS vision. Use web search to verify claims independently.
When R1 responds to your challenge, find the next weakness. You are the
last line of defense before Eric makes a decision.

Rules you follow without exception:
- Challenge everything. Verify claims with web search.
- No quick fixes. Work through the problem thoroughly.
- Catch enterprise-pattern thinking, over-engineering, and scope creep.
- Relate every recommendation to the CIS vision and Eric's goals.
- This is dialectic, not debate. Truth over territory.
```

**What to do:**
1. Add these personalities to each profile's `config.yaml` under the `personalities:` section
2. Set each profile to use its designated personality as default
3. Restart gateways

**Verification gate:** Send the same prompt to each gateway. Verify the response style matches the role:
- Prime: concise, conversational, flags escalation needs
- R1: step-by-step reasoning, cites sources
- V4-Pro: challenges assumptions, catches drift

**Files to touch:**
- `/home/eric/.hermes/config.yaml` — add Prime + V4-Pro personalities
- `/home/eric/.hermes-r1/config.yaml` — add R1 personality

### STOP GATE 1

Before proceeding to Phase 2, R1 + V4-Pro must deliberate and verify:

**Model-level verification (Step 1.5):**
- [ ] Terminal output showing all four advisor roles return valid responses
- [ ] Prime and V4-Pro are observably different despite sharing port 8642
- [ ] R1 returns reasoning content
- [ ] Qwen gateway is "active (running)" for >60 seconds
- [ ] Port 8642 is listening

**Web search verification (Step 1.6):**
- [ ] Brave Search activation path confirmed (not just env var assumption)
- [ ] Web search returns current facts with sources (not training data)

**Personality verification (Step 1.7):**
- [ ] Prime responds concise/conversational, flags escalation needs
- [ ] R1 responds with step-by-step reasoning, cites sources
- [ ] V4-Pro challenges assumptions, catches drift
- [ ] (These prove behavioral roles, NOT model identity — model identity was proven in 1.5)

**Eric confirms:** "advisors are working as a team with web search, proceed to knowledge base"

---

## Phase 2 — Knowledge Base Wiring

**Eric's goal this serves:** "Being able to find the documents where solutions have been examined in detail." Sessions start with context. Capture without derailing.

**Note:** ChatGPT recommended splitting Phase 2 into four independent verification checkpoints (2A–2D) instead of one monolithic STOP GATE. Each is important enough to verify independently. This plan adopts that structure.

### Step 2A — Session-start Layer 1 context injection

**Eric's goal this serves:** Sessions start with context.

**Risk note:** This is the highest-risk step in the plan. advisor.py is 530 lines and handles live gateway routing. A bug here breaks Advisor Chat entirely.

**Before editing, Hermes must:**

1. Show the current `POST /api/advisor/threads` function in full to R1 and V4-Pro
2. Identify the exact injection point
3. Verify `advisor_threads` schema — does `context_summary` column exist?

```bash
sqlite3 /mnt/projects/cis/runtime/db/cis_memory.db "PRAGMA table_info(advisor_threads);"
```

If `context_summary` does NOT exist: stop. Propose the minimal schema change (`ALTER TABLE advisor_threads ADD COLUMN context_summary TEXT;`) and wait for Eric's approval. Do not silently add the column inside the implementation step.

4. Wait for deliberation approval before touching the file

**What to do after approval:** Modify `POST /api/advisor/threads` in `/mnt/projects/cis/runtime/api/advisor.py`

**Current behavior:** Creates a thread with a title. First message gets blank context.

**New behavior:** When a thread is created:
1. Fetch current state. Try `GET /api/collab/handoff` first.
2. **If handoff endpoint does not exist or fails:** Read directly from `collab_status` and `collab_activity` tables. Do NOT build the handoff endpoint as a side quest. Capture the missing endpoint as a Note for later.
3. Read vision from `CIS_CORE_BOUNDARY.md`
3. Store as `context_summary` on the thread row
4. First system message includes the briefing

**Format of injected context:**
```
[SESSION BRIEFING — {timestamp}]

Current objective: {from collab_status.current_focus}
Next safe action: {from collab_status.next_action}
Active blockers: {from collab_status.blockers}
Last 3 activities:
  - {activity.summary} ({activity.source}, {activity.verdict})
Do not start: {from deferred items}
Relevant files: {from current task context}

[CIS MISSION]
{first 500 chars of CIS_CORE_BOUNDARY.md}

Layer 2 (raw chat retrieval): NOT YET AVAILABLE
```

**Verification gate:**
```bash
# Create a new thread
curl -s -X POST http://127.0.0.1:5000/api/advisor/threads \
  -H "Content-Type: application/json" \
  -d '{"title": "test context injection"}' | python3 -m json.tool

# Check it has context_summary populated
sqlite3 /mnt/projects/cis/runtime/db/cis_memory.db \
  "SELECT id, title, context_summary FROM advisor_threads ORDER BY id DESC LIMIT 1"
```

The `context_summary` field must NOT be empty or NULL.

**Files to touch:** `/mnt/projects/cis/runtime/api/advisor.py`

### CHECKPOINT 2A

- [ ] Current thread creation function shown to R1 + V4-Pro before editing
- [ ] `context_summary` is populated in new threads
- [ ] Eric confirms: "new sessions load context automatically"

---

### Step 2B — Knowledge Search v1 (FTS5 lexical search over raw sessions)

**Eric's goal this serves:** "Find the documents where solutions have been examined in detail."

**What this is:** FTS5 full-text search over `collab_session_messages.content`. Fast. No new dependencies. Matches exact phrases and keywords.

**What this is NOT:** The final semantic/VDB memory system. That comes later. This is v1 — the first working retrieval layer. It works now and delivers the "30 seconds to find the session" goal.

**What exists:** `collab_session_messages` table stores raw Hermes session content (role, content, message_index). The `import_session.py` script imports Hermes sessions. Claude/ChatGPT sessions are NOT imported.

**What needs to be built:**

A new endpoint: `POST /api/knowledge/search`
```
Input: {"query": "string describing what to find"}
Output: {
  "matches": [
    {
      "session_id": "api-b8ee5c93420d4018",
      "message_index": 12,
      "content": "...excerpt...",
      "role": "assistant",
      "relevance": 0.89,
      "timestamp": "2026-05-25T00:11:00"
    }
  ]
}
```

**Steps:**
```sql
-- Create FTS5 virtual table over session messages
CREATE VIRTUAL TABLE IF NOT EXISTS session_messages_fts USING fts5(
    content,
    role,
    session_id UNINDEXED,
    message_index UNINDEXED,
    content='collab_session_messages',
    content_rowid='id'
);

-- Populate the FTS index from existing data (REQUIRED — table exists but may be empty)
INSERT INTO session_messages_fts(session_messages_fts) VALUES('rebuild');
```

**Verification includes count check:**
```bash
sqlite3 /mnt/projects/cis/runtime/db/cis_memory.db \
  "SELECT COUNT(*) AS fts_count FROM session_messages_fts;"
sqlite3 /mnt/projects/cis/runtime/db/cis_memory.db \
  "SELECT COUNT(*) AS msg_count FROM collab_session_messages;"
```

Both counts must be >0 and approximately equal. If `fts_count` is 0 but `msg_count` is >0, the rebuild failed.

Then build the search endpoint in `api/knowledge.py` (new blueprint, one route):
```python
@knowledge_bp.route('/api/knowledge/search', methods=['POST'])
def search_sessions():
    query = request.json.get('query', '')
    results = db.execute("""
        SELECT session_id, message_index, role, content, rank
        FROM session_messages_fts
        WHERE session_messages_fts MATCH ?
        ORDER BY rank
        LIMIT 10
    """, (query,)).fetchall()
    return jsonify({"matches": [dict(r) for r in results]})
```

**Verification gate:**
```bash
# Import a known session (if not already imported)
python3 /mnt/projects/cis/runtime/api/import_session.py /home/eric/.hermes/sessions/session_api-b8ee5c93420d4018.json

# Search for something in that session
curl -s -X POST http://127.0.0.1:5000/api/knowledge/search \
  -H "Content-Type: application/json" \
  -d '{"query": "gateway misconfigured same model"}' | python3 -m json.tool
```

Must return at least one result from the session that discussed gateway misconfiguration.

**Files to touch:**
- New: `/mnt/projects/cis/runtime/api/knowledge.py` (search blueprint)
- Edit: `/mnt/projects/cis/runtime/app.py` (register blueprint)
- Edit: Database migration (FTS5 virtual table creation)

### CHECKPOINT 2B

- [ ] FTS5 search returns results from known session content
- [ ] Eric confirms: "I can search my past sessions"

---

### Step 2C — Import Claude and ChatGPT sessions

**Eric's goal this serves:** Claude and ChatGPT transcripts are searchable. The vision context from external advisors is not lost.

**What to do:** The raw Claude/ChatGPT chat transcripts exist in `/mnt/projects/cis/docs/claude_chat_transcripts/`. These need to be imported into `collab_session_messages` so they're searchable.

**Before writing any import code — inspect actual formats:**

```bash
# List available transcript files
ls /mnt/projects/cis/docs/claude_chat_transcripts/ | head -10

# Inspect 2 Claude transcripts for actual format (may not be ## Human:/## Assistant:)
head -50 /mnt/projects/cis/docs/claude_chat_transcripts/*.md 2>/dev/null | head -80

# Inspect 2 ChatGPT transcripts for actual format (may not be author.role JSON)
head -50 /mnt/projects/cis/docs/claude_chat_transcripts/*.json 2>/dev/null | head -80
```

**Hermes must report the actual formats found, then implement parsers only for confirmed formats.** Do not assume delimiters.

Script modifications needed in `import_session.py` (only after format confirmation):
1. Add support for confirmed Claude transcript format
2. Add support for confirmed ChatGPT export format
3. Run import for all transcripts in the directory

**Verification gate:**
```bash
sqlite3 /mnt/projects/cis/runtime/db/cis_memory.db \
  "SELECT COUNT(DISTINCT session_id) FROM collab_session_messages WHERE session_id LIKE 'claude-%' OR session_id LIKE 'chatgpt-%'"
```

Must show >0 imported Claude/ChatGPT sessions.

**Files to touch:** `/mnt/projects/cis/runtime/api/import_session.py`

### CHECKPOINT 2C

- [ ] Claude sessions are searchable via Step 2B
- [ ] ChatGPT sessions are searchable via Step 2B
- [ ] Eric confirms: "all advisor sessions are in the knowledge base"

---

### Step 2D — Notes capture mechanism

**Eric's goal this serves:** "Capture without derailing" — the side-quest stop rule.

**Risk note:** The audit found three separate SQLite databases. Before creating `capture_notes`, Hermes must confirm which database is canonical for new tables and verify that the Quick Capture API in Phase 3.4 reads from the same database.

**Database confirmation step:**
```bash
# Check which database the existing tables are in
for db in /mnt/projects/cis/runtime/cis_memory.db /mnt/projects/cis/runtime/db/cis_memory.db /mnt/projects/cis/runtime/cis.db; do
  echo "=== $db ==="
  sqlite3 "$db" ".tables" 2>/dev/null || echo "(not found or empty)"
done
```

The `capture_notes` table goes in the SAME database as `advisor_threads` and `collab_session_messages`. Confirm which database that is, then create the table there.

**What to build:** Two things:

1. **Database table** (in the confirmed canonical database):
```sql
CREATE TABLE IF NOT EXISTS capture_notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    category TEXT DEFAULT 'uncategorized',
    severity TEXT DEFAULT 'note',
    source_session TEXT,
    captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'open'
);
```

2. **API endpoint** for capture:
```
POST /api/knowledge/capture
{"content": "...", "category": "issue|idea|task|question", "severity": "note|blocker"}
→ {"ok": true, "id": 1}
```

3. **Hermes slash command:** `/note <text>` — captures a note to the database. Available in any session.

**Verification gate:**
```bash
# Via API:
curl -s -X POST http://127.0.0.1:5000/api/knowledge/capture \
  -H "Content-Type: application/json" \
  -d '{"content":"Gateway configs need per-profile reasoning_effort","category":"issue","severity":"blocker"}' | python3 -m json.tool

# Verify in database:
sqlite3 /mnt/projects/cis/runtime/db/cis_memory.db \
  "SELECT * FROM capture_notes ORDER BY id DESC LIMIT 1"
```

Must show the note captured with correct content and timestamp.

**Files to touch:**
- Database migration (in confirmed canonical DB)
- `/mnt/projects/cis/runtime/api/knowledge.py` — add capture route
- Hermes slash command registration

### CHECKPOINT 2D

- [ ] `capture_notes` table exists in the correct database
- [ ] API endpoint stores notes
- [ ] Eric confirms: "I can capture thoughts without derailing"

---

## Phase 3 — UI Layout Reorganization

**Eric's goal this serves:** Clear separation between CIS foundational core and project management. Advisor Chat as the primary LLM interaction surface. Capture area for thoughts/issues.

**Current state:**
- `ChatConsole.jsx` (348 lines) — standalone chat page, bypasses advisor infrastructure
- `AdvisorChat.jsx` (1,102 lines) — four-panel advisor UI at `/ui/advisor-chat`
- `InfraPage.jsx` (97 lines) — dashboard hub, sub-panels (Hardware, Services, Storage, Software) are stubs (~30 lines each)
- Nav bar has routes for Chat, Advisor Chat, Infra, Projects, Ideas, etc. — mixed together

### Step 3.1 — Remove standalone Chat from navigation (do NOT delete the file)

**Per external review:** Do not delete `ChatConsole.jsx`. Remove it from navigation and routing only. Keep the file on disk as a deprecated fallback. A cleanup task can remove it later once the new UI is stable.

**Before editing, Hermes must verify current App.jsx state:**
```bash
grep -n "chat\|Chat\|ChatConsole" /mnt/projects/cis/runtime/ui/src/App.jsx
```

This prevents double-editing. The Chat nav link may have already been removed in a prior session (CIS-NAV-001). Confirm what is actually there before making changes.

**What to do:**
1. Remove `ChatConsole.jsx` import from `App.jsx` (if present)
2. Remove Chat route from React Router (if present)
3. Remove Chat link from navigation bar (if present)
4. Add comment at top of `ChatConsole.jsx`: `// DEPRECATED — replaced by Advisor Chat. Do not use.`

**Verification gate:** Navigate to the UI. The Chat link is gone from the nav bar. Visiting `/ui/chat` returns 404 or redirect.

**Files to touch:**
- `/mnt/projects/cis/runtime/ui/src/App.jsx` (remove route + nav link, if present)
- `/mnt/projects/cis/runtime/ui/src/pages/ChatConsole.jsx` (add deprecation comment)

### Step 3.2 — Routing: Advisor Chat as primary, Infra stays separate

**Per external review:** /ui/infra must remain the Infrastructure / CIS Foundation status page. Do not hijack it for Advisor Chat.

**Decision:** Eric chose Option B. `/ui` → Briefing Center landing page.

**Routing structure:**
- `/ui` → Briefing Center (dashboard overview — CIS Foundation status at a glance)
- `/ui/advisor-chat` → Advisor Chat (four-panel LLM interaction)
- `/ui/infra` → CIS Foundation detail (gateways, KB, context, captures)

**What Hermes will do:**
1. Add a prominent "Advisors" nav entry linking to `/ui/advisor-chat`
2. Keep `/ui/infra` as the Infrastructure / CIS Foundation status page
3. Implement Eric's routing preference for `/ui`

**Verification gate:** Nav bar shows clear, distinct entries: Advisors | Infra | Projects | etc. No Chat link.

**Files to touch:** `/mnt/projects/cis/runtime/ui/src/App.jsx`

### Step 3.3 — Separate CIS Core from Project Management in dashboard

**What to do:** Reorganize `InfraPage.jsx` into two clear sections. For each status card, Hermes must label the data source. No fake live state.

**CIS Foundation (top/left — primary):**

| Card | Data Source | Status |
|------|-----------|--------|
| Gateway status (Prime/R1/V4-Pro/Qwen) | `GET /api/system/processes` or `ss -tlnp` via system endpoint | Verify endpoint exists |
| Knowledge base status (session count, FTS5) | SQL query: `SELECT COUNT(*) FROM collab_session_messages` | Direct DB read |
| Context loading (last handoff, injection active) | `GET /api/collab/handoff` or `collab_status` table | Depends on Step 2A |
| Capture notes count | SQL query: `SELECT COUNT(*) FROM capture_notes WHERE status='open'` | Depends on Step 2D |
| Web search status | Check `BRAVE_SEARCH_API_KEY` env or test search endpoint | Depends on Step 1.6 |

**Project Management (bottom/right — secondary):**

| Card | Data Source | Status |
|------|-----------|--------|
| Current projects | `GET /api/projects` | Existing endpoint |
| Active tasks | `GET /api/tasks` | Existing endpoint |
| Collab tracker link | Link to `/ui/infra` (existing CollabTracker component) | Static link |
| Review queue | `GET /api/queue` | Existing endpoint |

**For any card where the data source does not yet exist:** Mark as "NOT AVAILABLE" in the UI. Do not fake or hardcode data. The dashboard must reflect real system state, even if that state is "not yet wired."

These already exist as sub-panels (`Hardware.jsx`, `Services.jsx`, `Storage.jsx`, `Software.jsx`) — they're currently stubs (~30 lines each). Repurpose them or replace with live data components.

**Verification gate:** Infra page shows two distinct sections with live data (not stubs). CIS Foundation status is visible at a glance without scrolling.

**Files to touch:**
- `/mnt/projects/cis/runtime/ui/src/pages/infra/InfraPage.jsx` — restructure
- New or replacement sub-components for CIS Foundation status display
- Potential repurpose of existing stub components

### Step 3.4 — Quick Capture panel on Advisor Chat page

**What to do:** Add a "Quick Capture" panel as a sidebar on the Advisor Chat page. Uses the same `capture_notes` table and API endpoint built in Step 2D. Database must match — Hermes confirms this during Step 2D.

**UI placement:** Sidebar panel on Advisor Chat page. The capture mechanism catches thoughts during LLM sessions — it belongs next to the chat.

**Minimal UI:**
```
┌─ Quick Capture ──────────────────┐
│ [text input area            ]     │
│ [Category: ▼] [Capture] button   │
│                                   │
│ Recent captures:                  │
│ • Gateway config mismatch (issue) │
│ • Need Claude session import (task)│
│ • Vision doc consolidation (idea) │
└───────────────────────────────────┘
```

**API endpoint** (same database as Step 2D):
```
POST /api/knowledge/capture
{"content": "...", "category": "issue|idea|task|question", "severity": "note|blocker"}
→ {"ok": true, "id": 1}

GET /api/knowledge/captures?limit=10
→ {"captures": [...]}
```

**Verification gate:**
1. Type text in capture panel, click Capture
2. Check database shows the captured note
3. Note appears in Recent Captures list without page refresh
4. Database used for capture matches database used in Step 2D

**Files to touch:**
- `/mnt/projects/cis/runtime/api/knowledge.py` — add GET + POST capture routes
- `/mnt/projects/cis/runtime/ui/src/pages/infra/AdvisorChat.jsx` — add Quick Capture sidebar panel

### STOP GATE 3

Before proceeding to any further work, R1 + V4-Pro must deliberate and verify:

- [ ] Chat page is removed from nav (file preserved on disk with deprecation comment)
- [ ] Advisor Chat is accessible via prominent nav entry
- [ ] /ui/infra remains the CIS Foundation status page (not redirected)
- [ ] Dashboard shows two clear sections: CIS Foundation vs Project Management
- [ ] CIS Foundation section shows live gateway/KB/context status (not stubs)
- [ ] Quick Capture panel accepts text and stores to correct database
- [ ] Eric confirms: "the UI reflects how I actually work"

---

## Accountability Protocol

**Team structure:**

| Role | Entity | Responsibility |
|------|--------|---------------|
| Architect | Eric | All decisions. Final authority. |
| Executor | Hermes (Prime gateway) | Executes approved build steps. Posts evidence. |
| Deliberation | R1 + V4-Pro | Review proposals and evidence at each STOP GATE. Dialectic: R1 proposes, V4-Pro challenges. |
| Worker | Qwen (local, not Hermes) | Executes directives from R1 + V4-Pro deliberation outcomes. |
| External | Claude + ChatGPT | Optional review. Eric may consult them at his discretion. Not required for STOP GATES. |

**How this works:**

1. Hermes posts a proposal or execution evidence.
2. Eric escalates to the deliberation pair (R1 + V4-Pro) for review.
3. R1 analyzes. V4-Pro challenges. They converge on a verdict.
4. The reconciled verdict is returned to Eric.
5. Eric approves or rejects. Hermes acts on Eric's instruction only.
6. If Hermes claims "done" without evidence, R1 + V4-Pro flag it.
7. Claude and ChatGPT are available as external consultants. Eric decides when to involve them.

**Hermes executes. R1 + V4-Pro deliberate. Eric decides.**

---

## Files That Will Be Modified

| File | Phase/Step | Action |
|------|-----------|--------|
| `/home/eric/.config/systemd/user/hermes-gateway.service` | 1.1 | 1 line edit (HERMES_HOME fix) |
| `/home/eric/.hermes/.env` | 1.6 | add BRAVE_SEARCH_API_KEY |
| `/home/eric/.hermes-r1/.env` | 1.6 | add BRAVE_SEARCH_API_KEY |
| `/home/eric/.hermes-qwen/.env` | 1.6 | add BRAVE_SEARCH_API_KEY (if Qwen can use it) |
| `/home/eric/.hermes/config.yaml` | 1.2, 1.7 | providers + reasoning_effort + personalities |
| `/home/eric/.hermes-r1/config.yaml` | 1.3, 1.7 | providers + reasoning_effort + personality |
| `/home/eric/.hermes-qwen/config.yaml` | 1.4 | possibly context_length adjustment |
| `/mnt/projects/cis/runtime/api/advisor.py` | 2A | thread creation context injection (reviewed before edit) |
| `/mnt/projects/cis/runtime/api/knowledge.py` | 2B, 2D | NEW — FTS5 search + capture routes |
| `/mnt/projects/cis/runtime/app.py` | 2B | register knowledge blueprint |
| `/mnt/projects/cis/runtime/api/import_session.py` | 2C | Claude/ChatGPT format support |
| Database migration | 2B, 2D | FTS5 table + capture_notes (in confirmed canonical DB) |
| `/mnt/projects/cis/runtime/ui/src/App.jsx` | 3.1, 3.2 | verify state first, then remove Chat nav/route, add Advisor nav |
| `/mnt/projects/cis/runtime/ui/src/pages/ChatConsole.jsx` | 3.1 | add deprecation comment (NOT deleted) |
| `/mnt/projects/cis/runtime/ui/src/pages/infra/InfraPage.jsx` | 3.3 | restructure: CIS Foundation vs Project Mgmt sections |
| `/mnt/projects/cis/runtime/ui/src/pages/infra/AdvisorChat.jsx` | 3.4 | add Quick Capture sidebar panel |

**No other files will be touched. This list is the contract.**
