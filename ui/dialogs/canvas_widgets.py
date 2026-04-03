"""
Compatibilidad: módulo histórico que expone `CanvasWidget` y `CardWidget`.

Este archivo existe para mantener imports estables (`ui.dialogs.canvas_widgets`)
tras la división del monolito en módulos más pequeños.
"""

from .canvas_widget import CanvasWidget
from .card_widget import CardWidget

__all__ = ["CanvasWidget", "CardWidget"]
