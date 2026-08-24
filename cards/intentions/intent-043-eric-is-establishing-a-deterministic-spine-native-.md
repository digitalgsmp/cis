# Intention Card

**Intention:** Eric is establishing a deterministic, spine-native handoff process for the Drafter-to-Reviewer transition in the CIS pipeline to bridge the gap between the designed system and current terminal reality.

**Mission Connection:** This intention directly supports the CIS mission of building a multi-agent pipeline system where AI models review each other's work, validate against documented intentions, and produce verified builds. By formalizing the handoff process, Eric ensures that the system's control plane can reliably route between agents, enforce containerized workflows, and maintain consistency across sessions.

**What Was Learned:** The current system lacks a formalized draft initiation process and deterministic closeout, creating a gap between the designed pipeline and actual implementation. Eric learned that a temporary contract (ADR-SEED-014) is needed to define the minimal manual initiation process until full spine-native automation is achieved.

**Relevance to Frontier Model:** Claude/ChatGPT need to understand that Eric is prioritizing deterministic, spine-native workflows to ensure system reliability and traceability. This exchange reveals that the system must support both temporary manual steps and long-term automated processes, with clear documentation and validation at each stage.

**Category:** infrastructure

**Session:** r1:20260614_230412_b3cbfb
**Date:** 2026-06-14 23:07

**Verbatim Quotes:**
- "Here's what the Drafter needs, broken down into three core requirements: 1. Session initialization must be spine-native and deterministic. 2. Closeout must be automated and closed-loop. 3. FINAL_JSON must be validated against the spine schema."
- "Objective: Close the gap between the designed CIS pipeline and current terminal reality by making Drafter session initialization, Drafter closeout, FINAL_JSON validation, and Reviewer dispatch deterministic and spine-native."
- "Yes. Draft ADR-SEED-014 first as a standalone decision, then revise the Tier 11C spec to reference it."
- "ADR-SEED-014 should define the temporary draft-initiation contract: Eric states the initiating intent. A minimal manual TRIAGE / drafter_start.py shim creates the workflow_run. Drafter receives workflow_run_id plus spine-derived briefing."
