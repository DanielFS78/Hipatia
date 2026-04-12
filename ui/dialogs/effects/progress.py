# -*- coding: utf-8 -*-
"""
Nombre del Módulo: ui.dialogs.effects.progress
Descripción: Efecto visual o animación para el canvas de flujo o simulación (pintado con QTimer).
"""

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QEvent, QRectF
from PyQt6.QtGui import QPainter, QColor, QPen
from typing import Any

class SimulationProgressEffect(QWidget):
    """
    Widget que dibuja un aro azulado grisáceo giratorio con efecto neón
    para indicar que una tarjeta está siendo procesada por la simulación.
    """

    def __init__(self, parent_card: Any) -> None:
        # El padre debe ser el canvas (el contenedor de las tarjetas)
        canvas_parent = parent_card.parent()
        super().__init__(canvas_parent)
        self.parent_card = parent_card
        self.rotation_angle = 0

        # Instalar filtro de eventos en la tarjeta padre
        self.parent_card.installEventFilter(self)

        # También instalar filtro en el canvas
        if canvas_parent:
            canvas_parent.installEventFilter(self)

        # Configurar geometría inicial
        self._update_geometry()

        # Hacer invisible a eventos de ratón
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        # Mostrar y asegurar que esté por encima
        self.show()
        self.raise_()

    def eventFilter(self, obj: Any, event: Any) -> bool:
        """Filtra eventos para actualizar geometría cuando sea necesario."""
        if obj == self.parent_card:
            if event.type() in (QEvent.Type.Move, QEvent.Type.Resize,
                                QEvent.Type.Show, QEvent.Type.Hide):
                self._update_geometry()
                return False

        if obj == self.parent():
            if event.type() in (QEvent.Type.Resize, QEvent.Type.LayoutRequest):
                self._update_geometry()
                return False

        return super().eventFilter(obj, event)

    def _update_geometry(self) -> None:
        """Actualiza posición y tamaño para rodear la tarjeta."""
        if not self.parent_card or not self.parent_card.isVisible():
            self.hide()
            return

        canvas = self.parent()
        if not canvas:
            self.hide()
            return

        margin = 20  # Ligeramente más grande que el efecto dorado

        card_pos = self.parent_card.pos()
        card_size = self.parent_card.size()

        self.setGeometry(
            card_pos.x() - margin,
            card_pos.y() - margin,
            card_size.width() + 2 * margin,
            card_size.height() + 2 * margin
        )

        self.show()
        self.raise_()

    def paintEvent(self, event: Any) -> None:
        """Dibuja un efecto neón azulado con luz circulante continua."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Dimensiones del rectángulo interno
        margin = 20
        # Placeholder del dibujo original que estaba incompleto en visual_effects.py
        # pero se mantiene la estructura.
        pass
