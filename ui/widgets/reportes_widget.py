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
from __future__ import annotations

import logging
from typing import Any

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QFrame,
    QLabel
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
    
    def __init__(self, controller: Any) -> None:
        """
        Inicializa el widget de reportes.
        
        Args:
            controller: Controlador de la aplicación
        """
        super().__init__()
        self.controller = controller
        self.app_model = self._resolve_app_model(controller)
        self.report_controller = controller  # Compatibilidad histórica
        self.logger = logging.getLogger("EvolucionTiemposApp.ReportesWidget")
        
        self.setStyleSheet(self.STYLE_MAIN)
        self._setup_ui()
        self._connect_signals()
        
        self.logger.info("ReportesWidget inicializado")
    
    def _setup_ui(self) -> None:
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
        self.search_widget = SmartSearchWidget(app_model=self.app_model)
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
        self.orders_widget = OrderListWidget(controller=self.app_model)
        right_splitter.addWidget(self.orders_widget)
        
        # Panel de gráficas
        self.charts_widget = ReportsChartsWidget(controller=self.app_model)
        right_splitter.addWidget(self.charts_widget)
        
        # Establecer tamaños iniciales (40% órdenes, 60% gráficas)
        right_splitter.setSizes([300, 400])
        
        main_layout.addWidget(right_splitter, 1)
    
    def _connect_signals(self) -> None:
        """Conecta las señales entre widgets."""
        # Cuando se selecciona un resultado de búsqueda
        if self.search_widget is not None:
            self.search_widget.result_selected.connect(self._on_search_result_selected)
            self.search_widget.search_cleared.connect(self._on_search_cleared)
        
        # Cuando se selecciona una orden
        if self.orders_widget is not None:
            self.orders_widget.order_selected.connect(self._on_order_selected)

    @staticmethod
    def _resolve_app_model(controller: Any) -> Any:
        """
        Resuelve un modelo de reportes estable desde el controlador recibido.
        Acepta tanto un AppController (con .model) como un AppModel/servicio directo.

        Debe comprobarse `.model` antes que `search_reports_data`: con `MagicMock`
        sueltos, `hasattr(mock, "search_reports_data")` suele ser True por hijos
        autocreados y se tomaba el mock del controlador en lugar del `.model`.
        """
        if controller is None:
            return None
        inner = getattr(controller, "model", None)
        if inner is not None:
            return inner
        if hasattr(controller, "search_reports_data"):
            return controller
        return None
    
    def _on_search_result_selected(self, tipo: str, codigo: str) -> None:
        """
        Maneja la selección de un resultado de búsqueda.
        
        Args:
            tipo: 'producto' o 'orden'
            codigo: Código del elemento seleccionado
        """
        self.logger.info(f"Seleccionado: {tipo} - {codigo}")
        
        if tipo == 'producto':
            # Cargar órdenes del producto
            if self.orders_widget is not None:
                self.orders_widget.load_orders_for_product(codigo)
            # Actualizar gráficas del producto
            if self.charts_widget is not None:
                self.charts_widget.update_charts(codigo)
            
        elif tipo == 'orden':
            # Si es una orden, primero buscar el producto asociado
            try:
                if self.app_model:
                    detalle = self.app_model.get_order_details(codigo)
                    if detalle:
                        if self.orders_widget is not None:
                            self.orders_widget.load_orders_for_product(detalle.producto_codigo)
                            self.orders_widget.select_order(codigo)
                        if self.charts_widget is not None:
                            self.charts_widget.update_charts(detalle.producto_codigo)
            except Exception as e:
                self.logger.error(f"Error procesando orden: {e}")
    
    def _on_search_cleared(self) -> None:
        """Maneja el evento de búsqueda limpiada."""
        if self.orders_widget is not None:
            self.orders_widget.clear()
        if self.charts_widget is not None:
            self.charts_widget.clear()
    
    def _on_order_selected(self, orden_fabricacion: str) -> None:
        """
        Maneja la selección de una orden de fabricación.
        
        Args:
            orden_fabricacion: Identificador de la orden
        """
        self.logger.info(f"Orden seleccionada: {orden_fabricacion}")
        if not self.app_model or self.orders_widget is None:
            return
        try:
            detalle = self.app_model.get_order_details(orden_fabricacion)
            unidades = self.app_model.get_order_units(orden_fabricacion)
            if not detalle:
                self.orders_widget.status_label.setText("No se encontraron detalles para la orden seleccionada")
                self.orders_widget.status_label.show()
                return
            self.orders_widget.select_order(orden_fabricacion)
            tiempo_min = int((detalle.tiempo_total_segundos or 0) / 60)
            self.orders_widget.status_label.setText(
                f"Orden {detalle.orden_fabricacion}: {len(unidades)} unidad(es), "
                f"{tiempo_min} min totales, {detalle.incidencias_count} incidencia(s)"
            )
            self.orders_widget.status_label.show()
        except Exception as e:
            self.logger.error(f"Error cargando detalle de orden: {e}", exc_info=True)
    
    def set_controller(self, controller: Any) -> None:
        """
        Establece el controlador para todos los sub-widgets.
        
        Args:
            controller: Controlador de la aplicación
        """
        self.controller = controller
        self.app_model = self._resolve_app_model(controller)
        model_target = self.app_model if self.app_model is not None else controller
        if self.search_widget is not None:
            self.search_widget.set_controller(model_target)
        if self.orders_widget is not None:
            self.orders_widget.set_controller(model_target)
        if self.charts_widget is not None:
            self.charts_widget.set_controller(model_target)
    
    def refresh(self) -> None:
        """Refresca el contenido del widget."""
        # Limpiar todo para empezar de nuevo
        if self.search_widget is not None:
            self.search_widget.clear_search()
        if self.orders_widget is not None:
            self.orders_widget.clear()
        if self.charts_widget is not None:
            self.charts_widget.clear()
