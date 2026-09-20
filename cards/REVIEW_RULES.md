# Review rules

Prepended to every card dispatched in `review` mode. This run has no write
access to the repository; it reads and reports only.

- Read only: the card, its `evidence.md`, its `completion.json`, and the
  changed files it lists. Do not read anything else.
- Do not re-run the implementer's work, do not re-derive it from scratch,
  and do not explore the rest of the repository.
- Output exactly one verdict, `PASS` or `FAIL`, to `review.md`.
- List at most 10 reasons supporting the verdict, as short bullets.
- No rewrites. Do not propose or write code changes.
- No suggestions beyond the card: do not recommend follow-on work, scope
  expansions, or unrelated cleanups.
- No questions, no options, no follow-up offers. No subagents. No commits.
- Final reply to this prompt: 10 lines max. Then stop.
