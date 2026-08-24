# Intention Card

**Intention:** Eric is correcting a UI design decision to improve usability and maintain consistency with existing interface patterns by moving a control element out of an interactive input area and into a more appropriate, non-intrusive location.

**Mission Connection:** This aligns with the CIS mission of ensuring that all system components are validated against documented intentions and design principles, particularly in how user interfaces are structured to avoid interference with core functionality. By correcting the placement of the copy button, Eric reinforces the importance of interface clarity and user experience as part of the broader goal of building a reliable, self-correcting multi-agent system.

**What Was Learned:** The copy button should not be placed within the terminal container where it obstructs input; instead, it should be relocated to the page header, consistent with other UI controls like the mobile panel toggle. This confirms that interface layout decisions must be validated against both functional and ergonomic standards.

**Relevance to Frontier Model:** Frontier models need to understand that UI design decisions are not isolated but must align with established patterns and user behavior. This exchange shows that even small interface elements must be evaluated for their impact on usability and integration with the overall system architecture, which is critical for building a cohesive, user-centered system.

**Category:** cis

**Session:** prime:20260509_185113_7ebdea
**Date:** 2026-05-09 18:51

**Verbatim Quotes:**
- "why is it in the prompt, can't it live in the header or somewhere else out of the way?"
- "You're absolutely right. The button sits at `bottom-2 right-2` inside the terminal container — right where the cursor/input line is. It should be in the page header instead, alongside the mobile panel toggle that's already registered via `setEnd`."
