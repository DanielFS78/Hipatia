# -*- coding: utf-8 -*-
"""
Nombre del Módulo: preparation_service
Descripción: Servicio de dominio especializado en la gestión de grupos y pasos de preparación de máquinas.
"""
from typing import Any, Optional, Tuple

from core.dtos import PreparationGroupDTO, PreparationStepDTO
from database.database_manager import DatabaseManager
from database.repositories.machine import MachineRepository

class PreparationService:
    """
    Grupos y pasos de preparación de máquinas (tiempos y secuencias usados antes de fabricar).
    """

    def __init__(self, db_manager: DatabaseManager):
        self._db = db_manager

    @property
    def machine_repo(self) -> MachineRepository:
        return self._db.machine_repo

    def get_groups_for_machine(self, machine_id: int) -> list[PreparationGroupDTO]:
        """Obtiene los grupos de preparación asociados a una máquina."""
        return self.machine_repo.get_groups_for_machine(machine_id)

    def get_prep_info_for_product(self, producto_codigo: str) -> Tuple[Optional[int], Optional[int]]:
        """IDs de grupo y máquina del primer grupo de preparación asociado al producto."""
        return self.machine_repo.get_prep_info_for_product(producto_codigo)

    def add_prep_group(self, machine_id: int, name: str, description: str, 
                       producto_codigo: str | None = None) -> int | str | None:
        """Añade un nuevo grupo de preparación a una máquina."""
        return self.machine_repo.add_prep_group(machine_id, name, description, producto_codigo)

    def update_prep_group(self, group_id: int, name: str, description: str, 
                          producto_codigo: str | None = None) -> bool:
        """Actualiza un grupo de preparación existente."""
        return self.machine_repo.update_prep_group(group_id, name, description, producto_codigo)

    def delete_prep_group(self, group_id: int) -> bool:
        """Elimina un grupo de preparación."""
        return self.machine_repo.delete_prep_group(group_id)

    def get_steps_for_group(self, group_id: int) -> list[PreparationStepDTO]:
        """Obtiene los pasos de preparación de un grupo."""
        return self.machine_repo.get_steps_for_group(group_id)

    def add_prep_step(self, group_id: int, name: str, time: float, 
                      description: str, is_daily: bool) -> int | None:
        """Añade un paso de preparación a un grupo."""
        return self.machine_repo.add_prep_step(group_id, name, time, description, is_daily)

    def update_prep_step(self, step_id: int, data: dict[str, Any]) -> bool:
        """Actualiza un paso de preparación existente."""
        return self.machine_repo.update_prep_step(step_id, data)

    def delete_prep_step(self, step_id: int) -> bool:
        """Elimina un paso de preparación."""
        return self.machine_repo.delete_prep_step(step_id)

    def get_prep_step_details(self, step_id: int) -> PreparationStepDTO | None:
        """Obtiene los detalles de un paso de preparación específico."""
        return self.machine_repo.get_prep_step_details(step_id)
    
    def get_group_details(self, group_id: int) -> PreparationGroupDTO | None:
        """Obtiene los detalles de un grupo de preparación."""
        return self.machine_repo.get_group_details(group_id)
    
    def get_prep_step_details_by_ids(self, step_ids: list[int]) -> dict[int, PreparationStepDTO]:
        """Obtiene detalles de múltiples pasos por sus IDs."""
        return self.machine_repo.get_prep_step_details_by_ids(step_ids)
