---
name: Migración de Mixins a Composición
description: Histórico + referencia del patrón Composición (Managers/Helpers). En el repo actual la migración de mixins en controllers está cerrada; usar SKILL_INDEX.md y scripts de inventario para verificar.
---

# Migración de Mixins a Composición — Proyecto Hipatia

## Estado 2026-04 (worktree actual)

- **No** hay archivos `*_mixin.py` bajo `controllers/` (salvo referencias en tests o `scripts/analyze_mixin.py`).
- Sustituciones vigentes: `BackupIOManager`, `ReportExportManager`, `UISignalsWiring` (usado por `UISignalsController`), `ScheduleUiOpsHelper` (incluye la antigua API de `ScheduleLegacyApiHelper`), managers bajo `controllers/product/`, etc.

### Cierre explícito: señales UI y backup I/O (sin herencia múltiple)

| Histórico (ya no en el repo) | Implementación actual |
|:--|:--|
| `backup_controller_io_mixin.py` | `controllers/backup_controller_io_manager.py` → clase **`BackupIOManager`**: `BackupController` hace `self._db_io = BackupIOManager(self)` y delega `on_import_databases` / `on_export_databases` / `on_sync_databases`. **Sin mixin.** |
| `ui_signals_controller_mixin.py` | **`UISignalsController`** (`controllers/ui_signals_controller.py`) es un `QObject` aparte; el cableado vive en **`UISignalsWiring`** (`controllers/ui_signals_wiring.py`). `AppController` solo **compone** `self.ui_signals_controller = UISignalsController(self)` en `initialize_infra` / arranque. **Sin mixin sobre `AppController`.** |
- **Inventario reproducible:** `python3 scripts/analyze_mixin.py` (y búsqueda `rg '_mixin\\.py' --glob '*.py'`).
- Índice de skills: [SKILL_INDEX.md](SKILL_INDEX.md).

## Contexto (histórico)

En fases anteriores existían numerosos mixins “partidores”. Se distinguían dos tipos:

- **Tipo A — Fragmentadores de monolito:** debían migrar a composición.
- **Tipo B — Delegación:** válidos temporalmente; el destino era también composición explícita (`Helper`/`Manager`).

## Patrón a Seguir (ya implementado)

`PilaController` es el ejemplo correcto del proyecto:

```python
# ✅ CORRECTO: Composición — instancia collaborators
class PilaController(QObject):
    def __init__(self, app_controller):
        self.lote_manager = LoteManager(...)    # Collaborator
        self.pila_manager = PilaManager(...)    # Collaborator
```

```python
# ❌ INCORRECTO: Herencia múltiple para partir un archivo grande
class AppModel(QObject, AppModelFabricacionMixin, AppModelProductMixin, 
               AppModelPilaMixin, AppModelReportsMixin, ...):
```

## Archivos a Migrar (Tipo A — por prioridad)

### Prioridad 1: AppModel (6 mixins → delegates)

El caso más grave. 148 métodos delegadores repartidos en 6 mixins.

| Mixin actual | Nuevo Delegate | Métodos |
|:--|:--|--:|
| `app_model_fabricacion_mixin.py` | Ya delegado a `FabricacionService` — **eliminar mixin** | 18 |
| `app_model_product_mixin.py` | Ya delegado a `ProductService` — **eliminar mixin** | 23 |
| `app_model_pila_mixin.py` | Ya delegado a `PilaService` — **eliminar mixin** | 10 |
| `app_model_reports_mixin.py` | Ya delegado a `ReportService` — **eliminar mixin** | 9 |
| `app_model_resources_mixin.py` | Nuevo: `ResourceConfigDelegate` o mantener en `app_model.py` | 37 |
| `app_model_legacy_repos_mixin.py` | **Eliminar** — mover los 8 métodos restantes al propio `app_model.py` | 8 |

**Estrategia para AppModel:** Los mixins son pura delegación (`self.service.method(...)`). La migración consiste en eliminar cada mixin y mover sus métodos al `app_model.py` principal o, mejor, que los controladores accedan directamente al servicio vía `DIContainer.resolve(ProductService)`.

### Prioridad 2: ScheduleController (cerrado en 2026-04)

