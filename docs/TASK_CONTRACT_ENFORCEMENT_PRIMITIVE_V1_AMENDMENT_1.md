# TASK_CONTRACT_ENFORCEMENT_PRIMITIVE_V1 — Amendment 1 (Revised)
## §7/§14 Test-Rig Carve-Out

**Status:** PROPOSAL — for Eric approval only (amendment is mechanical, not architectural)
**Date:** 2026-06-20
**Revision:** 1 → adds root-owned sentinel source (§3) and control/workspace separation requirement (§4)
**Amends:** TASK_CONTRACT_ENFORCEMENT_PRIMITIVE_V1.md §7, §14
**Reason:** Structural contradiction — §14 requires override-plane evidence before any /opt/cis-control creation, but §7 Parts A+B test requires /opt/cis-control to exist. The test-rig carve-out resolves the deadlock.

---

## 1. The Contradiction

§14 line 665: "Before any implementation step (creating /opt/cis-control, writing hooks, configuring Docker mounts), the following raw evidence must be captured..."

§7 Parts A+B: The 9-step override-plane test requires:
- A `.GATE_DISABLED` sentinel at a host path mounted read-only into the container (Steps 2, 4–5)
- A Docker container with RO `/contract` mount (Steps 4–5)
- Container relaunch capability (Steps 3, 8)

The evidence gate blocks the infrastructure the evidence test requires. This is a provability deadlock, not a design flaw — the override plane is correctly specified but cannot be demonstrated without an operator-writable sentinel path.

---

## 2. Resolution: Disposable Test Root

The §7 Parts A+B override-plane evidence test shall run against a disposable test root, not the production `/opt/cis-control`:

```
/mnt/cache/catalog/override-plane-test/<run_id>/
```

This root contains two separate host directories:

```
<test_root>/
├── control/                              ← root-owned, operator-only writable
│   └── contracts/
│       └── inv-catalog-001/              ← mounted RO → /contract in container
│           └── .GATE_DISABLED            ← operator creates/removes via sudo
└── workspace/                            ← eric-owned, worker-writable
    └── <run_id>/                         ← mounted RW → /mnt/cache/catalog/<run_id>
```

The path is disposable — no production state depends on it.

---

## 3. Requirement: Root-Owned Sentinel Source

