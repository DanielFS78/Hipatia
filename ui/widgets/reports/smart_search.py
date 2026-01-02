# -*- coding: utf-8 -*-
"""
========================================================================
SMART SEARCH WIDGET - Widget de Búsqueda Inteligente
========================================================================
Widget que proporciona búsqueda en tiempo real con autocompletado
para productos, fabricaciones y órdenes de fabricación.

Características:
- Debounce de 300ms para evitar consultas excesivas
- Resultados agrupados por tipo (producto/orden)
- Iconos visuales para distinguir tipos
- Selección mediante clic o Enter
========================================================================
"""
import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor, QIcon


class SmartSearchWidget(QWidget):
    """
    Widget de búsqueda inteligente con autocompletado.
    
    Signals:
        result_selected(str, str): Emitido cuando se selecciona un resultado.
            - tipo: 'producto' o 'orden'
            - codigo: Código del elemento seleccionado
        search_cleared: Emitido cuando se limpia la búsqueda.
    """
    
    result_selected = pyqtSignal(str, str)  # (tipo, codigo)
    search_cleared = pyqtSignal()
    
    # Constantes de estilo
    STYLE_FRAME = """
        QFrame {
            background-color: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
        }
    """
    STYLE_SEARCH_INPUT = """
        QLineEdit {
            padding: 12px 16px;
            font-size: 14px;
            border: 2px solid #e2e8f0;
            border-radius: 6px;
            background-color: white;
        }
        QLineEdit:focus {
            border-color: #2563eb;
        }
    """
    STYLE_LIST = """
        QListWidget {
            border: none;
            background-color: transparent;
            font-size: 13px;
        }
        QListWidget::item {
            padding: 10px 12px;
            border-bottom: 1px solid #e2e8f0;
            border-radius: 4px;
            margin: 2px 0;
        }
        QListWidget::item:hover {
            background-color: #eff6ff;
        }
        QListWidget::item:selected {
            background-color: #dbeafe;
            color: #1e40af;
        }
    """
    
    def __init__(self, controller=None, parent=None):
        """
        Inicializa el widget de búsqueda inteligente.
        
        Args:
            controller: Controlador de la aplicación (para acceder al modelo)
            parent: Widget padre
        """
        super().__init__(parent)
        self.controller = controller
        self.logger = logging.getLogger("EvolucionTiemposApp.SmartSearchWidget")
        
        # Timer para debounce
        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(300)  # 300ms de debounce
        self._search_timer.timeout.connect(self._perform_search)
        
        # Último término buscado (evitar búsquedas duplicadas)
        self._last_query = ""
        
        # Resultados actuales
        self._current_results = []
        
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        """Configura la interfaz de usuario."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        # Frame contenedor
        container = QFrame()
        container.setStyleSheet(self.STYLE_FRAME)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(16, 16, 16, 16)
        container_layout.setSpacing(12)
        
        # Título
        title_label = QLabel("🔍 Buscar Producto u Orden")
        title_label.setFont(QFont("", 12, QFont.Weight.Bold))
        container_layout.addWidget(title_label)
        
        # Campo de búsqueda
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Escriba código o descripción...")
        self.search_input.setStyleSheet(self.STYLE_SEARCH_INPUT)
        self.search_input.setClearButtonEnabled(True)
        container_layout.addWidget(self.search_input)
        
        # Lista de resultados
        results_label = QLabel("Resultados")
        results_label.setStyleSheet("color: #64748b; font-size: 11px;")
        container_layout.addWidget(results_label)
        
        self.results_list = QListWidget()
        self.results_list.setStyleSheet(self.STYLE_LIST)
        self.results_list.setMinimumHeight(200)
        self.results_list.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        container_layout.addWidget(self.results_list, 1)
        
        # Mensaje de estado
        self.status_label = QLabel("Introduzca al menos 2 caracteres para buscar")
        self.status_label.setStyleSheet("color: #94a3b8; font-size: 11px; font-style: italic;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(self.status_label)
        
        layout.addWidget(container)
    
    def _connect_signals(self):
        """Conecta las señales internas."""
        self.search_input.textChanged.connect(self._on_text_changed)
        self.results_list.itemClicked.connect(self._on_item_clicked)
        self.results_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.search_input.returnPressed.connect(self._on_enter_pressed)
    
    def _on_text_changed(self, text: str):
        """Maneja cambios en el texto de búsqueda con debounce."""
        text = text.strip()
        
        if len(text) < 2:
            self._search_timer.stop()
            self.results_list.clear()
            self._current_results = []
            
            if len(text) == 0:
                self.status_label.setText("Introduzca al menos 2 caracteres para buscar")
                self.search_cleared.emit()
            else:
                self.status_label.setText("Introduzca al menos 2 caracteres...")
            return
        
        # Reiniciar timer de debounce
        self._search_timer.stop()
        self._search_timer.start()
        self.status_label.setText("Buscando...")
    
    def _perform_search(self):
        """Ejecuta la búsqueda real después del debounce."""
        query = self.search_input.text().strip()
        
        if query == self._last_query:
            return  # Evitar búsqueda duplicada
        
        self._last_query = query
        
        if len(query) < 2:
            return
        
        self.logger.info(f"Buscando: '{query}'")
        
        try:
            # Obtener resultados del modelo a través del controlador
            if self.controller and hasattr(self.controller, 'model'):
                results = self.controller.model.reports_buscar_por_codigo(query, limit=20)
            else:
                results = []
                self.logger.warning("No hay controlador disponible para realizar búsqueda")
            
            self._display_results(results)
            
        except Exception as e:
            self.logger.error(f"Error en búsqueda: {e}", exc_info=True)
            self.status_label.setText("Error al buscar. Intente de nuevo.")
            self.results_list.clear()
    
    def _display_results(self, results):
        """Muestra los resultados en la lista."""
        self.results_list.clear()
        self._current_results = results
        
        if not results:
            self.status_label.setText("No se encontraron resultados")
            return
        
        for result in results:
            item = QListWidgetItem()
            
            # Determinar icono según tipo
            if result.tipo == 'producto':
                icon_text = "📦"
                tipo_text = "Producto"
            elif result.tipo == 'orden':
                icon_text = "📋"
                tipo_text = "Orden"
            else:
                icon_text = "📄"
                tipo_text = result.tipo.capitalize()
            
            # Formatear texto
            display_text = f"{icon_text} {result.codigo}"
            if result.descripcion:
                display_text += f"\n    {result.descripcion[:50]}"
            if result.total_unidades > 0:
                display_text += f" ({result.total_unidades} uds)"
            
            item.setText(display_text)
            item.setData(Qt.ItemDataRole.UserRole, {
                'tipo': result.tipo,
                'codigo': result.codigo
            })
            
            # Color de fondo según tipo
            if result.tipo == 'producto':
                item.setBackground(QColor("#f0fdf4"))  # Verde muy claro
            elif result.tipo == 'orden':
                item.setBackground(QColor("#fef3c7"))  # Amarillo muy claro
            
            self.results_list.addItem(item)
        
        self.status_label.setText(f"{len(results)} resultado(s) encontrado(s)")
    
    def _on_item_clicked(self, item: QListWidgetItem):
        """Maneja clic en un elemento de la lista."""
        data = item.data(Qt.ItemDataRole.UserRole)
        if data:
            self.result_selected.emit(data['tipo'], data['codigo'])
    
    def _on_item_double_clicked(self, item: QListWidgetItem):
        """Maneja doble clic en un elemento (mismo comportamiento que clic simple)."""
        self._on_item_clicked(item)
    
    def _on_enter_pressed(self):
        """Maneja la tecla Enter - selecciona el primer resultado."""
        if self.results_list.count() > 0:
            first_item = self.results_list.item(0)
            self.results_list.setCurrentItem(first_item)
            self._on_item_clicked(first_item)
    
    def clear_search(self):
        """Limpia la búsqueda y resultados."""
        self.search_input.clear()
        self.results_list.clear()
        self._current_results = []
        self._last_query = ""
        self.status_label.setText("Introduzca al menos 2 caracteres para buscar")
    
    def set_controller(self, controller):
        """Establece el controlador para acceder al modelo."""
        self.controller = controller
    
    def get_selected_result(self):
        """Retorna el resultado actualmente seleccionado."""
        current_item = self.results_list.currentItem()
        if current_item:
            return current_item.data(Qt.ItemDataRole.UserRole)
        return None
