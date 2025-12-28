# -*- coding: utf-8 -*-
from .base import *
from PyQt6.QtWidgets import QToolTip

class TimelineVisualizationWidget(QWidget):
    """Widget que dibuja un diagrama de Gantt interactivo y detallado."""
    task_selected = pyqtSignal(dict, list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.results = []
        self.audit = []
        self.tasks = []
        self.task_rects = []
        self.start_time = datetime.now()
        self.total_days = 7
        self.padding_left = 50
        self.padding_top = 80
        self.padding_bottom = 20
        self.bar_height = 30
        self.row_gap = 10
        self.setMouseTracking(True)

    def setData(self, results, audit):
        self.results = sorted(results, key=lambda x: x['Inicio'])
        self.audit = audit
        if results:
            min_start = min(r['Inicio'] for r in results)
            max_end = max(r['Fin'] for r in results)
            self.start_time = min_start.replace(hour=0, minute=0, second=0, microsecond=0)
            self.total_days = max(1, (max_end - self.start_time).days + 1)
        else:
            self.start_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            self.total_days = 1
        self.update()

    def paintEvent(self, event):
        if not self.results:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        pixels_per_day = (self.width() - self.padding_left - 20) / max(1, self.total_days)
        
        self._draw_time_axis(painter, pixels_per_day)
        self._draw_tasks(painter, pixels_per_day)
        self._draw_dependencies(painter)

    def _draw_time_axis(self, painter, pixels_per_day):
        painter.setPen(QColor("#adb5bd"))
        font = painter.font()
        font.setPointSize(8)
        painter.setFont(font)

        last_month = -1
        for day_index in range(self.total_days + 1):
            x_pos = self.padding_left + day_index * pixels_per_day
            current_date = self.start_time.date() + timedelta(days=day_index)

            if current_date.month != last_month:
                last_month = current_date.month
                painter.setPen(QPen(QColor("#007bff"), 1, Qt.PenStyle.DashLine))
                painter.drawLine(int(x_pos), self.padding_top - 10, int(x_pos), self.height() - self.padding_bottom)

                month_font = painter.font()
                month_font.setBold(True)
                painter.setFont(month_font)
                painter.setPen(QColor("#007bff"))
                painter.drawText(QRect(int(x_pos) + 5, self.padding_top - 45, 100, 20), Qt.AlignmentFlag.AlignLeft,
                                 current_date.strftime("%B %Y"))
                painter.setFont(font)

            elif current_date.weekday() >= 5:
                painter.setPen(QPen(QColor("#e63946"), 1, Qt.PenStyle.DotLine))
                painter.drawLine(int(x_pos), self.padding_top - 5, int(x_pos), self.height() - self.padding_bottom)

            date_str = current_date.strftime("%d/%m")
            painter.setPen(QColor("#adb5bd"))
            painter.drawText(QRect(int(x_pos) - 20, self.padding_top - 30, 40, 20), Qt.AlignmentFlag.AlignCenter,
                             date_str)

    def _draw_tasks(self, painter, pixels_per_day):
        self.task_rects.clear()
        font = painter.font()
        font.setPointSize(9)
        painter.setFont(font)

        y_pos = self.padding_top
        for i, task in enumerate(self.results):
            task_audit = [d for d in self.audit if d.task_name == task['Tarea']]
            has_warning = any(d.status.value == 'WARNING' for d in task_audit)
            color = QColor("#ffc107") if has_warning else QColor("#28a745")

            start_offset_days = (task['Inicio'] - self.start_time).total_seconds() / (24 * 3600)
            duration_days = (task['Fin'] - task['Inicio']).total_seconds() / (24 * 3600)

            rect_x = self.padding_left + (start_offset_days * pixels_per_day)
            rect_y = y_pos + (i * (self.bar_height + self.row_gap))
            rect_width = duration_days * pixels_per_day

            task_rect = QRect(int(rect_x), int(rect_y), int(rect_width), self.bar_height)
            self.task_rects.append((task_rect, task, task_audit))

            painter.setBrush(QBrush(color.lighter(120)))
            painter.setPen(QPen(color, 2))
            painter.drawRoundedRect(task_rect, 5, 5)

            painter.setPen(Qt.GlobalColor.black)
            workers_str = ", ".join(task['Trabajador Asignado'])
            display_text = f"{task['Tarea']} ({workers_str})"
            painter.drawText(task_rect.adjusted(5, 0, -5, 0),
                             Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, display_text)

        self.setMinimumHeight(int(y_pos + len(self.results) * (self.bar_height + self.row_gap) + self.padding_bottom))

    def _draw_dependencies(self, painter):
        painter.setPen(QPen(QColor("#023e8a"), 2, Qt.PenStyle.SolidLine))
        painter.setBrush(QBrush(QColor("#023e8a")))

        for i, task_data in enumerate(self.results):
            parent_index = task_data.get('Parent Index')
            if parent_index is not None and 0 <= parent_index < len(self.results):
                parent_rect, _, _ = self.task_rects[parent_index]
                child_rect, _, _ = self.task_rects[i]

                start_point = QPoint(parent_rect.right(), parent_rect.center().y())
                end_point = QPoint(child_rect.left(), child_rect.center().y())

                painter.drawLine(start_point, end_point)
                self._draw_arrowhead(painter, start_point, end_point)

    def _draw_arrowhead(self, painter, p1, p2, size=10):
        from math import atan2, cos, sin, pi
        angle = atan2(p2.y() - p1.y(), p2.x() - p1.x())
        p3 = QPoint(int(p2.x() - size * cos(angle + pi / 6)), int(p2.y() - size * sin(angle + pi / 6)))
        p4 = QPoint(int(p2.x() - size * cos(angle - pi / 6)), int(p2.y() - size * sin(angle - pi / 6)))
        painter.drawPolygon(p2, p3, p4)

    def mousePressEvent(self, event):
        for rect, task, audit in self.task_rects:
            if rect.contains(event.pos()):
                self.task_selected.emit(task, audit)
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        found_task = False
        for rect, task, audit in self.task_rects:
            if rect.contains(event.pos()):
                tooltip_text = f"""
                <b>{task['Tarea']}</b><br>
                <b>Inicio:</b> {task['Inicio'].strftime('%d/%m %H:%M')}<br>
                <b>Fin:</b> {task['Fin'].strftime('%d/%m %H:%M')}<br>
                <b>Duración:</b> {task['Duracion (min)']:.1f} min<br>
                <hr>
                <b>Eventos Clave:</b><br>
                """
                event_count = 0
                for decision in audit:
                    if decision.status.value in ['WARNING', 'POSITIVE'] or decision.icon == '🛠':
                        tooltip_text += f" • {decision.icon} {decision.user_friendly_reason}<br>"
                        event_count += 1
                        if event_count >= 3:
                            break
                QToolTip.showText(event.globalPosition().toPoint(), tooltip_text, self)
                found_task = True
                break
        if not found_task:
            QToolTip.hideText()
        super().mouseMoveEvent(event)

    def clear(self):
        self.results = []
        self.tasks = []
        self.update()


class TaskAnalysisPanel(QWidget):
    """Widget que muestra el detalle de una tarea seleccionada."""

    def __init__(self, parent=None):
        super().__init__(parent)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        self.header_label = QLabel("Seleccione una tarea del gráfico")
        font = self.header_label.font()
        font.setPointSize(16)
        font.setBold(True)
        self.header_label.setFont(font)
        self.header_label.setWordWrap(True)

        log_frame = QFrame()
        log_frame.setFrameShape(QFrame.Shape.StyledPanel)
        log_layout = QVBoxLayout(log_frame)
        log_title = QLabel("<b>Log de Decisiones del Cálculo</b>")

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        self.log_content_widget = QWidget()
        self.log_vbox = QVBoxLayout(self.log_content_widget)
        self.log_vbox.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll_area.setWidget(self.log_content_widget)

        log_layout.addWidget(log_title)
        log_layout.addWidget(scroll_area)

        main_layout.addWidget(self.header_label)
        main_layout.addWidget(log_frame, 1)

    def displayTask(self, task_data, task_audit):
        while self.log_vbox.count():
            child = self.log_vbox.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        has_warning = any(d.status.value == 'WARNING' for d in task_audit)
        if has_warning:
            self.header_label.setText(f"Tarea '{task_data['Tarea']}': Requiere Atención ⚠️")
            self.header_label.setStyleSheet("color: #d97706;")
        else:
            self.header_label.setText(f"Tarea '{task_data['Tarea']}': OK ✅")
            self.header_label.setStyleSheet("color: #166534;")

        if not task_audit:
            self.log_vbox.addWidget(QLabel("No hay detalles de auditoría para esta tarea."))
            return

        for decision in sorted(task_audit, key=lambda d: d.timestamp):
            log_line = f"{decision.icon} <b>{decision.user_friendly_reason}</b>"
            color = "#6b7280"
            if decision.status == 'POSITIVE':
                color = "#16a34a"
            elif decision.status == 'WARNING':
                color = "#f59e0b"

            label = QLabel(log_line)
            label.setStyleSheet(f"color: {color}; font-size: 14px;")
            label.setWordWrap(True)
            self.log_vbox.addWidget(label)

        self.log_vbox.addStretch()
