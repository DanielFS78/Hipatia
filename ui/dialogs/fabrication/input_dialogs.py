"""
Interfaz PyQt6 (`input_dialogs`): widgets, diálogos o recursos visuales conectados al flujo de usuario.
"""

from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QSpinBox, 
    QDateEdit, QDialogButtonBox, QLabel, QVBoxLayout,
    QTextEdit, QListWidget, QListWidgetItem, QHBoxLayout,
    QPushButton, QMessageBox
)
from PyQt6.QtCore import Qt, QDate
from typing import Tuple, Dict, Any, List, Optional, Union, TYPE_CHECKING
from datetime import date

if TYPE_CHECKING:
    from PyQt6.QtWidgets import QWidget
    from core.dtos import LoteInstanceParametersDTO

class GetLoteInstanceParametersDialog(QDialog):
    """
    Diálogo para solicitar los parámetros de una instancia de Lote al añadirla a la Pila.
    """

    def __init__(self, lote_codigo: str, parent: Optional["QWidget"] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Parámetros para Lote: {lote_codigo}")
        self.setModal(True)

        layout = QFormLayout(self)
        layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)

        # --- Widgets del formulario ---
        self.identificador_entry = QLineEdit()
        self.identificador_entry.setPlaceholderText("Ej: Pedido Cliente A, Lote de Stock...")

        self.units_spinbox = QSpinBox()
        self.units_spinbox.setRange(1, 99999)
        self.units_spinbox.setValue(1)

        self.deadline_edit = QDateEdit(QDate.currentDate().addDays(14))  # Por defecto, 2 semanas
        self.deadline_edit.setCalendarPopup(True)
        self.deadline_edit.setMinimumDate(QDate.currentDate())

        layout.addRow("<b>Identificador Único:</b>", self.identificador_entry)
        layout.addRow("<i>(Para diferenciar este lote dentro del plan)</i>", QLabel())

        layout.addRow("<b>Unidades a Fabricar:</b>", self.units_spinbox)
        layout.addRow("<b>Fecha Límite de Entrega:</b>", self.deadline_edit)

        # --- Botones de Aceptar/Cancelar ---
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addRow(self.buttons)

    def get_data(self) -> "LoteInstanceParametersDTO":
        """Devuelve un objeto LoteInstanceParametersDTO con los parámetros introducidos por el usuario."""
        from core.dtos import LoteInstanceParametersDTO
        return LoteInstanceParametersDTO(
            identificador=self.identificador_entry.text().strip(),
            unidades=self.units_spinbox.value(),
            deadline=self.deadline_edit.date().toPyDate()
        )


class GetOptimizationParametersDialog(QDialog):
    """
    Diálogo para solicitar fecha de inicio, fecha de fin y unidades para la optimización.
    """
    def __init__(self, parent: Optional["QWidget"] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Parámetros de Optimización")
        self.setModal(True)
        self.setMinimumWidth(400)

        layout = QFormLayout(self)
        self.start_date_edit = QDateEdit(QDate.currentDate())
        self.start_date_edit.setCalendarPopup(True)
        self.end_date_edit = QDateEdit(QDate.currentDate().addDays(30))
        self.end_date_edit.setCalendarPopup(True)
        self.units_spinbox = QSpinBox()
        self.units_spinbox.setRange(1, 99999)
        self.units_spinbox.setValue(1)

        layout.addRow("<b>Unidades a Fabricar:</b>", self.units_spinbox)
        layout.addRow("<b>Fecha de Inicio Deseada:</b>", self.start_date_edit)
        layout.addRow("<b>Fecha Límite de Entrega:</b>", self.end_date_edit)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        ok_button = button_box.button(QDialogButtonBox.StandardButton.Ok)
        if ok_button:
            ok_button.setText("Optimizar Plan")
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addRow(button_box)

    def get_parameters(self) -> Dict[str, Any]:
        return {
            "start_date": self.start_date_edit.date().toPyDate(),
            "end_date": self.end_date_edit.date().toPyDate(),
            "units": self.units_spinbox.value()
        }


class GetUnitsDialog(QDialog):
    """Diálogo simple para solicitar el número de unidades a producir."""

    def __init__(self, parent: Optional["QWidget"] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Unidades a Producir")
        self.setMinimumWidth(300)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("¿Cuántas unidades deseas producir?"))

        self.units_spinbox = QSpinBox()
        self.units_spinbox.setMinimum(1)
        self.units_spinbox.setMaximum(100000)
        self.units_spinbox.setValue(1)
        layout.addWidget(self.units_spinbox)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_units(self) -> int:
        return self.units_spinbox.value()
