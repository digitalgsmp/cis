# Advisor review — consolidate-author-role

- packet: `reviews/pending/consolidate-author-role.md`
- advisor: advisor on port 8649, no tools
- run tag: consolidate-author-role @ 2026-09-12T10:00:58-05:00
- at: 2026-09-12T10:01:32
- prompt_tokens: 21151
- completion_tokens: 1647
- total_tokens: 22798
- token source: gateway response usage
- model turns: 1 (single-turn: the advisor has no tools, so there is nothing to iterate on)
- finish_reason: stop

---

FRAME: RIGHT_WORK

Eric directly asked for this — the verbatim intent is a clear instruction to move his brainstorming/card-writing from the host Drafter into a consolidated container Author. The consolidation is sound (same model, same lineage, no enforcement value in the split). The pending build plan node is Enforcement — Container Isolation (ADR-015/016), which the proposal correctly scopes out — but moving the Author INTO the container is logically upstream of enforcing container isolation, not in conflict with it. The current phase (Control Plane Observation Pipeline spec revision) is not blocked by this work, and this is infrastructure plumbing Eric needs to get his chat path working. It's the right item at the right time.

---

Now the actual review:

**What's solid:**

The intent citation is clean and verbatim. The rationale (same model, same lineage, no enforcement/independence value) is correct — the current phase confirms Brainstorm (8644) and Drafter (8645) are both DeepSeek profiles in the same pipeline team. The acceptance criteria are concrete and testable: port up, sqlite rows, queue_items INSERT, delivered chat message. The evidence requirements match the criteria. The out-of-scope boundary (design-spec loading, enforcement gates) is correctly drawn.

**Problems:**

1. **Scope item 2 (MCP bridge re-enable) is under-specified.** The proposal says "re-enable the `cis-knowledge` MCP bridge (currently `enabled: false`)" but doesn't say what broke it or what "re-enable" entails — config flag flip, code change, container rebuild? If it's just a YAML toggle, fine, but the acceptance criterion for it (sqlite rows returned) tests the spine, not the MCP bridge specifically. A passing sqlite SELECT doesn't prove the MCP bridge is wired; it proves the database is reachable. The evidence should include the Author successfully calling an MCP tool, not just sqlite returning rows.

2. **Scope item 3 (chat path) is too open.** "Telegram or the 5000 front-door" — these are very different integrations with different failure modes. The packet should pick one and spec it. The acceptance criterion ("Eric can send a message and get a reply") is good but the implementation path is ambiguous, which means the worker will have to make a design decision that should be in the card.

3. **No rollback / migration plan for the existing pipeline.** The currentpipeline team explicitly lists Brainstorm (8644) and Drafter (8645) as active agents in the Control Plane Observation Pipeline. Merging them into one Author profile on one port means the pipeline relay code that dispatches to port 8644 and port 8645 will break unless it's updated. The proposal doesn't mention updating pipeline_relay.py, the agent registry, or whatever config maps pipeline phases to ports. This is the biggest gap — the consolidation is presented as a profile merge, but it's actually a pipeline topology change. The worker needs to know: does pipeline_relay.py reference these ports by number? Is there an agent registry? What else dispatches to 8644/8645?

4. **"Host Drafter is being retired" is asserted but not evidenced.** The proposal says the host Drafter is being retired, but nothing in the project state confirms this is a decided thing vs. an aspiration. If the host Drafter is still in active use, retiring it as part of this card creates a gap. If it's already moribund, fine — but the card should say so with evidence.

5. **No mention of what happens to brain.yaml and draft.yaml.** Are they deleted? Left in place but disabled? Renamed? If left alive, the pipeline might still dispatch to them. If deleted, that's a git history change the worker needs to make deliberately. The card should specify the disposition.

**Summary of what I'd require before approving this card:**

- Specify the chat path (pick one: Telegram or 5000 front-door) and describe the integration.
- Add a scope item for updating pipeline_relay.py / agent registry to point at the new Author port instead of 8644/8645.
- Change the MCP bridge evidence from "sqlite returns rows" to "Author successfully calls an MCP tool" — or add it as a separate criterion.
- Specify disposition of brain.yaml and draft.yaml (delete, disable, archive).
- Evidence or rationale for the claim that the host Drafter is being retired (is this already decided, or is this card making that decision?).
