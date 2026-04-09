# -*- coding: utf-8 -*-
"""
Nombre del Módulo: subfabricacion_rows
Descripcion: Normaliza filas de subfabricación (dict legado u objetos con atributos) a
             ``SubfabricacionDTO``. Vive en ``core/`` para que la UI no use ``.get``/claves
             sueltas en la frontera Fase 12C (analizador ``ui_dto_boundary``).
"""

from __future__ import annotations

from typing import Any, Sequence

from core.dtos import SubfabricacionDTO


def coerce_subfabricaciones_rows(rows: Sequence[Any] | None) -> list[SubfabricacionDTO]:
    """
    El widget de productos puede guardar subfabricaciones como dict; el diálogo opera con DTOs.

    Args:
        rows: Filas heterogéneas (DTO, dict compatible u objetos con los mismos campos).

    Returns:
        Lista de ``SubfabricacionDTO`` listos para pintar o persistir.
    """
    if not rows:
        return []
    out: list[SubfabricacionDTO] = []
    for row in rows:
        if isinstance(row, SubfabricacionDTO):
            out.append(row)
            continue
        if isinstance(row, dict):
            try:
                tiempo = float(row.get("tiempo") or 0)
            except (TypeError, ValueError):
                tiempo = 0.0
            try:
                tipo = int(row.get("tipo_trabajador") or 1)
            except (TypeError, ValueError):
                tipo = 1
            raw_id = row.get("id")
            try:
                sid = int(raw_id) if raw_id is not None else 0
            except (TypeError, ValueError):
                sid = 0
            mid_raw = row.get("maquina_id")
            if mid_raw is None or mid_raw == "":
                maquina_id: int | None = None
            else:
                try:
                    maquina_id = int(mid_raw)
                except (TypeError, ValueError):
                    maquina_id = None
            out.append(
                SubfabricacionDTO(
                    id=sid,
                    producto_codigo=str(row.get("producto_codigo") or ""),
                    descripcion=str(row.get("descripcion") or ""),
                    tiempo=tiempo,
                    tipo_trabajador=tipo,
                    maquina_id=maquina_id,
                )
            )
            continue
        out.append(
            SubfabricacionDTO(
                id=int(getattr(row, "id", 0) or 0),
                producto_codigo=str(getattr(row, "producto_codigo", "") or ""),
                descripcion=str(getattr(row, "descripcion", "") or ""),
                tiempo=float(getattr(row, "tiempo", 0.0) or 0.0),
                tipo_trabajador=int(getattr(row, "tipo_trabajador", 1) or 1),
                maquina_id=getattr(row, "maquina_id", None),
            )
        )
    return out
