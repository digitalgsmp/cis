# Advisor review — intent-slate-loop

- packet: `reviews/pending/intent-slate-loop.md`
- advisor: evaluator on port 8650, no tools
- run tag: intent-slate-loop @ 2026-09-09T19:29:53-05:00
- at: 2026-09-09T19:33:19
- prompt_tokens: 2867
- completion_tokens: 2531
- total_tokens: 5398
- token source: gateway response usage
- model turns: 1 (single-turn: the advisor has no tools, so there is nothing to iterate on)
- finish_reason: stop

---

1. What Eric is trying to achieve.

Eric is trying to build a software development machine that manages its own state and proposes its own next steps, leaving him to act only as a final gatekeeper who picks from a menu of options. He wants to completely remove himself from the role of context carrier, dependency tracker, and project manager. The document frames this as building a slate generation mechanism and fixing real time queue updates, but that is a mechanical framing. The actual intent is to eliminate his own cognitive load in directing the work. He wants to supervise a self driving pipeline, not drive it.

2. Missing capabilities.

First, a live source of truth for project state. The activity tables stopped writing months ago, and the queue database is disconnected from the actual files. The system needs a mechanism that updates the queue in real time as work happens, so proposals are based on current reality, not stale snapshots.

Second, a regenerating dependency graph. The current dependency map is a static, hand made snapshot. The system needs a way to automatically derive what blocks what, so it does not propose work that is premature.

Third, a reliable execution outcome signal. The success link was withdrawn because of false positives, and there is no test suite. The system needs a trustworthy way to know if a card actually succeeded, otherwise the slate will propose fixes for things that are already done, or move on from things that failed.

Fourth, the slate proposer itself. There is currently no mechanism that synthesizes the queue state, dependencies, and recent outcomes into a short list of next steps for the advisors to contest and Eric to pick from.

Fifth, two way communication with Eric. Telegram is currently a one way feed. If he is supposed to pick an item and have the loop proceed, his reply must actually reach the system.

3. The smallest first build.

The smallest first build is the degraded slate itself, injected directly into step three of the existing loop. Do not build the real time database updates, the dependency graph, or the success signals first. Have an agent read the raw markdown file at the end of every result review and output a proposed next item, along with its reasoning. Eric picks it or corrects it. This makes the loop self improving because the very first slates will naturally expose their own blindness. When the degraded slate proposes an item that is already done, or misses a critical dependency, that failure becomes the exact input needed to justify building the real time updates and dependency graphs as the next cards. The loop bootstraps its own infrastructure by tripping over the lack of it.
