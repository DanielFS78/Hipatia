# -*- coding: utf-8 -*-
"""
Nombre del Módulo: worker.annotation_manager
Descripción: Datos de trabajadores, anotaciones y repositorio compuesto del subpaquete worker.
"""

from typing import List
from datetime import datetime
from sqlalchemy.orm import Session
from core.dtos import WorkerAnnotationDTO
from ..base import BaseRepository


class WorkerAnnotationManager(BaseRepository):
    """
    Gestor DAO para la gestión de anotaciones de trabajadores.
    """

    def get_worker_annotations(self, worker_id: int) -> List[WorkerAnnotationDTO]:
        """Obtiene todas las anotaciones para un trabajador específico."""
        def _operation(session: Session) -> List[WorkerAnnotationDTO]:
            from ...models import TrabajadorPilaAnotacion

            anotaciones = session.query(TrabajadorPilaAnotacion).filter_by(
                worker_id=worker_id
            ).order_by(
                TrabajadorPilaAnotacion.fecha.desc()
            ).all()

            return [
                WorkerAnnotationDTO(
                    pila_id=int(a.pila_id or 0),
                    fecha=a.fecha or datetime.min,
                    anotacion=a.anotacion or ""
                ) for a in anotaciones
            ]

        return self.safe_execute(_operation) or []

    def add_worker_annotation(self, worker_id: int, pila_id: int, annotation: str) -> bool:
        """Añade una nueva anotación para un trabajador asociada a una pila específica."""
        def _operation(session: Session) -> bool:
            from ...models import TrabajadorPilaAnotacion

            nueva_anotacion = TrabajadorPilaAnotacion(
                worker_id=worker_id,
                pila_id=pila_id,
                anotacion=annotation
            )
            session.add(nueva_anotacion)
            return True

        return self.safe_execute(_operation) or False
