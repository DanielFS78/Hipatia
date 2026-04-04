"""
Script ejecutable (`test_quality_analyzer`): automatización, informes o mantenimiento del proyecto (no forma parte del runtime de la app).
"""

import os
import re
import json
from pathlib import Path
from typing import Any
import ast

# ---------------------------------------------------------------------------
# Patrones de detección — compilados una sola vez para rendimiento
# ---------------------------------------------------------------------------

# Mocks ESTRICTOS: create_autospec(), MagicMock(spec=...), autospec=True
_RE_STRICT_MOCK = re.compile(
    r'create_autospec\s*\('
    r'|MagicMock\s*\(\s*spec\s*='
    r'|Mock\s*\(\s*spec\s*='
    r'|autospec\s*=\s*True'
    r'|spec_set\s*='
)

# Mocks SUELTOS: MagicMock() o Mock() sin ningún spec
_RE_LOOSE_MOCK = re.compile(r'\bMagicMock\s*\(\s*\)|\bMock\s*\(\s*\)')

# Copias Finder: test_foo 2.py, test_foo 3.py, conftest 2.py, …
_RE_FINDER_DUP_TEST = re.compile(r" \d+\.py$")
_RE_FINDER_DUP_CONFTEST = re.compile(r"^conftest \d+\.py$")

# Patches SIN autospec (patch("...") sin autospec=True ni new_callable)
_RE_PATCH_NO_AUTOSPEC = re.compile(
    r'@patch\s*\([^)]*\)(?!\s*#\s*noqa)'
)
_RE_PATCH_WITH_AUTOSPEC = re.compile(
    r'@patch\s*\([^)]*autospec\s*=\s*True[^)]*\)'
    r'|@patch\s*\([^)]*new_callable\s*=[^)]*\)'
    r'|@patch\s*\([^)]*new\s*=[^)]*\)'
    r'|patch\s*\([^)]*autospec\s*=\s*True[^)]*\)'
    r'|patch\s*\([^)]*new\s*=[^)]*\)'
)

# Verificación de interacciones
_RE_ASSERT_CALLED = re.compile(
    r'\.assert_called_once_with\s*\('
    r'|\.assert_called_with\s*\('
    r'|\.assert_any_call\s*\('
    r'|\.assert_called_once\s*\('
    r'|\.assert_called\s*\('
    r'|\.assert_not_called\s*\('
    r'|\.call_args_list'
    r'|\.call_count'
)

_RE_ASSERT_CALLED_NO_ARGS = re.compile(r'\.assert_called_once\s*\(\s*\)')

_RE_ASSERT_CALLED_WITH_ARGS = re.compile(
    r'\.assert_called_once_with\s*\('
    r'|\.assert_called_with\s*\('
    r'|\.assert_any_call\s*\('
)

_RE_ISINSTANCE_DTO = re.compile(r'isinstance\s*\([^,]+,\s*\w*DTO\w*\s*\)')
_RE_DOCSTRING = re.compile(r'^\s*("""|\'\'\').+', re.MULTILINE | re.DOTALL)

_RE_MOCK_SESSION = re.compile(
    # Detect real SQLAlchemy Session mocking patterns.
    # IMPORTANT: avoid false positives for "session_controller" and similar app objects.
    r'MagicMock\s*\(\s*\).*\bsession(?!_controller)\b'
    r'|\bsession(?!_controller)\b.*MagicMock\s*\(\s*\)'
    r'|mock_session\s*=\s*MagicMock\s*\(\s*\)'
    r'|MagicMock\s*\(\s*spec\s*=\s*[Ss]ession\b'
    r'|MagicMock\s*\(\s*spec\s*=\s*\[[^\]]*\bSession\b[^\]]*\]'
)

