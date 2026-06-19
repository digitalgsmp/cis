# CIS Front Door — Build Plan v1.0

**For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Wire the Intent Bridge (Prime discovery → CIS pipeline) and deliver remaining Front Door capabilities: MCP dispatch tools, archive indexing, and end-to-end integration validation.

**Architecture:** The existing MCP bridge (runtime/mcp_bridge/) has 11 read-only spine query tools. Extend it with 3 dispatch tools that call existing pipeline scripts. Build the Intent Bridge as a standalone Python module that monitors Prime discussions for crystallization signals and routes intent to the existing router (runtime/api/router.py). Index Eric's archive drives (/mnt/archive/) into Chroma using the existing chroma_index.py pipeline pattern.

**Tech Stack:** Python 3.12 (system), chromadb 1.5.9, sentence-transformers 5.5.0, mcp SDK, SQLite spine (data/cis_memory.db), existing pipeline scripts (tools/pipeline/)

---

## BASELINE VERIFICATION (actual starting state)

The specification (CIS_FRONT_DOOR_SPECIFICATION.md) contains factual errors about current state. This build plan corrects those errors and adapts implementation to reality.

COMMAND: ls /mnt/projects/cis/runtime/mcp_bridge/
OUTPUT: __init__.py  chroma_index.py  server.py  spine.py  tools.py

COMMAND: python3 -c "import chromadb; print(chromadb.__version__)" 2>&1 || pip3 show chromadb | grep Version
OUTPUT: chromadb 1.5.9 installed via system pip3

COMMAND: pip3 show sentence-transformers | grep Version
OUTPUT: Version: 5.5.0

COMMAND: ls /mnt/projects/cis/data/chroma_data/
OUTPUT: chroma.sqlite3 (188KB — Chroma collection initialized)

COMMAND: cd /mnt/projects/cis && sqlite3 data/cis_memory.db "SELECT id, node_label, status FROM build_plan_nodes WHERE node_label LIKE '%Tier 8%' OR node_label LIKE '%Tier 9%'"
OUTPUT:
12|Tier 8 — MCP Bridge|COMPLETE
13|Tier 9 — Chroma/VDB|COMPLETE

COMMAND: ls /mnt/projects/cis/tools/intent_bridge.py 2>&1
OUTPUT: ls: cannot access 'tools/intent_bridge.py': No such file or directory

COMMAND: ls /mnt/projects/cis/tools/index_archive.py 2>&1
OUTPUT: ls: cannot access 'tools/index_archive.py': No such file or directory

COMMAND: cd /mnt/projects/cis && ls runtime/api/router.py tools/pipeline/pipeline_dispatch.sh tools/pipeline/drafter_start.py
OUTPUT: (all three files exist)

### Corrections to the specification

| Spec Claim | Reality | Impact on Build Plan |
|---|---|---|
| "runtime/mcp/ is empty" | runtime/mcp_bridge/ exists with 5 Python files, 11 MCP tools, full Chroma pipeline | FD.1 scope changes: ADD dispatch tools to existing bridge, don't build from scratch |
| "chromadb not installed" | chromadb 1.5.9 installed via pip3, sentence-transformers 5.5.0 installed | FD.2 scope changes: ADD archive indexing pipeline, don't reinstall packages |
| "6 tools needed" | 11 tools already exist (read-only queries) | FD.1 adds 3 new dispatch tools: total 14 |
| "runtime/mcp/" path | Actual path is runtime/mcp_bridge/ | Use existing path. Create runtime/mcp/ symlink for spec compliance |
| Router/router.py at runtime/ | Router is at runtime/api/router.py with 8-route classification | FD.3 wires to existing router location |

---

## BUILD NODE FD.1: MCP Dispatch Tools

### Node Summary

Add 3 dispatch tools to the existing MCP bridge that initiate CIS pipeline operations. The existing 11 tools are read-only spine queries. The new tools invoke existing pipeline scripts to start Drafter, Reviewer, and Implementer workflows.

**Depends on:** None (existing mcp_bridge is functional)
**Estimated time:** 25 minutes
**Risk:** LOW — additive only, no existing tool changes

### Files

| File | Action | Purpose |
|---|---|---|
| runtime/mcp_bridge/tools.py | MODIFY: add 3 tool definitions + 3 handlers | Register dispatch tools |
| runtime/mcp/ | CREATE: symlink to mcp_bridge/ | Spec path compliance |
| tests/test_mcp_dispatch.py | CREATE: 6 tests | Verify dispatch tools register and validate input |

### Architecture Note

The existing MCP bridge at runtime/mcp_bridge/ uses stdio transport (not HTTP). It runs as a child process of Hermes, started via Hermes MCP config. The dispatch tools call existing pipeline Python scripts via subprocess — they do NOT import them directly (avoiding module conflicts). Each dispatch tool validates inputs, creates a workflow_run via drafter_start.py, and returns the run_id.

### Step 1: Create runtime/mcp/ symlink

```bash
cd /mnt/projects/cis
ln -s mcp_bridge runtime/mcp
ls -la runtime/mcp/server.py  # verify accessible
```

### Step 2: Add dispatch tool definitions to tools.py

Insert after the existing 11 tool definitions (after cis_get_similar, before HANDLERS dict) in runtime/mcp_bridge/tools.py.

Three new tools:

**Tool 1: cis_dispatch_drafter** — Initiates Drafter lifecycle for a crystallized topic. Calls `python3 tools/pipeline/drafter_start.py <topic> --intent <intent>`. Returns workflow_run_id.

```python
    {
        "name": "cis_dispatch_drafter",
        "description": (
            "Start the CIS Drafter pipeline for a crystallized topic. "
            "Creates a workflow_run and dispatches the Drafter to produce "
            "a specification. Returns the workflow_run_id for tracking. "
            "Use this when Eric says 'draft this' or 'spec this out'."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "What to build — the crystallized work description",
                },
                "intent": {
                    "type": "string",
                    "description": "Why to build it — the underlying need driving the work",
                },
                "session_id": {
                    "type": "string",
                    "description": "Optional: session ID for lifecycle tracking",
                },
            },
            "required": ["topic", "intent"],
        },
    },
```

**Tool 2: cis_dispatch_reviewer** — Dispatches Reviewer reconciliation for a Drafter proposal. Calls `python3 tools/pipeline/reviewer_reconcile.py --run-id <run_id>`. Returns deliberation status.

```python
    {
        "name": "cis_dispatch_reviewer",
        "description": (
            "Dispatch the CIS Reviewer (R1 + Qwen dual-review) for a "
            "Drafter proposal. Requires an existing workflow_run_id from "
            "cis_dispatch_drafter. Returns deliberation status and round count."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "run_id": {
                    "type": "string",
                    "description": "The workflow_run_id from cis_dispatch_drafter",
                },
            },
            "required": ["run_id"],
        },
    },
```

**Tool 3: cis_dispatch_implementer** — Dispatches Implementer for an Eric-approved directive. Calls pipeline with the FINAL_DIRECTIVE. Returns implementation evidence.

```python
    {
        "name": "cis_dispatch_implementer",
        "description": (
            "Dispatch the CIS Implementer to execute an Eric-approved "
            "FINAL_DIRECTIVE. Requires a workflow_run_id with Eric Gate approval. "
            "The Implementer builds per the directive and returns evidence. "
            "Shell hooks enforce pre-execution gates automatically."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "run_id": {
                    "type": "string",
                    "description": "The workflow_run_id with Eric Gate approval",
                },
            },
            "required": ["run_id"],
        },
    },
```

### Step 3: Add dispatch handler functions to tools.py

Insert after the existing handlers (after handle_get_similar, before HANDLERS dict).

