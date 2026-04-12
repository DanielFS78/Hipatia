# -*- coding: utf-8 -*-
"""
Nombre del Módulo: repositories
Descripción: Paquete de acceso a datos: repositorios por dominio (producto, máquina, pila,
             trabajador, informes, tracking, etc.) y exportaciones para ``DatabaseManager``.

Las clases públicas se listan en ``__all__`` para imports explícitos desde ``database.repositories``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .base import BaseRepository
from .product_repository import ProductRepository
from .configuration_repository import ConfigurationRepository
from .worker import WorkerRepository
from .machine import MachineRepository
from .pila import PilaRepository
from .material_repository import MaterialRepository
from .iteration_repository import IterationRepository
from .preproceso import PreprocesoRepository
from .lote_repository import LoteRepository
from .tracking_repository import TrackingRepository
from .label_counter_repository import LabelCounterRepository

if TYPE_CHECKING:
    from .reports import ReportsRepository

__all__ = [
    "BaseRepository",
    "ProductRepository",
    "WorkerRepository",
    "MachineRepository",
    "PilaRepository",
    "PreprocesoRepository",
    "ConfigurationRepository",
    "MaterialRepository",
    "IterationRepository",
    "LoteRepository",
    "TrackingRepository",
    "LabelCounterRepository",
    "ReportsRepository",
]


def __getattr__(name: str) -> Any:
    """Carga perezosa de ``ReportsRepository`` para no exigir el subpaquete ``reports`` en imports parciales."""
    if name == "ReportsRepository":
        from .reports import ReportsRepository as _ReportsRepository

        return _ReportsRepository
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
