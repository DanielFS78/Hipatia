# -*- coding: utf-8 -*-
"""Tests del analizador AST de capas (`scripts/architecture_layer_edges.py`)."""

from __future__ import annotations

import ast
import importlib.util
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT = _ROOT / "scripts" / "architecture_layer_edges.py"


def _load_script():
    spec = importlib.util.spec_from_file_location("architecture_layer_edges", _SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def ale():
    return _load_script()


def test_collect_import_targets_basic(ale) -> None:
    tree = ast.parse(
        "import os\n"
        "from core.dtos import X\n"
        "from ui.widgets.foo import bar\n",
        filename="<test>",
    )
    t = ale.collect_import_targets(tree)
    assert "os" in t
    assert "core.dtos" in t
    assert "ui.widgets.foo" in t


def test_module_layer(ale) -> None:
    assert ale.module_layer("core.services.worker_service") == "core"
    assert ale.module_layer("ui.main_window") == "ui"
    assert ale.module_layer("stdlib_only") is None


def test_build_layer_edge_list(ale) -> None:
    modules = {
        "ui.a": {"core.dtos", "localpkg"},
        "core.b": {"database.models"},
        "database.c": {"core.dtos"},
    }
    edges = ale.build_layer_edge_list(modules)
    assert ("ui", "core") in edges
    assert ("core", "database") in edges
    assert ("database", "core") in edges


def test_find_simple_cycles_two_node(ale) -> None:
    adj = {("a", "b"), ("b", "a")}
    c = ale.find_simple_cycles(adj)
    assert any(len(x) >= 3 and x[0] == x[-1] for x in c)


def test_repo_scan_non_empty(ale) -> None:
    root = ale.repo_root()
    modules = ale.scan_layers(root)
    assert len(modules) > 50
    assert any(m.startswith("ui.") for m in modules)
    assert any(m.startswith("controllers.") for m in modules)
