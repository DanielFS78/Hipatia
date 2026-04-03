# EN: database/repositories/__init__.py

"""
Este archivo hace que el directorio 'repositories' sea un paquete de Python
y expone las clases de repositorio para facilitar su importación.
"""

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
from .reports import ReportsRepository
# Opcional: Define qué se importa con 'from .repositories import *'
__all__ = [
    'BaseRepository',
    'ProductRepository',
    'WorkerRepository',
    'MachineRepository',
    'PilaRepository',
    'PreprocesoRepository',
    'ConfigurationRepository',
    'MaterialRepository',
    'IterationRepository',
    'TrackingRepository',
    'ReportsRepository'
]