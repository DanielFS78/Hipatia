# Inventario migración AppModel → DI (2026)

Fuente: `core/app_model.py`, búsquedas `rg` por consumidor y plan «Migración completa AppModel → DI».

## Criterio de cierre (recordatorio)

- **Delegación pura:** eliminar de `AppModel` solo cuando **cero** referencias en repo (`model.<metodo>`, `app.model.<metodo>`, tests, scripts).
- **Orquestación** (`get_dashboard_stats`, etc.): permanece en `AppModel`.
- **Señales** y `_connect_service_signals`: permanecen en `AppModel`.
- Contrato de «terminado» del plan: **no** borrar la clase `AppModel`; sí podar delegadores huérfanos y consumir servicios vía **DI** donde ya se migró la UI.

## Oleada 1 — Reportes (cerrada 2026-04)

Los siguientes delegadores **ya fueron eliminados** de `AppModel`; la UI usa solo `ReportService` (`hub.container` o `hub.model.report_service`):

| Método (histórico AppModel) | API actual |
|----------------------------|------------|
| `search_reports_data` | `ReportService.search_reports_data` |
| `get_orders_for_product` | `ReportService.get_orders_for_product` |
| `get_order_details` | `ReportService.get_order_details` |
| `get_order_units` | `ReportService.get_order_units` |
| `get_product_time_stats` | `ReportService.get_product_time_stats` |
| `get_worker_time_stats` | `ReportService.get_worker_time_stats` |
| `get_incidents_stats` | `ReportService.get_incidents_stats` |
| `get_evolution_stats` | `ReportService.get_evolution_stats` |
| `get_product_summary` | `ReportService.get_product_summary` |
| `get_product_reports_dashboard` | `ReportService.get_product_dashboard` |

Archivos de referencia: `ui/widgets/reportes_widget.py`, `ui/widgets/reports/order_list.py`, `charts_container.py`, `smart_search.py`.

## Oleada 2 — Diálogos / presenters (cerrada en alcance B5 + seguimiento)

- Bitácora, `define_flow`, `dialog_dependencies`: alineados con `.agents/skills/ui_dialog_dependency_wiring/SKILL.md`.
- `AssignPreprocesosDialog`: fallback de preprocesos vía `model.fabricacion_service.get_preprocesos_by_fabricacion` (no delegador directo en `AppModel`).

## Oleada 3 — Tests

- Tests de reportes migrados a `create_autospec(ReportService, instance=True)` (y `model.report_service` en integración).
- Otros dominios pueden seguir mockeando `app.model.get_*` hasta la siguiente poda por método.

## Oleada 4 — Controladores / cableado

- Sin megarefactor de `AppController`: el hub (`set_controller`, señales) se mantiene; nuevas pantallas deben preferir DI según `.agents/skills/reduccion_god_objects/SKILL.md`.

## Poda incremental reciente (simulación / lotes)

- `get_lote_details` retirado de `AppModel`: `ui/widgets/calculate_times_widget.py` usa `app.model.system_integration.get_lote_details` si no hay `db.lote_repo`; fabricación asociada vía `db.preproceso_repo.get_fabricacion_by_id`.

## Próximos pasos (mantenimiento)

- Inventariar con `rg` cada delegador restante en `app_model.py` (patrón `return self\.\w+\.`) y podar solo con consumidor cero.
- Mantener coherente `scripts/generate_daniel_doc.py` y la skill `reduccion_god_objects` al cambiar contratos de widgets raíz.

## Referencias

- `.agents/skills/reduccion_god_objects/SKILL.md` — política B5, poda reciente, métodos que suelen permanecer.
- `.agents/skills/ui_dialog_dependency_wiring/SKILL.md` — resolución de servicios en diálogos.
