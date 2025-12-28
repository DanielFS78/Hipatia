# -*- coding: utf-8 -*-
from .base import *

class DashboardWidget(QWidget):
    """Widget para mostrar gráficos y estadísticas de producción."""

    def __init__(self, controller=None):
        super().__init__()
        self.controller = controller
        self.machine_chart_view = None
        self.worker_chart_view = None
        self.components_chart_view = None
        self.activity_chart_view = None
        self.setup_ui()

    def set_controller(self, controller):
        """Asigna el controlador al widget."""
        self.controller = controller

    def setup_ui(self):
        """Configura la interfaz del dashboard."""
        main_layout = QGridLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)

        self.machine_chart_view = self._create_chart_view("Uso de Máquinas")
        self.worker_chart_view = self._create_chart_view("Carga de Trabajo por Operario")
        self.components_chart_view = self._create_chart_view("Componentes en Iteraciones")
        self.activity_chart_view = self._create_chart_view("Actividad Mensual (Último Año)")

        main_layout.addWidget(self.machine_chart_view, 0, 0)
        main_layout.addWidget(self.worker_chart_view, 0, 1)
        main_layout.addWidget(self.components_chart_view, 1, 0)
        main_layout.addWidget(self.activity_chart_view, 1, 1)

    def _create_chart_view(self, title):
        """Función auxiliar para crear un QChartView con un título."""
        chart = QChart()
        chart.setTitle(title)
        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        return chart_view

    def update_machine_usage(self, data):
        """Actualiza el gráfico de uso de máquinas."""
        series = QBarSeries()
        bar_set = QBarSet("Minutos Totales")
        colors = [QColor("#3498db"), QColor("#2ecc71"), QColor("#f1c40f"), QColor("#e74c3c"), QColor("#9b59b6")]
        for i, (name, minutes) in enumerate(data):
            bar_set.append(minutes)
            bar_set.setBrush(colors[i % len(colors)])
        series.append(bar_set)

        chart = self.machine_chart_view.chart()
        chart.removeAllSeries()
        chart.addSeries(series)
        chart.createDefaultAxes()
        chart.legend().setVisible(False)

    def update_worker_load(self, data):
        """Actualiza el gráfico de carga de trabajo."""
        series = QBarSeries()
        bar_set = QBarSet("Minutos Totales")
        colors = [QColor("#2ecc71"), QColor("#f1c40f"), QColor("#e74c3c"), QColor("#9b59b6"), QColor("#3498db")]
        for i, (name, minutes) in enumerate(data):
            bar_set.append(minutes)
            bar_set.setBrush(colors[i % len(colors)])
        series.append(bar_set)

        chart = self.worker_chart_view.chart()
        chart.removeAllSeries()
        chart.addSeries(series)
        chart.createDefaultAxes()
        chart.legend().setVisible(False)

    def update_problematic_components(self, data):
        """Actualiza el gráfico de componentes problemáticos."""
        series = QPieSeries()
        for item in data:
            if hasattr(item, 'codigo_componente') and hasattr(item, 'frecuencia'):
                 name = item.codigo_componente
                 frequency = item.frecuencia
            else:
                 name, frequency = item
            series.append(f"{name} ({frequency})", frequency)
        series.setLabelsVisible(True)

        chart = self.components_chart_view.chart()
        chart.removeAllSeries()
        chart.addSeries(series)
        chart.legend().setVisible(True)

    def update_monthly_activity(self, iterations_data, fabrications_data):
        """Actualiza el nuevo gráfico de actividad mensual."""
        series_iter = QLineSeries()
        series_iter.setName("Iteraciones")
        series_fab = QLineSeries()
        series_fab.setName("Fabricaciones")

        max_val = 0
        if iterations_data:
            for timestamp, count in iterations_data.items():
                series_iter.append(timestamp, count)
                if count > max_val: max_val = count

        if fabrications_data:
            for timestamp, count in fabrications_data.items():
                series_fab.append(timestamp, count)
                if count > max_val: max_val = count

        chart = QChart()
        chart.addSeries(series_iter)
        chart.addSeries(series_fab)

        axis_x = QDateTimeAxis()
        axis_x.setFormat("MMM yyyy")
        axis_x.setTitleText("Mes")
        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        series_iter.attachAxis(axis_x)
        series_fab.attachAxis(axis_x)

        axis_y = QValueAxis()
        axis_y.setLabelFormat("%i")
        axis_y.setTitleText("Nº de Eventos")
        axis_y.setRange(0, max_val + 1)
        axis_y.setTickCount(max_val + 2 if max_val < 10 else 10)
        chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series_iter.attachAxis(axis_y)
        series_fab.attachAxis(axis_y)

        self.activity_chart_view.setChart(chart)
