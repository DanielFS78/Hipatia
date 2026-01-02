# -*- coding: utf-8 -*-
"""
========================================================================
ORDER LIST WIDGET - Widget de Lista de Órdenes de Fabricación
========================================================================
Widget que muestra las órdenes de fabricación de un producto,
con información resumida y opción de expandir para ver detalles.
========================================================================
"""
import logging
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QSizePolicy, QSpacerItem
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor


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
    
    def __init__(self, order_data, parent=None):
        """
        Args:
            order_data: OrdenFabricacionResumenDTO
        """
        super().__init__(parent)
        self.order_data = order_data
        self.setStyleSheet(self.STYLE_CARD)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._setup_ui()
    
    def _setup_ui(self):
        """Configura la interfaz de la tarjeta."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)
        
        # Fila superior: OF y estado
        top_row = QHBoxLayout()
        
        of_label = QLabel(f"📋 {self.order_data.orden_fabricacion}")
        of_label.setFont(QFont("", 11, QFont.Weight.Bold))
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
    
    def mousePressEvent(self, event):
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
    
    def __init__(self, controller=None, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.logger = logging.getLogger("EvolucionTiemposApp.OrderListWidget")
        self._current_producto = None
        self._order_cards = []
        self._setup_ui()
    
    def _setup_ui(self):
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
        self.title_label.setFont(QFont("", 12, QFont.Weight.Bold))
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
    
    def load_orders_for_product(self, producto_codigo: str):
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
            if self.controller and hasattr(self.controller, 'model'):
                orders = self.controller.model.reports_obtener_ordenes_por_producto(
                    producto_codigo, limit=50
                )
            else:
                orders = []
            
            self._display_orders(orders)
            
        except Exception as e:
            self.logger.error(f"Error cargando órdenes: {e}", exc_info=True)
            self.status_label.setText("Error al cargar órdenes")
    
    def _display_orders(self, orders):
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
    
    def _clear_cards(self):
        """Elimina todas las tarjetas."""
        for card in self._order_cards:
            self.cards_layout.removeWidget(card)
            card.deleteLater()
        self._order_cards = []
    
    def _on_order_clicked(self, orden_fabricacion: str):
        """Maneja clic en una orden."""
        self.order_selected.emit(orden_fabricacion)
    
    def set_controller(self, controller):
        """Establece el controlador."""
        self.controller = controller
    
    def clear(self):
        """Limpia el widget."""
        self._clear_cards()
        self._current_producto = None
        self.title_label.setText("📋 Órdenes de Fabricación")
        self.status_label.setText("Seleccione un producto para ver sus órdenes")
        self.status_label.show()
