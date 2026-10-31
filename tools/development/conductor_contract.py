"""Pure compiler for a bounded CIS host-development transaction.

The compiler grants no authority and performs no I/O.  It turns an operator's
verbatim instruction plus explicit constraints into a canonical, hash-bound
packet suitable for continuity evaluation and a later execution adapter.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Iterable, Optional


CONTRACT_VERSION = "cis.development-conductor/v1"


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False)


def _hash(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _strings(name: str, values: Iterable[str]) -> tuple[str, ...]:
    result = tuple(str(value).strip() for value in values if str(value).strip())
    if not result:
        raise ValueError(f"{name} must contain at least one bounded item")
    if len(set(result)) != len(result):
        raise ValueError(f"{name} contains duplicate items")
    return result


def _optional_strings(name: str, values: Iterable[str]) -> tuple[str, ...]:
    result = tuple(str(value).strip() for value in values if str(value).strip())
    if len(set(result)) != len(result):
        raise ValueError(f"{name} contains duplicate items")
    return result


def _bounded_path(path: str) -> bool:
    return not (
        path in {"*", "**", "/", "."}
        or ".." in path.split("/")
        or any(char in path for char in "*?[]{}")
    )


@dataclass(frozen=True)
class DevelopmentIntent:
    operator_instruction: str
    expected_outcome: str
    task_id: str
    project_id: str
    prepared_context_refs: tuple[str, ...]
    repo_baseline: str
    allowed_files: tuple[str, ...]
    allowed_commands: tuple[str, ...]
    success_checks: tuple[str, ...]
    stop_conditions: tuple[str, ...]
    capability: str
    role: str
    backend_preference: Optional[str] = None


def compile_transaction(intent: DevelopmentIntent) -> dict:
    """Validate and compile a deterministic packet without mutating state."""
    instruction = intent.operator_instruction.strip()
    outcome = intent.expected_outcome.strip()
    task_id = intent.task_id.strip()
    project_id = intent.project_id.strip()
    baseline = intent.repo_baseline.strip()
    capability = intent.capability.strip()
    role = intent.role.strip()
    for name, value in (
        ("operator_instruction", instruction), ("expected_outcome", outcome),
        ("task_id", task_id), ("project_id", project_id),
        ("repo_baseline", baseline), ("capability", capability), ("role", role),
    ):
        if not value:
            raise ValueError(f"{name} is required")

    context_refs = _strings("prepared_context_refs", intent.prepared_context_refs)
    files = _strings("allowed_files", intent.allowed_files)
    commands = _optional_strings("allowed_commands", intent.allowed_commands)
    checks = _strings("success_checks", intent.success_checks)
    stops = _strings("stop_conditions", intent.stop_conditions)
    if any(not _bounded_path(path) for path in files):
        raise ValueError("allowed_files must be explicit repository-relative paths")
    if any(command.lower() in {
        "any", "all", "unrestricted", "*", "bash", "sh", "python",
        "python3", "node", "sudo",
    }
           for command in commands):
        raise ValueError("allowed_commands is unbounded")

    core = {
        "contract_version": CONTRACT_VERSION,
        "operator_instruction": instruction,
        "expected_outcome": outcome,
        "task": {"task_id": task_id, "project_id": project_id},
        "prepared_context_refs": list(context_refs),
        "repo_baseline": baseline,
        "scope": {
            "allowed_files": list(files),
            "allowed_commands": list(commands),
        },
        "success_checks": list(checks),
        "stop_conditions": list(stops),
        "executor": {"capability": capability, "role": role},
    }
    # Backend selection is a replaceable preference, never an authority grant.
    preference = (intent.backend_preference or "").strip()
    if preference:
        core["executor"]["backend_preference"] = preference
    transaction_id = _hash(core)
    return {
        **core,
        "transaction_id": transaction_id,
        "bindings": {
            "instruction_hash": _hash(instruction),
            "context_refs_hash": _hash(list(context_refs)),
            "repo_baseline_hash": _hash(baseline),
            "scope_hash": _hash(core["scope"]),
            "success_checks_hash": _hash(list(checks)),
            "stop_conditions_hash": _hash(list(stops)),
            "transaction_hash": transaction_id,
        },
        "authority": {
            "source": "operator_instruction",
            "compiler_grants_execution": False,
            "may_expand_scope": False,
        },
    }


def validate_transaction(packet: dict) -> None:
    """Recompute every compiler binding; raise when a packet was changed."""
    if not isinstance(packet, dict):
        raise ValueError("conductor transaction must be an object")
    required = {
        "contract_version", "operator_instruction", "expected_outcome", "task",
        "prepared_context_refs", "repo_baseline", "scope", "success_checks",
        "stop_conditions", "executor", "transaction_id", "bindings", "authority",
    }
    if not required.issubset(packet):
        raise ValueError("conductor transaction is incomplete")
    if packet["contract_version"] != CONTRACT_VERSION:
        raise ValueError("unsupported conductor contract version")
    core = {key: packet[key] for key in (
        "contract_version", "operator_instruction", "expected_outcome", "task",
        "prepared_context_refs", "repo_baseline", "scope", "success_checks",
        "stop_conditions", "executor",
    )}
    expected_transaction = _hash(core)
    expected_bindings = {
        "instruction_hash": _hash(packet["operator_instruction"]),
        "context_refs_hash": _hash(packet["prepared_context_refs"]),
        "repo_baseline_hash": _hash(packet["repo_baseline"]),
        "scope_hash": _hash(packet["scope"]),
        "success_checks_hash": _hash(packet["success_checks"]),
        "stop_conditions_hash": _hash(packet["stop_conditions"]),
        "transaction_hash": expected_transaction,
    }
    if packet["transaction_id"] != expected_transaction:
        raise ValueError("conductor transaction hash mismatch")
    if packet["bindings"] != expected_bindings:
        raise ValueError("conductor transaction binding mismatch")
    if packet["authority"] != {
        "source": "operator_instruction",
        "compiler_grants_execution": False,
        "may_expand_scope": False,
    }:
        raise ValueError("conductor authority declaration changed")
