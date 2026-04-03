"""
Nombre del Módulo: canvas_widget
Descripción: Widget canvas para arrastrar, soltar y visualizar conexiones entre tareas
             en el flujo de producción.
"""

import math
from typing import Any, Mapping, Union

from core.flow_canvas_io import (
    CanvasVisualConnection,
    legacy_canvas_task_is_cycle_start,
    legacy_canvas_task_widget,
    normalize_canvas_visual_connections,
)
from PyQt6.QtCore import Qt, QPointF, QLineF
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QPolygonF, QLinearGradient
from PyQt6.QtWidgets import QWidget


class CanvasWidget(QWidget):
    """
    Un widget personalizado que actúa como un canvas para arrastrar, soltar y visualizar
    las tareas del flujo de producción.
    """

    def __init__(self, parent_dialog: Any) -> None:
        super().__init__(parent_dialog)
        self.parent_dialog = parent_dialog
        self.setAcceptDrops(True)
        # Usamos la paleta del sistema para el fondo, para que se adapte al modo oscuro/claro
        self.setStyleSheet(
            """
            background-color: palette(base);
            border: 1px solid #dee2e6;
            """
        )

        self.connections: list[CanvasVisualConnection] = []

    def set_connections(
        self, new_connections: list[Union[CanvasVisualConnection, Mapping[str, Any]]]
    ) -> None:
        """Recibe conexiones (dict legacy o DTO) y fuerza un redibujado."""
        self.connections = normalize_canvas_visual_connections(new_connections)
        self.update()  # Llama a paintEvent para redibujar el widget

    def dragEnterEvent(self, event: Any) -> None:
        event.acceptProposedAction()

    def dragMoveEvent(self, event: Any) -> None:
        event.acceptProposedAction()

    def dropEvent(self, event: Any) -> None:
        task_data = event.source().currentItem().data(0, Qt.ItemDataRole.UserRole)
        drop_position = event.position().toPoint()
        # Explicitly pass skip_confirmation=False to always validate duplicates on drop
        self.parent_dialog._add_task_to_canvas(task_data, drop_position, skip_confirmation=False)
        event.acceptProposedAction()

    def paintEvent(self, event: Any) -> None:
        """
        Se llama cuando el widget necesita ser redibujado.
        Dibuja el grid de fondo y las conexiones con el estilo adecuado según su tipo.
        """
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Dibujar el grid ANTES que las conexiones
        self._draw_grid(painter)

        for connection in self.connections:
            start_widget = connection.start
            end_widget = connection.end
            conn_type = connection.connection_type

            if conn_type == "cyclic":
                start_point = QPointF(start_widget.geometry().center().x(), start_widget.geometry().bottom())
                end_point = QPointF(end_widget.geometry().center().x(), end_widget.geometry().top())

                start_task_index = self._get_task_index_by_widget(start_widget)
                end_task_index = self._get_task_index_by_widget(end_widget)

                is_from_mother = False
                is_to_mother = False

                if start_task_index is not None:
                    is_from_mother = legacy_canvas_task_is_cycle_start(
                        self.parent_dialog.canvas_tasks[start_task_index]
                    )

                if end_task_index is not None:
                    is_to_mother = legacy_canvas_task_is_cycle_start(
                        self.parent_dialog.canvas_tasks[end_task_index]
                    )

                self._draw_cyclic_arrow_with_glow(
                    painter,
                    start_point,
                    end_point,
                    start_widget,
                    end_widget,
                    is_from_mother,
                    is_to_mother,
                )
            else:
                pen = QPen(QColor("#007bff"), 2, Qt.PenStyle.SolidLine)
                brush = QBrush(QColor("#007bff"))
                start_point = QPointF(start_widget.geometry().right(), start_widget.geometry().center().y())
                end_point = QPointF(end_widget.geometry().left(), end_widget.geometry().center().y())

                painter.setPen(pen)
                painter.setBrush(brush)

                smart_path = self._calculate_smart_path(start_point, end_point, start_widget, end_widget)

                for i in range(len(smart_path) - 1):
                    painter.drawLine(smart_path[i], smart_path[i + 1])

                if len(smart_path) >= 2:
                    self._draw_arrowhead(painter, smart_path[-2], smart_path[-1])

    def _get_task_index_by_widget(self, widget: Any) -> int | None:
        """Obtiene el índice de una tarea por su widget."""
        for i, task in enumerate(self.parent_dialog.canvas_tasks):
            if legacy_canvas_task_widget(task) == widget:
                return i
        return None

    def _draw_cyclic_arrow_with_glow(
        self,
        painter: QPainter,
        start_point: QPointF,
        end_point: QPointF,
        start_widget: Any,
        end_widget: Any,
        is_from_mother: bool,
        is_to_mother: bool,
    ) -> None:
        """Dibuja una flecha cíclica con efecto neón y gradiente de color."""
        smart_path = self._calculate_smart_path(start_point, end_point, start_widget, end_widget)

        if is_from_mother:
            color_start = QColor(255, 200, 0)
            color_end = QColor(40, 167, 69)
        elif is_to_mother:
            color_start = QColor(40, 167, 69)
            color_end = QColor(255, 200, 0)
        else:
            color_start = QColor(40, 167, 69)
            color_end = QColor(40, 167, 69)

        num_glow_layers = 5
        for layer in range(num_glow_layers, 0, -1):
            alpha = int(150 * (1 - layer / num_glow_layers))
            pen_width = 4 + (layer * 2)

            for i in range(len(smart_path) - 1):
                p1 = smart_path[i]
                p2 = smart_path[i + 1]

                gradient = QLinearGradient(p1, p2)
                start_with_alpha = QColor(color_start.red(), color_start.green(), color_start.blue(), alpha)
                end_with_alpha = QColor(color_end.red(), color_end.green(), color_end.blue(), alpha)
                gradient.setColorAt(0, start_with_alpha)
                gradient.setColorAt(1, end_with_alpha)

                pen = QPen(QBrush(gradient), pen_width, Qt.PenStyle.SolidLine)
                pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                painter.setPen(pen)
                painter.drawLine(p1, p2)

        for i in range(len(smart_path) - 1):
            p1 = smart_path[i]
            p2 = smart_path[i + 1]

            gradient = QLinearGradient(p1, p2)
            gradient.setColorAt(0, color_start)
            gradient.setColorAt(1, color_end)

            pen = QPen(QBrush(gradient), 4, Qt.PenStyle.SolidLine)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            painter.drawLine(p1, p2)

        if len(smart_path) >= 2:
            painter.setBrush(QBrush(color_end))
            self._draw_arrowhead(painter, smart_path[-2], smart_path[-1], size=15)

    def _draw_grid(self, painter: QPainter) -> None:
        """Dibuja una cuadrícula de fondo tipo papel milimétrico."""
        grid_size = 20
        grid_color = QColor(200, 200, 200, 80)
        painter.setPen(QPen(grid_color, 1, Qt.PenStyle.SolidLine))

        width = self.width()
        height = self.height()

        x = 0
        while x <= width:
            painter.drawLine(x, 0, x, height)
            x += grid_size

        y = 0
        while y <= height:
            painter.drawLine(0, y, width, y)
            y += grid_size

    def _calculate_smart_path(
        self, start_point: QPointF, end_point: QPointF, start_widget: Any, end_widget: Any
    ) -> list[QPointF]:
        """Calcula una ruta inteligente siguiendo el grid entre dos puntos evitando tarjetas."""
        grid_size = 20

        start_x = round(start_point.x() / grid_size) * grid_size
        start_y = round(start_point.y() / grid_size) * grid_size
        end_x = round(end_point.x() / grid_size) * grid_size
        end_y = round(end_point.y() / grid_size) * grid_size

        obstacles = []
        for task in self.parent_dialog.canvas_tasks:
            widget = legacy_canvas_task_widget(task)
            if widget and widget != start_widget and widget != end_widget:
                rect = widget.geometry()
                obstacles.append(rect.adjusted(-10, -10, 10, 10))

        path1 = [QPointF(start_x, start_y), QPointF(end_x, start_y), QPointF(end_x, end_y)]
        path2 = [QPointF(start_x, start_y), QPointF(start_x, end_y), QPointF(end_x, end_y)]

        collisions1 = self._count_path_collisions(path1, obstacles)
        collisions2 = self._count_path_collisions(path2, obstacles)

        if collisions1 <= collisions2:
            if collisions1 > 0:
                return self._adjust_path_to_avoid_obstacles(path1, obstacles, grid_size)
            return path1

        if collisions2 > 0:
            return self._adjust_path_to_avoid_obstacles(path2, obstacles, grid_size)
        return path2

    def _count_path_collisions(self, path: list[QPointF], obstacles: list[Any]) -> int:
        """Cuenta cuántos segmentos del path colisionan con obstáculos."""
        collisions = 0
        for i in range(len(path) - 1):
            line = QLineF(path[i], path[i + 1])
            for obstacle in obstacles:
                if self._line_intersects_rect(line, obstacle):
                    collisions += 1
                    break
        return collisions

    def _line_intersects_rect(self, line: QLineF, rect: Any) -> bool:
        """Comprueba si una línea intersecta con un rectángulo."""
        top = QLineF(QPointF(rect.topLeft()), QPointF(rect.topRight()))
        bottom = QLineF(QPointF(rect.bottomLeft()), QPointF(rect.bottomRight()))
        left = QLineF(QPointF(rect.topLeft()), QPointF(rect.bottomLeft()))
        right = QLineF(QPointF(rect.topRight()), QPointF(rect.bottomRight()))

        for rect_line in [top, bottom, left, right]:
            result = line.intersects(rect_line)
            if result[0] == QLineF.IntersectionType.BoundedIntersection:
                return True

        if rect.contains(line.p1().toPoint()) or rect.contains(line.p2().toPoint()):
            return True
        return False

    def _adjust_path_to_avoid_obstacles(self, path: list[QPointF], obstacles: list[Any], grid_size: int) -> list[QPointF]:
        """Intenta ajustar el path para evitar obstáculos desplazándolo."""
        if len(path) != 3:
            return path

        start = path[0]
        middle = path[1]
        end = path[2]

        offsets = [grid_size * i for i in range(-5, 6) if i != 0]

        if abs(middle.x() - start.x()) > abs(middle.y() - start.y()):
            for offset in offsets:
                new_middle_y = middle.y() + offset
                adjusted_path = [start, QPointF(middle.x(), new_middle_y), QPointF(end.x(), new_middle_y), end]
                if self._count_path_collisions(adjusted_path, obstacles) == 0:
                    return adjusted_path
        else:
            for offset in offsets:
                new_middle_x = middle.x() + offset
                adjusted_path = [start, QPointF(new_middle_x, middle.y()), QPointF(new_middle_x, end.y()), end]
                if self._count_path_collisions(adjusted_path, obstacles) == 0:
                    return adjusted_path

        return path

    def _draw_arrowhead(self, painter: QPainter, p1: QPointF, p2: QPointF, size: int = 10) -> None:
        """Dibuja la punta de una flecha."""
        angle = math.atan2(p2.y() - p1.y(), p2.x() - p1.x())
        p3 = p2 - QPointF(math.cos(angle + math.pi / 6) * size, math.sin(angle + math.pi / 6) * size)
        p4 = p2 - QPointF(math.cos(angle - math.pi / 6) * size, math.sin(angle - math.pi / 6) * size)
        painter.drawPolygon(QPolygonF([p2, p3, p4]))

    def mousePressEvent(self, event: Any) -> None:
        """Detecta clics en el canvas (fondo) para ocultar el inspector."""
        clicked_widget = self.childAt(event.position().toPoint())
        if clicked_widget is None or clicked_widget == self:
            self.parent_dialog._hide_inspector_panel()
        super().mousePressEvent(event)

