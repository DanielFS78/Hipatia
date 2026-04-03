from __future__ import annotations
"""
Interfaz PyQt6 (`flow_canvas`): widgets, diálogos o recursos visuales conectados al flujo de usuario.
"""

from typing import Any, List, Optional

from core.flow_canvas_io import (
    CanvasVisualConnection,
    connection_cyclic_paint_flags,
    connection_link_type,
    connection_widgets_pair,
    normalize_canvas_visual_connections,
)
from core.flow_card_labels import flow_card_task_id_str
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtGui import QPainter

from .flow_card_widget import FlowCardWidget
from .flow_connection_painter import FlowConnectionPainter

class ProductionFlowCanvas(QWidget):
    """
    Un widget personalizado que actúa como un canvas para arrastrar, soltar y visualizar
    las tareas del flujo de producción.
    """
    
    # Señales para comunicación externa
    taskDropped = pyqtSignal(dict, QPoint) # task_data, position
    cardSelected = pyqtSignal(str)         # task_id
    cardMoved = pyqtSignal(str, QPoint)    # task_id, new_position
    backgroundClicked = pyqtSignal()
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setStyleSheet("""
            background-color: palette(base); 
            border: 1px solid #dee2e6;
        """)

        self.connections: List[CanvasVisualConnection] = []
        self.task_widgets: List[FlowCardWidget] = []

    def set_connections(
        self, new_connections: List[Any]
    ) -> None:
        """Actualiza la lista de conexiones (dict o CanvasVisualConnection) y redibuja."""
        self.connections = normalize_canvas_visual_connections(new_connections)
        self.update()

    def add_task_widget(self, widget: FlowCardWidget) -> None:
        """Registra un widget de tarea en el canvas y conecta sus señales."""
        widget.setParent(self)
        widget.show()
        self.task_widgets.append(widget)
        
        # Conexiones de señales
        widget.clicked.connect(lambda data: self.cardSelected.emit(flow_card_task_id_str(data)))
        widget.moved.connect(self.cardMoved.emit)
        widget.moved.connect(self.update) # Redibujar al mover
        
    def clear_widgets(self) -> None:
        """Limpia todos los widgets de tareas y conexiones."""
        for w in self.task_widgets:
            w.hide()
            w.deleteLater()
        self.task_widgets = []
        self.connections = []
        self.update()

    # --- Drag & Drop ---

    def dragEnterEvent(self, event: Any) -> None:
        event.acceptProposedAction()

    def dragMoveEvent(self, event: Any) -> None:
        event.acceptProposedAction()

    def dropEvent(self, event: Any) -> None:
        try:
            source = event.source()
            if hasattr(source, 'currentItem'):
                item = source.currentItem()
                if item:
                    task_data = item.data(Qt.ItemDataRole.UserRole)
                    self.taskDropped.emit(task_data, event.position().toPoint())
                    event.acceptProposedAction()
        except (AttributeError, RuntimeError):
            pass

    # --- Mouse Events ---

    def mousePressEvent(self, event: Any) -> None:
        """Detecta clics en el fondo del canvas."""
        clicked_widget = self.childAt(event.position().toPoint())
        if clicked_widget is None or clicked_widget == self:
            self.backgroundClicked.emit()
        super().mousePressEvent(event)

    # --- Painting ---

    def paintEvent(self, event: Any) -> None:
        """Renderiza la rejilla y las conexiones entre tareas."""
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 1. Dibujar Rejilla
        FlowConnectionPainter.draw_grid(painter, self.width(), self.height())

        # 2. Dibujar Conexiones
        conn_painter = FlowConnectionPainter(painter)
        all_widgets: List[QWidget] = [w for w in self.task_widgets]
        
        for conn in self.connections:
            sw, ew = connection_widgets_pair(conn)
            if not isinstance(sw, QWidget) or not isinstance(ew, QWidget):
                continue
            if not sw.isVisible() or not ew.isVisible():
                continue

            link_t = connection_link_type(conn)
            flags = connection_cyclic_paint_flags(conn)
            conn_painter.draw_connection(sw, ew, link_t, flags, all_widgets)
