# core/labels/__init__.py

"""
Nombre del Módulo: core.label_manager

Descripción: Concentra datos de configuración o catálogos estáticos: ``__all__``, consumidos por la UI y controladores. Integración típica con: ``pathlib``, ``base``, ``manager``.
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
