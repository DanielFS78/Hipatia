# -*- coding: utf-8 -*-
"""
Nombre del Módulo: core.utils.helpers

Descripción: Funciones puras de apoyo (sin estado de proceso): ``resource_path``. Integración típica con: ``sys``, ``os``.
"""

import sys
import os

def resource_path(relative_path: str) -> str:
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)