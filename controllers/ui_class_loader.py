# -*- coding: utf-8 -*-
"""
Nombre del Módulo: controllers.ui_class_loader

Descripción: Funciones puras de apoyo (sin estado de proceso): ``ui_class``. Integración típica con: ``__future__``, ``importlib``.
"""

from __future__ import annotations

import importlib
from typing import Any


def ui_class(module_path: str, attribute: str) -> Any:
    """Devuelve un atributo (típicamente una clase QWidget/QDialog) de un submódulo `ui`.

    Sin caché inter-test: los tests pueden parchear ``ui.dialogs.*`` o el nombre reexportado
    en el módulo controlador antes de cada llamada.
    """
    mod = importlib.import_module(module_path)
    return getattr(mod, attribute)
