"""
Interfaz PyQt6 (`preproceso_dialog`): widgets, diálogos o recursos visuales conectados al flujo de usuario.
"""
from __future__ import annotations

import os
import logging
from datetime import datetime, date, timedelta, time
from typing import Any, Dict, List, Sequence, Set, cast

from core.services.time_calculator import CalculadorDeTiempos

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QDialogButtonBox, QListWidget,
    QListWidgetItem, QLabel, QCheckBox, QScrollArea,
    QWidget, QTableWidget, QTableWidgetItem, QSpinBox,
    QMessageBox, QComboBox, QTextEdit, QTreeWidget,
    QTreeWidgetItem, QDateEdit, QRadioButton, QButtonGroup,
    QFrame, QSizePolicy, QPlainTextEdit, QTabWidget,
    QHeaderView, QAbstractItemView, QTimeEdit, QApplication,
    QCompleter, QInputDialog, QFileDialog, QCalendarWidget,
    QGroupBox, QStackedWidget, QDateTimeEdit, QTreeWidgetItemIterator,
)

from PyQt6.QtCore import Qt, pyqtSignal, QEvent, QDate, QTimer, QTime, QPoint, QRectF
from PyQt6.QtGui import (
    QFont, QPixmap, QPainter, QColor, QBrush, QTextCharFormat, QIcon, QPen, QPalette,
    QPolygonF
)

