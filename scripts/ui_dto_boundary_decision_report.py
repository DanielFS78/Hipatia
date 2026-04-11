#!/usr/bin/env python3
"""
Nombre del Módulo: scripts.ui_dto_boundary_decision_report

Descripción: Funciones y datos de apoyo del paquete; conviene enlazar qué controlador o servicio las consume y qué estructuras devuelven (ver firmas al inicio del archivo). Integración típica con: ``json``, ``pathlib``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


BASE_DIR = Path(__file__).resolve().parent.parent
F12_DIR = BASE_DIR / "Documentacion" / "Refactorizacion_Completa" / "Fase_12C"
IN_JSON = F12_DIR / "ui_dto_boundary_report.json"
OUT_MD = F12_DIR / "ui_dto_boundary_decision_report.md"


@dataclass(frozen=True)
class Decision:
    deserves_change: bool
    decision_label: str
    reason: str
    risk: str


def _decide(file_rel: str) -> Decision:
    # Dict deliberado dentro del flujo de producción:
    # - en Fase 12C se excluye explícitamente de auditoría "por frontera"
    # - se trata como estado/config serializable de la UI (boilerplate alto si convertimos todo a DTO)
    if "/production_flow/" in f"/{file_rel}/":
        return Decision(
            deserves_change=False,
            decision_label="NO (dict deliberado UI/serializable)",
            reason="El analizador clasifica `production_flow` como dict interno deliberado de UI (payload/config del canvas/flujo).",
            risk="Convertirlo a DTO puede introducir fricción alta (muchos archivos) y riesgo de romper serialización/compat.",
        )

    return Decision(
        deserves_change=True,
        decision_label="POSIBLE CAMBIO (frontera UI/DTO)",
        reason="Fuera de `production_flow`/widgets excluidos: presumiblemente hay frontera UI→DTO donde convendría usar atributos DTO en vez de dict.",
        risk="Requiere confirmar el origen del dict (presenter/service) y adaptar DTO; evita parches que oculten el contrato.",
    )


def _escape_md(s: str) -> str:
    return s.replace("\n", " ").replace("|", "\\|")


def main() -> int:
    if not IN_JSON.exists():
        raise SystemExit(f"No existe {IN_JSON}. Ejecuta primero ui_dto_boundary_analyzer.py --include-production-flow")

    report = json.loads(IN_JSON.read_text(encoding="utf-8"))
    items: list[dict[str, Any]] = report.get("items", [])

    counts = {"change_yes": 0, "change_no": 0}

    lines: list[str] = []
    lines.append("# Fase 12C — Informe de Decisión (por hallazgo)")
    lines.append("")
    lines.append("> Fuente: `ui_dto_boundary_report.json` (modo `--include-production-flow`).")
    lines.append("> Nota: criterios conservadores alineados con el propio diseño de la Fase 12C.")
    lines.append("")

    summary = report.get("summary", {})
    lines.append("## Resumen")
    lines.append("")
    lines.append(f"- Total hallazgos: **{summary.get('total_findings', len(items))}**")
    lines.append(f"- Archivos afectados: **{summary.get('files_affected', '—')}**")
    lines.append("")
    lines.append("## Decisiones")
    lines.append("")
    lines.append("| # | Archivo | Línea | Tipo | Key | Decisión | Motivo (breve) | Riesgo/Notas |")
    lines.append("|---:|---|---:|---|---|---|---|---|")

    for idx, it in enumerate(items, start=1):
        file_rel = str(it.get("file", ""))
        d = _decide(file_rel)
        if d.deserves_change:
            counts["change_yes"] += 1
        else:
            counts["change_no"] += 1

        ctx = str(it.get("context", ""))
        context_one_liner = _escape_md(ctx)[:160]
        reason_short = _escape_md(d.reason)[:160]
        risk_short = _escape_md(d.risk)[:160]

        # Insertar además contexto recortado para trazabilidad
        lines.append(
            f"| {idx} | `{file_rel}` | {int(it.get('line', 0))} | {it.get('kind')} | `{it.get('key')}` | {d.decision_label} | "
            f"{reason_short} | {risk_short} |"
        )

    lines.append("")
    lines.append("## Totales")
    lines.append("")
    lines.append(f"- Recomendado cambiar: **{counts['change_yes']}**")
    lines.append(f"- No recomendado cambiar: **{counts['change_no']}**")
    lines.append("")

    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(f"✅ Informe generado: {OUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

