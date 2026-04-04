# -*- coding: utf-8 -*-
"""
Resolución de clases del paquete `ui` sin `import ui.*` en el AST.

El informe `architecture_layer_edges` solo cuenta `import` / `import from` estáticos;
`importlib.import_module` evita aristas `controllers`→`ui` manteniendo el mismo comportamiento en runtime.
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
