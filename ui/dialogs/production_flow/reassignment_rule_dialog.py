# -*- coding: utf-8 -*-
"""
Nombre del Módulo: ui.dialogs.production_flow.reassignment_rule_dialog
Descripción: Definición o simulación del flujo de producción (estado, presentadores, reglas y diálogos auxiliares).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.reassignment_rule_dialog_io import (
    reassignment_dialog_canvas_row_task_id,
    reassignment_dialog_canvas_row_task_name,
    reassignment_dialog_current_task_id,
    reassignment_dialog_current_task_name,
    reassignment_rule_condition_value_as_int,
    reassignment_rule_is_after_units,
    reassignment_rule_mode_is_parallel_join,
    reassignment_rule_target_task_id,
)
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QRadioButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


class ReassignmentRuleDialog(QDialog):
    """Diálogo para definir la regla de reasignación de un trabajador para una tarea."""

    def __init__(
        self,
        worker_name: str,
        current_task: Dict[str, Any],
        all_canvas_tasks: List[Dict[str, Any]],
        current_rule: Any,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Regla para {worker_name} en {reassignment_dialog_current_task_name(current_task)}")
        self.setMinimumWidth(500)

        self.all_canvas_tasks = all_canvas_tasks
        self.current_task_id = reassignment_dialog_current_task_id(current_task)

        main_layout = QVBoxLayout(self)

        condition_group = QGroupBox("El trabajador se liberará de esta tarea...")
        cond_layout = QVBoxLayout(condition_group)
        self.rb_on_finish = QRadioButton("Al finalizar la producción total de la tarea.")
        self.rb_after_units = QRadioButton("Tras fabricar un número específico de unidades:")
        self.sb_units_value = QSpinBox()
        self.sb_units_value.setRange(1, 99999)
        cond_layout.addWidget(self.rb_on_finish)
        cond_layout.addWidget(self.rb_after_units)
        cond_layout.addWidget(self.sb_units_value)
        main_layout.addWidget(condition_group)

        action_group = QGroupBox("Acción al liberarse")
        act_layout = QFormLayout(action_group)
        self.cb_target_task = QComboBox()
        act_layout.addRow("Reasignar a la tarea:", self.cb_target_task)
        main_layout.addWidget(action_group)

        tipo_grupo = QGroupBox("Tipo de Reasignación")
        tipo_layout = QVBoxLayout(tipo_grupo)
        self.tipo_compartir = QRadioButton("Compartir carga (comportamiento actual)")
        self.tipo_compartir.setToolTip(
            "El trabajador se une al grupo existente y comparten el tiempo restante de la unidad actual."
        )
        self.tipo_compartir.setChecked(True)
        self.tipo_paralelo = QRadioButton("Trabajar en paralelo (NUEVO)")
        self.tipo_paralelo.setToolTip(
            "El trabajador inicia su propia línea de trabajo paralela en la misma tarea, trabajando en unidades diferentes."
        )
        tipo_layout.addWidget(self.tipo_compartir)
        tipo_layout.addWidget(self.tipo_paralelo)
        main_layout.addWidget(tipo_grupo)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

        self._populate_fields(current_rule)
        self.rb_on_finish.toggled.connect(lambda checked: self.sb_units_value.setEnabled(not checked))

    def _populate_fields(self, rule: Any) -> None:
        self.cb_target_task.addItem("--- Ninguna (queda libre) ---", None)
        for task in self.all_canvas_tasks:
            if reassignment_dialog_canvas_row_task_id(task) != self.current_task_id:
                self.cb_target_task.addItem(
                    reassignment_dialog_canvas_row_task_name(task),
                    reassignment_dialog_canvas_row_task_id(task),
                )

        if rule is None:
            self.rb_on_finish.setChecked(True)
            self.sb_units_value.setEnabled(False)
            return

        if reassignment_rule_is_after_units(rule):
            self.rb_after_units.setChecked(True)
            self.sb_units_value.setValue(reassignment_rule_condition_value_as_int(rule))
            self.sb_units_value.setEnabled(True)
        else:
            self.rb_on_finish.setChecked(True)
            self.sb_units_value.setEnabled(False)

        target_id = reassignment_rule_target_task_id(rule)
        if target_id:
            target_index = self.cb_target_task.findData(target_id)
            if target_index != -1:
                self.cb_target_task.setCurrentIndex(target_index)

        if reassignment_rule_mode_is_parallel_join(rule):
            self.tipo_paralelo.setChecked(True)
        else:
            self.tipo_compartir.setChecked(True)

    def get_rule(self) -> Optional[Dict[str, Any]]:
        condition_type = None
        condition_value = None
        if self.rb_on_finish.isChecked():
            condition_type = "ON_FINISH"
        elif self.rb_after_units.isChecked():
            condition_type = "AFTER_UNITS"
            condition_value = self.sb_units_value.value()

        target_task_id = self.cb_target_task.currentData()
        mode = "PARALLEL_JOIN" if self.tipo_paralelo.isChecked() else "compartir"
        if condition_type or target_task_id:
            return {
                "condition_type": condition_type,
                "condition_value": condition_value,
                "target_task_id": target_task_id,
                "mode": mode,
            }
        return None

