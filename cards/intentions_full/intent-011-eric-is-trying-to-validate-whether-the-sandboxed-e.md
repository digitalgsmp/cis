# Intention Card

**Intention:** Eric is trying to validate whether the sandboxed environment is necessary for DeepSeek to function correctly within the CIS system, and he is seeking confirmation that removing the sandbox will not compromise the system's integrity or performance.

**Mission Connection:** This exchange connects to the broader CIS mission by ensuring that the control plane portal and containerized enforcement mechanisms are aligned with the actual operational needs of AI agents. By questioning the necessity of the sandbox, Eric is evaluating the balance between security/containment and functional efficacy, which is central to the governance and infrastructure design of CIS.

**What Was Learned:** The sandbox environment is not required for DeepSeek to operate effectively within the CIS framework, and removing it allows for direct access to the real project root, enabling proper MCP integration and workflow execution.

**Relevance to Frontier Model:** Claude/ChatGPT need to understand that the CIS system must support flexible, context-aware execution environments—where security boundaries can be adjusted based on operational requirements without compromising system integrity. This insight informs how frontier models should design and validate agent workflows in multi-agent systems.

**Category:** infrastructure

**Session:** prime:20260512_163833_7ac9d8
**Date:** 2026-05-12 16:39

**Verbatim Quotes:**
- "make that change"
- "I think chatgtp insisted on sandboxing deepseek when I first tried to set it up. what happens if the sandbox is removed. is the sandbox the way deepseek is meant to run to do the work I need?"
