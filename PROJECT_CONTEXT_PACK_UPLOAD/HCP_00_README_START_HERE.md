# Project Context Pack — Hermes Harness / CIS
Version: 2026-06-01 (CIS Deterministic Pipeline Decision)
Maintained by: Hermes/DeepSeek (transitional — target: generated export Phase F)
Reviewed by: Eric

## IMPORTANT — Architecture Change (2026-06-01)

**CIS is a Hermes-native adversarial deliberation engine. The pipeline is the product.**

HCP files are the external advisor packet for ChatGPT and Claude.
They are transitioning from manually maintained markdown to generated exports
from a Hermes-native deterministic state spine (SQLite).

During this transition, these files are still manually updated.
After Phase F (HCP export pipeline), they will be auto-generated.

**HERMES_CIS_BRIEFING_PATH is transitional.** Target retirement: Phase E.
Replacement: /mnt/projects/cis/AGENTS.md auto-loaded by all profiles natively.

## Purpose
This pack is the current state of the Hermes Harness / CIS project,
shared between Hermes, ChatGPT, and Claude.
Read this before asking Eric for context.
Do not infer from older files if this pack conflicts with them.
Do not reopen decisions marked complete.
Ask Eric before changing direction.

## How to use it
1. Read HCP_01_CURRENT_STATE.md first
2. Read HCP_05_NEXT_ACTIONS.md
3. Read HCP_07_RECENT_HANDOFF.md if starting a cold session
4. Reference other HCP_ files as needed

## Update protocol (current — transitioning)
Hermes updates these HCP_ files after each significant session.
In Phase F, a deterministic export pipeline will generate them from the state spine.
Eric reviews and uploads to ChatGPT and Claude projects periodically.
