# Intention Card

**Intention:** Eric was trying to enable context-aware, multi-turn conversation handling in the advisor agent by injecting prior message history into each API call, ensuring agents can maintain coherent dialogue across interactions.

**Mission Connection:** This connects to the broader CIS mission by enhancing the control plane's ability to manage multi-agent workflows with persistent context, enabling agents to reason over prior exchanges and route appropriately—key to building a self-correcting, review-driven system.

**What Was Learned:** The system must preserve and inject conversation history in a standardized format to support stateful interactions, and the advisor agent must be updated to dynamically construct messages based on thread context rather than treating each request in isolation.

**Relevance to Frontier Model:** Frontier models need to understand that context injection is not just a coding task but a foundational requirement for enabling coherent, long-term agent collaboration within CIS, where each agent must reason over prior decisions and validate against historical intent.

**Category:** infrastructure

**Session:** prime:20260521_004014_161f67
**Date:** 2026-05-21 00:40

**Verbatim Quotes:**
- "Modify /mnt/projects/cis/runtime/api/advisor.py to add thread history injection and auto-routing between agents."
- "Add a `get_thread_history(thread_id)` helper function that: Queries all advisor_messages for the thread, ordered by message_index, Returns them as an OpenAI-format messages list: [{role: "user"|"assistant", content: "..."}], Skip the current message (the one we're about to send) — only include prior messages, Max last 20 messages to avoid blowing context."
- "Modify the `chat()` function: Before calling the gateway, build messages list by first calling get_thread_history(), then appending the current user message, Pass this full message list to the gateway instead of just the single message, After saving the assistant response an [truncated]"
