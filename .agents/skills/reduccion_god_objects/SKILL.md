---
name: Reducción de God Objects (AppModel Facade)
description: Guía de arquitectura y mantenimiento sobre AppModel. La tarea coordinada B5 («inyectar servicios directos») está FINALIZADA (2026-04); esta skill documenta qué se hizo, qué queda fuera del alcance de B5 y por qué, y cómo hacer podas futuras opcionales.
---

# Reducción de God Objects — Proyecto Hipatia

## Estado de la tarea B5 (coordinador producción): **FINALIZADA**

La fila **B5** en `.agents/skills/plan_produccion_coordinador/SKILL.md` está **cerrada de forma definitiva**. No hay subtareas pendientes bajo el epígrafe «B5»; lo que sigue en la lista del coordinador es el **Bloque C** (Windows).

**Qué cubría B5 (hecho):** priorizar **servicios registrados en `DIContainer`** frente a `AppModel` en los puntos acordados (`AppController.on_data_changed` + `ProductService`, reportes UI + `ReportService`, config temprana vía `self.db`, y `DefineProductionFlowDialog` / `DefineFlowPresenter` con servicios desde DI o extraídos de `model.*_service` sin pasar `AppModel` al presenter).

**Qué queda fuera del alcance de B5 (y por qué):**

| Fuera de alcance | Qué es concretamente | Por qué no forma parte de B5 | Dónde queda documentado / regla |
|------------------|----------------------|------------------------------|----------------------------------|
| Poda masiva de `AppModel` | Siguen existiendo muchos métodos delegadores (~orden cientos de líneas de API en `core/app_model.py`) | B5 era **reducir dependencia en el uso**, no borrar la fachada entera; eliminar métodos solo con **`rg` = 0 consumidores** en repo | Esta skill, §Fase 2–3; REGISTRO ítems 005–006 |
| Fallback en diálogos de fabricación | Bitácora → `planning_facade` / servicios; preprocesos → `model.fabricacion_service.get_preprocesos_by_fabricacion` si `resolve_fabricacion_service` es `None` | Plan en **ui_dialog_dependency_wiring** (Fase 5) | `.agents/skills/ui_dialog_dependency_wiring/SKILL.md` + `REGISTRO.md` |
| Señales Qt y conexión desde controladores | p. ej. `app.model.machines_changed_signal`, `product_deleted_signal` | Arquitectura acordada: **señales permanecen en `AppModel`** (o un hub futuro sería **otra** tarea) | Esta skill, §Regla 3 |
| Orquestación multi-servicio en `AppModel` | p. ej. `get_dashboard_stats` y métodos que combinan varios servicios | No son delegación de una línea; rediseñarlos es **nuevo caso de uso**, no cierre de B5 | §Fase 3 «Mínimo razonable» |
| Bootstrap de arranque | `StartupController` lee `self.model.db`, registra instancias que viven en `AppModel` | El **compositor raíz** sigue construyendo el grafo; B5 no sustituyó el bootstrap completo | `controllers/startup_controller.py` |
| Sub-widgets de reportes | Solo `report_service=` / `set_report_service` (`ReportService` desde DI o `hub.model.report_service`) | Sin `fallback_reports_model` ni delegadores de reportes en `AppModel` (2026-04) | `ui/widgets/reportes_widget.py`, `ui/widgets/reports/order_list.py`, `charts_container.py`, `smart_search.py` |

**Para el agente o desarrollador:** si aparece la duda «¿B5 sigue abierta?» → **No.** Cualquier mejora adicional es **mantenimiento opcional** (poda puntual de `AppModel`, más DI en un widget concreto) y debe ir con su propio ítem en `REGISTRO_EJECUCION_ITEMS.md` o issue, no como «continuación de B5».

---

## Problema

`AppModel` (`core/app_model.py`) actúa como fachada con **~110 métodos** de delegación a servicios, facades y `DatabaseManager`. Cada método suele ser una línea que reenvía a `*_service`, `product_facade`, `planning_facade` o `system_integration`. Eso diluye el SRP: nuevos casos de uso empujan a crecer la fachada sin aportar lógica.

**Nota (2026-04):** La fase de mixins en AppModel está cerrada; el modelo es una clase única. La reducción pasa por **inyección directa** y **poda de delegadores huérfanos** (solo tras `rg` con cero consumidores).

