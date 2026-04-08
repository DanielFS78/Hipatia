from __future__ import annotations
"""
Nombre del Modulo: flow_canvas
Descripcion: Canvas PyQt6 del flujo de produccion: tarjetas ``FlowCardWidget`` arrastrables,
             rejilla de fondo en el propio widget y conexiones dibujadas en un hijo
             ``_FlowConnectionsLayer`` encima de las tarjetas (Qt pinta primero el padre y luego
             los hijos; sin capa, las flechas quedarian tapadas). Ajusta geometria de la capa en
             ``resizeEvent``, ``set_connections`` y ``add_task_widget``, y la mantiene al frente
             con ``raise_``. Clic en fondo: ``mousePressEvent`` ignora la capa transparente para
             emitir ``backgroundClicked``. Las aristas se delegan a ``FlowConnectionPainter``.
"""

from typing import Any, List, Optional

from core.flow_card_labels import flow_card_task_id_str
from core.flow_canvas_io import (
    CanvasVisualConnection,
    connection_cyclic_paint_flags,
    connection_link_type,
    connection_widgets_pair,
    normalize_canvas_visual_connections,
)
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtGui import QPainter

from .flow_card_widget import FlowCardWidget
from .flow_connection_painter import FlowConnectionPainter


class _FlowConnectionsLayer(QWidget):
    """
    Hijo a pantalla completa del canvas: solo pinta conexiones, sin capturar raton
    (``WA_TransparentForMouseEvents``), para que el trazo quede visible sobre las tarjetas.
    """

    def __init__(self, canvas: "ProductionFlowCanvas") -> None:
        super().__init__(canvas)
        self._canvas = canvas
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAutoFillBackground(False)

    def paintEvent(self, event: Any) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        conn_painter = FlowConnectionPainter(painter)
        all_widgets: list[QWidget] = [w for w in self._canvas.task_widgets]

        for conn in self._canvas.connections:
            sw, ew = connection_widgets_pair(conn)
            if not isinstance(sw, QWidget) or not isinstance(ew, QWidget):
                continue
            if not sw.isVisible() or not ew.isVisible():
                continue
            link_t = connection_link_type(conn)
            flags = connection_cyclic_paint_flags(conn)
            conn_painter.draw_connection(sw, ew, link_t, flags, all_widgets)


def _drag_source_item_user_data(item: Any) -> Any:
    """``UserRole`` en el ítem: QListWidget usa data(role); QTreeWidget/QTableWidget, data(0, role)."""
    role = Qt.ItemDataRole.UserRole
    try:
        return item.data(role)
    except TypeError:
        return item.data(0, role)


class ProductionFlowCanvas(QWidget):
    """
    Area de trabajo del grafo de tareas: drop desde biblioteca, seleccion y movimiento de tarjetas,
    lista ``connections`` normalizada con ``CanvasVisualConnection`` y capa superior para flechas.
    Senales: ``taskDropped``, ``cardSelected`` (UID canvas o id logico), ``cardMoved``, ``backgroundClicked``.
    """
    
    # Señales para comunicación externa
    taskDropped = pyqtSignal(dict, QPoint) # task_data, position
    cardSelected = pyqtSignal(str)  # canvas_unique_id como str, o id lógico de tarea si no hay UID
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
        self._conn_layer = _FlowConnectionsLayer(self)
        self._conn_layer.setGeometry(self.rect())
        self._conn_layer.show()

    def _emit_card_selected_from_task_data(self, task_data: dict[str, Any]) -> None:
        uid = task_data.get("canvas_unique_id")
        if uid is not None:
            self.cardSelected.emit(str(int(uid)))
        else:
            self.cardSelected.emit(flow_card_task_id_str(task_data))

    def set_connections(
        self, new_connections: List[Any]
    ) -> None:
        """Actualiza la lista de conexiones (dict o CanvasVisualConnection) y redibuja."""
        self.connections = normalize_canvas_visual_connections(new_connections)
        self._conn_layer.setGeometry(self.rect())
        self._conn_layer.raise_()
        self._conn_layer.update()
        self.update()

    def add_task_widget(self, widget: FlowCardWidget) -> None:
        """Registra un widget de tarea en el canvas y conecta sus señales."""
        widget.setParent(self)
        widget.show()
        self.task_widgets.append(widget)
        
        # Conexiones de señales (UID de tarjeta = clave estable para el grafo; ver FlowGraphManager._on_card_selected)
        widget.clicked.connect(self._emit_card_selected_from_task_data)
        widget.moved.connect(self.cardMoved.emit)
        widget.moved.connect(self.update)
        widget.moved.connect(self._conn_layer.update)

        self._conn_layer.setGeometry(self.rect())
        self._conn_layer.raise_()
        self._conn_layer.update()

    def clear_widgets(self) -> None:
        """Limpia todos los widgets de tareas y conexiones."""
        for w in self.task_widgets:
            w.hide()
            w.deleteLater()
        self.task_widgets = []
        self.connections = []
        self._conn_layer.update()
        self.update()

    def resizeEvent(self, event: Any) -> None:
        super().resizeEvent(event)
        self._conn_layer.setGeometry(self.rect())
        self._conn_layer.raise_()
        self._conn_layer.update()

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
                    task_data = _drag_source_item_user_data(item)
                    self.taskDropped.emit(task_data, event.position().toPoint())
                    event.acceptProposedAction()
        except (AttributeError, RuntimeError):
            pass

    # --- Mouse Events ---

    def mousePressEvent(self, event: Any) -> None:
        """Detecta clics en el fondo del canvas."""
        clicked_widget = self.childAt(event.position().toPoint())
        if clicked_widget is None or clicked_widget is self or clicked_widget is self._conn_layer:
            self.backgroundClicked.emit()
        super().mousePressEvent(event)

    # --- Painting ---

    def paintEvent(self, event: Any) -> None:
        """Rejilla de fondo (las flechas van en ``_FlowConnectionsLayer``, encima de las tarjetas)."""
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        FlowConnectionPainter.draw_grid(painter, self.width(), self.height())
