# -*- coding: utf-8 -*-
"""
Nombre del Módulo: iteration_repository_helpers
Descripción: Funciones puras de mapeo entre filas ORM de iteración y ``ProductIterationDTO``.

Mantiene ``IterationRepository`` enfocado en SQL; sin dependencia de sesión aquí.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from core.dtos import ProductIterationDTO, ProductIterationMaterialDTO


def material_to_dto(material: Any) -> ProductIterationMaterialDTO:
    """Convierte un material ORM a DTO."""
    return ProductIterationMaterialDTO(
        id=material.id or 0,
        codigo=material.codigo_componente or "",
        descripcion=material.descripcion_componente or "",
    )


def iteration_to_dto(iteracion: Any, include_materiales: bool = True, include_product_desc: bool = False) -> ProductIterationDTO:
    """Convierte una iteración ORM a DTO."""
    materiales = [material_to_dto(m) for m in iteracion.materiales] if include_materiales else []
    product_desc = ((iteracion.producto.descripcion if iteracion.producto else "") or "") if include_product_desc else ""
    return ProductIterationDTO(
        id=iteracion.id or 0,
        producto_codigo=iteracion.producto_codigo or "",
        descripcion=iteracion.descripcion_cambio or "",
        fecha_creacion=iteracion.fecha_creacion or datetime.min,
        nombre_responsable=iteracion.nombre_responsable or "",
        tipo_fallo=iteracion.tipo_fallo or "",
        materiales=materiales,
        ruta_imagen=iteracion.ruta_imagen,
        ruta_plano=iteracion.ruta_plano,
        producto_descripcion=product_desc,
    )
