"""
Nombre del Módulo: import_manager.dto
Descripcion: DTOs para representar árboles BOM importados desde A3RP.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class BOMImportRole(str, Enum):
    """Clasificación explícita de cada fila marcada en la supervisión de importación A3RP."""

    FINAL_PRODUCT = "final"
    SUBFABRICATION = "subfab"
    MECHANICAL_PROCESS = "proceso"
    COMPONENT = "componente"


@dataclass
class BOMNodeDTO:
    nivel: int
    codigo_componente: str
    capitulo: str = ""
    denominacion: str = ""
    es_subfabricacion: bool = False  # True si era "Compuesto" en el Excel (hint del adaptador)
    cantidad: float = 1.0
    hijos: List["BOMNodeDTO"] = field(default_factory=list)
    # Supervisión en UI: si False, el nodo no se importa
    import_selected: bool = False
    import_role: Optional[BOMImportRole] = None
