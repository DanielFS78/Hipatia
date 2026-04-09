"""
Nombre del Módulo: flow_card_widget
Descripcion: Tarjeta de tarea en el canvas de flujo; textos delegados en core.flow_card_labels.
"""
from __future__ import annotations
from typing import Any, Optional

from core.flow_card_labels import (
    flow_card_primary_html,
    flow_card_task_id_str,
    flow_card_with_workers_html,
)
from PyQt6.QtWidgets import QLabel, QWidget
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtGui import QMouseEvent

class FlowCardWidget(QLabel):
    """
    Una tarjeta visual y MOVIBLE que representa una tarea en el canvas.
    Emite 'clicked' al ser seleccionada y 'moved' al ser movida.
    """
    # Señal para cuando se hace clic para seleccionar la tarjeta
    clicked = pyqtSignal(dict)
    # Nueva señal para notificar al diálogo principal que la tarjeta se ha movido
    moved = pyqtSignal(str, QPoint)  # task_id, new_position

    def __init__(self, task_data: dict[str, Any], parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.task_data = task_data
        
        self.setText(flow_card_primary_html(self.task_data))
        self.setFixedSize(180, 60)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setWordWrap(True)

        self._apply_base_style()

        # Atributos para gestionar el arrastre
        self.dragging = False
        self.drag_start_position = QPoint()

    def _apply_base_style(self) -> None:
        """Aplica el estilo CSS base."""
        self.setStyleSheet("""
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
        """)

    def mousePressEvent(self, event: QMouseEvent | None) -> None:
        """Se activa al hacer clic en la tarjeta."""
        if event is not None:
            self.clicked.emit(self.task_data)
            if event.button() == Qt.MouseButton.LeftButton:
                self.dragging = True
                self.drag_start_position = event.position().toPoint()

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent | None) -> None:
        """Se activa al mover el ratón mientras se mantiene presionado."""
        if event is not None and self.dragging:
            new_pos = self.mapToParent(event.position().toPoint() - self.drag_start_position)
            self.move(new_pos)
            parent = self.parent()
            if isinstance(parent, QWidget):
                # Forzar redibujado de conexiones en el canvas
                parent.update()

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent | None) -> None:
        """Se activa al soltar el botón del ratón."""
        if event is not None and event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False
            self._snap_to_grid()
            self.moved.emit(flow_card_task_id_str(self.task_data), self.pos())

        super().mouseReleaseEvent(event)

    def _snap_to_grid(self) -> None:
        """Ajusta la posición de la tarjeta al punto más cercano de la cuadrícula."""
        grid_size = 20
        snapped_x = round(self.x() / grid_size) * grid_size
        snapped_y = round(self.y() / grid_size) * grid_size
        self.move(snapped_x, snapped_y)

    def set_selected(self, selected: bool) -> None:
        """Marca visualmente la tarjeta como seleccionada."""
        if selected:
            self.setStyleSheet("""
                QLabel {
                    background-color: palette(highlight);
                    color: palette(highlightedText);
                    border: 2px solid #0056b3;
                    border-radius: 5px;
                    padding: 5px;
                }
            """)
        else:
            self._apply_base_style()

    def set_highlighted(self, highlighted: bool, color: Optional[str] = None) -> None:
        """Resalta la tarjeta con un color específico."""
        if highlighted and color:
            self.setStyleSheet(f"""
                QLabel {{
                    background-color: {color};
                    color: white;
                    border: 2px solid {color};
                    border-radius: 5px;
                    padding: 5px;
                }}
            """)
        else:
            self.set_selected(False) 

    def update_workers(self, worker_names: list[str]) -> None:
        """Actualiza la visualización de los trabajadores asignados."""
        text, tip = flow_card_with_workers_html(self.task_data, worker_names)
        self.setToolTip(tip)
        self.setText(text)
