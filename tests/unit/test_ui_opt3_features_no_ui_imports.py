"""Opt-3: la capa `features` no debe importar el paquete top-level `ui` (AST estático)."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

REPO_ROOT = Path(__file__).resolve().parents[2]
FEATURES_DIR = REPO_ROOT / "features"


def _collect_py_files() -> list[Path]:
    return sorted(p for p in FEATURES_DIR.rglob("*.py") if "__pycache__" not in p.parts)


def _forbidden_ui_imports(py_path: Path) -> list[str]:
    text = py_path.read_text(encoding="utf-8")
    tree = ast.parse(text, filename=str(py_path))
    bad: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".", 1)[0] == "ui":
                    bad.append(f"import {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                if node.module.split(".", 1)[0] == "ui":
                    bad.append(f"from {node.module} import …")
    return bad


@pytest.mark.parametrize("py_path", _collect_py_files(), ids=lambda p: str(p.relative_to(REPO_ROOT)))
def test_features_module_has_no_ui_imports(py_path: Path) -> None:
    found = _forbidden_ui_imports(py_path)
    assert not found, f"{py_path.relative_to(REPO_ROOT)}: imports a `ui` prohibidos en features: {found}"
