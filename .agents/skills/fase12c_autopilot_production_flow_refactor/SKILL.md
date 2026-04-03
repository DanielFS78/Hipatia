---
name: Fase 12C Autopilot — DTO en production_flow
description: Autopilot que refactoriza de forma conservadora la frontera UI/DTO en archivos de `ui/**/production_flow/**` (y widgets afectados) hasta dejar `total_findings == 0` en `ui_dto_boundary_analyzer.py --include-production-flow`.
---

# [ARCHIVO — no usar como backlog activo] Fase 12C Autopilot — DTO en production_flow

## Fuentes

1. Candidatos priorizados:
   - `Documentacion/Refactorizacion_Completa/Fase_12C/ui_dto_boundary_refactor_candidates.md`
2. Analizador:
   - `scripts/ui_dto_boundary_analyzer.py --include-production-flow`
3. Datos del analizador:
   - `Documentacion/Refactorizacion_Completa/Fase_12C/ui_dto_boundary_report.json`

## Objetivo de cierre

- `ui_dto_boundary_report.json.summary.total_findings == 0`
- `python3 run_tests.py` pasa (0 fallos)
- MyPy no debe introducir nuevos errores

## Reglas de seguridad (conservadoras)

1. Un archivo por iteración.
2. No “arreglar” el analizador con trucos tipo `getattr(x, "k")`: el contrato debe ser DTO/atributos.
3. Preferir mover la conversión dict->DTO fuera de `ui/` cuando sea posible (en `core/` o `controllers/`) y que `ui/` consuma DTO por atributos.
4. Mantener fixtures/mocks; si hay tests débiles, crearlos/fortalecerlos.
5. `pytest`: nunca pasar el siguiente archivo si hay fallo, warning o skipped.

## Bucle autónomo (determinista)

Repetir hasta que no queden candidatos con hallazgos:

1. Ejecutar:
   - `python3 scripts/ui_dto_boundary_analyzer.py --include-production-flow`
2. Leer:
   - `Documentacion/Refactorizacion_Completa/Fase_12C/ui_dto_boundary_report.json`
3. Selección del siguiente archivo:
   - Tomar el primer archivo de `ui_dto_boundary_refactor_candidates.md` cuyo conteo en el reporte sea > 0.
4. Refactorización del archivo seleccionado:
   - Identificar cada acceso `obj["campo"]` / `obj.get("campo")`
   - Convertir el origen a DTO y en `ui/` reemplazar por `dto.campo`
   - Si el DTO no existe, crear DTO mínimo en `core/dtos.py` (o módulo core adecuado) y ajustar presenter/servicio/controller para producirlo.
5. Tests:
   - Ejecutar `python3 -m pytest <tests_relacionados> -x -q`
   - Si no hay tests para el scope, crearlos siguiendo:
     - `.agents/skills/testing_pyqt6_headless/SKILL.md`
     - `.agents/skills/testing_fixtures_y_mocks/SKILL.md`
6. Validación global:
   - `python3 run_tests.py`
7. Documentación:
   - Regenerar `ui_dto_boundary_report.md/json`
   - Añadir nota de completado en `Documentacion/Refactorizacion_Completa/Fase_12C/`
8. Repetir con el siguiente.

## Fin

Cuando `total_findings == 0`, generar un informe final:
- `Documentacion/Refactorizacion_Completa/Fase_12C/informe_fase12c_production_flow_cierre.md`