**Puentes `core/app_model_bridges/`:** No existen en el repo (`compat.py` / `planning.py` / `product.py` de ese paquete). Si un informe antiguo los cita como tarea pendiente, está obsoleto; ver `Documentacion/Arquitectura_AppModel_Bridges.md`.

## Solución

1. **Registrar servicios y facades en `DIContainer`** desde `StartupController._init_services` (`ProductService`, `WorkerService`, `PilaService`, `MachineService`, `PreparationService`, `FabricacionService`, `ReportService`, `TrackingAssignmentService`, `ProductFacade`, `PlanningFacade`, `SystemIntegrationService`, etc.).
2. **Constructores explícitos** en controladores que antes recibían solo `app` y leían `app.model.*`.
3. **`AppController`**: mantener API de compatibilidad donde la UI pasa el hub (`handle_save_flow_only`, `search_fabricaciones`, …); el refresco global de productos en `on_data_changed` usa `product_controller.product_service`, luego `ProductService` del DI si está registrado, y si no `model.product_service`. Config lectura/escritura temprana usa `self.db.config_repo` en el fallback sin `ScheduleController`.
4. **Podar `AppModel`**: eliminar métodos delegadores solo cuando no quede ningún uso en repo (tests, UI, scripts).

### Ejemplo de migración

```python
# ❌ ANTES: Controller → AppModel → Service
class MachineController:
    def __init__(self, app):
        self.model = app.model

    def get_machines(self):
        return self.model.get_all_machines()

# ✅ DESPUÉS: Controller → Service (directo)
class MachineController:
    def __init__(self, machine_service: MachineService):
        self.machine_service = machine_service

    def get_machines(self):
        return self.machine_service.get_all_machines()
```

## Fases de reducción

### Fase 1: Identificar delegación pura

Buscar patrones `return self.<servicio|facade>.` en `core/app_model.py`.

### Fase 2: Migrar controladores uno a uno

Para cada controlador que usa `self.app.model.get_X()`:

1. Cambiar el constructor para recibir el servicio (o facade) necesario.
2. Actualizar la factory en `startup_controller.py` resolviendo del contenedor.
3. Eliminar el delegador en `AppModel` **solo cuando `rg` no encuentre consumidores**.

### Fase 3: Mínimo razonable en AppModel

Conservar:

- Señales (`product_added_signal`, `workers_changed_signal`, …).
- `_connect_service_signals`.
- Métodos que **orquestan** varios servicios (p. ej. `get_dashboard_stats`).
- Delegación que siga siendo el contrato estable para pantallas que aún pasan el hub con `model` (hasta migrarlas a servicios concretos).

## Estado de controladores (2026-04)

| Controlador | Notas |
|:--|:--|
| `MachineController` | `MachineService` inyectado |
| `ReportController` | Servicios inyectados |
| `HistorialController` | Servicios inyectados |
| `WorkerController` | `WorkerService`, `ProductService`, `FabricacionService`, `workers_changed_signal`; `app` mínimo para sesión/navegación |
| `PilaController` | Servicios + `system_integration` + `ApplicationState` + `schedule_manager` |
| `SimulationController` | `WorkerService`, `MachineService`, `PilaService` + `app` |
| `CalculationController` | `PilaService` + `app` |
| `SessionController` | `db`, `WorkerService` + `app` |
| `ProductController` | Constructor explícito; `IApplicationShell` para managers (`handle_attach_file`, `session_controller`, `ui_controller`) |
| `AppController` | `on_data_changed` → `ProductService` vía DI; `config_*` fallback → `self.db` |
| `ReportesWidget` / sub-widgets reportes | `set_controller(hub)` re-resuelve `ReportService` vía `hub.container` o `hub.model.report_service`; hijos solo reciben `ReportService`, no guardan `AppController`. `connect_reportes_signals` enlaza con `self.app`. |
| `SettingsWidget` | `ScheduleController` vía `set_schedule_controller`; fallback lectura `config_repo` vía `set_config_db_fallback(db)` (`MainView.set_controller`) |
| `GestionDatosWidget` / pestañas | Productos, máquinas, trabajadores, lotes y fabricaciones: DI en ctor; primer arg desde `MainView` es `_app_controller` ignorado salvo compat. `PreprocesosWidget`: asignación a fabricaciones vía `FabricacionService` + `ProductController.show_fabricacion_preprocesos`, sin guardar `AppController`. |

**Resumen:** B5 **finalizada**; tabla de exclusiones arriba («Estado de la tarea B5»). Nuevas pantallas: preferir DI (`DefineProductionFlowDialog`, reportes) como patrón de referencia.

