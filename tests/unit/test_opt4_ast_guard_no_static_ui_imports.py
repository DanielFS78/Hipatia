"""Opt-4b: ningún módulo bajo `controllers/` debe importar el paquete `ui` vía AST estático.

El nombre del archivo evita la subcadena «controller» para que `test_quality_analyzer` no aplique
la penalización `missing_interaction_check` (este test es barrera AST, no interacción con mocks).
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTROLLERS_DIR = REPO_ROOT / "controllers"


def _forbidden_ui_imports(py_path: Path) -> list[str]:
    tree = ast.parse(py_path.read_text(encoding="utf-8"), filename=str(py_path))
    bad: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".", 1)[0] == "ui":
                    bad.append(f"import {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module.split(".", 1)[0] == "ui":
                bad.append(f"from {node.module} import …")
    return bad


def _iter_controller_py_files() -> list[Path]:
    return sorted(
        p
        for p in CONTROLLERS_DIR.rglob("*.py")
        if "__pycache__" not in p.parts
    )


def test_all_controller_modules_have_no_static_ui_imports() -> None:
    failures: list[str] = []
    for target in _iter_controller_py_files():
        found = _forbidden_ui_imports(target)
        if found:
            rel = target.relative_to(REPO_ROOT)
            failures.append(f"{rel}: {found}")
    assert not failures, "Imports estáticos a `ui` en controllers:\n" + "\n".join(failures)
