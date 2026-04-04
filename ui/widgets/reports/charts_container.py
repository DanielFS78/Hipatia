# -*- coding: utf-8 -*-
"""
========================================================================
CHARTS CONTAINER WIDGET - Contenedor de Gráficas de Análisis
========================================================================
Widget contenedor que muestra múltiples gráficas de análisis para
un producto seleccionado: tiempo promedio, evolución temporal,
tiempos por trabajador y patrón de incidencias.

Datos: ``report_service=`` opcional con la misma prioridad que en ``OrderListWidget``.
========================================================================
"""
import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QTabWidget, QGridLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor, QPainter, QPen, QBrush
from typing import Any
from ui.widgets.reports.stat_card import StatCard
from ui.widgets.reports.charts_renderers import (
    clear_stats_layout,
    update_stats_cards,
)

# Import condicional de Charts
try:
    from PyQt6.QtCharts import (
        QChart, QChartView, QBarSeries, QBarSet, QLineSeries,
        QPieSeries, QValueAxis, QBarCategoryAxis
    )
    CHARTS_AVAILABLE = True
except ImportError:
    CHARTS_AVAILABLE = False
    logging.warning("PyQt6.QtCharts no disponible. Gráficas deshabilitadas.")


class ReportsChartsWidget(QWidget):
    """
    Widget contenedor para las gráficas de análisis.
    Muestra estadísticas y gráficas para un producto seleccionado.
    """
    
    STYLE_CONTAINER = """
        QFrame {
            background-color: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
        }
    """
    
    def __init__(
        self,
        controller: Any = None,
        parent: Any = None,
        *,
        report_service: Any = None,
    ) -> None:
        super().__init__(parent)
        self.controller = controller
        self._report_service = report_service
        self.logger = logging.getLogger("EvolucionTiemposApp.ReportsChartsWidget")
        self._current_producto: str | None = None
        self._tab_titles = ["📈 Evolución", "👥 Por Trabajador", "⚠️ Incidencias"]
        self._tab_descriptions = [
            "Evolución temporal del tiempo de producción",
            "Comparativa de tiempos entre trabajadores",
            "Distribución de incidencias por tipo",
        ]
        self._setup_ui()

    def _get_reports_model(self) -> Any:
        """Prioriza `ReportService` inyectado; si no, controlador o `controller.model`."""
        if self._report_service is not None:
            return self._report_service
        if self.controller is None:
            return None
        if hasattr(self.controller, "get_product_time_stats"):
            return self.controller
        if hasattr(self.controller, "model"):
            return self.controller.model
        return None
    
    def _setup_ui(self) -> None:
        """Configura la interfaz."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Frame contenedor
        container = QFrame()
        container.setStyleSheet(self.STYLE_CONTAINER)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(16, 16, 16, 16)
        container_layout.setSpacing(16)
        
        # Título
        self.title_label = QLabel("📊 Análisis de Producción")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setWeight(QFont.Weight.Bold)
        self.title_label.setFont(title_font)
        container_layout.addWidget(self.title_label)
        
        # Grid de tarjetas de estadísticas
        self.stats_layout = QHBoxLayout()
        self.stats_layout.setSpacing(12)
        container_layout.addLayout(self.stats_layout)
        
        # Placeholder para estadísticas
        self.stats_placeholder = QLabel("Seleccione un producto para ver estadísticas")
        self.stats_placeholder.setStyleSheet("color: #94a3b8; font-style: italic;")
        self.stats_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.stats_layout.addWidget(self.stats_placeholder)
        
        # Tabs para las diferentes gráficas
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                background-color: white;
            }
            QTabBar::tab {
                padding: 8px 16px;
                margin-right: 4px;
                background-color: #f1f5f9;
                border-radius: 4px 4px 0 0;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 2px solid #2563eb;
            }
        """)
        
        # Crear tabs placeholder
        self._create_placeholder_tabs()
        
        container_layout.addWidget(self.tabs, 1)
        layout.addWidget(container)
    
    def _create_placeholder_tabs(self) -> None:
        """Crea tabs con placeholders."""
        for title, description in zip(self._tab_titles, self._tab_descriptions):
            tab = QWidget()
            tab_layout = QVBoxLayout(tab)
            tab_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            placeholder = QLabel(description)
            placeholder.setStyleSheet("color: #94a3b8; font-style: italic;")
            tab_layout.addWidget(placeholder)
            
            self.tabs.addTab(tab, title)

    def _set_placeholder_tab(self, index: int, message: str) -> None:
        tab = QWidget()
        tab_layout = QVBoxLayout(tab)
        tab_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder = QLabel(message)
        placeholder.setStyleSheet("color: #94a3b8; font-style: italic;")
        tab_layout.addWidget(placeholder)
        old_widget = self.tabs.widget(index)
        if old_widget is not None:
            self.tabs.removeTab(index)
        self.tabs.insertTab(index, tab, self._tab_titles[index])

    def _set_chart_tab(self, index: int, chart: Any, empty_message: str) -> None:
        if not CHARTS_AVAILABLE:
            self._set_placeholder_tab(index, empty_message)
            return
        if chart is None:
            self._set_placeholder_tab(index, empty_message)
            return
        current_widget = self.tabs.widget(index)
        if current_widget is not None:
            set_chart = getattr(current_widget, "setChart", None)
            if callable(set_chart):
                set_chart(chart)
                return
        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        if current_widget is not None:
            self.tabs.removeTab(index)
        self.tabs.insertTab(index, chart_view, self._tab_titles[index])
    
    def update_charts(self, producto_codigo: str) -> None:
        """
        Actualiza todas las gráficas para un producto.
        
        Args:
            producto_codigo: Código del producto
        """
        self._current_producto = producto_codigo
        self.title_label.setText(f"📊 Análisis: {producto_codigo}")
        
        try:
            model = self._get_reports_model()
            if model is None:
                return
            
            # Cargar estadísticas de tiempo promedio
            promedio_data = model.get_product_time_stats(producto_codigo) if hasattr(model, "get_product_time_stats") else None
            self._update_stats_cards(promedio_data)
            
            # Cargar datos para gráficas
            if CHARTS_AVAILABLE:
                evolucion_data = model.get_evolution_stats(producto_codigo, days=30) if hasattr(model, "get_evolution_stats") else []
                self._update_evolution_chart(evolucion_data)
                
                trabajadores_data = model.get_worker_time_stats(producto_codigo) if hasattr(model, "get_worker_time_stats") else []
                self._update_workers_chart(trabajadores_data)
                
                incidencias_data = model.get_incidents_stats(producto_codigo) if hasattr(model, "get_incidents_stats") else []
                self._update_incidents_chart(incidencias_data)
            
        except Exception as e:
            self.logger.error(f"Error actualizando gráficas: {e}", exc_info=True)
    
    def _update_stats_cards(self, promedio_data: Any) -> None:
        """Actualiza las tarjetas de estadísticas."""
        update_stats_cards(self, promedio_data, StatCard)
    
    def _update_evolution_chart(self, evolucion_data: Any) -> None:
        """Actualiza la gráfica de evolución temporal."""
        if not CHARTS_AVAILABLE or not evolucion_data:
            self._set_placeholder_tab(0, self._tab_descriptions[0])
            return
        
        # Crear serie de línea
        series = QLineSeries()
        series.setName("Tiempo promedio")
        
        for punto in evolucion_data:
            timestamp = punto.fecha.timestamp() * 1000  # Qt usa milisegundos
            valor = punto.promedio_segundos / 60  # Convertir a minutos
            series.append(timestamp, valor)
        
        # Crear chart
        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("Evolución del Tiempo de Producción")
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        legend = chart.legend()
        if legend:
            legend.hide()
        
        self._set_chart_tab(0, chart, self._tab_descriptions[0])
    
    def _update_workers_chart(self, trabajadores_data: Any) -> None:
        """Actualiza la gráfica de tiempos por trabajador."""
        if not CHARTS_AVAILABLE or not trabajadores_data:
            self._set_placeholder_tab(1, self._tab_descriptions[1])
            return
        
        # Crear serie de barras
        bar_set = QBarSet("Tiempo promedio (min)")
        categories = []
        
        for trab in trabajadores_data[:10]:  # Limitar a 10 trabajadores
            tiempo_min = trab.promedio_segundos / 60
            bar_set.append(tiempo_min)
            # Usar solo primer nombre para legibilidad
            nombre = trab.trabajador_nombre.split()[0] if trab.trabajador_nombre else "N/A"
            categories.append(nombre)
        
        series = QBarSeries()
        series.append(bar_set)
        
        # Crear chart
        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("Tiempo Promedio por Trabajador")
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        
        # Eje de categorías
        axis_x = QBarCategoryAxis()
        axis_x.append(categories)
        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(axis_x)
        
        # Eje de valores
        axis_y = QValueAxis()
        chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axis_y)
        
        legend = chart.legend()
        if legend:
            legend.setVisible(False)
        
        self._set_chart_tab(1, chart, self._tab_descriptions[1])
    
    def _update_incidents_chart(self, incidencias_data: Any) -> None:
        """Actualiza la gráfica de incidencias (pie chart)."""
        if not CHARTS_AVAILABLE or not incidencias_data:
            self._set_placeholder_tab(2, self._tab_descriptions[2])
            return
        
        # Crear serie de pastel
        series = QPieSeries()
        
        for i, inc in enumerate(incidencias_data[:6]):  # Limitar a 6 tipos
            slice = series.append(f"{inc.tipo_incidencia} ({inc.cantidad})", inc.cantidad)
            if slice:
                slice.setLabelVisible(True)
        
        # Crear chart
        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("Distribución de Incidencias")
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        legend = chart.legend()
        if legend:
            legend.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        self._set_chart_tab(2, chart, self._tab_descriptions[2])
    
    def set_controller(self, controller: Any) -> None:
        """Establece el controlador."""
        self.controller = controller

    def set_report_service(self, report_service: Any) -> None:
        self._report_service = report_service
    
    def clear(self) -> None:
        """Limpia el widget."""
        self._current_producto = None
        self.title_label.setText("📊 Análisis de Producción")
        
        clear_stats_layout(self)
        
        self.stats_placeholder = QLabel("Seleccione un producto para ver estadísticas")
        self.stats_placeholder.setStyleSheet("color: #94a3b8; font-style: italic;")
        self.stats_layout.addWidget(self.stats_placeholder)
        
        for index, description in enumerate(self._tab_descriptions):
            self._set_placeholder_tab(index, description)
