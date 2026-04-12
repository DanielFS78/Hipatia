# -*- coding: utf-8 -*-
"""
Nombre del Módulo: ui.dialogs.effects.mixed_gold_green
Descripción: Efecto visual o animación para el canvas de flujo o simulación (pintado con QTimer).
"""

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QEvent, QRectF
from PyQt6.QtGui import QPainter, QColor, QPen
from typing import Any

class MixedGoldGreenEffect(QWidget):
    """
    Widget que dibuja un aro con efecto mixto dorado-verde para tareas finales de ciclo.
    """

    def __init__(self, parent_card: Any) -> None:
        canvas_parent = parent_card.parent()
        super().__init__(canvas_parent)
        self.parent_card = parent_card
        self.rotation_angle = 0

        self.parent_card.installEventFilter(self)
        if canvas_parent:
            canvas_parent.installEventFilter(self)

        self._update_geometry()
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.show()
        self.raise_()

    def eventFilter(self, obj: Any, event: Any) -> bool:
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
        if not self.parent_card or not self.parent_card.isVisible():
            self.hide()
            return
        canvas = self.parent()
        if not canvas:
            self.hide()
            return

        margin = 15
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
        """Efecto neón mixto ESTÁTICO (sin animación)."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        margin = 15
        inner_rect = QRectF(
            margin, margin,
            self.width() - 2 * margin,
            self.height() - 2 * margin
        )
        corner_radius = 10

        # Capas doradas (izquierda/arriba)
        for i in range(3, 0, -1):
            alpha = int(60 * (1 - i / 3))
            pen_width = max(1, 4 - i)

            layer_color = QColor(255, 215, 0, alpha)
            pen = QPen(layer_color, pen_width)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)

            expansion = i * 2
            current_rect = inner_rect.adjusted(-expansion, -expansion, expansion, expansion)
            painter.drawRoundedRect(current_rect, corner_radius + i, corner_radius + i)

        # Capas verdes (derecha/abajo)
        for i in range(3, 0, -1):
            alpha = int(60 * (1 - i / 3))
            pen_width = max(1, 4 - i)

            layer_color = QColor(40, 167, 69, alpha)
            pen = QPen(layer_color, pen_width)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)

            expansion = int(i * 1.5)  # Ligeramente diferente para mezcla
            current_rect = inner_rect.adjusted(-expansion, -expansion, expansion, expansion)
            painter.drawRoundedRect(current_rect, corner_radius + i, corner_radius + i)

        # Línea central mixta (un color intermedio)
        painter.setPen(QPen(QColor(147, 191, 39, 255), 2))  # Verde-amarillento
        painter.drawRoundedRect(inner_rect, corner_radius, corner_radius)

    def stop_animation(self) -> None:
        if hasattr(self, 'animation_timer'):
            self.animation_timer.stop()
        if self.parent_card:
            self.parent_card.removeEventFilter(self)
        parent = self.parent()
        if parent:
            parent.removeEventFilter(self)
