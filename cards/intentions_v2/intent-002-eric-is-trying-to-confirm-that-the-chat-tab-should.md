# Intention Card

**Intention:** Eric is trying to confirm that the Chat tab should be accessible by default in the Hermes dashboard without requiring the --tui flag, and he is seeking validation that the current behavior is intentional or a bug.

**Mission Connection:** This exchange connects to the CIS mission by highlighting the need for consistent and intuitive user experience across the control plane portal. As the conductor of the multi-agent system, Eric must ensure that the interface tools (like the Hermes dashboard) are reliable and aligned with documented workflows, enabling seamless routing between AI agents and validation processes. A missing or hidden feature undermines trust in the system’s integrity and usability.

**What Was Learned:** The Chat tab is intentionally hidden unless the dashboard is launched with the --tui flag, which suggests a design choice to separate TUI-based interaction from the web interface. This clarifies a configuration boundary in the system, but also reveals a potential usability gap that may affect Eric’s ability to conduct real-time agent interactions through the portal.

**Relevance to Frontier Model:** Claude/ChatGPT needs to understand that the Hermes dashboard is part of a larger control plane ecosystem where interface behavior must align with user expectations and operational workflows. This exchange shows that even minor UI inconsistencies can disrupt the conductor’s ability to route and validate agent outputs, so frontier models must account for both technical design and human-in-the-loop usability in CIS architecture.

**Category:** portal

**Session:** prime:20260509_095016_c82fc8
**Date:** 2026-05-09 09:50

**Verbatim Quotes:**
- "The chat tab is missing from the Hermes dashboard at http://127.0.0.1:9119."
- "The Chat tab is gone."
- "Diagnose and fix this."
