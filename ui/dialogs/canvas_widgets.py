# =================================================================================
# ui/dialogs/canvas_widgets.py
# Contiene los widgets de canvas y tarjetas para el flujo de producción.
# =================================================================================
import math

from PyQt6.QtWidgets import QWidget, QLabel
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QPointF, QLineF
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QPolygonF, QLinearGradient


class CanvasWidget(QWidget):
    """
    Un widget personalizado que actúa como un canvas para arrastrar, soltar y visualizar
    las tareas del flujo de producción.
    """
    def __init__(self, parent_dialog):
        super().__init__(parent_dialog)
        self.parent_dialog = parent_dialog
        self.setAcceptDrops(True)
        # Usamos la paleta del sistema para el fondo, para que se adapte al modo oscuro/claro
        self.setStyleSheet("""
            background-color: palette(base); 
            border: 1px solid #dee2e6;
        """)

        # Guardará una lista de tuplas: (widget_origen, widget_destino)
        self.connections = []

    def set_connections(self, new_connections):
        """
        Recibe la lista de conexiones desde el diálogo principal y fuerza un redibujado.
        """
        self.connections = new_connections
        self.update()  # Muy importante: Llama a paintEvent para redibujar el widget

    def dragEnterEvent(self, event):
        event.acceptProposedAction()

    def dragMoveEvent(self, event):
        event.acceptProposedAction()

    def dropEvent(self, event):
        task_data = event.source().currentItem().data(0, Qt.ItemDataRole.UserRole)
        drop_position = event.position().toPoint()
        # Explicitly pass skip_confirmation=False to always validate duplicates on drop
        self.parent_dialog._add_task_to_canvas(task_data, drop_position, skip_confirmation=False)
        event.acceptProposedAction()

    def paintEvent(self, event):
        """
        Este método se llama automáticamente cada vez que el widget necesita ser redibujado.
        Dibuja el grid de fondo y las conexiones inteligentes con el estilo adecuado según su tipo.
        """
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # ✨ Dibujar el grid ANTES que las conexiones
        self._draw_grid(painter)

        # Iteramos sobre la lista de diccionarios de conexión
        for connection in self.connections:
            start_widget = connection['start']
            end_widget = connection['end']
            conn_type = connection['type']

            # ✨ Elegir el estilo y los puntos de anclaje según el tipo
            if conn_type == 'cyclic':
                # Conectar desde la parte inferior central a la superior central
                start_point = QPointF(start_widget.geometry().center().x(), start_widget.geometry().bottom())
                end_point = QPointF(end_widget.geometry().center().x(), end_widget.geometry().top())

                # ✨ NUEVO: Determinar si es una flecha desde tarea madre o hacia tarea madre
                start_task_index = self._get_task_index_by_widget(start_widget)
                end_task_index = self._get_task_index_by_widget(end_widget)

                is_from_mother = False
                is_to_mother = False

                if start_task_index is not None:
                    start_config = self.parent_dialog.canvas_tasks[start_task_index].get('config', {})
                    is_from_mother = start_config.get('is_cycle_start', False)

                if end_task_index is not None:
                    end_config = self.parent_dialog.canvas_tasks[end_task_index].get('config', {})
                    is_to_mother = end_config.get('is_cycle_start', False)

                # ✨ NUEVO: Dibujar flecha cíclica con efecto neón y gradiente
                self._draw_cyclic_arrow_with_glow(
                    painter, start_point, end_point,
                    start_widget, end_widget,
                    is_from_mother, is_to_mother
                )

            else:  # Por defecto, es una dependencia normal
                # Estilo para dependencias: Azul, sólido, de derecha a izquierda
                pen = QPen(QColor("#007bff"), 2, Qt.PenStyle.SolidLine)
                brush = QBrush(QColor("#007bff"))
                # Conectar desde el centro derecho al centro izquierdo
                start_point = QPointF(start_widget.geometry().right(), start_widget.geometry().center().y())
                end_point = QPointF(end_widget.geometry().left(), end_widget.geometry().center().y())

                painter.setPen(pen)
                painter.setBrush(brush)

                # Calcular ruta inteligente siguiendo el grid
                smart_path = self._calculate_smart_path(start_point, end_point, start_widget, end_widget)

                # Dibujar la ruta completa (múltiples segmentos)
                for i in range(len(smart_path) - 1):
                    painter.drawLine(smart_path[i], smart_path[i + 1])

                # Dibujar la punta de flecha en el último segmento
                if len(smart_path) >= 2:
                    self._draw_arrowhead(painter, smart_path[-2], smart_path[-1])

    def _get_task_index_by_widget(self, widget):
        """Obtiene el índice de una tarea por su widget."""
        for i, task in enumerate(self.parent_dialog.canvas_tasks):
            if task.get('widget') == widget:
                return i
        return None

    def _draw_cyclic_arrow_with_glow(self, painter, start_point, end_point, start_widget, end_widget, is_from_mother,
                                     is_to_mother):
        """
        Dibuja una flecha cíclica con efecto neón y gradiente de color.
        """
        # Calcular ruta inteligente
        smart_path = self._calculate_smart_path(start_point, end_point, start_widget, end_widget)

        # ✨ Crear gradiente de color según el tipo de conexión
        if is_from_mother:
            # Desde tarea madre: dorado → verde
            color_start = QColor(255, 200, 0)  # Dorado
            color_end = QColor(40, 167, 69)  # Verde
        elif is_to_mother:
            # Hacia tarea madre: verde → dorado
            color_start = QColor(40, 167, 69)  # Verde
            color_end = QColor(255, 200, 0)  # Dorado
        else:
            # Normal: verde sólido
            color_start = QColor(40, 167, 69)
            color_end = QColor(40, 167, 69)

        # ✨ Dibujar efecto neón (capas de resplandor)
        num_glow_layers = 5
        for layer in range(num_glow_layers, 0, -1):
            alpha = int(150 * (1 - layer / num_glow_layers))
            pen_width = 4 + (layer * 2)  # Grosor base 4, aumenta por capa

            # Aplicar gradiente a cada segmento
            for i in range(len(smart_path) - 1):
                p1 = smart_path[i]
                p2 = smart_path[i + 1]

                # Crear gradiente para este segmento
                gradient = QLinearGradient(p1, p2)

                # Aplicar colores con alpha ajustado
                start_with_alpha = QColor(color_start.red(), color_start.green(), color_start.blue(), alpha)
                end_with_alpha = QColor(color_end.red(), color_end.green(), color_end.blue(), alpha)

                gradient.setColorAt(0, start_with_alpha)
                gradient.setColorAt(1, end_with_alpha)

                pen = QPen(QBrush(gradient), pen_width, Qt.PenStyle.SolidLine)
                pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                painter.setPen(pen)

                painter.drawLine(p1, p2)

        # ✨ Dibujar línea central sólida (más brillante)
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

        # Dibujar punta de flecha con el color final
        if len(smart_path) >= 2:
            painter.setBrush(QBrush(color_end))
            self._draw_arrowhead(painter, smart_path[-2], smart_path[-1], size=15)

    def _draw_grid(self, painter):
        """
        Dibuja una cuadrícula de fondo tipo papel milimétrico.
        """
        # Tamaño de la cuadrícula (ajustable)
        grid_size = 20

        # Color del grid (gris muy claro, casi transparente)
        grid_color = QColor(200, 200, 200, 80)  # RGBA con alpha bajo

        # Configurar el pincel para líneas finas
        painter.setPen(QPen(grid_color, 1, Qt.PenStyle.SolidLine))

        # Obtener dimensiones del canvas
        width = self.width()
        height = self.height()

        # Dibujar líneas verticales
        x = 0
        while x <= width:
            painter.drawLine(x, 0, x, height)
            x += grid_size

        # Dibujar líneas horizontales
        y = 0
        while y <= height:
            painter.drawLine(0, y, width, y)
            y += grid_size

    def _calculate_smart_path(self, start_point, end_point, start_widget, end_widget):
        """
        Calcula una ruta inteligente siguiendo el grid entre dos puntos,
        evitando pasar por detrás de tarjetas.
        """
        grid_size = 20

        # Ajustar puntos al grid más cercano
        start_x = round(start_point.x() / grid_size) * grid_size
        start_y = round(start_point.y() / grid_size) * grid_size
        end_x = round(end_point.x() / grid_size) * grid_size
        end_y = round(end_point.y() / grid_size) * grid_size

        # Obtener rectángulos de todas las tarjetas (excepto start y end)
        obstacles = []
        for task in self.parent_dialog.canvas_tasks:
            widget = task.get('widget')
            if widget and widget != start_widget and widget != end_widget:
                # Expandir el rectángulo un poco para dar margen
                rect = widget.geometry()
                expanded_rect = rect.adjusted(-10, -10, 10, 10)
                obstacles.append(expanded_rect)

        # Intentar ruta en L (horizontal primero, luego vertical)
        path1 = [
            QPointF(start_x, start_y),
            QPointF(end_x, start_y),
            QPointF(end_x, end_y)
        ]

        # Intentar ruta en L inversa (vertical primero, luego horizontal)
        path2 = [
            QPointF(start_x, start_y),
            QPointF(start_x, end_y),
            QPointF(end_x, end_y)
        ]

        # Comprobar cuál ruta tiene menos colisiones
        collisions1 = self._count_path_collisions(path1, obstacles)
        collisions2 = self._count_path_collisions(path2, obstacles)

        if collisions1 <= collisions2:
            # Si path1 tiene colisiones, intentar desplazarla
            if collisions1 > 0:
                return self._adjust_path_to_avoid_obstacles(path1, obstacles, grid_size)
            return path1
        else:
            # Si path2 tiene colisiones, intentar desplazarla
            if collisions2 > 0:
                return self._adjust_path_to_avoid_obstacles(path2, obstacles, grid_size)
            return path2

    def _count_path_collisions(self, path, obstacles):
        """Cuenta cuántos segmentos del path colisionan con obstáculos."""
        collisions = 0
        for i in range(len(path) - 1):
            p1 = path[i]
            p2 = path[i + 1]

            # Crear línea del segmento
            line = QLineF(p1, p2)

            # Comprobar intersección con cada obstáculo
            for obstacle in obstacles:
                if self._line_intersects_rect(line, obstacle):
                    collisions += 1
                    break  # Contar solo una vez por segmento

        return collisions

    def _line_intersects_rect(self, line, rect):
        """Comprueba si una línea intersecta con un rectángulo."""
        # ✨ CORRECCIÓN: Convertir QPoint a QPointF y usar sintaxis correcta de intersects()
        top = QLineF(
            QPointF(rect.topLeft()),
            QPointF(rect.topRight())
        )
        bottom = QLineF(
            QPointF(rect.bottomLeft()),
            QPointF(rect.bottomRight())
        )
        left = QLineF(
            QPointF(rect.topLeft()),
            QPointF(rect.bottomLeft())
        )
        right = QLineF(
            QPointF(rect.topRight()),
            QPointF(rect.bottomRight())
        )

        # Comprobar intersección con cada lado
        # En PyQt6, intersects() devuelve una tupla (tipo_intersección, punto)
        for rect_line in [top, bottom, left, right]:
            result = line.intersects(rect_line)
            if result[0] == QLineF.IntersectionType.BoundedIntersection:
                return True

        # También comprobar si algún punto del segmento está dentro del rectángulo
        if rect.contains(line.p1().toPoint()) or rect.contains(line.p2().toPoint()):
            return True

        return False

    def _adjust_path_to_avoid_obstacles(self, path, obstacles, grid_size):
        """
        Intenta ajustar el path para evitar obstáculos desplazándolo verticalmente.
        """
        if len(path) != 3:
            return path

        start = path[0]
        middle = path[1]
        end = path[2]

        # Determinar si es ruta horizontal-vertical o vertical-horizontal
        if abs(middle.x() - start.x()) > abs(middle.y() - start.y()):
            # Ruta horizontal primero
            # Intentar desplazar verticalmente el punto medio
            offsets = [grid_size * i for i in range(-5, 6) if i != 0]

            for offset in offsets:
                new_middle_y = middle.y() + offset
                adjusted_path = [
                    start,
                    QPointF(middle.x(), new_middle_y),
                    QPointF(end.x(), new_middle_y),
                    end
                ]

                if self._count_path_collisions(adjusted_path, obstacles) == 0:
                    return adjusted_path
        else:
            # Ruta vertical primero
            # Intentar desplazar horizontalmente el punto medio
            offsets = [grid_size * i for i in range(-5, 6) if i != 0]

            for offset in offsets:
                new_middle_x = middle.x() + offset
                adjusted_path = [
                    start,
                    QPointF(new_middle_x, middle.y()),
                    QPointF(new_middle_x, end.y()),
                    end
                ]

                if self._count_path_collisions(adjusted_path, obstacles) == 0:
                    return adjusted_path

        # Si no se puede evitar, devolver el path original
        return path

    def _draw_arrowhead(self, painter, p1, p2, size=10):
        """Función auxiliar para dibujar la punta de una flecha (sin cambios lógicos)."""
        angle = math.atan2(p2.y() - p1.y(), p2.x() - p1.x())

        # Puntos para formar el triángulo de la punta de flecha
        p3 = p2 - QPointF(math.cos(angle + math.pi / 6) * size,
                          math.sin(angle + math.pi / 6) * size)
        p4 = p2 - QPointF(math.cos(angle - math.pi / 6) * size,
                          math.sin(angle - math.pi / 6) * size)

        arrow_head = QPolygonF([p2, p3, p4])
        painter.drawPolygon(arrow_head)

    def mousePressEvent(self, event):
        """Detecta clics en el canvas (fondo) para ocultar el inspector."""
        # Verificar si el clic fue en el fondo (no en una tarjeta CardWidget)
        # self.childAt() devuelve el widget hijo en esa posición, o None si no hay ninguno.
        clicked_widget = self.childAt(event.position().toPoint())

        # Si no se hizo clic en ningún widget hijo (clicked_widget es None)
        # O si se hizo clic directamente en el propio CanvasWidget (clicked_widget es self)
        # entonces consideramos que se hizo clic en el fondo.
        if clicked_widget is None or clicked_widget == self:
            # Llamamos a la función para ocultar el inspector en el diálogo padre
            self.parent_dialog._hide_inspector_panel()

        # Llamamos al método original para no interferir con otros eventos de ratón
        # (como iniciar el arrastre de una tarjeta si se hace clic en ella)
        super().mousePressEvent(event)


