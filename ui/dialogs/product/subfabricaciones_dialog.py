# =================================================================================
# ui/dialogs/product/subfabricaciones_dialog.py
# =================================================================================
# -*- coding: utf-8 -*-
"""
Nombre del Módulo: ui.dialogs.product.subfabricaciones_dialog
Descripción: Formulario PyQt6 del catálogo de productos (detalle, iteraciones, subfabricaciones o procesos).
"""

from __future__ import annotations

import os
import logging
from datetime import datetime, date, timedelta, time
from typing import Any, Sequence, cast
from core.services.time_calculator import CalculadorDeTiempos
import math
import uuid # Importado para ID único
import copy # Importado para copias profundas

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

from PyQt6.QtCore import Qt, pyqtSignal, QEvent, QDate, QTimer, QTime, QPoint, QRectF, QSize
from PyQt6.QtGui import (
    QFont, QFontMetrics, QPixmap, QPainter, QColor, QBrush, QTextCharFormat, QIcon, QPen, QPalette,
    QPolygonF
)

from core.dtos import MachineDTO, SubfabricacionDTO
from core.subfabricacion_rows import coerce_subfabricaciones_rows


def _make_combo_readable(combo: QComboBox, option_labels: list[str], *, min_width_px: int) -> None:
    """Ensancha el combo y la lista desplegable para textos largos (máquinas, etc.)."""
    combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
    if option_labels:
        combo.setMinimumContentsLength(max(12, min(48, max(len(s) for s in option_labels))))
    fm = QFontMetrics(combo.font())
    w = min_width_px
    for t in option_labels:
        w = max(w, fm.horizontalAdvance(t) + 64)
    combo.setMinimumWidth(min(w, 720))
    combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    view = combo.view()
    if view is not None:
        view.setMinimumWidth(combo.minimumWidth())
        view.setTextElideMode(Qt.TextElideMode.ElideNone)


# --- Split Dialogs Imports ---


