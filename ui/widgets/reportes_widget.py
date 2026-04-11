# -*- coding: utf-8 -*-
"""
Nombre del Módulo: reportes_widget

Descripción: Vista principal de reportes: búsqueda inteligente, lista de órdenes y gráficas.
             ``ReportService`` se resuelve desde el contenedor del hub o desde ``model.report_service``;
             los sub-widgets consumen solo ese servicio.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QSplitter, QFrame,
)
from PyQt6.QtCore import Qt

from core.services.report_service import ReportService

from .reports.smart_search import SmartSearchWidget
from .reports.order_list import OrderListWidget
from .reports.charts_container import ReportsChartsWidget


class ReportesWidget(QWidget):
    """
    Módulo de reportes: búsqueda, órdenes por producto y gráficas.

    Tras ``set_controller(hub)`` los hijos reciben únicamente ``ReportService`` resuelto del hub.
    """

    STYLE_MAIN = """
        ReportesWidget {
            background-color: #f1f5f9;
        }
    """

    search_widget = None
    orders_widget = None
    charts_widget = None

    def __init__(self, app_hub: Any = None, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._report_service: Any = None
        if app_hub is not None:
            self._bind_hub(app_hub)
        self.logger = logging.getLogger("EvolucionTiemposApp.ReportesWidget")

        self.setStyleSheet(self.STYLE_MAIN)
        self._setup_ui(app_hub)
        self._connect_signals()

        self.logger.info("ReportesWidget inicializado")

    def _bind_hub(self, hub: Any) -> None:
        if hub is None:
            self._report_service = None
            return
        self._report_service = self._resolve_report_service(hub)

    @staticmethod
    def _resolve_report_service(hub: Any) -> Any:
        if hub is None:
            return None
        container = getattr(hub, "container", None)
        if container is not None and container.is_registered(ReportService):
            return container.resolve(ReportService)
        model = getattr(hub, "model", None)
        if model is not None:
            rs = getattr(model, "report_service", None)
            if rs is not None:
                return rs
        return None

    def _setup_ui(self, app_hub: Any) -> None:
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)

        left_panel = QFrame()
        left_panel.setMaximumWidth(380)
        left_panel.setMinimumWidth(300)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        self.search_widget = SmartSearchWidget(
            parent=self,
            report_service=self._report_service,
        )
        left_layout.addWidget(self.search_widget)

        main_layout.addWidget(left_panel)

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

        self.orders_widget = OrderListWidget(
            report_service=self._report_service,
        )
        right_splitter.addWidget(self.orders_widget)

        self.charts_widget = ReportsChartsWidget(
            report_service=self._report_service,
        )
        right_splitter.addWidget(self.charts_widget)

        right_splitter.setSizes([300, 400])

        main_layout.addWidget(right_splitter, 1)

    def _connect_signals(self) -> None:
        if self.search_widget is not None:
            self.search_widget.result_selected.connect(self._on_search_result_selected)
            self.search_widget.search_cleared.connect(self._on_search_cleared)

        if self.orders_widget is not None:
            self.orders_widget.order_selected.connect(self._on_order_selected)

    def _report_api(self) -> Any:
        return self._report_service

    def _on_search_result_selected(self, tipo: str, codigo: str) -> None:
        self.logger.info(f"Seleccionado: {tipo} - {codigo}")

        if tipo == "producto":
            if self.orders_widget is not None:
                self.orders_widget.load_orders_for_product(codigo)
            if self.charts_widget is not None:
                self.charts_widget.update_charts(codigo)

        elif tipo == "orden":
            try:
                api = self._report_api()
                if api:
                    detalle = api.get_order_details(codigo)
                    if detalle:
                        if self.orders_widget is not None:
                            self.orders_widget.load_orders_for_product(detalle.producto_codigo)
                            self.orders_widget.select_order(codigo)
                        if self.charts_widget is not None:
                            self.charts_widget.update_charts(detalle.producto_codigo)
            except Exception as e:
                self.logger.error(f"Error procesando orden: {e}")

    def _on_search_cleared(self) -> None:
        if self.orders_widget is not None:
            self.orders_widget.clear()
        if self.charts_widget is not None:
            self.charts_widget.clear()

    def _on_order_selected(self, orden_fabricacion: str) -> None:
        self.logger.info(f"Orden seleccionada: {orden_fabricacion}")
        api = self._report_api()
        if not api or self.orders_widget is None:
            return
        try:
            detalle = api.get_order_details(orden_fabricacion)
            unidades = api.get_order_units(orden_fabricacion)
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

    def set_controller(self, hub: Any) -> None:
        """Enlaza hub: actualiza ``ReportService`` en sub-widgets."""
        self._bind_hub(hub)
        if self.search_widget is not None:
            self.search_widget.set_report_service(self._report_service)
        if self.orders_widget is not None:
            self.orders_widget.set_report_service(self._report_service)
        if self.charts_widget is not None:
            self.charts_widget.set_report_service(self._report_service)

    def refresh(self) -> None:
        if self.search_widget is not None:
            self.search_widget.clear_search()
        if self.orders_widget is not None:
            self.orders_widget.clear()
        if self.charts_widget is not None:
            self.charts_widget.clear()
