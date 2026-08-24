# Intention Card

**Intention:** Eric is correcting a UI design decision to improve usability and maintain consistency with existing interface patterns by relocating a button from an obstructive position to a more appropriate location in the page header.

**Mission Connection:** This aligns with the CIS mission of building a robust, user-centered system where AI models validate design choices against documented intentions and established UI patterns, ensuring that components are not only functional but also intuitive and non-disruptive to user workflows.

**What Was Learned:** The placement of interactive elements within a terminal interface must respect both user input flow and visual hierarchy; positioning controls in the terminal container can interfere with user interaction, while placing them in the page header maintains consistency and usability.

**Relevance to Frontier Model:** Frontier models must understand that UI decisions are not isolated but must align with broader design principles and user experience goals. They should be able to assess component placement not just for technical feasibility but for contextual appropriateness and user-centric design.

**Category:** cis

**Session:** prime:20260509_185113_7ebdea
**Date:** 2026-05-09 18:51

**Verbatim Quotes:**
- "why is it in the prompt, can't it live in the header or somewhere else out of the way?"
- "You're absolutely right. The button sits at `bottom-2 right-2` inside the terminal container — right where the cursor/input line is. It should be in the page header instead, alongside the mobile panel toggle that's already registered via `setEnd`."
