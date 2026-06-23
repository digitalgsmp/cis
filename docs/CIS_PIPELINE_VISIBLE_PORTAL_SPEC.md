# Spec: Pipeline-Visible Portal — Conversation as the Pipeline Surface

**Author:** deepseek-v4-pro (hermes-v4pro)  
**Date:** 2026-06-23  
**Status:** DRAFT v2 — rewritten after Eric design direction  

## Core Principle

The user does not leave the conversation. The pipeline does not run in a black box. The portal panels become windows into the pipeline stages, visible and interactive in real time.

## Design

### Stage 0: Clarification (mandatory, before any trigger)

When a model detects that Eric's conversation may need the pipeline:

1. Model stops and says: "Here's what I understand you want: [restatement]. Here's what I intend to do: [proposed action]. Is this correct?"

2. Eric responds. This is a back-and-forth clarification. Not one prompt.

3. Only when Eric confirms alignment does the model commit to the trigger.

4. If Eric says "no, that's not right" — the model revises understanding. No pipeline fires.

### Stage 1: Trigger (visible in chat panel)

When alignment is confirmed:

1. The model announces: "Routing through pipeline." 

2. The portal adds panels or expands the view to show:
   - **Pipeline panel**: intent → classify_route result → which gateway was selected, why
   - **Drafter panel**: the proposal being drafted, live
   - **Reviewer panel(s)**: R1 verdict, Qwen verdict, objections, live
   - **Gate panel**: each gate firing — git_state, no_secrets, staleness, deliberation — with PASS/FAIL visible
   - **Hook panel**: pre_tool_call gate checks firing, showing what's blocked and why

3. Eric can pause, question, or redirect at any stage. Each panel has an input for Eric to interject.

4. Nothing executes without Eric seeing it. The panels ARE the pipeline.

### Stage 2: Deliberation (visible, interactive)

1. Drafter produces proposal → visible in Drafter panel
2. Reviewer(s) fire → verdicts and objections visible in Reviewer panel
3. If OBJECTIONS or deadlock → visible to Eric immediately
4. Eric can: accept objections and revise, override and proceed, or escalate manually
5. Only when CONSENSUS_REACHED (or Eric overrides) does the gate panel unlock

### Stage 3: Gates (visible, interactive)

1. Each gate fires in sequence → result appears in Gate panel
2. FAIL on any gate → what failed, why, visible. Eric decides: fix, override (GATE_DISABLED), or abort
3. All gates PASS → Implementer panel unlocks

### Stage 4: Implementation (visible, constrained)

1. Implementer receives directive with gates cleared
2. Hooks fire before every write_file/patch/terminal → visible in Hook panel
3. Eric sees every tool call being gated
4. Final evidence (git diff, test output) visible before Eric approves closeout

### What the Portal Looks Like After This Change

Current: 3 tabs (Control, Deliberation, Chat) in one row of 4 panels

After: The 4-panel chat grid remains. Below it or beside it, additional panels appear when the pipeline is active:
- Pipeline status bar (always visible): shows current workflow_run state
- When active: Drafter panel, Reviewer panel, Gate panel, Hook panel
- Eric can resize, show/hide, focus any panel
- All panels are read/write: Eric can type into any of them

### What Does NOT Change

- The Chat tab remains the default. You start every interaction in chat.
- Direct model chats (Qwen, GLM, Claude) remain as they are — they're for thinking, not building.
- classify_route() keyword matching remains as fallback.
- gate_runner.sh, hooks, deliberation engine — unchanged. Just exposed.

### What IS New

- Clarification stage before any trigger
- Pipeline stages visible as portal panels
- Eric retains control at every stage
- No black box
