# Governance vs Direct Action — The Three Breaks

## Eric's Correction (July 12, 2026)

Eric explicitly corrected the treatment of ADRs as real decisions:

> "did you just connect the old useless adrs to the new ui or did you document the
> work that was actually done after I broke from the ceremonial governance dev and
> let deepseek start building the real app. I did the same with glm 5.2 when I
> figured out the project had stalled with pipeline circular building and allowed
> glm to just go through and build what was needed."

The 16 ADRs (ADR-SEED-001 through 016, all dated June 7-19) are governance-era
artifacts produced by the Claude/ChatGPT advisory process. They are NOT current
decisions. The real history is in git log, session closeouts, and handoff docs.

## The Three Breaks

### Break 1: Claude/ChatGPT Governance → Direct Building (June 19-20)
Eric recognized that the ADR + closeout + tier process was governance theater.
The FD.1 revert-and-rebuild on June 19-20 was the last act under the old process.
After that, no more ADRs were recorded. Models were allowed to build directly.

### Break 2: DeepSeek Pipeline Circular Building → GLM Direct Build (July 7-8)
The pipeline had stalled with circular building — specs about specs, reviews about
reviews. Eric allowed DeepSeek and then GLM to go through and build what was
needed. The 18 commits on July 8 are the result: a working pipeline relay,
end-to-end verification, data integrity fixes, and a passing test.

### Break 3: Stale Context → Fresh Start (July 12, current)
Eric wants to stop using Telegram and host-level agents to do work, and start
working through the pipeline UI. The project-centered UI was built to enable this.

## The Pattern

Each break followed the same arc:
1. **Progress stalls** — the current process produces ceremony, not software
2. **Eric recognizes the stall** — "governance theater", "circular building"
3. **Direct action is authorized** — a model is told to "just go through and build"
4. **Working software is produced** — faster than the preceding governance period

The GLM build era produced more working software in 5 days than the governance
era produced in 20. That's the lesson.

## Self-Evolving Implication

This history exists to demonstrate a pattern for the self-evolving feature:
the system should detect when progress stalls and allow direct action breaks.

1. **Detect stalls** — if the same spec is being revised without implementation,
   flag it. If review rounds produce no code, flag it.
2. **Allow direct action breaks** — when a model can build the thing, let it build
   the thing. Document after, not before.
3. **Track real decisions, not just ADRs** — the most consequential decisions in
   this project were made by breaking from the documented process. The git log
   is the real record; ADRs are historical context.
4. **Invalidate stale tracking** — the DEV-PIVOT table was created June 30 and
   never updated. The ADRs are historical. The git log is authoritative.
5. **Preserve the reasoning** — not "what was decided" but "why the process was
   abandoned in favor of direct action."

## UI Display Rule

When showing project decisions in the UI:
- ADRs must be labeled as "Governance Era — Historical" with date range
- Dev pivots should show alongside ADRs with their real status (LIVE/INVALIDATED)
- Closeout stats (passed/blocked/failed) show real development activity
- The git log is the source of truth for what was actually built

## Reference

- `docs/DEVELOPMENT_HISTORY.md` — full timeline with the three-era framework
- `dev_pivot_status` table — 17 entries tracking what's still relevant
- `session_closeouts` table — 50 records (34 PASS, 12 BLOCKED, 4 FAIL)
- `project_decisions` table — 16 ADRs (all governance-era, June 7-19)
