# -*- coding: utf-8 -*-
"""
Interfaz PyQt6 (`smart_search`): widgets, diálogos o recursos visuales conectados al flujo de usuario.
"""

import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLineEdit, QListWidget, QListWidgetItem,
    QLabel, QHBoxLayout, QFrame
)
from PyQt6.QtCore import pyqtSignal, Qt, QTimer
from PyQt6.QtGui import QIcon, QAction
from typing import Any

class SmartSearchWidget(QWidget):
    """
    Widget de búsqueda inteligente que ofrece autocompletado y
    filtrado en tiempo real para el módulo de reportes.
    """
    # Señal emitida cuando se selecciona un resultado
    # Args: tipo (str), codigo (str)
    result_selected = pyqtSignal(str, str)
    # Señal emitida cuando se limpia la búsqueda
    search_cleared = pyqtSignal()

    def __init__(
        self,
        app_model: Any,
        parent: Any = None,
        *,
        report_service: Any = None,
    ) -> None:
        super().__init__(parent)
        self.app_model = app_model
        self._report_service = report_service
        self.logger = logging.getLogger("EvolucionTiemposApp.SmartSearch")
        self._last_query_executed: str = ""
        
        # Estado interno
        self.debounce_timer = QTimer()
        self.debounce_timer.setSingleShot(True)
        self.debounce_timer.setInterval(300)  # 300ms de espera
        self.debounce_timer.timeout.connect(self._perform_search)
        
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # --- Campo de Búsqueda ---
        search_container = QWidget()
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.setSpacing(0)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar producto, OF o tarea...")
        self.search_input.setFixedHeight(40)
        self.search_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                padding: 0 12px;
                background-color: white;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #2563eb;
            }
        """)
        
        self.search_input.textChanged.connect(self._on_text_changed)
        
        search_layout.addWidget(self.search_input)
        layout.addWidget(search_container)

        # --- Lista de Resultados (Flotante o Debajo) ---
        # Para simplificar, en esta fase la ponemos debajo, pero colapsada si no hay resultados.
        self.results_list = QListWidget()
        self.results_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                background-color: white;
                outline: none;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #f1f5f9;
            }
            QListWidget::item:selected {
                background-color: #eff6ff;
                color: #1e293b;
            }
            QListWidget::item:hover {
                background-color: #f8fafc;
            }
        """)
        self.results_list.itemClicked.connect(self._on_item_clicked)
        self.results_list.hide() # Oculta inicialmente
        
        # Altura máxima para no ocupar toda la pantalla
        self.results_list.setMaximumHeight(300)
        
        layout.addWidget(self.results_list)

    def _on_text_changed(self, text: str) -> None:
        """Maneja el cambio de texto con debounce."""
        if len(text.strip()) < 2:
            self.results_list.hide()
            self.results_list.clear()
            if not text.strip():
                self.search_cleared.emit()
            return
            
        self.debounce_timer.start()

    def _perform_search(self) -> None:
        """Ejecuta la búsqueda contra el AppModel."""
        query = self.search_input.text().strip()
        if not query:
            return
        if query.lower() == self._last_query_executed:
            return
        
        api = self._report_api()
        if not api:
            self.logger.warning("No hay servicio de reportes ni AppModel configurado para buscar.")
            return

        self.logger.info(f"Buscando: {query}")
        
        try:
            results = api.search_reports_data(query)
            self._last_query_executed = query.lower()
            self._update_results_list(results)
        except Exception as e:
            self.logger.error(f"Error en búsqueda: {e}")
            # Podría mostrar un mensaje de error en la lista vacía

    def _update_results_list(self, results: list[Any]) -> None:
        """Actualiza la lista visual de resultados."""
        self.results_list.clear()
        
        if not results:
            self.results_list.hide()
            return
            
        self.results_list.show()
        
        for dto in results:
            item = QListWidgetItem()
            # Usamos setData para guardar el objeto completo o sus partes clave
            item.setData(Qt.ItemDataRole.UserRole, dto)
            
            # Crear un widget personalizado para la fila es mejor, pero text simple por ahora
            tipo_icon = "📦" if dto.tipo == 'producto' else "🏭" if dto.tipo == 'fabricacion' else "📄"
            display_text = f"{tipo_icon}  {dto.codigo} - {dto.descripcion}"
            
            item.setText(display_text)
            self.results_list.addItem(item)

    def _on_item_clicked(self, item: Any) -> None:
        """Maneja el clic en un resultado."""
        dto = item.data(Qt.ItemDataRole.UserRole)
        if dto:
            self.logger.info(f"Seleccionado: {dto.tipo} - {dto.codigo}")
            self.result_selected.emit(dto.tipo, dto.codigo)
            
            # Opcional: limpiar búsqueda o mantenerla
            self.results_list.hide()
            # self.search_input.setText(dto.codigo) # Feedback visual

    def _report_api(self) -> Any:
        if self._report_service is not None:
            return self._report_service
        return self.app_model

    def set_report_service(self, report_service: Any) -> None:
        """Prioridad sobre `app_model` cuando el DI expone ReportService (B5)."""
        self._report_service = report_service

    def clear_search(self) -> None:
        """Limpia el campo de búsqueda y resultados."""
        self._last_query_executed = ""
        self.search_input.clear()
        self.results_list.clear()
        self.results_list.hide()
        self.search_cleared.emit()

    def set_controller(self, controller: Any) -> None:
        """Actualiza el modelo desde el controlador."""
        if controller is None:
            self.app_model = None
            return
        if hasattr(controller, "search_reports_data"):
            self.app_model = controller
            return
        if hasattr(controller, "model"):
            self.app_model = controller.model
