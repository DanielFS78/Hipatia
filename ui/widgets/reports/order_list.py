# -*- coding: utf-8 -*-
"""
Nombre del Módulo: order_list

Descripción: Lista de órdenes de fabricación de un producto con tarjetas expandibles; datos vía ``ReportService``.
"""
import logging
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QSizePolicy, QSpacerItem
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor
from typing import Any


class OrderCard(QFrame):
    """
    Tarjeta individual para mostrar resumen de una orden de fabricación.
    """
    
    clicked = pyqtSignal(str)  # orden_fabricacion
    detail_requested = pyqtSignal(str, str)  # (orden_fabricacion, detail_type)
    
    STYLE_CARD = """
        QFrame {
            background-color: white;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 12px;
        }
        QFrame:hover {
            border-color: #2563eb;
            background-color: #f8fafc;
        }
    """

    STYLE_SELECTED = """
        QFrame {
            background-color: #eff6ff;
            border: 2px solid #2563eb;
            border-radius: 8px;
            padding: 12px;
        }
    """
    
    def __init__(self, order_data: Any, parent: Any = None) -> None:
        """
        Args:
            order_data: OrdenFabricacionResumenDTO
        """
        super().__init__(parent)
        self.order_data = order_data
        self.setStyleSheet(self.STYLE_CARD)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Configura la interfaz de la tarjeta."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)
        
        # Fila superior: OF y estado
        top_row = QHBoxLayout()
        
        of_label = QLabel(f"📋 {self.order_data.orden_fabricacion}")
        of_font = QFont()
        of_font.setPointSize(11)
        of_font.setWeight(QFont.Weight.Bold)
        of_label.setFont(of_font)
        top_row.addWidget(of_label)
        
        top_row.addStretch()
        
        # Badge de estado
        estado = self.order_data.estado
        if estado == "completado":
            estado_text = "✅ Completado"
            estado_color = "#16a34a"
        elif estado == "en_proceso":
            estado_text = "🔄 En Proceso"
            estado_color = "#2563eb"
        else:
            estado_text = "⏸ Pausado"
            estado_color = "#f59e0b"
        
        estado_label = QLabel(estado_text)
        estado_label.setStyleSheet(f"color: {estado_color}; font-size: 11px;")
        top_row.addWidget(estado_label)
        
        layout.addLayout(top_row)
        
        # Fila de datos: fecha, cantidad, tiempo
        data_row = QHBoxLayout()
        data_row.setSpacing(16)
        
        # Fecha
        fecha_str = self.order_data.fecha_inicio.strftime("%d/%m/%Y") if self.order_data.fecha_inicio else "N/A"
        fecha_label = QLabel(f"📅 {fecha_str}")
        fecha_label.setStyleSheet("color: #64748b; font-size: 11px;")
        data_row.addWidget(fecha_label)
        
        # Cantidad
        cantidad_label = QLabel(f"📦 {self.order_data.cantidad_unidades} uds")
        cantidad_label.setStyleSheet("color: #64748b; font-size: 11px;")
        data_row.addWidget(cantidad_label)
        
        # Tiempo total
        tiempo_min = self.order_data.tiempo_total_segundos // 60
        tiempo_label = QLabel(f"⏱ {tiempo_min} min")
        tiempo_label.setStyleSheet("color: #64748b; font-size: 11px;")
        data_row.addWidget(tiempo_label)
        
        # Incidencias
        if self.order_data.incidencias_count > 0:
            inc_label = QLabel(f"⚠️ {self.order_data.incidencias_count}")
            inc_label.setStyleSheet("color: #f59e0b; font-size: 11px;")
            data_row.addWidget(inc_label)
        
        data_row.addStretch()
        layout.addLayout(data_row)

    def set_selected(self, selected: bool) -> None:
        """Actualiza estilo visual para reflejar selección."""
        self.setStyleSheet(self.STYLE_SELECTED if selected else self.STYLE_CARD)
    
    def mousePressEvent(self, event: Any) -> None:
        """Emite señal al hacer clic."""
        self.clicked.emit(self.order_data.orden_fabricacion)
        super().mousePressEvent(event)


