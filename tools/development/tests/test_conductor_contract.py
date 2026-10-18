"""Deterministic tests for the pure host Conductor contract compiler."""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from conductor_contract import (  # noqa: E402
    DevelopmentIntent, compile_transaction, validate_transaction,
)


def valid(**changes):
    values = dict(
        operator_instruction="Implement the bounded continuity slice.",
        expected_outcome="Tests prove a hash-bound transaction.",
        task_id="WB.1", project_id="cis",
        prepared_context_refs=("continuity:177", "queue:WB.1"),
        repo_baseline="git:abc123+dirty-manifest:deadbeef",
        allowed_files=("runtime/continuity_interceptor.py",),
        allowed_commands=("python3 runtime/tests/test_continuity_interceptor.py",),
        success_checks=("continuity unit tests pass",),
        stop_conditions=("scope change required", "test regression outside scope"),
        capability="implementation", role="bounded implementer",
        backend_preference="claude-code",
    )
    values.update(changes)
    return DevelopmentIntent(**values)


def run():
    packet = compile_transaction(valid())
    checks = [
        ("deterministic", packet == compile_transaction(valid())),
        ("transaction hash bound", packet["transaction_id"] ==
         packet["bindings"]["transaction_hash"]),
        ("backend is only preference", packet["executor"]["backend_preference"] ==
         "claude-code" and packet["authority"]["may_expand_scope"] is False),
        ("compiler grants no execution",
         packet["authority"]["compiler_grants_execution"] is False),
    ]
    validate_transaction(packet)
    checks.append(("compiled packet revalidates", True))
    no_shell = compile_transaction(valid(allowed_commands=()))
    checks.append(("explicitly empty command scope is bounded", no_shell["scope"]["allowed_commands"] == []))
    changed = dict(packet)
    changed["expected_outcome"] = "silently changed"
    try:
        validate_transaction(changed)
        changed_rejected = False
    except ValueError:
        changed_rejected = True
    checks.append(("post-compile change rejected", changed_rejected))
    invalid = (
        {"operator_instruction": ""}, {"expected_outcome": ""},
        {"allowed_files": ("*",)}, {"allowed_commands": ("unrestricted",)},
        {"success_checks": ()}, {"stop_conditions": ()},
    )
    for change in invalid:
        try:
            compile_transaction(valid(**change))
            rejected = False
        except ValueError:
            rejected = True
        checks.append((f"rejects {next(iter(change))}", rejected))
    for label, passed in checks:
        print(f"{'PASS' if passed else 'FAIL'}  {label}")
    failed = [label for label, passed in checks if not passed]
    print(f"\n{len(checks) - len(failed)}/{len(checks)} passed")
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    run()
