# Spec: Chat-to-Pipeline Inference Trigger

**Author:** deepseek-v4-pro (hermes-v4pro)  
**Date:** 2026-06-22  
**Status:** DRAFT — submitted for adversarial review  

## Problem

The CIS Portal Chat tab is disconnected from the CIS pipeline. When Eric describes a task in chat, models respond in flat 1:1 mode — no intent classification, no drafter/reviewer deliberation, no gate checks, no workflow_run creation, no session logging. The pipeline exists and works, but Eric must manually switch to the Control tab to trigger it.

## What Eric Actually Wants

Eric described it directly: "the chat itself IS the input. The models you're talking to should detect when you're asking for something that needs the pipeline, and trigger it automatically. You keep talking. The pipeline runs in the background. Results surface back into the chat. You never leave the conversation."

The trigger pattern was demonstrated in this very session when I (v4pro) inferred Eric's goal from full conversation context and stated it explicitly. That inference — "from everything I know about Eric and CIS, does this conversation need to enter the pipeline?" — IS the trigger.

## Design

### Trigger: Model Inference, Not Keyword Matching

The existing `classify_route()` at `runtime/api/advisor.py:86` uses keyword signals (does the message contain "build"? "design"?). This is v0.1 and blind to conversation context.

The new trigger uses the model's own inference. When Eric chats with any model, that model is given context about CIS pipeline capabilities. If the model detects Eric is describing a task that should enter the pipeline, it signals the backend.

### Flow

```
Eric types in Chat tab
  ↓
Message sent to Hermes gateway with SYSTEM prompt:
  "You are a CIS pipeline-aware agent. If Eric describes a task that
   needs design/planning, implementation, review, or research with
   evidence, begin your response with [PIPELINE:<intent summary>].
   Otherwise respond normally."
  ↓
Model responds
  ↓
Backend checks response for [PIPELINE:...] marker
  ↓
  ├─ Not found → display response in chat normally (flat chat)
  │
  └─ Found → 
      1. Extract intent summary after [PIPELINE:]
      2. Call /api/advisor/route with the intent
      3. classify_route() dispatches to correct gateway
      4. drafter_start.py creates workflow_run
      5. pipeline_dispatch.sh fires staleness + deliberation
      6. Return chat response + pipeline status to UI
      7. Chat panel shows: model response + "Pipeline triggered: <intent> [status]"
      8. Deliberation results surface in the Deliberation tab
      9. Eric can approve/reject from Control tab
```

### Implementation Points

1. **Backend: `/api/portal/chat`** (app.py ~line 287)
   - Modified to send a SYSTEM message before the user message:
     "If Eric is describing a task that requires the CIS pipeline (design, plan, build, implement, review, research requiring evidence, or tool execution), begin your response with [PIPELINE:<1-sentence intent summary>]. Otherwise respond normally. The pipeline will route your intent to the appropriate gateway, run deliberation, and enforce gate checks."
   - After receiving model response, scan first line for `[PIPELINE:...]`
   - If found: strip the marker, call `/api/advisor/route` with the intent, return both chat response and pipeline run_id
   - If not found: return response as-is (backward compatible)

2. **Frontend: `portal.html`** `sendChat()` and friends
   - Parse response for `pipeline_triggered` and `run_id` fields
   - Show inline notification in chat panel when pipeline fires
   - Add link/button to view deliberation results
   - NO other changes to existing chat behavior

3. **No changes to:** classify_route(), drafter_start.py, pipeline_dispatch.sh, gate_runner.sh, hooks. The pipeline is unchanged — only the input path changes.

4. **Configuration**
   - Add `pipeline_trigger_enabled: true` to runtime.env (toggle)
   - Default ON for v4pro, r1 gateways; OFF for direct models
   - SYSTEM prompt configurable per gateway

### What This Does NOT Change
- Direct model chats (Qwen, GLM, Claude) still go through chat-direct — no Hermes pipeline
- The Control tab still works exactly as it does now
- classify_route() keyword matching still works as a fallback
- Hooks and gates are unchanged

### Evidence of Success
1. Eric types "can you help me design a logging system" in Chat tab
2. Model responds with [PIPELINE:design a universal session logging system for all portal models]
3. Backend strips marker, routes intent through classify_route()
4. Drafter gets the intent, produces proposal
5. Reviewer deliberates
6. Eric sees chat response + "Pipeline running: run-abc123 [DRAFTING]"
7. Eric can check Deliberation tab for reviewer verdicts
8. If CONSENSUS_REACHED, Eric approves → Implementer builds under gates

---

## Open Questions for Reviewers
1. Should the [PIPELINE:] marker be in the model's visible response, or a separate field?
2. Should the trigger be configurable per gateway? (e.g. prime always triggers, qwen never triggers)
3. What happens if the model triggers the pipeline but Eric was just thinking out loud? Cancel mechanism?
4. Should conversation history be injected into the workflow_run context?
