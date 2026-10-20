#!/usr/bin/env python3
import datetime as dt
import hashlib
import json
import os
import stat
import sys
import tempfile

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from tools.development import control_contract as cc
from tools.development import control_dispatch as cd


def _inputs(tmp):
    work = os.path.join(tmp, "work")
    os.makedirs(work)
    fake = os.path.join(tmp, "claude")
    with open(fake, "w") as handle:
        handle.write("#!/bin/sh\ncat\n")
    os.chmod(fake, stat.S_IRWXU)
    proposal = {
        "proposal_version": cc.PROPOSAL_VERSION,
        "task": "TEST.1", "authorization_revision": 7,
        "intent_original": "Eric's exact instruction.",
        "intent_interpretation": "Implement only the bounded fixture.",
        "tool": "claude", "working_directory": work, "ttl_seconds": 300,
    }
    policy = {
        "policy_version": cc.POLICY_VERSION, "max_ttl_seconds": 600,
        "allowed_working_roots": [work],
        "tools": {"claude": {"executable": fake,
                               "executable_sha256": hashlib.sha256(
                                   open(fake, "rb").read()).hexdigest(),
                               "argv_profile": "claude_accept_edits"}},
    }
    return proposal, policy, work


def test_compiler_preserves_original_and_interpretation_separately():
    with tempfile.TemporaryDirectory() as tmp:
        proposal, policy, _ = _inputs(tmp)
        contract = cc.compile_contract(
            proposal, policy, now=dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc))
        assert contract["intent_original"] == "Eric's exact instruction."
        assert contract["intent_interpretation"] == "Implement only the bounded fixture."
        assert contract["intent_sha256"] != contract["interpretation_sha256"]


def test_compiler_rejects_workspace_widening():
    with tempfile.TemporaryDirectory() as tmp:
        proposal, policy, _ = _inputs(tmp)
        proposal["working_directory"] = tmp
        try:
            cc.compile_contract(proposal, policy)
            assert False, "workspace widening was accepted"
        except cc.ContractCompileError as exc:
            assert "outside fixed policy roots" in str(exc)


def test_frozen_contract_is_dispatcher_compatible_and_read_only():
    with tempfile.TemporaryDirectory() as tmp:
        proposal, policy, _ = _inputs(tmp)
        root = os.path.join(tmp, "control")
        output = os.path.join(root, "contracts")
        os.makedirs(output)
        proposal_path = os.path.join(tmp, "proposal.json")
        policy_path = os.path.join(tmp, "policy.json")
        with open(proposal_path, "w") as handle:
            json.dump(proposal, handle)
        with open(policy_path, "w") as handle:
            json.dump(policy, handle)
        destination, contract = cc.freeze_contract(
            proposal_path, policy_path, output, control_root=root,
            enforce_root_ownership=False)
        assert stat.S_IMODE(os.stat(destination).st_mode) == 0o444
        loaded = cd.load_contract(destination, control_root=root,
                                  enforce_root_ownership=False)
        assert loaded["intent_sha256"] == contract["intent_sha256"]


def run():
    tests = [
        test_compiler_preserves_original_and_interpretation_separately,
        test_compiler_rejects_workspace_widening,
        test_frozen_contract_is_dispatcher_compatible_and_read_only,
    ]
    rows = []
    for test in tests:
        try:
            test()
            rows.append(f"{test.__name__}: PASS")
        except Exception as exc:
            rows.append(f"{test.__name__}: FAIL — {exc}")
    print("\n".join(rows))
    failed = [row for row in rows if ": FAIL" in row]
    print(f"\n{len(rows)-len(failed)}/{len(rows)} passed.")
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    run()
