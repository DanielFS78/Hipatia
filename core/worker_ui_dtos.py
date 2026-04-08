# -*- coding: utf-8 -*-
"""
Nombre del Modulo: worker_ui_dtos
Descripcion: DTOs tipados para la vista trabajador (lista de fabricaciones asignadas).

Origen típico: ``WorkerDbSync.get_assigned_fabricaciones``. La UI serializa filas con
``to_signal_dict()`` cuando el receptor aún espera un mapping plano.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Mapping


@dataclass(frozen=True)
class WorkerTaskListRowDTO:
    """Fila plana para la lista de tareas/fabricaciones en WorkerMainWindow."""

    id: Any
    codigo: str
    descripcion: str
    producto_codigo: str
    producto_descripcion: str
    cantidad: int
    fecha_asignacion: Any = None
    estado: Any = None
    productos: Any = None

    def to_signal_dict(self) -> Dict[str, Any]:
        """Payload para señales y controladores que aún esperan dict plano."""
        return {
            "id": self.id,
            "codigo": self.codigo,
            "descripcion": self.descripcion,
            "producto_codigo": self.producto_codigo,
            "producto_descripcion": self.producto_descripcion,
            "cantidad": self.cantidad,
            "fecha_asignacion": self.fecha_asignacion,
            "estado": self.estado,
            "productos": self.productos,
        }

    @classmethod
    def from_flat_mapping(cls, m: Mapping[str, Any]) -> WorkerTaskListRowDTO:
        """Construye desde el dict histórico de WorkerDbSync (tests y migración)."""
        pc = m.get("producto_codigo")
        pd_ = m.get("producto_descripcion")
        return cls(
            id=m.get("id"),
            codigo=str(m.get("codigo") or ""),
            descripcion=str(m.get("descripcion") or ""),
            producto_codigo=str(pc or ""),
            producto_descripcion=str(pd_ or ""),
            cantidad=int(m.get("cantidad") or 0),
            fecha_asignacion=m.get("fecha_asignacion"),
            estado=m.get("estado"),
            productos=m.get("productos"),
        )
