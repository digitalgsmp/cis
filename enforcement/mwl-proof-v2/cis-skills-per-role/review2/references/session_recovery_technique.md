# Session State Recovery Technique

## When to Use
- OpenRouter (or other provider) ran out of credits mid-session, causing a memory gap
- Session was reset (`/new`) and you need to reconstruct what was happening before
- Cross-session handoff where the previous session's context is lost or incomplete
- Any time you need to figure out "what did I do last time and where did I leave off"

## The Problem
Hermes sessions store conversation context in `state.db` (SQLite). If the LLM provider
returns errors (credit exhaustion, rate limits, outages) mid-session, the conversation
may continue after the gap but the agent has no memory of what it did during the gap.
The session appears to have messages, but the agent's working context was lost.

## Recovery Sources (in priority order)

### 1. state.db — Session messages
The authoritative record of what was said. Query directly:

```bash
# List all sessions in this profile
sqlite3 ~/.hermes-<profile>/state.db \
  "SELECT id, title, datetime(started_at, 'unixepoch') FROM sessions ORDER BY started_at DESC LIMIT 10;"

# Read messages from a specific session (user + assistant only, with previews)
sqlite3 ~/.hermes-<profile>/state.db \
  "SELECT id, role, substr(content, 1, 300) FROM messages WHERE session_id='<ID>' AND role IN ('user','assistant') ORDER BY id ASC;"
```

### 2. request_dump_*.json — Raw API payloads
Gateway sessions store full API request payloads in `~/.hermes-<profile>/sessions/`.
These contain the complete message array sent to the LLM, including tool calls and results.
Essential for seeing what the agent actually did during the gap.

```bash
# List request dumps for a session (sorted by time)
ls -lt ~/.hermes-<profile>/sessions/request_dump_<session_id>_*.json
```

Each file contains the full `messages` array up to that point in the conversation.
Read the LAST dump to see the complete conversation state at the end of the session.

### 3. git log + git status — What was committed vs uncommitted
```bash
git log --oneline -10          # what's committed
git status --short             # what's modified but uncommitted
git diff --stat HEAD           # summary of uncommitted changes
```

The commit hash and timestamp tell you when the last committed work happened.
Uncommitted files show what was done after the last commit (during the gap).

### 4. CIS Spine DB — Pipeline state
```bash
# Recent workflow runs
sqlite3 data/cis_memory.db "SELECT * FROM workflow_runs ORDER BY created_at DESC LIMIT 5;"

# Session handoffs (cross-session context)
sqlite3 data/cis_memory.db "SELECT * FROM session_handoffs ORDER BY rowid DESC LIMIT 3;"

# Schema verification (what migrations were applied)
sqlite3 data/cis_memory.db "PRAGMA table_info(agent_trajectories);"
sqlite3 data/cis_memory.db "PRAGMA table_info(deliberation_rounds);" | grep -E "output|human"
```

### 5. Docker images — What was built
```bash
sg docker -c "docker images --format '{{.Repository}}:{{.Tag}} {{.CreatedAt}}' | grep cis"
```

Image creation timestamps tell you when builds happened. Compare against git commits
to identify work that was done but never committed.

### 6. Filesystem artifacts — What exists on disk
Check for files that should exist if a step was completed:
```bash
# Does the file exist?
ls -la <expected_path>

# Is the migration applied?
sqlite3 data/cis_memory.db "PRAGMA table_info(<table_name>);"

# Are the Docker images built?
sg docker -c "docker images | grep <image_name>"
```

## Reconstruction Pattern

1. **Find the session ID** — query `state.db` sessions table
2. **Read the message history** — get user + assistant messages to understand the task
3. **Check what was committed** — `git log` tells you the last stable state
4. **Check what's uncommitted** — `git status` shows work done after the last commit
5. **Verify artifacts on disk** — confirm files, DB schema, Docker images exist
6. **Cross-reference with the spec** — compare what's on disk against the build plan
7. **Report the gap** — tell the user exactly what was done during the gap and what's next

## Pitfall: `/resume` by name requires title to be set first

Eric tried `/new` then `/resume pipeline-build`. The resume failed because the
previous session's title was never actually set — the agent told Eric to type
`/title pipeline-build` but Eric did `/new` first, which starts a fresh session.

**The title must be set in the OLD session before `/new`.** After `/new` you're
in a new session and can't rename the old one.

If you need to resume by name:
1. Set the title BEFORE resetting: `/title pipeline-build`
2. Then `/new` to start fresh
3. Then `/resume pipeline-build` to load the old session

If the title was never set, resume by session ID instead:
```
/resume 20260708_001405_b5f276fb
```

Find the session ID via `state.db`:
```bash
sqlite3 ~/.hermes-<profile>/state.db \
  "SELECT id, title FROM sessions ORDER BY started_at DESC LIMIT 10;"
```

## Session Recovery vs session_search

`session_search` (the built-in tool) searches past sessions by keyword. It's useful
for finding relevant prior work but does NOT reconstruct the full state — it returns
snippets and bookends, not the complete picture.

For full state reconstruction (especially after a credit gap), use the direct SQLite
queries above. `session_search` is for discovery; this technique is for verification.
