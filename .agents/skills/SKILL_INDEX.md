# Índice de Agent Skills — Hipatia

Actualizado: 2026-04. Las skills en **Activa** son norma operativa; **Archivo** indica fases cerradas o autopilots obsoletos (solo contexto histórico).

| Skill | Estado | Uso |
|-------|--------|-----|
| `strict_testing` | Activa | Reglas del dashboard / mocks estrictos |
| `testing_antipatrones` | Activa | Catálogo de falsos positivos |
| `testing_fixtures_y_mocks` | Activa | Fixtures, autospec, DummyModel |
| `testing_por_capa` | Activa | Qué testear por capa |
| `testing_pyqt6_headless` | Activa | Qt headless / macOS |
| `orden_trabajo_tests` | Activa | Orden de archivos de test |
| `backlog_tests` | Activa | Backlog por impacto |
| `backlog_tests_en_progreso` | Activa | Tests en progreso |
| `estandar_documentacion` | Activa | Docstrings y docs técnicas |
| `ejecucion_secuencial_calidad` | Activa | Gates por item + REGISTRO |
| `references/sync_icloud_continuo.md` | Activa | Sync worktree → iCloud (obligación del agente); automatizar con `scripts/sync_worktree_to_icloud.py` |
| `plan_produccion_coordinador` | Activa | Prioridades hacia Windows |
| `plan_mejora_calidad` | Activa | Hub calidad / fases cerradas |
| `preparacion_windows` | Activa | DPI, Qt, PyInstaller |
| `ui_pyqt_layout_freezes` | Activa | Congelaciones UI PyQt6 |
| `limpieza_proyecto` | Activa | Artefactos antes de empaquetar |
| `migracion_mixins_composicion` | Solo referencia | Migración **cerrada** en repo actual; inventario: `python3 scripts/analyze_mixin.py` |
| `reduccion_god_objects` | Activa | Reducir fachada AppModel |
| `refactorizacion_mcp` | Solo referencia | Plan histórico cerrado 2026-03-20 |
| `fase12c_sanear_frontera_ui` | Solo referencia | Frontera UI/DTO cerrada |
| `fase12c_autopilot_production_flow_refactor` | Archivo | Autopilot cerrado; no backlog activo |
| `fase_legacy` | Solo referencia | Criterios legacy |
| `fase_legacy_autopilot` | Archivo | Autopilot; no ejecutar como cola viva |
| `fase_monolitos_autopilot` | Archivo | Idem |
| `fase_monolitos_finales_autopilot` | Archivo | Idem |
| `fase_tests_en_progreso_74_autopilot` | Archivo | Idem |

**Inventario real de mixins (controllers):** en el worktree actual no hay `*_mixin.py` bajo `controllers/`. Controladores usan `*Manager` / `*Helper` / `*Binder`. Ver `migracion_mixins_composicion/SKILL.md` § Estado 2026-04.

**Scripts de arquitectura / documentación:** `scripts/audit_module_docstrings.py`, `scripts/audit_import_graph.py` → informes bajo `reports/`.
