## DEPENDENCY MAP — what blocks what (2026-08-29)

TIER 0 — the container cannot be trusted until these are true
  [DONE] container semantic search (was 1)
  [DONE] KB coverage for the build corpus (was 2/3)
  [DONE] Eric Gate briefing populated
  [DONE] FINAL_JSON parser
  [DONE] agent state on persistent volumes (was 10)
  T0-a  CHROMA CONCURRENCY ARBITRATION (from item 1's notes)
        The container now queries Chroma live. A host-side ingest or re-embed
        while it does corrupts the read — proven 2026-08-29:
        "Error deserializing pickle file: trailing bytes found".
        BLOCKS: every other item that runs an ingest, which is 8, 14, 19.
        Until this is decided, no host job may run while a pipeline run is live.

TIER 1 — blocks a run completing end to end
  T1-a  PROVE A RUN COMPLETES PAST THE GATE (new, and this is the real one)
        No run has ever gone intake -> deliberation -> gate -> implement ->
        verify -> done. The furthest any run reached is ERIC_GATE.
        DEPENDS ON: item 5 (approve the waiting run).
        BLOCKS: everything downstream. Until this passes once, we do not know
        what else is broken.
  5     APPROVE OR CLOSE run-e70293544935a92e-1787973534
        Briefing renders, hash stable, goal_reference 12 exists.
        Eric's decision. This is the gate on T1-a.
  9     MEASURE PROMPT SIZE, then decide a cap
        Over-length input fails silently; the three largest prompts ever sent
        went to VERIFICATION, the phase whose job is checking claims.
        tokens_in exists and is 0 on every row.
        BLOCKS: trusting any verify result, so it blocks T1-a's meaning.
  12    STREAM AGENT COMPLETIONS
        Replaces the heartbeat's weak liveness proxy with observed output.
        menter reports elapsed 180s / idle 180s — its gateway log is never
        written during a call, so liveness may be measuring nothing for it.
        BLOCKS: knowing whether a long run is working or hung.

TIER 2 — blocks trusting what a run produces
  T2-a  CAPTURE TOOL CALLS PER RUN (prerequisite, verified missing)
        agent_trajectories has no record of which files an agent read.
        No tool_calls table exists.
        BLOCKS: item 22 entirely. Also blocks any evidence-based gate.
  22    GATE: NEVER GUESS — LOOK AT THE FILE  (needs T2-a)
  6     effort_metric scores DRAFT by code complexity; draft writes prose specs.
        False "sandbagging" on every draft. Advisory, so noise not blockage.
  4     POINT RUNS AT DEV-PIVOT DOCS, not build_plan_nodes
        Briefing's last blank fields. Needs Eric's call: does a run name its
        DEV-PIVOT at intake, or are repairs marked maintenance?
        Do NOT let brain infer it.
  16    gateway_status_qwen stale — claims Qwen is 2nd reviewer on 8644.
        Container reviewers are review1 8643, review2 8647. Wrong facts in the
        agents' own briefing.
  17    CLAUDE.md says spine is runtime/spine.db; that file is 0 bytes.
        Both spine and KB are data/cis_memory.db. Wrong facts in the operator
        instructions every agent reads.

TIER 3 — independent defects, no dependants
  7     ask_history hybrid search (FTS5 + vector merged). relay does this now;
        ask_history does not.
  13    Export gate "expected 12 artifacts, found 13" on every commit.
  15    data/ is gitignored — container_sessions and drive_imports not in VC.
  18    Retention policy for data/backups/.
  P     projects.id 'cis' vs build_plan_nodes.project_id 'CIS' — plain join
        returns 0 of 30 rows; relay:1058 papers over it with COLLATE NOCASE.

TIER 4 — after the infrastructure works
  8     Session ingest trigger (manual today) — needs T0-a
  14    Container agent history to the KB — needs T0-a; state now persists
  11    What the container regulates itself vs human trigger
  19    601 mined asks -> cards
  20    A hermes agent in these working sessions
  21    Implement the role theory into the agents
  ARCH  Archive processing — prose vs software split, Troy excluded. Not now.