_RE_SPEC_OBJECT = re.compile(r'MagicMock\s*\(\s*spec\s*=\s*object\s*\)')
_RE_TEST_FUNC = re.compile(r'^\s*def\s+(test_\w+)\s*\(', re.MULTILINE)
_RE_ANY_ASSERT = re.compile(r'\bassert\b')
_RE_TRIVIAL_ASSERT_TRUE = re.compile(r'^\s*assert\s+True\s*(#.*)?$', re.MULTILINE)
_RE_TRIVIAL_ASSERT_TRUE_JUSTIFIED = re.compile(
    r'^\s*assert\s+True\s*#\s*smoke_test\s*:\s*.+$',
    re.MULTILINE
)

_CONTROLLER_SERVICE_PATTERN = re.compile(
    r'controller|service|manager',
    re.IGNORECASE
)

# ---------------------------------------------------------------------------
# Detección de dependencias inevitables (techo real)
# ---------------------------------------------------------------------------

# Importa PyQt6/PyQt5 → MagicMock() de widgets Qt son inevitables
_RE_QT_IMPORT = re.compile(r'from PyQt6|import PyQt6|from PyQt5|import PyQt5')

# Importa docx (python-docx) → MagicMock() de objetos docx son inevitables
_RE_DOCX_IMPORT = re.compile(r"sys\.modules\[.docx|from docx|import docx")

# Targets de @patch que no requieren autospec (builtins, Qt dialogs, OS, etc.)
_EXTERNAL_PATCH_WHITELIST = {
    "builtins.",
    "QFileDialog",
    "QDialog",
    "QMessageBox",
    "platform.",
    "subprocess.",
    "os.startfile",
    "shutil.",
    "pathlib.Path",
    "controllers.schedule_controller.QDialog",
    "controllers.schedule_controller.QFormLayout",
    "controllers.schedule_controller.QTimeEdit",
    "controllers.schedule_controller.QDialogButtonBox",
    "controllers.schedule_controller.get_add_break_dialog_class",
    "controllers.calculation_controller.QFileDialog",
    "controllers.calculation_controller.getattr",
}


def _is_whitelisted_patch(patch_target: str) -> bool:
    """Devuelve True si el target del patch está en la whitelist de inevitables."""
    for prefix in _EXTERNAL_PATCH_WHITELIST:
        if prefix in patch_target:
            return True
    return False


def _count_inevitable_patches(content: str) -> int:
    """Cuenta @patch sin autospec que son inevitables (builtins, Qt, OS)."""
    count = 0
    for match in re.finditer(r'@patch\s*\(\s*[\'"]([^\'"]+)[\'"]', content):
        target = match.group(1)
        has_autospec = False
        # Buscar si la misma línea o la siguiente tiene autospec=True
        pos = match.start()
        snippet = content[pos:pos+200]
        if "autospec=True" in snippet or "new_callable=" in snippet or "new=" in snippet:
            has_autospec = True
        if not has_autospec and _is_whitelisted_patch(target):
            count += 1
    return count


def _count_inevitable_loose_mocks(content: str, has_qt: bool, has_docx: bool) -> int:
    """
    Cuenta MagicMock() sueltos que son inevitables por dependencias externas sin stubs.

    - Qt: widgets PyQt6 no tienen stubs de tipo → MagicMock() es la única opción
    - docx: python-docx no tiene stubs → MagicMock() para Document, Run, etc.
    """
    if not has_qt and not has_docx:
        return 0

    total_loose = len(_RE_LOOSE_MOCK.findall(content))
    if total_loose == 0:
        return 0

    # Heurística: contar MagicMock() que aparecen en contexto de Qt o docx
    inevitable = 0
    lines = content.splitlines()
    for line in lines:
        if not re.search(r'\bMagicMock\s*\(\s*\)', line):
            continue
        # Si la línea menciona un widget Qt o un objeto docx, es inevitable
        qt_keywords = ["Widget", "Dialog", "Button", "Label", "Table", "List",
                       "Edit", "View", "Window", "Layout", "Action", "Menu",
                       "QTime", "QDate", "QDialog", "QWidget", "page", "calc",
                       "mock_calc", "mock_page", "mock_settings"]
        docx_keywords = ["doc", "run", "paragraph", "table", "cell", "row",
                         "section", "style", "font", "DocumentFactory"]
        line_lower = line.lower()
        if has_qt and any(kw.lower() in line_lower for kw in qt_keywords):
            inevitable += 1
        elif has_docx and any(kw.lower() in line_lower for kw in docx_keywords):
            inevitable += 1

    return inevitable


