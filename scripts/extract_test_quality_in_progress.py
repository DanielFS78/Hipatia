"""
Nombre del Módulo: extract_test_quality_in_progress
Descripción: Genera un backlog detallado de archivos de test en estado "En Progreso"
             según `test_reports/compliance_data.json`, incluyendo penalizaciones
             corregibles y recomendaciones conservadoras para elevar el score.

Uso:
    python3 scripts/extract_test_quality_in_progress.py

Salidas:
    - Documentacion/Mejora_Calidad/backlog_tests_en_progreso.md
    - .agents/skills/backlog_tests_en_progreso/SKILL.md
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


_ROOT = Path(__file__).resolve().parent.parent
_COMPLIANCE_JSON = _ROOT / "test_reports" / "compliance_data.json"
_DOC_OUT = _ROOT / "Documentacion" / "Mejora_Calidad" / "backlog_tests_en_progreso.md"
_SKILL_OUT = _ROOT / ".agents" / "skills" / "backlog_tests_en_progreso" / "SKILL.md"


@dataclass(frozen=True)
class BacklogItem:
    name: str
    path: str
    score: int
    ceiling_score: int
    actionable_penalties: dict[str, int]
    metrics: dict[str, Any]
    ceiling_explanation: str


def _recommendations(item: BacklogItem) -> list[str]:
    """
    Devuelve recomendaciones conservadoras basadas en penalizaciones.

    Nota: No intenta "forzar 100/100" si el techo real está limitado por Qt/docx/builtins.
    """
    recs: list[str] = []
    ap = item.actionable_penalties
    m = item.metrics

    if ap.get("tests_without_assert"):
        recs.append(
            f"Eliminar tests sin assert (detectados: {m.get('tests_without_assert', 0)}). "
            "Priorizar asserts observables: retorno/estado/interacción; evitar `assert True` salvo humo justificado."
        )
    if ap.get("loose_mocks"):
        recs.append(
            f"Reemplazar `MagicMock()`/`Mock()` sueltos (detectados: {m.get('loose_mock_count', 0)}) por "
            "`create_autospec(..., instance=True)` o `MagicMock(spec=[...])` cuando sean clases del proyecto."
        )
    if ap.get("patches_no_autospec"):
        recs.append(
            f"Añadir `autospec=True` en patches corregibles (detectados: {m.get('patches_without_autospec', 0)}), "
            "excepto whitelist (Qt/builtins/OS) donde no aplica."
        )
    if ap.get("assert_called_no_args"):
        recs.append(
            f"Evitar `assert_called_once()` sin args (detectados: {m.get('assert_called_no_args_count', 0)}). "
            "Usar `assert x.call_count == 1` + `assert_called_once_with(...)` cuando los args sean conocidos."
        )
    if ap.get("missing_interaction_check"):
        recs.append(
            "Archivo de ctrl/servicio sin verificación de interacción: añadir al menos un `assert_called_*` "
            "contra el colaborador correcto."
        )
    if ap.get("mock_session"):
        recs.append(
            "Evitar mock de sesión SQLAlchemy en repositorios: usar fixtures reales en memoria (`session`/`repos`)."
        )
    if ap.get("spec_object"):
        recs.append(
            "Evitar `spec=object` (no aporta). Sustituir por `create_autospec(ClaseReal, instance=True)` "
            "o `MagicMock(spec=[...])` mínimo."
        )

    if not recs:
        recs.append("Sin penalizaciones corregibles detectadas por el analizador (posible techo real).")

    return recs


def _load_items() -> list[BacklogItem]:
    data = json.loads(_COMPLIANCE_JSON.read_text(encoding="utf-8"))
    items: list[BacklogItem] = []
    for entry in data:
        if entry.get("status") != "En Progreso":
            continue
        items.append(
            BacklogItem(
                name=str(entry.get("name", "")),
                path=str(entry.get("path", "")),
                score=int(entry.get("score", 0)),
                ceiling_score=int(entry.get("ceiling_score", 0)),
                actionable_penalties=dict(entry.get("actionable_penalties", {}) or {}),
                metrics=dict(entry.get("metrics", {}) or {}),
                ceiling_explanation=str(entry.get("ceiling_explanation", "") or ""),
            )
        )
    # Orden conservador: más cerca de “Actualizado” primero (menos riesgo), luego por penalización corregible total.
    def _sort_key(it: BacklogItem) -> tuple[int, int, str]:
        penalty_sum = sum(abs(int(v)) for v in it.actionable_penalties.values())
        return (-(it.score), -penalty_sum, it.path)

    return sorted(items, key=_sort_key)


def _write_markdown(items: list[BacklogItem]) -> None:
    _DOC_OUT.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = []
    lines.append("# Backlog — Tests en Progreso (dashboard)\n")
    lines.append("Este backlog se genera automáticamente desde `test_reports/compliance_data.json`.\n")
    lines.append("Objetivo: mover todos estos archivos a **Actualizado** (score ≥ 80) o justificar **techo real**.\n")
    lines.append("\n## Cómo regenerar\n")
    lines.append("```bash\npython3 scripts/extract_test_quality_in_progress.py\n```\n")
    lines.append("\n## Listado (En Progreso)\n")
    lines.append(f"Total: **{len(items)}**\n")
    lines.append("| # | Archivo | Score | Techo | Penalizaciones corregibles | Acción recomendada |")
    lines.append("|---:|---|---:|---:|---|---|")

    for idx, it in enumerate(items, start=1):
        ap = ", ".join(f"{k}({v})" for k, v in sorted(it.actionable_penalties.items())) or "—"
        rec = _recommendations(it)[0]
        lines.append(
            f"| {idx} | `{Path(it.path).as_posix()}` | {it.score} | {it.ceiling_score} | {ap} | {rec} |"
        )

    lines.append("\n---\n")
    lines.append("## Detalle por archivo (checklist)\n")
    for idx, it in enumerate(items, start=1):
        lines.append(f"### {idx}. `{Path(it.path).as_posix()}`\n")
        lines.append(f"- **Score actual**: {it.score} | **Techo**: {it.ceiling_score}")
        ap_str = ", ".join(
            f"{k}({v})" for k, v in sorted(it.actionable_penalties.items())
        ) or "—"
        lines.append(f"- **Penalizaciones corregibles**: {ap_str}")
        if it.ceiling_explanation:
            lines.append(f"- **Techo real (explicación)**: {it.ceiling_explanation}")
        lines.append("- **Pasos sugeridos (conservadores)**:")
        for rec in _recommendations(it):
            lines.append(f"  - {rec}")
        lines.append("- **Verificación obligatoria**:")
        lines.append(f"  - `python3 -m mypy {Path(it.path).as_posix()} --config-file mypy.ini --show-error-codes`")
        lines.append(f"  - `python3 -m pytest {Path(it.path).as_posix()} -q`")
        lines.append("  - `python3 -m pytest -q`")
        lines.append("")

    _DOC_OUT.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def _write_skill(items: list[BacklogItem]) -> None:
    _SKILL_OUT.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = []
    lines.append("---")
    lines.append("name: Backlog — Tests En Progreso (Dashboard)")
    lines.append("description: Listado vivo de archivos en estado 'En Progreso' según el analizador. Incluye penalizaciones corregibles y el orden de trabajo recomendado. Regenerar con scripts/extract_test_quality_in_progress.py.")
    lines.append("---\n")
    lines.append("# Backlog — Tests En Progreso (Dashboard)\n")
    lines.append("Fuente: `test_reports/compliance_data.json`.\n")
    lines.append("Regenerar:\n")
    lines.append("```bash\npython3 scripts/extract_test_quality_in_progress.py\n```\n")
    lines.append(f"Total actual: **{len(items)}**\n")
    lines.append("## Listado vivo (marcar ✅ al completar)\n")
    lines.append("| # | Archivo | Estado | Score | Techo | Penalizaciones |")
    lines.append("|---:|---|:---:|---:|---:|---|")

    for idx, it in enumerate(items, start=1):
        ap = ", ".join(f"{k}({v})" for k, v in sorted(it.actionable_penalties.items())) or "—"
        lines.append(
            f"| {idx} | `{Path(it.path).as_posix()}` | — | {it.score} | {it.ceiling_score} | {ap} |"
        )

    lines.append("\n## Criterio de ✅ (obligatorio)\n")
    lines.append("- `python3 -m mypy <archivo> ...` pasa")
    lines.append("- `pytest <archivo> -q` pasa")
    lines.append("- `pytest -q` pasa")
    lines.append("- `python3 scripts/test_quality_analyzer.py` ya no lista ese archivo como 'En Progreso' (o queda en techo real con explicación)\n")

    _SKILL_OUT.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    if not _COMPLIANCE_JSON.exists():
        raise SystemExit(f"No existe {_COMPLIANCE_JSON}. Ejecuta antes: python3 scripts/test_quality_analyzer.py")

    items = _load_items()
    _write_markdown(items)
    _write_skill(items)
    print(f"✅ Backlog generado: {_DOC_OUT}")
    print(f"✅ Skill generada:  {_SKILL_OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