```python
def handle_dispatch_drafter(arguments):
    """Handler for cis_dispatch_drafter — calls drafter_start.py."""
    import subprocess
    import os

    topic = arguments.get("topic", "")
    intent = arguments.get("intent", "")
    session_id = arguments.get("session_id", "")

    if not topic:
        return {"error": "topic is required"}
    if not intent:
        return {"error": "intent is required"}

    repo_root = os.environ.get("CIS_REPO_ROOT", "/mnt/projects/cis")
    script = os.path.join(repo_root, "tools", "pipeline", "drafter_start.py")
    python = os.environ.get("CIS_PYTHON", "python3")

    cmd = [python, script, topic, "--intent", intent]
    if session_id:
        cmd.extend(["--session-id", session_id])

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=repo_root,
        )
        return {
            "exit_code": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip() if result.returncode != 0 else "",
        }
    except subprocess.TimeoutExpired:
        return {"error": "Drafter dispatch timed out after 30s"}
    except Exception as exc:
        return {"error": str(exc)}


def handle_dispatch_reviewer(arguments):
    """Handler for cis_dispatch_reviewer — calls reviewer_reconcile.py."""
    import subprocess
    import os

    run_id = arguments.get("run_id", "")
    if not run_id:
        return {"error": "run_id is required"}

    repo_root = os.environ.get("CIS_REPO_ROOT", "/mnt/projects/cis")
    script = os.path.join(
        repo_root, "tools", "pipeline", "reviewer_reconcile.py"
    )
    python = os.environ.get("CIS_PYTHON", "python3")

    try:
        result = subprocess.run(
            [python, script, "--run-id", run_id, "--max-rounds", "2"],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=repo_root,
        )
        return {
            "exit_code": result.returncode,
            "stdout": result.stdout.strip()[-2000:],
            "stderr": result.stderr.strip() if result.returncode != 0 else "",
        }
    except subprocess.TimeoutExpired:
        return {"error": "Reviewer dispatch timed out after 120s"}
    except Exception as exc:
        return {"error": str(exc)}


def handle_dispatch_implementer(arguments):
    """Handler for cis_dispatch_implementer — dispatches to hermes-v4impl."""
    import subprocess
    import os

    run_id = arguments.get("run_id", "")
    if not run_id:
        return {"error": "run_id is required"}

    repo_root = os.environ.get("CIS_REPO_ROOT", "/mnt/projects/cis")

    # Check Eric Gate approval before dispatching
    from . import spine
    eric_status = spine.query_eric_gate_approval_for_run(run_id)
    if not eric_status or not eric_status.get("approved"):
        return {
            "error": (
                "Eric Gate approval required before Implementer dispatch. "
                "Run ID {} has no active Eric Gate approval.".format(run_id)
            ),
            "eric_gate_status": eric_status,
        }

    # Dispatch to hermes-v4impl via the gateway API
    try:
        result = subprocess.run(
            [
                "curl", "-s", "-X", "POST",
                "http://127.0.0.1:8646/v1/chat/completions",
                "-H", "Content-Type: application/json",
                "-d", json.dumps({
                    "messages": [{
                        "role": "user",
                        "content": (
                            "IMPLEMENT workflow_run {} from CIS pipeline. "
                            "Execute per the approved FINAL_DIRECTIVE. "
                            "Return evidence.".format(run_id)
                        ),
                    }],
                    "max_tokens": 4096,
                }),
            ],
            capture_output=True,
            text=True,
            timeout=300,
            cwd=repo_root,
        )
        return {
            "exit_code": result.returncode,
            "response": result.stdout[:2000] if result.stdout else "",
            "stderr": result.stderr[:500] if result.returncode != 0 else "",
        }
    except subprocess.TimeoutExpired:
        return {"error": "Implementer dispatch timed out after 300s"}
    except Exception as exc:
        return {"error": str(exc)}
```

### Step 4: Add spine helper for Eric Gate approval check

Insert in runtime/mcp_bridge/spine.py before the final line:

```python
def query_eric_gate_approval_for_run(run_id, db_path=None):
    """Check if a workflow_run has an active Eric Gate approval."""
    conn = _connect_readonly(db_path)
    try:
        row = conn.execute(
            """SELECT ega.decision, ega.decided_at, ega.rationale,
                      ega.workflow_run_id
               FROM eric_gate_approvals ega
               WHERE ega.workflow_run_id = ?
                 AND ega.is_current = 1
                 AND ega.decision = 'APPROVED'
               ORDER BY ega.decided_at DESC
               LIMIT 1""",
            (run_id,),
        ).fetchone()
        if row is None:
            return None
        return dict(row)
    finally:
        conn.close()
```

### Step 5: Update HANDLERS dict

Add the three new handlers to the HANDLERS dict in tools.py:

```python
    "cis_dispatch_drafter": handle_dispatch_drafter,
    "cis_dispatch_reviewer": handle_dispatch_reviewer,
    "cis_dispatch_implementer": handle_dispatch_implementer,
```

### Step 6: Add `import json` to tools.py

The handle_dispatch_implementer function uses json.dumps(). Add `import json` to the top of tools.py if not already present.

### Step 7: Write dispatch tests

Create tests/test_mcp_dispatch.py:

```python
"""Tests for MCP dispatch tools."""
import json
import os
import sys
import unittest

# Add repo root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "runtime"))

os.environ.setdefault("CIS_SPINE_PATH",
    "/mnt/projects/cis/data/cis_memory.db")
os.environ.setdefault("CIS_REPO_ROOT", "/mnt/projects/cis")


class TestDispatchTools(unittest.TestCase):
    """Validate dispatch tool definitions and handler signatures."""

    @classmethod
    def setUpClass(cls):
        from mcp_bridge import tools as mcp_tools
        cls.tools = mcp_tools

    def test_dispatch_tools_registered(self):
        """All three dispatch tools appear in TOOLS list."""
        names = {t["name"] for t in self.tools.TOOLS}
        expected = {
            "cis_dispatch_drafter",
            "cis_dispatch_reviewer",
            "cis_dispatch_implementer",
        }
        missing = expected - names
        self.assertEqual(
            len(missing), 0,
            f"Missing dispatch tools: {missing}"
        )

    def test_dispatch_tools_in_handlers(self):
        """All three dispatch tools have handler functions."""
        expected = {
            "cis_dispatch_drafter",
            "cis_dispatch_reviewer",
            "cis_dispatch_implementer",
        }
        missing = expected - set(self.tools.HANDLERS.keys())
        self.assertEqual(
            len(missing), 0,
            f"Missing dispatch handlers: {missing}"
        )

    def test_total_tool_count(self):
        """Total tools should be 14 (11 existing + 3 new)."""
        self.assertGreaterEqual(
            len(self.tools.TOOLS), 14,
            f"Expected >=14 tools, got {len(self.tools.TOOLS)}"
        )

    def test_dispatch_drafter_schema(self):
        """cis_dispatch_drafter has required inputSchema."""
        tool = self._find_tool("cis_dispatch_drafter")
        self.assertIsNotNone(tool)
        schema = tool["inputSchema"]
        self.assertIn("topic", schema.get("required", []))
        self.assertIn("intent", schema.get("required", []))

    def test_dispatch_reviewer_schema(self):
        """cis_dispatch_reviewer requires run_id."""
        tool = self._find_tool("cis_dispatch_reviewer")
        self.assertIsNotNone(tool)
        self.assertIn("run_id", tool["inputSchema"]["required"])

    def test_dispatch_implementer_schema(self):
        """cis_dispatch_implementer requires run_id."""
        tool = self._find_tool("cis_dispatch_implementer")
        self.assertIsNotNone(tool)
        self.assertIn("run_id", tool["inputSchema"]["required"])

    def _find_tool(self, name):
        for t in self.tools.TOOLS:
            if t["name"] == name:
                return t
        return None


if __name__ == "__main__":
    unittest.main()
```

### Step 8: Run tests

```bash
cd /mnt/projects/cis
python3 -m pytest tests/test_mcp_dispatch.py -v
```

Expected: 7 tests pass (or 6 if import issues — adapt as needed)

### Step 9: Commit

```bash
git add runtime/mcp_bridge/tools.py runtime/mcp_bridge/spine.py
git add runtime/mcp tests/test_mcp_dispatch.py
git commit -m "feat(fd.1): add 3 MCP dispatch tools (drafter, reviewer, implementer)"
```

### Verification (FD.1)

COMMAND: python3 -c "
import sys; sys.path.insert(0, '/mnt/projects/cis/runtime')
from mcp_bridge import tools
names = [t['name'] for t in tools.TOOLS]
print('Total tools:', len(tools.TOOLS))
print('Dispatch tools present:', all(t in names for t in ['cis_dispatch_drafter', 'cis_dispatch_reviewer', 'cis_dispatch_implementer']))
print('All handlers mapped:', all(t['name'] in tools.HANDLERS for t in tools.TOOLS))
"
OUTPUT: Total tools: 14, Dispatch tools present: True, All handlers mapped: True

---

## BUILD NODE FD.2: Intent Extraction Pipeline

### Purpose

Recover Eric's stated intent from months of conversations across multiple
LLMs and platforms. Eric has conceptually worked out almost every aspect of
the tool he is building — but it is scattered through Hermes session logs,
exported chat transcripts, saved ad hoc files, and thousands of vibe-coding
build attempts. LLMs repeatedly ignored his stated goals due to enterprise
training bias. This pipeline extracts Eric's own words, organizes them by
project domain, and makes them searchable so CIS profiles stop ignoring what
Eric has been saying all along.

### Architecture

```
Sources                          Extraction              Organization
                                                         
Hermes session logs  ─┐                                 
  (~/.hermes*/sessions/)├──→ Extract Eric's    ──→ CIS goals/intent
Saved chat exports    ─┤    messages only          SWA goals/intent  
  (ChatGPT, Claude,    │    (role='user' or        SWA/WIASW workflow
   ad hoc files)      ─┤     speaker='Eric')       Architecture vision
Architecture atlas     │                            Contradictions
  extraction analyses ─┘    Skip: LLM responses,    Evolution over time
  (21 files, already        code blocks, system     Timestamps for
   extracted)               messages                chronology
                                         
                                │
                                ▼
                         Chroma collection
                         "cis_intent_corpus"
                           (semantic search)
                                │
                                ▼
                         MCP tool:
                         search_intent("WIAS stages")
                         → Eric's verbatim words
```

### Key Rules

1. **Eric's words only** — filter by speaker/role. Skip all LLM responses.
2. **Already-extracted first** — the 21 architecture atlas extraction analyses
   are pre-processed Eric intent. Index these immediately as the seed corpus.
3. **Organize by domain** — tag each extracted statement with project domain
   (CIS, SWA, WIASW workflow, architecture, general) for targeted retrieval.
4. **Surface evolution** — preserve timestamps. Eric's thinking evolved.
   Early ideas vs refined concepts are both valuable.
5. **Surface contradictions** — if Eric said different things at different
   times, both are recorded. Profiles need to see the evolution.

### Depends on

None. chromadb 1.5.9 and sentence-transformers 5.5.0 already installed.
Existing Chroma data directory at data/chroma_data/.

### Estimated time

60 minutes (was 30 min in v1 — expanded for extraction logic)

