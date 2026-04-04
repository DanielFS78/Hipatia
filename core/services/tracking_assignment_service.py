# -*- coding: utf-8 -*-
"""
Lógica o utilidades del núcleo (`tracking_assignment_service`): tipos, servicios auxiliares o infraestructura compartida fuera de la capa de interfaz.
"""

from typing import List, Any
from sqlalchemy import and_
from sqlalchemy.orm import Session

from database.database_manager import DatabaseManager
from database.models import Trabajador, Fabricacion, trabajador_fabricacion_link, fabricacion_productos, Producto
from core.dtos import FabricacionProductoDTO
from core.tracking_dtos import FabricacionAsignadaDTO

class TrackingAssignmentService:
    """Servicio de dominio para gestionar asignaciones trabajador↔fabricación."""
    
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
        def _operation(session: Session, **_kwargs: Any) -> bool:
            trabajador = session.query(Trabajador).filter_by(id=trabajador_id).first()
            fabricacion = session.query(Fabricacion).filter_by(id=fabricacion_id).first()
            if not trabajador or not fabricacion:
                return False
            if fabricacion in trabajador.fabricaciones_asignadas:
                return True
            trabajador.fabricaciones_asignadas.append(fabricacion)
            return True

        return self._db.tracking_repo.safe_execute(_operation, default_value=False, commit=True) or False

    def desasignar_trabajador_de_fabricacion(self, trabajador_id: int, fabricacion_id: int) -> bool:
        def _operation(session: Session, **_kwargs: Any) -> bool:
            trabajador = session.query(Trabajador).filter_by(id=trabajador_id).first()
            fabricacion = session.query(Fabricacion).filter_by(id=fabricacion_id).first()
            if not trabajador or not fabricacion:
                return False
            if fabricacion in trabajador.fabricaciones_asignadas:
                trabajador.fabricaciones_asignadas.remove(fabricacion)
                return True
            return False

        return self._db.tracking_repo.safe_execute(_operation, default_value=False, commit=True) or False