## Governanza anti–crecimiento (post–plan viabilidad 2026-04)

- **No añadir nuevos delegadores de una línea** en `AppModel` sin revisión explícita (issue o fila en `REGISTRO_EJECUCION_ITEMS.md`). La fachada no debe crecer «por comodidad».
- **Nuevas capacidades de dominio:** registrar el servicio en [`StartupController`](../../controllers/startup_controller.py) (`DIContainer`) e inyectar en controlador o widget; el consumo preferente es `container.resolve(T)` o el servicio ya expuesto en el controlador.
- **`AppController` permanece como hub** de arranque, sub-controladores y vista; no se exige eliminarlo; sí evitar que **nueva** lógica de negocio se acumule ahí o en `AppModel` en lugar de en servicios.

## Reglas

1. **Un controlador (o un eje) por iteración** — migrar, `pytest` focalizado, `mypy` en paquetes tocados.
2. **No eliminar método de `AppModel`** hasta que no quede ningún consumidor (`rg` en todo el repo).
3. **Las señales permanecen en `AppModel`** (o en un único hub de señales explícito si se extrae más adelante).
4. **Evitar megarefactor de tipos** en `AppController`: `Protocol` o tipos concretos solo donde se toque el archivo.

## Épica opcional (no implementada): hub de señales Qt fuera de `AppModel`

Solo si se **reabre** la arquitectura con criterios de aceptación propios:

1. Crear un `QObject` dedicado (p. ej. `ApplicationSignalBridge`) con los `pyqtSignal` hoy definidos en `AppModel`, instanciado en el arranque (`StartupController` o composición raíz).
2. Mover `_connect_service_signals` para que los servicios emitan hacia ese bridge; los controladores/UI enlazan `bridge.product_deleted_signal` (u homólogos) en lugar de `app.model.*`.
3. `AppModel` quedaría como composición de servicios + facades **sin** superficie de señales, o se deprecaría gradualmente.

**Criterios de aceptación sugeridos:** cero regresión en [`controllers/ui_signals_wiring.py`](../../controllers/ui_signals_wiring.py), tests que mockean señales actualizados, y documentación en esta skill. Priorizar frente a otras épicas (p. ej. producción Windows) solo si el equipo lo decide explícitamente.

## Checklist de verificación

### Cierre B5 (histórico, 2026-04)

- [x] Ítems REGISTRO 005–006: `pytest` focal + `mypy` en archivos tocados.
- [x] Coordinador: fila B5 marcada **Completada**; detalle B5 con exclusiones explícitas.

### Mantenimiento posterior (solo si se hace poda o nuevo wiring)

- [ ] Tras cada cambio: `pytest` relevante + `python3 -m mypy` sobre `app.py core controllers database features ui` (política CI).
- [ ] Antes de borrar un método de `AppModel`: `rg` en todo el repo sin consumidores.

## Poda reciente

- Eliminados de `AppModel` (sin consumidores externos): `get_latest_workers`, `get_latest_machines` — usar `WorkerService` / `MachineService` o el repositorio según capa.
- **Reportes (2026-04):** eliminados delegadores puros hacia `ReportService` (`search_reports_data`, `get_orders_for_product`, `get_order_details`, `get_order_units`, `get_product_time_stats`, `get_worker_time_stats`, `get_incidents_stats`, `get_evolution_stats`, `get_product_summary`, `get_product_reports_dashboard`). La UI y los tests usan `ReportService` o `model.report_service`. Permanecen en `AppModel` orquestaciones que usan reportes por dentro (`get_problematic_components_stats`, `get_dashboard_stats`).
- **Lotes (2026-04):** eliminado `get_lote_details` en `AppModel` (cero consumidores tras `calculate_times_widget`: fallback vía `model.system_integration.get_lote_details`). Detalle de fabricación en ese flujo vía `db.preproceso_repo.get_fabricacion_by_id` en lugar de `model.get_fabricacion_by_id`.

## Métodos que suelen permanecer en `AppModel` (post-migración reportes)

- **Señales** y `_connect_service_signals`.
- **Orquestación:** p. ej. `get_dashboard_stats` (agrega `machine_stats`, `worker_stats`, `component_stats`).
- **Delegación estable** a servicios/facades para el resto de dominios hasta nueva poda con `rg=0`.
- **Reportes:** no hay reexport tabular; usar `ReportService` (DI / `model.report_service`).
