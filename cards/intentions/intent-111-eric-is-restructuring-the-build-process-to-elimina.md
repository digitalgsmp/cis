# Intention Card

**Intention:** Eric is restructuring the build process to eliminate runtime defeatable surfaces by sealing all configuration and hook scripts at build time, ensuring that no critical components can be modified after the image is built.

**Mission Connection:** This aligns with the CIS mission of creating a secure, containerized enforcement system where all components are validated and sealed during build, preventing runtime tampering and ensuring integrity across the pipeline.

**What Was Learned:** The current system allows runtime modification of config.yaml, .env, and the hook script via in_container.sh, which creates a security vulnerability. By moving these components into the build process and sealing them, Eric is closing a critical defeatable surface.

**Relevance to Frontier Model:** A frontier model must understand that CIS prioritizes security through immutability and build-time sealing. This exchange reveals that runtime configuration is a high-risk area that must be eliminated in favor of sealed, verified artifacts.

**Category:** container

**Session:** v4pro:20260625_025701_daed90
**Date:** 2026-06-25

**Verbatim Quotes:**
- "The current Dockerfile seals the plugin correctly but never bakes or seals config.yaml, .env, or the hook script."
- "Those are all written at runtime by the worker in in_container.sh — the defeatable surface."
- "All config setup moves into the build as the worker, then root seals the directories."
- "The hook script moves out of /tmp into a root-owned path."
