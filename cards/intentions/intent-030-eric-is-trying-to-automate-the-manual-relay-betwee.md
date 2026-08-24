# Intention Card

**Intention:** Eric is trying to automate the manual relay between the Drafter and Reviewer agents in the CIS pipeline, enabling a self-contained, state-driven deliberation loop that operates without human intervention.

**Mission Connection:** This aligns with the CIS mission of building a multi-agent system where AI models review each other’s work, validate against documented intentions, and produce verified builds through autonomous, containerized processes. Automating the orchestration loop reduces friction, increases reliability, and enables scalable, repeatable validation workflows.

**What Was Learned:** Eric confirmed that the orchestrator must be a state machine that manages the flow between agents via HTTP REST calls to the gateway, and that the goal is to eliminate manual handoffs. This validates the need for a centralized control plane component that enforces process integrity.

**Relevance to Frontier Model:** A frontier model must understand that Eric is not just requesting code, but designing a critical control mechanism in a larger system where autonomy, validation, and process governance are paramount. It must align with the broader architecture of CIS, including containerized enforcement, dual review, and knowledge base integration.

**Category:** infrastructure

**Session:** v4pro:api-d7883219432ff918
**Date:** 2026-06-05 19:58

**Verbatim Quotes:**
- "Build orchestrator.py at /mnt/projects/cis/orchestrator.py — a state machine that drives the Drafter→Reviewer deliberation loop via HTTP REST calls to gateway endpoints, removing Eric from manual relay."
