# -*- coding: utf-8 -*-
"""
========================================================================
CHARTS CONTAINER WIDGET - Contenedor de Gráficas de Análisis
========================================================================
Widget contenedor que muestra múltiples gráficas de análisis para
un producto seleccionado: tiempo promedio, evolución temporal,
tiempos por trabajador y patrón de incidencias.
========================================================================
"""
import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QTabWidget, QSizePolicy, QGridLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor, QPainter, QPen, QBrush

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


class StatCard(QFrame):
    """Tarjeta de estadística individual."""
    
    STYLE = """
        QFrame {
            background-color: white;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 16px;
        }
    """
    
    def __init__(self, title: str, value: str, subtitle: str = "", color: str = "#2563eb"):
        super().__init__()
        self.setStyleSheet(self.STYLE)
        self.setMinimumWidth(150)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)
        
        title_label = QLabel(title)
        title_label.setStyleSheet(f"color: #64748b; font-size: 11px;")
        layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setStyleSheet(f"color: {color}; font-size: 24px; font-weight: bold;")
        layout.addWidget(value_label)
        
        if subtitle:
            sub_label = QLabel(subtitle)
            sub_label.setStyleSheet("color: #94a3b8; font-size: 10px;")
            layout.addWidget(sub_label)


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
    
    def __init__(self, controller=None, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.logger = logging.getLogger("EvolucionTiemposApp.ReportsChartsWidget")
        self._current_producto = None
        self._setup_ui()
    
    def _setup_ui(self):
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
        self.title_label.setFont(QFont("", 12, QFont.Weight.Bold))
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
    
    def _create_placeholder_tabs(self):
        """Crea tabs con placeholders."""
        tabs_info = [
            ("📈 Evolución", "Evolución temporal del tiempo de producción"),
            ("👥 Por Trabajador", "Comparativa de tiempos entre trabajadores"),
            ("⚠️ Incidencias", "Distribución de incidencias por tipo")
        ]
        
        for title, description in tabs_info:
            tab = QWidget()
            tab_layout = QVBoxLayout(tab)
            tab_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            placeholder = QLabel(description)
            placeholder.setStyleSheet("color: #94a3b8; font-style: italic;")
            tab_layout.addWidget(placeholder)
            
            self.tabs.addTab(tab, title)
    
    def update_charts(self, producto_codigo: str):
        """
        Actualiza todas las gráficas para un producto.
        
        Args:
            producto_codigo: Código del producto
        """
        self._current_producto = producto_codigo
        self.title_label.setText(f"📊 Análisis: {producto_codigo}")
        
        try:
            if not self.controller or not hasattr(self.controller, 'model'):
                return
            
            model = self.controller.model
            
            # Cargar estadísticas de tiempo promedio
            promedio_data = model.reports_calcular_promedio_tiempo(producto_codigo)
            self._update_stats_cards(promedio_data)
            
            # Cargar datos para gráficas
            if CHARTS_AVAILABLE:
                evolucion_data = model.reports_obtener_evolucion_temporal(producto_codigo, dias=30)
                self._update_evolution_chart(evolucion_data)
                
                trabajadores_data = model.reports_obtener_tiempos_por_trabajador(producto_codigo)
                self._update_workers_chart(trabajadores_data)
                
                incidencias_data = model.reports_obtener_incidencias_por_producto(producto_codigo)
                self._update_incidents_chart(incidencias_data)
            
        except Exception as e:
            self.logger.error(f"Error actualizando gráficas: {e}", exc_info=True)
    
    def _update_stats_cards(self, promedio_data):
        """Actualiza las tarjetas de estadísticas."""
        # Limpiar layout actual
        while self.stats_layout.count():
            child = self.stats_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        if not promedio_data:
            placeholder = QLabel("No hay datos de producción")
            placeholder.setStyleSheet("color: #94a3b8; font-style: italic;")
            self.stats_layout.addWidget(placeholder)
            return
        
        # Tiempo promedio
        tiempo_min = promedio_data.promedio_segundos / 60
        card1 = StatCard(
            "Tiempo Promedio",
            f"{tiempo_min:.1f} min",
            f"σ = {promedio_data.desviacion_estandar/60:.1f} min",
            "#2563eb"
        )
        self.stats_layout.addWidget(card1)
        
        # Total unidades
        card2 = StatCard(
            "Total Unidades",
            str(promedio_data.total_unidades),
            "producidas",
            "#16a34a"
        )
        self.stats_layout.addWidget(card2)
        
        # Tiempo mínimo
        min_min = promedio_data.minimo_segundos / 60
        card3 = StatCard(
            "Mejor Tiempo",
            f"{min_min:.1f} min",
            "por unidad",
            "#0891b2"
        )
        self.stats_layout.addWidget(card3)
        
        # Tiempo máximo
        max_min = promedio_data.maximo_segundos / 60
        card4 = StatCard(
            "Peor Tiempo",
            f"{max_min:.1f} min",
            "por unidad",
            "#dc2626"
        )
        self.stats_layout.addWidget(card4)
        
        self.stats_layout.addStretch()
    
    def _update_evolution_chart(self, evolucion_data):
        """Actualiza la gráfica de evolución temporal."""
        if not CHARTS_AVAILABLE or not evolucion_data:
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
        chart.legend().hide()
        
        # Crear vista
        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Reemplazar tab
        self.tabs.removeTab(0)
        self.tabs.insertTab(0, chart_view, "📈 Evolución")
        self.tabs.setCurrentIndex(0)
    
    def _update_workers_chart(self, trabajadores_data):
        """Actualiza la gráfica de tiempos por trabajador."""
        if not CHARTS_AVAILABLE or not trabajadores_data:
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
        
        chart.legend().setVisible(False)
        
        # Crear vista
        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Reemplazar tab
        self.tabs.removeTab(1)
        self.tabs.insertTab(1, chart_view, "👥 Por Trabajador")
    
    def _update_incidents_chart(self, incidencias_data):
        """Actualiza la gráfica de incidencias (pie chart)."""
        if not CHARTS_AVAILABLE or not incidencias_data:
            return
        
        # Crear serie de pastel
        series = QPieSeries()
        
        colors = ["#ef4444", "#f59e0b", "#eab308", "#22c55e", "#3b82f6", "#8b5cf6"]
        
        for i, inc in enumerate(incidencias_data[:6]):  # Limitar a 6 tipos
            slice = series.append(f"{inc.tipo_incidencia} ({inc.cantidad})", inc.cantidad)
            slice.setLabelVisible(True)
        
        # Crear chart
        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("Distribución de Incidencias")
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        chart.legend().setAlignment(Qt.AlignmentFlag.AlignRight)
        
        # Crear vista
        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Reemplazar tab
        self.tabs.removeTab(2)
        self.tabs.insertTab(2, chart_view, "⚠️ Incidencias")
    
    def set_controller(self, controller):
        """Establece el controlador."""
        self.controller = controller
    
    def clear(self):
        """Limpia el widget."""
        self._current_producto = None
        self.title_label.setText("📊 Análisis de Producción")
        
        # Limpiar stats
        while self.stats_layout.count():
            child = self.stats_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        self.stats_placeholder = QLabel("Seleccione un producto para ver estadísticas")
        self.stats_placeholder.setStyleSheet("color: #94a3b8; font-style: italic;")
        self.stats_layout.addWidget(self.stats_placeholder)
        
        # Recrear tabs placeholder
        self.tabs.clear()
        self._create_placeholder_tabs()
