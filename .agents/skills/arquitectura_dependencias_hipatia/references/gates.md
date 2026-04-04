# Gates por ítem (arquitectura / dependencias)

Checklist copiable al cerrar un ítem de **Fase 4** (remedio acotado).

## Obligatorios

- [ ] **Pytest focal** del árbol tocado (`python3 -m pytest <ruta> -q --tb=short`); ampliar si el cambio cruza capas.
- [ ] **Mypy** sobre paths de producto tocados o corrida CI-equivalente si el cambio es transversal:
  `python3 -m mypy app.py core controllers database features ui tests`
- [ ] **REGISTRO:** entrada en `Documentacion/Refactorizacion_Completa/Auditoria_Secuencial/REGISTRO_EJECUCION_ITEMS.md` (usar plantilla `plantilla_item_registro.md`).
- [ ] **Progreso:** actualizar `Documentacion/Refactorizacion_Completa/Arquitectura_Dependencias/PROGRESO_OPTIMIZACION_CAPAS.md` (estado de fase Opt, `ultima_actualizacion`, `proxima_accion_sugerida`, historial o sub-ítems si aplica).

## Si el ítem toca `ui/` (widgets o diálogos)

- [ ] `python3 scripts/ui_dto_boundary_analyzer.py` → **0 hallazgos** (o justificar excepción documentada en REGISTRO).

## Hitos mayores (varios módulos o contrato público)

- [ ] `python3 scripts/generate_daniel_doc.py`
- [ ] `python3 scripts/check_documentation_omissions.py` → **omitidos=0**

## Worktree ≠ iCloud

- [ ] `python3 scripts/sync_worktree_to_icloud.py` (o `cp` según `ejecucion_secuencial_calidad/references/sync_icloud_continuo.md`).

## Post-remedio (opcional pero recomendado)

- [ ] Regenerar informe: `python3 scripts/architecture_layer_edges.py`
- [ ] Actualizar sección “Última regeneración” o tabla de backlog en `ANALISIS_CAPAS.md` si cambia el diagnóstico.
