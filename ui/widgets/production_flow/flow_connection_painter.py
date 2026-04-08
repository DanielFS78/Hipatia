"""
Nombre del Módulo: flow_connection_painter
Descripcion: Pintado y enrutado de conectores entre tarjetas del canvas de flujo de produccion.

    - Enrutado (``calculate_smart_path``): polilinea ortogonal Manhattan que no cruza ninguna
      tarjeta visible, incluidos origen y destino. Margen de exclusion ``CONNECTOR_OBSTACLE_PAD``;
      los puntos de ruta usan ``CONNECTOR_EDGE_STUB`` mas alla del borde para quedar fuera de ese
      rectangulo. Si el tramo directo es libre, se prefieren codos en L o un «jog» para evitar
      lineas rectas entre celdas alineadas. Respaldo: barrido de corredores y desvios en U.
    - Dibujo: terminales visuales en el borde de la celda se anteponen/sufijan a la polilinea de
      ruta para que linea y flecha encajen con la tarjeta (sin hueco flotante). Trazo con
      ``QPainterPath`` y esquinas redondeadas (``quadTo``). Conexiones ciclicas: anclajes
      verticalmente (abajo/arriba), gradiente y flecha segun tangente real del path.
    - API de aristas: tipos y flags ciclicos via ``CanvasCyclicConnectionFlags`` (sin dict en
      la firma de pintado).
"""
from __future__ import annotations

import math
from typing import Any, List, Optional, Tuple

from core.dtos import CanvasCyclicConnectionFlags
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QPointF, QLineF, QRect
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QPolygonF, QLinearGradient, QPainterPath

# Margen de exclusión al comprobar intersecciones; los anclajes deben quedar FUERA de rect ± pad.
CONNECTOR_OBSTACLE_PAD = 18
CONNECTOR_EDGE_STUB = float(CONNECTOR_OBSTACLE_PAD + 14)


def _anchors_by_vector(
    sw: QWidget, ew: QWidget, stub: float = CONNECTOR_EDGE_STUB, margin: float = 12.0
) -> Tuple[QPointF, QPointF]:
    """
    Puntos de enrutamiento fuera del borde (``stub``), con Y o X orientada hacia la otra tarjeta.
    Deben usar ``stub >= CONNECTOR_OBSTACLE_PAD`` para quedar fuera del rectangulo de colision.
    """
    sr = sw.geometry()
    er = ew.geometry()
    scx, scy = sr.center().x(), sr.center().y()
    ecx, ecy = er.center().x(), er.center().y()
    dx = float(ecx - scx)
    dy = float(ecy - scy)

    def cy(rect: QRect, qy: float) -> float:
        return float(max(rect.top() + margin, min(rect.bottom() - margin, qy)))

    def cx(rect: QRect, qx: float) -> float:
        return float(max(rect.left() + margin, min(rect.right() - margin, qx)))

    if abs(dx) >= abs(dy):
        if dx >= 0:
            return QPointF(sr.right() + stub, cy(sr, float(ecy))), QPointF(er.left() - stub, cy(er, float(scy)))
        return QPointF(sr.left() - stub, cy(sr, float(ecy))), QPointF(er.right() + stub, cy(er, float(scy)))
    if dy >= 0:
        return QPointF(cx(sr, float(ecx)), sr.bottom() + stub), QPointF(cx(er, float(scx)), er.top() - stub)
    return QPointF(cx(sr, float(ecx)), sr.top() - stub), QPointF(cx(er, float(scx)), er.bottom() + stub)


def _cyclic_anchors(
    sw: QWidget, ew: QWidget, stub: float = CONNECTOR_EDGE_STUB, margin: float = 12.0
) -> Tuple[QPointF, QPointF]:
    """Anclajes de ruta bajo el borde inferior del origen y sobre el superior del destino (con ``stub``)."""
    sr = sw.geometry()
    er = ew.geometry()
    scx = float(sr.center().x())
    ecx = float(er.center().x())
    x0 = float(max(sr.left() + margin, min(sr.right() - margin, ecx)))
    x1 = float(max(er.left() + margin, min(er.right() - margin, scx)))
    return QPointF(x0, float(sr.bottom() + stub)), QPointF(x1, float(er.top() - stub))


