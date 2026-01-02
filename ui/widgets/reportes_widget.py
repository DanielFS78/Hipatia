# -*- coding: utf-8 -*-
"""
========================================================================
REPORTES WIDGET - Módulo Principal de Reportes de Producción
========================================================================
Widget principal que integra los componentes de búsqueda inteligente,
lista de órdenes de fabricación y gráficas de análisis.

Estructura:
- Panel Izquierdo: Búsqueda inteligente
- Panel Derecho Superior: Lista de órdenes de fabricación
- Panel Derecho Inferior: Gráficas y análisis
========================================================================
"""
import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QFrame,
    QLabel, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

# Importar widgets de reportes
from .reports.smart_search import SmartSearchWidget
from .reports.order_list import OrderListWidget
from .reports.charts_container import ReportsChartsWidget


class ReportesWidget(QWidget):
    """
    Widget principal para el módulo de Reportes de Producción.
    
    Integra búsqueda inteligente, lista de órdenes y gráficas de análisis.
    """
    
    STYLE_MAIN = """
        ReportesWidget {
            background-color: #f1f5f9;
        }
    """
    
    # Attributes for strict mocks
    controller = None
    search_widget = None
    orders_widget = None
    charts_widget = None
    
    def __init__(self, controller):
        """
        Inicializa el widget de reportes.
        
        Args:
            controller: Controlador de la aplicación
        """
        super().__init__()
        self.controller = controller
        self.logger = logging.getLogger("EvolucionTiemposApp.ReportesWidget")
        
        self.setStyleSheet(self.STYLE_MAIN)
        self._setup_ui()
        self._connect_signals()
        
        self.logger.info("ReportesWidget inicializado")
    
    def _setup_ui(self):
        """Configura la interfaz de usuario."""
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)
        
        # =====================================================================
        # PANEL IZQUIERDO: Búsqueda
        # =====================================================================
        left_panel = QFrame()
        left_panel.setMaximumWidth(380)
        left_panel.setMinimumWidth(300)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)
        
        # Widget de búsqueda inteligente
        self.search_widget = SmartSearchWidget(controller=self.controller)
        left_layout.addWidget(self.search_widget)
        
        main_layout.addWidget(left_panel)
        
        # =====================================================================
        # PANEL DERECHO: Órdenes + Gráficas (Splitter vertical)
        # =====================================================================
        right_splitter = QSplitter(Qt.Orientation.Vertical)
        right_splitter.setHandleWidth(8)
        right_splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #e2e8f0;
                border-radius: 4px;
            }
            QSplitter::handle:hover {
                background-color: #cbd5e1;
            }
        """)
        
        # Panel de órdenes de fabricación
        self.orders_widget = OrderListWidget(controller=self.controller)
        right_splitter.addWidget(self.orders_widget)
        
        # Panel de gráficas
        self.charts_widget = ReportsChartsWidget(controller=self.controller)
        right_splitter.addWidget(self.charts_widget)
        
        # Establecer tamaños iniciales (40% órdenes, 60% gráficas)
        right_splitter.setSizes([300, 400])
        
        main_layout.addWidget(right_splitter, 1)
    
    def _connect_signals(self):
        """Conecta las señales entre widgets."""
        # Cuando se selecciona un resultado de búsqueda
        self.search_widget.result_selected.connect(self._on_search_result_selected)
        self.search_widget.search_cleared.connect(self._on_search_cleared)
        
        # Cuando se selecciona una orden
        self.orders_widget.order_selected.connect(self._on_order_selected)
    
    def _on_search_result_selected(self, tipo: str, codigo: str):
        """
        Maneja la selección de un resultado de búsqueda.
        
        Args:
            tipo: 'producto' o 'orden'
            codigo: Código del elemento seleccionado
        """
        self.logger.info(f"Seleccionado: {tipo} - {codigo}")
        
        if tipo == 'producto':
            # Cargar órdenes del producto
            self.orders_widget.load_orders_for_product(codigo)
            # Actualizar gráficas del producto
            self.charts_widget.update_charts(codigo)
            
        elif tipo == 'orden':
            # Si es una orden, primero buscar el producto asociado
            try:
                if self.controller and hasattr(self.controller, 'model'):
                    detalle = self.controller.model.reports_obtener_detalle_orden(codigo)
                    if detalle:
                        # Cargar órdenes del producto asociado
                        self.orders_widget.load_orders_for_product(detalle.producto_codigo)
                        # Actualizar gráficas
                        self.charts_widget.update_charts(detalle.producto_codigo)
            except Exception as e:
                self.logger.error(f"Error procesando orden: {e}")
    
    def _on_search_cleared(self):
        """Maneja el evento de búsqueda limpiada."""
        self.orders_widget.clear()
        self.charts_widget.clear()
    
    def _on_order_selected(self, orden_fabricacion: str):
        """
        Maneja la selección de una orden de fabricación.
        
        Args:
            orden_fabricacion: Identificador de la orden
        """
        self.logger.info(f"Orden seleccionada: {orden_fabricacion}")
        # Aquí se podría mostrar un diálogo de detalle de la orden
        # o actualizar una vista adicional con las unidades individuales
    
    def set_controller(self, controller):
        """
        Establece el controlador para todos los sub-widgets.
        
        Args:
            controller: Controlador de la aplicación
        """
        self.controller = controller
        self.search_widget.set_controller(controller)
        self.orders_widget.set_controller(controller)
        self.charts_widget.set_controller(controller)
    
    def refresh(self):
        """Refresca el contenido del widget."""
        # Limpiar todo para empezar de nuevo
        self.search_widget.clear_search()
        self.orders_widget.clear()
        self.charts_widget.clear()
