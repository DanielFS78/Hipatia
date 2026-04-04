# -*- coding: utf-8 -*-
"""
Interfaz PyQt6 (`define_flow_dialog`): widgets, diálogos o recursos visuales conectados al flujo de usuario.
"""

import logging
from typing import List, Dict, Any, Optional, TYPE_CHECKING
from PyQt6.QtWidgets import (
    QDialog, QHBoxLayout, QVBoxLayout, QMessageBox, QDialogButtonBox, QWidget, QInputDialog
)
from ui.widgets.production_flow.define_control_panel import DefineControlPanel
from ui.dialogs.utility_dialogs import MultiWorkerSelectionDialog
from ui.dialogs.fabrication.persistence_dialogs import SavePilaDialog
from ui.dialogs.production_flow.define_flow_presenter import DefineFlowPresenter
from ui.widgets.production_flow.flow_display_panel import FlowDisplayPanel
from ui.dialogs.production_flow.machine_resource_manager import MachineResourceManager
from core.define_flow_form_io import define_form_data_to_flow_task_config
from core.dtos import ProductionFlowStepDTO, FlowTaskDataDTO
from core.di_container import DIContainer
from core.services.machine_service import MachineService
from core.services.preparation_service import PreparationService
from ui.dialogs.fabrication.dialog_dependencies import resolve_fabricacion_service

if TYPE_CHECKING:
    from controllers.app_controller import AppController
    from core.config import ScheduleConfig

