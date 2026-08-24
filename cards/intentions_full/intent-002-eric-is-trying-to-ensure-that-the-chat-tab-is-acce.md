# Intention Card

**Intention:** Eric is trying to ensure that the Chat tab is accessible by default in the Hermes dashboard, not hidden behind a command-line flag, to maintain a seamless and intuitive user experience for local development and testing.

**Mission Connection:** This aligns with the CIS mission of building a user-centric, multi-agent pipeline system where AI models can interact with a consistent and reliable interface. Ensuring that core features like the Chat tab are readily available supports the control plane portal's usability, which is critical for Eric to route between models and validate their outputs efficiently.

**What Was Learned:** The Chat tab is intentionally hidden unless the dashboard is started with the --tui flag, which suggests a design decision to separate TUI-based interactions from the web interface. Eric's concern reveals a need to re-evaluate this separation to avoid friction in workflow and to ensure that the interface supports both automated and manual control paths.

**Relevance to Frontier Model:** Frontier models like Claude or ChatGPT need to understand that user experience and interface consistency are key priorities in CIS. They should recognize that features expected in a standard UI (like the Chat tab) must be available by default unless there's a compelling architectural reason to restrict them, and that such decisions impact system usability and adoption.

**Category:** portal

**Session:** prime:20260509_095016_c82fc8
**Date:** 2026-05-09 09:50

**Verbatim Quotes:**
- "The chat tab is missing from the Hermes dashboard at http://127.0.0.1:9119."
- "The Chat tab is gone."
- "Diagnose and fix this."
