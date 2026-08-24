# Intention Card

**Intention:** Eric is establishing a foundational integration between the React Flow UI and the CIS database to ensure graph persistence and statefulness, while also defining a structured UI architecture that supports the kernel workbench's multi-panel navigation and future domain expansions.

**Mission Connection:** This aligns with the CIS mission of building a multi-agent pipeline system where AI models validate and produce verified builds through a persistent, stateful, and modular architecture. By making the React Flow UI database-backed and integrating it with the workbench navigation, Eric is enabling a system where agents can interact with a shared, evolving knowledge graph that supports both real-time updates and long-term data integrity.

**What Was Learned:** The React Flow UI currently uses hardcoded node templates, which limits scalability and persistence. The system must evolve to support dynamic data flow between the UI and the CIS database, enabling agents to create, modify, and retrieve graph elements in a coordinated way. This also sets the stage for future integrations like calendar events, search, and real-time knowledge extraction.

**Relevance to Frontier Model:** Frontier models like Claude or ChatGPT need to understand that the CIS system is not just about building a UI, but about creating a persistent, agent-validated knowledge environment. They must prioritize database integration, state management, and modular UI design when proposing solutions, ensuring that their outputs align with the system's long-term vision of self-correcting, multi-agent collaboration.

**Category:** cis

**Session:** prime:20260515_091520_2fe8d4
**Date:** 2026-05-15

**Verbatim Quotes:**
- "Align React Flow to CIS DB — nodes are still hardcoded template objects. They need to read/write to a `maps` table (or equivalent) so the graph is persistent and stateful."
- "Rebuild UI around React Flow — kernel workbench nav tabs (Ideas, Session, Map, Project, etc.) integrated as panels around the graph."
- "Open source calendar — FullCalendar integration, drag nodes → events"
- "Work domain → SWA — expanding the domain model, SWA under Work"
