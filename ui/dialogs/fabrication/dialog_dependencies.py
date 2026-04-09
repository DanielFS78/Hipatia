"""
Resolución centralizada de servicios para diálogos de fabricación.

Prioridad fija (testeable vía ``resolve_fabricacion_service`` / ``resolve_pila_service``):

- **FabricacionService**: DI registrado → ``product_controller.fabricacion_service`` → ``model.fabricacion_service``.
- **PilaService**: DI registrado → ``pila_controller.pila_service`` → ``model.pila_service``.

La bitácora y ``FlowActionHandler`` reutilizan ``resolve_pila_service``; si sigue siendo ``None``,
la UI puede usar ``model.planning_facade`` (no métodos de bitácora en ``AppModel``).
"""

from __future__ import annotations

from typing import Any

from core.di_container import DIContainer
from core.services.fabricacion_service import FabricacionService
from core.services.pila_service import PilaService


def resolve_fabricacion_service(controller: Any, container: DIContainer) -> Any | None:
    """Resuelve `FabricacionService` para UI sin duplicar reglas en cada diálogo."""
    if container.is_registered(FabricacionService):
        return container.resolve(FabricacionService)
    pc = getattr(controller, "product_controller", None)
    fs = getattr(pc, "fabricacion_service", None) if pc is not None else None
    if fs is not None:
        return fs
    mod = getattr(controller, "model", None)
    fs = getattr(mod, "fabricacion_service", None) if mod is not None else None
    if fs is not None:
        return fs
    return None


def resolve_pila_service(controller: Any, container: DIContainer) -> Any | None:
    """Resuelve `PilaService` para UI (bitácora, flujo de producción, etc.)."""
    if container.is_registered(PilaService):
        return container.resolve(PilaService)
    pila_ctrl = getattr(controller, "pila_controller", None)
    ps = getattr(pila_ctrl, "pila_service", None) if pila_ctrl is not None else None
    if ps is not None:
        return ps
    mod = getattr(controller, "model", None)
    ps = getattr(mod, "pila_service", None) if mod is not None else None
    if ps is not None:
        return ps
    return None
