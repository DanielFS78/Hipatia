# EN: database/repositories/__init__.py

"""
Este archivo hace que el directorio 'repositories' sea un paquete de Python
y expone las clases de repositorio para facilitar su importación.
"""

from .base import BaseRepository
from .product_repository import ProductRepository
from .configuration_repository import ConfigurationRepository
from .worker_repository import WorkerRepository
from .machine_repository import MachineRepository
from .pila_repository import PilaRepository
from .material_repository import MaterialRepository
from .iteration_repository import IterationRepository
from .preproceso_repository import PreprocesoRepository
from .lote_repository import LoteRepository
from .tracking_repository import TrackingRepository
from .label_counter_repository import LabelCounterRepository
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
    'TrackingRepository'
]