| Antes (histórico) | Estado actual |
|:--|:--|
| UI vía mixin | `ScheduleUiOpsHelper` |
| API programática legacy | Misma clase: métodos `add_break` / `delete_break` / `save_work_hours` / `load_schedule_config` en `ScheduleUiOpsHelper` (archivo `schedule_legacy_helper.py` eliminado). |

### Prioridad 3: Repositorios (4 mixins)

| Mixin actual | Acción |
|:--|:--|
| `iteration_repository_crud_mixin.py` | Absorber en `iteration_repository.py` (archivo resultante < 200 líneas) |
| `iteration_repository_images_mixin.py` | Absorber en `iteration_repository.py` |
| `material_repository_links_mixin.py` | Absorber en `material_repository.py` |
| `product_repository_fabricacion_mixin.py` | Absorber en `product_repository.py` |

### Prioridad 4: UI (2 mixins)

| Mixin actual | Acción |
|:--|:--|
| `settings_widget_schedule_mixin.py` | Nuevo: `ScheduleSettingsPanel(QWidget)` como widget embebido |
| `iterations_widget_gallery_mixin.py` | Absorber en widget principal si < 300 líneas, o crear `GalleryHelper` |

### Prioridad 5: Mixins de Delegación Remanentes (User Detection)

Mixins que, aunque delegan, crean herencia múltiple innecesaria.

| Mixin actual | Acción |
|:--|:--|
| `backup_controller_io_mixin.py` | ✅ Sustituido por **`BackupIOManager`** (`backup_controller_io_manager.py`), composición en `BackupController`. |
| `ui_signals_controller_mixin.py` | ✅ Sustituido por **`UISignalsController`** + **`UISignalsWiring`**; no hay mixin en `AppController`. |
| `app_controller_compat_mixin.py` | ✅ Absorbido en `AppController` (mixin eliminado) |
| `fabricacion_manager_products_mixin.py` | ✅ Sustituido por `fabricacion_products_handler.py` (`FabricacionProductsHandler`) |
| `enhanced_flow_presenter_builder.py` | ✅ `FlowBuilder` en `ui/dialogs/production_flow/flow_builder.py` |

## Reglas de Migración

1. **Un mixin a la vez.** Migrar, ejecutar tests, pasar al siguiente.
2. **No cambiar la API pública.** Los métodos que expone la clase final deben seguir existiendo con la misma firma.
3. **Verificación obligatoria:** `pytest tests/ -x -q` tras cada mixin eliminado.
4. **Si el archivo resultante supera 400 líneas**, crear un `Delegate`/`Helper` como clase independiente (composición), no un nuevo mixin.
5. **Actualizar imports** en todos los consumidores del mixin eliminado.

## Estado

- [x] AppModel — `app_model_fabricacion_mixin.py` eliminado
- [x] AppModel — `app_model_product_mixin.py` eliminado
- [x] AppModel — `app_model_pila_mixin.py` eliminado
- [x] AppModel — `app_model_reports_mixin.py` eliminado
- [x] AppModel — `app_model_resources_mixin.py` absorbido/delegado
- [x] AppModel — `app_model_legacy_repos_mixin.py` eliminado
- [x] ScheduleController — `schedule_ui_ops.py` → Helper
- [x] ScheduleController — `schedule_legacy_api.py` → Helper
- [x] Repositorios — 4 mixins absorbidos (Material, Product, Iteration CRUD/Images)
- [x] UI — 2 mixins absorbidos/delegados (Settings, Iterations Gallery)
- [x] B4.5 — Mixins de Delegación (AppController, Fabricacion, FlowBuilder) — ver § **B4.5 — Protocolo de implementación**
  - [x] **Fabricación:** `FabricacionManagerProductsMixin` sustituido por `FabricacionProductsHandler` (composición).
  - [x] AppController — `AppControllerCompatMixin` absorbido en `app_controller.py`
  - [x] Enhanced flow — `FlowBuilder` compuesto desde `EnhancedFlowPresenter` (`flow_builder.py`)
  - [x] **Backup I/O:** `backup_controller_io_mixin` → `BackupIOManager` en `BackupController`.
  - [x] **Señales UI:** `ui_signals_controller_mixin` → `UISignalsController` + `UISignalsWiring` (composición desde `AppController`).

---

## B4.5 — Protocolo de implementación (Plan Producción, Bloque B)

