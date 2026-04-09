# Audit import graph — controllers ↔ core.services

Generado por `scripts/audit_import_graph.py`.

## `controllers.*` → `core.services.*`

| Módulo controlador | Importa |
|:--|:--|
| `controllers.app_controller` | `core.services.product_service` |
| `controllers.backup_controller` | `core.services.audit_logger` |
| `controllers.backup_controller` | `core.services.backup_service` |
| `controllers.backup_controller_io_manager` | `core.services.audit_logger` |
| `controllers.historial.report_manager` | `core.services.report_strategy` |
| `controllers.machine_controller` | `core.services.machine_service` |
| `controllers.machine_controller` | `core.services.preparation_service` |
| `controllers.machine_controller` | `core.services.product_service` |
| `controllers.navigation_controller` | `core.services.product_service` |
| `controllers.pila.pila_manager` | `core.services.time_calculator` |
| `controllers.product.material_manager` | `core.services.data_importer` |
| `controllers.product.protocols` | `core.services.fabricacion_service` |
| `controllers.product.protocols` | `core.services.product_service` |
| `controllers.report_controller` | `core.services.pila_service` |
| `controllers.report_controller` | `core.services.product_service` |
| `controllers.report_controller` | `core.services.report_strategy` |
| `controllers.report_controller` | `core.services.worker_service` |
| `controllers.session_controller` | `core.services.audit_logger` |
| `controllers.session_controller` | `core.services.rate_limiter` |
| `controllers.simulation.controller` | `core.services.flow_builder_service` |
| `controllers.simulation.execution_manager` | `core.services.time_calculator` |
| `controllers.simulation.optimizer_worker` | `core.services.flow_builder_service` |
| `controllers.simulation.optimizer_worker` | `core.services.time_calculator` |
| `controllers.startup_controller` | `core.services.audit_logger` |
| `controllers.startup_controller` | `core.services.backup_service` |
| `controllers.startup_controller` | `core.services.fabricacion_service` |
| `controllers.startup_controller` | `core.services.machine_service` |
| `controllers.startup_controller` | `core.services.maintenance_service` |
| `controllers.startup_controller` | `core.services.pila_service` |
| `controllers.startup_controller` | `core.services.preparation_service` |
| `controllers.startup_controller` | `core.services.product_service` |
| `controllers.startup_controller` | `core.services.rate_limiter` |
| `controllers.startup_controller` | `core.services.report_service` |
| `controllers.startup_controller` | `core.services.system_integration_service` |
| `controllers.startup_controller` | `core.services.tracking_assignment_service` |
| `controllers.startup_controller` | `core.services.worker_service` |
| `controllers.ui_controller` | `core.services.machine_service` |
| `controllers.ui_controller` | `core.services.product_service` |
| `controllers.ui_controller` | `core.services.report_service` |
| `controllers.ui_controller` | `core.services.worker_service` |

## Resumen por prefijo (módulos escaneados)

- `core.*`: **117** referencias desde imports nominales
- `controllers.*`: **87** referencias desde imports nominales
- `ui.*`: **57** referencias desde imports nominales
- `core.services.*`: **53** referencias desde imports nominales
- `database.*`: **34** referencias desde imports nominales
- `features.*`: **6** referencias desde imports nominales
