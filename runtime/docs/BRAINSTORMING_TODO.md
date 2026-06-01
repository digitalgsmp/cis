# Brainstorming TODO

Items discussed during sessions that need tracking. Checked items are resolved.

| ID | Status | Item | Notes |
|----|--------|------|-------|
| 001 | pending | R1 + V4-Pro evaluate creating a database table for tracking brainstorm items | Better than a flat markdown file long-term |
| 002 | pending | Audio connection for Advisor Chat | Talk instead of type |
| 003 | pending | Escalation routing is broken | Dashboard model picker doesn't switch gateways — selecting R1 or Qwen still spawns a new Prime gateway. Escalation needs to be context snapshot-and-handoff, not a research phase |
| 004 | pending | No handoff acknowledgment signal | User switches to new model thread and gets silence — need "R1 received context, working" indicator |
| 005 | pending | Model identity: Prime = deepseek-v4-pro ("fast" mode, snappy chat). V4-Pro Advisor = deepseek-v4-pro ("reasoning" mode, deep analyst paired with R1). Both are the same underlying model, different inference modes | Document this clearly so I stop talking about myself in third person |
| 006 | pending | Prime incorrectly calls V4-Pro "Qwen" | I keep referring to the deep analyst as Qwen. Qwen is a separate model entirely |
| 007 | pending | Qwen = local 30B MOE model running on GPU. Hardware is not powerful enough to run Qwen with more reasoning capability, so it is used to execute detailed instructions from V4-Pro reasoning and R1 after their opinions have been reconciled | Worker only, never deliberates |
| 008 | pending | Unified memory across Prime, V4-Pro, and R1 | ChromaDB + SQLite needs to serve all three profiles so they share session history, decisions, and preferences |
| 009 | pending | Can Prime, Deep Reasoning (R1), and Deep Analyst (V4-Pro) search each other's session files? | Current answer: no. Each gets its own session store. This is part of the unified memory problem (#008) |
| 010 | pending | Define per-profile providers in config.yaml so each gateway is locked to its correct model/mode | Currently `providers: {}` is empty. Need named providers (deepseek-fast, deepseek-reasoning, deepseek-r1) with different reasoning_effort settings. Also: deepseek-v4-pro is ONE model ID — fast vs reasoning is controlled by reasoning_effort, not by model name |
| 011 | pending | Three Hermes installations (~/.hermes,~/.hermes-r1,~/.hermes-qwen) all have effectively identical configs — same reasoning_effort:medium across the board, no per-profile provider differentiation | All three answer as v4-pro because DeepSeek decides when to reason. The config files don't force the behavior: Prime should be fast/snappy (low/no reasoning), V4-Pro should be deep analyst (high reasoning), R1 should be the reasoner model. Right now the three-installation split is cosmetic — the configs don't enforce the intended division of labor |
| 012 | pending | Research: a primary CIS process is being ignored by all models at all levels — from external advisors down to Prime. Same behavior likely present in Qwen if it ever gets a chance to act. | Need to identify what the primary CIS process is, document how each model ignores it, and determine why. This is systemic — not a single-model failure |