class DefineProductionFlowDialog(QDialog):
    """Diálogo orquestador para definir la secuencia de tareas, dependencias y trabajadores."""

    def __init__(
        self, 
        tasks_data: List[Dict[str, Any]], 
        workers: List[str], 
        units: int, 
        controller: Optional["AppController"], 
        schedule_config: "ScheduleConfig", 
        parent: Optional[QWidget] = None, 
        existing_flow: Optional[List[Dict[str, Any]] | List[ProductionFlowStepDTO]] = None
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Definir Pila de Producción")
        self.setMinimumSize(1100, 700)
        self.units = units
        self.workers = sorted(workers)
        self.controller = controller
        # Compatibilidad con tests/consumidores legacy que inspeccionan este atributo.
        self.schedule_config = schedule_config
        
        _c = DIContainer.get_instance()
        _use_services = _c.is_registered(MachineService) and _c.is_registered(PreparationService)
        _presenter_kw: dict[str, Any] = {
            "schedule_config": schedule_config,
            "default_units": units,
        }
        if _use_services:
            _presenter_kw["machine_service"] = _c.resolve(MachineService)
            _presenter_kw["preparation_service"] = _c.resolve(PreparationService)
            fs = resolve_fabricacion_service(controller, _c)
            if fs is not None:
                _presenter_kw["fabricacion_service"] = fs
            _presenter_kw["model"] = None
        else:
            m = controller.model if controller else None
            _presenter_kw["model"] = m
            # Misma frontera que con DI: servicios colgando de AppModel (sin registrar tipos en el contenedor).
            if m is not None:
                ms = getattr(m, "machine_service", None)
                if ms is not None:
                    _presenter_kw["machine_service"] = ms
                prep = getattr(m, "preparation_service", None)
                if prep is not None:
                    _presenter_kw["preparation_service"] = prep
                fab = getattr(m, "fabricacion_service", None)
                if fab is not None:
                    _presenter_kw["fabricacion_service"] = fab
        self.presenter = DefineFlowPresenter(**_presenter_kw)
        self.task_data_by_product = self.presenter.prepare_task_data(tasks_data)
        self.editing_index: Optional[int] = None

        if existing_flow:
            self.presenter.set_production_flow(existing_flow)

        self._init_components()
        self._connect_signals()
        self._initial_load(existing_flow is not None)

    def _init_components(self) -> None:
        """Inicializa los sub-componentes y managers."""
        self.control_panel = DefineControlPanel(self.task_data_by_product, self.workers, self.units, self)
        self.flow_display_panel = FlowDisplayPanel(self)
        # Alias de compatibilidad histórica (botones movidos al sub-panel derecho).
        self.save_flow_button = self.flow_display_panel.save_flow_button
        self.group_steps_button = self.flow_display_panel.group_steps_button
        self.resource_manager = MachineResourceManager(self.control_panel, self.presenter)

        main_layout = QHBoxLayout(self)
        main_layout.addWidget(self.control_panel, 1)
        
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.addWidget(self.flow_display_panel)
        
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        right_layout.addWidget(button_box)
        
        main_layout.addWidget(right_container, 2)

    def _connect_signals(self) -> None:
        """Conecta las señales de los componentes."""
        # Señales del panel de control
        self.control_panel.task_selected_signal.connect(self._on_task_selected)
        self.control_panel.add_update_clicked.connect(self._add_or_update_step)
        self.control_panel.start_condition_changed.connect(self._toggle_start_condition)
        self.control_panel.machine_changed_signal.connect(self.resource_manager.load_prep_steps)
        self.control_panel.cancel_edit_clicked.connect(self._reset_form)

        # Señales del panel de visualización
        self.flow_display_panel.edit_requested.connect(self._edit_step)
        self.flow_display_panel.delete_requested.connect(self._delete_step)
        self.flow_display_panel.assign_workers_requested.connect(self._assign_worker_to_group)
        self.flow_display_panel.group_selected_requested.connect(self._group_selected_steps)
        self.flow_display_panel.save_flow_requested.connect(self._on_save_flow)

    def _initial_load(self, is_editing: bool) -> None:
        """Realiza la carga inicial de datos."""
        self._update_flow_display()
        self._update_previous_task_menu()
        if is_editing:
            self.setWindowTitle("Editar Pila de Producción")
        else:
            self._toggle_start_condition()
            self._on_task_selected(None)

    def _on_save_flow(self) -> None:
        """Gestiona el guardado de un flujo sin calcular."""
        flow = self.presenter.get_production_flow()
        if not flow:
            QMessageBox.warning(self, "Flujo Vacío", "No hay pasos en el flujo para guardar.")
            return

        dialog = SavePilaDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            nombre, descripcion = dialog.get_data()
            if not nombre:
                QMessageBox.warning(self, "Nombre Requerido", "El nombre de la pila es obligatorio.")
                return
            if self.controller:
                self.controller.handle_save_flow_only(nombre, descripcion, flow)
            QMessageBox.information(self, "Éxito", f"El flujo '{nombre}' ha sido guardado.")

    def _on_task_selected(self, task_info: Optional[FlowTaskDataDTO] = None) -> None:
        """Delega la actualización de máquinas al resource manager."""
        if not task_info:
             task_info = self.control_panel.get_selected_task()
        if task_info:
            self.resource_manager.update_machines_for_task(task_info)

    def _on_machine_selected(self) -> None:
        """Capa de compatibilidad para tests."""
        self.resource_manager.load_prep_steps()

    def _add_or_update_step(self) -> None:
        """Añade o actualiza un paso en la pila."""
        task_info = None
        if self.editing_index is not None:
            step = self.presenter.get_step(self.editing_index)
            if step:
                task_info = step.task
        else:
            task_info = self.control_panel.get_selected_task()

        if not task_info:
            QMessageBox.warning(self, "Selección Requerida", "Debe seleccionar una tarea específica.")
            return

        form_data = self.control_panel.get_form_data()
        config_dto = define_form_data_to_flow_task_config(form_data, self.units)
        if task_info.requiere_maquina_tipo and config_dto.machine_id is None:
            QMessageBox.warning(self, "Error", "Debe asignar una máquina disponible para esta tarea.")
            return
        step_dto = ProductionFlowStepDTO(task=task_info, config=config_dto)
        
        if self.editing_index is not None:
            self.presenter.update_step(self.editing_index, step_dto)
        else:
            self.presenter.add_step(step_dto)

        self._update_flow_display()
        self._reset_form()

    def _update_flow_display(self) -> None:
        """Actualiza el panel de visualización del flujo."""
        self.flow_display_panel.update_display(self.presenter.get_production_flow(), self.presenter)

    def _reset_form(self) -> None:
        """Limpia el formulario y resincroniza."""
        self.editing_index = None
        self.control_panel.clear_form()
        self._update_previous_task_menu()
        self._toggle_start_condition()
        self._on_task_selected(None)

    def _edit_step(self, index: int) -> None:
        """Prepara el formulario para editar un paso."""
        self.editing_index = index
        step = self.presenter.get_step(index)
        if not step: return
        
        task_name = step.task.name
        self.control_panel.set_editing_mode(True, task_name, index)
        self.control_panel.populate_form(step)
        self._toggle_start_condition()
        self._on_task_selected(step.task)
        
        if step.config.machine_id:
            idx = self.control_panel.machine_menu.findData(step.config.machine_id)
            if idx != -1: self.control_panel.machine_menu.setCurrentIndex(idx)

    def _toggle_start_condition(self) -> None:
        """Coordina la habilitación de condiciones de inicio."""
        has_flow = len(self.presenter.get_production_flow()) > 0
        self.control_panel.dependency_radio.setEnabled(has_flow)
        
        is_dep = self.control_panel.dependency_radio.isChecked()
        is_worker = self.control_panel.worker_dependency_radio.isChecked()
        is_date = self.control_panel.start_date_radio.isChecked()

        self.control_panel.start_date_entry.setEnabled(is_date)
        self.control_panel.previous_task_menu.setEnabled(is_dep)
        self.control_panel.min_predecessor_units_entry.setEnabled(is_dep)
        self.control_panel.worker_dependency_menu.setEnabled(is_worker)

        if not has_flow and (is_dep or is_worker):
             self.control_panel.start_date_radio.setChecked(True)

    def _update_previous_task_menu(self) -> None:
        """Puebla el menú de dependencias."""
        menu = self.control_panel.previous_task_menu
        menu.clear()
        flow = self.presenter.get_production_flow()
        added = False
        for i, step in enumerate(flow):
            if i == self.editing_index: continue
            name = f"Paso {i + 1}: " + (step.task.name if not step.config.is_group else "Grupo Secuencial")
            menu.addItem(name, i)
            added = True
        if not added:
            menu.addItem("(No hay tareas previas)")
            self.control_panel.dependency_radio.setEnabled(False)

    def _delete_step(self, index: int) -> None:
        """Elimina un paso tras confirmación."""
        if QMessageBox.question(self, "Confirmar Eliminación", f"¿Eliminar Paso {index + 1}?") == QMessageBox.StandardButton.Yes:
            self.presenter.delete_step(index)
            self._update_flow_display()
            self._reset_form()

    def _assign_worker_to_group(self, index: int) -> None:
        """Asigna trabajadores a un grupo secuencial."""
        step = self.presenter.get_step(index)
        if not step or not step.config.is_group: return
        
        dialog = MultiWorkerSelectionDialog(self.workers, step.config.workers, self)
        if dialog.exec():
            selected = dialog.get_selected_workers()
            if selected:
                step.config.workers = selected
                self._update_flow_display()

    def _group_selected_steps(self) -> None:
        """Agrupa los pasos seleccionados."""
        indices = self.flow_display_panel.get_selected_indices()
        if len(indices) < 2:
            QMessageBox.warning(self, "Selección Insuficiente", "Seleccione al menos dos tareas.")
            return

        dialog = MultiWorkerSelectionDialog(self.workers, parent=self)
        if not dialog.exec(): return
        workers = dialog.get_selected_workers()
        if not workers: return

        units, ok = QInputDialog.getInt(self, "Configurar Ciclo", "Unidades por ciclo:", 20, 1, self.units)
        if not ok: return

        try:
            self.presenter.group_tasks(indices, workers, units, self.units)
            self._update_flow_display()
            self._reset_form()
        except ValueError as e:
            QMessageBox.warning(self, "Error al agrupar", str(e))

    def get_production_flow(self) -> List[ProductionFlowStepDTO]:
        return self.presenter.get_production_flow()

    @property
    def flow_item_widgets(self) -> List[Any]:
        """Capa de compatibilidad para la suite de tests."""
        return self.flow_display_panel.flow_item_widgets
