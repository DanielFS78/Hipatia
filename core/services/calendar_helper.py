# -*- coding: utf-8 -*-
"""
Nombre del Módulo: calendar_helper
Descripción: Acceso global opcional a la configuración de calendario y jornada (compatibilidad).

Algunos módulos históricos leen el horario vía ``get_schedule_config`` tras un
``set_schedule_config`` en el arranque de la aplicación.
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