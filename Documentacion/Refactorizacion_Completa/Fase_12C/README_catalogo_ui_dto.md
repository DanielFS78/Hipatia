# Catálogo de hallazgos UI/DTO (Fase 12C)

## Estado del catálogo

**Cierre 2026-03-20:** el catálogo estricto (todos los `.py` bajo `ui/`, incluido `production_flow`) quedó en **0 hallazgos**. Para comprobarlo en cualquier momento:

```bash
python3 scripts/ui_dto_findings_catalog.py
```

Los lotes y la verificación con `run_tests.py` están en `.agents/skills/fase12c_sanear_frontera_ui/SKILL.md`.

## Propósito

Inventariar todos los accesos tipo diccionario detectados en `ui/` (`obj["clave"]`, `obj.get("clave")`) que la Fase 12C puede convertir a contrato con **DTOs por atributos**, junto con **conexiones** entre hallazgos (mismo receptor AST y archivo).

## Scripts

| Script | Función |
|--------|---------|
| `scripts/ui_dto_findings_catalog.py` | Genera catálogo JSON/MD + checklist con grupos y `related_ids`. |
| `scripts/ui_dto_boundary_analyzer.py` | Informe estándar (`ui_dto_boundary_report.json`) para métricas globales. |

Comandos típicos:

```bash
python3 scripts/ui_dto_findings_catalog.py
python3 scripts/ui_dto_findings_catalog.py --no-production-flow
python3 scripts/ui_dto_boundary_analyzer.py
```

## Salidas

- `ui_dto_findings_catalog.json` — lista maestra con `id` (F0001…), `receiver`, `group_id`, `related_ids`, `imports_sample`, `status`.
- `ui_dto_findings_catalog.md` — muestra legible.
- `ui_dto_findings_checklist.md` — tabla con casillas `[x]` para marcar cierre por hallazgo.

Al regenerar el JSON, los ítems con `status: "hecho"` se conservan por **`signature`** (`file|kind|key|receiver`), aunque cambien línea o numeración `F0001`.

## Documentación técnica global

Tras cambios en módulos `.py`, ejecutar:

```bash
python3 scripts/generate_daniel_doc.py
```

Ver `.agents/skills/estandar_documentacion/SKILL.md`.

## Progreso documentado (lotes)

Los lotes cerrados se anotan en `.agents/skills/fase12c_sanear_frontera_ui/SKILL.md` (sección **Progreso**).
