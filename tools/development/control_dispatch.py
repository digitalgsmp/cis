#!/usr/bin/env python3
"""Root-owned execution dispatcher for transitional external development.

The installed copy lives at ``/opt/cis-control/bin/cis-dispatch``.  The
repository copy is installation source and tests; it is not the runtime
authority.  A real dispatch requires a frozen, root-owned contract below
``/opt/cis-control/contracts``.  The caller cannot add model CLI flags:
the contract selects one fixed argv profile and this dispatcher supplies
the edit-capable Claude flag only after validating that contract.

This is a bootstrap boundary, not the finished contained worker.  It moves
the host edit grant out of model-writable launcher code, but filesystem
confinement still comes from the container/mount work that follows.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
import stat
import subprocess
import sys

CONTROL_ROOT = "/opt/cis-control"
CONTRACTS_DIR = os.path.join(CONTROL_ROOT, "contracts")
CONTRACT_VERSION = "cis-dispatch-contract-v1"


class DispatchError(Exception):
    pass


def _sha256(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _parse_time(value):
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, ValueError) as exc:
        raise DispatchError("contract expires_at is not an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise DispatchError("contract expires_at must carry a timezone")
    return parsed.astimezone(dt.timezone.utc)


def _assert_root_owned_chain(path, control_root):
    root = os.path.realpath(control_root)
    current = os.path.realpath(path)
    if current != root and not current.startswith(root + os.sep):
        raise DispatchError("contract escapes the control root")
    if os.path.islink(path):
        raise DispatchError("contract may not be a symlink")
    while True:
        info = os.stat(current)
        if info.st_uid != 0:
            raise DispatchError(f"control path is not root-owned: {current}")
        if info.st_mode & (stat.S_IWGRP | stat.S_IWOTH):
            raise DispatchError(f"control path is group/world writable: {current}")
        if current == root:
            break
        parent = os.path.dirname(current)
        if parent == current:
            raise DispatchError("control path ownership walk escaped its root")
        current = parent


def load_contract(path, *, control_root=CONTROL_ROOT, enforce_root_ownership=True,
                  now=None):
    contracts_dir = os.path.realpath(os.path.join(control_root, "contracts"))
    resolved = os.path.realpath(path)
    if not resolved.startswith(contracts_dir + os.sep):
        raise DispatchError("contract must be below /opt/cis-control/contracts")
    if enforce_root_ownership:
        _assert_root_owned_chain(resolved, control_root)
    try:
        with open(resolved, encoding="utf-8") as handle:
            contract = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise DispatchError(f"cannot read contract: {exc}") from exc

    required = {
        "contract_version", "task", "authorization_revision", "intent_original",
        "intent_sha256", "intent_interpretation", "interpretation_sha256",
        "tool", "executable", "executable_sha256", "argv_profile",
        "working_directory", "expires_at",
    }
    missing = sorted(required - set(contract))
    unknown = sorted(set(contract) - required)
    if missing or unknown:
        raise DispatchError(f"contract shape mismatch; missing={missing}, unknown={unknown}")
    if contract["contract_version"] != CONTRACT_VERSION:
        raise DispatchError("unsupported contract_version")
    if not isinstance(contract["authorization_revision"], int) or contract["authorization_revision"] < 1:
        raise DispatchError("authorization_revision must be a positive integer")
    if not isinstance(contract["intent_original"], str) or not contract["intent_original"].strip():
        raise DispatchError("intent_original must be non-empty text")
    if _sha256(contract["intent_original"].strip()) != contract["intent_sha256"]:
        raise DispatchError("intent_sha256 does not match intent_original")
    if not isinstance(contract["intent_interpretation"], str):
        raise DispatchError("intent_interpretation must be text, even when empty")
    if _sha256(contract["intent_interpretation"]) != contract["interpretation_sha256"]:
        raise DispatchError("interpretation_sha256 does not match intent_interpretation")
    profiles = {"claude": "claude_accept_edits", "codex": "codex_exec"}
    if profiles.get(contract["tool"]) != contract["argv_profile"]:
        raise DispatchError("tool and argv_profile are not an allowed fixed pair")
    executable = os.path.realpath(contract["executable"])
    if not os.path.isfile(executable) or not os.access(executable, os.X_OK):
        raise DispatchError("contract executable is absent or not executable")
    if _sha256_file(executable) != contract["executable_sha256"]:
        raise DispatchError("executable hash no longer matches the frozen contract")
    workdir = os.path.realpath(contract["working_directory"])
    if not os.path.isdir(workdir):
        raise DispatchError("contract working_directory is absent")
    instant = now or dt.datetime.now(dt.timezone.utc)
    if _parse_time(contract["expires_at"]) <= instant.astimezone(dt.timezone.utc):
        raise DispatchError("contract has expired")
    contract["executable"] = executable
    contract["working_directory"] = workdir
    contract["_path"] = resolved
    return contract


def dispatch(contract_path, handoff_path, *, expected_task,
             expected_authorization_revision, expected_tool,
             control_root=CONTROL_ROOT,
             enforce_root_ownership=True, dry_run=False, timeout=300, now=None):
    contract = load_contract(
        contract_path, control_root=control_root,
        enforce_root_ownership=enforce_root_ownership, now=now,
    )
    if contract["task"] != expected_task:
        raise DispatchError("contract task does not match the requested task")
    if contract["authorization_revision"] != expected_authorization_revision:
        raise DispatchError("contract authorization revision does not match the request")
    if contract["tool"] != expected_tool:
        raise DispatchError("contract tool does not match the requested tool")
    try:
        with open(handoff_path, encoding="utf-8") as handle:
            payload = handle.read()
    except OSError as exc:
        raise DispatchError(f"cannot read handoff payload: {exc}") from exc
    directive = contract["intent_original"].strip()
    if not payload.startswith(directive + "\n\n"):
        raise DispatchError("handoff does not begin with the exact frozen intent")

    if contract["argv_profile"] == "claude_accept_edits":
        argv = [contract["executable"], "-p", "--output-format", "text",
                "--permission-mode", "acceptEdits"]
    else:
        argv = [contract["executable"], "exec", "-"]
    base = {
        "contract": contract["_path"], "task": contract["task"],
        "authorization_revision": contract["authorization_revision"],
        "tool": contract["tool"], "argv_profile": contract["argv_profile"],
        "working_directory": contract["working_directory"],
        "payload_sha256": _sha256(payload),
    }
    if dry_run:
        return dict(base, launched=False, dry_run=True, would_run=argv)
    result = subprocess.run(
        argv, input=payload, capture_output=True, text=True,
        cwd=contract["working_directory"], timeout=timeout,
    )
    return dict(
        base, launched=True, returncode=result.returncode,
        stdout=result.stdout, stderr=result.stderr,
        completion_status="transport_only_not_verified",
    )


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", required=True)
    parser.add_argument("--handoff", required=True)
    parser.add_argument("--task", required=True)
    parser.add_argument("--authorization-revision", required=True, type=int)
    parser.add_argument("--tool", required=True, choices=["claude", "codex"])
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = dispatch(
            args.contract, args.handoff, expected_task=args.task,
            expected_authorization_revision=args.authorization_revision,
            expected_tool=args.tool, timeout=args.timeout, dry_run=args.dry_run,
        )
    except (DispatchError, subprocess.TimeoutExpired) as exc:
        print(json.dumps({"launched": False, "completion_status": "not_dispatched",
                          "reason": str(exc)}))
        return 2
    print(json.dumps(result))
    return 0 if result.get("dry_run") or result.get("launched") else 1


if __name__ == "__main__":
    sys.exit(main())
