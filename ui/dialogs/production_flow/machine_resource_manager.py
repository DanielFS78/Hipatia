# -*- coding: utf-8 -*-
"""
Interfaz PyQt6 (`machine_resource_manager`): widgets, diálogos o recursos visuales conectados al flujo de usuario.
"""

from PyQt6.QtWidgets import QLabel, QCheckBox
from typing import Any, List, Optional, Dict, TYPE_CHECKING
if TYPE_CHECKING:
    from ui.widgets.production_flow.define_control_panel import DefineControlPanel
    from ui.dialogs.production_flow.define_flow_presenter import DefineFlowPresenter
    from core.dtos import FlowTaskDataDTO

class MachineResourceManager:
    """
    Gestiona la lógica de recursos de máquina y fases de preparación para DefineProductionFlowDialog.
    Desacopla la carga dinámica de componentes de la UI del diálogo principal.
    """
    def __init__(self, control_panel: "DefineControlPanel", presenter: "DefineFlowPresenter") -> None:
        self.panel = control_panel
        self.presenter = presenter

    def update_machines_for_task(self, task_info: Optional["FlowTaskDataDTO"]) -> None:
        """Configura el menú de máquinas basado en el tipo de tarea y carga valores por defecto."""
        menu = self.panel.machine_menu
        menu.blockSignals(True)
        menu.clear()

        if not task_info:
            self.panel.resource_layout.setRowVisible(0, False)
            menu.blockSignals(False)
            return

        self.panel.resource_layout.setRowVisible(0, True)
        tipo_requerido = task_info.requiere_maquina_tipo
        product_code = task_info.original_product_code

        default_group_id, default_machine_id = self.presenter.get_prep_info(product_code)

        if tipo_requerido:
            menu.setEnabled(True)
            machines = self.presenter.get_machines_for_task(task_info)
            if machines:
                menu.addItem("--- Seleccione una Máquina ---", userData=None)
                for m in machines:
                    menu.addItem(m.nombre, userData=m.id)
            else:
                menu.addItem(f"¡No hay máquinas para '{tipo_requerido}'!", userData=None)
                menu.setEnabled(False)

            if default_machine_id:
                idx = menu.findData(default_machine_id)
                if idx != -1:
                    menu.setCurrentIndex(idx)
                    menu.setProperty("default_group_id", default_group_id)
            else:
                menu.setProperty("default_group_id", None)
        else:
            menu.addItem("Esta tarea no requiere máquina", userData=None)
            menu.setEnabled(False)

        menu.blockSignals(False)
        self.load_prep_steps()

    def load_prep_steps(self) -> None:
        """Carga dinámicamente los checkboxes de fases de preparación para la máquina seleccionada."""
        self.panel.clear_prep_steps()
        
        machine_id = self.panel.machine_menu.currentData()
        if machine_id is None:
            self.panel.prep_steps_scroll.setVisible(False)
            self.panel.prep_steps_label.setVisible(False)
            return

        all_steps = self.presenter.get_prep_steps_for_machine(machine_id)

        if not all_steps:
            self.panel.prep_steps_layout.addWidget(QLabel("Máquina sin fases de preparación."))
            self.panel.prep_steps_scroll.setVisible(True)
            self.panel.prep_steps_label.setVisible(True)
            return

        for step in all_steps:
            cb = QCheckBox(f"{step.nombre} ({step.tiempo_fase} min)")
            cb.setProperty("step_id", step.id)
            self.panel.prep_steps_layout.addWidget(cb)
            self.panel.prep_steps_checkboxes.append(cb)

        # Aplicar estados inactivos para fases obligatorias (default)
        default_group_id = self.panel.machine_menu.property("default_group_id")
        if default_group_id:
            default_step_ids = self.presenter.get_default_step_ids(default_group_id)
            for cb in self.panel.prep_steps_checkboxes:
                if cb.property("step_id") in default_step_ids:
                    cb.setChecked(True)
                    cb.setEnabled(False)
                    cb.setStyleSheet("QCheckBox { color: #005A9C; font-weight: bold; }")

        self.panel.prep_steps_scroll.setVisible(True)
        self.panel.prep_steps_label.setVisible(True)
