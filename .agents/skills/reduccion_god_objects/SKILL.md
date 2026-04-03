---
name: Reducción de God Objects (AppModel Facade)
description: Plan para reducir la centralización excesiva en AppModel. Los controladores deben resolver servicios directamente vía DIContainer (registrados en StartupController) y constructores explícitos en lugar de depender de la fachada para cada operación.
---

# Reducción de God Objects — Proyecto Hipatia

## Problema

`AppModel` (`core/app_model.py`) actúa como fachada con **~110 métodos** de delegación a servicios, facades y `DatabaseManager`. Cada método suele ser una línea que reenvía a `*_service`, `product_facade`, `planning_facade` o `system_integration`. Eso diluye el SRP: nuevos casos de uso empujan a crecer la fachada sin aportar lógica.

**Nota (2026-04):** La fase de mixins en AppModel está cerrada; el modelo es una clase única. La reducción pasa por **inyección directa** y **poda de delegadores huérfanos** (solo tras `rg` con cero consumidores).

## Solución

1. **Registrar servicios y facades en `DIContainer`** desde `StartupController._init_services` (`ProductService`, `WorkerService`, `PilaService`, `MachineService`, `PreparationService`, `FabricacionService`, `ReportService`, `TrackingAssignmentService`, `ProductFacade`, `PlanningFacade`, `SystemIntegrationService`, etc.).
2. **Constructores explícitos** en controladores que antes recibían solo `app` y leían `app.model.*`.
3. **`AppController`**: mantener API de compatibilidad donde la UI pasa el hub (`handle_save_flow_only`, `search_fabricaciones`, …); el refresco global de productos en `on_data_changed` usa `product_controller.product_service` o, en arranque parcial, `model.product_service` (no `model.search_products`).
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
- Delegación que siga siendo el contrato estable para widgets que aún reciben `app_model` (hasta migrarlos).

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

## Reglas

1. **Un controlador (o un eje) por iteración** — migrar, `pytest` focalizado, `mypy` en paquetes tocados.
2. **No eliminar método de `AppModel`** hasta que no quede ningún consumidor (`rg` en todo el repo).
3. **Las señales permanecen en `AppModel`** (o en un único hub de señales explícito si se extrae más adelante).
4. **Evitar megarefactor de tipos** en `AppController`: `Protocol` o tipos concretos solo donde se toque el archivo.

## Checklist de verificación

- [ ] Tras cada cambio: `pytest` relevante + `python3 -m mypy` sobre `app.py core controllers database features ui` (política CI).
- [ ] Tendencia a la baja: `rg '\.model\.' controllers/` y usos de delegadores en UI.

## Poda reciente

- Eliminados de `AppModel` (sin consumidores externos): `get_latest_workers`, `get_latest_machines` — usar `WorkerService` / `MachineService` o el repositorio según capa.
