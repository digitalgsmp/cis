# Environment Manifest — CIS Gateway Profiles
# Generated: 2026-06-06
# Purpose: Recoverable record of required env vars per gateway profile.
#          No secret values. Secrets marked <REQUIRED_SECRET_NOT_TRACKED>.
#          Reconstruct .env files from this manifest + the secret store.

## Shared (all five profiles)
| Variable | Value |
|----------|-------|
| HERMES_CIS_BRIEFING_PATH | /mnt/projects/cis/session_handoffs/CURRENT_CONTEXT_BRIEFING.md |

## Kanban Coordination (all five profiles)
| Variable | Value |
|----------|-------|
| HERMES_KANBAN_DB | /mnt/projects/cis/data/kanban.db |
| HERMES_KANBAN_HOME | /mnt/projects/cis/data |

---

### ~/.hermes/.env — Prime / Flash / Research (port 8642)
| Variable | Value |
|----------|-------|
| API_SERVER_KEY | <REQUIRED_SECRET_NOT_TRACKED> |
| DEEPSEEK_API_KEY | <REQUIRED_SECRET_NOT_TRACKED> |
| TELEGRAM_BOT_TOKEN | <REQUIRED_SECRET_NOT_TRACKED> |
| BROWSERBASE_ADVANCED_STEALTH | <REQUIRED_SECRET_NOT_TRACKED> |
| BROWSERBASE_PROXIES | <REQUIRED_SECRET_NOT_TRACKED> |
| HERMES_CIS_BRIEFING_PATH | /mnt/projects/cis/session_handoffs/CURRENT_CONTEXT_BRIEFING.md |
| HERMES_KANBAN_DB | /mnt/projects/cis/data/kanban.db |
| HERMES_KANBAN_HOME | /mnt/projects/cis/data |
| TERMINAL_TIMEOUT | 60 |
| TERMINAL_LIFETIME_SECONDS | 300 |
| TERMINAL_MODAL_IMAGE | nikolaik/python-nodejs:python3.11-nodejs20 |
| BROWSER_SESSION_TIMEOUT | 300 |
| BROWSER_INACTIVITY_TIMEOUT | 120 |
| WEB_TOOLS_DEBUG | false |
| VISION_TOOLS_DEBUG | false |
| MOA_TOOLS_DEBUG | false |
| IMAGE_TOOLS_DEBUG | false |

### ~/.hermes-v4pro/.env — V4 Drafter (port 8645)
| Variable | Value |
|----------|-------|
| API_SERVER_KEY | <REQUIRED_SECRET_NOT_TRACKED> |
| DEEPSEEK_API_KEY | <REQUIRED_SECRET_NOT_TRACKED> |
| HERMES_CIS_BRIEFING_PATH | /mnt/projects/cis/session_handoffs/CURRENT_CONTEXT_BRIEFING.md |
| HERMES_KANBAN_DB | /mnt/projects/cis/data/kanban.db |
| HERMES_KANBAN_HOME | /mnt/projects/cis/data |
| GATEWAY_ALLOW_ALL_USERS | true |

### ~/.hermes-r1/.env — V4 Reviewer (port 8643)
| Variable | Value |
|----------|-------|
| API_SERVER_KEY | <REQUIRED_SECRET_NOT_TRACKED> |
| DEEPSEEK_API_KEY | <REQUIRED_SECRET_NOT_TRACKED> |
| HERMES_CIS_BRIEFING_PATH | /mnt/projects/cis/session_handoffs/CURRENT_CONTEXT_BRIEFING.md |
| HERMES_KANBAN_DB | /mnt/projects/cis/data/kanban.db |
| HERMES_KANBAN_HOME | /mnt/projects/cis/data |
| TERMINAL_TIMEOUT | 60 |
| TERMINAL_LIFETIME_SECONDS | 300 |

### ~/.hermes-v4impl/.env — V4 Implementer (port 8646)
| Variable | Value |
|----------|-------|
| API_SERVER_KEY | <REQUIRED_SECRET_NOT_TRACKED> |
| DEEPSEEK_API_KEY | <REQUIRED_SECRET_NOT_TRACKED> |
| HERMES_CIS_BRIEFING_PATH | /mnt/projects/cis/session_handoffs/CURRENT_CONTEXT_BRIEFING.md |
| HERMES_KANBAN_DB | /mnt/projects/cis/data/kanban.db |
| HERMES_KANBAN_HOME | /mnt/projects/cis/data |

### ~/.hermes-qwen/.env — Qwen (port 8644, paused)
| Variable | Value |
|----------|-------|
| API_SERVER_KEY | <REQUIRED_SECRET_NOT_TRACKED> |
| HERMES_CIS_BRIEFING_PATH | /mnt/projects/cis/session_handoffs/CURRENT_CONTEXT_BRIEFING.md |
| HERMES_KANBAN_DB | /mnt/projects/cis/data/kanban.db |
| HERMES_KANBAN_HOME | /mnt/projects/cis/data |
| TERMINAL_TIMEOUT | 60 |
| TERMINAL_LIFETIME_SECONDS | 300 |

---

## Secret Variables Reference (not stored — must be provided from secret store)

| Variable | Profiles that need it |
|----------|----------------------|
| API_SERVER_KEY | prime, v4pro, r1, v4impl, qwen |
| DEEPSEEK_API_KEY | prime, v4pro, r1, v4impl |
| TELEGRAM_BOT_TOKEN | prime only |
| BROWSERBASE_ADVANCED_STEALTH | prime only |
| BROWSERBASE_PROXIES | prime only |
