"""Workbench adapter for the pure host-development Conductor contract."""

from __future__ import annotations

import json
import os
import sys
from typing import Mapping, Any

_IMPORT_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _IMPORT_REPO_ROOT not in sys.path:
    sys.path.insert(0, _IMPORT_REPO_ROOT)
from tools.development.conductor_contract import (
    DevelopmentIntent,
    compile_transaction,
)


def _json_list(value: Any, name: str) -> tuple[str, ...]:
    try:
        parsed = json.loads(value or "[]") if isinstance(value, str) else value
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ValueError(f"{name} is not valid JSON") from exc
    if not isinstance(parsed, list) or not all(isinstance(item, str) for item in parsed):
        raise ValueError(f"{name} must be a list of strings")
    return tuple(parsed)


def compile_proposal_transaction(
    proposal: Mapping[str, Any],
    *,
    project_name: str,
    card_fingerprint: str,
    target: str,
    mode: str,
    repo_baseline: str,
) -> dict:
    """Compile exactly the proposal revision the operator approved."""
    if mode not in ("implement", "review"):
        raise ValueError("mode must be 'implement' or 'review'")
    if target not in ("claude", "codex"):
        raise ValueError("target must be 'claude' or 'codex'")
    proposal_id = proposal["id"]
    revision = proposal["revision"]
    try:
        source_ids = json.loads(proposal["source_message_ids_json"] or "[]")
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ValueError("source_message_ids_json is not valid JSON") from exc
    if not isinstance(source_ids, list) or not all(
            isinstance(item, (str, int)) for item in source_ids):
        raise ValueError("source_message_ids_json must be a list of identifiers")
    permitted_files = _json_list(proposal["permitted_files_json"],
                                 "permitted_files_json")
    permitted_commands = _json_list(proposal["permitted_commands_json"],
                                    "permitted_commands_json")
    context_refs = [
        f"workbench-proposal:{proposal_id}:revision:{revision}",
        f"card-factory-card:{proposal['card_factory_card_id']}:sha256:{card_fingerprint}",
    ]
    context_refs.extend(f"workbench-message:{message_id}" for message_id in source_ids)
    boundaries = str(proposal["boundaries"] or "").strip()
    success = str(proposal["success_criteria"] or "").strip()
    return compile_transaction(DevelopmentIntent(
        operator_instruction=str(proposal["user_words"] or ""),
        expected_outcome=str(proposal["outcome"] or ""),
        task_id=f"workbench-proposal-{proposal_id}-r{revision}",
        project_id=str(project_name or proposal["project_id"]),
        prepared_context_refs=tuple(context_refs),
        repo_baseline=repo_baseline,
        allowed_files=permitted_files,
        allowed_commands=permitted_commands,
        success_checks=(success,) if success else (),
        stop_conditions=(boundaries,) if boundaries else (),
        capability="repository implementation" if mode == "implement" else "independent review",
        role="bounded implementer" if mode == "implement" else "independent reviewer",
        backend_preference=target,
    ))


def require_exact_scope(transaction: Mapping[str, Any], *, files, commands) -> None:
    """Reject approval-time scope substitution or expansion."""
    expected_files = list(transaction["scope"]["allowed_files"])
    expected_commands = list(transaction["scope"]["allowed_commands"])
    supplied_files = expected_files if files is None else list(files)
    supplied_commands = expected_commands if commands is None else list(commands)
    if supplied_files != expected_files:
        raise ValueError("permitted_files differs from the confirmed proposal scope")
    if supplied_commands != expected_commands:
        raise ValueError("permitted_commands differs from the confirmed proposal scope")
