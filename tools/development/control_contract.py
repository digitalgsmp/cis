#!/usr/bin/env python3
"""Compile a descriptive proposal into a fixed-boundary dispatch contract.

The proposal supplies meaning: exact human instruction, a separately
labelled model interpretation, task identity, requested tool/workspace and
TTL.  The root-owned policy supplies authority: executable, argv profile,
allowed workspace roots and maximum TTL.  Proposal data can narrow those
fixed boundaries but cannot widen or replace them.

The installed compiler belongs in /opt/cis-control/bin.  This repository
copy is source and test material, not runtime authority.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
import re
import sys
import tempfile

try:
    from .control_dispatch import (
        CONTRACT_VERSION, CONTROL_ROOT, DispatchError, _assert_root_owned_chain,
        _sha256_file,
    )
except ImportError:  # installed beside cis-dispatch under /opt/cis-control/bin
    from control_dispatch import (  # type: ignore
        CONTRACT_VERSION, CONTROL_ROOT, DispatchError, _assert_root_owned_chain,
        _sha256_file,
    )

POLICY_VERSION = "cis-dispatch-policy-v1"
PROPOSAL_VERSION = "cis-dispatch-proposal-v1"
TASK_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$")


class ContractCompileError(Exception):
    pass


def _hash(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _load_json(path, label):
    try:
        with open(path, encoding="utf-8") as handle:
            value = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractCompileError(f"cannot read {label}: {exc}") from exc
    if not isinstance(value, dict):
        raise ContractCompileError(f"{label} must be a JSON object")
    return value


def _below(path, roots):
    resolved = os.path.realpath(path)
    return any(resolved == root or resolved.startswith(root + os.sep) for root in roots)


def compile_contract(proposal, policy, *, now=None):
    proposal_keys = {
        "proposal_version", "task", "authorization_revision", "intent_original",
        "intent_interpretation", "tool", "working_directory", "ttl_seconds",
    }
    policy_keys = {
        "policy_version", "max_ttl_seconds", "allowed_working_roots", "tools",
    }
    if set(proposal) != proposal_keys:
        raise ContractCompileError(
            f"proposal shape mismatch; missing={sorted(proposal_keys-set(proposal))}, "
            f"unknown={sorted(set(proposal)-proposal_keys)}")
    if set(policy) != policy_keys:
        raise ContractCompileError(
            f"policy shape mismatch; missing={sorted(policy_keys-set(policy))}, "
            f"unknown={sorted(set(policy)-policy_keys)}")
    if proposal["proposal_version"] != PROPOSAL_VERSION:
        raise ContractCompileError("unsupported proposal_version")
    if policy["policy_version"] != POLICY_VERSION:
        raise ContractCompileError("unsupported policy_version")
    task = proposal["task"]
    if not isinstance(task, str) or not TASK_RE.fullmatch(task):
        raise ContractCompileError("task has an invalid control-plane identifier")
    revision = proposal["authorization_revision"]
    if not isinstance(revision, int) or revision < 1:
        raise ContractCompileError("authorization_revision must be a positive integer")
    original = proposal["intent_original"]
    interpretation = proposal["intent_interpretation"]
    if not isinstance(original, str) or not original.strip():
        raise ContractCompileError("intent_original must be non-empty verbatim text")
    if not isinstance(interpretation, str):
        raise ContractCompileError("intent_interpretation must be separately supplied text")
    ttl = proposal["ttl_seconds"]
    maximum = policy["max_ttl_seconds"]
    if (not isinstance(ttl, int) or isinstance(ttl, bool) or ttl < 1
            or not isinstance(maximum, int) or maximum < 1 or ttl > maximum):
        raise ContractCompileError("ttl_seconds is invalid or exceeds policy maximum")
    tool = proposal["tool"]
    tool_policy = policy["tools"].get(tool) if isinstance(policy["tools"], dict) else None
    if (not isinstance(tool_policy, dict)
            or set(tool_policy) != {"executable", "executable_sha256", "argv_profile"}):
        raise ContractCompileError("requested tool is absent from fixed policy")
    roots = policy["allowed_working_roots"]
    if not isinstance(roots, list) or not roots or not all(isinstance(v, str) for v in roots):
        raise ContractCompileError("policy allowed_working_roots must be a non-empty string list")
    resolved_roots = [os.path.realpath(v) for v in roots]
    workdir = os.path.realpath(proposal["working_directory"])
    if not os.path.isdir(workdir) or not _below(workdir, resolved_roots):
        raise ContractCompileError("working_directory is absent or outside fixed policy roots")
    executable = os.path.realpath(tool_policy["executable"])
    profiles = {"claude": "claude_accept_edits", "codex": "codex_exec"}
    if profiles.get(tool) != tool_policy["argv_profile"]:
        raise ContractCompileError("policy tool/argv_profile pair is not recognized")
    if not os.path.isfile(executable) or not os.access(executable, os.X_OK):
        raise ContractCompileError("policy executable is absent or not executable")
    if _sha256_file(executable) != tool_policy["executable_sha256"]:
        raise ContractCompileError("policy executable hash does not match current bytes")
    instant = now or dt.datetime.now(dt.timezone.utc)
    if instant.tzinfo is None:
        raise ContractCompileError("compiler time must be timezone-aware")
    expires = instant.astimezone(dt.timezone.utc) + dt.timedelta(seconds=ttl)
    return {
        "contract_version": CONTRACT_VERSION,
        "task": task,
        "authorization_revision": revision,
        "intent_original": original.strip(),
        "intent_sha256": _hash(original.strip()),
        "intent_interpretation": interpretation,
        "interpretation_sha256": _hash(interpretation),
        "tool": tool,
        "executable": executable,
        "executable_sha256": tool_policy["executable_sha256"],
        "argv_profile": tool_policy["argv_profile"],
        "working_directory": workdir,
        "expires_at": expires.isoformat(),
    }


def freeze_contract(proposal_path, policy_path, output_dir, *, control_root=CONTROL_ROOT,
                    enforce_root_ownership=True, now=None):
    if enforce_root_ownership:
        _assert_root_owned_chain(policy_path, control_root)
        _assert_root_owned_chain(output_dir, control_root)
    proposal = _load_json(proposal_path, "proposal")
    policy = _load_json(policy_path, "policy")
    contract = compile_contract(proposal, policy, now=now)
    os.makedirs(output_dir, exist_ok=True)
    name = f"{contract['task']}-r{contract['authorization_revision']}-{contract['intent_sha256'][:16]}.json"
    destination = os.path.join(output_dir, name)
    if os.path.exists(destination):
        raise ContractCompileError("contract destination already exists; contracts are immutable")
    fd, temporary = tempfile.mkstemp(prefix=".contract-", dir=output_dir, text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(contract, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o444)
        os.replace(temporary, destination)
    except Exception:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise
    return destination, contract


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--proposal", required=True)
    parser.add_argument("--policy", default="/opt/cis-control/policy/dispatch-policy.json")
    parser.add_argument("--output-dir", default="/opt/cis-control/contracts")
    args = parser.parse_args(argv)
    try:
        destination, contract = freeze_contract(args.proposal, args.policy, args.output_dir)
    except (ContractCompileError, DispatchError, OSError) as exc:
        print(json.dumps({"frozen": False, "reason": str(exc)}))
        return 2
    print(json.dumps({"frozen": True, "path": destination,
                      "task": contract["task"],
                      "intent_sha256": contract["intent_sha256"],
                      "interpretation_sha256": contract["interpretation_sha256"]}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
