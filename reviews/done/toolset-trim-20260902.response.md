# Advisor review — toolset-trim-20260902

- packet: `reviews/pending/toolset-trim-20260902.md`
- advisor: review2 on port 8647, no tools
- run tag: toolset-trim-20260902 @ 2026-09-02T03:30:41-05:00
- at: 2026-09-02T03:31:09
- prompt_tokens: 2083
- completion_tokens: 1223
- total_tokens: 3306
- token source: gateway response usage
- model turns: 1 (single-turn: the advisor has no tools, so there is nothing to iterate on)
- finish_reason: stop

---

Here is my review.

## What I would object to

1. prompt_tokens landed at 4,502, which is above the "near 3-4k" target. The result packet reports this asa success, but 4.5k is 12-15 percent over the top of the requested band. It is close, but the card said "near 3-4k" and the result overshoots. If the goal was to get an advisor small enough to borrow cheaply, that extra 500-1,500 tokens matters. The packet never addresses the gap.

2. The file toolset is all-or-nothing, and the card acknowledged this, but the result did not act on it. write_file and patch are in the final tool surface. An advisor that is supposed to read and answer should not be able to patch files or write files. The caveat was logged, not resolved. If there is no per-tool granularity in the platform_toolsets mechanism, that should be stated explicitly as a known limitation blocking the ideal configuration, and the residual risk should be called out.

3. cis-knowledge carries three dispatch tools — cis_dispatch_drafter, cis_dispatch_reviewer, cis_dispatch_implementer — that can start pipeline runs. The standing rule is that runs are not started without Eric. The card flagged this but did not resolve it. Leaving dispatch tools live in an advisor config is a real problem, not a footnote. Either those tools should have been removed (if cis-knowledge is also all-or-nothing, say so), or the config should not have been committed without Eric's sign-off on the exception.

4. The backup naming is confusing. config.yaml.bak.20260902-devmode is described as "pre-skills state" but its timestamp is Aug 29 21:47, which is before Sep 2. The naming says 20260902 but the file predates that. This is likely because the skills disable was done earlier and the backup was named for the review run, not the write date. It is not wrong per se, but the packet should clarify this so nobody restoring from backups picks the wrong file.

5. The instruction asked for "a list of what the agent can still do." Evidence 5 enumerates 22 tools by name with byte counts, which is a tool inventory, not a capability list. There is no plain-language summary of what the advisor can actually do for a user — e.g., "read files, search the CIS knowledge base, check build status, query open decisions." The letter of the request was not met.

## What the packet does not establish

1. It does not establish that 4,502 prompt_tokens is good enough. The card's expectation was "near 3-4k." The result exceeds it. No comparison to a 3-tool or 1-tool configuration is given to show whether further trimming is possible or whether 4.5k is a floor.

2. It does not establish that the agent still functions correctly as an advisor. The only functional test was "Reply with exactly: PONG." That proves the model responds, not that it can read a file and answer a question about it, or query the CIS KB and synthesize a result. No end-to-end advisor task was run.

3. It does not establish that the dispatch tools in cis-knowledge are safe to leave enabled. The caveat is flagged but unresolved. If a borrowed advisor can start a pipeline run, that is a standing risk that needs explicit approval.

4. It does not establish that write_file and patch are acceptable in an advisor config. Same pattern — flagged, not resolved.

5. It does not establish that the other five agent configs are unaffected beyond md5. The md5 check is good, but it only proves the files were not modified. It does not prove those agents still work — e.g., if they share a toolset definition file or a plugin directory that was changed, their configs could be identical but their runtime behavior could differ. The packet gives no evidence about shared resources.

6. It does not establish what "basic text response" is in this context. The instruction mentioned "whatever provides basic text response" as something to keep. The final config keeps file and cis-knowledge. Is basic text response built into the model and therefore needs no toolset? Or was there a toolset that provides it that was dropped? The packet does not address this.

7. It does not establish a restoration path. The diff comment says "Restoring means deleting this block." That is correct in principle, but there is no automated restoration mechanism, no cron job, no guardrail. If someone forgets, the reviewer agent runs with 2 toolsets instead of 14 and produces incomplete reviews. The packet should state whether this is an accepted risk or whether a restoration guard is planned.

## Bottom line

The trimming itself was done cleanly — backup, verify, diff, isolation of other configs. The measurement methodology is sound. But the result overshoots the token target, two known safety issues (dispatch tools, write/patch) were flagged but left unresolved, the "what can the agent still do" deliverable was not really produced, and the only functional test was a PONG. I would not sign off without: a reduction to the 3-4k band or an explanation of why 4.5k is the floor, resolution of the dispatch and write/patch issues, a plain-language capability list, and at least one end-to-end advisor task proving the trimmed agent can actually advise.
