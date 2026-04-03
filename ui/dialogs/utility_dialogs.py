# =================================================================================
# ui/dialogs.py
# Contiene todas las clases de Diálogos personalizados para la aplicación.
# =================================================================================
"""
Interfaz PyQt6 (`utility_dialogs`): widgets, diálogos o recursos visuales conectados al flujo de usuario.
"""

import os
import logging
from datetime import datetime, date, timedelta, time
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

from PyQt6.QtCore import Qt, pyqtSignal, QEvent, QDate, QTimer, QTime, QPoint, QRectF
from PyQt6.QtGui import (
    QFont, QPixmap, QPainter, QColor, QBrush, QTextCharFormat, QIcon, QPen, QPalette,
    QPolygonF
)
from typing import Any


# --- Split Dialogs Imports ---


class AddBreakDialog(QDialog):
    """Diálogo simple para añadir un nuevo descanso."""
    def __init__(self, parent: Any = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Añadir Nuevo Descanso")
        layout = QFormLayout(self)

        self.start_time_edit = QTimeEdit(QTime(10, 0))
        self.end_time_edit = QTimeEdit(QTime(10, 15))

        layout.addRow("Hora de Inicio:", self.start_time_edit)
        layout.addRow("Hora de Fin:", self.end_time_edit)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addRow(button_box)

    def get_times(self) -> dict[str, str]:
        """Devuelve las horas seleccionadas en formato de texto."""
        return {
            "start": self.start_time_edit.time().toString("HH:mm"),
            "end": self.end_time_edit.time().toString("HH:mm")
        }


class LoginDialog(QDialog):
    """Diálogo para la autenticación de usuarios."""

    def __init__(self, parent: Any = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Inicio de Sesión")
        self.setModal(True)  # Bloquea la ventana principal hasta que se cierre

        layout = QFormLayout(self)
        self.username_edit = QLineEdit()
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)

        layout.addRow("Usuario:", self.username_edit)
        layout.addRow("Contraseña:", self.password_edit)

        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addRow(self.buttons)

    def get_credentials(self) -> tuple[str, str]:
        """Devuelve el usuario y la contraseña introducidos."""
        return self.username_edit.text().strip(), self.password_edit.text().strip()


class ChangePasswordDialog(QDialog):
    """Diálogo para cambiar la contraseña de un usuario."""

    def __init__(self, require_current_password: bool = False, parent: Any = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Cambiar Contraseña")

        layout = QFormLayout(self)

        self.current_password_edit = QLineEdit()
        self.current_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_password_edit = QLineEdit()
        self.new_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password_edit = QLineEdit()
        self.confirm_password_edit.setEchoMode(QLineEdit.EchoMode.Password)

        # Mostrar el campo de contraseña actual solo si es necesario
        self.current_password_label = QLabel("Contraseña Actual:")
        if require_current_password:
            layout.addRow(self.current_password_label, self.current_password_edit)
        else:
            self.current_password_label.hide()
            self.current_password_edit.hide()

        layout.addRow("Nueva Contraseña:", self.new_password_edit)
        layout.addRow("Confirmar Nueva Contraseña:", self.confirm_password_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def get_passwords(self) -> dict[str, str]:
        """Devuelve las contraseñas introducidas."""
        return {
            "current": self.current_password_edit.text(),
            "new": self.new_password_edit.text(),
            "confirm": self.confirm_password_edit.text()
        }


from core.dtos import (
    SyncRecordDTO,
    SyncTableDifferencesDTO,
    DatabaseComparisonDTO
)


class SyncDialog(QDialog):
    """Diálogo para mostrar diferencias entre dos bases de datos y seleccionar cuáles importar."""

    def __init__(self, comparison: DatabaseComparisonDTO, parent: Any = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Sincronizar Bases de Datos")
        self.setMinimumSize(900, 600)
        self.comparison = comparison
        self.selected_items: DatabaseComparisonDTO = DatabaseComparisonDTO(tables=[])

        main_layout = QVBoxLayout(self)
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

        self._populate_tabs()

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        ok_btn = buttons.button(QDialogButtonBox.StandardButton.Ok)
        if ok_btn: ok_btn.setText("Importar Selección")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)

    def _populate_tabs(self) -> None:
        """Crea una pestaña por cada tabla con diferencias."""
        for table_diff in self.comparison.tables:
            table_name = table_diff.table_name
            diff_data = table_diff.differences
            
            if not diff_data:
                continue

            tab = QWidget()
            layout = QVBoxLayout(tab)
            self.tab_widget.addTab(tab, table_name.capitalize())

            table_widget = QTableWidget()
            # headers = ["Importar", "Acción"] + keys de la data
            headers = ["Importar", "Acción"] + list(diff_data[0].data.fields.keys())
            table_widget.setColumnCount(len(headers))
            table_widget.setHorizontalHeaderLabels(headers)
            table_widget.setRowCount(len(diff_data))

            for row_idx, record in enumerate(diff_data):
                # Checkbox para seleccionar
                chk_box_item = QTableWidgetItem()
                chk_box_item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
                chk_box_item.setCheckState(Qt.CheckState.Unchecked)
                table_widget.setItem(row_idx, 0, chk_box_item)
                
                # Acción (new/updated)
                table_widget.setItem(row_idx, 1, QTableWidgetItem(record.action))

                # Datos de la fila
                for col_idx, (key, value) in enumerate(record.data.fields.items(), 2):
                    table_widget.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))

            header = table_widget.horizontalHeader()
            if header:
                header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
                header.setSectionResizeMode(len(headers) - 1, QHeaderView.ResizeMode.Stretch)
            layout.addWidget(table_widget)

    def get_selected_changes(self) -> DatabaseComparisonDTO:
        """Recopila todos los elementos marcados por el usuario para ser importados."""
        selected_tables = []
        for i in range(self.tab_widget.count()):
            table_name = self.tab_widget.tabText(i).lower()
            tab_widget_child = self.tab_widget.widget(i)
            if not tab_widget_child: continue
            table_widget = tab_widget_child.findChild(QTableWidget)
            if not table_widget: continue
            
            selected_records = []

            # Buscar el table_diff original para esta pestaña
            orig_table_diff = next(
                (t for t in self.comparison.tables if t.table_name.lower() == table_name), 
                None
            )
            if not orig_table_diff: continue

            for row in range(table_widget.rowCount()):
                item_0 = table_widget.item(row, 0)
                if item_0 and item_0.checkState() == Qt.CheckState.Checked:
                    # Usar el record original
                    selected_records.append(orig_table_diff.differences[row])

            if selected_records:
                selected_tables.append(SyncTableDifferencesDTO(
                    table_name=table_name,
                    differences=selected_records
                ))

        return DatabaseComparisonDTO(tables=selected_tables)


class SeleccionarHojasExcelDialog(QDialog):
    """Diálogo para que el usuario elija qué hojas incluir en el informe Excel."""
    def __init__(self, parent: Any = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Opciones de Informe Excel")
        self.main_layout = QVBoxLayout(self)

        self.main_layout.addWidget(QLabel("Seleccione las hojas que desea incluir en el informe:"))

        # Creamos las casillas de verificación
        self.check_resumen = QCheckBox("Hoja de Resumen de Planificación")
        self.check_desglose = QCheckBox("Hoja de Desglose por Tareas")
        self.check_trabajador = QCheckBox("Hoja de Carga por Trabajador")

        # Marcamos la de resumen por defecto
        self.check_resumen.setChecked(True)

        self.main_layout.addWidget(self.check_resumen)
        self.main_layout.addWidget(self.check_desglose)
        self.main_layout.addWidget(self.check_trabajador)

        # Botones de Aceptar/Cancelar
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        ok_btn = self.buttons.button(QDialogButtonBox.StandardButton.Ok)
        if ok_btn: ok_btn.setText("Generar Informe")
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.main_layout.addWidget(self.buttons)

    def get_opciones(self) -> dict[str, bool]:
        """Devuelve un diccionario con las opciones seleccionadas."""
        return {
            "imprimir_resumen": self.check_resumen.isChecked(),
            "imprimir_desglose": self.check_desglose.isChecked(),
            "imprimir_trabajador": self.check_trabajador.isChecked()
        }


class MultiWorkerSelectionDialog(QDialog):
    """Diálogo para seleccionar múltiples trabajadores de una lista."""

    def __init__(self, all_workers: list[str], previously_selected: list[str] | None = None, parent: Any = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Asignar Trabajadores al Grupo")
        self.setMinimumSize(350, 450)
        
        layout = QVBoxLayout(self)
        
        layout.addWidget(QLabel("Seleccione los operarios que realizarán las tareas de este grupo:"))
        
        # Área de scroll para la lista de trabajadores
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        container = QWidget()
        self.worker_layout = QVBoxLayout(container)
        
        self.checkboxes: list[QCheckBox] = []
        for worker_name in all_workers:
            checkbox = QCheckBox(worker_name)
            if previously_selected and worker_name in previously_selected:
                checkbox.setChecked(True)
            self.checkboxes.append(checkbox)
            self.worker_layout.addWidget(checkbox)

        scroll_area.setWidget(container)
        layout.addWidget(scroll_area)

        # Botones OK y Cancelar
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_selected_workers(self) -> list[str]:
        """Devuelve una lista con los nombres de los trabajadores seleccionados."""
        return [cb.text() for cb in self.checkboxes if cb.isChecked()]
