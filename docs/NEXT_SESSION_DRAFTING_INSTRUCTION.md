# Next Session Drafting Instruction

## Task
Draft `docs/TASK_CONTRACT_ENFORCEMENT_PRIMITIVE_V1.md`.

**Scope:** DRAFT ONLY. Do not implement. Do not create /opt/cis-control/. Do not modify hooks, configs, gates, DB schema, Docker settings, or any live enforcement files. This is a proposal for Claude + ChatGPT audit and Eric approval before implementation.

## Verified Premise
- Docker 29.6.0 installed. Container with /mnt/projects/cis mounted read-only refused write to breach.txt — "Read-only file system", exit 1. Host confirmed no breach file.
- Caveat: user eric is not in docker group (correct). Docker invocation requires sudo/root-orchestrated CIS control-plane launcher.

## Architecture (settled — conform, don't redesign)
Three-layer process isolation:
1. **CIS control plane** — owns hooks, policy checker, task templates, frozen contracts. Lives at /opt/cis-control/, root-owned, mounted READ-ONLY into worker container.
2. **Hermes worker** — executes inside Docker, reads context + contract + tools, writes ONLY to workspace.
3. **Workspace** — /mnt/cache/catalog/<run_id>/ — the only writable mount.

Source roots (/mnt/archive, /mnt/projects/cis, /mnt/projects/swa) mounted read-only. Docker provides kernel-level filesystem wall. Hook provides per-action policy on top.

## Trust Root (load-bearing — enforce all)
- Constrained agent cannot author its own contract. Valid authors: Claude API proposal validated by deterministic local compiler against fixed template; Eric directly; prior approved DB row.
- Compiler REJECTS proposals widening paths/tools beyond template. Descriptive fields only (labels, intent summary, risk notes). Paths, tools, deny-list from template, hardcoded.
- Enforcement files live OUTSIDE any path the worker can write (/opt/cis-control, not CIS repo).
- Worker cannot launch Docker (eric not in docker group; control plane launches containers).

## Spec Must Include

1. **Problem statement:** 16 failures are LLM behavior failures, not future app features. Prompt/SOUL/profile instructions insufficient (agent can ignore/mutate them). Inventory is the proving ground.

2. **SOUL/skills split:** procedural knowledge stays in agent context; enforcement rules move to external policy layer. State which is which.

3. **Three-layer model** with /opt/cis-control layout.

4. **Contract format:** task_id/run_id, original Eric intent, interpreted task class, contract author, contract hash, allowed tools, allowed read paths, allowed write paths, denied write paths, evidence_required, candidate_required, review_required, reviewer target, release behavior, completion condition, override behavior, created_at/expires_at.

5. **Fixed inventory_catalog template** (hardcoded boundary).

6. **Hook logic:** thin. Check override FIRST, verify contract hash, extract tool+target+cwd, call deterministic policy checker, exit 0/1. Zero policy in the hook itself.

7. **Override plane:** `.GATE_DISABLED` checked first by hook, testable from bare shell. Explain how this prevents the v2.0 deadlock. Override plane built/tested BEFORE hook is trusted — step zero.

8. **Fail-mode policy:** what happens if policy checker crashes. Separate dev/proving mode from enforcement mode. State fail-open vs fail-closed for each. Bare-shell override must always recover.

9. **Adversarial review:** hook does NOT judge answer quality. Reviewer (Claude API) checks alignment with intent, evidence, constraints, contradiction. Reviewer is NOT the constrained agent. Accept → reconciled; reject → loops back with objection. State explicitly: hook alone does not solve the 16; reviewer required for quality.

10. **Docker invocation:** exact mount table (RO source roots, RO /opt/cis-control, RO frozen contract, RW workspace only). Container launched by control plane, not worker.

11. **Acceptance tests (deterministic):**
    - override disables enforcement from bare shell
    - allowed write passes
    - forbidden write blocks (kernel AND policy)
    - forbidden tool blocks
    - answer without required evidence blocks release
    - evidence exists but no candidate row blocks release
    - candidate exists but review pending blocks release
    - rejected review loops back
    - accepted review releases
    - compiler REJECTS proposal requesting /mnt/projects/cis as writable
    - worker cannot edit contract/hook/policy/template (EROFS)
    - hook-crash behavior matches selected fail-mode

## Out of Scope
- Judging answer quality in the hook
- Claiming this solves all 16 alone
- Full UI
- Full catalog extraction
- Profile migration
- Removing the reviewer

## Final Line
"This is a proposal for Claude + ChatGPT audit and Eric approval before implementation."

## Authorship Rule (do not violate)
Hermes is drafting the spec for a cage that constrains Hermes. That's fine for a draft (proposing, not authoring the live contract), but the draft goes through review — Claude audit, ChatGPT audit, Eric approve — before any of it becomes actual /opt/cis-control/ files. The constrained agent proposing its own constraint spec is acceptable; the constrained agent writing the live enforcement files is not.
