# Model-Agnostic Naming Convention

**Established:** 2026-07-07 by Eric's directive
**Principle:** Role names describe function, not provider. Models change; roles don't.

## Canonical Role Labels

| Label | Role Key | Port | Function | Current Model (config detail, not identity) |
|---|---|---|---|---|
| Brain | `brain` | 8644 | Lateral exploration, assumption-challenging | DeepSeek V4 Pro |
| Draft | `draft` | 8645 | Proposals, designs, plans | DeepSeek V4 Pro |
| Review1 | `review1` | 8643 | First independent reviewer | Qwen 3.7 Max |
| Review2 | `review2` | 8647 | Second independent reviewer | GLM 5.2 |
| Menter | `menter` | 8646 | Code execution, builds | DeepSeek V4 Pro |
| Verify | `verify` | 8648 | Evidence verification gate | GLM 5.2 |

## Where Role Names Must Be Used

1. **`agents_static.yaml`** — `label:` field (source of truth for display names)
2. **`dispatch.py`** — PROFILES dict keys, descriptions, ROLE_ALIASES
3. **`router.py`** — ROUTER_AGENT_MAP keys, ROUTER_NEXT_ACTION strings
4. **`advisor.py`** — system prompts, variable names, error messages, user-facing strings
5. **`adapter.py`** — ROUTE_TO_ROLE mapping, next-action strings
6. **Enforcement profile configs** — `display.personality` briefing text ("You are Brain...", not "You are CIS Brainstorm...")
7. **AGENTS.md** — gateway table (auto-generated from agents_static.yaml)

## Where Model Names Are Allowed

- `agents_static.yaml` — `model:` and `provider:` fields (these are config details)
- Enforcement profile configs — `model.default:`, `model.provider:` (these are how the gateway knows which API to call)
- `advisor.py` — the `model` field in gateway API payloads (the gateway needs to know which model to invoke)
- API response payloads — health checks may include the model for informational purposes

## Legacy Alias Support

`dispatch.py` ROLE_ALIASES maps old names to new keys for backward compatibility:

```
"drafter" → "draft"
"brainstorm" → "brain"
"implementer" → "menter"
"verifier" → "verify"
"reviewer" → "review1"
"v4_drafter" → "draft"
"v4_reviewer" → "review1"
"v4_implementer" → "menter"
"qwen" → "review1"
"glm_reviewer" → "review2"
... etc
```

Legacy route keys in `router.py` ROUTER_AGENT_MAP (`v4_drafter`, `v4_reviewer`, `fast`) are kept as aliases pointing to the same ports. New code should use the canonical keys.

## Refactor Procedure (When Adding/Changing Roles)

1. Update `agents_static.yaml` — change `label:` field
2. Update `dispatch.py` — PROFILES dict (add/rename role key, update description, add to ROLE_ALIASES)
3. Update `router.py` — ROUTER_AGENT_MAP and ROUTER_NEXT_ACTION
4. Update `adapter.py` — ROUTE_TO_ROLE and user-facing strings
5. Update `advisor.py` — system prompts, variable names, comments, error messages
6. Update enforcement profile configs — briefing text in `display.personality`
7. Update `collab_rounds.py` — any DB insert that writes a role name
8. Regenerate AGENTS.md: `python3 tools/export/generate_agents_md.py`
9. Verify: `grep -rn '<old-name>' runtime/` should return nothing
10. Verify: all Python files compile: `python3 -c "import py_compile; ..."`
11. Verify: all gateways still respond on their ports

## Pitfalls

- **Do NOT rename directory paths** (`~/.hermes-brainstorm`, `~/.hermes-r1`, etc.). These are filesystem locations referenced by systemd units, scripts, and HERMES_HOME env vars. The directory name is NOT the role name.
- **Do NOT remove legacy aliases** from ROLE_ALIASES. Existing sessions, database rows, and user muscle memory reference old names. Aliases are cheap; breakage is expensive.
- **When using `execute_code` for batch replacements**, read the file with `subprocess.run(['cat', path])`, NOT `hermes_tools.read_file()` — the latter returns line-numbered content that corrupts files when written back.
