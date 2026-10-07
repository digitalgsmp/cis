# CIS Architecture Reconstruction — Independent External Review & Phase Handoff — 2026-10-07

**AUTHORITY CLASS: LAYER-2 EXTERNAL REVIEW EVIDENCE / ARCHITECTURAL SYNTHESIS.**

This artifact is **not** an ADR, **not** Seed Intent, **not** project-state
authority, **not** queue authority, **not** implementation authorization, **not**
a replacement for the underlying evidence it interprets, and **not** an
authorization to reconstruct CIS. Nothing in Part A becomes authoritative by
appearing here. Part B records which of its propositions already have authority,
which are evidence only, and which require an explicit architectural decision.

Layer-1 authority remains `project_decisions`, `project_state`, `open_questions`,
`queue_items`/`queue_edges` and `dev_continuity_events` in the spine
(`CIS_CONTEXT_CONTRACT.md` "Two-Layer Knowledge System"; ADR-PIPE-006).

---

## Provenance

| | |
|---|---|
| Author / reviewer | **Independent ChatGPT external reviewer** (external advisor-deliberator role, AGENTS.md §11.6) |
| Transported by | Eric (architect) — pasted into Claude Code for sanctioned durable recording |
| Recorded by | Claude Code (`claude-opus-5`), implementation agent — **not** an independent reviewer |
| Date | 2026-10-07 |
| Phase | post-P0 / pre-architecture-freeze / pre-reconstruction |
| Measured at SHA | `bf01df4d45a9de8981c2d057cf629e4cd24ba514` (local HEAD = `origin/master` = `git ls-remote` origin master; all three agree) |
| Authority class | **evidence** (`external_dev_handoffs` family, `config/kb_source_policy.yaml`) |
| Relationship to authority | **interpretive / synthetic, not substitutive** |
| Reference environment | `/mnt/projects/cis` — PROTECTED. Nothing deleted, cleaned, reorganized or reconstructed. |

**ChatGPT did not write to CIS.** ChatGPT has no write path into this
repository or spine. The synthesis below was produced in a ChatGPT conversation,
carried into Claude Code by Eric, and recorded here through the sanctioned
external-development handoff structure. The recording agent did not author the
architectural content and has not independently verified its judgements — only
its live-state claims, which are checked in "Live state at preservation time"
below.

### Source context — the underlying evidence this synthesis interprets

This document **points at** the following rather than duplicating them. They
remain the evidence; this is the reasoning that connects them.

| Source | Path / record |
|---|---|
| Deep architecture handoff (the material ChatGPT reviewed) | `data/agent_handoffs/ARCH-RECOVERY-01-three-plane/CIS_DEEP_ARCHITECTURE_HANDOFF_FOR_CHATGPT.md` |
| Architecture recovery independent review packet | `data/agent_handoffs/ARCH-RECOVERY-01-three-plane/ARCHITECTURE_REVIEW_PACKET.md` |
| KB integrity addendum (blocking finding) | `data/agent_handoffs/ARCH-RECOVERY-01-three-plane/ADDENDUM_02_KB_INTEGRITY.md` |
| KB source coverage & development-history recovery report | `data/agent_handoffs/KB-COVERAGE-01/KB_SOURCE_COVERAGE_AND_DEVELOPMENT_HISTORY_RECOVERY_REPORT.md` |
| Coverage matrix (regenerable) | `data/agent_handoffs/KB-COVERAGE-01/coverage_matrix.{json,txt}` |
| Architecture recovery opened | `dev_continuity_events` task WB.1 revision **126** |
| Trust-boundary exposure (live blocker) | `dev_continuity_events` revision **127** |
| Architecture recovery result | revision **128**; abstraction-plane addendum **130** |
| KB integrity audit | revision **131** |
| Deep architecture handoff ready | revision **132** |
| KB coverage recovery result | revision **133**, reconciliation **134** |
| P0 closure + independent remote acceptance | revisions **121**, **122**, **123**, **125**; `project_state.external_dev_checkpoint` |
| WIASW destination specification | `project_decisions` ADR-WIASW-001 … ADR-WIASW-006 |
| Layer ownership | ADR-SEED-018 |
| External-development durability | ADR-XDEV-001, ADR-XDEV-002 |
| Two-layer knowledge model | `docs/CIS_CONTEXT_CONTRACT.md` §"Two-Layer Knowledge System" |
| KB source policy (single declaration) | `config/kb_source_policy.yaml` |
| KB coverage gate | `tools/gates/gate_kb_source_coverage.py` |
| KB ingestion provenance | `runtime/manifests/KB_SOURCE_MANIFEST.json` |

---

## Live state at preservation time

Read live on 2026-10-07, not inherited from the KB recovery report. The report
measured `bf01df4d45a9de8981c2d057cf629e4cd24ba514`; **that SHA is still
authority**, so the external review's premises hold. Four differences from the
report's snapshot are recorded, none of which changes the architectural position.

