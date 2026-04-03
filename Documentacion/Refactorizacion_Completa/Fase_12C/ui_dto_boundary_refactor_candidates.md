# Fase 12C — Candidatos para refactorización (production_flow incluido)

Este listado se genera a partir de:
- `Documentacion/Refactorizacion_Completa/Fase_12C/ui_dto_boundary_report.json` (modo `--include-production-flow`)

Criterio de selección (pragmático y orientado a calidad):
- Archivos con hallazgos de acceso tipo dict en `ui/**`
- Se prioriza por cantidad de hallazgos (impacto) para maximizar la mejora del contrato UI→DTO.

## Work order (orden por prioridad)

| # | Archivo | Hallazgos |
|---:|---|---:|
| 1 | `ui/widgets/production_flow/inspector_panel.py` | 120 |
| 2 | `ui/dialogs/production_flow/enhanced_flow_presenter_builder.py` | 64 |
| 3 | `ui/widgets/production_flow/flow_graph_manager.py` | 47 |
| 4 | `ui/dialogs/production_flow/enhanced_flow_presenter_state.py` | 36 |
| 5 | `ui/dialogs/production_flow/define_flow_dialog.py` | 35 |
| 6 | `ui/dialogs/production_flow/define_flow_presenter.py` | 32 |
| 7 | `ui/dialogs/production_flow/common_dialogs.py` | 23 |
| 8 | `ui/widgets/production_flow/flow_canvas.py` | 12 |
| 9 | `ui/widgets/production_flow/inspector_presenter.py` | 12 |
| 10 | `ui/dialogs/production_flow/enhanced_flow_dialog.py` | 10 |
| 11 | `ui/dialogs/canvas_widget.py` | 7 |
| 12 | `ui/dialogs/card_widget.py` | 2 |
| 13 | `ui/widgets/production_flow/define_control_panel.py` | 2 |
| 14 | `ui/widgets/production_flow/library_panel.py` | 2 |

## Criterio de ✅ (cerrar archivo)

- Tras refactorización, re-ejecutar:
  - `python3 scripts/ui_dto_boundary_analyzer.py --include-production-flow`
- El archivo ya no debe aparecer como afectado en el reporte (o su conteo cae a 0).
- `python3 -m pytest <tests_relacionados> -x -q` pasa.
- `python3 run_tests.py` pasa.