The disposable control directory must be owned by root on the host. The `.GATE_DISABLED` sentinel must be created and removed by the operator using `sudo`. This proves the operator/worker boundary: the normal user (worker's identity) cannot create or remove the sentinel on the host.

**Required evidence before Step 2:**

```
COMMAND: sudo mkdir -p /mnt/cache/catalog/override-plane-test/<run_id>/control/contracts/inv-catalog-001
COMMAND: sudo chown -R root:root /mnt/cache/catalog/override-plane-test/<run_id>/control
COMMAND: stat -c '%U:%G %a %n' /mnt/cache/catalog/override-plane-test/<run_id>/control
COMMAND: stat -c '%U:%G %a %n' /mnt/cache/catalog/override-plane-test/<run_id>/control/contracts/inv-catalog-001
```

**After Step 2 (sentinel creation):**

```
COMMAND: stat -c '%U:%G %a %n' /mnt/cache/catalog/override-plane-test/<run_id>/control/contracts/inv-catalog-001/.GATE_DISABLED
```

**Negative check — worker cannot create sentinel on host without sudo:**

```
COMMAND: touch /mnt/cache/catalog/override-plane-test/<run_id>/control/contracts/inv-catalog-001/.GATE_DISABLED_WORKER_TRY 2>&1
EXPECTED: non-zero exit, "Permission denied" — root-owned directory blocks write by normal user
```

---

## 4. Requirement: Control Source Separated from Workspace

The disposable control directory (`<test_root>/control/`) must NOT be inside the container's read-write workspace mount. Proof that control and workspace are separate host directories and that the container enforces different mount semantics:

**Host-side evidence — separate directories:**

```
COMMAND: realpath /mnt/cache/catalog/override-plane-test/<run_id>/control/contracts/inv-catalog-001
COMMAND: realpath /mnt/cache/catalog/override-plane-test/<run_id>/workspace/<run_id>
```

**Container-side evidence — mount semantics:**

```
COMMAND: docker inspect <container> | jq '.[0].Mounts[] | {Source, Destination, Mode}'
EXPECTED:
  /contract → Source: <test_root>/control/contracts/inv-catalog-001, Mode: ro
  /mnt/cache/catalog/<run_id> → Source: <test_root>/workspace/<run_id>, Mode: rw
  /mnt/projects/cis → Mode: ro
```

**Inside-container verification:**

```
COMMAND: mount | grep -E '/contract|/mnt/cache/catalog'
EXPECTED:
  /contract shows (ro,...)
  /mnt/cache/catalog/<run_id> shows (rw,...)
```

---

## 5. What This Amendment Allows

1. **Create a disposable, root-owned test control directory** at `<test_root>/control/`
2. **Create a disposable workspace directory** at `<test_root>/workspace/`
3. **Create and remove `.GATE_DISABLED` via sudo** inside the root-owned control directory
4. **Launch a disposable Docker container** with:
   - RO mount: `<test_root>/control/contracts/inv-catalog-001` → `/contract` (read-only)
   - RO mount: `/mnt/projects/cis` → `/mnt/projects/cis` (source tree, read-only)
   - RW mount: `<test_root>/workspace/<run_id>` → `/mnt/cache/catalog/<run_id>` (workspace, read-write)
5. **Run the 9-step §7 Parts A+B test** inside that disposable container as a bare shell
6. **Tear down** the container and test root after evidence capture

---

## 6. What This Amendment Does NOT Allow

1. No production `/opt/cis-control` may be created
2. No Hermes configs, hooks, DB schema, migrations, compiler, reviewer loop, or release automation may be modified
3. No enforcement files may be written outside `/mnt/cache/catalog/override-plane-test/`
4. The test-rig does not prove the full enforcement primitive — it proves ONLY the operator/worker mount semantics:
   - Sentinel creation/removal requires operator privilege (sudo, root-owned directory)
   - RO enforcement at the Docker/filesystem layer
   - Override is honored when sentinel is present
   - Re-engagement after sentinel removal and container restart
5. The test container must not run Hermes as the worker — this is a bare-shell test of mount semantics, not an enforcement hook test
6. The workspace directory must NOT contain the control directory — they are separate host paths with different owners and mount modes

---

## 7. Evidence Mapping: §7 Parts A+B Against Disposable Root

| Original | Amended |
|----------|---------|
| `/opt/cis-control/contracts/inv-catalog-001/` | `<test_root>/control/contracts/inv-catalog-001/` (root-owned) |
| `/opt/cis-control/contracts/inv-catalog-001/.GATE_DISABLED` | Same file, created via `sudo` on host |
| `/contract/.GATE_DISABLED` (inside container) | Same container path, RO mount from root-owned host dir |
| Container relaunch | `docker rm -f <container> && docker run ...` (operator action) |

The 9 steps are mechanically identical — only the host-side sentinel path and ownership model move from a hypothetical production root to a real disposable root.

---

## 8. Acceptance Criteria

The amendment is satisfied when:

1. The control directory is root-owned on the host (stat evidence)
2. The workspace directory is separate from the control directory (realpath evidence)
3. Docker mounts show `/contract` as `ro` and workspace as `rw` (docker inspect evidence)
4. The 9-step test completes against the disposable root
5. Every command reports COMMAND / OUTPUT / EXIT / INTERPRETATION
6. Final result is PASS / FAIL / BLOCKED
7. PASS means:
   - (a) Worker cannot create/remove sentinel inside container (/contract/ is RO)
   - (b) Worker cannot create sentinel on host without sudo (root-owned directory)
   - (c) Operator can create sentinel on host via sudo
   - (d) Override is honored when sentinel is present
   - (e) Docker wall is never bypassed
   - (f) Hook/wall re-engages after operator removes sentinel and container restarts

Only after PASS may Eric decide whether to approve production `/opt/cis-control` implementation.

---

## 9. Spine Impact

- NA-SEED-014 marked BLOCKED — structural contradiction (infra gate blocks evidence test)
- NA-SEED-015 marked COMPLETE — this amendment drafted and revised
- NA-SEED-016 — PENDING: execute §7 Parts A+B test against disposable root per this amendment
- current_direction points to this amendment, not production implementation

---

**Authorship rule:** This amendment was drafted by Hermes (v4pro Implementer) per Eric's directive. Revision 1 adds root-owned sentinel source (§3) and control/workspace separation requirement (§4). It is a mechanical scope clarification, not a design change. No implementation authority is granted beyond what this amendment explicitly allows.

**Next step:** Eric approval → execute NA-SEED-016 (disposable test-rig 9-step evidence with root-owned control directory and separate workspace mount).
