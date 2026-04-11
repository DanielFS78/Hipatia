# -*- coding: utf-8 -*-
"""
Nombre del Módulo: prep_steps_widget

Descripción: CRUD de fases de preparación (pasos) con validación y señales hacia el controlador.
"""

from .base import *
from typing import Any


def _ui_record_field(record: Any, key: str, default: Any = None) -> Any:
    """Lee un campo de un dict o de un objeto/DTO (la UI acepta ambas formas)."""
    if isinstance(record, dict):
        return record.get(key, default)
    return getattr(record, key, default)


class PrepStepsWidget(QWidget):
    """Widget para gestionar la base de datos de fases de preparación (CRUD)."""

    add_step_signal = pyqtSignal(dict)
    update_step_signal = pyqtSignal(int, dict)
    delete_step_signal = pyqtSignal(int)
    validation_warning = pyqtSignal(str, str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.current_step_id: Any = None
        self.form_widgets: dict[str, Any] = {}

        main_layout = QHBoxLayout(self)

        left_panel = QFrame()
        left_layout = QVBoxLayout(left_panel)
        left_layout.addWidget(QLabel("<b>Fases de Preparación</b>"))
        self.steps_list = QListWidget()
        left_layout.addWidget(self.steps_list)
        self.add_button = QPushButton("Añadir Nueva Fase")
        left_layout.addWidget(self.add_button)

        right_panel = QFrame()
        self.details_container_layout = QVBoxLayout(right_panel)
        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(right_panel, 2)
        self.clear_details_area()

    def load_preprocesos_data(self, data: list[Any]) -> None:
        """Carga los datos de los preprocesos en la lista."""
        self.steps_list.clear()
        for preproceso in data:
            pid = _ui_record_field(preproceso, "id")
            if pid is None:
                continue
            nombre = str(_ui_record_field(preproceso, "nombre", "") or "")
            descripcion = str(_ui_record_field(preproceso, "descripcion", "") or "")
            item_text = f"{nombre} - {descripcion}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, pid)
            self.steps_list.addItem(item)

    def populate_list(self, steps_data: list[Any]) -> None:
        self.steps_list.blockSignals(True)
        self.steps_list.clear()
        for step_data in steps_data:
            step_id, nombre, _, tiempo_fase, _, _ = step_data
            item = QListWidgetItem(f"{nombre} ({tiempo_fase} min)")
            item.setData(Qt.ItemDataRole.UserRole, step_id)
            self.steps_list.addItem(item)
        self.steps_list.blockSignals(False)
        self.clear_details_area()

    def clear_details_area(self) -> None:
        """Limpia el panel de detalles."""
        while self.details_container_layout.count():
            child = self.details_container_layout.takeAt(0)
            if child is not None:
                w = child.widget()
                if w is not None:
                    w.deleteLater()
        self.form_widgets = {}
        self.current_step_id = None
        placeholder = QLabel("Seleccione una fase o añada una nueva.")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.details_container_layout.addWidget(placeholder)

    def _create_form_widgets(self) -> None:
        """Crea la estructura del formulario de detalles."""
        self.clear_details_area()
        container_widget = QWidget()
        container_layout = QVBoxLayout(container_widget)
        self.details_container_layout.addWidget(container_widget)

        self.form_widgets["title"] = QLabel()
        font = self.form_widgets["title"].font()
        font.setBold(True)
        font.setPointSize(14)
        self.form_widgets["title"].setFont(font)
        container_layout.addWidget(self.form_widgets["title"])

        form_layout = QFormLayout()
        self.form_widgets["nombre"] = QLineEdit()
        self.form_widgets["tiempo_fase"] = QLineEdit()
        self.form_widgets["descripcion"] = QTextEdit()
        self.form_widgets["descripcion"].setFixedHeight(80)
        self.form_widgets["es_diario"] = QCheckBox("Este paso se repite cada día de trabajo")
        self.form_widgets["es_verificacion"] = QCheckBox("Este paso es una verificación (no consume tiempo)")

        form_layout.addRow("Nombre de la Fase:", self.form_widgets["nombre"])
        form_layout.addRow("Tiempo (minutos):", self.form_widgets["tiempo_fase"])
        form_layout.addRow(self.form_widgets["es_diario"])
        form_layout.addRow(self.form_widgets["es_verificacion"])
        form_layout.addRow("Descripción:", self.form_widgets["descripcion"])
        container_layout.addLayout(form_layout)

        button_layout = QHBoxLayout()
        save_btn = QPushButton("Guardar Cambios")
        delete_btn = QPushButton("Eliminar Fase")
        self.form_widgets["save_button"] = save_btn
        self.form_widgets["delete_button"] = delete_btn
        save_btn.clicked.connect(self._on_save_button_clicked)
        delete_btn.clicked.connect(lambda: self.delete_step_signal.emit(self.current_step_id))
        button_layout.addStretch()
        button_layout.addWidget(delete_btn)
        button_layout.addWidget(save_btn)
        container_layout.addLayout(button_layout)
        container_layout.addStretch()

    def show_step_details(self, step_data: dict[str, Any] | Any) -> None:
        self._create_form_widgets()
        self.current_step_id = _ui_record_field(step_data, "id")
        self.form_widgets["title"].setText("Editar Fase de Preparación")
        self.form_widgets["nombre"].setText(str(_ui_record_field(step_data, "nombre", "") or ""))
        self.form_widgets["tiempo_fase"].setText(str(_ui_record_field(step_data, "tiempo_fase", "") or ""))
        self.form_widgets["descripcion"].setPlainText(str(_ui_record_field(step_data, "descripcion", "") or ""))
        self.form_widgets["es_diario"].setChecked(bool(_ui_record_field(step_data, "es_diario", 0)))
        self.form_widgets["es_verificacion"].setChecked(bool(_ui_record_field(step_data, "es_verificacion", 0)))
        self.form_widgets["delete_button"].setVisible(True)
        self.form_widgets["save_button"].setVisible(True)

    def show_add_new_form(self) -> None:
        self._create_form_widgets()
        self.current_step_id = None
        self.form_widgets["title"].setText("Añadir Nueva Fase de Preparación")
        self.form_widgets["delete_button"].setVisible(False)
        self.form_widgets["nombre"].setFocus()

    def _on_save_button_clicked(self) -> None:
        data = self.get_form_data()
        if not data:
            return
        if self.current_step_id is None:
            self.add_step_signal.emit(data)
        else:
            self.update_step_signal.emit(self.current_step_id, data)

    def get_form_data(self) -> dict[str, Any] | None:
        if not self.form_widgets:
            return None
        nombre = self.form_widgets["nombre"].text().strip()
        tiempo_str = self.form_widgets["tiempo_fase"].text().strip().replace(",", ".")
        if not nombre or not tiempo_str:
            self.validation_warning.emit(
                "Campos Obligatorios",
                "El nombre y el tiempo son obligatorios.",
            )
            return None
        try:
            tiempo = float(tiempo_str)
            if tiempo < 0:
                raise ValueError
        except ValueError:
            self.validation_warning.emit(
                "Dato Inválido",
                "El tiempo debe ser un número positivo.",
            )
            return None
        if self.form_widgets["es_verificacion"].isChecked():
            tiempo = 0
        return {
            "nombre": nombre,
            "tiempo_fase": tiempo,
            "descripcion": self.form_widgets["descripcion"].toPlainText().strip(),
            "es_diario": 1 if self.form_widgets["es_diario"].isChecked() else 0,
            "es_verificacion": 1 if self.form_widgets["es_verificacion"].isChecked() else 0,
        }

    def clear_form(self) -> None:
        self.steps_list.clearSelection()
        self.clear_details_area()
