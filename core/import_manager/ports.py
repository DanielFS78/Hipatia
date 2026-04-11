# -*- coding: utf-8 -*-
"""
Nombre del Módulo: import_manager.ports
Descripción: Contratos mínimos para lectores de BOM (interfaz común entre adaptadores y tests).
"""

from typing import Protocol
from core.import_manager.dto import BOMNodeDTO


class IBOMImporter(Protocol):
    """Lector de fichero que devuelve la raíz del árbol de materiales como ``BOMNodeDTO``."""

    def parse_file(self, file_path: str) -> BOMNodeDTO:
        """Lee la ruta indicada y devuelve el nodo raíz del BOM."""
        ...
