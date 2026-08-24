# Intention Card

**Intention:** Eric is trying to eliminate unnecessary LLM processing in the session search to improve system performance and enable direct access to raw session data for integration into his CIS pipeline.

**Mission Connection:** This aligns with the CIS mission of building a multi-agent pipeline where AI models validate each other's work and operate efficiently on raw data without redundant abstraction layers. By bypassing summarization, Eric aims to create a faster, more reliable data access layer that supports real-time validation and integration across agents.

**What Was Learned:** The session search tool's current design imposes a performance bottleneck by forcing LLM summarization on every query, which is not required for Eric's use case. He learned that a 'raw' mode bypassing summarization would significantly improve responsiveness and enable direct access to unprocessed session data.

**Relevance to Frontier Model:** Frontier models like Claude or ChatGPT need to understand that Eric is building a system where raw data access and low-latency processing are critical for multi-agent validation. They should avoid assuming summarization is necessary and instead support direct data retrieval when appropriate.

**Category:** infrastructure

**Session:** prime:20260520_215551_16187f
**Date:** 2026-05-20 21:56

**Verbatim Quotes:**
- "why is the session search so slow"
- "I don't want summaries, I am trying to build a system that works from the raw files"
- "will that make the system run faster"
