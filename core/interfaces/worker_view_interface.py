"""
Lógica o utilidades del núcleo (`worker_view_interface`): tipos, servicios auxiliares o infraestructura compartida fuera de la capa de interfaz.
"""

from abc import abstractmethod
from typing import Any, Dict, List, Optional
from core.interfaces.controller_interface import QABCMeta

class IWorkerView(metaclass=QABCMeta):
    """
    Interfaz abstracta para la vista del trabajador.
    """

    # Firmas de señales para el tipado estático (PyQtSignals runtime)
    logout_requested: Any
    camera_config_requested: Any
    task_selected: Any
    generate_labels_requested: Any
    consult_qr_requested: Any
    start_task_requested: Any
    end_task_requested: Any
    register_incidence_requested: Any
    export_data_requested: Any

    @abstractmethod
    def update_tasks_list(self, tasks: List[Dict[str, Any]]) -> None:
        """Actualiza la lista de tareas asignadas."""
        pass

    @abstractmethod
    def update_task_state(self, state: str, current_step_name: Optional[str] = None) -> None:
        """Actualiza el estado visual de la tarea actual."""
        pass

    @abstractmethod
    def show_message(self, title: str, message: str, level: str = "info") -> None:
        """Muestra un mensaje al trabajador."""
        pass

    @abstractmethod
    def show_confirmation_dialog(self, title: str, message: str) -> bool:
        """Muestra un diálogo de confirmación."""
        pass

    @abstractmethod
    def enable_action_buttons(self, enabled: bool) -> None:
        """Habilita o deshabilita los botones de acción."""
        pass

    # Las señales deben estar disponibles para que el controlador las conecte
    # En una interfaz abstracta pura de Python (no QObject), esto es complicado
    # con PyQt. Usaremos una clase base que herede de QObject para las señales.
