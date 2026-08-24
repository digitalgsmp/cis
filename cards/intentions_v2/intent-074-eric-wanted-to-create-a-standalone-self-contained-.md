# Intention Card

**Intention:** Eric wanted to create a standalone, self-contained web chat interface that connects directly to the Hermes Gateway API without relying on or modifying the existing CIS UI or infrastructure.

**Mission Connection:** This aligns with the CIS mission of enabling modular, containerized, and independently verifiable components. By requesting a standalone web chat, Eric is emphasizing the need for isolated, testable systems that can be validated independently and integrated later, supporting the multi-agent validation and control plane architecture.

**What Was Learned:** Eric is focused on maintaining separation between the control plane (CIS UI) and the functional components (like the chatbot). He wants to avoid unintended dependencies and ensure that each system component can be built, tested, and validated in isolation before integration.

**Relevance to Frontier Model:** A frontier model must understand that Eric is not just requesting a chatbot, but a design pattern that supports modularity, containerization, and independent validation—core principles of the CIS system. This ensures future models can build components that align with the system’s governance and integration standards.

**Category:** infrastructure

**Session:** prime:20260519_002121_fa2a56
**Date:** 2026-05-19 00:23

**Verbatim Quotes:**
- "can you create a chatbot in my ui where I can use my deepseek api to chat with hermes"
- "ok but that is talking to deepseek model, I am askinf can I control hermes through a webui"
- "ok the is a chat page on the ui, build a webchat using that port"
- "leave all of that stuff alone and only build what I am asking you. as a matter of fact stay away from the ui and build a stand alone web chat that connects with hermes."
- "build it"
