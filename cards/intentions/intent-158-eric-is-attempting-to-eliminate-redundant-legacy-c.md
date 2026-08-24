# Intention Card

**Intention:** Eric is attempting to eliminate redundant, legacy code in the pipeline relay system to improve maintainability and align with the CIS architecture's modular, containerized design.

**Mission Connection:** This aligns with the CIS mission of building a multi-agent pipeline system where code is validated, consolidated, and enforced through containerized components. By removing legacy code, Eric is ensuring that the system remains clean, scalable, and consistent with the control plane's intended structure, which supports the long-term goal of automated, self-correcting system validation.

**What Was Learned:** The legacy relay code in app.py is no longer necessary because the production relay functionality is already implemented in api/relay.py. This confirms that the system has evolved beyond its initial state and that redundancy must be actively removed to maintain integrity.

**Relevance to Frontier Model:** A frontier model like Claude or ChatGPT needs to understand that Eric is not just requesting a code change, but is enforcing a governance principle: eliminate redundancy and align with the system's architectural vision. This ensures that any future model-generated code adheres to the CIS design philosophy of modularity, validation, and containerized enforcement.

**Category:** infrastructure

**Session:** glm-verifier:api-a0a2a6174ae15743
**Date:** 2026-07-08 13:43

**Verbatim Quotes:**
- "# TODO: Legacy inline pipeline relay code at lines 794-917 (PIPELINE_RUNS dict, portal_pipeline_start, portal_pipeline_status) should be consolidated into api/relay.py or removed — the production relay blueprint at api/relay.py already handles intent submission, status polling, gates, and verification."