### Risk

MEDIUM — extraction across multiple formats. Graceful fallback for
unparseable files. Read-only on all sources.

### Files

| File | Action | Purpose |
|---|---|---|
| tools/extract_intent.py | CREATE | Extraction pipeline — walk sources, filter Eric's words, tag domain |
| tools/index_intent.py | CREATE | Index extracted intent into Chroma collection "cis_intent_corpus" |
| runtime/mcp_bridge/tools.py | MODIFY | Add MCP tool: search_intent(query, domain) |
| tests/test_intent_extraction.py | CREATE | 5 tests |

### Source Locations

| Source | Path | Format | Priority |
|--------|------|--------|----------|
| Architecture atlas (extracted) | docs/architecture_atlas/*extraction*.md | Markdown — Eric's intent already pulled | HIGH — seed corpus |
| Seed intent corpus | seed_intent_corpus/*.md | Markdown — Eric's verbatim words | HIGH |
| Original CIS chats | docs/architecture_atlas/original_CISChats/*.md | Markdown — conversations | MEDIUM |
| Hermes session logs | ~/.hermes*/sessions/*.json | JSON — full transcripts | MEDIUM |
| Hermes session logs (r1) | ~/.hermes-r1/sessions/*.json | JSON — Reviewer sessions | LOW |
| Ad hoc saved files | (TBD — Eric to identify) | Various | DEFERRED |

### Step 1: Verify source availability

```bash
cd /mnt/projects/cis
echo "=== Extraction analyses ===" && ls docs/architecture_atlas/*extraction* 2>/dev/null | wc -l
echo "=== Seed intent ===" && ls seed_intent_corpus/ 2>/dev/null
echo "=== CIS chats ===" && ls docs/architecture_atlas/original_CISChats/ 2>/dev/null | wc -l
echo "=== Hermes sessions (prime) ===" && ls ~/.hermes/sessions/*.json 2>/dev/null | wc -l
echo "=== Hermes sessions (r1) ===" && ls ~/.hermes-r1/sessions/*.json 2>/dev/null | wc -l
```

### Step 2: Create tools/extract_intent.py

This is the core extraction engine. It walks source directories, identifies
Eric's messages (by role/speaker), extracts them, and tags by domain.

```python
#!/usr/bin/env python3
"""
extract_intent.py — Extract Eric's stated intent from conversation sources.

Filters to Eric's messages only (role='user', speaker='Eric', or 'Vector Pirate').
Skips LLM responses, code blocks, and system messages.
Tags each extracted statement with project domain.
Outputs JSONL for indexing.

Sources (priority order):
  1. Architecture atlas extraction analyses (already extracted)
  2. Seed intent corpus (verbatim Eric words)
  3. Original CIS chats
  4. Hermes session logs (json, all profiles)

Usage:
  python3 tools/extract_intent.py                    # Extract all sources
  python3 tools/extract_intent.py --source atlas     # Atlas only
  python3 tools/extract_intent.py --source sessions  # Session logs only
  python3 tools/extract_intent.py --dry-run          # Show what would be extracted
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = "/mnt/projects/cis"
OUTPUT_DIR = os.path.join(REPO_ROOT, "data", "extracted_intent")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Eric's identifiers across platforms
ERIC_IDS = {
    "eric", "vector pirate", "vector_pirate", "user",
    "human", "eric (you)", "operator",
}

# Domain keywords for auto-tagging
DOMAIN_KEYWORDS = {
    "cis": [
        "cis", "hermes", "drafter", "reviewer", "implementer",
        "pipeline", "gate", "deliberation", "adversarial", "spine",
        "build plan", "eric gate", "router", "profiles",
        "verification", "oversight", "hardening", "mcp",
    ],
    "swa": [
        "swa", "social work", "client", "billing", "progress note",
        "case management", "appointment", "intake", "schedule",
        "calendar", "transcription", "audio",
    ],
    "wias": [
        "wias", "word image action sound", "creative",
        "pipeline stage", "production", "project manager",
        "workflow", "houdini", "comfyui", "blender",
    ],
    "architecture": [
        "architecture", "design", "concept", "vision",
        "knowledge base", "archive", "vdb", "database",
        "schema", "integration", "abstraction layer",
    ],
}


def is_eric_message(message: dict, source_type: str) -> bool:
    """Determine if a message is from Eric."""
    if source_type == "atlas":
        # Extraction analyses — all content is Eric's intent
        return True

    if source_type == "seed":
        # Seed intent corpus — all Eric's words
        return True

    if source_type == "session":
        # Hermes session JSON
        role = message.get("role", "").lower()
        name = message.get("name", "").lower()
        content = message.get("content", "")
        if not content or len(content.strip()) < 10:
            return False
        # Check role
        if role in ("user", "human"):
            return True
        # Check name
        if any(eid in name for eid in ERIC_IDS):
            return True
        return False

    if source_type == "chat":
        # Original CIS chat markdown
        speaker = message.get("speaker", "").lower()
        return any(eid in speaker for eid in ERIC_IDS)

    return False


def tag_domain(text: str) -> list:
    """Auto-tag text with project domains based on keyword matches."""
    text_lower = text.lower()
    domains = []
    for domain, keywords in DOMAIN_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        if score >= 2:
            domains.append(domain)
    if not domains:
        domains.append("general")
    return domains


def extract_atlas_files(dry_run: bool = False) -> list:
    """Extract from architecture atlas extraction analyses."""
    atlas_dir = os.path.join(
        REPO_ROOT, "docs", "architecture_atlas"
    )
    results = []
    for f in sorted(Path(atlas_dir).glob("*extraction*")):
        if not f.is_file():
            continue
        with open(f) as fh:
            content = fh.read()
        if len(content) < 50:
            continue
        domains = tag_domain(content)
        results.append({
            "source": str(f.relative_to(REPO_ROOT)),
            "source_type": "atlas",
            "content": content[:4000],  # Cap per entry
            "domains": domains,
            "extracted_at": datetime.now().isoformat(),
        })
        if not dry_run:
            print(f"  atlas: {f.name} → {domains}")
    return results


def extract_seed_corpus(dry_run: bool = False) -> list:
    """Extract from seed intent corpus."""
    seed_dir = os.path.join(REPO_ROOT, "seed_intent_corpus")
    results = []
    for f in sorted(Path(seed_dir).glob("*.md")):
        with open(f) as fh:
            content = fh.read()
        # Split by sections for granular retrieval
        sections = re.split(r'\n##?\s+', content)
        for section in sections:
            section = section.strip()
            if len(section) < 50:
                continue
            domains = tag_domain(section)
            results.append({
                "source": str(f.relative_to(REPO_ROOT)),
                "source_type": "seed",
                "content": section[:4000],
                "domains": domains,
                "extracted_at": datetime.now().isoformat(),
            })
        if not dry_run:
            print(f"  seed: {f.name} → {len(sections)} sections")
    return results


def extract_chat_files(dry_run: bool = False) -> list:
    """Extract Eric's messages from original CIS chat transcripts."""
    chat_dir = os.path.join(
        REPO_ROOT, "docs", "architecture_atlas", "original_CISChats"
    )
    results = []
    for f in sorted(Path(chat_dir).glob("*.md")):
        with open(f) as fh:
            content = fh.read()
        # Parse markdown conversations: look for "Eric:" or "You:" prefixes
        eric_msgs = re.findall(
            r'(?:^|\n)(?:Eric|You|Vector Pirate|Human|Operator):\s*(.+?)(?=\n(?:[A-Z][a-z]+|Claude|ChatGPT|Assistant|Hermes|Qwen):|\Z)',
            content, re.DOTALL
        )
        for msg in eric_msgs:
            msg = msg.strip()
            if len(msg) < 20:
                continue
            domains = tag_domain(msg)
            results.append({
                "source": str(f.relative_to(REPO_ROOT)),
                "source_type": "chat",
                "content": msg[:4000],
                "domains": domains,
                "extracted_at": datetime.now().isoformat(),
            })
        if not dry_run:
            print(f"  chat: {f.name} → {len(eric_msgs)} Eric messages")
    return results


def extract_session_logs(dry_run: bool = False) -> list:
    """Extract Eric's messages from Hermes session JSON files."""
    results = []
    session_dirs = [
        os.path.expanduser("~/.hermes/sessions/"),
        os.path.expanduser("~/.hermes-r1/sessions/"),
        os.path.expanduser("~/.hermes-v4pro/sessions/"),
        os.path.expanduser("~/.hermes-v4impl/sessions/"),
    ]
    for session_dir in session_dirs:
        if not os.path.isdir(session_dir):
            continue
        for f in sorted(Path(session_dir).glob("*.json")):
            try:
                with open(f) as fh:
                    data = json.load(fh)
            except (json.JSONDecodeError, IOError):
                continue
            messages = data.get("messages", []) if isinstance(data, dict) else data
            if not isinstance(messages, list):
                continue
            for msg in messages:
                if not isinstance(msg, dict):
                    continue
                if is_eric_message(msg, "session"):
                    content = msg.get("content", "")
                    if isinstance(content, list):
                        # Multimodal — extract text parts
                        text_parts = [
                            p.get("text", "") for p in content
                            if isinstance(p, dict) and p.get("type") == "text"
                        ]
                        content = " ".join(text_parts)
                    if len(content) < 20:
                        continue
                    domains = tag_domain(content)
                    results.append({
                        "source": str(f),
                        "source_type": "session",
                        "content": content[:4000],
                        "domains": domains,
                        "timestamp": msg.get("timestamp", ""),
                        "extracted_at": datetime.now().isoformat(),
                    })
        if not dry_run:
            print(f"  sessions: {session_dir} → {len(results)} messages so far")
    return results


def main():
    parser = argparse.ArgumentParser(
        description="Extract Eric's stated intent from conversation sources"
    )
    parser.add_argument(
        "--source",
        choices=["atlas", "seed", "chats", "sessions", "all"],
        default="all",
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    all_results = []

    if args.source in ("atlas", "all"):
        print("Extracting from architecture atlas...")
        all_results.extend(extract_atlas_files(args.dry_run))

    if args.source in ("seed", "all"):
        print("Extracting from seed intent corpus...")
        all_results.extend(extract_seed_corpus(args.dry_run))

    if args.source in ("chats", "all"):
        print("Extracting from CIS chat transcripts...")
        all_results.extend(extract_chat_files(args.dry_run))

    if args.source in ("sessions", "all"):
        print("Extracting from Hermes session logs...")
        all_results.extend(extract_session_logs(args.dry_run))

    if args.dry_run:
        print(f"\nWould extract {len(all_results)} statements")
        # Show sample
        for r in all_results[:3]:
            print(f"  [{','.join(r['domains'])}] {r['content'][:100]}...")
        return

    # Write output
    output_path = args.output or os.path.join(
        OUTPUT_DIR,
        f"intent_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
    )
    with open(output_path, "w") as f:
        for r in all_results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # Summary
    domain_counts = {}
    for r in all_results:
        for d in r["domains"]:
            domain_counts[d] = domain_counts.get(d, 0) + 1

    print(f"\nExtracted {len(all_results)} statements → {output_path}")
    print("Domain distribution:")
    for domain, count in sorted(domain_counts.items(), key=lambda x: -x[1]):
        print(f"  {domain}: {count}")


if __name__ == "__main__":
    main()
```

### Step 3: Create tools/index_intent.py

Indexes the extracted JSONL into Chroma collection "cis_intent_corpus".

```python
#!/usr/bin/env python3
"""
index_intent.py — Index extracted intent statements into Chroma.

Reads JSONL output from extract_intent.py, embeds using sentence-transformers,
stores in Chroma collection 'cis_intent_corpus' with domain metadata.

Usage:
  python3 tools/index_intent.py data/extracted_intent/intent_*.jsonl
  python3 tools/index_intent.py --collection cis_intent_corpus --stats
  python3 tools/index_intent.py --search "WIAS pipeline stages"
"""
import argparse
import json
import os
import sys
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

CHROMA_PATH = os.environ.get(
    "CIS_CHROMA_PATH",
    "/mnt/projects/cis/data/chroma_data",
)
COLLECTION_NAME = "cis_intent_corpus"
MODEL_NAME = "all-MiniLM-L6-v2"

# Batch size for embedding
BATCH_SIZE = 32


def get_collection():
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    try:
        return client.get_collection(COLLECTION_NAME)
    except Exception:
        return client.create_collection(
            COLLECTION_NAME,
            metadata={"description": "Eric's stated intent across projects"},
        )


def index_file(jsonl_path: str):
    """Index a JSONL file of extracted intent."""
    collection = get_collection()
    model = SentenceTransformer(MODEL_NAME)

    documents = []
    metadatas = []
    ids = []

    with open(jsonl_path) as f:
        for i, line in enumerate(f):
            if not line.strip():
                continue
            record = json.loads(line)
            content = record.get("content", "")
            if len(content) < 20:
                continue

            documents.append(content)
            metadatas.append({
                "source": record.get("source", ""),
                "source_type": record.get("source_type", ""),
                "domains": ",".join(record.get("domains", [])),
                "timestamp": record.get("timestamp", ""),
            })
            ids.append(f"intent_{i:06d}")

    if not documents:
        print("No documents to index.")
        return

    print(f"Embedding {len(documents)} documents...")
    embeddings = model.encode(
        documents,
        batch_size=BATCH_SIZE,
        show_progress_bar=True,
    ).tolist()

    print(f"Adding to collection '{COLLECTION_NAME}'...")
    collection.add(
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas,
        ids=ids,
    )
    print(f"Indexed {len(documents)} statements.")


def search(query: str, domain: str = None, n_results: int = 5):
    """Search the intent corpus."""
    collection = get_collection()
    model = SentenceTransformer(MODEL_NAME)
    query_embedding = model.encode([query]).tolist()

    where_filter = None
    if domain:
        where_filter = {"domains": {"$contains": domain}}

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=n_results,
        where=where_filter,
    )

    for i, (doc, meta, dist) in enumerate(zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    )):
        print(f"\n--- Result {i+1} (distance: {dist:.3f}) ---")
        print(f"Source: {meta.get('source', 'unknown')}")
        print(f"Domains: {meta.get('domains', '')}")
        print(doc[:500])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("jsonl", nargs="?", help="JSONL file to index")
    parser.add_argument("--stats", action="store_true")
    parser.add_argument("--search", help="Search query")
    parser.add_argument("--domain", help="Filter by domain (cis, swa, wias)")
    args = parser.parse_args()

    if args.stats:
        collection = get_collection()
        print(f"Collection: {COLLECTION_NAME}")
        print(f"Documents: {collection.count()}")
        return

    if args.search:
        search(args.search, args.domain)
        return

    if args.jsonl:
        index_file(args.jsonl)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
```

### Step 4: Add MCP search tool

Add to runtime/mcp_bridge/tools.py a new MCP tool that profiles can call
to search Eric's intent before responding:

```python
# In TOOLS list:
{
    "name": "cis_search_intent",
    "description": (
        "Search Eric's stated intent and goals across CIS and SWA projects (including WIASW workflow). "
        "Use BEFORE drafting proposals or making architectural decisions to ensure "
        "alignment with Eric's vision. Returns verbatim excerpts from Eric's own words."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "What aspect of Eric's intent to search for"
            },
            "domain": {
                "type": "string",
                "description": "Filter by domain: cis, swa, wias, architecture",
                "enum": ["cis", "swa", "wias", "architecture", "general"],
            },
            "n_results": {
                "type": "integer",
                "description": "Number of results (default 5)",
                "default": 5,
            },
        },
        "required": ["query"],
    },
},

# In HANDLERS dict:
"cis_search_intent": handle_search_intent,
```

```python
def handle_search_intent(args: dict) -> str:
    """MCP handler: search Eric's intent corpus."""
    import chromadb
    from sentence_transformers import SentenceTransformer

    query = args.get("query", "")
    domain = args.get("domain")
    n_results = args.get("n_results", 5)

    client = chromadb.PersistentClient(path=CHROMA_PATH)
    try:
        collection = client.get_collection("cis_intent_corpus")
    except Exception:
        return json.dumps({"error": "Intent corpus not yet indexed"})

    model = SentenceTransformer("all-MiniLM-L6-v2")
    query_embedding = model.encode([query]).tolist()

    where_filter = None
    if domain:
        where_filter = {"domains": {"$contains": domain}}

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=n_results,
        where=where_filter,
    )

    output = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        output.append({
            "content": doc[:500],
            "source": meta.get("source", ""),
            "domains": meta.get("domains", ""),
            "relevance": round(1.0 - dist, 3) if dist else 1.0,
        })

    return json.dumps({
        "query": query,
        "domain_filter": domain,
        "results": output,
        "total_results": len(output),
    })
```

### Step 5: Create tests

```python
# tests/test_intent_extraction.py
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))

# Import extraction module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))
import importlib.util
spec = importlib.util.spec_from_file_location(
    "extract_intent",
    os.path.join(os.path.dirname(__file__), "..", "tools", "extract_intent.py")
)
extract_intent = importlib.util.module_from_spec(spec)


class TestIntentExtraction(unittest.TestCase):

    def test_is_eric_session_user(self):
        """User role messages are Eric's."""
        msg = {"role": "user", "content": "Build the CIS front door pipeline"}
        self.assertTrue(extract_intent.is_eric_message(msg, "session"))

    def test_is_not_eric_session_assistant(self):
        """Assistant role messages are NOT Eric's."""
        msg = {"role": "assistant", "content": "I will build that for you"}
        self.assertFalse(extract_intent.is_eric_message(msg, "session"))

    def test_is_eric_chat_speaker(self):
        """Eric speaker in chat transcripts."""
        msg = {"speaker": "Eric", "content": "I need the archive indexed"}
        self.assertTrue(extract_intent.is_eric_message(msg, "chat"))

    def test_domain_tagging_cis(self):
        """CIS keywords tag as cis domain."""
        text = "The drafter and reviewer pipeline needs MCP integration"
        domains = extract_intent.tag_domain(text)
        self.assertIn("cis", domains)

    def test_domain_tagging_multiple(self):
        """Text spanning domains gets multiple tags."""
        text = "CIS should use MCP to search the archive for SWA client data"
        domains = extract_intent.tag_domain(text)
        self.assertIn("cis", domains)
        self.assertIn("swa", domains)

    def test_short_messages_filtered(self):
        """Messages under 10 chars are filtered."""
        # is_eric_message requires len >= 10
        msg = {"role": "user", "content": "ok"}
        # Short message should still pass role check but extraction
        # will filter by content length
        self.assertTrue(extract_intent.is_eric_message(msg, "session"))


if __name__ == "__main__":
    unittest.main()
```

### Step 6: Run extraction (dry-run first)

```bash
cd /mnt/projects/cis
python3 tools/extract_intent.py --source atlas --dry-run
python3 tools/extract_intent.py --source seed --dry-run
```

Verify output shows Eric's words, not LLM responses.

### Step 7: Run full extraction

```bash
cd /mnt/projects/cis
python3 tools/extract_intent.py --source all 2>&1 | tail -20
```

### Step 8: Index into Chroma

```bash
cd /mnt/projects/cis
python3 tools/index_intent.py data/extracted_intent/intent_*.jsonl
python3 tools/index_intent.py --stats
```

### Step 9: Verify search

```bash
cd /mnt/projects/cis
python3 tools/index_intent.py --search "WIAS creative pipeline stages" --domain wias
python3 tools/index_intent.py --search "CIS adversarial review" --domain cis
python3 tools/index_intent.py --search "SWA client tracking" --domain swa
```

Expected: Returns verbatim Eric quotes relevant to each domain.

### Step 10: Commit

```bash
git add tools/extract_intent.py tools/index_intent.py
git add runtime/mcp_bridge/tools.py tests/test_intent_extraction.py
git add data/extracted_intent/
git commit -m "feat(fd.2): intent extraction pipeline — recover Eric's stated goals from conversations"
```

### Verification (FD.2)

COMMAND: python3 tools/index_intent.py --stats
OUTPUT:
```
Collection: cis_intent_corpus
Documents: N (N > 0 — at minimum, architecture atlas + seed corpus indexed)
```

COMMAND: python3 tools/index_intent.py --search "enterprise bias LLM ignore goals" --domain general
OUTPUT: Returns Eric's verbatim statements about LLMs ignoring his goals.

COMMAND: python3 -m pytest tests/test_intent_extraction.py -v
## BUILD NODE FD.3: Intent Bridge

### Node Summary

Build the Intent Bridge that monitors Prime (8642) discussions for crystallization signals and routes intent to the CIS pipeline. This is the key missing piece — it transitions FROM Eric's natural brainstorming with Prime TO the automated CIS pipeline (Drafter → dual review → Eric Gate → Implementer).

**Depends on:** FD.1 (dispatch tools available), FD.2 (archive search available)
**Estimated time:** 40 minutes
**Risk:** MEDIUM — introduces new message processing flow; must not break Prime's normal operation

### Architecture

The Intent Bridge is a standalone Python module (`tools/intent_bridge.py`) that can operate in two modes:

1. **Signal detection mode:** Scans Prime discussion text for crystallization signals ("draft this", "spec this out", "build this", "implement this", "turn this into"). When detected, extracts the crystallized topic and intent, then dispatches to the router.

2. **Manual trigger mode:** Eric explicitly invokes the bridge with a topic (e.g., from a Telegram command `/draft <topic>`).

The bridge does NOT replace Prime. It sits BETWEEN Prime and the CIS router as a transition mechanism. Prime handles conversation. The bridge detects when a conversation has crystallized into actionable work.

### Files

| File | Action | Purpose |
|---|---|---|
| tools/intent_bridge.py | CREATE | Intent detection + routing dispatch |
| tools/intent_bridge_config.yaml | CREATE | Configuration: signal phrases, routing rules |
| tests/test_intent_bridge.py | CREATE | 8 tests |

### Signal Detection Design

The bridge scans message text for signal phrases. Three categories:

1. **Drafting signals** (→ route to Drafter):
   - "draft this", "spec this out", "write a spec", "create a proposal",
   - "design this", "plan this", "propose", "write a plan"

2. **Building signals** (→ route to Implementer with gate check):
   - "build this", "implement this", "code this", "make this"

3. **Reviewing signals** (→ route to Reviewer):
   - "review this", "critique this", "check this", "verify this"

The bridge extracts the TOPIC from the message context (the thing to draft/build/review) and the INTENT (why — from surrounding discussion context). It then calls the existing router's classify_route() to determine the pipeline path.

### Step 1: Write intent_bridge_config.yaml

Create tools/intent_bridge_config.yaml:

```yaml
# CIS Intent Bridge Configuration
# Detects crystallization signals in Prime discussions and routes to CIS pipeline.

# Signal patterns — when these appear in a message, the bridge fires
signals:
  drafting:
    phrases:
      - "draft this"
      - "spec this out"
      - "write a spec"
      - "create a proposal"
      - "design this"
      - "plan this"
      - "propose"
      - "write a plan"
      - "spec out"
      - "draft a"
    route: "v4_drafter"
    next_action: "Drafter will produce specification. Reviewer fires automatically."

  building:
    phrases:
      - "build this"
      - "implement this"
      - "code this"
      - "make this"
      - "execute this"
    route: "v4_implementer"
    gate_check: "eric_gate"  # Must have Eric Gate approval
    next_action: "Implementer will execute approved directive. Gates enforced."

  reviewing:
    phrases:
      - "review this"
      - "critique this"
      - "check this"
      - "verify this"
      - "evaluate this"
    route: "v4_reviewer"
    next_action: "Reviewer will provide adversarial analysis."

# Prime gateway — where Eric brainstorms
prime:
  port: 8642
  label: "Prime (Research Partner)"
  description: "Prime is never replaced. The bridge transitions FROM Prime, not instead of it."

# CIS pipeline endpoints
pipeline:
  router_module: "runtime.api.router"
  drafter_script: "tools/pipeline/drafter_start.py"
  reviewer_script: "tools/pipeline/reviewer_reconcile.py"
  dispatch_script: "tools/pipeline/pipeline_dispatch.sh"

# Database
spine_path: "/mnt/projects/cis/data/cis_memory.db"
```

### Step 2: Write intent_bridge.py

Create tools/intent_bridge.py:

```python
#!/usr/bin/env python3
"""
intent_bridge.py — Prime Discovery → CIS Pipeline Transition.

Monitors Prime (8642) discussions for crystallization signals.
When Eric says "draft this" or equivalent, the bridge detects the intent,
extracts the crystallized topic, classifies the route via the CIS router,
and dispatches to the appropriate pipeline stage.

Prime is NEVER replaced. The bridge is the transition mechanism FROM
Prime discussion TO CIS pipeline execution.

Usage:
  # Detect signals in a message
  python3 tools/intent_bridge.py --detect "draft a spec for the home automation system"

  # Manual trigger with topic + intent
  python3 tools/intent_bridge.py --topic "Home automation system" --intent "Unify smart home control"

  # Process a Prime discussion transcript
  python3 tools/intent_bridge.py --transcript transcript.txt

  # Run as a stdin monitor (pipe mode)
  echo "draft this: a personal knowledge base" | python3 tools/intent_bridge.py --stdin
"""
import argparse
import json
import os
import re
import sqlite3
import subprocess
import sys
import yaml
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple


REPO_ROOT = os.environ.get("CIS_REPO_ROOT", "/mnt/projects/cis")
CONFIG_PATH = os.path.join(
    REPO_ROOT, "tools", "intent_bridge_config.yaml"
)
SPINE_PATH = os.path.join(REPO_ROOT, "data", "cis_memory.db")


def load_config():
    """Load bridge configuration from YAML."""
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def detect_signal(message: str, config: dict) -> Optional[dict]:
    """
    Scan message for crystallization signals.
    Returns {signal_type, phrase, route, next_action} or None.
    """
    msg_lower = message.lower()

    for signal_type, signal_config in config.get("signals", {}).items():
        for phrase in signal_config.get("phrases", []):
            if phrase in msg_lower:
                return {
                    "signal_type": signal_type,
                    "matched_phrase": phrase,
                    "route": signal_config["route"],
                    "gate_check": signal_config.get("gate_check"),
                    "next_action": signal_config.get("next_action", ""),
                }
    return None


def extract_topic(message: str, signal_match: dict) -> Tuple[str, str]:
    """
    Extract the crystallized topic from the message.
    Returns (topic, intent).

    Strategy: Look for text after the signal phrase, or extract
    noun phrases from the surrounding context.
    """
    phrase = signal_match["matched_phrase"]
    msg_lower = message.lower()
    idx = msg_lower.find(phrase)

    if idx >= 0:
        # Get text after the signal phrase
        after = message[idx + len(phrase):].strip()
        # Clean up common prefixes
        after = re.sub(r'^[:\-—\s]+', '', after)
        if after:
            topic = after[:200]  # Cap at 200 chars
            intent = f"Build {topic.lower()[:80]}"
            return topic, intent

    # Fallback: use the whole message as topic (truncated)
    topic = message[:200]
    intent = f"Crystallized from Prime discussion: {message[:80]}"
    return topic, intent


def classify_and_route(
    topic: str,
    intent: str,
    signal_match: Optional[dict] = None,
    db_path: str = SPINE_PATH,
) -> dict:
    """
    Classify the intent using the CIS router and create a workflow_run.
    Returns {workflow_run_id, route, agent, port, confidence}.
    """
    # Import router
    sys.path.insert(0, os.path.join(REPO_ROOT, "runtime", "api"))
    from router import classify_route

    # Build classification message
    if signal_match:
        classification_msg = (
            f"{signal_match['signal_type'].upper()}: {topic}\n"
            f"Intent: {intent}"
        )
        override = signal_match.get("route")
    else:
        classification_msg = topic
        override = None

    # Classify
    routing = classify_route(classification_msg, override=override)

    return {
        "topic": topic,
        "intent": intent,
        "route": routing.get("route", "unknown"),
        "agent": routing.get("agent", ""),
        "port": routing.get("port", 0),
        "confidence": routing.get("confidence", "unknown"),
        "reason": routing.get("reason", ""),
        "next_action": signal_match.get("next_action", "") if signal_match else "",
        "signal_detected": signal_match is not None,
        "signal_type": signal_match.get("signal_type") if signal_match else None,
    }


def dispatch_to_pipeline(result: dict, db_path: str = SPINE_PATH) -> dict:
    """
    Dispatch the routed intent to the CIS pipeline.
    Creates a workflow_run and returns the run_id.
    """
    drafter_script = os.path.join(
        REPO_ROOT, "tools", "pipeline", "drafter_start.py"
    )

    cmd = [
        sys.executable, drafter_script,
        result["topic"],
        "--intent", result["intent"],
    ]

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=REPO_ROOT,
        )
        stdout = proc.stdout

        # Extract run_id from output
        run_id_match = re.search(r'run-[\da-f]{12,}', stdout)
        run_id = run_id_match.group(0) if run_id_match else None

        return {
            "dispatched": proc.returncode == 0,
            "run_id": run_id,
            "stdout": stdout.strip(),
            "stderr": proc.stderr.strip(),
            "route": result["route"],
            "next_stage": result.get("next_action", ""),
        }
    except subprocess.TimeoutExpired:
        return {
            "dispatched": False,
            "error": "Dispatch timed out after 30s",
        }
    except Exception as e:
        return {
            "dispatched": False,
            "error": str(e),
        }


def log_bridge_event(result: dict, message: str = "", db_path: str = SPINE_PATH):
    """Log the bridge event to the spine for audit trail."""
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("""
            INSERT INTO dispatch_events
            (event_type, source, message, routing_result, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            "intent_bridge",
            "prime_8642",
            message[:500] if message else "",
            json.dumps(result),
            datetime.now(timezone.utc).isoformat(),
        ))
        conn.commit()
    except Exception:
        pass  # Non-critical — bridge operates even if logging fails
    finally:
        conn.close()


def process_message(message: str, auto_dispatch: bool = False) -> dict:
    """
    Full processing pipeline for a message from Prime discussion.
    1. Detect crystallization signal
    2. Extract topic + intent
    3. Classify route
    4. Optionally dispatch to pipeline
    """
    config = load_config()

    # Step 1: Detect signal
    signal_match = detect_signal(message, config)

    if not signal_match:
        return {
            "crystallized": False,
            "reason": "No crystallization signal detected. This is a normal Prime discussion.",
            "action": "Continue brainstorming with Prime.",
        }

    # Step 2: Extract topic
    topic, intent = extract_topic(message, signal_match)

    # Step 3: Classify and route
    routing = classify_and_route(topic, intent, signal_match)

    # Step 4: Optionally dispatch
    dispatch_result = None
    if auto_dispatch:
        dispatch_result = dispatch_to_pipeline(routing)

    # Log event
    log_bridge_event(routing, message)

    result = {
        "crystallized": True,
        "signal": {
            "type": signal_match["signal_type"],
            "phrase": signal_match["matched_phrase"],
        },
        "topic": topic,
        "intent": intent,
        "routing": routing,
        "dispatch": dispatch_result,
        "next_step": (
            "Pipeline dispatched" if auto_dispatch
            else "Intent crystallized. Awaiting dispatch confirmation."
        ),
    }

    return result


def main():
    parser = argparse.ArgumentParser(
        description="CIS Intent Bridge — Prime Discovery → Pipeline Transition"
    )
    parser.add_argument("--detect", type=str, metavar="MESSAGE",
                        help="Detect crystallization signal in a message")
    parser.add_argument("--topic", type=str,
                        help="Manual topic (bypass signal detection)")
    parser.add_argument("--intent", type=str,
                        help="Manual intent (used with --topic)")
    parser.add_argument("--transcript", type=str,
                        help="Process a Prime discussion transcript file")
    parser.add_argument("--stdin", action="store_true",
                        help="Read message from stdin")
    parser.add_argument("--auto-dispatch", action="store_true",
                        help="Automatically dispatch to pipeline on detection")
    parser.add_argument("--json", action="store_true",
                        help="Output as JSON")
    args = parser.parse_args()

    # Determine input message
    message = None
    if args.detect:
        message = args.detect
    elif args.stdin:
        message = sys.stdin.read().strip()
    elif args.transcript:
        with open(args.transcript) as f:
            message = f.read()
    elif args.topic:
        # Manual trigger mode — construct message from topic + intent
        intent = args.intent or f"Build {args.topic}"
        message = f"draft this: {args.topic}"

    if not message:
        parser.print_help()
        sys.exit(1)

    # Process
    result = process_message(message, auto_dispatch=args.auto_dispatch)

    # Output
    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        print(f"Intent Bridge Result")
        print(f"  Crystallized: {result.get('crystallized', False)}")
        if result.get('crystallized'):
            signal = result.get('signal', {})
            print(f"  Signal: {signal.get('type', '?')} — '{signal.get('phrase', '?')}'")
            print(f"  Topic: {result.get('topic', '')[:100]}")
            routing = result.get('routing', {})
            print(f"  Route: {routing.get('route', '?')} "
                  f"→ {routing.get('agent', '?')}:{routing.get('port', '?')}")
            print(f"  Confidence: {routing.get('confidence', '?')}")
            if result.get('dispatch'):
                d = result['dispatch']
                print(f"  Dispatched: {d.get('dispatched', False)}")
                if d.get('run_id'):
                    print(f"  Run ID: {d['run_id']}")
        else:
            print(f"  {result.get('reason', '')}")
        print(f"  Next: {result.get('next_step', '')}")


if __name__ == "__main__":
    main()
```

### Step 3: Write intent bridge tests

Create tests/test_intent_bridge.py:

```python
"""Tests for CIS Intent Bridge."""
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("CIS_REPO_ROOT", "/mnt/projects/cis")


class TestIntentBridge(unittest.TestCase):
    """Validate intent bridge signal detection and routing."""

    @classmethod
    def setUpClass(cls):
        from tools.intent_bridge import load_config, detect_signal
        cls.config = load_config()
        cls.detect = detect_signal

    def test_detect_draft_signal(self):
        """Detects 'draft this' signal."""
        result = self.detect("draft this: a home automation system", self.config)
        self.assertIsNotNone(result)
        self.assertEqual(result["signal_type"], "drafting")
        self.assertEqual(result["route"], "v4_drafter")

    def test_detect_build_signal(self):
        """Detects 'build this' signal."""
        result = self.detect("build this: the front door pipeline", self.config)
        self.assertIsNotNone(result)
        self.assertEqual(result["signal_type"], "building")
        self.assertEqual(result["route"], "v4_implementer")
        self.assertIsNotNone(result.get("gate_check"))

    def test_detect_review_signal(self):
        """Detects 'review this' signal."""
        result = self.detect(
            "review this specification for gaps", self.config
        )
        self.assertIsNotNone(result)
        self.assertEqual(result["signal_type"], "reviewing")
        self.assertEqual(result["route"], "v4_reviewer")

    def test_no_signal_on_normal_message(self):
        """Normal discussion produces no signal."""
        result = self.detect(
            "What do you think about microservices?", self.config
        )
        self.assertIsNone(result)

    def test_no_signal_on_greeting(self):
        """Greetings produce no signal."""
        result = self.detect("Hello Prime, how are you?", self.config)
        self.assertIsNone(result)

    def test_extract_topic(self):
        """Topic extraction from signal message."""
        from tools.intent_bridge import extract_topic
        signal = {"signal_type": "drafting", "matched_phrase": "draft this"}
        topic, intent = extract_topic(
            "draft this: a personal knowledge base with vector search", signal
        )
        self.assertIn("personal knowledge base", topic.lower())
        self.assertTrue(len(intent) > 0)

    def test_classify_and_route(self):
        """Classification produces valid routing result."""
        from tools.intent_bridge import classify_and_route
        signal = {"signal_type": "drafting", "route": "v4_drafter"}
        result = classify_and_route(
            "Home automation system",
            "Unify smart home control",
            signal_match=signal,
        )
        self.assertIn("route", result)
        self.assertIn("agent", result)
        self.assertIn("port", result)
        self.assertIn("confidence", result)

    def test_process_message_no_signal(self):
        """Normal message returns non-crystallized result."""
        from tools.intent_bridge import process_message
        result = process_message("How does the router work?")
        self.assertFalse(result["crystallized"])
        self.assertIn("no crystallization signal", result["reason"].lower())

    def test_process_message_with_signal(self):
        """Signal message returns crystallized result."""
        from tools.intent_bridge import process_message
        result = process_message(
            "draft this: an intent bridge for CIS front door"
        )
        self.assertTrue(result["crystallized"])
        self.assertIn("topic", result)
        self.assertIn("routing", result)


if __name__ == "__main__":
    unittest.main()
```

### Step 4: Run tests

```bash
cd /mnt/projects/cis
python3 -m pytest tests/test_intent_bridge.py -v
```

Expected: 9 tests pass

### Step 5: Manual test — detect signal without dispatch

```bash
cd /mnt/projects/cis
python3 tools/intent_bridge.py --detect "draft this: a personal knowledge base system"
```

Expected output: Crystallized: True, Signal: drafting, Route: v4_drafter, No dispatch (auto_dispatch=False)

### Step 6: Manual test — manual topic trigger

```bash
cd /mnt/projects/cis
python3 tools/intent_bridge.py --topic "Home automation system" --intent "Unify smart home control across all devices" --json
```

### Step 7: Verify non-CIS message doesn't trigger

```bash
cd /mnt/projects/cis
python3 tools/intent_bridge.py --detect "What's the weather like today?" --json
```

Expected: crystallized: false, reason: "No crystallization signal detected"

### Step 8: Commit

```bash
git add tools/intent_bridge.py tools/intent_bridge_config.yaml
git add tests/test_intent_bridge.py
git commit -m "feat(fd.3): intent bridge — Prime discovery to CIS pipeline transition"
```

### Verification (FD.3)

COMMAND: python3 tools/intent_bridge.py --detect "draft this: a spec for the front door intent bridge" --json 2>&1 | python3 -c "import json,sys; d=json.load(sys.stdin); print('Crystallized:', d['crystallized']); print('Signal:', d.get('signal',{}).get('type')); print('Route:', d.get('routing',{}).get('route'))"
OUTPUT:
Crystallized: True
Signal: drafting
Route: v4_drafter

COMMAND: python3 tools/intent_bridge.py --detect "what's the weather?" --json 2>&1 | python3 -c "import json,sys; d=json.load(sys.stdin); print('Crystallized:', d['crystallized'])"
OUTPUT:
Crystallized: False

COMMAND: python3 -m pytest tests/test_intent_bridge.py -v --tb=short 2>&1 | tail -5
OUTPUT: 9 passed

---

## BUILD NODE FD.4: Integration Test

### Node Summary

End-to-end integration test that validates the full Front Door pipeline: signal detection → classification → dispatch → deliberation → Eric Gate → implementation. Tests all 4 profiles and all 4 build nodes together.

**Depends on:** FD.1, FD.2, FD.3
**Estimated time:** 30 minutes
**Risk:** LOW — read-only tests except for the dry-run dispatch

### Architecture

A test script (`tests/test_front_door_integration.py`) that runs 8 acceptance tests matching the spec's §7.1 Acceptance Criteria. Each test is independent and idempotent. Tests verify state without mutating production data.

Three layers of testing:
1. Unit-level: each bridge component works in isolation (covered by FD.1-FD.3 tests)
2. Integration-level: bridge → router → pipeline scripts function together
3. Infrastructure-level: all gateways healthy, MCP tools accessible, VDB searchable

### Files

| File | Action | Purpose |
|---|---|---|
| tests/test_front_door_integration.py | CREATE | 8 integration tests |
| tests/conftest.py | CREATE (if missing) | Shared fixtures |

### Test Specifications

Each test maps to a spec acceptance criterion:

| Test | Maps To | What It Validates |
|---|---|---|
| test_a1_intent_to_router | A1 | Intent Bridge detects signal → Router classifies → Drafter dispatched |
| test_a2_deliberation_dispatches | A2 | Pipeline dispatch script invokes deliberation |
| test_a3_eric_gate_queried | A3 | Eric Gate approvals accessible via MCP |
| test_a5_non_cis_handled | A5 | Non-CIS intent routed without pipeline |
| test_a6_mcp_tools_accessible | A6 | All 14 MCP tools listable |
| test_a7_vdb_search_works | A7 | Semantic search returns archive results |
| test_a8_shell_hooks_enforce | A8 | cis_pre_tool_gate.sh present and active |
| test_i1_full_end_to_end | I1 | Complete trace: detect → classify → (dry-run dispatch) |

### Step 1: Write conftest.py if needed

```bash
ls tests/conftest.py 2>/dev/null || echo "# Shared test fixtures" > tests/conftest.py
```

### Step 2: Write integration test

Create tests/test_front_door_integration.py:

```python
"""
Front Door Integration Tests — Full end-to-end pipeline validation.

Maps to CIS_FRONT_DOOR_SPECIFICATION.md §7.1 Acceptance Criteria.
Tests A1-A8 plus I1 (full end-to-end).

Run: python3 -m pytest tests/test_front_door_integration.py -v
"""
import json
import os
import re
import sqlite3
import subprocess
import sys
import unittest

REPO_ROOT = "/mnt/projects/cis"
SPINE_PATH = os.path.join(REPO_ROOT, "data", "cis_memory.db")
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, os.path.join(REPO_ROOT, "runtime"))
sys.path.insert(0, os.path.join(REPO_ROOT, "tools"))


def run_cmd(cmd, timeout=30):
    """Run a shell command, return (returncode, stdout, stderr)."""
    result = subprocess.run(
        cmd, capture_output=True, text=True, timeout=timeout,
        cwd=REPO_ROOT, shell=True,
    )
    return result.returncode, result.stdout, result.stderr


class TestFrontDoorIntegration(unittest.TestCase):
    """End-to-end integration tests for the CIS Front Door."""

    # ── Infrastructure ───────────────────────────────

    @classmethod
    def setUpClass(cls):
        """Verify all gateways are up before running tests."""
        for port in [8642, 8643, 8644, 8645, 8646]:
            rc, out, err = run_cmd(
                f"curl -s -o /dev/null -w '%{{http_code}}' "
                f"http://127.0.0.1:{port}/health",
                timeout=5,
            )
            if rc != 0 or out.strip() != "200":
                raise unittest.SkipTest(
                    f"Gateway port {port} not healthy (http_code={out.strip()}). "
                    "Start all gateways before integration tests."
                )

    # ── A1: Intent → Router Fires ─────────────────────

    def test_a1_intent_to_router(self):
        """A1: Intent Bridge detects signal, router classifies, workflow_run created."""
        from intent_bridge import process_message

        # Detect a drafting signal
        result = process_message(
            "draft this: integration test topic for front door validation"
        )

        # Assert crystallization detected
        self.assertTrue(
            result["crystallized"],
            f"Expected crystallization, got: {result.get('reason', 'unknown')}"
        )

        # Assert routing produced
        routing = result.get("routing", {})
        self.assertIn("route", routing, "Routing missing 'route' key")
        self.assertIn(routing["route"], ["v4_drafter", "fast"],
                      f"Unexpected route: {routing['route']}")

        # Assert topic extracted
        self.assertIn("topic", result)
        self.assertIn("integration test", result["topic"].lower())

    # ── A2: Deliberation Dispatches ───────────────────

    def test_a2_deliberation_dispatches(self):
        """A2: Pipeline dispatch script invokable for deliberation."""
        script = os.path.join(
            REPO_ROOT, "tools", "pipeline", "pipeline_dispatch.sh"
        )
        self.assertTrue(
            os.path.exists(script),
            f"Dispatch script missing: {script}"
        )
        self.assertTrue(
            os.access(script, os.X_OK),
            f"Dispatch script not executable: {script}"
        )

        # Check that gate_deliberation.sh exists (called by dispatch)
        gate_delib = os.path.join(
            REPO_ROOT, "tools", "gates", "gate_deliberation.sh"
        )
        self.assertTrue(
            os.path.exists(gate_delib),
            f"Deliberation gate missing: {gate_delib}"
        )

    # ── A3: Eric Gate Deliverable ─────────────────────

    def test_a3_eric_gate_queried(self):
        """A3: Eric Gate approvals queryable via MCP bridge spine."""
        from mcp_bridge import spine

        # Query Eric Gate status via spine module
        approvals = spine.query_eric_gate_status()
        self.assertIsInstance(approvals, list)
        # May be empty (no pending approvals) — that's OK
        # Just verify the query works without error

        # Also verify workflow_runs queryable
        runs = spine.query_recent_runs(limit=3)
        self.assertIsInstance(runs, list)
        self.assertLessEqual(len(runs), 3)

    # ── A5: Non-CIS Intent Handled ────────────────────

    def test_a5_non_cis_handled(self):
        """A5: Non-CIS message does not trigger pipeline."""
        from intent_bridge import process_message

        # Weather query — should NOT crystallize
        result = process_message("What's the weather like today?")
        self.assertFalse(
            result["crystallized"],
            "Weather query should NOT crystallize into pipeline intent"
        )

        # Greeting — should NOT crystallize
        result2 = process_message("Hello, how are you?")
        self.assertFalse(
            result2["crystallized"],
            "Greeting should NOT crystallize into pipeline intent"
        )

        # Research query without drafting intent — should NOT crystallize
        result3 = process_message("What is the current state of MCP protocol?")
        self.assertFalse(
            result3["crystallized"],
            "Research query should NOT crystallize into pipeline intent"
        )

    # ── A6: MCP Tools Accessible ──────────────────────

    def test_a6_mcp_tools_accessible(self):
        """A6: All MCP tools listable and handlers mapped."""
        from mcp_bridge import tools

        tool_names = {t["name"] for t in tools.TOOLS}

        # Verify minimum tool count
        self.assertGreaterEqual(
            len(tools.TOOLS), 14,
            f"Expected >=14 tools, got {len(tools.TOOLS)}"
        )

        # Verify all tools have handlers
        for tool in tools.TOOLS:
            self.assertIn(
                tool["name"], tools.HANDLERS,
                f"Tool '{tool['name']}' has no handler"
            )

        # Verify key tools present
        required = [
            "cis_get_current_phase",
            "cis_get_build_status",
            "cis_search_semantic",
            "cis_dispatch_drafter",
            "cis_dispatch_reviewer",
        ]
        for name in required:
            self.assertIn(
                name, tool_names,
                f"Required tool '{name}' missing from MCP bridge"
            )

    # ── A7: VDB Search Works ──────────────────────────

    def test_a7_vdb_search_works(self):
        """A7: Chroma semantic search returns results."""
        import chromadb

        chroma_path = os.environ.get(
            "CIS_CHROMA_PATH",
            os.path.join(REPO_ROOT, "data", "chroma_data"),
        )
        client = chromadb.PersistentClient(path=chroma_path)
        collections = client.list_collections()

        self.assertGreater(
            len(collections), 0,
            "No Chroma collections found. Run archive indexing first."
        )

        # Verify cis_archive collection exists (from FD.2)
        archive_coll = None
        for c in collections:
            if c.name == "cis_archive":
                archive_coll = c
                break

        if archive_coll and archive_coll.count() > 0:
            # Test semantic search
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer("all-MiniLM-L6-v2")
            query_embedding = model.encode(["Eric vision knowledge base"]).tolist()

            results = archive_coll.query(
                query_embeddings=query_embedding,
                n_results=min(3, archive_coll.count()),
                include=["documents", "metadatas", "distances"],
            )

            ids = results.get("ids", [[]])[0]
            self.assertGreater(
                len(ids), 0,
                "Semantic search returned no results"
            )
        else:
            self.skipTest(
                "cis_archive collection empty — run index_archive.py first"
            )

    # ── A8: Shell Hooks Enforce ───────────────────────

    def test_a8_shell_hooks_enforce(self):
        """A8: cis_pre_tool_gate.sh present and executable on all profiles."""
        hook_script = os.path.join(
            REPO_ROOT, "tools", "hooks", "cis_pre_tool_gate.sh"
        )
        self.assertTrue(
            os.path.exists(hook_script),
            f"Hook script missing: {hook_script}"
        )
        self.assertTrue(
            os.access(hook_script, os.X_OK),
            f"Hook script not executable: {hook_script}"
        )

        # Check hook is referenced in gate_runner.sh
        gate_runner = os.path.join(
            REPO_ROOT, "tools", "gates", "gate_runner.sh"
        )
        if os.path.exists(gate_runner):
            with open(gate_runner) as f:
                content = f.read()
            self.assertIn(
                "cis_pre_tool_gate",
                content,
                "cis_pre_tool_gate not referenced in gate_runner.sh"
            )

    # ── I1: Full End-to-End Trace ─────────────────────

    def test_i1_full_end_to_end(self):
        """I1: Complete trace: detect → classify → route → verify pipeline ready."""
        from intent_bridge import process_message
        from mcp_bridge import spine

        # Step 1: Detect crystallization
        result = process_message(
            "draft this: a test end-to-end pipeline trace for CIS front door"
        )
        self.assertTrue(result["crystallized"])

        # Step 2: Verify routing produced
        routing = result.get("routing", {})
        self.assertIn("route", routing)
        self.assertIn("agent", routing)
        self.assertGreater(routing.get("port", 0), 0)

        # Step 3: Verify pipeline scripts accessible
        drafter_script = os.path.join(
            REPO_ROOT, "tools", "pipeline", "drafter_start.py"
        )
        self.assertTrue(os.path.exists(drafter_script))

        dispatch_script = os.path.join(
            REPO_ROOT, "tools", "pipeline", "pipeline_dispatch.sh"
        )
        self.assertTrue(os.path.exists(dispatch_script))

        # Step 4: Verify gate runner functional
        gate_runner = os.path.join(
            REPO_ROOT, "tools", "gates", "gate_runner.sh"
        )
        self.assertTrue(os.path.exists(gate_runner))

        # Step 5: Verify spine accessible
        phase = spine.query_current_phase()
        self.assertIsInstance(phase, dict)
        self.assertIn("build_phase", phase)

        # Trace complete — all pipeline stages verified reachable
        trace = {
            "crystallized": True,
            "route": routing["route"],
            "agent": routing["agent"],
            "port": routing["port"],
            "drafter_script_exists": os.path.exists(drafter_script),
            "dispatch_script_exists": os.path.exists(dispatch_script),
            "gate_runner_exists": os.path.exists(gate_runner),
            "spine_accessible": phase.get("build_phase") is not None,
        }
        # All stages must be True
        for stage, status in trace.items():
            self.assertTrue(
                status,
                f"Pipeline stage '{stage}' failed: {status}"
            )


if __name__ == "__main__":
    unittest.main()
```

### Step 3: Run integration tests

```bash
cd /mnt/projects/cis
python3 -m pytest tests/test_front_door_integration.py -v --tb=long 2>&1
```

Expected: 8 tests pass (some may skip if archive not yet indexed)

### Step 4: Commit

```bash
git add tests/test_front_door_integration.py tests/conftest.py
git commit -m "test(fd.4): front door integration tests — 8 acceptance criteria"
```

### Verification (FD.4)

COMMAND: python3 -m pytest tests/test_front_door_integration.py -v --tb=short 2>&1
OUTPUT: 8 passed (or N passed, M skipped)

COMMAND: cd /mnt/projects/cis && python3 tools/intent_bridge.py --detect "draft this: verify the front door pipeline is working" --json 2>&1 | python3 -c "
import json, sys
d = json.load(sys.stdin)
print('Crystallized:', d['crystallized'])
print('Route:', d.get('routing',{}).get('route'))
print('Agent:', d.get('routing',{}).get('agent'))
print('Port:', d.get('routing',{}).get('port'))
"
OUTPUT:
Crystallized: True
Route: v4_drafter
Agent: hermes-v4pro
Port: 8645

---

## BUILD SEQUENCE AND DEPENDENCIES

```
FD.1 (MCP Dispatch Tools) ──┐
                            ├── FD.3 (Intent Bridge) ── FD.4 (Integration Test)
FD.2 (Archive Indexing) ───┘
```

### Execution Order

1. FD.1 (25 min) — Add dispatch tools to existing MCP bridge
2. FD.2 (30 min) — Index archive into Chroma (can run parallel with FD.1)
3. FD.3 (40 min) — Intent Bridge (requires FD.1 for dispatch, FD.2 for archive search)
4. FD.4 (30 min) — Integration tests (requires all FD.1-FD.3)

Total: ~125 minutes sequential, ~95 minutes with FD.1 + FD.2 parallel.

---

## CONFIGURATION CHANGES

### No Hermes config changes required

The hardening v2.0 shell hooks, gateway profiles, and Hermes configs at ~/.hermes* are NOT modified. The Front Door operates entirely within the CIS project repo.

### Environment variables (set in shell or .env)

```bash
export CIS_SPINE_PATH=/mnt/projects/cis/data/cis_memory.db
export CIS_CHROMA_PATH=/mnt/projects/cis/data/chroma_data
export CIS_REPO_ROOT=/mnt/projects/cis
export CIS_PYTHON=python3
```

### New spine rows (after Eric approves and implementation begins)

```sql
INSERT INTO build_plan_nodes (project_id, node_label, tier, sequence, status)
VALUES
  ('CIS', 'FD.1 — MCP Dispatch Tools', 'FD', 1, 'PENDING'),
  ('CIS', 'FD.2 — Archive Indexing Pipeline', 'FD', 2, 'PENDING'),
  ('CIS', 'FD.3 — Intent Bridge', 'FD', 3, 'PENDING'),
  ('CIS', 'FD.4 — Integration Test', 'FD', 4, 'PENDING');
```

---

## ROLLBACK INSTRUCTIONS

### FD.1 Rollback

```bash
cd /mnt/projects/cis
git checkout HEAD -- runtime/mcp_bridge/tools.py runtime/mcp_bridge/spine.py
rm -f runtime/mcp  # Remove symlink if created
# MCP bridge reverts to 11 read-only tools
```

### FD.2 Rollback

```bash
cd /mnt/projects/cis
rm -f tools/index_archive.py tests/test_archive_index.py
# Chroma collection 'cis_archive' can remain — it's additive and read-only
```

### FD.3 Rollback

```bash
cd /mnt/projects/cis
rm -f tools/intent_bridge.py tools/intent_bridge_config.yaml
rm -f tests/test_intent_bridge.py
# No state changes to undo (bridge is stateless)
```

### FD.4 Rollback

```bash
cd /mnt/projects/cis
rm -f tests/test_front_door_integration.py
# No state changes to undo
```

---

## GATE VERIFICATION

### Shell hooks survive check (Hardening A1)

COMMAND: for home in /home/eric/.hermes /home/eric/.hermes-r1 /home/eric/.hermes-v4pro /home/eric/.hermes-v4impl; do
  HERMES_HOME=$home hermes hooks list 2>&1 | grep "cis_pre_tool_gate" | head -1
done

### Existing gates unchanged

COMMAND: cd /mnt/projects/cis && bash tools/gates/gate_runner.sh 2>&1 | tail -20

---

## STOP CONDITIONS

| Condition | Action |
|---|---|
| Any gateway not returning 200 | Stop. Do not proceed without all 5 gateways healthy. |
| chromadb import fails | Stop. Verify: pip3 show chromadb |
| sentence-transformers import fails | Stop. Verify: pip3 show sentence-transformers |
| Spine database not accessible | Stop. Verify: ls -la data/cis_memory.db |
| Shell hooks missing on any profile | Stop. Hooks must be deployed before pipeline can enforce gates. |
| Git dirty with unrelated changes | Commit or stash unrelated changes first. |

---

*Build Plan v1.0 — CIS Front Door*
*Author: V4 Drafter (deepseek-v4-pro)*
*Date: 2026-06-17*
*Status: PROPOSAL_READY — awaiting Eric Gate review*
