"""
Nombre del Módulo: import_manager.dto
Descripcion: DTOs para representar árboles BOM importados desde A3RP.
"""

from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class BOMNodeDTO:
    nivel: int
    codigo_componente: str
    capitulo: str = ""
    denominacion: str = ""
    es_subfabricacion: bool = False # True si era "Compuesto", False si "Artículo"
    cantidad: float = 1.0
    hijos: List['BOMNodeDTO'] = field(default_factory=list)
