# calendar_helper.py (versión simplificada para compatibilidad)
_schedule_config = None

def set_schedule_config(config):
    """Establece la configuración de horario global para compatibilidad."""
    global _schedule_config
    _schedule_config = config

def get_schedule_config():
    """Obtiene la configuración de horario global."""
    return _schedule_config