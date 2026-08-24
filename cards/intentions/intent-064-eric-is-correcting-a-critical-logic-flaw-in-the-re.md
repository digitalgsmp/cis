# Intention Card

**Intention:** Eric is correcting a critical logic flaw in the review workflow's idempotency check and result validation to prevent false rejections and ensure data integrity, while reinforcing the need for precise, context-aware validation in the CIS system.

**Mission Connection:** This exchange connects to the broader CIS mission by ensuring that the multi-agent validation pipeline correctly identifies and resolves logical inconsistencies in system behavior. By addressing the specific technical objections, Eric is reinforcing the system's ability to self-correct through rigorous, independent review and validation—key to the CIS goal of producing verified, reliable builds.

**What Was Learned:** The idempotency check must be scoped to the current round of review, not the entire proposal lifecycle, to avoid false rejections due to stale REVIEW_COMPLETE events. Additionally, the workflow_runs.result field must be constrained to valid outcomes based on the current workflow state, preventing invalid or ambiguous result assignments.

**Relevance to Frontier Model:** A frontier model like Claude or ChatGPT needs to understand that CIS relies on precise, context-sensitive validation logic to avoid systemic errors. This exchange reveals that the system must not only enforce constraints but also interpret them in the correct operational context—such as distinguishing between lifecycle-wide and round-specific events—demonstrating the importance of contextual awareness in AI-driven validation.

**Category:** infrastructure

**Session:** api-8a0873a6a223f488
**Date:** 2026-06-17 07:59

**Verbatim Quotes:**
- "The OTHER reviewer (R1) had these objections in the previous round. Address each one, then re-evaluate:"
- "Idempotency check in §6.2 step 6 queries COUNT(*) WHERE to_state='REVIEW_COMPLETE' globally per proposal_id. After a revision round, round 1's REVIEW_COMPLETE event persists. When round 2 reaches REVIEWING and reviewer_closeout.py runs step 6, it finds the stale REVIEW_COMPLETE from round 1 and refuses closeout. Fix: scope the check to the current round by verifying the most recent lifecycle event's to_state is not already REVIEW_COMPLETE, or check that no REVIEW_COMPLETE exists with id > the most recent DRAFTING event."
- "workflow_runs.result has NOT NULL CHECK (result IN ('CONSENSUS_REACHED','ESCALATE','ERROR')). §6.2 step 16 always sets result=?, but for OBJECTIONS-with-remaining-ro"
