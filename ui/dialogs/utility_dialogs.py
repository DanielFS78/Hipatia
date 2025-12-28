# =================================================================================
# ui/dialogs.py
# Contiene todas las clases de Diálogos personalizados para la aplicación.
# =================================================================================
import os
import logging
from datetime import datetime, date, timedelta, time
from time_calculator import CalculadorDeTiempos
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


# --- Split Dialogs Imports ---


class AddBreakDialog(QDialog):
    """Diálogo simple para añadir un nuevo descanso."""
    def __init__(self, parent=None):
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

    def get_times(self):
        """Devuelve las horas seleccionadas en formato de texto."""
        return {
            "start": self.start_time_edit.time().toString("HH:mm"),
            "end": self.end_time_edit.time().toString("HH:mm")
        }


class LoginDialog(QDialog):
    """Diálogo para la autenticación de usuarios."""

    def __init__(self, parent=None):
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

    def get_credentials(self):
        """Devuelve el usuario y la contraseña introducidos."""
        return self.username_edit.text().strip(), self.password_edit.text().strip()


class ChangePasswordDialog(QDialog):
    """Diálogo para cambiar la contraseña de un usuario."""

    def __init__(self, require_current_password=False, parent=None):
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

    def get_passwords(self):
        """Devuelve las contraseñas introducidas."""
        return {
            "current": self.current_password_edit.text(),
            "new": self.new_password_edit.text(),
            "confirm": self.confirm_password_edit.text()
        }


class SyncDialog(QDialog):
    """Diálogo para mostrar diferencias entre dos bases de datos y seleccionar cuáles importar."""

    def __init__(self, differences, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sincronizar Bases de Datos")
        self.setMinimumSize(900, 600)
        self.differences = differences
        self.selected_items = {}

        main_layout = QVBoxLayout(self)
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

        self._populate_tabs()

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Importar Selección")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)

    def _populate_tabs(self):
        """Crea una pestaña por cada tabla con diferencias."""
        for table_name, diff_data in self.differences.items():
            if not diff_data:
                continue

            tab = QWidget()
            layout = QVBoxLayout(tab)
            self.tab_widget.addTab(tab, table_name.capitalize())

            table_widget = QTableWidget()
            headers = ["Importar", ] + list(diff_data[0].keys())
            table_widget.setColumnCount(len(headers))
            table_widget.setHorizontalHeaderLabels(headers)
            table_widget.setRowCount(len(diff_data))

            for row_idx, row_data in enumerate(diff_data):
                # Checkbox para seleccionar
                chk_box_item = QTableWidgetItem()
                chk_box_item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
                chk_box_item.setCheckState(Qt.CheckState.Unchecked)
                table_widget.setItem(row_idx, 0, chk_box_item)

                # Datos de la fila
                for col_idx, (key, value) in enumerate(row_data.items(), 1):
                    table_widget.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))

            table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
            table_widget.horizontalHeader().setSectionResizeMode(len(headers) - 1, QHeaderView.ResizeMode.Stretch)
            layout.addWidget(table_widget)

    def get_selected_changes(self):
        """Recopila todos los elementos marcados por el usuario para ser importados."""
        selected_changes = {}
        for i in range(self.tab_widget.count()):
            table_name = self.tab_widget.tabText(i).lower()
            table_widget = self.tab_widget.widget(i).findChild(QTableWidget)
            selected_rows = []

            for row in range(table_widget.rowCount()):
                if table_widget.item(row, 0).checkState() == Qt.CheckState.Checked:
                    # Reconstruir el diccionario de la fila original
                    original_data = self.differences[table_name][row]
                    selected_rows.append(original_data)

            if selected_rows:
                selected_changes[table_name] = selected_rows

        return selected_changes


class SeleccionarHojasExcelDialog(QDialog):
    """Diálogo para que el usuario elija qué hojas incluir en el informe Excel."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Opciones de Informe Excel")
        self.layout = QVBoxLayout(self)

        self.layout.addWidget(QLabel("Seleccione las hojas que desea incluir en el informe:"))

        # Creamos las casillas de verificación
        self.check_resumen = QCheckBox("Hoja de Resumen de Planificación")
        self.check_desglose = QCheckBox("Hoja de Desglose por Tareas")
        self.check_trabajador = QCheckBox("Hoja de Carga por Trabajador")

        # Marcamos la de resumen por defecto
        self.check_resumen.setChecked(True)

        self.layout.addWidget(self.check_resumen)
        self.layout.addWidget(self.check_desglose)
        self.layout.addWidget(self.check_trabajador)

        # Botones de Aceptar/Cancelar
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Generar Informe")
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)

    def get_opciones(self):
        """Devuelve un diccionario con las opciones seleccionadas."""
        return {
            "imprimir_resumen": self.check_resumen.isChecked(),
            "imprimir_desglose": self.check_desglose.isChecked(),
            "imprimir_trabajador": self.check_trabajador.isChecked()
        }


class MultiWorkerSelectionDialog(QDialog):
    """Diálogo para seleccionar múltiples trabajadores de una lista."""

    def __init__(self, all_workers, previously_selected=None, parent=None):
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

        self.checkboxes = []
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

    def get_selected_workers(self):
        """Devuelve una lista con los nombres de los trabajadores seleccionados."""
        return [cb.text() for cb in self.checkboxes if cb.isChecked()]
