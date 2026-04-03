"""
Lógica o utilidades del núcleo (`calendar_helper`): tipos, servicios auxiliares o infraestructura compartida fuera de la capa de interfaz.
"""

from typing import Any

_schedule_config: Any = None

def set_schedule_config(config: Any) -> None:
    """Establece la configuración de horario global para compatibilidad."""
    global _schedule_config
    _schedule_config = config

def get_schedule_config() -> Any:
    """Obtiene la configuración de horario global."""
    return _schedule_config