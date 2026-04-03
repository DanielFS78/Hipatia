# core/labels/__init__.py

"""
Lógica o utilidades del núcleo (`__init__`): tipos, servicios auxiliares o infraestructura compartida fuera de la capa de interfaz.
"""

from pathlib import Path
from typing import Any


from .base import LABEL_FORMATS

from . import printer
from .manager import LabelManager, quick_print_labels

__all__ = [
    'LabelManager',
    'quick_print_labels',
    'LABEL_FORMATS',
    'Path',
    'printer'
]
