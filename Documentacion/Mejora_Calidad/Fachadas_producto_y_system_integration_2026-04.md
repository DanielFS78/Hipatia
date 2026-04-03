# Fachadas de producto / planificación y `SystemIntegrationService` (abr. 2026)

Nota técnica breve para alinear el árbol iCloud y los worktrees con el wiring vigente.

## Objetivo

- Reducir acceso directo a repositorios desde controladores donde ya existe una capa estable.
- Unificar el catálogo de producto detrás de `ProductFacade` y los datos de cálculo detrás de `PlanningFacade`.

## Cambios relevantes

### `SystemIntegrationService` (`core/services/system_integration_service.py`)

- Encapsula lotes, configuración persistente y órdenes de tracking.
- Expone `lote_repo` y `preproceso_repo` como propiedades de delegación hacia `DatabaseManager` para compatibilidad con `IPilaDatabase`.

### `PilaController` / `LoteManager`

- `LoteManager` recibe `db=model.system_integration` (antes `db.lote_repo`).
- Selección y detalle de lotes en gestión usan `model.system_integration.get_lote_details` y `preproceso_repo` vía la misma integración.

### `ProductFacade` y `ProductController` v2

- `ProductFacade` delega métodos usados por la UI: entre otros `get_product_by_code`, `update_product_iteration`, `update_iteration_file_path`.
- `ProductController`: `product_facade = model.product_facade`, `product_service = product_facade.service` (señales Qt y compatibilidad).
- `ProductManager` y `BOMImportService` usan `product_facade`.
- `FabricacionProductsHandler`: catálogo vía `product_facade`; `get_data_for_calculation` vía `planning_facade` (dominio de pilas/planificación).

### Protocolos

- `IProductModel` incluye `product_facade` y `planning_facade`.
- `get_data_for_calculation` se retiró de `IProductService` (no pertenece al servicio de producto).

## Tests tocados (referencia)

- `tests/unit/test_phase5_di_injection.py`, `test_pila_controller_comprehensive.py`
- `tests/controllers/product/test_product_manager.py`, `test_fabricacion_manager.py`
- `tests/unit/test_product_controller_preprocesos.py`, `test_product_controller_v2_comprehensive.py`, `test_security_phase2_integration.py`

## Tabla archivo → destino (lote focal copiado al clon iCloud)

La ruta de destino es siempre la **misma ruta relativa** dentro del árbol Hipatia en iCloud. Definición habitual de la variable:

`HIPATIA_ICLOUD="$HOME/Library/Mobile Documents/com~apple~CloudDocs/Programacion/Calcular_tiempos_fabricacion"`

| Archivo (origen en worktree / repo) | Destino |
| --- | --- |
| `Documentacion/Mejora_Calidad/Fachadas_producto_y_system_integration_2026-04.md` | `$HIPATIA_ICLOUD/Documentacion/Mejora_Calidad/Fachadas_producto_y_system_integration_2026-04.md` |
| `core/app_model.py` | `$HIPATIA_ICLOUD/core/app_model.py` |
| `core/facades/__init__.py` | `$HIPATIA_ICLOUD/core/facades/__init__.py` |
| `core/facades/planning_facade.py` | `$HIPATIA_ICLOUD/core/facades/planning_facade.py` |
| `core/facades/product_facade.py` | `$HIPATIA_ICLOUD/core/facades/product_facade.py` |
| `core/services/product_service.py` | `$HIPATIA_ICLOUD/core/services/product_service.py` |
| `core/services/system_integration_service.py` | `$HIPATIA_ICLOUD/core/services/system_integration_service.py` |
| `controllers/pila/controller.py` | `$HIPATIA_ICLOUD/controllers/pila/controller.py` |
| `controllers/pila/protocols.py` | `$HIPATIA_ICLOUD/controllers/pila/protocols.py` |
| `controllers/product/fabricacion_manager.py` | `$HIPATIA_ICLOUD/controllers/product/fabricacion_manager.py` |
| `controllers/product/fabricacion_products_handler.py` | `$HIPATIA_ICLOUD/controllers/product/fabricacion_products_handler.py` |
| `controllers/product/product_manager.py` | `$HIPATIA_ICLOUD/controllers/product/product_manager.py` |
| `controllers/product/protocols.py` | `$HIPATIA_ICLOUD/controllers/product/protocols.py` |
| `controllers/product_controller_v2.py` | `$HIPATIA_ICLOUD/controllers/product_controller_v2.py` |
| `tests/controllers/product/test_fabricacion_manager.py` | `$HIPATIA_ICLOUD/tests/controllers/product/test_fabricacion_manager.py` |
| `tests/controllers/product/test_product_manager.py` | `$HIPATIA_ICLOUD/tests/controllers/product/test_product_manager.py` |
| `tests/unit/test_phase5_di_injection.py` | `$HIPATIA_ICLOUD/tests/unit/test_phase5_di_injection.py` |
| `tests/unit/test_pila_controller_comprehensive.py` | `$HIPATIA_ICLOUD/tests/unit/test_pila_controller_comprehensive.py` |
| `tests/unit/test_product_controller_preprocesos.py` | `$HIPATIA_ICLOUD/tests/unit/test_product_controller_preprocesos.py` |
| `tests/unit/test_product_controller_v2_comprehensive.py` | `$HIPATIA_ICLOUD/tests/unit/test_product_controller_v2_comprehensive.py` |
| `tests/unit/test_security_phase2_integration.py` | `$HIPATIA_ICLOUD/tests/unit/test_security_phase2_integration.py` |

Ruta absoluta de ejemplo en macOS (misma fila que la primera):  
`~/Library/Mobile Documents/com~apple~CloudDocs/Programacion/Calcular_tiempos_fabricacion/Documentacion/Mejora_Calidad/Fachadas_producto_y_system_integration_2026-04.md`

## Sincronización worktree → iCloud

Si el workspace es un worktree distinto del clon en iCloud:

```bash
export HIPATIA_ICLOUD="$HOME/Library/Mobile Documents/com~apple~CloudDocs/Programacion/Calcular_tiempos_fabricacion"
python3 scripts/sync_worktree_to_icloud.py --dry-run   # revisar
python3 scripts/sync_worktree_to_icloud.py              # copia todo lo que salga en git status
```

**Advertencia:** con muchos cambios locales, el script puede listar cientos de rutas; conviene revisar el dry-run antes de copiar.