class OrderListWidget(QWidget):
    """
    Widget que muestra lista de órdenes de fabricación.
    
    Signals:
        order_selected(str): Emitido cuando se selecciona una orden.
    """
    
    order_selected = pyqtSignal(str)  # orden_fabricacion
    
    STYLE_CONTAINER = """
        QFrame {
            background-color: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
        }
    """
    
    def __init__(
        self,
        parent: Any = None,
        *,
        report_service: Any = None,
    ) -> None:
        super().__init__(parent)
        self._report_service = report_service
        self.logger = logging.getLogger("EvolucionTiemposApp.OrderListWidget")
        self._current_producto: str | None = None
        self._selected_order: str | None = None
        self._order_cards: list[Any] = []
        self._setup_ui()

    def _get_reports_model(self) -> Any:
        return self._report_service
    
    def _setup_ui(self) -> None:
        """Configura la interfaz del widget."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Frame contenedor
        container = QFrame()
        container.setStyleSheet(self.STYLE_CONTAINER)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(16, 16, 16, 16)
        container_layout.setSpacing(12)
        
        # Título
        self.title_label = QLabel("📋 Órdenes de Fabricación")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setWeight(QFont.Weight.Bold)
        self.title_label.setFont(title_font)
        container_layout.addWidget(self.title_label)
        
        # Scroll area para las tarjetas
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; }")
        
        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(8)
        self.cards_layout.addStretch()
        
        scroll.setWidget(self.cards_container)
        container_layout.addWidget(scroll, 1)
        
        # Mensaje de estado
        self.status_label = QLabel("Seleccione un producto para ver sus órdenes")
        self.status_label.setStyleSheet("color: #94a3b8; font-size: 11px; font-style: italic;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(self.status_label)
        
        layout.addWidget(container)
    
    def load_orders_for_product(self, producto_codigo: str) -> None:
        """
        Carga las órdenes de fabricación de un producto.
        
        Args:
            producto_codigo: Código del producto
        """
        self._current_producto = producto_codigo
        self._clear_cards()
        
        self.title_label.setText(f"📋 Órdenes de: {producto_codigo}")
        self.status_label.setText("Cargando órdenes...")
        
        try:
            reports_model = self._get_reports_model()
            orders = reports_model.get_orders_for_product(producto_codigo) if reports_model else []
            
            self._display_orders(orders)
            
        except Exception as e:
            self.logger.error(f"Error cargando órdenes: {e}", exc_info=True)
            self.status_label.setText("Error al cargar órdenes")
    
    def _display_orders(self, orders: list[Any]) -> None:
        """Muestra las órdenes en tarjetas."""
        self._clear_cards()
        
        if not orders:
            self.status_label.setText("No hay órdenes para este producto")
            self.status_label.show()
            return
        
        self.status_label.hide()
        
        for order in orders:
            card = OrderCard(order)
            card.clicked.connect(self._on_order_clicked)
            self.cards_layout.insertWidget(self.cards_layout.count() - 1, card)
            self._order_cards.append(card)
        
        self.logger.info(f"Mostradas {len(orders)} órdenes")
    
    def _clear_cards(self) -> None:
        """Elimina todas las tarjetas."""
        for card in self._order_cards:
            self.cards_layout.removeWidget(card)
            card.deleteLater()
        self._order_cards = []
    
    def _on_order_clicked(self, orden_fabricacion: str) -> None:
        """Maneja clic en una orden."""
        self.select_order(orden_fabricacion)
        self.order_selected.emit(orden_fabricacion)

    def select_order(self, orden_fabricacion: str) -> None:
        """Marca visualmente una orden como seleccionada en la lista actual."""
        self._selected_order = orden_fabricacion
        for card in self._order_cards:
            card.set_selected(card.order_data.orden_fabricacion == orden_fabricacion)
    
    def set_report_service(self, report_service: Any) -> None:
        self._report_service = report_service
    
    def clear(self) -> None:
        """Limpia el widget."""
        self._clear_cards()
        self._current_producto = None
        self._selected_order = None
        self.title_label.setText("📋 Órdenes de Fabricación")
        self.status_label.setText("Seleccione un producto para ver sus órdenes")
        self.status_label.show()
