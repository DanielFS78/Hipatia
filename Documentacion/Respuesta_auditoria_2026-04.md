# Seguimiento auditoría técnica (2026-04)

Resumen de cambios alineados con el plan de seguimiento (DTO/RBAC/RegistroTemporal/mypy/AppModel/doc).

## Frontera UI / DTO (Fase 12C)

- `PrepStepsWidget` usa `_ui_record_field` para listas y detalle (dict o DTO).
- Informe del analizador: salida bajo `Documentacion/Refactorizacion_Completa/Fase_12C/` (`ui_dto_boundary_report.json` / `.md` tras ejecutar `scripts/ui_dto_boundary_analyzer.py`).
- **CI:** paso informativo `python scripts/ui_dto_boundary_analyzer.py` con `continue-on-error: true` (`.github/workflows/ci.yml`).

## RBAC en profundidad

- `BackupController`: `MANAGE_SETTINGS` en import/export/sync y diálogo de restore.
- `HistorialReportManager.on_print_report_clicked`: `GENERATE_REPORTS`.
- Tests: `tests/unit/test_backup_controller.py`, `tests/unit/test_historial_report_manager_security.py`.

## RegistroTemporal / motor

- WAL en archivos temporales; `cleanup()` elimina `.db`, `-wal` y `-shm`.
- Motor: se elimina el uso de `_flush_buffer_to_disk` privado; el vaciado previo a lectura queda en `consultar_eventos`.
- Test: `tests/unit/test_temporal_storage.py`.

## Mypy (scripts)

- `mypy.ini`: bloque `[mypy-scripts.init_database]`; CI incluye `scripts/init_database.py` en la corrida de mypy.

## AppModel

- **Oleada reportes (2026-04):** eliminados en `AppModel` los delegadores puros hacia `ReportService`; la UI consume `ReportService` vía DI o `model.report_service`. Permanecen orquestación (`get_dashboard_stats`, `get_problematic_components_stats` vía servicio) y el resto de delegadores con consumidores activos.
- Política y próximas podas (solo con `rg` = 0): `.agents/skills/reduccion_god_objects/SKILL.md`, inventario `Documentacion/Refactorizacion_Completa/AppModel_migracion_inventario_2026.md`, y `scripts/generate_daniel_doc.py` (*Política AppModel y nuevas features*).

## Documentación generada

Tras regenerar: `python scripts/generate_daniel_doc.py` → `Documentacion/Documentacion Daniel.md`.