| Dimension | Live value |
|---|---|
| HEAD | `bf01df4d45a9de8981c2d057cf629e4cd24ba514` |
| branch | `master` |
| `origin/master` | `bf01df4d45a9de8981c2d057cf629e4cd24ba514` |
| remote `refs/heads/master` (`git ls-remote`) | `bf01df4d45a9de8981c2d057cf629e4cd24ba514` |
| working tree | **DIRTY** — 17 modified, 10 untracked (see below) |
| P0 | COMPLETE AND CLOSED (2026-10-06); `bf01df4d` independently `REMOTE_VERIFIED` (rev 125, `project_state.external_dev_checkpoint`) |
| P1 | **NOT ACTIVATED**. Sequence unchanged: P0 closed → queue triage (blocked on OQ-TRIAGE-001) → independent review of triage → P1 |
| queue | 133 items; **0 unclassified** (`need_status`: OPEN 91, DONE 15, UNASSESSED 11, NEEDS_ERIC 8, HALF_DONE 6, NO_CHECK_WRITTEN 1, UNCLEAR 1) |
| architecture recovery | OPEN — revision 126, result at 128, addendum at 130 |
| KB recovery | **RECORDED AND CLOSED as PARTIAL** — revision 133, reconciled at 134 (the report's own snapshot predated this) |
| revision-127 trust boundary | **STILL OPEN AND BLOCKING** — no reconciliation exists against revision 127; it remains in `closeout-check`'s blocker set |
| reconstruction | NOT BEGUN, NOT AUTHORIZED |
| latest continuity revision | **134** |

### Differences from the KB recovery report's snapshot

1. **Continuity has advanced from 131 to 134.** The KB recovery's own result
   (133) and reconciliation (134) now exist. The report was written before its
   own durable record landed. No architectural claim changes.
2. **The KB recovery work is uncommitted.** `config/kb_source_policy.yaml`,
   `tools/kb/`, `enforcement/mwl-proof-v2/gates/gate_kb_source_coverage.py`
   (reached as `tools/gates/` via symlink) and
   `runtime/manifests/KB_SOURCE_MANIFEST.json` are untracked or modified in the
   working tree. The mechanism is live and measurable on this host; it is **not
   in the pushed tree**, so it is not independently verifiable from the remote
   under ADR-XDEV-001. This is a real gap in the KB recovery's durability, not a
   finding of this card, and it is returned rather than fixed.
3. **The coverage gate is currently RED** (`GATE FAIL`, exit 1) — and
   permanently so. All four measurable required families are at 100%; the two
   failing families are `chatgpt_sessions` and `claude_ai_sessions`, whose only
   violation is `INGESTION PATH MISSING — ARCHITECTURE DECISION REQUIRED`. This
   is the permanently-red-gate condition Part IX of the governing card warned
   against, observed live. See "Returned decisions", item R3.
4. **`external_dev_handoffs` has grown** from the 236 files the report measured
   to 238 (the report updated itself at 07:34 on 2026-10-07). Coverage is 100%
   at both counts.

---

# PART A — VERBATIM INDEPENDENT ARCHITECTURE HANDOFF

Preserved from the independent ChatGPT external review of 2026-10-07.
Formatting is adapted to repository Markdown conventions. **The architectural
claims, distinctions, unresolved decisions and sequencing are unchanged.**

> Everything from here to the end of Part A is the external reviewer's text, not
> the recording agent's, and not CIS authority.

---

## A1. Executive orientation

CIS should not be reconstructed as a cleaner copy of the current filesystem.

The reconstruction objective is:

> **Reconstruct CIS so its existing intended boundaries become mechanically
> true, while preserving verified capabilities and making execution backends,
> models, providers, interfaces, and future WIASW applications replaceable
> behind CIS-owned contracts.**

The existing `/mnt/projects/cis` environment should remain the reference /
archaeological implementation until a reconstructed CIS proves sufficient
equivalence and accepted migration criteria.

The reconstruction should recover **capabilities and contracts**, not copy
historical directory structure and then delete unwanted material.

---

## A2. What CIS fundamentally is

The accumulated architecture and WIASW destination evidence indicates that CIS
is fundamentally a **deterministic governed substrate that converts high-level
human intent into bounded, inspectable, evidence-producing execution**.

The durable conceptual chain is:

```
HUMAN INTENT
    ↓
INTERPRETATION
    ↓
AUTHORITATIVE CONTEXT
    ↓
PROJECT STATE
    ↓
WORK DECOMPOSITION
    ↓
POLICY / GOVERNANCE
    ↓
EXECUTION CONTRACT
    ↓
REVIEW / AUTHORIZATION
    ↓
GOVERNED EXECUTION
    ↓
EVIDENCE
    ↓
EVALUATION
    ↓
PROJECT-STATE ADVANCEMENT
```

LLMs, harnesses, providers, gateways and creative applications **participate in**
that system. They are not themselves the durable definition of CIS.

---

## A3. Do not create a new competing three-plane architecture

The architecture recovery found multiple different historical three-part
decompositions.

Therefore: **Control Plane / Hermes Backend / CIS Infrastructure must NOT
automatically become a new competing top-level architecture.**

The recovered authoritative dependency model in **ADR-SEED-018** should remain
the starting architectural constraint unless superseded through formal decision.
Its essential dependency pattern is:

```
L1 — CIS UI / CONTROL SURFACE
          ↓
L2 — CIS-OWNED ABSTRACTION / CONTROL BOUNDARY
          ↓
L3 — REPLACEABLE EXECUTION INFRASTRUCTURE
```

Dependency/ownership architecture and deployment/trust topology are **different
dimensions**. Do not force both into the same three boxes.

---

## A4. Layers versus trust / deployment domains

A future CIS module should be describable using properties such as:
architectural layer; responsibility; trust domain; authority relationship;
inputs; outputs; permitted dependencies; forbidden dependencies; mutation
rights; execution location; failure domain; recovery behavior; replacement
contract.

This allows a component to belong to an architectural layer **while executing
inside a particular security/deployment domain**.

Do not create another hierarchy merely to represent deployment. Use
topology/trust metadata unless evidence demonstrates that a separate
authoritative hierarchy is necessary.

---

## A5. Hermes is an implementation, not the permanent definition of the backend

Recovered architecture establishes that Hermes was intended to be **replaceable
execution infrastructure behind a CIS-owned abstraction**. The durable boundary
is more important than Hermes itself.

Hermes currently implements L3 execution capability. CIS should not require
Hermes-specific behavior to leak upward into authority, policy, UI,
project-state logic or destination applications.

The current system **fails the intended abstraction in measured ways**,
including:

- Hermes source patches;
- expanded / multiple install topology;
- an adapter marked complete but not actually registered in the authoritative
  live path;
- direct reading of Hermes private `.env` and `config.yaml`;
- parsing Hermes log files to infer runtime liveness;
- hard-coded gateway assumptions.

These are **architectural coupling points**, not merely directory-cleanliness
issues.

---

## A6. Hermes replaceability acceptance test

The immediate boundary test should remain:

> **Can Hermes be updated to a current supported release without changing
> CIS-owned runtime code and without reapplying Hermes source patches?**

The present answer is **no**.

The eventual generalized test should be:

> **Can a different execution harness satisfy a stable CIS-owned
> execution-backend contract without redesigning CIS authority, policy, UI,
> project state or destination logic?**

That generalized contract is a **future architecture decision**. Do NOT pretend
it already exists merely by documenting it. A contract above a backend that
cannot actually be swapped is documentation, not a proven boundary.

---

## A7. DeepSeek Harness

DeepSeek Harness has been identified by Eric as a potentially significant
emerging alternative to Hermes, although it is currently beta.

Current CIS evidence gives DeepSeek Harness **no architectural authority or
adoption status**. Therefore:

- do not install it as part of this handoff;
- do not migrate to it;
- do not redesign CIS around it;
- do not promote it to architecture merely because it exists.

Its immediate architectural value is as a **replaceability test case**.

When the execution-backend contract is eventually specified, the correct question
should be:

> «Can DeepSeek Harness satisfy the CIS execution-backend contract?»

not:

> «Should CIS be redesigned around DeepSeek Harness?»

The same should apply to future agent harnesses.

---

## A8. Execution backend conceptual direction

The architecture should be capable of evolving toward:

```
CIS AUTHORITY / POLICY / CONTROL
              │
              ▼
     CIS-OWNED EXECUTION CONTRACT
              │
              ▼
     EXECUTION ABSTRACTION
              │
       ┌──────┼─────────┐
       ▼      ▼         ▼
    HERMES  DEEPSEEK   FUTURE
    ADAPTER  HARNESS    HARNESS
       │     ADAPTER    ADAPTER
       ▼      │         │
    HERMES    ▼         ▼
           DEEPSEEK    ...
            HARNESS
```

This is a **conceptual destination to test against recovered authority**. It is
**NOT implementation authorization**.

ADR-WIASW-002 already permits future generalization toward CIS-owned stable
contracts above replaceable execution backends while explicitly **not**
authorizing a Hermes refactor. Preserve that distinction.

---

## A9. Module contract direction

CIS already contains mechanisms that should **inform** rather than be discarded
during reconstruction.

The **Task Contract Enforcement Primitive** already demonstrates concepts
including: declared inputs; declared outputs; allowed capabilities; forbidden
capabilities; constrained execution; deterministic refusal; separation between
worker and contract author.

WIASW architecture additionally introduces structured **Execution Contracts**
and **Tool Adapter Contracts**. These should inform a future common contract
vocabulary.

**Do NOT collapse every contract into one giant schema.** At minimum
distinguish:

**TASK / WORKER CONTRACT** — constrains what a governed worker may do.

**EXECUTION CONTRACT** — represents an authorized bounded unit of work.

**TOOL ADAPTER CONTRACT** — defines the governed interface to an external
application/tool.

**INTERNAL MODULE CONTRACT** — should eventually make explicit: module identity;
architectural layer; responsibility; inputs; outputs; authority read; authority
mutation; sanctioned interfaces; permitted dependencies; forbidden dependencies;
trust domain; evidence produced; failure behavior; recovery behavior;
replacement boundary.

The internal module contract is **not yet fully specified**. It should be
generalized from existing proven mechanisms rather than invented as another
governance subsystem.

---

## A10. WIASW is the destination, not the current implementation phase

The durable destination is **WORD · IMAGE · ACTION · SOUND + WEB**. CIS is the
governed substrate beneath that destination.

Future consumers may include: writing and research; image generation; ComfyUI;
Blender; Houdini; Unreal Engine; DaVinci Resolve; music/audio systems;
browser/computer-use systems; websites; web applications; social media; online
sales; productivity applications; future professional creative tools.

**Do not implement those during CIS reconstruction.** Use them as architectural
boundary tests.

---

## A11. General tool-adapter pattern

The destination architecture supports a pattern conceptually equivalent to:

```
WIASW APPLICATION
        ↓
       CIS
        ↓
CIS-OWNED STABLE TOOL CONTRACT
        ↓
APPLICATION-SPECIFIC ADAPTER
        ↓
API / SCRIPT / CLI / PROTOCOL / GUI
        ↓
EXTERNAL PROFESSIONAL APPLICATION
```

Prefer deterministic application interfaces where available. GUI/computer-use
operation remains **legitimate where necessary**, but should not replace
deterministic interfaces merely for convenience.

Hermes is therefore useful as the first major proof of the broader adapter
principle: **external capability must remain replaceable behind CIS-owned
contracts.**

---

## A12. Authority versus history

The recovered CIS Context Contract's two-layer distinction is essential.

**LAYER 1 — CURRENT TRUTH / AUTHORITY.** Answers «What is true now?» Includes
appropriate authoritative state such as: accepted decisions; Seed Intent;
project state; queue authority; current architecture decisions; accepted
verification state.

**LAYER 2 — HISTORICAL / CAUSAL EVIDENCE.** Answers «Why did we get here?»
Includes appropriate: development sessions; architecture handoffs; review
packets; reasoning history; implementation reports; historical investigation.

**Layer-2 evidence must not override Layer-1 authority merely because semantic
retrieval ranks it highly.**

The KB recovery demonstrated why both are necessary: **authority survived while
causality became inaccessible.**

---

## A13. KB recovery finding

The KB recovery confirmed Eric's concern. The problem was larger than a stale
document set.

Before recovery:

- only 7 of 70 Claude Code sessions were ingested;
- `data/agent_handoffs/` had never been a source family;
- review packets were absent;
- large portions of `cis_kernel` were absent;
- several recent architectural concepts had authority but no retrievable causal
  history;
- no ingestion mechanism was scheduled.

The recovery brought four measurable required source families to 100% coverage
with provenance: repository documentation; external-development handoffs;
`cis_kernel`; Claude Code sessions.

A deterministic coverage/staleness gate now exists.

The newly recovered material **confirmed or refined the major architecture
conclusions and contradicted none.** Therefore the architecture recovery remains
usable.

---

## A14. Remaining knowledge-system issues

The knowledge system is improved but **not finished**. Remaining issues include:

- ChatGPT browser history frozen at an old manual export;
- claude.ai browser history frozen at an old manual export;
- no automatic ingestion trigger;
- `advisor_loop` keyword-visible but semantically invisible;
- archive material dominating corpus volume;
- legacy ADR material capable of outranking current authority semantically;
- unresolved policy for raw Hermes sessions;
- unresolved policy for cards;
- retrieval quality/ranking not yet measured.

**Do not turn all of these into reconstruction blockers.** Separate *knowledge
integrity required to make the architecture decision* from *future
retrieval-quality improvements*. The recovered corpus is now sufficient for
architecture evaluation.

---

## A15. External session / handoff principle

Do not depend on Eric manually remembering which external conversations matter.
The durable pattern should become:

```
EXTERNAL DEVELOPMENT / REVIEW
              ↓
   DURABLE SESSION OR PHASE EVIDENCE
              ↓
     SANCTIONED HANDOFF SOURCE
              ↓
         KB INGESTION
              ↓
EXTERNAL-DEVELOPER COLD START / RETRIEVAL
```

Accepted decisions discovered through that process must be **promoted
separately** into Layer 1. Do not make raw conversations authority. Do not
require a comprehensive handoff after every ordinary conversation. Use
comprehensive handoffs at **meaningful phase or architecture boundaries**.

---

## A16. This handoff's role

This artifact is one such boundary checkpoint. It captures the synthesis reached
after: P0 completion; independent remote acceptance; deep architecture
archaeology; recovery evaluation; WIASW destination reconciliation; KB source
recovery; execution-harness abstraction analysis.

Future external developers should be able to use it to understand the
architectural position without Eric reproducing this ChatGPT conversation
manually. It should point to underlying evidence rather than replacing it.

---

## A17. Cards and execution contracts — proposition requiring decision

A significant architectural proposition emerged during the independent review:

> «Cards are an early manual projection of what CIS should eventually compile as
> structured Execution Contracts; cards themselves should not become
> architectural authority.»

The KB recovery found that this framing is currently present only as session
evidence and is **not established in durable authority**.

This proposition is consistent with the WIASW direction but **MUST NOT silently
become authoritative** merely because it appears in this handoff. It requires
explicit architectural disposition.

Recommended disposition for independent consideration: **PROMOTE THE PRINCIPLE,
NOT THE CURRENT CARD FORMAT.**

Potential principle:

> «Human- and model-readable task cards are projections of authoritative
> structured work/execution contracts. Durable work authority resides in
> structured CIS state/contracts; cards may initiate, display or transport that
> state but do not independently become authority.»

Do not record this as accepted unless the sanctioned decision mechanism and
current architecture-review process authorize doing so.

---

## A18. Workbench and Mermaid

Workbench/Mermaid should survive reconstruction. The recovery established that
CIS already has deterministic visualization behavior driven from authority.

**Do not create another manually maintained architecture-diagram system.**

Target principle:

> «DB / ADR / structured module and relationship records are truth; Workbench
> and Mermaid are generated lenses.»

Useful future views include: (1) executive architecture; (2) module
dependencies; (3) authority/data flow; (4) trust boundaries; (5)
database/schema abstraction; (6) KB/retrieval architecture; (7)
current-versus-intended architecture; (8) destination-extension architecture.

The **trust-boundary view** deserves relatively high priority because the
revision-127 exposure demonstrates its operational value.

Do not make a diagram another source of truth.

---

## A19. The ceremony problem

The architecture review does **NOT** conclude that independent review, evidence,
recovery, Eric Gate, constrained execution or authority ownership are
unnecessary. Those controls protect different failure modes.

The larger problem is:

> «the same underlying fact is sometimes represented manually in too many
> places.»

That creates: reconciliation work; stale projections; contradictory freshness;
duplicated bookkeeping; excessive handoff maintenance; human memory burden.

The reconstruction principle should therefore be:

> **«RECORD ONCE → DERIVE EVERYWHERE.»**

Remove duplicate representation and synchronization burden **before** removing
safeguards that protect distinct failure modes.

---

## A20. Automation test

The WIASW destination specification expects CIS increasingly to automate: state
retrieval; context assembly; decomposition; dependency checking; policy
selection; contract generation; tool selection; implementation; validation;
evidence collection; checkpoints; routine review; provenance; synchronization;
recovery.

Therefore:

> «Every recurring coordination action currently performed manually by Eric or
> an external developer should be examined to determine whether it is actually
> destination functionality waiting to become structured automation.»

Some current ceremony may be an early manual prototype of useful future
automation. Automate it rather than preserving the manual ritual. Other
duplicated representations should simply disappear.

---

## A21. Database / authority direction

Do not split databases merely because trust separation is needed. The immediate
requirement is to make the **enforcement boundary match the semantic authority
model**.

A governed worker should conceptually mutate authority through:

```
WORKER → SANCTIONED CIS MUTATION INTERFACE → AUTHORITY
```

not:

```
WORKER → DIRECT FILESYSTEM SQLITE WRITE
```

Use kernel/filesystem/container/process isolation as appropriate so declared
read-only behavior is actually enforced. Consider physical database separation
only if later evidence demonstrates it is necessary. **Do not create another
truth system casually.**

---

## A22. Security / trust boundary precedes reconstruction

The current architecture recovery identified a **live trust-boundary blocker at
continuity revision 127.** At the KB-recovery checkpoint it remained open.

The reported condition includes public reachability to the authoritative
listener and unauthenticated/fail-open paths.

**That must be remediated before clean reconstruction is authorized.** Security
containment of the reference implementation is not the reconstruction itself.
Treat it as the first prerequisite after this handoff is durably preserved.

---

## A23. Reconstruction sequence

Recommended sequence from this checkpoint:

**STEP 1 — PRESERVE THIS HANDOFF.** Complete this card.

**STEP 2 — REMEDIATE REVISION 127.** Close the live public trust-boundary
exposure. At minimum address the actual measured paths, including fail-open
authentication and inappropriate public reachability. Obtain evidence
appropriate to that distinct security failure.

**STEP 3 — REMOVE ERIC FROM ROUTINE KB INGESTION.** Implement the smallest
supported automatic mechanism. The KB recovery recommends considering a
session-end ingestion trigger, and the deterministic KB coverage gate joining
closeout checking. Do not build a new subsystem when a small trigger suffices.
Resolve the browser-product-history policy explicitly rather than maintaining an
impossible permanently-red gate.

**STEP 4 — ARCHITECTURE FREEZE DECISIONS.** Resolve the minimum decisions
required to reconstruct: exact internal module contract; architectural-layer
versus trust-domain representation; Hermes/L3 boundary; status/timing of
generalized execution-backend contract; cards-versus-structured-Execution-Contract
principle; any remaining authority/retrieval issue that would corrupt
reconstruction. Do not solve every future WIASW question.

**STEP 5 — AUTHORIZE CLEAN MODULAR RECONSTRUCTION.** Only after Steps 1–4.
Preserve `/mnt/projects/cis` as reference. Build the clean environment from
positively identified modules/contracts rather than copying everything and
deleting.

**STEP 6 — PROVE THE BOUNDARIES.** At minimum prove: authority remains
single-owner; worker mutation is enforced through sanctioned paths; projections
regenerate from authority; recovery works; external verification works; Hermes
boundary is materially improved; execution backend remains replaceable in
architecture; destination applications can attach through stable interfaces; no
new competing source of truth was created.

**STEP 7 — THEN RETURN TO PIPELINE BUILD.** Architecture recovery should not
become a permanent project phase. Once the corrected substrate is proven, resume
forward pipeline/WIASW development.

---

## A24. What must survive reconstruction

Preserve the capabilities/protections, not necessarily every current
implementation:

Seed Intent; accepted ADR authority; deterministic current-state authority;
queue/build authority; author ≠ verifier; pushed versus independently accepted
state distinction; recovery/cold-start capability; external-development
continuity; constrained task execution; evidence before completion claims;
fail-closed behavior where required; provider/model replaceability;
Hermes/execution-backend replaceability; generated projections; Workbench
architecture visibility; KB provenance; authority/history distinction;
security/trust boundaries; destination extensibility.

---

## A25. What should not automatically survive

Do not preserve something merely because it exists. Candidates requiring
justification include:

duplicate representations of current state; dormant authority-shaped tables;
superseded handoff mechanisms; manual synchronization; legacy ADR material
presented as current; historical scaffolding with no remaining failure mode;
provider-specific coupling above its adapter; Hermes-private configuration
dependencies in CIS logic; patched external source as a permanent integration
mechanism; manually maintained diagrams duplicating authority; prose parsing
used where structured state already exists; governance bookkeeping whose only
purpose is reconciling other governance bookkeeping.

**Preserve historical evidence even when the mechanism itself is retired.**

---

## A26. Clean-room principle

Do not begin by asking «Which files can we delete?»

Ask: **«Which positively identified capabilities, contracts, authorities and
protections constitute CIS?»** Then construct those in the clean environment.

The reference system remains available to prove behavior and recover missed
dependencies. A component left behind in the reference environment is not
automatically obsolete. A component copied into the new environment is not
automatically legitimate.

---

## A27. Destination extensibility test

The reconstruction should pass this conceptual test:

> Can future WIASW capabilities attach through stable CIS-owned interfaces
> without requiring changes throughout CIS core?

Examples: Blender; Houdini; Unreal; ComfyUI; DaVinci Resolve; audio/music
systems; browser/computer control; websites; web applications; social
platforms; commerce; productivity software; future execution harnesses.

**If each new tool requires edits across authority, orchestration, security and
UI internals, the modular boundary has failed.**

---

## A28. Current architectural verdict

At this checkpoint:

| Subject | Verdict |
|---|---|
| **P0** | COMPLETE / CLOSED / INDEPENDENTLY REMOTE VERIFIED, subject to live-state confirmation |
| **Architecture recovery** | SUFFICIENT TO SUPPORT FREEZE DECISIONS. The expanded KB corpus confirmed or refined the major conclusions and contradicted none |
| **KB integrity** | SUBSTANTIALLY RECOVERED, WITH REMAINING POLICY/AUTOMATION GAPS. The absence of browser-product raw history does not erase the surviving authoritative verdicts, but its disposition must be explicit |
| **Revision 127 trust boundary** | OPEN BLOCKER TO RECONSTRUCTION, subject to live-state confirmation |
| **Three-plane proposal** | DO NOT PROMOTE AS A COMPETING TOP-LEVEL ARCHITECTURE. Preserve authoritative dependency layering and represent trust/deployment separately |
| **Hermes** | CURRENT REPLACEABLE EXECUTION IMPLEMENTATION WHOSE BOUNDARY IS NOT YET MECHANICALLY CLEAN |
| **Generic execution-harness contract** | DIRECTIONALLY SUPPORTED / NOT YET SPECIFIED OR AUTHORIZED |
| **DeepSeek Harness** | POTENTIAL FUTURE COMPATIBILITY / REPLACEABILITY TEST; NO CURRENT AUTHORITY OR ADOPTION |
| **WIASW** | DURABLE DESTINATION ARCHITECTURE / CAPABILITY SPECIFICATION, NOT CURRENT IMPLEMENTATION PHASE |
| **Workbench / Mermaid** | PRESERVE AS GENERATED ARCHITECTURE/STATE PROJECTION MECHANISM |
| **Reconstruction** | NOT YET AUTHORIZED |

---

## A29. Next bounded action

After this handoff is durably preserved and retrieval is proven, the next
bounded implementation action should be:

> **«Remediate and independently verify closure of the revision-127 live public
> trust-boundary exposure.»**

Do not combine that security repair with the clean reconstruction. After
security closure, address the minimal KB-ingestion automation and
architecture-freeze decisions. Then authorize reconstruction.

---

**END OF VERBATIM INDEPENDENT HANDOFF.** Everything below is the recording
agent's classification work, not the external reviewer's text.

---

# PART B — PROMOTION-CANDIDATE CLASSIFICATION

Each of the ten propositions the governing card named, classified against
**live** `project_decisions` / `project_state` content read on 2026-10-07.
Classification vocabulary: **ALREADY AUTHORITATIVE** · **CONSISTENT WITH
AUTHORITY / EVIDENCE ONLY** · **REQUIRES ARCHITECTURAL DECISION** ·
**CONTRADICTED** · **SUPERSEDED**.

**Nothing in this table was promoted.** No ADR was created, amended or
superseded by this card. Where a new decision is required it is returned to
Eric/ChatGPT in Part C.

---

### B1. Dependency architecture and trust/deployment topology are distinct dimensions

**ALREADY AUTHORITATIVE — in part. The distinctness is authoritative; the
*representation* of trust domain as module metadata is not.**

ADR-SEED-018 states the distinction explicitly and in its own words: it
"is DISTINCT from ADR-SEED-015's three-layer PROCESS ISOLATION model (CIS
control plane / Docker worker / read-only /opt/cis-control), which is an
enforcement architecture and not this layering." Two separate accepted
decisions therefore already describe two different three-part decompositions,
and ADR-SEED-018 forbids conflating them — it names that conflation as "the
likely origin of the error" it was written to correct.