def _calculate_ceiling(
    content: str,
    score: int,
    penalties: dict[str, int],
    file_path: Path | None = None,
) -> dict[str, Any]:
    """
    Calcula el techo real de score para un archivo de test.

    Separa penalizaciones inevitables (dependencias externas sin stubs)
    de penalizaciones corregibles (antipatrones reales).

    Retorna dict con: ceiling_score, ceiling_penalties, actionable_penalties,
    at_ceiling, ceiling_explanation.
    """
    has_qt = bool(_RE_QT_IMPORT.search(content))
    # Excepción docx acotada: solo test_docx_adapter.py trata directamente
    # con python-docx (el resto usa la interfaz IDocumentGenerator).
    has_docx = (
        file_path is not None
        and file_path.name == "test_docx_adapter.py"
        and bool(_RE_DOCX_IMPORT.search(content))
    )

    ceiling_penalties: dict[str, int] = {}
    actionable_penalties: dict[str, int] = {}

    for key, value in penalties.items():
        if key == "loose_mocks":
            inevitable_count = _count_inevitable_loose_mocks(content, has_qt, has_docx)
            inevitable_penalty = min(inevitable_count * 5, 30)
            corregible_penalty = value - (-inevitable_penalty)  # value es negativo
            # value = -(total_penalty), inevitable_penalty es positivo
            inevitable_part = -inevitable_penalty
            corregible_part = value - inevitable_part  # lo que queda
            if inevitable_part < 0:
                ceiling_penalties[key] = inevitable_part
            if corregible_part < 0:
                actionable_penalties[key] = corregible_part

        elif key == "patches_no_autospec":
            inevitable_patch_count = _count_inevitable_patches(content)
            inevitable_patch_penalty = min(inevitable_patch_count * 3, 20)
            inevitable_part = -inevitable_patch_penalty
            corregible_part = value - inevitable_part
            if inevitable_part < 0:
                ceiling_penalties[key] = inevitable_part
            if corregible_part < 0:
                actionable_penalties[key] = corregible_part
        else:
            # Resto de penalizaciones son siempre corregibles
            actionable_penalties[key] = value

    # Techo = score actual + suma de penalizaciones inevitables (que se "perdonan")
    inevitable_total = sum(abs(v) for v in ceiling_penalties.values())
    ceiling_score = min(100, score + inevitable_total)
    at_ceiling = len(actionable_penalties) == 0

    # Explicación legible para la consola
    explanation_parts = []
    if has_qt:
        explanation_parts.append(
            "importa PyQt6: el techo solo perdona MagicMock() sueltos en contexto de widgets Qt; "
            "repositorios y servicios del proyecto siguen siendo mejorable con create_autospec "
            "(ver .agents/skills/testing_fixtures_y_mocks/SKILL.md)"
        )
    if has_docx:
        explanation_parts.append("usa python-docx (objetos sin stubs de tipo)")
    if ceiling_penalties.get("patches_no_autospec"):
        explanation_parts.append("parchea builtins/Qt/OS (autospec no aplicable)")

    ceiling_explanation = "; ".join(explanation_parts) if explanation_parts else ""

    return {
        "ceiling_score": ceiling_score,
        "ceiling_penalties": ceiling_penalties,
        "actionable_penalties": actionable_penalties,
        "at_ceiling": at_ceiling,
        "ceiling_explanation": ceiling_explanation,
    }


