# -*- coding: utf-8 -*-
"""
Nombre del Módulo: ui.dialogs.prep.prep_steps_dialog

Descripción: Define protocolos o tipos principales: ``PrepStepsDialog``. Diálogo para gestionar los pasos individuales de un grupo de preparación. Integración típica con: ``__future__``, ``os``, ``datetime``, ``core``, ``PyQt6``.
"""

from __future__ import annotations

import os
import logging
from datetime import datetime, date, timedelta, time
from typing import Any, cast, TYPE_CHECKING

from core.services.preparation_service import PreparationService

if TYPE_CHECKING:
    from core.interfaces.view_interface import IView

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


class PrepStepsDialog(QDialog):
    """
    Diálogo para gestionar los pasos individuales de un grupo de preparación.
    Permite visualizar, añadir, actualizar y eliminar pasos.
    """

    def __init__(
        self,
        group_id: int,
        group_name: str,
        preparation_service: PreparationService,
        view: "IView",
        parent: Any = None,
    ) -> None:
        """
        Inicializa el diálogo de pasos de preparación.

        Args:
            group_id: ID del grupo de preparación.
            group_name: Nombre del grupo para el título.
            preparation_service: Servicio de grupos y pasos de preparación.
            view: Vista para mensajes y confirmaciones.
            parent: Widget padre.
        """
        super().__init__(parent)
        self.setWindowTitle(f"Pasos para el Grupo: {group_name}")
        self.setMinimumSize(700, 550)
        self.group_id = group_id
        self.preparation_service = preparation_service
        self.view = view
        self.current_step_id: int | None = None

        main_layout = QVBoxLayout(self)

        self.steps_table = QTableWidget()
        self.steps_table.setColumnCount(4)
        self.steps_table.setHorizontalHeaderLabels(["Nombre del Paso", "Tiempo (min)", "Es Diario", "Descripción"])
        header = self.steps_table.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
            header.setStretchLastSection(True)
        self.steps_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.steps_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.steps_table.itemSelectionChanged.connect(self._on_step_selected)
        main_layout.addWidget(self.steps_table)

        form_frame = QFrame()
        form_frame.setFrameShape(QFrame.Shape.StyledPanel)
        form_layout = QFormLayout(form_frame)
        self.step_name_edit = QLineEdit()
        self.step_time_edit = QLineEdit()
        self.step_desc_edit = QTextEdit()
        self.step_desc_edit.setFixedHeight(60)
        self.is_daily_check = QCheckBox("Este paso se repite cada día de trabajo")

        form_layout.addRow("Nombre del Paso:", self.step_name_edit)
        form_layout.addRow("Tiempo (minutos):", self.step_time_edit)
        form_layout.addRow(self.is_daily_check)
        form_layout.addRow("Descripción:", self.step_desc_edit)
        main_layout.addWidget(form_frame)

        button_layout = QHBoxLayout()
        self.add_update_button = QPushButton("Añadir Nuevo Paso")
        self.delete_button = QPushButton("Eliminar Paso Seleccionado")
        self.clear_button = QPushButton("Limpiar Formulario")
        button_layout.addWidget(self.add_update_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.clear_button)
        main_layout.addLayout(button_layout)

        self.add_update_button.clicked.connect(self._add_or_update_step)
        self.delete_button.clicked.connect(self._delete_step)
        self.clear_button.clicked.connect(self._clear_form)

        self._load_steps()
        self._clear_form()

    def _load_steps(self) -> None:
        """Carga los pasos del grupo y los muestra en la tabla."""
        self.steps_table.setRowCount(0)
        steps = self.preparation_service.get_steps_for_group(self.group_id)
        self.steps_table.blockSignals(True)
        for step_data in steps:
            # step_data es un PreparationStepDTO: id, nombre, tiempo_fase, descripcion, es_diario
            step_id = step_data.id
            name = step_data.nombre
            v_time = step_data.tiempo_fase
            description = step_data.descripcion
            is_daily = step_data.es_diario

            row_position = self.steps_table.rowCount()
            self.steps_table.insertRow(row_position)
            item_name = QTableWidgetItem(name)
            item_name.setData(Qt.ItemDataRole.UserRole, step_id)
            item_time = QTableWidgetItem(str(v_time))
            item_daily = QTableWidgetItem("Sí" if is_daily else "No")
            item_desc = QTableWidgetItem(description)
            item_time.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_daily.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.steps_table.setItem(row_position, 0, item_name)
            self.steps_table.setItem(row_position, 1, item_time)
            self.steps_table.setItem(row_position, 2, item_daily)
            self.steps_table.setItem(row_position, 3, item_desc)
        self.steps_table.blockSignals(False)

    def _on_step_selected(self) -> None:
        """Carga los datos de un paso seleccionado en el formulario."""
        selected_items = self.steps_table.selectedItems()
        if not selected_items:
            return
        selected_row = self.steps_table.row(selected_items[0])
        item0 = self.steps_table.item(selected_row, 0)
        item1 = self.steps_table.item(selected_row, 1)
        item2 = self.steps_table.item(selected_row, 2)
        item3 = self.steps_table.item(selected_row, 3)
        if not item0 or not item1 or not item2 or not item3:
            return

        self.current_step_id = cast(int | None, item0.data(Qt.ItemDataRole.UserRole))
        name = item0.text()
        time = item1.text()
        is_daily_text = item2.text()
        description = item3.text()
        self.step_name_edit.setText(name)
        self.step_time_edit.setText(time)
        self.is_daily_check.setChecked(is_daily_text == "Sí")
        self.step_desc_edit.setPlainText(description)
        self.add_update_button.setText("Actualizar Paso Seleccionado")
        self.delete_button.setEnabled(True)

    def _clear_form(self) -> None:
        """Limpia el formulario para añadir un nuevo paso."""
        self.steps_table.clearSelection()
        self.step_name_edit.clear()
        self.step_time_edit.clear()
        self.step_desc_edit.clear()
        self.is_daily_check.setChecked(False)
        self.step_name_edit.setFocus()
        self.current_step_id = None
        self.add_update_button.setText("Añadir Nuevo Paso")
        self.delete_button.setEnabled(False)

    def _add_or_update_step(self) -> None:
        """Añade un nuevo paso o actualiza el seleccionado en el grupo."""
        name = self.step_name_edit.text().strip()
        time_str = self.step_time_edit.text().strip().replace(",", ".")
        description = self.step_desc_edit.toPlainText().strip()
        is_daily = self.is_daily_check.isChecked()

        if not name:
            self.view.show_message("Campo Requerido", "El nombre del paso es obligatorio.", "warning")
            return

        try:
            val_time = float(time_str)
            if val_time < 0:
                raise ValueError
        except ValueError:
            self.view.show_message("Dato Inválido", "El tiempo debe ser un número positivo.", "warning")
            return

        if self.current_step_id:
            # Actualizar paso existente
            data: dict[str, Any] = {
                'nombre': name,
                'tiempo_fase': val_time,
                'descripcion': description,
                'es_diario': is_daily
            }
            if self.preparation_service.update_prep_step(self.current_step_id, data):
                self.view.show_message("Éxito", f"Paso '{name}' actualizado correctamente.", "info")
            else:
                self.view.show_message("Error", "No se pudo actualizar el paso.", "critical")
        else:
            # Añadir nuevo paso
            if self.preparation_service.add_prep_step(self.group_id, name, val_time, description, is_daily):
                self.view.show_message("Éxito", f"Paso '{name}' añadido correctamente.", "info")
            else:
                self.view.show_message("Error", "No se pudo añadir el paso.", "critical")

        self._load_steps()
        self._clear_form()

    def _delete_step(self) -> None:
        """Elimina el paso seleccionado."""
        if self.current_step_id is None:
            self.view.show_message("Selección Requerida", "Por favor, seleccione un paso para eliminar.", "warning")
            return
        step_name = self.step_name_edit.text()
        if self.view.show_confirmation_dialog("Confirmar Eliminación", f"¿Está seguro de que desea eliminar el paso '{step_name}'?"):
            if self.preparation_service.delete_prep_step(self.current_step_id):
                self.view.show_message("Éxito", "El paso se ha eliminado.", "info")
                self._load_steps()
                self._clear_form()
            else:
                self.view.show_message("Error", "No se pudo eliminar el paso.", "critical")