What is **not** authoritative is A4's prescription: that trust domain, execution
location, failure domain and replacement contract should be carried as *module
metadata* on a single layer hierarchy rather than as a second hierarchy. No
record establishes a module-property vocabulary. That half is evidence only and
is folded into the internal-module-contract decision (B5, returned as **R1**).

---

### B2. Hermes is replaceable L3 execution infrastructure rather than the permanent definition of CIS

**ALREADY AUTHORITATIVE.**

ADR-SEED-018: "LAYER 3 — HERMES BACKEND: replaceable execution infrastructure
ONLY — Hermes gateways, Hermes profiles, containers, and model/provider
execution configuration."

ADR-WIASW-002: "Hermes is the current primary Layer-3 execution and backend
infrastructure. Future backends may exist."

ADR-SEED-018 additionally supplies the explicit corrections A5 depends on:
`pipeline_relay.py`, `dispatch.py` and `guardrails.py` are **CIS-owned Layer 2,
NOT Hermes Layer 3**, and the run-plane tables are CIS run-plane/spine data,
**not** "Layer-3 tables".

A5's *measured coupling findings* (Hermes source patches, `.env` and
`config.yaml` reads, log parsing for liveness, hard-coded gateway assumptions,
an adapter complete-but-unregistered) are **evidence**, recorded in the
architecture recovery packet and continuity revisions 126/128/130. They are not
authority and do not need to be: they are observations about how far the live
system sits from an already-accepted boundary. AGENTS.md §3 carries the four
Hermes source patches as current active architecture, which corroborates the
finding from the authoritative projection side.

