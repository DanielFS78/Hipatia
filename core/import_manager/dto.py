# -*- coding: utf-8 -*-
"""
Nombre del Módulo: import_manager.dto
Descripción: Estructuras de datos para un listado de materiales (BOM) leído desde Excel A3RP.

Cada nodo puede marcarse en pantalla para importar o no, y recibir un rol (producto final,
subfabricación, proceso mecánico o componente) antes de persistir en base de datos.
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
    """
    Nodo del árbol BOM leído desde A3RP y enriquecido en la supervisión de importación.

    Attributes:
        nivel: Profundidad en la lista de materiales.
        codigo_componente: Identificador de fila (código de pieza o operación según contexto).
        capitulo: Metadato de capítulo del listado, si existe.
        denominacion: Texto descriptivo mostrado al usuario.
        es_subfabricacion: Hint del adaptador Excel (``Compuesto``); la verdad operativa es ``import_role``.
        cantidad: Cantidad de la línea.
        hijos: Subárbol recursivo.
        import_selected: Si True, el usuario marcó la fila para persistir.
        import_role: Rol asignado en el diálogo (obligatorio si está marcada).
    """

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