class PreprocesoDialog(QDialog):
    """
    Diálogo para crear o editar un Preproceso, permitiendo la asignación
    de materiales (componentes).
    """
    def __init__(
        self,
        preproceso_existente: Any = None,
        all_materials: Sequence[Any] | None = None,
        material_port: Any = None,
        parent: Any = None,
    ) -> None:
        """
        Inicializa el diálogo de preproceso.

        Args:
            preproceso_existente: Datos del preproceso a editar (opcional).
            all_materials: Lista de todos los materiales disponibles.
            material_port: Controlador de producto / materiales (p. ej. ``ProductController``).
            parent: Widget padre.
        """
        super().__init__(parent)
        logging.info(f"PreprocesoDialog.__init__ called. material_port arg: {material_port}")
        self.preproceso_data = preproceso_existente
        self.all_materials: List[Any] = list(all_materials) if all_materials else []
        self.material_port = material_port
        self.assigned_material_ids: Set[int] = set()

        if self.preproceso_data:
            # Assume DTO (Phase 12C Compliance)
            self.assigned_material_ids = {int(comp.id) for comp in self.preproceso_data.componentes}

        title = "Editar Preproceso" if self.preproceso_data else "Crear Nuevo Preproceso"
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumSize(600, 500)
        self.setup_ui()

    def setup_ui(self) -> None:
        """Configura la interfaz gráfica del diálogo."""
        main_layout = QVBoxLayout(self)

        # --- Pestañas para organizar la información ---
        tab_widget = QTabWidget()
        main_layout.addWidget(tab_widget)

        # --- Pestaña 1: Datos Básicos ---
        basic_data_widget = QWidget()
        form_layout = QFormLayout(basic_data_widget)
        self.nombre_entry = QLineEdit()
        self.tiempo_entry = QLineEdit()
        self.descripcion_entry = QTextEdit()
        self.descripcion_entry.setMaximumHeight(80)
        form_layout.addRow("<b>Nombre:</b>", self.nombre_entry)
        form_layout.addRow("<b>Tiempo (minutos):</b>", self.tiempo_entry)
        form_layout.addRow("<b>Descripción:</b>", self.descripcion_entry)
        tab_widget.addTab(basic_data_widget, "📝 Datos Básicos")

        # --- Pestaña 2: Asignación de Componentes ---
        components_widget = QWidget()
        components_layout = QVBoxLayout(components_widget)
        components_layout.addWidget(QLabel("Seleccione los materiales que componen este preproceso:"))
        
        # Lista de materiales
        self.materials_list = QListWidget()
        self.materials_list.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        components_layout.addWidget(self.materials_list)

        # Botones de gestión de componentes (NUEVO)
        btns_layout = QHBoxLayout()
        add_btn = QPushButton("Añadir Componente")
        edit_btn = QPushButton("Editar Componente")
        del_btn = QPushButton("Eliminar Componente")
        btns_layout.addWidget(add_btn)
        btns_layout.addWidget(edit_btn)
        btns_layout.addWidget(del_btn)
        components_layout.addLayout(btns_layout)

        add_btn.clicked.connect(self._on_add_material)
        edit_btn.clicked.connect(self._on_edit_material)
        del_btn.clicked.connect(self._on_delete_material)

        tab_widget.addTab(components_widget, "🔩 Componentes")

        # Poblar datos si estamos editando
        if self.preproceso_data:
            # DTO Access (Phase 12C)
            self.nombre_entry.setText(self.preproceso_data.nombre)
            self.tiempo_entry.setText(str(getattr(self.preproceso_data, 'tiempo', 0.0)))
            self.descripcion_entry.setPlainText(self.preproceso_data.descripcion or '')

        self._populate_materials_list()
        
        # Botones
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

    def _populate_materials_list(self) -> None:
        """
        Rellena la lista con los materiales disponibles.
        Marca como seleccionados aquellos que ya pertenecen al preproceso.
        """
        self.materials_list.clear()
        for material in self.all_materials:
            # Assume MaterialDTO (Phase 12C Compliance)
            mat_id = material.id
            mat_desc = material.descripcion_componente
            mat_code = material.codigo_componente if hasattr(material, 'codigo_componente') else "N/A"
            
            item = QListWidgetItem(f"{mat_code} - {mat_desc}")
            item.setData(Qt.ItemDataRole.UserRole, mat_id)
            item.setData(Qt.ItemDataRole.UserRole + 1, mat_code) # Guardar codigo
            item.setData(Qt.ItemDataRole.UserRole + 2, mat_desc) # Guardar desc

            self.materials_list.addItem(item)
            if mat_id in self.assigned_material_ids:
                item.setSelected(True)

    def _refresh_data(self) -> None:
        """
        Recarga los materiales desde el modelo a través del controlador
        y actualiza la visualización de la lista.
        """
        if not self.material_port:
            return
        self.all_materials = list(self.material_port.material_service.get_all_materials_for_selection())
        
        # Guardamos la selección actual para restaurarla (si es que aún existen los items)
        # Nota: assigned_material_ids ya rastrea lo que queremos que esté seleccionado.
        # Pero si el usuario seleccionó cosas nuevas en la UI antes de añadir un nuevo item,
        # deberíamos actualizar assigned_material_ids primero.
        self._update_assigned_ids_from_selection()
        
        self._populate_materials_list()

    def _update_assigned_ids_from_selection(self) -> None:
        """
        Sincroniza el conjunto interno de IDs asignados con los elementos
        actualmente seleccionados en el widget de lista.
        """
        current_selection: Set[int] = set()
        for item in self.materials_list.selectedItems():
            raw_id = item.data(Qt.ItemDataRole.UserRole)
            if raw_id is not None:
                current_selection.add(int(raw_id))
        # Actualizamos assigned_material_ids con la selección actual en UI
        # (Mejor comportamiento: Mantener lo seleccionado visiblemente)
        self.assigned_material_ids = current_selection

    def _on_add_material(self) -> None:
        """Inicia el flujo para crear un nuevo componente/material en el sistema."""
        logging.info(f"_on_add_material clicked. Controller: {self.material_port}")
        if not self.material_port:
            return
        codigo, ok1 = QInputDialog.getText(self, "Añadir Componente", "Código:")
        if not (ok1 and codigo.strip()):
            return
        desc, ok2 = QInputDialog.getText(self, "Añadir Componente", "Descripción:")
        if not (ok2 and desc.strip()):
            return

        if self.material_port.handle_create_material(codigo, desc):
            self._refresh_data()

    def _on_edit_material(self) -> None:
        """Inicia el flujo para editar un componente existente seleccionado."""
        logging.info(f"_on_edit_material clicked. Controller: {self.material_port}")
        if not self.material_port:
            return
        selected_items = self.materials_list.selectedItems()
        # Nota: QListWidget en MultiSelection permite seleccionar varios.
        # Para editar, pedimos que seleccione solo uno (o tomamos el primero).
        if len(selected_items) != 1:
            QMessageBox.warning(self, "Selección Única", "Seleccione un único componente para editar.")
            return

        item = selected_items[0]
        mat_id = cast(int, item.data(Qt.ItemDataRole.UserRole))
        old_code = cast(str, item.data(Qt.ItemDataRole.UserRole + 1))
        old_desc = cast(str, item.data(Qt.ItemDataRole.UserRole + 2))

        new_code, ok1 = QInputDialog.getText(self, "Editar Componente", "Código:", text=old_code)
        if not (ok1 and new_code.strip()):
            return
        new_desc, ok2 = QInputDialog.getText(self, "Editar Componente", "Descripción:", text=old_desc)
        if not (ok2 and new_desc.strip()):
            return

        if self.material_port.handle_update_material(mat_id, new_code, new_desc):
            self._refresh_data()

    def _on_delete_material(self) -> None:
        """
        Elimina los componentes seleccionados del sistema completo.
        Requiere confirmación del usuario debido al impacto global.
        """
        logging.info(f"_on_delete_material clicked. Controller: {self.material_port}")
        if not self.material_port:
            return
        selected_items = self.materials_list.selectedItems()
        if not selected_items:
             QMessageBox.warning(self, "Selección", "Seleccione componente(s) para eliminar.")
             return
        
        if QMessageBox.question(self, "Confirmar Eliminación", 
                                "¿Está seguro de eliminar los componentes seleccionados DEL SISTEMA COMPLETO?\n"
                                "Esto afectará a todos los productos y preprocesos que los usen.",
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
            return

        for item in selected_items:
            mat_id = cast(int, item.data(Qt.ItemDataRole.UserRole))
            self.material_port.handle_delete_material(mat_id)
            # Removemos del set assigned para que no intente re-seleccionarlo
            if mat_id in self.assigned_material_ids:
                self.assigned_material_ids.remove(mat_id)
        
        self._refresh_data()

    def get_data(self) -> Dict[str, Any] | None:
        """
        Recolecta los datos del formulario y los devuelve como un diccionario.

        Returns:
            Diccionario con datos del preproceso o None si la validación falla.
        """
        nombre = self.nombre_entry.text().strip()
        if not nombre:
            QMessageBox.warning(self, "Campo Requerido", "El nombre del preproceso es obligatorio.")
            return None
        try:
            tiempo = float(self.tiempo_entry.text().strip().replace(",", "."))
            if tiempo < 0: raise ValueError
        except (ValueError, TypeError):
            QMessageBox.warning(self, "Dato Inválido", "El tiempo debe ser un número positivo (o cero).")
            return None

        # Sincronizamos selección final
        self._update_assigned_ids_from_selection()
        
        return {
            "nombre": nombre,
            "descripcion": self.descripcion_entry.toPlainText().strip(),
            "tiempo": tiempo,
            "componentes_ids": list(self.assigned_material_ids)
        }
