"""Containment regression for the Eric approval provenance gate."""

import ast
from pathlib import Path


def test_export_agreement_check_is_read_only():
    gate_path = Path(__file__).parents[2] / "tools/gates/gate_eric_approval.py"
    tree = ast.parse(gate_path.read_text())
    function = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "check_6_export_agreement"
    )
    constants = {
        node.value for node in ast.walk(function)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }

    assert not any("generate_all.py" in value for value in constants)
    assert any("gate_export_agreement.sh" in value for value in constants)

