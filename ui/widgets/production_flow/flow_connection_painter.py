"""
Nombre del Módulo: flow_connection_painter
Descripcion: Dibuja conexiones entre tarjetas del canvas de flujo usando
             metadatos tipados para aristas ciclicas (sin dict en la firma de pintado).
"""
from __future__ import annotations
import math
from typing import Any, List

from core.dtos import CanvasCyclicConnectionFlags
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QPointF, QLineF
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QPolygonF, QLinearGradient

class FlowConnectionPainter:
    """
    Clase de utilidad para dibujar conexiones entre tareas en el canvas.
    Centraliza la lógica de cálculo de rutas y renderizado.
    """

    def __init__(self, painter: QPainter) -> None:
        self.painter = painter

    def draw_connection(
        self,
        start_widget: QWidget,
        end_widget: QWidget,
        conn_type: str,
        cyclic_flags: CanvasCyclicConnectionFlags,
        all_widgets: List[QWidget],
    ) -> None:
        """Dibuja una conexión entre dos widgets."""
        if conn_type == "cyclic":
            self._draw_cyclic_connection(start_widget, end_widget, cyclic_flags, all_widgets)
        else:
            self._draw_normal_connection(start_widget, end_widget, all_widgets)

    def _draw_normal_connection(self, start_widget: QWidget, end_widget: QWidget, 
                                all_widgets: List[QWidget]) -> None:
        """Dibuja una conexión estándar con flecha."""
        pen = QPen(QColor("#007bff"), 2, Qt.PenStyle.SolidLine)
        brush = QBrush(QColor("#007bff"))
        
        start_point = QPointF(start_widget.geometry().right(), start_widget.geometry().center().y())
        end_point = QPointF(end_widget.geometry().left(), end_widget.geometry().center().y())

        self.painter.setPen(pen)
        self.painter.setBrush(brush)

        path = self.calculate_smart_path(start_point, end_point, start_widget, end_widget, all_widgets)
        
        for i in range(len(path) - 1):
            self.painter.drawLine(path[i], path[i + 1])

        if len(path) >= 2:
            self._draw_arrowhead(path[-2], path[-1])

    def _draw_cyclic_connection(
        self,
        start_widget: QWidget,
        end_widget: QWidget,
        cyclic_flags: CanvasCyclicConnectionFlags,
        all_widgets: List[QWidget],
    ) -> None:
        """Dibuja una conexión cíclica con efectos de brillo."""
        start_point = QPointF(start_widget.geometry().center().x(), start_widget.geometry().bottom())
        end_point = QPointF(end_widget.geometry().center().x(), end_widget.geometry().top())
        
        is_from_mother = cyclic_flags.is_from_mother
        is_to_mother = cyclic_flags.is_to_mother
        
        path = self.calculate_smart_path(start_point, end_point, start_widget, end_widget, all_widgets)

        color_start = QColor(40, 167, 69) # Verde por defecto
        color_end = QColor(40, 167, 69)
        
        if is_from_mother:
            color_start, color_end = QColor(255, 200, 0), QColor(40, 167, 69)
        elif is_to_mother:
            color_start, color_end = QColor(40, 167, 69), QColor(255, 200, 0)

        # Glow effect
        num_layers = 5
        for layer in range(num_layers, 0, -1):
            alpha = int(150 * (1 - layer / num_layers))
            pen_width = 4 + (layer * 2)
            self._draw_path_with_gradient(path, color_start, color_end, alpha, pen_width)

        # Solid center line
        self._draw_path_with_gradient(path, color_start, color_end, 255, 4)

        if len(path) >= 2:
            self.painter.setBrush(QBrush(color_end))
            self._draw_arrowhead(path[-2], path[-1], size=15)

    def _draw_path_with_gradient(self, path: List[QPointF], c1: QColor, c2: QColor, 
                                 alpha: int, width: int) -> None:
        """Dibuja un camino con gradiente de color."""
        for i in range(len(path) - 1):
            p1, p2 = path[i], path[i+1]
            gradient = QLinearGradient(p1, p2)
            gradient.setColorAt(0, QColor(c1.red(), c1.green(), c1.blue(), alpha))
            gradient.setColorAt(1, QColor(c2.red(), c2.green(), c2.blue(), alpha))
            
            pen = QPen(QBrush(gradient), width, Qt.PenStyle.SolidLine)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            self.painter.setPen(pen)
            self.painter.drawLine(p1, p2)

    def calculate_smart_path(self, start: QPointF, end: QPointF, 
                             sw: QWidget, ew: QWidget, 
                             all_widgets: List[QWidget]) -> List[QPointF]:
        """Calcula una ruta que evita obstáculos."""
        grid = 20
        s_grid = QPointF(round(start.x()/grid)*grid, round(start.y()/grid)*grid)
        e_grid = QPointF(round(end.x()/grid)*grid, round(end.y()/grid)*grid)

        obstacles = [w.geometry().adjusted(-10, -10, 10, 10) 
                     for w in all_widgets if w not in (sw, ew) and w.isVisible()]

        p1 = [s_grid, QPointF(e_grid.x(), s_grid.y()), e_grid]
        p2 = [s_grid, QPointF(s_grid.x(), e_grid.y()), e_grid]

        c1 = self._count_collisions(p1, obstacles)
        c2 = self._count_collisions(p2, obstacles)

        best_path = p1 if c1 <= c2 else p2
        if self._count_collisions(best_path, obstacles) > 0:
            return self._avoid_obstacles(best_path, obstacles, grid)
        return best_path

    def _count_collisions(self, path: List[QPointF], obstacles: List[Any]) -> int:
        count = 0
        for i in range(len(path)-1):
            line = QLineF(path[i], path[i+1])
            for obs in obstacles:
                if self._line_intersects_rect(line, obs):
                    count += 1
                    break
        return count

    def _line_intersects_rect(self, line: QLineF, rect: Any) -> bool:
        if rect.contains(line.p1().toPoint()) or rect.contains(line.p2().toPoint()):
            return True
        for edge_points in [(rect.topLeft(), rect.topRight()), (rect.bottomLeft(), rect.bottomRight()),
                           (rect.topLeft(), rect.bottomLeft()), (rect.topRight(), rect.bottomRight())]:
            edge = QLineF(QPointF(edge_points[0]), QPointF(edge_points[1]))
            if line.intersects(edge)[0] == QLineF.IntersectionType.BoundedIntersection:
                return True
        return False

    def _avoid_obstacles(self, path: List[QPointF], obstacles: List[Any], grid: int) -> List[QPointF]:
        if len(path) != 3: return path
        s, m, e = path[0], path[1], path[2]
        is_h = abs(m.x() - s.x()) > abs(m.y() - s.y())
        
        for offset in [grid * i for i in range(-5, 6) if i != 0]:
            if is_h:
                adj = [s, QPointF(m.x(), m.y()+offset), QPointF(e.x(), m.y()+offset), e]
            else:
                adj = [s, QPointF(m.x()+offset, m.y()), QPointF(m.x()+offset, e.y()), e]
            if self._count_collisions(adj, obstacles) == 0:
                return adj
        return path

    def _draw_arrowhead(self, p1: QPointF, p2: QPointF, size: int = 10) -> None:
        angle = math.atan2(p2.y() - p1.y(), p2.x() - p1.x())
        p3 = p2 - QPointF(math.cos(angle + math.pi/6)*size, math.sin(angle + math.pi/6)*size)
        p4 = p2 - QPointF(math.cos(angle - math.pi/6)*size, math.sin(angle - math.pi/6)*size)
        self.painter.drawPolygon(QPolygonF([p2, p3, p4]))

    @staticmethod
    def draw_grid(painter: QPainter, width: int, height: int) -> None:
        """Dibuja la cuadrícula de fondo."""
        grid_size = 20
        painter.setPen(QPen(QColor(200, 200, 200, 80), 1, Qt.PenStyle.SolidLine))
        for x in range(0, width, grid_size):
            painter.drawLine(x, 0, x, height)
        for y in range(0, height, grid_size):
            painter.drawLine(0, y, width, y)