class SubfabricacionesDialog(QDialog):
    """
    Diálogo para gestionar (CRUD) la lista de sub-fabricaciones de un producto.
    """

    def __init__(
        self,
        subfabricaciones_actuales: Sequence[Any] | None,
        available_machines: Sequence[MachineDTO],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Gestionar Sub-fabricaciones")
        self.setMinimumSize(720, 520)

        self.subfabricaciones: list[SubfabricacionDTO] = coerce_subfabricaciones_rows(
            list(subfabricaciones_actuales) if subfabricaciones_actuales is not None else None
        )
        self._selected_row = -1

        main_layout = QVBoxLayout(self)

        # --- Tabla para mostrar la lista ---
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Descripción", "Tiempo (min)", "Tipo Trabajador", "Máquina Asignada"])
        header = self.table.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self._on_item_selected)
        main_layout.addWidget(self.table)

        # --- Formulario para añadir/editar ---
        form_frame = QFrame()
        form_frame.setFrameShape(QFrame.Shape.StyledPanel)
        form_layout = QFormLayout(form_frame)
        form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)

        self.desc_entry = QLineEdit()
        self.desc_entry.setMinimumHeight(self.desc_entry.sizeHint().height())
        self.tiempo_entry = QLineEdit()
        self.trabajador_menu = QComboBox()
        worker_labels = ["Tipo 1", "Tipo 2", "Tipo 3"]
        self.trabajador_menu.addItems(worker_labels)
        _make_combo_readable(self.trabajador_menu, worker_labels, min_width_px=220)

        self.tipo_proceso_menu = QComboBox()
        machine_labels: list[str] = ["(Ninguna)"]
        self.tipo_proceso_menu.addItem(machine_labels[0], userData=None)
        for machine in available_machines:
            self.tipo_proceso_menu.addItem(machine.nombre, userData=machine.id)
            machine_labels.append(machine.nombre)
        _make_combo_readable(self.tipo_proceso_menu, machine_labels, min_width_px=320)

        form_layout.addRow("Descripción:", self.desc_entry)
        form_layout.addRow("Tiempo (min):", self.tiempo_entry)
        form_layout.addRow("Tipo de Trabajador:", self.trabajador_menu)
        form_layout.addRow("Máquina Requerida:", self.tipo_proceso_menu)

        self.add_update_button = QPushButton("Añadir Sub-fabricación")
        self.add_update_button.clicked.connect(self._add_or_update)
        form_layout.addRow(self.add_update_button)
        main_layout.addWidget(form_frame)

        action_layout = QHBoxLayout()
        self.delete_button = QPushButton("Eliminar Seleccionado")
        self.delete_button.setEnabled(False)
        self.delete_button.clicked.connect(self._delete_selected)
        action_layout.addStretch()
        action_layout.addWidget(self.delete_button)
        main_layout.addLayout(action_layout)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

        self._refresh_table()

    def _refresh_table(self) -> None:
        self.table.setRowCount(0)
        for sub in self.subfabricaciones:
            row_pos = self.table.rowCount()
            self.table.insertRow(row_pos)
            self.table.setItem(row_pos, 0, QTableWidgetItem(sub.descripcion))
            self.table.setItem(row_pos, 1, QTableWidgetItem(str(sub.tiempo)))
            self.table.setItem(row_pos, 2, QTableWidgetItem(f"Tipo {sub.tipo_trabajador}"))

            # CORRECCIÓN: Busca el nombre de la máquina usando el maquina_id guardado.
            machine_name = ""
            machine_id = sub.maquina_id
            if machine_id:
                # Busca en el ComboBox el item cuyo 'userData' (el ID) coincida.
                index = self.tipo_proceso_menu.findData(machine_id)
                if index != -1:
                    machine_name = self.tipo_proceso_menu.itemText(index)
            self.table.setItem(row_pos, 3, QTableWidgetItem(machine_name))

    def _on_item_selected(self) -> None:
        selected_items = self.table.selectedItems()
        if not selected_items:
            self._selected_row = -1
            self.delete_button.setEnabled(False)
            self.add_update_button.setText("Añadir Sub-fabricación")
            self._clear_form()
            return

        self._selected_row = self.table.row(selected_items[0])
        sub = self.subfabricaciones[self._selected_row]

        self.desc_entry.setText(sub.descripcion)
        self.tiempo_entry.setText(str(sub.tiempo))
        self.trabajador_menu.setCurrentIndex(sub.tipo_trabajador - 1)

        assigned_machine_id = sub.maquina_id
        if assigned_machine_id:
            index = self.tipo_proceso_menu.findData(assigned_machine_id)
            if index != -1:
                self.tipo_proceso_menu.setCurrentIndex(index)
            else:
                # Si no se encuentra la máquina (p.ej. fue eliminada), se selecciona "(Ninguna)"
                self.tipo_proceso_menu.setCurrentIndex(0)
        else:
            self.tipo_proceso_menu.setCurrentIndex(0)

        self.delete_button.setEnabled(True)
        self.add_update_button.setText("Actualizar Sub-fabricación")

    def _add_or_update(self) -> None:
        desc = self.desc_entry.text().strip()
        tiempo_str = self.tiempo_entry.text().strip().replace(",", ".")

        if not desc or not tiempo_str:
            QMessageBox.warning(self, "Campos Vacíos", "La descripción y el tiempo son obligatorios.")
            return

        try:
            tiempo = float(tiempo_str)
            if tiempo <= 0: raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Dato Inválido", "El tiempo debe ser un número positivo.")
            return

        tipo_trabajador = self.trabajador_menu.currentIndex() + 1
        machine_id = cast(int | None, self.tipo_proceso_menu.currentData())
        new_data = SubfabricacionDTO(
            id=0,
            producto_codigo="",
            descripcion=desc,
            tiempo=tiempo,
            tipo_trabajador=tipo_trabajador,
            maquina_id=machine_id,
        )

        if self._selected_row != -1:
            self.subfabricaciones[self._selected_row] = new_data
        else:
            self.subfabricaciones.append(new_data)

        self._clear_form()
        self._refresh_table()

    def _delete_selected(self) -> None:
        if self._selected_row != -1:
            self.subfabricaciones.pop(self._selected_row)
            self._clear_form()
            self._refresh_table()

    def _clear_form(self) -> None:
        self.desc_entry.clear()
        self.tiempo_entry.clear()
        self.trabajador_menu.setCurrentIndex(0)
        self.tipo_proceso_menu.setCurrentIndex(0)
        self.table.clearSelection()
        self._selected_row = -1
        self.delete_button.setEnabled(False)
        self.add_update_button.setText("Añadir Sub-fabricación")

    def get_updated_subfabricaciones(self) -> list[dict[str, Any]]:
        return [
            {
                "id": s.id,
                "producto_codigo": s.producto_codigo,
                "descripcion": s.descripcion,
                "tiempo": s.tiempo,
                "tipo_trabajador": s.tipo_trabajador,
                "maquina_id": s.maquina_id,
            }
            for s in self.subfabricaciones
        ]

    def accept(self) -> None:
        """
        Sobrescribe el método accept para avisar si hay datos en el formulario sin guardar.
        """
        if self.desc_entry.text().strip() or self.tiempo_entry.text().strip():
            reply = QMessageBox.question(
                self,
                "Cambios sin guardar",
                "Hay datos en el formulario de edición que no se han añadido/actualizado en la lista.\n"
                "¿Deseas descartarlos y cerrar?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return

        super().accept()