---

### B3. Future execution harnesses should sit behind CIS-owned stable contracts

**ALREADY AUTHORITATIVE AS DIRECTION — NOT AS A SPECIFIED CONTRACT. A6/A8's own
distinction is already the accepted one, verbatim.**

ADR-WIASW-002: "The destination may GENERALIZE the Layer-2 to Layer-3
relationship over time toward CIS-owned stable contracts above replaceable
execution backends, but that is a future generalization of the existing
architecture, NOT a reclassification of currently accepted ownership, and
nothing here authorizes refactoring Hermes or broad Layer-2 refactoring."

ADR-WIASW-002 also already lists "model execution adapters" among "POSSIBLE
FUTURE LAYER-2 ADAPTER FAMILIES, destination possibilities only, none
instantiated or authorized here," and its destination graph already carries
`CIS controls EXECUTION_LAYER`, `EXECUTION_LAYER contains MODEL_BACKENDS`,
`CIS orchestrates MODEL_BACKENDS`.

So A8's diagram is a **projection of accepted direction**, and A6's warning —
"Do NOT pretend it already exists merely by documenting it" — matches the ADR's
own activation vocabulary. **Specifying the contract is a future decision
(R2).** The ADR does not authorize writing it.

---

### B4. DeepSeek Harness has no current architectural standing