def _visual_terminals_lateral(sw: QWidget, ew: QWidget, margin: float = 12.0) -> Tuple[QPointF, QPointF]:
    """Bordes visibles de las tarjetas (sin hueco); la ruta geométrica usa EDGE_STUB más allá."""
    sr = sw.geometry()
    er = ew.geometry()
    scx, scy = sr.center().x(), sr.center().y()
    ecx, ecy = er.center().x(), er.center().y()
    dx = float(ecx - scx)
    dy = float(ecy - scy)

    def cy(rect: QRect, qy: float) -> float:
        return float(max(rect.top() + margin, min(rect.bottom() - margin, qy)))

    def cx(rect: QRect, qx: float) -> float:
        return float(max(rect.left() + margin, min(rect.right() - margin, qx)))

    if abs(dx) >= abs(dy):
        if dx >= 0:
            v0 = QPointF(float(sr.right()), cy(sr, float(ecy)))
            v1 = QPointF(float(er.left()), cy(er, float(scy)))
        else:
            v0 = QPointF(float(sr.left()), cy(sr, float(ecy)))
            v1 = QPointF(float(er.right()), cy(er, float(scy)))
    elif dy >= 0:
        v0 = QPointF(cx(sr, float(ecx)), float(sr.bottom()))
        v1 = QPointF(cx(er, float(scx)), float(er.top()))
    else:
        v0 = QPointF(cx(sr, float(ecx)), float(sr.top()))
        v1 = QPointF(cx(er, float(scx)), float(er.bottom()))
    return v0, v1


def _visual_terminals_cyclic(sw: QWidget, ew: QWidget, margin: float = 12.0) -> Tuple[QPointF, QPointF]:
    """Borde inferior de origen y borde superior de destino (flecha llega a la celda)."""
    sr = sw.geometry()
    er = ew.geometry()
    scx = float(sr.center().x())
    ecx = float(er.center().x())
    x0 = float(max(sr.left() + margin, min(sr.right() - margin, ecx)))
    x1 = float(max(er.left() + margin, min(er.right() - margin, scx)))
    # Origen en el borde inferior visible; destino unos px dentro por arriba para que la flecha apunte a la celda.
    inset_end = 3.0
    return QPointF(x0, float(sr.bottom())), QPointF(x1, float(er.top() + inset_end))


def _dedupe_consecutive_points(pts: List[QPointF], eps: float = 0.5) -> List[QPointF]:
    """Elimina vertices consecutivos casi coincidentes al unir terminales visuales con la ruta."""
    if not pts:
        return []
    out: List[QPointF] = [pts[0]]
    for p in pts[1:]:
        if (p - out[-1]).manhattanLength() > eps:
            out.append(p)
    return out


def _orthogonal_polyline_to_rounded_path(pts: List[QPointF], radius: float = 14.0) -> QPainterPath:
    """
    Convierte una polilínea ortogonal en un QPainterPath con esquinas redondeadas (quadTo),
    estilo conector tipo diagrama profesional.
    """
    pp = QPainterPath()
    n = len(pts)
    if n < 2:
        return pp
    if n == 2:
        pp.moveTo(pts[0])
        pp.lineTo(pts[1])
        return pp

    r_cap = max(4.0, min(radius, 22.0))
    pp.moveTo(pts[0])
    for i in range(1, n - 1):
        p_prev, p_curr, p_next = pts[i - 1], pts[i], pts[i + 1]
        v_in = QPointF(p_curr.x() - p_prev.x(), p_curr.y() - p_prev.y())
        v_out = QPointF(p_next.x() - p_curr.x(), p_next.y() - p_curr.y())
        len_in = math.hypot(v_in.x(), v_in.y())
        len_out = math.hypot(v_out.x(), v_out.y())
        if len_in < 1e-6 or len_out < 1e-6:
            pp.lineTo(p_curr)
            continue
        v_in = QPointF(v_in.x() / len_in, v_in.y() / len_in)
        v_out = QPointF(v_out.x() / len_out, v_out.y() / len_out)
        dot = v_in.x() * v_out.x() + v_in.y() * v_out.y()
        if abs(abs(dot) - 1.0) < 0.035:
            pp.lineTo(p_curr)
            continue
        rr = min(r_cap, len_in * 0.48, len_out * 0.48)
        if rr < 3.0:
            pp.lineTo(p_curr)
            continue
        corner_in = QPointF(p_curr.x() - v_in.x() * rr, p_curr.y() - v_in.y() * rr)
        corner_out = QPointF(p_curr.x() + v_out.x() * rr, p_curr.y() + v_out.y() * rr)
        pp.lineTo(corner_in)
        pp.quadTo(p_curr, corner_out)
    pp.lineTo(pts[-1])
    return pp


