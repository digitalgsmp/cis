# .gate-control — the override plane

This directory is the off switch for the container's enforcement wall.

## Turning enforcement off

```bash
touch /mnt/projects/cis/.gate-control/DISABLED
```

Every `pre_tool_call` check in the container reads this file as its **first**
action. While `DISABLED` exists, the wall allows every tool call and records
each one in `/workspace/cis/gate_override.log`. No restart is needed — the
check runs per tool call, so it takes effect on the very next one.

## Turning it back on

```bash
rm /mnt/projects/cis/.gate-control/DISABLED
```

Also immediate.

## Why this exists

In the v2.0 attempt a `pre_tool_call` hook required a clearance token that the
gate itself refused to issue while git was dirty — so the hook blocked the very
writes needed to reach a clean state, and the only way to disable the hook was
to edit a config file the hook would not let anyone edit. From the record:

> "No escape hatch. The only way to disable the hook was to edit config.yaml,
> but the hook blocked edits. The lock could only be opened from inside the
> locked room."

The rule that came out of that:

> "This single rule is the difference between the v2.0 deadlock and a safe
> enforcement system. Every gate in this architecture checks the override plane
> as its first line. You are never more than one `touch` command from a working
> system."

## Why it is a host directory mounted read-only

The container mounts this directory at `/opt/cis-control/gate` with `:ro`, so
the agents can **read** the file and can never **create** it. That asymmetry is
the whole design. An override the constrained agent can set is not an override;
it is a self-disable, and it would hand every agent the ability to switch off
the wall that governs it.

Read-only here is enforced by the kernel at the mount layer, not by file
permissions, so it holds even for root inside the container.

## What is tracked and what is not

`README.md` is committed so the directory exists in a fresh clone — Docker
creates a missing bind-mount source as a root-owned directory, which would then
be unwritable from a normal shell and break the `touch` above.

`DISABLED` is git-ignored. Whether enforcement is currently off is machine
state, not source, and committing it would ship a disabled wall to anyone who
checked the repo out.

## Proving it works

```bash
bash tools/test_override_plane.sh
```

Deterministic, runs from a bare shell, involves no Hermes. The record requires
this to pass before the wall is ever trusted to block:

> "The override plane must be verified by a deterministic acceptance test
> BEFORE the hook is enabled in enforcement mode."

## What this does NOT do

It does not change the failure mode. The wall currently **fails open** — if the
gate runner errors, times out, or is missing, the tool call proceeds. That is
why the system cannot deadlock today, and it is why the override plane is being
built and proven first. Flipping fail-open to fail-closed is the second half of
queue item 0.4 and comes only after this test passes.
