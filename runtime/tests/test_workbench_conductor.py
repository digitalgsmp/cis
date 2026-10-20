"""Pure tests for the Workbench-to-Conductor approval adapter."""

import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "runtime"))

from workbench_conductor import (  # noqa: E402
    compile_proposal_transaction, require_exact_scope,
)
from tools.development.conductor_contract import validate_transaction  # noqa: E402


PROPOSAL = {
    "id": 7, "revision": 3, "project_id": "cis",
    "source_message_ids_json": json.dumps([10, 11]),
    "user_words": "Build the continuity-aware Workbench execution path.",
    "outcome": "One bounded development run reaches a replaceable backend.",
    "boundaries": "Stop if another file or command is required.",
    "success_criteria": "The contract is validated before dispatch.",
    "permitted_files_json": json.dumps(["runtime/workbench_app.py"]),
    "permitted_commands_json": json.dumps([]),
    "card_factory_card_id": 22,
}


def run():
    packet = compile_proposal_transaction(
        PROPOSAL, project_name="CIS", card_fingerprint="a" * 64,
        target="claude", mode="implement", repo_baseline="git:abc;dirty:def",
    )
    validate_transaction(packet)
    checks = [
        ("verbatim operator words retained",
         packet["operator_instruction"] == PROPOSAL["user_words"]),
        ("source messages become context refs",
         "workbench-message:10" in packet["prepared_context_refs"]),
        ("confirmed proposal scope is compiled",
         packet["scope"]["allowed_files"] == ["runtime/workbench_app.py"]),
        ("backend is a preference",
         packet["executor"]["backend_preference"] == "claude"),
        ("compiler does not grant execution",
         packet["authority"]["compiler_grants_execution"] is False),
    ]
    require_exact_scope(packet, files=None, commands=None)
    checks.append(("omitted approval scope reuses confirmed scope", True))
    try:
        require_exact_scope(packet, files=["runtime/extra.py"], commands=[])
        expansion_blocked = False
    except ValueError:
        expansion_blocked = True
    checks.append(("approval-time scope expansion blocked", expansion_blocked))
    try:
        compile_proposal_transaction(
            {**PROPOSAL, "boundaries": ""}, project_name="CIS",
            card_fingerprint="a" * 64, target="claude", mode="implement",
            repo_baseline="git:abc;dirty:def",
        )
        missing_stop_blocked = False
    except ValueError:
        missing_stop_blocked = True
    checks.append(("missing stop condition blocks compilation", missing_stop_blocked))

    for label, passed in checks:
        print(f"{'PASS' if passed else 'FAIL'}  {label}")
    failed = [label for label, passed in checks if not passed]
    print(f"\n{len(checks) - len(failed)}/{len(checks)} passed")
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    run()
