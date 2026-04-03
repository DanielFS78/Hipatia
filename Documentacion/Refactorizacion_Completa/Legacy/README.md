# Fase 4 — Código Legacy

Esta carpeta contiene los informes generados por el analizador de código legacy (Fase 4 del Plan de Mejora de Calidad).

## Generación

```bash
python3 scripts/legacy_analyzer.py
```

## Archivos

- **legacy_report.json** — Datos estructurados para el agente (ítems por categoría).
- **legacy_report.md** — Informe legible en Markdown.

## Skills relacionadas

- `.agents/skills/fase_legacy/SKILL.md` — Definición de legacy y checklist.
- `.agents/skills/plan_mejora_calidad/SKILL.md` — Hub del plan de calidad (fases cerradas; vigilancia y tests).

## Categorías detectadas

| Categoría | Descripción |
|-----------|-------------|
| print_en_produccion | `print()` en controllers, core, database, features, ui |
| bare_except | `except:` sin tipo |
| deprecated_markers | Comentarios con @deprecated, TODO: Remove |
| docstring_legacy | Docstrings con obsoleto/legacy/deprecated |
| simple_delegation | Funciones que solo delegan en otra (posibles shims) |
| legacy_comment | Comentarios tipo "Métodos Legacy / Re-Exports" |
