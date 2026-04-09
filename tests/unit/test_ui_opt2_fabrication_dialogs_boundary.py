"""Opt-2: la capa ui no debe importar database (AST estático, sin TYPE_CHECKING)."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

REPO_ROOT = Path(__file__).resolve().parents[2]


def _forbidden_database_imports(py_path: Path) -> list[str]:
    text = py_path.read_text(encoding="utf-8")
    tree = ast.parse(text, filename=str(py_path))
    bad: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".", 1)[0]
                if root == "database":
                    bad.append(f"import {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                root = node.module.split(".", 1)[0]
                if root == "database":
                    bad.append(f"from {node.module} import …")
    return bad


def test_create_dialog_has_no_database_imports() -> None:
    path = REPO_ROOT / "ui" / "dialogs" / "fabrication" / "create_dialog.py"
    found = _forbidden_database_imports(path)
    assert not found, f"create_dialog.py no debe importar database: {found}"


def test_selection_dialogs_has_no_database_imports() -> None:
    path = REPO_ROOT / "ui" / "dialogs" / "fabrication" / "selection_dialogs.py"
    found = _forbidden_database_imports(path)
    assert not found, f"selection_dialogs.py no debe importar database: {found}"