**ALREADY AUTHORITATIVE BY CONSTRUCTION — no promotion possible or needed.**

There is no `project_decisions` row, `project_state` key, `queue_items` row or
`open_questions` row naming DeepSeek Harness — verified by query, all four
empty. Under ADR-WIASW-002's activation vocabulary, absence *is* the status: a
backend with no record is not an adopted backend.

**Layer-2 evidence does exist, and more than expected.** `knowledge_messages`
holds 91 chunks containing the exact string "DeepSeek Harness": 68 in
`hermes_v4pro`, 17 in `claude_code`, 4 in `cis_handoff_packets`, 2 in
`chatgpt_export`. The `hermes_v4pro` material is a prior session in which Eric
asked for research on "the new deepseek harness" and a comparison against the
CIS contained Docker pipeline, and received a substantive answer (dsh v0.1
developer preview, 2026-08-13, MIT-licensed, built on the Cordis plugin
meta-framework, `Agent = Model + Harness`). So the causal history A7 assumes is
absent is in fact retrievable — which strengthens rather than weakens A7's
conclusion: Eric has already evaluated it, and it still has no authority. That
is the correct state, not an oversight.

AGENTS.md §11.6 independently constrains proposing it: "DeepSeek and OpenRouter
credit is exhausted, all keys revoked, those gateways DEAD until repointed. Do
not propose work that assumes a paid per-token gateway." Note the distinction —
that line concerns the DeepSeek *API provider*, not the DeepSeek *Harness*
product; they are different things and should not be conflated in a future
decision.