class CardWidget(QLabel):
    """
    Una tarjeta visual y MOVIBLE que representa una tarea en el canvas.
    Emite 'clicked' al ser seleccionada y 'moved' al ser movida.
    """
    # Señal para cuando se hace clic para seleccionar la tarjeta
    clicked = pyqtSignal(dict)
    # Nueva señal para notificar al diálogo principal que la tarjeta se ha movido
    moved = pyqtSignal()

    def __init__(self, task_data, parent):
        super().__init__(parent)
        self.task_data = task_data
        # Accedemos al diálogo principal a través de la jerarquía de parents
        # self.parent() es el CanvasWidget, self.parent().parent_dialog es el EnhancedProductionFlowDialog
        self.parent_dialog = self.parent().parent_dialog

        self.setText(f"<b>{self.task_data['name']}</b>\n<small>{self.task_data['duration']:.2f} min</small>")
        self.setFixedSize(180, 60)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setWordWrap(True)

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

        # Atributos para gestionar el arrastre
        self.dragging = False
        self.drag_start_position = QPoint()

    def mousePressEvent(self, event):
        """Se activa al hacer clic en la tarjeta."""
        # Emitimos la señal para que el inspector se actualice
        self.clicked.emit(self.task_data)

        # Si se hace clic con el botón izquierdo, iniciamos el arrastre
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            # Guardamos la posición del clic RELATIVA a la tarjeta
            self.drag_start_position = event.position().toPoint()

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Se activa al mover el ratón mientras se mantiene presionado."""
        if self.dragging:
            # Calculamos la nueva posición de la tarjeta y la movemos
            new_pos = self.mapToParent(event.position().toPoint() - self.drag_start_position)
            self.move(new_pos)
            # Forzamos el redibujado de las conexiones MIENTRAS se arrastra
            self.parent_dialog._update_canvas_connections()

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Se activa al soltar el botón del ratón."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False

            # ✨ NUEVO: Ajustar posición al grid más cercano
            self._snap_to_grid()

            # Emitimos la señal para confirmar que el movimiento ha terminado
            self.moved.emit()

        super().mouseReleaseEvent(event)

    def _snap_to_grid(self):
        """
        Ajusta la posición de la tarjeta al punto más cercano de la cuadrícula.
        """
        grid_size = 20  # Debe coincidir con el tamaño del grid en CanvasWidget

        # Obtener posición actual
        current_x = self.x()
        current_y = self.y()

        # Calcular la posición más cercana en el grid
        snapped_x = round(current_x / grid_size) * grid_size
        snapped_y = round(current_y / grid_size) * grid_size

        # Mover la tarjeta a la nueva posición
        self.move(snapped_x, snapped_y)
