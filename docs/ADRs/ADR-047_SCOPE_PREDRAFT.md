# ADR-047 — Filesystem Governance and Canonicality
# Status: PRE-DRAFT — scope only, not yet locked
# Updated: 2026-04-30
# Do not implement until this document is locked via L1 + L3 verification.

---

## Problem Statement

CIS has accumulated filesystem paths that exist outside config.py authority,
share ambiguous names across distinct concepts, and have no formal lifecycle,
retention, or ownership rules. This creates conditions for:

- Silent writes to wrong locations
- AI session misattribution of governance authority
- Irreversible data loss once agents begin autonomous filesystem actions
- Ceremonial governance: contracts that assume canonical paths that do not exist

---

## Manifest Taxonomy (Primary Motivation)

Three distinct manifest classes currently share the bare noun "manifest":

| Class Name | Path | Owner | Lifecycle |
|---|---|---|---|
| Verification manifest | logs/manifests/ | cis_verify.py / queue_worker.py | Retain per session |
| Runtime manifest | runtime/manifests/ | Unknown — pre-ADR-033 | TBD — may be deprecated |
| Source manifest | INGEST_ROOT/source_id/manifest.json | pipeline.py | Retain per source |

Config constants established (2026-04-30):
- VERIFICATION_MANIFEST_DIR
- RUNTIME_MANIFEST_DIR
- SOURCE_MANIFEST_NAME

The bare word "manifest" is now prohibited in new code.
All manifest references must use the named config constant.

---

## Filesystem Zone Classification (Required)

Every path under /mnt/projects/cis/ must be classified into one of:

| Zone | Meaning |
|---|---|
| ACTIVE | Currently written to and read from in runtime |
| MIRROR | Read-only copy of canonical data (e.g. Obsidian vault) |
| ARCHIVE | Retained for history, not active |
| LEGACY | Exists from earlier build phase, ownership unclear |
| TRANSITIONAL | Temporary — will be replaced or removed |
| DEPRECATED | No longer used — scheduled for archive |

---

## Required Decisions for ADR-047

1. Zone classification for all top-level paths under /mnt/projects/cis/
2. Formal retention policy for verification manifests
3. Resolution of runtime/manifests/ — classify, rename, or deprecate
4. Canonical naming convention for all three manifest classes
5. Policy: any new path requires a config.py constant before first use
6. Policy: no file may be written outside a classified zone by runtime code

---

## Governance Constraints

- ADR-047 does not exist yet. No cleanup actions until it is locked.
- No deletions. Archive policy must be defined before any files move.
- config.py is the sole path authority. ADR-047 formalizes this as constitutional.
- Agents must not perform filesystem actions until zone classification is complete.

---

## Scope Boundary

ADR-047 covers: path authority, zone classification, manifest taxonomy,
retention policy, naming conventions.

ADR-047 does not cover: execution ownership, verification chain,
operator abstraction, or queue mechanics. Those are ADR-043/044/045.

---

## Dependencies

Blocked by: nothing — can be drafted in parallel with ADR-045 completion.
Blocks: agent filesystem actions, autonomous cleanup, manifest schema enforcement.
