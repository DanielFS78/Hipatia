# database/repositories/machine/maintenance_manager.py
"""
Capa de datos (`maintenance_manager`): modelos, repositorios o acceso SQLAlchemy relacionado con este módulo.
"""

from typing import List
from datetime import date
from sqlalchemy.orm import Session
from ..base import BaseRepository
from ...models import MachineMaintenanc
from core.dtos import MachineMaintenanceDTO

class MachineMaintenanceManager(BaseRepository):
    """Gestor DAO para el historial de mantenimiento de máquinas."""

    def add_machine_maintenance(self, machine_id: int, maintenance_date: date, notes: str) -> bool:
        def _operation(session: Session) -> bool:
            session.add(MachineMaintenanc(machine_id=machine_id, maintenance_date=str(maintenance_date), notes=notes))
            return True
        return self.safe_execute(_operation) or False

    def get_machine_maintenance_history(self, machine_id: int) -> List[MachineMaintenanceDTO]:
        def _operation(session: Session) -> List[MachineMaintenanceDTO]:
            mantenimientos = session.query(MachineMaintenanc).filter_by(machine_id=machine_id).order_by(MachineMaintenanc.maintenance_date.desc()).all()
            return [MachineMaintenanceDTO(maintenance_date=date.fromisoformat(str(m.maintenance_date)) if m.maintenance_date else date.today(), 
                                         notes=m.notes or "") for m in mantenimientos]
        return self.safe_execute(_operation) or []
