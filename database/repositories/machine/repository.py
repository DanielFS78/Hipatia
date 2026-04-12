# -*- coding: utf-8 -*-
"""
Nombre del Módulo: machine.repository
Descripción: Acceso a datos de máquinas (CRUD, mantenimiento, preparación y estadísticas).
"""

from datetime import date
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from sqlalchemy.orm import Session

from ..base import BaseRepository
from .crud_manager import MachineCRUDManager
from .maintenance_manager import MachineMaintenanceManager
from .preparation_manager import MachinePreparationManager
from .stats_manager import MachineStatsManager
from core.dtos import (
    MachineDTO,
    MachineMaintenanceDTO,
    PreparationGroupDTO,
    PreparationStepDTO,
)


class MachineRepository(BaseRepository):
    """
    Repositorio para la gestión de máquinas.
    Implementa el patrón Fachada delegando en DAO Managers especializados.
    """

    def __init__(self, session_factory: Callable[[], Session]) -> None:
        super().__init__(session_factory)

        # Composición de gestores
        self.crud = MachineCRUDManager(session_factory)
        self.maintenance = MachineMaintenanceManager(session_factory)
        self.preparation = MachinePreparationManager(session_factory)
        self.stats = MachineStatsManager(session_factory)

        # Sincronización inicial para asegurar que comparten el mismo safe_execute (importante para tests)
        self._sync_managers()

    def _sync_managers(self) -> None:
        """Sincroniza la configuración del repositorio con sus gestores internos."""
        for manager in [self.crud, self.maintenance, self.preparation, self.stats]:
            manager.session_factory = self.session_factory

    def __setattr__(self, name: str, value: Any) -> None:
        """Propaga cambios en session_factory o safe_execute a los managers."""
        super().__setattr__(name, value)
        if name in ("session_factory", "safe_execute"):
            if hasattr(self, "crud"):
                managers = [self.crud, self.maintenance, self.preparation, self.stats]
                for m in managers:
                    setattr(m, name, value)

    # Delegación: MachineCRUDManager
    def get_all_machines(self, include_inactive: bool = False) -> List[MachineDTO]:
        return self.crud.get_all_machines(include_inactive=include_inactive)

    def get_latest_machines(self, limit: int = 10) -> List[MachineDTO]:
        return self.crud.get_latest_machines(limit=limit)

    def get_machines_by_process_type(self, tipo_proceso: str) -> List[MachineDTO]:
        return self.crud.get_machines_by_process_type(tipo_proceso)

    def get_distinct_machine_processes(self) -> List[str]:
        return self.crud.get_distinct_machine_processes()

    def add_machine(
        self,
        nombre: str,
        departamento: str,
        tipo_proceso: str,
        activa: bool = True,
        machine_id: Optional[int] = None,
    ) -> Union[bool, str]:
        return self.crud.add_machine(
            nombre, departamento, tipo_proceso, activa=activa, machine_id=machine_id
        )

    def update_machine(
        self,
        machine_id: int,
        nombre: str,
        departamento: str,
        tipo_proceso: str,
        activa: bool,
    ) -> bool:
        return self.crud.update_machine(
            machine_id, nombre, departamento, tipo_proceso, activa
        )

    def delete_machine(self, machine_id: int) -> bool:
        return self.crud.delete_machine(machine_id)

    # Delegación: MachineMaintenanceManager
    def add_machine_maintenance(
        self, machine_id: int, maintenance_date: date, notes: str
    ) -> bool:
        return self.maintenance.add_machine_maintenance(
            machine_id, maintenance_date, notes
        )

    def get_machine_maintenance_history(
        self, machine_id: int
    ) -> List[MachineMaintenanceDTO]:
        return self.maintenance.get_machine_maintenance_history(machine_id)

    def get_machine_history(self, machine_id: int) -> Dict[str, Any]:
        """
        Wrapper de compatibilidad para `DatabaseManager.get_machine_history()`.

        Históricamente este método devolvía un diccionario con el historial de la máquina.
        En la implementación actual, el historial se obtiene desde el manager de mantenimiento.
        """
        return {"maintenance": self.get_machine_maintenance_history(machine_id)}

    # Delegación: MachinePreparationManager
    def add_prep_group(
        self,
        machine_id: int,
        name: str,
        description: str,
        producto_codigo: Optional[str] = None,
    ) -> Union[int, str, None]:
        return self.preparation.add_prep_group(
            machine_id, name, description, producto_codigo=producto_codigo
        )

    def get_groups_for_machine(self, machine_id: int) -> List[PreparationGroupDTO]:
        return self.preparation.get_groups_for_machine(machine_id)

    def get_prep_info_for_product(self, producto_codigo: str) -> Tuple[Optional[int], Optional[int]]:
        return self.preparation.get_prep_info_for_product(producto_codigo)

    def get_group_details(self, group_id: int) -> Optional[PreparationGroupDTO]:
        return self.preparation.get_group_details(group_id)

    def update_prep_group(
        self,
        group_id: int,
        name: str,
        description: str,
        producto_codigo: Optional[str] = None,
    ) -> bool:
        return self.preparation.update_prep_group(
            group_id, name, description, producto_codigo=producto_codigo
        )

    def delete_prep_group(self, group_id: int) -> bool:
        return self.preparation.delete_prep_group(group_id)

    def add_prep_step(
        self,
        group_id: int,
        name: str,
        time: float,
        description: str,
        is_daily: bool,
    ) -> Optional[int]:
        return self.preparation.add_prep_step(
            group_id, name, time, description, is_daily
        )

    def update_prep_step(self, step_id: int, data: Dict[str, Any]) -> bool:
        return self.preparation.update_prep_step(step_id, data)

    def get_steps_for_group(self, group_id: int) -> List[PreparationStepDTO]:
        return self.preparation.get_steps_for_group(group_id)

    def delete_prep_step(self, step_id: int) -> bool:
        return self.preparation.delete_prep_step(step_id)

    def get_prep_step_details(self, step_id: int) -> Optional[PreparationStepDTO]:
        return self.preparation.get_prep_step_details(step_id)

    def get_prep_step_details_by_ids(self, step_ids: List[int]) -> Dict[int, PreparationStepDTO]:
        return self.preparation.get_prep_step_details_by_ids(step_ids)

    # Delegación: MachineStatsManager
    def get_machine_usage_stats(self) -> List[Tuple[str, float]]:
        return self.stats.get_machine_usage_stats()
