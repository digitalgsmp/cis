# CIS Profile Map and Orientation Reference

**Last verified:** 2026-07-07 (post-rename)
**Verified by:** Verify (port 8648)

## 1. Pipeline Team Composition (Intended Design)

Eric's intended pipeline architecture: **DeepSeek V4 Pro × 3** counterbalanced by **dual independent reviewers** with different training data.

Role names are **model-agnostic** — they describe function, not provider. Models can be swapped without changing code.

| Role Label | Role Key | Model | Profile Dir | Port | Function |
|---|---|---|---|---|---|
| Brain | `brain` | DeepSeek V4 Pro | `~/.hermes-brainstorm` | 8644 | Lateral exploration before Draft narrows |
| Draft | `draft` | DeepSeek V4 Pro | `~/.hermes-v4pro` | 8645 | Proposals based on Eric's verbatim intentions |
| Menter | `menter` | DeepSeek V4 Pro | `~/.hermes-v4impl` | 8646 | Constrained worker — builds exactly what spec says |
| Review1 | `review1` | Qwen 3.7 Max | `~/.hermes-r1` | 8643 | Independent reviewer, first pass |
| Review2 | `review2` | GLM 5.2 | `~/.hermes-glm-reviewer` | 8647 | Independent reviewer, second pass |
| Verify | `verify` | GLM 5.2 | `~/.hermes-glm-verifier` | 8648 | Evidence-based verification per ADR-SEED-002 |

**Key insight:** Review1 and Review2 counterbalance the DeepSeek trio (Brain, Draft, Menter). Different training data, different blind spots. Models may change behind any role — the role label stays fixed.

**Legacy names still work as aliases** in `dispatch.py` ROLE_ALIASES: `drafter`→`draft`, `reviewer`→`review1`, `implementer`→`menter`, `brainstorm`→`brain`, `verifier`→`verify`, etc.

## 2. Profile Map

Discovered via `ls -d /home/eric/.hermes*/` and config inspection.

| Profile Dir | Role Label | Port | Model | Status |
|---|---|---|---|---|
| `~/.hermes` | Default/Prime (legacy) | 8642 | deepseek-v4-pro (medium) | DOWN — irrelevant per Eric |
| `~/.hermes-brainstorm` | Brain | 8644 | deepseek-v4-pro (xhigh) | UP |
| `~/.hermes-r1` | Review1 | 8643 | qwen/qwen3.7-max (openrouter) | UP |
| `~/.hermes-v4pro` | Draft | 8645 | deepseek-v4-pro (xhigh) | UP |
| `~/.hermes-v4impl` | Menter | 8646 | deepseek-v4-pro (xhigh) | UP |
| `~/.hermes-glm-reviewer` | Review2 | 8647 | z-ai/glm-5.2 | UP |
| `~/.hermes-glm-verifier` | Verify | 8648 | z-ai/glm-5.2 | UP |
| `~/.hermes-qwen` | Old Qwen (paused) | 8650 | qwen3-vl-30b (local) | DOWN — legacy |

### Notes
- `agents_static.yaml` in the CIS repo (`/mnt/projects/cis/config/`) is the authoritative source for the pipeline team mapping — labels updated 2026-07-07 to model-agnostic names.
- Directory names (`~/.hermes-brainstorm`, `~/.hermes-r1`, etc.) are filesystem paths, NOT identity. They stay as-is to avoid breaking systemd units and scripts. The **display label** is what matters.
- Port check: `ss -tlnp | grep -E "864[0-9]"`
- Brainstorm profile shares V4 Pro's hermes-agent install via symlink: `~/.hermes-brainstorm/hermes-agent -> ~/.hermes-v4pro/hermes-agent/`

## 3. Orientation Checklist (READ_ONLY_STANDING_BY)

Per AGENTS.md §11.5, every fresh session start requires inspection-only orientation before any execution.

### Required Commands

```bash
# 1. Git state
cd /mnt/projects/cis && git rev-parse --short HEAD && git status --short | head -20

# 2. Confirm own identity
echo "Profile: $HERMES_HOME"
```

### MCP Knowledge Base Queries (read-only)

- `cis_get_current_phase` — build phase, in-progress nodes, pending nodes, next action
- `cis_get_eric_gate_status` — pending Eric Gate approvals
- `cis_get_next_actions` — all PENDING build_plan_nodes ordered by sequence

### Rules
- Inspection-only commands allowed: `git status`, `git rev-parse`, `grep`, `sed`, `cat`, `sqlite3 SELECT`, file listing
- Must NOT: modify files, run imports, apply migrations, patch code, alter databases, stage files, commit, or start implementation
- Exit READ_ONLY_STANDING_BY only after Eric gives explicit execution instruction (PROCEED, IMPLEMENT, FINAL_DIRECTIVE)
- Required response ends with "Standing by"

## 4. Gateway Restart Procedure

When gateways are down and need to be brought back online:

