# Índice de Agent Skills — Hipatia

Actualizado: 2026-04. Se retiraron **autopilots** y el hub histórico **refactorizacion_mcp** (fases cerradas). Lo que queda es **metodología operativa** y **referencia puntual** para mantenimiento.

## Metodología y calidad (activas)

| Skill | Uso |
|-------|-----|
| `plan_mejora_calidad` | Hub del plan de calidad; leer primero en sesiones de mejora |
| `ejecucion_secuencial_calidad` | Auditoría por ítems, gates, REGISTRO |
| `strict_testing` | Dashboard / mocks estrictos |
| `testing_antipatrones` | Falsos positivos |
| `testing_fixtures_y_mocks` | Fixtures, autospec, DummyModel |
| `testing_por_capa` | Qué testear por capa |
| `testing_pyqt6_headless` | Qt headless / macOS |
| `orden_trabajo_tests` | Orden de archivos de test |
| `backlog_tests` | Backlog por impacto |
| `backlog_tests_en_progreso` | Tests en progreso |
| `estandar_documentacion` | Docstrings y docs técnicas |
| `plan_produccion_coordinador` | Prioridades hacia Windows |
| `preparacion_windows` | DPI, Qt, PyInstaller |
| `ui_pyqt_layout_freezes` | Congelaciones UI PyQt6 |
| `limpieza_proyecto` | Artefactos antes de empaquetar |
| `reduccion_god_objects` | Reducir fachada AppModel |
| `references/sync_icloud_continuo.md` | Sync worktree → iCloud; `scripts/sync_worktree_to_icloud.py` |

## Referencia (fases cerradas; mantenimiento / criterios)

| Skill | Uso |
|-------|-----|
| `fase12c_sanear_frontera_ui` | Frontera UI/DTO cerrada; analizadores y catálogo |
| `fase_legacy` | Criterios legacy y checklist |
| `migracion_mixins_composicion` | Migración mixins → composición **cerrada**; inventario: `python3 scripts/analyze_mixin.py` |

**Inventario mixins (controllers):** en el worktree actual no hay `*_mixin.py` bajo `controllers/`. Ver `migracion_mixins_composicion/SKILL.md`.

**Monolitos:** informes bajo demanda con `python3 scripts/monolith_analyzer.py` — ver `Documentacion/Refactorizacion_Completa/Monolitos/PLAN_MONOLITOS.md`.

**Scripts útiles:** `scripts/audit_module_docstrings.py`, `scripts/audit_import_graph.py` → salidas habituales bajo `reports/` (ignorado en git si aplica).