> **No confundir** con el **«Checklist Revisión Fase B»** de tests (`.agents/skills/backlog_tests/SKILL.md`). **B4.5** es la tarea **B4.5** del coordinador: *Limpieza final de mixins* antes de **B5** (`reduccion_god_objects`).

### Alcance (tres piezas del corazón)

| Pieza | Archivo actual | Clase host | Riesgo |
|-------|----------------|------------|--------|
| Compat AppController | *(eliminado)* | `AppController` | ✅ Métodos en el propio `AppController`. |
| Productos fabricación | `controllers/product/fabricacion_products_handler.py` | `FabricacionManager` | ✅ `FabricacionProductsHandler`. |
| Builder flujo enhanced | `ui/dialogs/production_flow/flow_builder.py` | `EnhancedFlowPresenter` | ✅ `FlowBuilder`; estado en el presentador / helpers asociados. |

### Orden recomendado (una pieza por iteración)

1. **FabricacionManager** — Menor radio de imports; validar `FabricacionManager` y `fabricacion_controller` / `product_controller`.
2. **EnhancedFlowPresenter** — Extraer **`FlowBuilder`** (o nombre acordado: `EnhancedFlowBuildService`) instanciado por el presentador; conservar **misma API pública** del presentador (`load_flow`, `build_production_flow`, etc.).
3. **AppController** — Último: absorber en `AppController` o extraer **`NavigationHelper` / `AppControllerCompatBridge`** (objeto con referencias a controladores) para no tocar firmas públicas usadas en decenas de tests.

### Patrón de trabajo (obligatorio)

Seguir **Protocolo de Trabajo** de `.agents/skills/plan_produccion_coordinador/SKILL.md` (tests base → cambio → tests nuevos si aplica → suite/mypy → docstrings → `generate_daniel_doc.py` → marcar tarea).

Además, para B4.5:

1. **Antes de codificar — mapa de hilos**
   - `rg -n "NombreMixin|nombre_metodo_clave" --glob '*.py'` sobre `controllers/` y `ui/`.
   - Para cada mixin: `python3 scripts/analyze_mixin.py <ruta_del_mixin.py>` (atributos `self.*` y llamadas).
   - Opcional: `scripts/analysis/analyze_dependencies.py` / informes en `scripts/analysis/` para impacto entre capas.
2. **Nomenclatura**
   - Helpers: sufijo **`Helper`** o **`…Service`** si es lógica sin Qt; **`…Panel`** solo si es widget.
   - No renombrar métodos públicos de `AppController` / `FabricacionManager` / `EnhancedFlowPresenter` salvo plan explícito + actualizar todos los callers y tests.
3. **DTOs y tipado**
   - Mantener anotaciones existentes (`ProductionFlowStepDTO`, `FileOperationResultDTO`, `CalculationProductDTO`, etc.).
   - Tras mover código: `python3 -m mypy <archivos_tocados> --config-file mypy.ini` y ampliar a proyecto si el cambio es transversal.
4. **Tests**
   - Localizar con `rg` tests que mockean `handle_save_flow_only`, `show_fabricacion_products`, `EnhancedFlowPresenter`, `load_flow`, `build_production_flow`.
   - Prioridad: `tests/unit/test_product_controller_v2_comprehensive.py`, `test_fabricacion_controller_comprehensive.py`, `test_simulation_controller_comprehensive.py`, `test_enhanced_flow_presenter.py`, `test_enhanced_flow_dialog.py`, `tests/unit/ui/production_flow/test_flow_action_handler.py`.
   - Cualquier clase nueva: tests dedicados o ampliación siguiendo `strict_testing` + `testing_fixtures_y_mocks`.
5. **Documentación**
   - Docstrings en español en módulos/clases nuevas o sustancialmente cambiadas (`estandar_documentacion`).
   - `python3 scripts/generate_daniel_doc.py` al cerrar cada sub-bloque.
   - Actualizar esta skill ([x] B4.5) y la tabla en `plan_produccion_coordinador` cuando las tres piezas estén hechas.

### Relación con B5

**B4.5** elimina herencia mixin; **B5** reduce la fachada `AppModel` hacia servicios vía DI. No mezclar: cerrar B4.5 antes de asumir refactors grandes de `AppModel` salvo coordinación explícita.
