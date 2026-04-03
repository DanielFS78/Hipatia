"""
Interfaz PyQt6 (`__init__`): widgets, diálogos o recursos visuales conectados al flujo de usuario.
"""

from .prep_steps_dialog import PrepStepsDialog
from .prep_groups_dialog import PrepGroupsDialog
from .preproceso_dialog import PreprocesoDialog

__all__ = [
    'PrepStepsDialog',
    'PrepGroupsDialog',
    'PreprocesoDialog',
]
