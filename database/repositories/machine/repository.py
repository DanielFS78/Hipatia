"""
Capa de datos (`repository`): modelos, repositorios o acceso SQLAlchemy relacionado con este módulo.
"""

from ..base import BaseRepository
from typing import List, Optional, Union, Tuple, Dict, Any
from sqlalchemy.orm import Session
from .crud_manager import MachineCRUDManager
from .maintenance_manager import MachineMaintenanceManager
from .preparation_manager import MachinePreparationManager
from .stats_manager import MachineStatsManager
from core.dtos import MachineDTO, MachineMaintenanceDTO, PreparationGroupDTO, PreparationStepDTO

class MachineRepository(BaseRepository):
    """
    Repositorio para la gestión de máquinas.
    Implementa el patrón Fachada delegando en DAO Managers especializados.
    """

    def __init__(self, session_factory) -> None:
        super().__init__(session_factory)
        
        # Composición de gestores
        self.crud = MachineCRUDManager(session_factory)
        self.maintenance = MachineMaintenanceManager(session_factory)
        self.preparation = MachinePreparationManager(session_factory)
        self.stats = MachineStatsManager(session_factory)
        
        # Sincronización inicial para asegurar que comparten el mismo safe_execute (importante para tests)
        self._sync_managers()

    def _sync_managers(self):
        """Sincroniza la configuración del repositorio con sus gestores internos."""
        for manager in [self.crud, self.maintenance, self.preparation, self.stats]:
            manager.session_factory = self.session_factory
            # Nota: No podemos asignar el método directamente si queremos que sea dinámico,
            # pero en los tests se suele asignar un mock al atributo de la instancia.
            # Al delegar explícitamente en los métodos del repositorio, 
            # ya estamos usando el 'safe_execute' del repositorio si el manager lo llamara a través de self.
            # Pero el manager usa su PROPIO self.safe_execute.
            
    def __setattr__(self, name: str, value: Any) -> None:
        """Propaga cambios en session_factory o safe_execute a los managers."""
        super().__setattr__(name, value)
        if name in ('session_factory', 'safe_execute'):
            if hasattr(self, 'crud'):
                managers = [self.crud, self.maintenance, self.preparation, self.stats]
                for m in managers:
                    setattr(m, name, value)

    # Delegación: MachineCRUDManager
    def get_all_machines(self, *args, **kwargs) -> List[MachineDTO]:
        return self.crud.get_all_machines(*args, **kwargs)

    def get_latest_machines(self, *args, **kwargs) -> List[MachineDTO]:
        return self.crud.get_latest_machines(*args, **kwargs)

    def get_machines_by_process_type(self, *args, **kwargs) -> List[MachineDTO]:
        return self.crud.get_machines_by_process_type(*args, **kwargs)

    def get_distinct_machine_processes(self, *args, **kwargs) -> List[str]:
        return self.crud.get_distinct_machine_processes(*args, **kwargs)

    def add_machine(self, *args, **kwargs) -> Union[bool, str]:
        return self.crud.add_machine(*args, **kwargs)

    def update_machine(self, *args, **kwargs) -> bool:
        return self.crud.update_machine(*args, **kwargs)

    def delete_machine(self, *args, **kwargs) -> bool:
        return self.crud.delete_machine(*args, **kwargs)

    # Delegación: MachineMaintenanceManager
    def add_machine_maintenance(self, *args, **kwargs) -> bool:
        return self.maintenance.add_machine_maintenance(*args, **kwargs)

    def get_machine_maintenance_history(self, *args, **kwargs) -> List[MachineMaintenanceDTO]:
        return self.maintenance.get_machine_maintenance_history(*args, **kwargs)

    def get_machine_history(self, machine_id: int) -> Dict[str, Any]:
        """
        Wrapper de compatibilidad para `DatabaseManager.get_machine_history()`.

        Históricamente este método devolvía un diccionario con el historial de la máquina.
        En la implementación actual, el historial se obtiene desde el manager de mantenimiento.
        """
        return {"maintenance": self.get_machine_maintenance_history(machine_id)}

    # Delegación: MachinePreparationManager
    def add_prep_group(self, *args, **kwargs) -> Union[int, str, None]:
        return self.preparation.add_prep_group(*args, **kwargs)

    def get_groups_for_machine(self, *args, **kwargs) -> List[PreparationGroupDTO]:
        return self.preparation.get_groups_for_machine(*args, **kwargs)

    def get_group_details(self, *args, **kwargs) -> Optional[PreparationGroupDTO]:
        return self.preparation.get_group_details(*args, **kwargs)

    def update_prep_group(self, *args, **kwargs) -> bool:
        return self.preparation.update_prep_group(*args, **kwargs)

    def delete_prep_group(self, *args, **kwargs) -> bool:
        return self.preparation.delete_prep_group(*args, **kwargs)

    def add_prep_step(self, *args, **kwargs) -> Optional[int]:
        return self.preparation.add_prep_step(*args, **kwargs)

    def update_prep_step(self, *args, **kwargs) -> bool:
        return self.preparation.update_prep_step(*args, **kwargs)

    def get_steps_for_group(self, *args, **kwargs) -> List[PreparationStepDTO]:
        return self.preparation.get_steps_for_group(*args, **kwargs)

    def delete_prep_step(self, *args, **kwargs) -> bool:
        return self.preparation.delete_prep_step(*args, **kwargs)

    def get_prep_step_details(self, *args, **kwargs) -> Optional[PreparationStepDTO]:
        return self.preparation.get_prep_step_details(*args, **kwargs)

    # Delegación: MachineStatsManager
    def get_machine_usage_stats(self, *args, **kwargs) -> List[Tuple[str, float]]:
        return self.stats.get_machine_usage_stats(*args, **kwargs)