def _count_patches(content: str) -> tuple[int, int]:
    """Devuelve (total_patches, patches_con_autospec)."""
    qt_tokens = (
        "QFileDialog",
        "QUrl",
        "QDesktopServices",
        "QColor",
        "QTextCharFormat",
        "QChart",
        "QChartView",
        "QPainter",
        "QBrush",
        "QBarSet",
        "QBarSeries",
        "QPieSeries",
        "QValueAxis",
        "QDateTimeAxis",
        "QLineSeries",
        "QMessageBox",
        "QProgressDialog",
        "QTimer",
        "builtins.",
        "PyQt6.",
        "QtWidgets.",
        "QtCore.",
        "ChangePasswordDialog",
        "QInputDialog",
        "timeline_widget",
        ".sys",
        ".os",
    )

    total = 0
    with_autospec = 0
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped.startswith("@patch"):
            continue
        # Si el patch fuerza un objeto con new/new_callable, autospec no aplica.
        if "new=" in stripped or "new_callable=" in stripped:
            continue
        # Excluir parches sobre Qt (no se permite autospec en Qt en Hipatia).
        if any(tok in stripped for tok in qt_tokens):
            continue
        total += 1
        if "autospec=True" in stripped:
            with_autospec += 1
    return total, with_autospec


def _count_loose_mocks_ast(content: str) -> int:
    """
    Cuenta llamadas reales a MagicMock()/Mock() sin args/kwargs.

    Importante: no contar ocurrencias en docstrings/comentarios (los regex dan falsos positivos).
    """
    try:
        tree = ast.parse(content)
    except SyntaxError:
        # Si el fichero no parsea, caer al heurístico regex (mejor que romper el analizador).
        return len(_RE_LOOSE_MOCK.findall(content))

    count = 0
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = None
        if isinstance(func, ast.Name):
            name = func.id
        elif isinstance(func, ast.Attribute):
            # e.g. mock.MagicMock() — contamos igual si el atributo se llama MagicMock/Mock
            name = func.attr
        if name not in ("MagicMock", "Mock"):
            continue
        if node.args or node.keywords:
            continue
        count += 1
    return count


def _count_tests_without_assert(content: str) -> int:
    """
    Cuenta tests que no tienen ningún assert significativo.

    Regla: `assert True` se considera **trivial** y no cuenta como verificación real.
    Un test se considera "sin assert" si NO contiene:
    - asserts no triviales (`assert x == ...`, `assert mock.call_count == ...`, etc.), o
    - verificaciones de interacción (`.assert_called_*`, `.call_count`, etc.)

    Solo se considera fin de test al ver "def test_..." o "async def test_..." al mismo
    indent o menor; así se evita truncar el cuerpo por líneas "def"/"class" dentro de
    strings multilínea (p. ej. código de ejemplo en el test).
    """
    lines = content.splitlines()
    tests_without_assert = 0
    in_test = False
    current_test_lines: list[str] = []
    test_indent = 0

    def _has_non_trivial_assert(block: str) -> bool:
        lines_wo_trivial = [
            ln for ln in block.splitlines()
            if not _RE_TRIVIAL_ASSERT_TRUE.match(ln)
        ]
        cleaned = "\n".join(lines_wo_trivial)
        return bool(_RE_ANY_ASSERT.search(cleaned))

    def _is_test_boundary(stripped: str) -> bool:
        """Solo siguiente test cuenta como límite; evita 'class'/def en strings."""
        return stripped.startswith("def test_") or stripped.startswith("async def test_")

    for line in lines:
        stripped = line.lstrip()
        indent = len(line) - len(stripped)

        if _is_test_boundary(stripped):
            if in_test and current_test_lines:
                block = "\n".join(current_test_lines)
                has_interaction_check = bool(_RE_ASSERT_CALLED.search(block))
                has_non_trivial_assert = _has_non_trivial_assert(block)
                if not (has_non_trivial_assert or has_interaction_check):
                    tests_without_assert += 1
            in_test = True
            current_test_lines = [line]
            test_indent = indent
        elif in_test:
            if stripped and not stripped.startswith("#") and indent <= test_indent and _is_test_boundary(stripped):
                block = "\n".join(current_test_lines)
                has_interaction_check = bool(_RE_ASSERT_CALLED.search(block))
                has_non_trivial_assert = _has_non_trivial_assert(block)
                if not (has_non_trivial_assert or has_interaction_check):
                    tests_without_assert += 1
                in_test = False
                current_test_lines = []
                in_test = True
                current_test_lines = [line]
                test_indent = indent
            else:
                current_test_lines.append(line)

    if in_test and current_test_lines:
        block = "\n".join(current_test_lines)
        has_interaction_check = bool(_RE_ASSERT_CALLED.search(block))
        has_non_trivial_assert = _has_non_trivial_assert(block)
        if not (has_non_trivial_assert or has_interaction_check):
            tests_without_assert += 1

    return tests_without_assert


