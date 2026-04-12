# -*- coding: utf-8 -*-
"""
Nombre del Módulo: machine_service
Descripción: Servicio de dominio especializado en la gestión de máquinas, mantenimientos y procesos.
"""
import logging
from typing import Any

from PyQt6.QtCore import QObject, pyqtSignal

from core.dtos import MachineDTO
from database.database_manager import DatabaseManager
from database.repositories.machine import MachineRepository

class MachineService(QObject):
    """
    Catálogo y mantenimiento lógico de máquinas de planta (consultas y cambios vía repositorio).
    """

    machines_changed_signal = pyqtSignal()

    def __init__(self, db_manager: DatabaseManager):
        super().__init__()
        self._db = db_manager
        self.logger = logging.getLogger("MachineService")

    @property
    def machine_repo(self) -> MachineRepository:
        return self._db.machine_repo

    def get_all_machines(self, include_inactive: bool = False) -> list[MachineDTO]:
        """Obtiene todas las máquinas."""
        return self.machine_repo.get_all_machines(include_inactive)

    def get_latest_machines(self, limit: int = 10) -> list[MachineDTO]:
        """Obtiene las últimas máquinas añadidas."""
        return self.machine_repo.get_latest_machines(limit)
        
    def get_machines_by_process_type(self, tipo_proceso: str) -> list[MachineDTO]:
        """Obtiene máquinas filtradas por tipo de proceso."""
        return self.machine_repo.get_machines_by_process_type(tipo_proceso)

    def add_machine(self, nombre: str, departamento: str, tipo_proceso: str) -> bool | str:
        """Añade una nueva máquina."""
        result = self.machine_repo.add_machine(nombre, departamento, tipo_proceso)
        if result is True:
            self.machines_changed_signal.emit()
        return result

    def update_machine(self, machine_id: int, nombre: str, departamento: str, 
                       tipo_proceso: str, activa: bool) -> bool:
        """Actualiza la información de una máquina."""
        success = self.machine_repo.update_machine(machine_id, nombre, departamento, tipo_proceso, activa)
        if success:
            self.machines_changed_signal.emit()
        return success

    def delete_machine(self, machine_id: int) -> bool:
        """Elimina una máquina."""
        success = self.machine_repo.delete_machine(machine_id)
        if success:
            self.machines_changed_signal.emit()
        return success

    def get_machine_history(self, machine_id: int) -> dict[str, Any]:
        """Obtiene el historial de una máquina."""
        maintenance_history = self.machine_repo.get_machine_maintenance_history(machine_id)
        return {
            'num_fabrications': 0,
            'total_hours': 0.0,
            'hours_since_maintenance': 0.0,
            'maintenance_history': maintenance_history
        }
        
    def add_machine_maintenance(self, machine_id: int, maintenance_date: Any, notes: str) -> bool:
        """Añade un registro de mantenimiento a una máquina."""
        success = self.machine_repo.add_machine_maintenance(machine_id, maintenance_date, notes)
        if success:
            self.machines_changed_signal.emit()
        return success

    def get_distinct_machine_processes(self) -> list[str]:
        """Obtiene la lista de procesos únicos definidos en las máquinas."""
        return self.machine_repo.get_distinct_machine_processes()

    def get_machine_usage_stats(self) -> list[tuple[str, float]]:
        """Obtiene las estadísticas de uso de las máquinas."""
        return self.machine_repo.get_machine_usage_stats()
