"""
Interfaz PyQt6 (`prep_groups_dialog`): widgets, diálogos o recursos visuales conectados al flujo de usuario.
"""
from __future__ import annotations

import os
import logging
from datetime import datetime, date, timedelta, time
from typing import Any, Tuple, cast
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

from .prep_steps_dialog import PrepStepsDialog

class PrepGroupsDialog(QDialog):
    """
    Diálogo para gestionar los Grupos de Preparación de una máquina.
    Permite organizar fases de preparación en grupos lógicos.
    """

    def __init__(
        self,
        machine_id: int,
        machine_name: str,
        controller: Any,
        parent: Any = None,
    ) -> None:
        """
        Inicializa el diálogo de grupos de preparación.

        Args:
            machine_id: ID de la máquina.
            machine_name: Nombre de la máquina.
            controller: Controlador de máquinas.
            parent: Widget padre.
        """
        super().__init__(parent)
        self.setWindowTitle(f"Grupos de Preparación para: {machine_name}")
        self.setMinimumSize(800, 500)
        from core.di_container import DIContainer
        from core.app_model import AppModel
        self.app_model = DIContainer.get_instance().resolve(AppModel)
        self.machine_id = machine_id
        self.controller = controller # MachineController
        self.products = self.app_model.search_products("")
        self.current_group_id: int | None = None

        main_layout = QHBoxLayout(self)

        # --- Panel izquierdo ---
        left_panel = QFrame()
        left_layout = QVBoxLayout(left_panel)
        left_layout.addWidget(QLabel("<b>Grupos de esta Máquina</b>"))
        self.groups_list = QListWidget()
        self.groups_list.itemSelectionChanged.connect(self._on_group_selected)
        left_layout.addWidget(self.groups_list)
        group_buttons = QHBoxLayout()
        add_group_btn = QPushButton("Añadir Grupo")
        delete_group_btn = QPushButton("Eliminar Grupo")
        manage_steps_btn = QPushButton("Gestionar Pasos del Grupo")
        group_buttons.addWidget(add_group_btn)
        group_buttons.addWidget(delete_group_btn)
        left_layout.addLayout(group_buttons)
        left_layout.addWidget(manage_steps_btn)

        # --- Panel derecho (Formulario) ---
        right_panel = QFrame()
        self.form_layout = QFormLayout(right_panel)
        self.group_name_edit = QLineEdit()
        self.group_desc_edit = QTextEdit()

        # ComboBox editable y con autocompletado
        self.product_combo = QComboBox()
        self.product_combo.setEditable(True)
        self.product_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.product_combo.addItem("Ninguno", None)

        product_list_for_completer = []
        for product in self.products:
            display_text = f"{product.codigo} - {product.descripcion}"
            self.product_combo.addItem(display_text, product.codigo)
            product_list_for_completer.append(display_text)

        completer = QCompleter(product_list_for_completer, self)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.product_combo.setCompleter(completer)

        self.save_group_btn = QPushButton("Guardar Cambios")

        self.form_layout.addRow("Nombre del Grupo:", self.group_name_edit)
        self.form_layout.addRow("Producto Asociado (Opcional):", self.product_combo)
        self.form_layout.addRow("Descripción:", self.group_desc_edit)
        self.form_layout.addWidget(self.save_group_btn)

        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(right_panel, 2)

        # Conexiones
        add_group_btn.clicked.connect(self._add_group)
        delete_group_btn.clicked.connect(self._delete_group)
        self.save_group_btn.clicked.connect(self._save_group)
        manage_steps_btn.clicked.connect(self._manage_steps)

        self._load_groups()
        self._toggle_form(False)

    def _toggle_form(self, enabled: bool) -> None:
        """Habilita o deshabilita los campos del formulario."""
        for i in range(self.form_layout.rowCount()):
            item = self.form_layout.itemAt(i, QFormLayout.ItemRole.FieldRole)
            if item:
                widget = item.widget()
                if widget:
                    widget.setEnabled(enabled)

    def _load_groups(self) -> None:
        """Carga los grupos de preparación de la máquina en la lista."""
        self.groups_list.clear()
        groups = self.app_model.get_groups_for_machine(self.machine_id)
        for group in groups:
            # group es un PreparationGroupDTO
            item = QListWidgetItem(group.nombre)
            payload: Tuple[int, str, str] = (group.id, group.nombre, group.descripcion)
            item.setData(Qt.ItemDataRole.UserRole, payload)
            self.groups_list.addItem(item)
        self._toggle_form(False)
        self.group_name_edit.clear()
        self.group_desc_edit.clear()
        self.product_combo.setCurrentIndex(0)

    def _on_group_selected(self) -> None:
        """Carga los datos del grupo seleccionado en el formulario."""
        selected_items = self.groups_list.selectedItems()
        if not selected_items:
            self._toggle_form(False)
            return

        self._toggle_form(True)
        group_id, name, desc = cast(
            Tuple[int, str, str], selected_items[0].data(Qt.ItemDataRole.UserRole)
        )
        self.current_group_id = group_id
        self.group_name_edit.setText(name)
        self.group_desc_edit.setPlainText(desc)

        group_details = self.app_model.get_group_details(group_id)
        if group_details:
            # DTO access (PreparationGroupDTO)
            product_code = group_details.producto_codigo
            if product_code:
                index = self.product_combo.findData(product_code)
                if index != -1:
                    self.product_combo.setCurrentIndex(index)
                else:
                    self.product_combo.setCurrentIndex(0)
            else:
                self.product_combo.setCurrentIndex(0)

    def _add_group(self) -> None:
        """Prepara el formulario para añadir un nuevo grupo."""
        self.groups_list.clearSelection()
        self.current_group_id = None
        self.group_name_edit.clear()
        self.group_desc_edit.clear()
        self.product_combo.setCurrentIndex(0)
        self._toggle_form(True)
        self.group_name_edit.setFocus()

    def _save_group(self) -> None:
        """Guarda o actualiza el grupo actual."""
        name = self.group_name_edit.text().strip()
        desc = self.group_desc_edit.toPlainText().strip()
        product_code = cast(str | None, self.product_combo.currentData())

        if not name:
            self.controller.view.show_message("Error", "El nombre del grupo es obligatorio.", "warning")
            return

        if self.current_group_id:
            if self.app_model.update_prep_group(self.current_group_id, name, desc, product_code):
                 self.controller.view.show_message("Éxito", f"Grupo '{name}' actualizado.", "info")
            else:
                 self.controller.view.show_message("Error", "No se pudo actualizar el grupo.", "critical")
        else:
            res = self.app_model.add_prep_group(self.machine_id, name, desc, product_code)
            if isinstance(res, int) and not isinstance(res, bool):
                self.controller.view.show_message("Éxito", f"Grupo '{name}' creado correctamente.", "info")
            elif res == "UNIQUE_CONSTRAINT":
                self.controller.view.show_message("Error", f"Ya existe un grupo llamado '{name}' para esta máquina.", "warning")
            else:
                self.controller.view.show_message("Error", "No se pudo crear el grupo.", "critical")

        self._load_groups()

    def _delete_group(self) -> None:
        """Elimina el grupo seleccionado."""
        selected_items = self.groups_list.selectedItems()
        if not selected_items:
            self.controller.view.show_message("Selección Requerida", "Por favor, seleccione un grupo para eliminar.", "warning")
            return

        group_id, group_name, _ = cast(
            Tuple[int, str, str], selected_items[0].data(Qt.ItemDataRole.UserRole)
        )
        if self.controller.view.show_confirmation_dialog("Confirmar Eliminación", f"¿Está seguro de que desea eliminar el grupo '{group_name}'?"):
            if self.app_model.delete_prep_group(group_id):
                self.controller.view.show_message("Éxito", "Grupo eliminado correctamente.", "info")
            else:
                self.controller.view.show_message("Error", "No se pudo eliminar el grupo.", "critical")
            self._load_groups()

    def _manage_steps(self) -> None:
        """Abre el diálogo de pasos para el grupo seleccionado."""
        selected_items = self.groups_list.selectedItems()
        if not selected_items:
            self.controller.view.show_message("Selección Requerida", "Por favor, seleccione un grupo para gestionar sus pasos.", "warning")
            return

        group_id, group_name, _ = cast(
            Tuple[int, str, str], selected_items[0].data(Qt.ItemDataRole.UserRole)
        )
        dialog = PrepStepsDialog(group_id, group_name, self.controller, self)
        dialog.exec()
