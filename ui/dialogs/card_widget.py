"""
Nombre del Módulo: card_widget
Descripción: Tarjeta visual movible que representa una tarea dentro de un `CanvasWidget`.
"""

from typing import Any
from core.dtos import FlowTaskDataDTO

from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtWidgets import QLabel


class CardWidget(QLabel):
    """
    Una tarjeta visual y MOVIBLE que representa una tarea en el canvas.
    Emite 'clicked' al ser seleccionada y 'moved' al ser movida.
    """

    clicked = pyqtSignal(object)
    moved = pyqtSignal()

    def __init__(self, task_data: FlowTaskDataDTO | dict[str, Any], parent: Any) -> None:
        super().__init__(parent)
        self.task_data: FlowTaskDataDTO = (
            FlowTaskDataDTO.from_legacy_mapping(task_data)
            if isinstance(task_data, dict)
            else task_data
        )
        parent_widget = self.parent()
        self.parent_dialog = getattr(parent_widget, "parent_dialog", None)

        name, duration = self._task_name_duration()
        self.setText(f"<b>{name}</b>\n<small>{duration:.2f} min</small>")
        self.setFixedSize(180, 60)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setWordWrap(True)

        self.setStyleSheet(
            """
            QLabel {
                background-color: palette(window);
                color: palette(windowText);
                border: 1px solid #007bff;
                border-radius: 5px;
                padding: 5px;
            }
            QLabel:hover {
                background-color: palette(highlight);
            }
            """
        )

        self.dragging = False
        self.drag_start_position = QPoint()

    def mousePressEvent(self, event: Any) -> None:
        """Se activa al hacer clic en la tarjeta."""
        self.clicked.emit(self.task_data)
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.drag_start_position = event.position().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: Any) -> None:
        """Se activa al mover el ratón mientras se mantiene presionado."""
        if self.dragging:
            new_pos = self.mapToParent(event.position().toPoint() - self.drag_start_position)
            self.move(new_pos)
            if self.parent_dialog:
                self.parent_dialog._update_canvas_connections()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: Any) -> None:
        """Se activa al soltar el botón del ratón."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False
            self._snap_to_grid()
            self.moved.emit()
        super().mouseReleaseEvent(event)

    def _snap_to_grid(self) -> None:
        """Ajusta la posición de la tarjeta al punto más cercano de la cuadrícula."""
        grid_size = 20
        snapped_x = round(self.x() / grid_size) * grid_size
        snapped_y = round(self.y() / grid_size) * grid_size
        self.move(snapped_x, snapped_y)

    def _task_name_duration(self) -> tuple[str, float]:
        """Devuelve nombre y duración desde el DTO de tarea."""
        return self.task_data.name, float(self.task_data.duration)

