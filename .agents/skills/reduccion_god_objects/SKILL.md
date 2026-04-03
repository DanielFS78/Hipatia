---
name: Reducción de God Objects (AppModel Facade)
description: Plan para reducir la centralización excesiva en AppModel (148 métodos delegadores). Los controladores deben acceder a los servicios directamente vía DIContainer en lugar de pasar por la fachada para cada operación.
---

# Reducción de God Objects — Proyecto Hipatia

## Problema

`AppModel` actúa como una fachada con **148 métodos delegadores** repartidos en 6 mixins. Cada método es una línea tipo:

```python
def get_all_workers(self, include_inactive=False):
    return self.worker_service.get_all_workers(include_inactive)
```

Esto viola SRP: cualquier nuevo servicio obliga a añadir N delegadores aquí.

## Solución

**Los controladores deben resolver servicios directamente del `DIContainer`** en lugar de pasar por `AppModel` para cada operación.

### Ejemplo de Migración

```python
# ❌ ANTES: Controller → AppModel → Service
class MachineController:
    def __init__(self, app):
        self.model = app.model  # Pasa por AppModel
    
    def get_machines(self):
        return self.model.get_all_machines()  # AppModel delega a MachineService

# ✅ DESPUÉS: Controller → Service (directo)
class MachineController:
    def __init__(self, machine_service: MachineService):
        self.machine_service = machine_service  # Inyección directa
    
    def get_machines(self):
        return self.machine_service.get_all_machines()  # Directo, sin fachada
```

## Fases de Reducción

### Fase 1: Identificar métodos que son pura delegación

Ejecutar:
```bash
grep -n "return self\.\w*_service\." core/app_model.py core/app_model_*_mixin.py
```

Estos son los candidatos inmediatos para eliminar de AppModel.

### Fase 2: Migrar controladores uno a uno

Para cada controlador que usa `self.app.model.get_X()`:
1. Cambiar constructor para recibir el servicio directamente.
2. Actualizar `startup_controller.py` para pasar el servicio en la factory del DI.
3. Eliminar el método delegador de AppModel **solo cuando ningún consumidor lo use**.

### Fase 3: Reducir AppModel a su mínimo

AppModel debe conservar solo:
- Las señales de cambio (`product_added_signal`, `workers_changed_signal`, etc.)
- El puente de señales entre servicios (`_connect_service_signals`)
- Métodos que **realmente orquestan** varios servicios (como `get_dashboard_stats`)

## Controladores a Migrar (por prioridad)

| Controlador | Servicios que consume vía AppModel | Acción |
|:--|:--|:--|
| `MachineController` | `machine_service` | Ya recibe `MachineService` directamente ✅ |
| `WorkerController` | `worker_service` via `app.model` | Inyectar `WorkerService` directamente |
| `ProductController` | `product_service` via `app.model` | Inyectar `ProductService` directamente |
| `ReportController` | `worker_service`, `product_service`, `pila_service` | Ya recibe servicios directamente ✅ |
| `HistorialController` | `pila_service`, `worker_service` | Ya recibe servicios directamente ✅ |
| `PilaController` | `pila_service` via `app.model` | Inyectar `PilaService` directamente |
| `SimulationController` | Múltiples via `app.model` | Inyectar servicios directamente |
| `CalculationController` | Múltiples via `app` | Inyectar servicios directamente |

## Reglas

1. **Un controlador a la vez.** Migrar, ejecutar tests, pasar al siguiente.
2. **No eliminar el método de AppModel** hasta que CERO consumidores lo usen (buscar con `grep`).
3. **Las señales se quedan en AppModel** — son el mecanismo de notificación cross-cutting.
4. **Verificación:** `pytest tests/ -x -q` tras cada controlador migrado.

## Estado

- [x] MachineController — ya recibe MachineService directamente
- [x] ReportController — ya recibe servicios directamente
- [x] HistorialController — ya recibe servicios directamente
- [ ] WorkerController — pendiente
- [ ] ProductController — pendiente
- [ ] PilaController — pendiente
- [ ] SimulationController — pendiente
- [ ] CalculationController — pendiente
- [ ] Limpieza final de AppModel (eliminar métodos huérfanos)