1. Check which ports are up: `for port in 8643 8644 8645 8646 8647 8648; do echo -n "Port $port: "; ss -tlnp | grep -q ":$port " && echo "UP" || echo "DOWN"; done`
2. For each down gateway, start it with its HERMES_HOME:
   ```bash
   HERMES_HOME=/home/eric/.hermes-r1 /home/eric/.hermes-r1/hermes-agent/.venv/bin/python -m hermes_cli.main gateway run
   ```
   Use `terminal(background=true)` — NOT shell-level `&` or `disown`.
3. Re-check ports after 5 seconds.
4. Do NOT over-explain the diagnosis. Check ports, start what's down, report the result.

### Venv paths by profile
| Profile Dir | Venv |
|---|---|
| `~/.hermes-brainstorm` | `.hermes-brainstorm/hermes-agent/.venv/bin/python` |
| `~/.hermes-v4pro` | `.hermes-v4pro/hermes-agent/.venv/bin/python` |
| `~/.hermes-r1` | `.hermes-r1/hermes-agent/.venv/bin/python` |
| `~/.hermes-v4impl` | `.hermes-v4impl/hermes-agent/.venv/bin/python` |
| `~/.hermes-glm-reviewer` | `.hermes-glm-reviewer/hermes-agent/.venv/bin/python` |
| `~/.hermes-glm-verifier` | `.hermes-glm-verifier/hermes-agent/.venv/bin/python` |

## 5. Documentation Reconciliation Procedure

When runtime reality and `agents_static.yaml` / AGENTS.md drift apart, run this procedure to sync them.

### Step 1: Audit All Profiles

```bash
for p in /home/eric/.hermes /home/eric/.hermes-brainstorm /home/eric/.hermes-v4pro /home/eric/.hermes-r1 /home/eric/.hermes-v4impl /home/eric/.hermes-glm-reviewer /home/eric/.hermes-glm-verifier /home/eric/.hermes-qwen; do
  name=$(basename $p)
  echo "=== $name ==="
  echo "Port: $(grep '^  port:' $p/config.yaml 2>/dev/null | head -1 | awk '{print $2}')"
  echo "Model: $(grep '^  default:' $p/config.yaml 2>/dev/null | head -1 | awk '{print $2}')"
  echo "Provider: $(grep '^  provider:' $p/config.yaml 2>/dev/null | head -1 | awk '{print $2}')"
  echo "Reasoning: $(grep 'reasoning_effort:' $p/config.yaml 2>/dev/null | head -1 | awk '{print $2}')"
  echo
done
```

### Step 2: Compare Against agents_static.yaml

```bash
cd /mnt/projects/cis && python3 -c "
import yaml
with open('config/agents_static.yaml') as f:
    c = yaml.safe_load(f)
for gw in c.get('gateways', []):
    print(f\"{gw['label']:20s} | {gw['profile']:25s} | {gw['port']:5s} | {gw['model']:30s} | {gw['provider']:10s} | {gw['status']}\")
"
```

### Step 3: Update agents_static.yaml and regenerate AGENTS.md

Edit `config/agents_static.yaml`, then:
```bash
cd /mnt/projects/cis && python3 tools/export/generate_agents_md.py
```

### Note: AGENTS.md §13 (Session Handoff) is spine-driven

AGENTS.md §13 is NOT manually written. It is auto-generated from the `session_handoffs` table in the spine (migration 0014). Draft built this to eliminate manual handoff drift.

- To update §13: write a row to `session_handoffs` table in `data/cis_memory.db`
- The generator reads the latest row (`is_current=1`) and includes it in AGENTS.md
- Pre-commit hook auto-regenerates AGENTS.md on commit
- Do NOT manually edit AGENTS.md §13 — it will be overwritten on next commit

**Eric correction (2026-07-07):** When told about stale AGENTS.md names, do NOT offer to regenerate it as a manual step. The pre-commit hook handles it. The spine table is authoritative.

## 6. Cross-Profile Session Access

### How It Works

The `session_search` tool has a `profile` parameter. When provided, it opens the target profile's `state.db` in **read-only mode** (`mode=ro`).

### Key Finding: state.db vs sessions.db

- **`state.db`** — contains the `messages` and `sessions` tables with FTS5 index. This is where session data lives.
- **`sessions.db`** — exists in every profile dir but is **empty** (no tables). Do not query it.

### Cross-Profile FTS5 Gap

`session_search(profile="hermes-v4pro", query="...")` may return 0 results even though the profile has 10K+ messages. Workarounds:
1. **Browse mode works cross-profile** — `session_search(profile="hermes-v4pro")` with no query returns recent sessions.
2. **Raw file access** — JSON/JSONL files in `~/.hermes-*/sessions/` are readable via terminal.
3. **Direct SQLite query** — `sqlite3 ~/.hermes-v4pro/state.db "SELECT ..."` works from terminal.
