# REGISTRO — UI dialog dependency wiring (Hipatia)

Fuente de verdad del avance del plan **wiring de dependencias en diálogos UI**. Actualizar al cerrar cada ítem o fase.

| Fase | Ítem | Archivos | Estado | Fecha | Commit | Notas | Tests ejecutados |
|------|------|----------|--------|-------|--------|-------|------------------|
| 0 | Baseline + inventario | REGISTRO, skill | Hecho | 2026-04-03 | 8f7be47 | AssignPreprocesosDialog: sin call site en app; solo tests + export público. Mantener API; enlazar menú = trabajo futuro opcional. | `pytest tests/unit -q` (2399 OK) |
| 1 | `dialog_dependencies` + refactor diálogos | `ui/dialogs/fabrication/dialog_dependencies.py`, assignment, bitacora, `test_dialog_dependencies.py` | Hecho | 2026-04-03 | — | Prioridades DI → product_controller → model.fabricacion_service / model.pila_service | ver gates.md |
| 2 | Inyección opcional constructores | bitacora, assignment | Hecho | 2026-04-03 | — | `pila_service=`, `fabricacion_service=` | ver gates.md |
| 3 | Call site bitácora | `pila_manager.py` | Hecho | 2026-04-03 | — | Pasa `pila_service=self._pila_service` | ver gates.md |
| 4 | Protocol `OpensFabricacionPreprocesos` | `ui/dialogs/fabrication/ui_dialog_protocols.py`, assignment | Hecho | 2026-04-03 | — | En UI para evitar import cíclico `controllers`→`ui.dialogs`; `AppController` por defecto | ver gates.md |
| 5 | Documentación fallback | SKILL.md, REGISTRO | Hecho | 2026-04-03 | — | Ramas `model.*` documentadas como fallback tests/legacy | — |
| 6 | `flow_action_handler` + deps pila | `flow_action_handler.py` | Hecho | 2026-04-03 | — | Usa `resolve_pila_service` compartido con bitácora | ver gates.md |
| 7 | Call site `AssignPreprocesosDialog` | `preprocesos_widget.py` | Hecho | 2026-04-04 | 2f65583 | Botón en pestaña Preprocesos; `set_controller` guarda `AppController` | `pytest tests/unit/test_preprocesos_widget.py -q` |
| 8 | `DefineProductionFlowDialog` + `resolve_fabricacion_service` | `define_flow_dialog.py` | Hecho | 2026-04-04 | 6e73d1b | Misma prioridad DI → PC → `model.fabricacion_service` que assignment | `pytest tests/unit/test_define_flow_dialog.py tests/unit/test_define_flow_dialog_edge.py -q` |
| 9 | Inyección explícita Fab + API única pilas | `preprocesos_widget.py`, `flow_action_handler.py` | Hecho | 2026-04-04 | 240e826 | `AssignPreprocesosDialog` recibe `fabricacion_service` desde `resolve_*`; `load_saved_pila` usa `_pila_list_load_api()` | `pytest tests/unit/test_preprocesos_widget.py tests/unit/ui/production_flow/test_flow_action_handler.py -q` |

## Inventario rápido (Fase 0)

- **FabricacionBitacoraDialog**: call site en `controllers/pila/pila_manager.py`.
- **AssignPreprocesosDialog**: call site en `ui/widgets/preprocesos_widget.py` (botón «Asignar preprocesos a fabricaciones»); export en `ui/dialogs/__init__.py`.
- **Lotes / DI**: `ui/widgets/lotes_widget.py` resuelve `LoteController`, `ProductService`, `FabricacionService` vía DI en `__init__` (fuera del alcance inmediato de este REGISTRO).
