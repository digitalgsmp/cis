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

from tools.development import control_dispatch as cd

RESULTS = []


def _fixture(tmp, *, expired=False, intent="Do the bounded thing."):
    root = os.path.join(tmp, "control")
    contracts = os.path.join(root, "contracts", "TEST")
    work = os.path.join(tmp, "work")
    os.makedirs(contracts)
    os.makedirs(work)
    fake = os.path.join(tmp, "claude")
    with open(fake, "w") as handle:
        handle.write("#!/bin/sh\nprintf 'ARGS:%s\\n' \"$*\"\ncat\n")
    os.chmod(fake, stat.S_IRWXU)
    expires = dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=-1 if expired else 1)
    contract = {
        "contract_version": cd.CONTRACT_VERSION,
        "task": "TEST", "authorization_revision": 1,
        "intent_original": intent,
        "intent_sha256": hashlib.sha256(intent.encode()).hexdigest(),
        "intent_interpretation": "Bounded test interpretation.",
        "interpretation_sha256": hashlib.sha256(
            b"Bounded test interpretation.").hexdigest(),
        "tool": "claude", "executable": fake,
        "executable_sha256": hashlib.sha256(
            open(fake, "rb").read()).hexdigest(),
        "argv_profile": "claude_accept_edits",
        "working_directory": work,
        "expires_at": expires.isoformat(),
    }
    path = os.path.join(contracts, "contract.json")
    with open(path, "w") as handle:
        json.dump(contract, handle)
    handoff = os.path.join(tmp, "handoff.txt")
    with open(handoff, "w") as handle:
        handle.write(intent + "\n\nreference context")
    return root, path, handoff


def test_dispatcher_owns_claude_edit_flag():
    with tempfile.TemporaryDirectory() as tmp:
        root, contract, handoff = _fixture(tmp)
        result = cd.dispatch(contract, handoff, expected_task="TEST",
                             expected_authorization_revision=1,
                             expected_tool="claude", control_root=root,
                             enforce_root_ownership=False)
        assert result["launched"] is True
        assert "--permission-mode acceptEdits" in result["stdout"]
        assert "Do the bounded thing." in result["stdout"]


def test_dispatcher_rejects_payload_not_bound_to_frozen_intent():
    with tempfile.TemporaryDirectory() as tmp:
        root, contract, handoff = _fixture(tmp)
        with open(handoff, "w") as handle:
            handle.write("Do something broader.\n\nreference context")
        try:
            cd.dispatch(contract, handoff, expected_task="TEST",
                        expected_authorization_revision=1,
                        expected_tool="claude", control_root=root,
                        enforce_root_ownership=False)
            assert False, "mismatched payload was accepted"
        except cd.DispatchError as exc:
            assert "exact frozen intent" in str(exc)


def test_dispatcher_rejects_expired_contract():
    with tempfile.TemporaryDirectory() as tmp:
        root, contract, handoff = _fixture(tmp, expired=True)
        try:
            cd.dispatch(contract, handoff, expected_task="TEST",
                        expected_authorization_revision=1,
                        expected_tool="claude", control_root=root,
                        enforce_root_ownership=False)
            assert False, "expired contract was accepted"
        except cd.DispatchError as exc:
            assert "expired" in str(exc)


def test_dispatcher_rejects_contract_for_another_task():
    with tempfile.TemporaryDirectory() as tmp:
        root, contract, handoff = _fixture(tmp)
        try:
            cd.dispatch(contract, handoff, expected_task="OTHER",
                        expected_authorization_revision=1,
                        expected_tool="claude", control_root=root,
                        enforce_root_ownership=False)
            assert False, "cross-task contract reuse was accepted"
        except cd.DispatchError as exc:
            assert "task does not match" in str(exc)


def test_dispatcher_rejects_changed_executable_bytes():
    with tempfile.TemporaryDirectory() as tmp:
        root, contract, handoff = _fixture(tmp)
        with open(os.path.join(tmp, "claude"), "a") as handle:
            handle.write("# changed after freeze\n")
        try:
            cd.dispatch(contract, handoff, expected_task="TEST",
                        expected_authorization_revision=1,
                        expected_tool="claude", control_root=root,
                        enforce_root_ownership=False)
            assert False, "changed executable was accepted"
        except cd.DispatchError as exc:
            assert "executable hash" in str(exc)


def run():
    tests = [
        test_dispatcher_owns_claude_edit_flag,
        test_dispatcher_rejects_payload_not_bound_to_frozen_intent,
        test_dispatcher_rejects_expired_contract,
        test_dispatcher_rejects_contract_for_another_task,
        test_dispatcher_rejects_changed_executable_bytes,
    ]
    for test in tests:
        try:
            test()
            RESULTS.append(f"{test.__name__}: PASS")
        except Exception as exc:
            RESULTS.append(f"{test.__name__}: FAIL — {exc}")
    print("\n".join(RESULTS))
    failed = [row for row in RESULTS if ": FAIL" in row]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} passed.")
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    run()