def _tangent_near_path_end(path: QPainterPath, back_px: float = 18.0) -> Tuple[QPointF, QPointF]:
    """Punto previo y final del trazado para orientar la flecha según la curva real."""
    length = path.length()
    if length < 1e-3:
        return QPointF(0.0, 0.0), QPointF(1.0, 0.0)
    end = path.pointAtPercent(1.0)
    t_back = min(0.45, back_px / length)
    before = path.pointAtPercent(max(0.0, 1.0 - t_back))
    dx = end.x() - before.x()
    dy = end.y() - before.y()
    if dx * dx + dy * dy < 2.25:
        before = path.pointAtPercent(max(0.0, 1.0 - 2.0 * t_back))
    return before, end


class FlowConnectionPainter:
    """
    Utilidad de pintado sobre un ``QPainter``: calcula polilinea de conexion (evitando tarjetas)
    y la dibuja con trazo redondeado, flecha alineada a la tangente del path y variante ciclica
    con resplandor. Los metodos publicos de interes para tests o reutilizacion son
    ``draw_connection``, ``calculate_smart_path`` y ``draw_grid``.
    """

    OBSTACLE_PAD = CONNECTOR_OBSTACLE_PAD
    EDGE_STUB = CONNECTOR_EDGE_STUB

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
        """
        Dibuja la arista entre dos tarjetas segun ``conn_type`` (normal o ciclica) y flags de ciclo.

        Args:
            all_widgets: Lista de tarjetas del canvas para obstaculos y orden de pintado.
        """
        if conn_type == "cyclic":
            self._draw_cyclic_connection(start_widget, end_widget, cyclic_flags, all_widgets)
        else:
            self._draw_normal_connection(start_widget, end_widget, all_widgets)

    def _draw_normal_connection(
        self, start_widget: QWidget, end_widget: QWidget, all_widgets: List[QWidget]
    ) -> None:
        """Conexión estándar: anclajes laterales y ruta ortogonal."""
        pen = QPen(QColor("#007bff"), 2, Qt.PenStyle.SolidLine)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        brush = QBrush(QColor("#007bff"))

        route_a, route_b = _anchors_by_vector(
            start_widget, end_widget, stub=self.EDGE_STUB
        )
        vis_a, vis_b = _visual_terminals_lateral(start_widget, end_widget)
        mid = self.calculate_smart_path(
            route_a, route_b, start_widget, end_widget, all_widgets
        )
        path_pts = _dedupe_consecutive_points([vis_a] + mid + [vis_b])

        self.painter.setBrush(brush)
        rounded = _orthogonal_polyline_to_rounded_path(path_pts, radius=14.0)
        self.painter.setPen(pen)
        self.painter.strokePath(rounded, pen)

        if len(path_pts) >= 2 and rounded.length() > 1e-3:
            p_before, p_tip = _tangent_near_path_end(rounded)
            self._draw_arrowhead(p_before, p_tip)

    def _draw_cyclic_connection(
        self,
        start_widget: QWidget,
        end_widget: QWidget,
        cyclic_flags: CanvasCyclicConnectionFlags,
        all_widgets: List[QWidget],
    ) -> None:
        """Conexión cíclica con efectos de brillo."""
        route_a, route_b = _cyclic_anchors(start_widget, end_widget, stub=self.EDGE_STUB)
        vis_a, vis_b = _visual_terminals_cyclic(start_widget, end_widget)
        mid = self.calculate_smart_path(
            route_a, route_b, start_widget, end_widget, all_widgets
        )
        path_pts = _dedupe_consecutive_points([vis_a] + mid + [vis_b])

        is_from_mother = cyclic_flags.is_from_mother
        is_to_mother = cyclic_flags.is_to_mother

        color_start = QColor(40, 167, 69)
        color_end = QColor(40, 167, 69)
        if is_from_mother:
            color_start, color_end = QColor(255, 200, 0), QColor(40, 167, 69)
        elif is_to_mother:
            color_start, color_end = QColor(40, 167, 69), QColor(255, 200, 0)

        rounded = _orthogonal_polyline_to_rounded_path(path_pts, radius=16.0)
        p0, p1 = path_pts[0], path_pts[-1]

        num_layers = 5
        for layer in range(num_layers, 0, -1):
            alpha = int(150 * (1 - layer / num_layers))
            pen_width = 4 + (layer * 2)
            self._stroke_rounded_path_gradient(rounded, p0, p1, color_start, color_end, alpha, pen_width)

        self._stroke_rounded_path_gradient(rounded, p0, p1, color_start, color_end, 255, 4)

        if len(path_pts) >= 2 and rounded.length() > 1e-3:
            self.painter.setBrush(QBrush(color_end))
            p_before, p_tip = _tangent_near_path_end(rounded, back_px=22.0)
            self._draw_arrowhead(p_before, p_tip, size=15)

    def _stroke_rounded_path_gradient(
        self,
        path_shape: QPainterPath,
        grad_start: QPointF,
        grad_end: QPointF,
        c1: QColor,
        c2: QColor,
        alpha: int,
        width: int,
    ) -> None:
        """Trazado suavizado con gradiente aproximado (eje inicio→fin del conector)."""
        gradient = QLinearGradient(grad_start, grad_end)
        gradient.setColorAt(0, QColor(c1.red(), c1.green(), c1.blue(), alpha))
        gradient.setColorAt(1, QColor(c2.red(), c2.green(), c2.blue(), alpha))
        pen = QPen(QBrush(gradient), width, Qt.PenStyle.SolidLine)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        self.painter.setPen(pen)
        self.painter.strokePath(path_shape, pen)

    def calculate_smart_path(
        self,
        start: QPointF,
        end: QPointF,
        sw: QWidget,
        ew: QWidget,
        all_widgets: List[QWidget],
    ) -> List[QPointF]:
        """
        Calcula la polilinea de enrutamiento entre ``start`` y ``end`` (puntos ya desplazados con stub).

        Returns:
            Lista de ``QPointF`` sin los terminales visuales en borde de celda; el llamador que
            dibuja suele anteponer/sufijar ``_visual_terminals_*``.
        """
        obstacles = self._obstacle_rects(all_widgets, sw, ew, pad=self.OBSTACLE_PAD)
        routed = self._route_manhattan(start, end, obstacles, grid=12)
        return self._simplify_polyline(routed)

    def _obstacle_rects(
        self, all_widgets: List[QWidget], sw: QWidget, ew: QWidget, pad: int
    ) -> List[QRect]:
        """Todas las tarjetas visibles son obstáculos; origen y destino también (los anclajes quedan fuera con EDGE_STUB)."""
        seen: set[int] = set()
        out: List[QRect] = []
        for w in (sw, ew, *all_widgets):
            if w is None:
                continue
            wid = id(w)
            if wid in seen:
                continue
            vis = getattr(w, "isVisible", None)
            if callable(vis) and not vis():
                continue
            geom_fn = getattr(w, "geometry", None)
            if not callable(geom_fn):
                continue
            try:
                g = geom_fn()
            except (AttributeError, RuntimeError, TypeError):
                continue
            if not hasattr(g, "adjusted"):
                continue
            seen.add(wid)
            out.append(g.adjusted(-pad, -pad, pad, pad))
        return out

    def _segment_clear(self, p: QPointF, q: QPointF, obstacles: List[QRect]) -> bool:
        line = QLineF(p, q)
        for obs in obstacles:
            if self._line_intersects_rect(line, obs):
                return False
        return True

    def _path_clear(self, pts: List[QPointF], obstacles: List[QRect]) -> bool:
        for i in range(len(pts) - 1):
            if not self._segment_clear(pts[i], pts[i + 1], obstacles):
                return False
        return True

    def _prefer_orthogonal_elbow(
        self, a: QPointF, b: QPointF, obstacles: List[QRect], grid: int
    ) -> Optional[List[QPointF]]:
        """
        Aunque el segmento A–B sea libre, propone un trazado en L o con «jog» para que
        siempre haya codos visibles (las tarjetas alineadas no dejan línea recta única).
        """
        ax, ay = float(a.x()), float(a.y())
        bx, by = float(b.x()), float(b.y())
        dx = bx - ax
        dy = by - ay
        if abs(dx) + abs(dy) < 18.0:
            return None

        def snap(v: float) -> float:
            return round(v / grid) * grid

        mid_x = (ax + bx) / 2.0
        mid_y = (ay + by) / 2.0
        candidates: List[List[QPointF]] = []

        # L horizontal: hace falta desnivel Y y recorrido X (si no, colapsa en línea recta).
        if abs(dy) > 6.0 and abs(dx) > 16.0:
            candidates.append([a, QPointF(mid_x, ay), QPointF(mid_x, by), b])
            candidates.append([a, QPointF(snap(mid_x), ay), QPointF(snap(mid_x), by), b])
        # L vertical: análogo (si ay≈by no usar este patrón).
        if abs(dx) > 6.0 and abs(dy) > 16.0:
            candidates.append([a, QPointF(ax, mid_y), QPointF(bx, mid_y), b])
            candidates.append([a, QPointF(ax, snap(mid_y)), QPointF(bx, snap(mid_y)), b])

        jog = max(float(grid * 2), 26.0)
        if abs(dy) <= 8.0 and abs(dx) > 32.0:
            for sign in (-1.0, 1.0):
                jy = ay + sign * jog
                candidates.append([a, QPointF(mid_x, ay), QPointF(mid_x, jy), QPointF(bx, jy), b])
                candidates.append(
                    [a, QPointF(snap(mid_x), ay), QPointF(snap(mid_x), jy), QPointF(bx, jy), b]
                )
        if abs(dx) <= 8.0 and abs(dy) > 32.0:
            for sign in (-1.0, 1.0):
                jx = ax + sign * jog
                candidates.append([a, QPointF(ax, mid_y), QPointF(jx, mid_y), QPointF(jx, by), b])
                candidates.append(
                    [a, QPointF(ax, snap(mid_y)), QPointF(jx, snap(mid_y)), QPointF(jx, by), b]
                )

        for path in candidates:
            if self._path_clear(path, obstacles):
                return path
        return None

    def _route_manhattan(
        self, a: QPointF, b: QPointF, obstacles: List[QRect], grid: int
    ) -> List[QPointF]:
        if (a - b).manhattanLength() < 0.5:
            return [a]

        direct_clear = self._segment_clear(a, b, obstacles)
        if direct_clear:
            elbow = self._prefer_orthogonal_elbow(a, b, obstacles, grid)
            if elbow is not None:
                return elbow
            return [a, b]

        mid_x = (a.x() + b.x()) / 2.0
        mid_y = (a.y() + b.y()) / 2.0

        def unique_sorted_offsets(center: float, step: int, spreads: tuple[int, ...]) -> List[float]:
            seen: set[float] = set()
            raw: List[float] = []
            for k in range(-45, 46):
                raw.append(center + k * step)
            for spread in spreads:
                lo = int(center - spread)
                hi = int(center + spread)
                t = lo
                while t <= hi:
                    raw.append(float(t))
                    t += step
            for v in raw:
                if v not in seen:
                    seen.add(v)
            return sorted(seen, key=lambda z: abs(z - center))

        x_candidates = unique_sorted_offsets(mid_x, grid, (360, 600, 900))
        y_candidates = unique_sorted_offsets(mid_y, grid, (360, 600, 900))

        for xm in x_candidates:
            path = [a, QPointF(xm, a.y()), QPointF(xm, b.y()), b]
            if self._path_clear(path, obstacles):
                return path

        for ym in y_candidates:
            path = [a, QPointF(a.x(), ym), QPointF(b.x(), ym), b]
            if self._path_clear(path, obstacles):
                return path

        # Desvío en U: tres tramos horizontales (útil cuando el segmento vertical central choca)
        margin_u = float(grid * 3)
        y_low = min(a.y(), b.y()) - margin_u
        y_high = max(a.y(), b.y()) + margin_u
        for y_detour in (y_low, y_high):
            path = [
                a,
                QPointF(a.x(), y_detour),
                QPointF(b.x(), y_detour),
                b,
            ]
            if self._path_clear(path, obstacles):
                return path

        x_left = min(a.x(), b.x()) - margin_u
        x_right = max(a.x(), b.x()) + margin_u
        for x_detour in (x_left, x_right):
            path = [
                a,
                QPointF(x_detour, a.y()),
                QPointF(x_detour, b.y()),
                b,
            ]
            if self._path_clear(path, obstacles):
                return path

        return [a, b]

    def _simplify_polyline(self, pts: List[QPointF]) -> List[QPointF]:
        if len(pts) < 3:
            return pts
        out: List[QPointF] = [pts[0]]
        for i in range(1, len(pts) - 1):
            p0, p1, p2 = out[-1], pts[i], pts[i + 1]
            cross = (p1.x() - p0.x()) * (p2.y() - p0.y()) - (p1.y() - p0.y()) * (p2.x() - p0.x())
            if abs(cross) < 1e-3:
                continue
            out.append(p1)
        out.append(pts[-1])
        return out

    def _count_collisions(self, path: List[QPointF], obstacles: List[Any]) -> int:
        count = 0
        for i in range(len(path) - 1):
            line = QLineF(path[i], path[i + 1])
            for obs in obstacles:
                if self._line_intersects_rect(line, obs):
                    count += 1
                    break
        return count

    def _line_intersects_rect(self, line: QLineF, rect: Any) -> bool:
        if rect.contains(line.p1().toPoint()) or rect.contains(line.p2().toPoint()):
            return True
        for edge_points in [
            (rect.topLeft(), rect.topRight()),
            (rect.bottomLeft(), rect.bottomRight()),
            (rect.topLeft(), rect.bottomLeft()),
            (rect.topRight(), rect.bottomRight()),
        ]:
            edge = QLineF(QPointF(edge_points[0]), QPointF(edge_points[1]))
            if line.intersects(edge)[0] == QLineF.IntersectionType.BoundedIntersection:
                return True
        return False

    def _avoid_obstacles(self, path: List[QPointF], obstacles: List[Any], grid: int) -> List[QPointF]:
        if len(path) != 3:
            return path
        s, m, e = path[0], path[1], path[2]
        is_h = abs(m.x() - s.x()) > abs(m.y() - s.y())

        for offset in [grid * i for i in range(-5, 6) if i != 0]:
            if is_h:
                adj = [s, QPointF(m.x(), m.y() + offset), QPointF(e.x(), m.y() + offset), e]
            else:
                adj = [s, QPointF(m.x() + offset, m.y()), QPointF(m.x() + offset, e.y()), e]
            if self._count_collisions(adj, obstacles) == 0:
                return adj
        return path

    def _draw_arrowhead(self, p1: QPointF, p2: QPointF, size: int = 10) -> None:
        angle = math.atan2(p2.y() - p1.y(), p2.x() - p1.x())
        p3 = p2 - QPointF(math.cos(angle + math.pi / 6) * size, math.sin(angle + math.pi / 6) * size)
        p4 = p2 - QPointF(math.cos(angle - math.pi / 6) * size, math.sin(angle - math.pi / 6) * size)
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
