# -*- coding: utf-8 -*-
"""
Nombre del Módulo: tracking_assignment_service
Descripción: Enlaza y desenlaza trabajadores con órdenes de fabricación en base de datos.

Escribe en la tabla ``trabajador_fabricacion_link`` (fecha de asignación en UTC y
estado, por ejemplo ``activo`` o ``cancelado``) para que la vista de operario y los
informes de trazabilidad reflejen siempre las asignaciones vigentes.
"""

from datetime import datetime, timezone
from typing import List, Any

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from database.database_manager import DatabaseManager
from database.models import Trabajador, Fabricacion, trabajador_fabricacion_link
from core.tracking_dtos import FabricacionAsignadaDTO

class TrackingAssignmentService:
    """Operaciones de dominio sobre el vínculo trabajador–fabricación (asignar, actualizar estado, desasignar)."""
    
    def __init__(self, db_manager: DatabaseManager):
        self._db = db_manager

    def get_fabricaciones_por_trabajador(self, trabajador_id: int) -> List[FabricacionAsignadaDTO]:
        """
        Recupera las fabricaciones asignadas a un trabajador desde el repositorio.

        Args:
            trabajador_id: ID del trabajador.

        Returns:
            Lista de fabricaciones asignadas.
        """
        return self._db.tracking_repo.get_fabricaciones_por_trabajador(trabajador_id)

    def actualizar_estado_asignacion(self, trabajador_id: int, fabricacion_id: int, nuevo_estado: str) -> bool:
        def _operation(session: Session, **_kwargs: Any) -> bool:
            update_stmt = trabajador_fabricacion_link.update().where(
                and_(
                    trabajador_fabricacion_link.c.trabajador_id == trabajador_id,
                    trabajador_fabricacion_link.c.fabricacion_id == fabricacion_id
                )
            ).values(estado=nuevo_estado)
            result: Any = session.execute(update_stmt)
            if result.rowcount > 0:
                self._db.tracking_repo.logger.info(f"Estado asignación actualizado: T{trabajador_id}, F{fabricacion_id} -> {nuevo_estado}")
                return True
            return False
        return self._db.tracking_repo.safe_execute(_operation, default_value=False) or False

    def asignar_trabajador_a_fabricacion(self, trabajador_id: int, fabricacion_id: int) -> bool:
        """
        Enlaza un trabajador con una fabricación si ambos existen y el enlace no existe aún.

        Inserta una fila en ``trabajador_fabricacion_link`` con ``fecha_asignacion``
        en UTC y ``estado`` ``activo``. Si el par ya estaba enlazado, devuelve True
        sin duplicar.
        """
        def _operation(session: Session, **_kwargs: Any) -> bool:
            trabajador = session.query(Trabajador).filter_by(id=trabajador_id).first()
            fabricacion = session.query(Fabricacion).filter_by(id=fabricacion_id).first()
            if not trabajador or not fabricacion:
                return False
            existing = session.execute(
                select(trabajador_fabricacion_link.c.trabajador_id).where(
                    and_(
                        trabajador_fabricacion_link.c.trabajador_id == trabajador_id,
                        trabajador_fabricacion_link.c.fabricacion_id == fabricacion_id,
                    )
                )
            ).first()
            if existing:
                return True
            session.execute(
                trabajador_fabricacion_link.insert().values(
                    trabajador_id=trabajador_id,
                    fabricacion_id=fabricacion_id,
                    fecha_asignacion=datetime.now(timezone.utc),
                    estado="activo",
                )
            )
            return True

        return self._db.tracking_repo.safe_execute(_operation, default_value=False, commit=True) or False

    def desasignar_trabajador_de_fabricacion(self, trabajador_id: int, fabricacion_id: int) -> bool:
        """
        Elimina la fila de ``trabajador_fabricacion_link`` para el par dado.

        Returns:
            True si se borró al menos una fila; False si no existía el enlace.
        """
        def _operation(session: Session, **_kwargs: Any) -> bool:
            result = session.execute(
                trabajador_fabricacion_link.delete().where(
                    and_(
                        trabajador_fabricacion_link.c.trabajador_id == trabajador_id,
                        trabajador_fabricacion_link.c.fabricacion_id == fabricacion_id,
                    )
                )
            )
            rc = getattr(result, "rowcount", None)
            return bool(rc is not None and rc > 0)

        return self._db.tracking_repo.safe_execute(_operation, default_value=False, commit=True) or False