def _is_controller_or_service_file(file_path: Path) -> bool:
    """Detecta si el archivo testea controladores o servicios."""
    name = file_path.name.lower()
    return bool(_CONTROLLER_SERVICE_PATTERN.search(name))


def analyze_test_file(file_path: Path) -> dict[str, Any]:
    """Analiza un archivo de test para verificar cumplimiento real de estándares."""
    content = file_path.read_text(encoding='utf-8')

    # --- Marcadores ---
    markers = {
        "unit": "@pytest.mark.unit" in content or "pytestmark = pytest.mark.unit" in content,
        "integration": "@pytest.mark.integration" in content or "pytestmark = pytest.mark.integration" in content,
        "e2e": "@pytest.mark.e2e" in content or "pytestmark = pytest.mark.e2e" in content,
        "setup": "@pytest.mark.setup" in content or "pytestmark = pytest.mark.setup" in content,
    }

    # --- Conteos reales ---
    strict_mock_count = len(_RE_STRICT_MOCK.findall(content))
    loose_mock_count = _count_loose_mocks_ast(content)
    total_patches, patches_with_autospec = _count_patches(content)
    patches_without_autospec = max(0, total_patches - patches_with_autospec)
    assert_called_count = len(_RE_ASSERT_CALLED.findall(content))
    assert_called_with_args_count = len(_RE_ASSERT_CALLED_WITH_ARGS.findall(content))
    assert_called_no_args_count = len(_RE_ASSERT_CALLED_NO_ARGS.findall(content))
    isinstance_dto_count = len(_RE_ISINSTANCE_DTO.findall(content))
    has_docstrings = bool(_RE_DOCSTRING.search(content))
    test_count = len(re.findall(r"^\s*def\s+test_", content, re.MULTILINE))
    tests_without_assert = _count_tests_without_assert(content)
    has_mock_session = bool(_RE_MOCK_SESSION.search(content))
    spec_object_count = len(_RE_SPEC_OBJECT.findall(content))
    trivial_assert_true_count = len(_RE_TRIVIAL_ASSERT_TRUE.findall(content))
    trivial_assert_true_justified_count = len(_RE_TRIVIAL_ASSERT_TRUE_JUSTIFIED.findall(content))
    is_ctrl_or_service = _is_controller_or_service_file(file_path)
    missing_interaction_check = is_ctrl_or_service and assert_called_count == 0 and test_count > 0

    is_infra = file_path.name in [
        "conftest.py", "macos_fix.py", "audit_report_generator.py", "test_qapp_crash.py",
        "__init__.py"
    ]

    # -----------------------------------------------------------------------
    # SCORING
    # -----------------------------------------------------------------------
    score = 0
    breakdown: dict[str, int] = {}

    if any(markers.values()):
        score += 25
        breakdown["markers"] = 25

    if is_infra:
        score += 65
        breakdown["infra_bonus"] = 65
    else:
        if strict_mock_count > 0:
            score += 20
            breakdown["strict_mocks"] = 20

        if assert_called_count > 0:
            score += 15
            breakdown["interaction_checks"] = 15

        if isinstance_dto_count > 0:
            score += 15
            breakdown["isinstance_dto"] = 15

        if total_patches == 0 or patches_without_autospec == 0:
            score += 15
            breakdown["patches_autospec"] = 15
        elif patches_with_autospec > 0:
            partial = int(15 * patches_with_autospec / total_patches)
            score += partial
            breakdown["patches_autospec_partial"] = partial

    if has_docstrings:
        score += 10
        breakdown["docstrings"] = 10

    # -----------------------------------------------------------------------
    # PENALIZACIONES
    # -----------------------------------------------------------------------
    penalties: dict[str, int] = {}

    if not is_infra:
        if loose_mock_count > 0:
            penalty = min(loose_mock_count * 5, 30)
            score -= penalty
            penalties["loose_mocks"] = -penalty

        if patches_without_autospec > 0:
            penalty = min(patches_without_autospec * 3, 20)
            score -= penalty
            penalties["patches_no_autospec"] = -penalty

        if tests_without_assert > 0:
            penalty = min(tests_without_assert * 5, 20)
            score -= penalty
            penalties["tests_without_assert"] = -penalty

        if missing_interaction_check:
            score -= 10
            penalties["missing_interaction_check"] = -10

        if assert_called_no_args_count > 0:
            penalty = min(assert_called_no_args_count * 3, 15)
            score -= penalty
            penalties["assert_called_no_args"] = -penalty

        if has_mock_session:
            score -= 8
            penalties["mock_session"] = -8

        if spec_object_count > 0:
            penalty = min(spec_object_count * 5, 15)
            score -= penalty
            penalties["spec_object"] = -penalty

        # `assert True` sin justificar incentiva tests débiles. Penalización suave
        # para empujar hacia asserts observables (estado/retorno/interacción).
        unjustified_trivial = max(0, trivial_assert_true_count - trivial_assert_true_justified_count)
        if unjustified_trivial > 0:
            penalty = min(unjustified_trivial * 1, 10)
            score -= penalty
            penalties["trivial_assert_true"] = -penalty

    score = max(0, min(100, score))

    # -----------------------------------------------------------------------
    # TECHO REAL
    # -----------------------------------------------------------------------
    ceiling_data = _calculate_ceiling(content, score, penalties, file_path)

    # Estado basado en ceiling_score para no penalizar lo ya optimizado.
    # Regla adicional (techo real): si el archivo está en su techo y no tiene penalizaciones
    # corregibles, se considera "Actualizado" aunque su techo sea < 80 (p.ej. PyQt6/docx).
    effective_score = ceiling_data["ceiling_score"]
    status_detail = ""
    if ceiling_data.get("at_ceiling") and not ceiling_data.get("actionable_penalties"):
        status = "Actualizado"
        status_detail = "Techo real alcanzado (sin penalizaciones corregibles)."
    elif effective_score >= 80:
        status = "Actualizado"
    elif effective_score >= 50:
        status = "En Progreso"
    else:
        status = "Legacy / Pendiente"

    return {
        "name": file_path.name,
        "path": str(file_path),
        "is_infra": is_infra,
        "markers": markers,
        "metrics": {
            "strict_mock_count": strict_mock_count,
            "loose_mock_count": loose_mock_count,
            "total_patches": total_patches,
            "patches_with_autospec": patches_with_autospec,
            "patches_without_autospec": patches_without_autospec,
            "assert_called_count": assert_called_count,
            "assert_called_with_args_count": assert_called_with_args_count,
            "assert_called_no_args_count": assert_called_no_args_count,
            "isinstance_dto_count": isinstance_dto_count,
            "has_docstrings": has_docstrings,
            "test_count": test_count,
            "tests_without_assert": tests_without_assert,
            "has_mock_session": has_mock_session,
            "spec_object_count": spec_object_count,
            "trivial_assert_true_count": trivial_assert_true_count,
            "trivial_assert_true_justified_count": trivial_assert_true_justified_count,
            "is_ctrl_or_service": is_ctrl_or_service,
            "missing_interaction_check": missing_interaction_check,
        },
        "score_breakdown": breakdown,
        "penalties": penalties,
        "score": score,
        "ceiling_score": ceiling_data["ceiling_score"],
        "ceiling_penalties": ceiling_data["ceiling_penalties"],
        "actionable_penalties": ceiling_data["actionable_penalties"],
        "status_detail": status_detail,
        "at_ceiling": ceiling_data["at_ceiling"],
        "ceiling_explanation": ceiling_data["ceiling_explanation"],
        "status": status,
    }


