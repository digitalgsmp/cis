# Intention Card

**Intention:** Eric is establishing a prerequisite governance rule: legacy database systems must be formally triaged (archived, absorbed, or read-only) before any schema changes are applied to the active application database, to prevent architectural drift and ensure system integrity.

**Mission Connection:** This aligns with the CIS mission of building a robust, self-validating multi-agent pipeline where AI models enforce structural consistency and prevent unverified changes from propagating. By mandating a pre-schema-change triage process, Eric is embedding a governance checkpoint that ensures all future builds are validated against a stable, well-understood data foundation.

**What Was Learned:** The legacy database (cis_memory.db) is not just a data store but a critical system component with historical and operational dependencies. Its status must be formally resolved before any new schema changes are introduced, or it risks becoming a source of conflict or inconsistency in the integrated system.

**Relevance to Frontier Model:** Frontier models like Claude or ChatGPT need to understand that CIS is not just about building features, but about enforcing a disciplined, audit-ready architecture. They must recognize that database schema changes are not isolated events but require upstream validation and governance, especially when dealing with legacy systems.

**Category:** governance

**Session:** r1:api-2cac3796e7325b36
**Date:** 2026-05-24 12:18

**Verbatim Quotes:**
- "the legacy DB (34 tables, knowledge spines, collab rounds) must be triaged — archived, absorbed, or left as read-only — before the schema changes land"
- "Add idea_drafts.promoted_project_id TEXT (runtime DB) — cross-DB bridge"
