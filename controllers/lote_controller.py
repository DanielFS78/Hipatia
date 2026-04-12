# -*- coding: utf-8 -*-
"""
Nombre del Módulo: lote_controller
Descripción: Gestiona la lógica de plantillas de lotes, incluyendo su definición, 
             búsqueda y la actualización de su contenido en la interfaz de cálculo.
"""
from __future__ import annotations

import logging
from typing import Any
from PyQt6.QtCore import QObject, pyqtSignal, Qt
from PyQt6.QtWidgets import QTableWidgetItem, QSpinBox
from database.database_manager import DatabaseManager


class LoteController(QObject):
    """
    Controlador dedicado a la gestión de lotes y sus plantillas.
    
    Permite el filtrado de lotes existentes, la actualización dinámica de su 
    contenido en tablas editables y la delegación de operaciones de persistencia 
    al controlador de pilas.
    """
    
    # Signals
    lotes_updated = pyqtSignal()
    lote_content_updated = pyqtSignal()
    
    def __init__(self, db_manager: DatabaseManager, view: Any, pila_controller: Any, logger: logging.Logger) -> None:
        """
        Inicializa el controlador de lotes.

        Args:
            db_manager: Instancia del gestor de base de datos.
            view: Referencia a la vista principal.
            pila_controller: Controlador de pilas para operaciones delegadas.
            logger: Instancia de logging.
        """
        super().__init__()
        self.db: DatabaseManager = db_manager
        self.view: Any = view
        self.pila_controller: Any = pila_controller
        self.logger: logging.Logger = logger
        self.current_lote_content: list[dict[str, Any]] = []
        
    def connect_signals(self) -> None:
        """Conecta las señales del widget de lotes."""
        # Las señales ya están delegadas a PilaController
        self.pila_controller._connect_lotes_management_signals()
        
    def connect_definir_lote_signals(self) -> None:
        """Conecta las señales del widget para definir plantillas de Lote."""
        # Delegado a PilaController
        # Esta lógica ya está implementada en app_controller._connect_definir_lote_signals
        pass
        
    def update_lotes_view(self) -> None:
        """Actualiza la vista de lotes."""
        # Delegado a PilaController
        self.pila_controller.update_lotes_view()
        self.lotes_updated.emit()
        
    def update_lote_content_table(self) -> None:
        """
        Refresca la tabla de contenido del lote en la interfaz de cálculo.
        Construye filas con controles interactivos (SpinBox) para gestionar cantidades.
        """
        calc_page = self.view.get_page("calculate")
        if not calc_page:
            return

        calc_page.pila_content_table.setRowCount(0)  # Limpiar tabla
        for row, item in enumerate(self.current_lote_content):
            calc_page.pila_content_table.insertRow(row)

            # Columna 0: Código
            item_code = QTableWidgetItem(item.get("codigo"))
            item_code.setData(Qt.ItemDataRole.UserRole, item)  # Guardamos todo el dict
            calc_page.pila_content_table.setItem(row, 0, item_code)

            # Columna 1: Descripción
            calc_page.pila_content_table.setItem(row, 1, QTableWidgetItem(item.get("descripcion")))

            # Columna 2: Cantidad (editable)
            qty_spinbox = QSpinBox()
            qty_spinbox.setRange(1, 99999)
            qty_spinbox.setValue(item.get("cantidad", 1))
            # Conectamos señal para actualizar el dato si el usuario cambia la cantidad
            qty_spinbox.valueChanged.connect(
                lambda value, r=row: self.current_lote_content[r].update({"cantidad": value}))
            calc_page.pila_content_table.setCellWidget(row, 2, qty_spinbox)

            # Columna 3: Origen
            calc_page.pila_content_table.setItem(row, 3, QTableWidgetItem(str(item.get("origen", ""))))
            
        self.lote_content_updated.emit()
        
    def on_calc_lote_search_changed(self, text: str) -> None:
        """
        Maneja cambios en la búsqueda de lotes.
        
        Args:
            text: Texto de búsqueda
        """
        # Delegado a PilaController
        self.pila_controller._on_calc_lote_search_changed(text)
        
    def set_current_lote_content(self, content: list[dict[str, Any]]) -> None:
        """
        Establece el contenido actual del lote.
        
        Args:
            content: Lista de items del lote
        """
        self.current_lote_content = content
        self.update_lote_content_table()
