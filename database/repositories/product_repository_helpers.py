# -*- coding: utf-8 -*-
"""
Nombre del Módulo: product_repository_helpers
Descripción: Mapeo de modelos ORM de producto a DTOs y normalización de identificadores de máquina.

Funciones puras usadas por ``ProductRepository`` para no duplicar conversiones en cada consulta.
"""

from __future__ import annotations

from typing import Any

from core.dtos import MaterialDTO, ProductDTO, ProcesoMecanicoDTO, SubfabricacionDTO


def to_product_dto(producto: Any) -> ProductDTO:
    """Convierte el modelo `Producto` a `ProductDTO`."""
    return ProductDTO(
        codigo=str(producto.codigo),
        descripcion=producto.descripcion or "",
        departamento=producto.departamento or "",
        tipo_trabajador=producto.tipo_trabajador or 0,
        donde=producto.donde or "",
        tiene_subfabricaciones=producto.tiene_subfabricaciones or False,
        tiempo_optimo=float(producto.tiempo_optimo or 0.0),
    )


def to_subfabricacion_dto(sub: Any) -> SubfabricacionDTO:
    """Convierte el modelo `Subfabricacion` a `SubfabricacionDTO`."""
    return SubfabricacionDTO(
        id=int(sub.id or 0),
        producto_codigo=str(sub.producto_codigo),
        descripcion=sub.descripcion or "",
        tiempo=float(sub.tiempo or 0.0),
        tipo_trabajador=sub.tipo_trabajador or 0,
        maquina_id=sub.maquina_id,
    )


def to_proceso_mecanico_dto(proceso: Any) -> ProcesoMecanicoDTO:
    """Convierte el modelo `ProcesoMecanico` a `ProcesoMecanicoDTO`."""
    return ProcesoMecanicoDTO(
        id=int(proceso.id or 0),
        producto_codigo=str(proceso.producto_codigo),
        nombre=proceso.nombre or "",
        descripcion=proceso.descripcion or "",
        tiempo=float(proceso.tiempo or 0.0),
        tipo_trabajador=proceso.tipo_trabajador or 0,
    )


def to_material_dto(material: Any) -> MaterialDTO:
    """Convierte el modelo `Material` a `MaterialDTO`."""
    return MaterialDTO(
        id=int(material.id or 0),
        codigo_componente=str(material.codigo_componente or ""),
        descripcion_componente=str(material.descripcion_componente or ""),
    )


def normalize_machine_id(value: Any) -> int | None:
    """Normaliza `maquina_id` a `int | None`."""
    if value in [None, ""]:
        return None
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return None

