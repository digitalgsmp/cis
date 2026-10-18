"""Containment regressions for the production pipeline relay."""

import ast
import inspect
import textwrap

from runtime.abstraction.pipeline_relay import PipelineRelay


def test_pattern_catalog_does_not_write_into_project_source():
    """Catalog state belongs to the run record, not the read-only repo mount."""
    source = textwrap.dedent(inspect.getsource(PipelineRelay._pattern_catalog))
    tree = ast.parse(source)

    calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
    direct_writes = [
        node
        for node in calls
        if isinstance(node.func, ast.Name) and node.func.id == "open"
    ]
    directory_writes = [
        node
        for node in calls
        if isinstance(node.func, ast.Attribute)
        and node.func.attr == "makedirs"
    ]

    assert direct_writes == []
    assert directory_writes == []
    assert "_complete_round" in source
