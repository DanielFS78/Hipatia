# -*- coding: utf-8 -*-
"""
Nombre del Módulo: products_widget
Descripción: Widget de catálogo de productos (búsqueda, formulario, subfabricaciones y procesos).
             Emite señales hacia ``ProductController`` e incluye entrada para importar BOM A3RP.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from core.dtos import SubfabricacionDTO
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QListWidget,
    QListWidgetItem, QLabel, QFrame, QPushButton, QFormLayout,
    QComboBox, QTextEdit, QDialog, QCheckBox,
)
from PyQt6.QtCore import pyqtSignal, Qt

_logger = logging.getLogger(__name__)


def _subfabricacion_row_from_domain(sub: Any) -> dict[str, Any]:
    """
    Serializa una subfabricación de dominio a dict para el formulario y persistencia.

    Args:
        sub: ``SubfabricacionDTO`` o objeto con atributos homólogos.

    Returns:
        Diccionario con claves ``id``, ``descripcion``, ``tiempo``, ``tipo_trabajador``, ``maquina_id``.
    """
    if isinstance(sub, SubfabricacionDTO):
        return {
            "id": sub.id,
            "descripcion": sub.descripcion,
            "tiempo": sub.tiempo,
            "tipo_trabajador": sub.tipo_trabajador,
            "maquina_id": sub.maquina_id,
        }
    return {
        "id": getattr(sub, "id", None),
        "descripcion": getattr(sub, "descripcion", "") or "",
        "tiempo": getattr(sub, "tiempo", 0.0),
        "tipo_trabajador": getattr(sub, "tipo_trabajador", 1),
        "maquina_id": getattr(sub, "maquina_id", None),
    }


class ProductsWidget(QWidget):
    """
    Vista principal de la pestaña Productos: lista, detalle editable y accesos a diálogos relacionados.

    Resuelve ``ProductController`` vía ``DIContainer`` en ``__init__`` (patrón sin ``AppController`` en el widget).
    """
    save_product_signal = pyqtSignal(str)
    delete_product_signal = pyqtSignal(str)
    manage_subs_signal = pyqtSignal()
    manage_procesos_signal = pyqtSignal()
    manage_details_signal = pyqtSignal(str)
    search_or_add_signal = pyqtSignal(str)
    import_bom_signal = pyqtSignal()

    results_list: Optional[QListWidget] = None
    search_entry: Optional[QLineEdit] = None
    current_subfabricaciones: List[Dict[str, Any]] = []
    current_procesos_mecanicos: List[Dict[str, Any]] = []
    form_widgets: Dict[str, Any] = {}

    def __init__(self, _app_controller: Any = None, parent: Optional[QWidget] = None) -> None:
        """`_app_controller` se ignora (compat ``MainView``); dependencias vía DI."""
        super().__init__(parent)
        from core.di_container import DIContainer
        from controllers.product_controller_v2 import ProductController
        self.product_controller = DIContainer.get_instance().resolve(ProductController)
        self.current_subfabricaciones = []
        self.current_procesos_mecanicos = []
        self.form_widgets = {}

        main_layout = QHBoxLayout(self)
        left_panel = QFrame(); left_layout = QVBoxLayout(left_panel); left_panel.setMaximumWidth(450)
        
        # Botones de acción superior
        top_btn_layout = QHBoxLayout()
        self.import_btn = QPushButton("📥 Importar Estructura A3RP")
        self.import_btn.setStyleSheet("background-color: #3498db; color: white; font-weight: bold; padding: 5px;")
        self.import_btn.clicked.connect(self.import_bom_signal.emit)
        top_btn_layout.addStretch()
        top_btn_layout.addWidget(self.import_btn)
        
        left_layout.addWidget(QLabel("<h2>Gestión de Productos</h2>"))
        left_layout.addLayout(top_btn_layout)

        self.search_entry = QLineEdit(); self.search_entry.setPlaceholderText("Buscar o Añadir producto...")
        search_entry = self.search_entry
        search_entry.returnPressed.connect(lambda: self.search_or_add_signal.emit(search_entry.text().strip()))
        left_layout.addWidget(QLabel("<b>Buscar o Añadir Producto:</b>")); left_layout.addWidget(self.search_entry)
        self.results_list = QListWidget(); left_layout.addWidget(self.results_list)
        main_layout.addWidget(left_panel)

        self.edit_area_container = QFrame(); self.edit_area_container_layout = QVBoxLayout(self.edit_area_container)
        main_layout.addWidget(self.edit_area_container, 1)
        self.clear_edit_area()

    def update_search_results(self, results: list[Any]) -> None:
        if self.results_list is None: return
        results_list = self.results_list
        results_list.clear()
        for product in results:
            iterations = (
                self.product_controller.product_service.get_product_iterations(product.codigo)
                if self.product_controller
                else []
            )
            item_text = f"📜 {product.codigo} | {product.descripcion}" if iterations else f"{product.codigo} | {product.descripcion}"
            item = QListWidgetItem(item_text); item.setData(Qt.ItemDataRole.UserRole, product.codigo)
            results_list.addItem(item)

    def clear_edit_area(self, show_placeholder: bool = True) -> None:
        layout = self.edit_area_container_layout
        if layout:
            while layout.count():
                item = layout.takeAt(0)
                if not item: continue
                
                widget = item.widget()
                if widget:
                    widget.deleteLater()
                    continue

                sub_layout = item.layout()
                if sub_layout:
                    # Usamos una lista para evitar problemas al modificar mientras iteramos
                    items = [sub_layout.takeAt(0) for _ in range(sub_layout.count())]
                    for si in items:
                        if si:
                            child_widget = si.widget()
                            if child_widget:
                                child_widget.deleteLater()
        
        self.form_widgets = {}; self.current_subfabricaciones = []; self.current_procesos_mecanicos = []
        if show_placeholder:
            placeholder = QLabel("Seleccione un producto para ver sus detalles.")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.edit_area_container_layout.addWidget(placeholder)

    def display_product_form(self, data: Any, sub_data: list[Any], is_new: bool = False) -> None:
        """
        Muestra el formulario para editar un producto o crear uno nuevo.

        Args:
            data: DTO del producto o código (si es nuevo).
            sub_data: Lista de subfabricaciones existentes.
            is_new: Si es True, configura el formulario para creación.
        """
        self.clear_edit_area(show_placeholder=False)
        
        # Sincronizar subfabricaciones: si es nuevo y sub_data está vacío, empezamos limpio.
        # Si sub_data trae algo (porque el usuario ya añadió en esta sesión), lo preservamos.
        if sub_data:
            self.current_subfabricaciones = [
                _subfabricacion_row_from_domain(s) for s in sub_data
            ]
        else:
             self.current_subfabricaciones = []

        self.current_procesos_mecanicos = []

        form_layout = QFormLayout()
        self.form_widgets['codigo'] = QLineEdit(data.codigo if not isinstance(data, str) else data)
        self.form_widgets['descripcion'] = QLineEdit(data.descripcion if not isinstance(data, str) else "")
        self.form_widgets['departamento'] = QComboBox(); self.form_widgets['departamento'].addItems(["Mecánica", "Electrónica", "Montaje"])
        
        if not is_new and not isinstance(data, str):
            self.form_widgets['departamento'].setCurrentText(data.departamento)
            
        self.form_widgets['donde'] = QTextEdit(data.donde if not isinstance(data, str) else ""); self.form_widgets['donde'].setFixedHeight(80)
        
        # Switch: DTO, filas de subfabricación cargadas desde BD, o borrador en memoria (producto nuevo).
        has_subs = False
        if not isinstance(data, str):
            has_subs = bool(data.tiene_subfabricaciones)
        if sub_data and len(sub_data) > 0:
            has_subs = True
        elif isinstance(data, str) and self.current_subfabricaciones:
            has_subs = True

        self.form_widgets['sub_switch'] = QCheckBox("¿Tiene subfabricaciones?"); self.form_widgets['sub_switch'].setChecked(has_subs)

        # Campos adicionales para productos sin subfabricaciones (usados al crear nuevo)
        self.form_widgets['trabajador_menu'] = QComboBox()
        self.form_widgets['trabajador_menu'].addItems(["Tipo 1", "Tipo 2", "Tipo 3"])
        self.form_widgets['tiempo_optimo'] = QLineEdit()

        self.form_widgets['manage_subs_button'] = QPushButton("➕ GESTIONAR SUB-FABRICACIONES")
        self.form_widgets['manage_subs_button'].setMinimumHeight(40)
        self.form_widgets['manage_subs_button'].setStyleSheet("background-color: #27ae60; color: white; font-weight: bold;")
        self.form_widgets['manage_subs_button'].clicked.connect(self.manage_subs_signal.emit)
        
        self.form_widgets['manage_procesos_button'] = QPushButton("⚙️ Gestionar Procesos Mecánicos")
        self.form_widgets['manage_procesos_button'].clicked.connect(self.manage_procesos_signal.emit)
        
        form_layout.addRow("Código:", self.form_widgets['codigo']); form_layout.addRow("Descripción:", self.form_widgets['descripcion'])
        form_layout.addRow("Departamento:", self.form_widgets['departamento']); form_layout.addRow("Dónde se ubica:", self.form_widgets['donde'])
        
        self.form_widgets['details_container'] = QWidget()
        details_layout = QFormLayout(self.form_widgets['details_container'])
        details_layout.addRow("Tipo de Trabajador:", self.form_widgets['trabajador_menu'])
        details_layout.addRow("Tiempo Óptimo (min):", self.form_widgets['tiempo_optimo'])
        
        self.edit_area_container_layout.addLayout(form_layout)
        self.edit_area_container_layout.addWidget(self.form_widgets['sub_switch'])
        self.edit_area_container_layout.addWidget(self.form_widgets['details_container'])
        self.edit_area_container_layout.addWidget(self.form_widgets['manage_subs_button'])
        self.edit_area_container_layout.addWidget(self.form_widgets['manage_procesos_button'])

        # Botón de detalles/iteraciones solo para productos existentes
        if not is_new:
            self.form_widgets['manage_details_button'] = QPushButton("Gestionar Componentes e Iteraciones")
            self.form_widgets['manage_details_button'].clicked.connect(lambda: self.manage_details_signal.emit(data.codigo))
            self.edit_area_container_layout.addWidget(self.form_widgets['manage_details_button'])

        button_layout = QHBoxLayout(); save_btn = QPushButton("Guardar Cambios" if not is_new else "Crear Producto")
        save_btn.clicked.connect(lambda: self.save_product_signal.emit(self.form_widgets['codigo'].text()))
        
        button_layout.addWidget(save_btn)
        
        if not is_new:
            delete_btn = QPushButton("Eliminar Producto")
            delete_btn.clicked.connect(lambda: self.delete_product_signal.emit(data.codigo))
            button_layout.addWidget(delete_btn)
            
        self.edit_area_container_layout.addLayout(button_layout)
        self.edit_area_container_layout.addStretch()

        def toggle_subs() -> None:
            is_checked = self.form_widgets['sub_switch'].isChecked()
            self.form_widgets['manage_subs_button'].setVisible(is_checked)
            self.form_widgets['details_container'].setVisible(not is_checked)
            _logger.debug(
                "Sub-switch toggled: %s. manage_subs visible=%s",
                is_checked,
                self.form_widgets["manage_subs_button"].isVisible(),
            )
            
        self.form_widgets['sub_switch'].toggled.connect(toggle_subs)
        # Forzar estado inicial explícitamente
        toggle_subs()

    def get_product_form_data(self) -> dict[str, Any]:
        data = {
            "codigo": self.form_widgets['codigo'].text().strip(), 
            "descripcion": self.form_widgets['descripcion'].text().strip(),
            "departamento": self.form_widgets['departamento'].currentText(), 
            "donde": self.form_widgets['donde'].toPlainText().strip(),
            "tiene_subfabricaciones": 1 if self.form_widgets['sub_switch'].isChecked() else 0,
            "tiempo_optimo": 0, 
            "tipo_trabajador": 1, 
            "sub_partes": self.current_subfabricaciones,
            "procesos_mecanicos": self.current_procesos_mecanicos
        }
        if not data["tiene_subfabricaciones"]:
            data["tiempo_optimo"] = self.form_widgets['tiempo_optimo'].text().replace(",", ".")
            try:
                text = self.form_widgets['trabajador_menu'].currentText()
                data["tipo_trabajador"] = text.split(" ")[-1] if " " in text else text
            except Exception:
                data["tipo_trabajador"] = "1"
        return data

    def clear_all(self) -> None:
        if self.search_entry: self.search_entry.clear()
        if self.results_list: self.results_list.clear()
        self.clear_edit_area()
