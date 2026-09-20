# Execution rules

Prepended to every card dispatched in `implement` mode. These rules govern
this run; the card text that follows is the full context for the work.

- Do only what the card says. Do not add, refactor, or "improve" anything
  the card did not ask for.
- Touch only files the card names or directly requires (e.g. a schema
  migration a named file's change requires). Read only files needed to do
  the card's work.
- No questions to Eric, no options, no follow-up offers.
- No subagents.
- No commits, no pushes.
- No edits to memory/docs/CLAUDE.md/AGENTS.md files unless the card
  explicitly asks for that edit.
- Do not touch any `data/agent_handoffs/` folder other than this run's own.
- Before changing any existing file, save its preimage under `backups/` in
  this run's folder.
- Make technical decisions yourself; record them in `evidence.md`.
- Write `evidence.md` (decisions, commands run, exit codes, key output,
  changed files, mock vs. live tested) first, then `completion.json` last
  (fields: `card_id`, `status` — `READY_FOR_VERIFICATION` or `BLOCKED` —,
  `changed_files`, `tests`, `remaining_limitations`). Never self-label
  `VERIFIED`.
- If something cannot be done safely, stop, keep whatever progress exists,
  and set `status` to `BLOCKED` with the exact reason.
- Final reply to this prompt: 10 lines max.
- Then stop. Do not continue, retry, or start follow-on work.