def run_analysis(tests_dir: str) -> list[dict[str, Any]]:
    """Ejecuta el análisis en toda la carpeta de tests."""
    results = []
    tests_path = Path(tests_dir)

    for py_file in tests_path.rglob("*.py"):
        if _RE_FINDER_DUP_CONFTEST.match(py_file.name):
            continue

        is_test = py_file.name.startswith("test_")
        is_infra = py_file.name in [
            "conftest.py", "macos_fix.py", "audit_report_generator.py", "test_qapp_crash.py",
            "__init__.py"
        ]

        if not (is_test or is_infra):
            continue

        if py_file.name.startswith("test_") and _RE_FINDER_DUP_TEST.search(py_file.name):
            continue

        if "__pycache__" in str(py_file) or "/." in str(py_file):
            continue

        results.append(analyze_test_file(py_file))

    return results


if __name__ == "__main__":
    tests_root = os.path.join(os.getcwd(), "tests")
    report_data = run_analysis(tests_root)

    output_path = os.path.join(os.getcwd(), "test_reports", "compliance_data.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=4)

    total = len(report_data)
    updated = sum(1 for r in report_data if r["status"] == "Actualizado")
    in_progress = sum(1 for r in report_data if r["status"] == "En Progreso")
    legacy = sum(1 for r in report_data if r["status"] == "Legacy / Pendiente")
    avg_score = sum(r["score"] for r in report_data) / total if total else 0
    avg_ceiling = sum(r["ceiling_score"] for r in report_data) / total if total else 0
    at_ceiling_count = sum(1 for r in report_data if r["at_ceiling"])

    print(f"\n{'='*60}")
    print(f"  ANÁLISIS DE CALIDAD DE TESTS — HIPATIA")
    print(f"{'='*60}")
    print(f"  Archivos analizados : {total}")
    print(f"  Actualizados        : {updated}")
    print(f"  En Progreso         : {in_progress}")
    print(f"  Legacy / Pendiente  : {legacy}")
    print(f"{'='*60}")
    print(f"  Score absoluto medio  : {avg_score:.1f}/100")
    print(f"  Score optimizado medio: {avg_ceiling:.1f}/100")
    print(f"  Archivos en su techo  : {at_ceiling_count}/{total}")
    print(f"{'='*60}\n")

    # Detalle por archivo — mostrar explicación cuando está en techo
    at_ceiling_files = [r for r in report_data if r["at_ceiling"] and not r["is_infra"]]
    if at_ceiling_files:
        print("  ✅ ARCHIVOS EN SU TECHO REAL (score optimizado = techo):")
        print(f"  {'Archivo':<55} {'Abs':>5}  {'Techo':>6}  Razón")
        print(f"  {'-'*55}  {'-'*5}  {'-'*6}  {'-'*30}")
        for r in sorted(at_ceiling_files, key=lambda x: x["ceiling_score"], reverse=True):
            explanation = r["ceiling_explanation"] or "sin dependencias externas"
            print(f"  {r['name']:<55} {r['score']:>5}  {r['ceiling_score']:>6}  {explanation}")
        print()

    # Archivos con penalizaciones corregibles
    actionable_files = [
        r for r in report_data
        if r["actionable_penalties"] and not r["is_infra"]
    ]
    if actionable_files:
        print("  ⚠️  ARCHIVOS CON PENALIZACIONES CORREGIBLES:")
        print(f"  {'Archivo':<55} {'Score':>5}  Penalizaciones")
        print(f"  {'-'*55}  {'-'*5}  {'-'*30}")
        for r in sorted(actionable_files, key=lambda x: x["score"]):
            pen_str = ", ".join(
                f"{k}({v})" for k, v in r["actionable_penalties"].items()
            )
            print(f"  {r['name']:<55} {r['score']:>5}  {pen_str}")
        print()

    print(f"  Datos guardados en: {output_path}\n")