Recording "DeepSeek Harness has no standing" as an ADR would **create** standing
where none exists, which A7 itself warns against. Correct disposition: leave it
unrecorded; it becomes relevant only as a test subject once R2 is decided.

---

### B5. Internal module contracts should generalize existing CIS contract mechanisms

**REQUIRES ARCHITECTURAL DECISION.**

The *ingredients* are authoritative. ADR-SEED-016 ("Enforcement Primitive
Approved") and ADR-SEED-015 (three-layer process isolation) establish the Task
Contract Enforcement Primitive; ADR-SEED-012 establishes the orchestrator
validation contract; ADR-WIASW-002 establishes the adapter-contract family and
the execution-interface preference ordering; the WB.1C card-contract mechanism
(`tools/development/card_contract.py`, `card-contract-record`/`-show`) is a
live, machine-readable contract primitive.

The *generalization* is not. No record defines an internal module contract, its
required fields, or the four-way contract taxonomy A9 proposes (task/worker,
execution, tool adapter, internal module). A9 is the most load-bearing
unresolved item in the whole synthesis: Step 4 of A23 names "exact internal
module contract" as a freeze prerequisite, and Step 5 makes reconstruction
depend on it.

Returned as **R1**. It is also where B1's module-property vocabulary belongs.

---

### B6. WIASW consumers attach through stable CIS-owned interfaces

**ALREADY AUTHORITATIVE.**

ADR-WIASW-002 states the destination execution pattern directly: "WIASW
application or workflow, then CIS, then a CIS-owned stable adapter contract,
then an application-specific adapter, then API, script or GUI, then the external
application" — which is A11's chain. Its execution-interface preference ordering
(native API → app scripting → CLI → domain-specific → GUI/computer-use) is A11's
deterministic-first rule, including the explicit statement that GUI automation
is "a LEGITIMATE FALLBACK … last by preference, not forbidden."

ADR-WIASW-001 carries the five domains and the `WIASW uses CIS` edge.
ADR-WIASW-002's `CREATIVE_TOOL_BACKENDS` node already names Blender, Houdini,
ComfyUI, Unreal Engine and DAWs "as destination possibilities only, with no
adapter authorized, built or installed," and keeps the `NOT_ACTIVATED` default.

A27's extensibility test is a **restatement of accepted architecture as an
acceptance criterion.** Promoting the *test* would be reasonable but is not
required; it is better attached to R1 than recorded alone.

---

### B7. Workbench/Mermaid are generated lenses, not authority

**ALREADY AUTHORITATIVE AS A PATTERN — NOT AS A NAMED RULE ABOUT DIAGRAMS.**

The projection-not-authority principle is established repeatedly and
mechanically:

- ADR-PIPE-006: `docs/UNIFIED_BUILD_LIST.md` is "a GENERATED PROJECTION of the
  queue authority … NOT an independent authority."
- ADR-WIASW-001: "The machine-readable graph is parsed from the clauses above by
  `tools/state/destination_architecture.py` and is a projection, never a second
  store: no destination architecture is written to
  `project_state.pipeline_roadmap`, `queue_items`, `queue_edges`,
  `build_plan_nodes` or `build_plan_dependencies`."
- ADR-SEED-018's boundary rule: "Run-plane state is normalized through a Layer-2
  read model/API before UI consumption."
- Mechanically enforced: `tools/gates/gate_export_agreement.sh` (13/13
  artifacts matched at this SHA) checks projections against authority.
- Live implementation: `runtime/ui/src/MermaidDiagram.jsx` with
  `BuildPathMermaid` and `DestinationArchitectureMermaid` rendering from
  authoritative read models, each with committed tests.

What has **no** record is the negative rule A18 asks for — "do not create
another manually maintained architecture-diagram system" — and the eight-view
list. The architecture review packet already applies the rule to itself ("Every
diagram in this packet is a **projection**, not authority … The rest are
hand-authored one-shot review aids and are labelled as such"), which shows the
norm is understood but held in evidence, not in authority.

Classification: the principle is **ALREADY AUTHORITATIVE**; the diagram-system
prohibition and the eight views are **CONSISTENT WITH AUTHORITY / EVIDENCE
ONLY**. The trust-boundary view's priority is a sequencing judgement, not a
decision.

---

### B8. "RECORD ONCE → DERIVE EVERYWHERE"

**CONSISTENT WITH AUTHORITY / EVIDENCE ONLY — and it is the single highest-value
promotion candidate.**

As a *practice* it is pervasive and mechanically enforced in named places:
ADR-PIPE-006 (one authority per plane, projections generated),
ADR-WIASW-001 (clause grammar rather than a new table — "No new table was
created"), ADR-XDEV-002 (checkpoint surfaced through the existing recovery chain
rather than a parallel one), `gate_export_agreement.sh`, and
`config/kb_source_policy.yaml`'s own design note: "This file is the ONLY place
that says which source families are expected … so there is no second list for
anyone to keep in step."

As a *stated principle* it appears **nowhere** in `project_decisions`,
`project_state` or `open_questions` — verified by query, all three empty. A
corpus search for "record once" returns exactly one chunk, in `claude_export`,
and it is coincidental phrasing ("the breach ledger now has three entries to
record once this settles"), not the principle. So the rule has no statement
anywhere in CIS, in authority or in evidence.

That asymmetry is itself the finding: the rule is obeyed by convention and
re-derived case by case, which is exactly the failure mode A19 describes. It is
also the rule most likely to be violated during reconstruction, when every
temptation is to add "one more place to look."

The live working tree shows the cost concretely: the KB recovery's mechanism
exists on disk and in the spine but is absent from the pushed tree, so there are
currently two different answers to "does CIS have a KB coverage gate" depending
on whether you read the host or the remote.

Returned as **R4** — a candidate for the smallest possible ADR, carrying the
principle and nothing else.

---

### B9. Cards are projections of structured Execution Contracts rather than independent work authority

**REQUIRES ARCHITECTURAL DECISION — and it is already recorded as undecided in
the right place, which is a meaningful finding.**

`config/kb_source_policy.yaml` already states the framing and already marks it
unsettled, in the `cards` family: "POLICY-DEPENDENT, currently excluded. The
destination specification treats cards as early manual projections of a future
Execution Contract rather than authority. Their durable outcome is recorded in
`dev_continuity_events`, and the card text itself is the operator's instruction,
not a finding."

That note is a **source-policy classification**, not an architectural decision,
and the policy file says so of itself: "It is NOT an authority registry. Nothing
in this file makes a source authoritative."

Corroborating evidence that the *practice* already follows the principle:
ADR-SEED-013 retired Kanban as required pipeline transport; durable card
outcomes land in `dev_continuity_events` and `queue_items`, not in card files;
`card_contract.py` already records a machine-readable contract separately from
card prose. The `cards/*.db` files at the repository root are **0 bytes** — the
card-as-database path was never populated, which is consistent with cards never
having become authority in practice.

A17's recommended disposition — promote the principle, not the current card
format — is sound and is **not** adopted here. Returned as **R5**.

---

### B10. Comprehensive external handoffs occur at meaningful phase/architecture boundaries rather than every session

**CONSISTENT WITH AUTHORITY / EVIDENCE ONLY — now mechanically supported, and
partly settled by this card's own implementation.**

Related authority exists but does not say this:

- ADR-SEED-008: "External advisor packet remains permanent."
- ADR-XDEV-001: external-developer work is not durable until independently
  verified from the remote; `LOCAL_COMPLETE → COMMITTED → PUSHED →
  REMOTE_REVIEW_REQUIRED → REMOTE_VERIFIED`.
- ADR-XDEV-002: checkpoint status must be visible in the recovery chain.
- ADR-WIASW-004: "any development-relevant input that may affect progress toward
  an accepted target architecture must have a durable path from discovery to
  disposition," and its existence "must NOT depend on architect memory, model
  memory, conversation context, surviving a context clear, handoff prose, a
  session log, or one model remembering a previous discussion."

ADR-WIASW-004 is the closest authority, and it argues for *both* halves of A15:
durability must not depend on memory (so sessions need an automatic path), and
disposition is separate from capture (so handoffs are not authority).

A15's *frequency* rule — comprehensive handoffs at phase boundaries, not every
session — is now partly answered mechanically rather than by policy. Session-end
ingestion (Part D) makes every session durable automatically, which removes the
reason a comprehensive handoff would ever be needed *for capture*. What remains
for a phase handoff is **synthesis**, which is a different product. That
reframing is evidence, not authority, and is folded into R3.

---

## B11. Summary matrix

| # | Proposition | Classification | Authority cited | Returned as |
|---|---|---|---|---|
| 1 | Dependency architecture ≠ trust/deployment topology | ALREADY AUTHORITATIVE (distinctness); EVIDENCE ONLY (module-metadata representation) | ADR-SEED-018, ADR-SEED-015 | part of R1 |
| 2 | Hermes is replaceable L3, not the definition of CIS | ALREADY AUTHORITATIVE | ADR-SEED-018, ADR-WIASW-002 | — |
| 3 | Future harnesses behind CIS-owned stable contracts | ALREADY AUTHORITATIVE as direction; contract NOT specified | ADR-WIASW-002 | R2 |
| 4 | DeepSeek Harness has no standing | ALREADY AUTHORITATIVE by construction (absence is the status) | ADR-WIASW-002 activation vocabulary; AGENTS.md §11.6 | — (do not record) |
| 5 | Internal module contracts generalize existing mechanisms | **REQUIRES ARCHITECTURAL DECISION** | ADR-SEED-012/015/016, ADR-WIASW-002 (ingredients only) | **R1** |
| 6 | WIASW consumers attach through stable CIS-owned interfaces | ALREADY AUTHORITATIVE | ADR-WIASW-001, ADR-WIASW-002 | — |
| 7 | Workbench/Mermaid are generated lenses | ALREADY AUTHORITATIVE as pattern; diagram prohibition EVIDENCE ONLY | ADR-PIPE-006, ADR-WIASW-001, ADR-SEED-018, `gate_export_agreement.sh` | optional, with R1 |
| 8 | RECORD ONCE → DERIVE EVERYWHERE | CONSISTENT WITH AUTHORITY / EVIDENCE ONLY | practice in ADR-PIPE-006, ADR-WIASW-001, ADR-XDEV-002; stated nowhere | **R4** |
| 9 | Cards are projections of Execution Contracts | **REQUIRES ARCHITECTURAL DECISION** | `kb_source_policy.yaml` `cards` note (policy, not authority); ADR-SEED-013 | **R5** |
| 10 | Comprehensive handoffs at phase boundaries | CONSISTENT WITH AUTHORITY / EVIDENCE ONLY | ADR-SEED-008, ADR-XDEV-001/002, ADR-WIASW-004 | part of R3 |

**Zero propositions are CONTRADICTED. Zero are SUPERSEDED.**

---

# PART C — RETURNED DECISIONS

Not taken by this card. Each requires Eric's disposition and, where it changes
architecture, an ADR recorded through the sanctioned mechanism.

**R1 — INTERNAL MODULE CONTRACT (blocking for reconstruction).** Define the
internal module contract and the contract taxonomy, generalized from the Task
Contract Enforcement Primitive, the orchestrator validation contract and the
WB.1C card contract, rather than invented as a new governance subsystem.
Includes B1's module-property vocabulary (layer / trust domain / execution
location / failure domain / replacement contract) and, optionally, B6's
extensibility test and B7's diagram prohibition as acceptance criteria. Named by
A23 Step 4 as a freeze prerequisite.

**R2 — GENERALIZED EXECUTION-BACKEND CONTRACT: STATUS AND TIMING.** ADR-WIASW-002
permits the generalization and authorizes no work. Decide whether specifying it
is in scope before reconstruction, after it, or deferred. Until decided, A6's
caution holds: a contract above a backend that cannot be swapped is
documentation, not a boundary. DeepSeek Harness becomes a test subject only once
this is decided (B4).

**R3 — BROWSER-PRODUCT HISTORY POLICY (live gate conflict).** `chatgpt_sessions`
and `claude_ai_sessions` are declared `required: true` with
`ingestion_path: MISSING`, so `gate_kb_source_coverage.py` is RED now and cannot
go green. Disposition required. See Part D for the three options and for why
this card refused to change the policy file. Includes B10's reframing: with
session-end ingestion live, a phase handoff's remaining purpose is synthesis,
not capture.

**R4 — "RECORD ONCE → DERIVE EVERYWHERE" AS A STATED PRINCIPLE.** Obeyed
pervasively, stated nowhere. The smallest possible ADR carrying the principle
and nothing else would make the rule citable during reconstruction instead of
re-derived per module. See B8.

**R5 — CARDS VERSUS STRUCTURED EXECUTION CONTRACTS.** A17's recommendation —
promote the principle, not the current card format — with A17's candidate wording
in Part A. Already visible as undecided in `kb_source_policy.yaml`'s `cards`
family. Named by A23 Step 4 as a freeze prerequisite.

**R6 — KB RECOVERY MECHANISM IS NOT IN THE PUSHED TREE.** Found live by this
card, not by the external review. The policy, gate, ingester, tests and manifest
exist only in the working tree at `bf01df4d`. Under ADR-XDEV-001 they are not
durable and not independently verifiable from the remote. Decide whether they
are committed before, with, or after revision-127 remediation. This card did not
commit them: committing is outside its scope, and `git status` shows 27 entries
whose disposition is Eric's.

**R8 — SEMANTIC RETRIEVAL HAS A MEASURED RECALL CEILING.** Found live by this
card while producing its own retrieval proof. On the 493,377-chunk collection,
`tools/ask_history.py`'s `n_results=50` search does not return the true nearest
chunk for 3 of 4 re-measured probes; the true top-1 appears only at depth ≥ 200.
Measurement in `evidence/hnsw_recall_measurement.txt`, detail in D3. Decide
whether this becomes a bounded retrieval-quality card before or after
architecture freeze. Per A14 it is **not** treated as a reconstruction blocker
here.

**R7 — `data/agent_handoffs/` IS OUTSIDE GIT.** `.gitignore:136` (`/data/*`)
excludes the entire sanctioned external-development handoff tree; 19 tracked
files under `data/` are all `mining_archive`. This artifact, every architecture
recovery packet and the KB recovery report are therefore **unreachable from the
GitHub remote**, which per AGENTS.md §11.6 is the only surface ChatGPT sees
through Codex. A15's cold-start chain works from inside the VM via KB retrieval
and does **not** work for a remote external reviewer. This is a structural
limitation of the existing handoff mechanism, surfaced rather than changed.

---

# PART D — MECHANISM CHANGES MADE BY THIS CARD

Recorded here so the mechanism is discoverable with the artifact it serves.
Full evidence is in the card's return packet and in `dev_continuity_events`.

### D1. Session-end ingestion — IMPLEMENTED

`tools/kb/session_end_ingest.sh`, registered as a Claude Code `SessionEnd` hook.
Deterministic, bounded, idempotent, no model summarisation, provenance
preserved, secret filtering unchanged (it calls the already-sanctioned
`tools/ingest_claude_code_sessions.py`, which is idempotent by `source_key` and
drops secrets at Chroma index time). It reads transcripts; it never writes them.
Failure is visible through the coverage gate, whose `claude_code_sessions` family
declares `max_age_days: 2` — a hook that stops working turns that family red
within two days.

Registered at **user scope** (`~/.claude/settings.json`), not project scope,
because **60 of the 75 policy-eligible transcripts** on this host were written
by sessions whose working directory is `/home/eric` rather than
`/mnt/projects/cis`. A project-scope hook would have covered 15 of 75 — 20% —
and reported success. The declared family root is `~/.claude/projects` (all
projects), so user scope matches the policy exactly.

Known limitation, recorded rather than hidden: an exchange still in progress at
ingest time is keyed `<project>/<session>/<idx>.<part>`; if that session is later
resumed, the same key is skipped as already-present, so the final few turns of a
resumed session can stay partial. Bounded and self-correcting for new exchanges.

### D2. Closeout coverage gate — IMPLEMENTED, in a mode that cannot be
permanently red

`gate_kb_source_coverage.py --closeout` fails only on families that are
`required` **and** `measurable`. A family that is `required` but
`measurable: false` with `ingestion_path: MISSING` is reported as
`POLICY UNDECIDED` and does not block. `tools/development/cli.py closeout-check`
calls it and surfaces both.

This reads the distinction the policy file **already declares** (`measurable`,
`ingestion_path`); it does **not** change any family's `required` flag, and
`config/kb_source_policy.yaml` was not modified. The default gate mode is
unchanged, so the standing red verdict and R3's conflict remain visible rather
than being quietly resolved.

The three options for R3, none chosen here: (a) build a supported ingestion path
for the browser exports; (b) reclassify the two families as policy-dependent,
accepting that independent-review reasoning held only in ChatGPT is not durable;
(c) accept phase handoffs such as this artifact as the supported durable
substitute for that reasoning. Option (c) is what this card *demonstrates*, and
it is explicitly **not** equivalent to raw browser-history ingestion — it
preserves synthesis at chosen boundaries, not the conversation.

### D3. Retrieval is proven, with a measured ceiling that is a new finding

This artifact is ingested (69 chunks, sha256-provenanced,
`external_dev_handoffs` 239/239 = 100%) and **retrievable for all seven probes
the governing card named**. But the depth at which it is retrievable is not the
depth `tools/ask_history.py` searches, and that gap is a property of the store,
not of this artifact.

Measured on the live collection (493,377 chunks), evidence in
`evidence/hnsw_recall_measurement.txt`:

| Probe | handoff rank @50 | @100 | @200 | best distance @50 | true best |
|---|---|---|---|---|---|
| dependency architecture versus trust/deployment topology | — | — | **1** | 0.7934 | **0.7594** |
| WIASW destination extensibility test | — | — | **1** | 1.0949 | **0.9424** |
| cards are projections of structured Execution Contracts | — | — | **1** | 0.8278 | **0.7602** |
| record once derive everywhere | — | — | — | 0.8825 | 0.8825 (@400: rank 7) |

**The top-50 window is not the true top 50.** For three probes the single
closest chunk in the entire corpus is not returned at `n_results=50` or `100` —
the best distance the search reports there is *worse* than the best distance the
same query finds at `n_results=200`. That is approximate-nearest-neighbour
recall loss in Chroma's HNSW index at this corpus size, and no reranking change
can recover a chunk the search never returned.

Consequence, stated plainly because it touches the KB recovery's own evidence:
`tools/ask_history.py` queries at `n_results = max(k*10, 50)`, so the
instrument revision 133 used to confirm "all twelve dead concepts retrievable"
has a recall ceiling. The concepts *are* retrievable — verified here at depth —
but a cold developer using the default tool gets the handoff in 3 of 7 probes,
not 7 of 7.

A second, independent effect compounds it: `PER_SOURCE=2` crowding by
model-execution chatter. The "WIASW destination extensibility test" probe's
top-5 at depth 50 is four Hermes gateway transcripts reading
`[TEST MODE] Respond in 3 sentences or fewer` plus one unrelated build plan.
That is concrete, measured support for A14's "archive material dominating corpus
volume" and for the `hermes_sessions` policy question — the noise is not
hypothetical.

**Not fixed by this card.** A14 is explicit that retrieval quality must not
become a reconstruction blocker, and changing search depth or ranking is
retrieval-quality work on the instrument the whole KB depends on, which deserves
its own bounded card and its own measurement. Recorded as a discovery against
WB.1 so it cannot be lost.

---

*Preserved 2026-10-07 by Claude Code at `bf01df4d45a9de8981c2d057cf629e4cd24ba514`
under the governing card "DURABLE INDEPENDENT ARCHITECTURE HANDOFF +
EXTERNAL-HANDOFF RECOVERY PATH". No reconstruction performed. Revision 127 not
touched. P1 not activated. Next bounded action: remediate the revision-127 live
public trust-boundary exposure.*
