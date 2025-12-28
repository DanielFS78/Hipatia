# database/repositories/label_counter_repository.py
"""
Repositorio para gestionar contadores de etiquetas usando SQLAlchemy.
Migrado de SQLite local a base de datos central.
"""

from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from database.models import FabricacionContador
from database.repositories.base import BaseRepository
from core.dtos import LabelRangeDTO


class LabelCounterRepository(BaseRepository):
    """
    Gestiona la numeración de unidades de fabricación usando la BD principal.
    Reemplaza la implementación anterior basada en 'etiquetas.db'.
    """

    def get_next_unit_range(self, fabricacion_id: int, cantidad: int) -> Optional[LabelRangeDTO]:
        """
        Obtiene y reserva un rango de números de unidad únicos para una fabricación.
        Operación atómica.

        Args:
            fabricacion_id (int): El ID de la fabricación.
            cantidad (int): Cuántos números se necesitan.

        Returns:
            LabelRangeDTO con el rango asignado (start, end, count) o None si hay error.
        """
        return self.safe_execute(self._get_next_unit_range_logic, fabricacion_id, cantidad)

    def _get_next_unit_range_logic(self, session: Session, fabricacion_id: int, cantidad: int) -> LabelRangeDTO:
        """
        Lógica interna transaccional para obtener el rango.
        """
        # 1. Buscar el contador existente (bloqueando fila si fuera necesario en soporte DB real,
        # pero con SQLite/ORM simple confiamos en la sesión y commit atómico)
        # Para mayor robustez en concurrencia real se usaría with_for_update,
        # pero SQLite tiene limitaciones con eso. La transacción serializable ayuda.
        contador = session.query(FabricacionContador).filter_by(fabricacion_id=fabricacion_id).first()

        if not contador:
            # Crear si no existe
            contador = FabricacionContador(fabricacion_id=fabricacion_id, ultimo_numero_unidad=0)
            session.add(contador)
            # Flush para asegurar que esté en la sesión
            session.flush()
            ultimo_actual = 0
            self.logger.info(f"Creado nuevo contador para Fabricacion ID: {fabricacion_id}")
        else:
            ultimo_actual = contador.ultimo_numero_unidad

        # 2. Calcular nuevo rango
        numero_inicial = ultimo_actual + 1
        numero_final = ultimo_actual + cantidad

        # 3. Actualizar contador
        contador.ultimo_numero_unidad = numero_final
        
        # El commit se hace en safe_execute

        self.logger.info(f"Rango asignado para Fab ID {fabricacion_id}: {numero_inicial} a {numero_final}")

        return LabelRangeDTO(
            fabricacion_id=fabricacion_id,
            start=numero_inicial,
            end=numero_final,
            count=cantidad
        )

    def close(self):
        """
        Método de compatibilidad. No hace nada porque la sesión se maneja por request/operación.
        """
        pass