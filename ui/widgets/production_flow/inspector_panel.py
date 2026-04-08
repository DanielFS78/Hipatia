"""
Interfaz PyQt6 (`inspector_panel`): widgets, diálogos o recursos visuales conectados al flujo de usuario.
"""

from dataclasses import fields
import logging
from typing import Any

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QLabel, QScrollArea, QWidget

from ui.widgets.production_flow.inspector_presenter import InspectorPresenter
from ui.widgets.production_flow.inspector_task_loader import apply_task_to_widgets
from ui.widgets.production_flow.inspector_ui import InspectorWidgets, build_inspector_ui


class ProductionTaskInspector(QWidget):
    """
    Panel lateral para inspeccionar y editar las propiedades de una tarea
    seleccionada en el flujo de producción.
    """

    widgets: InspectorWidgets
    content_scroll: QScrollArea
    placeholder: QLabel

    # Señal emitida cuando cambia cualquier configuración
    # Devuelve: (task_id, config_key, new_value)
    configChanged = pyqtSignal(str, object, object)

    # Señal específica para acciones complejas (como borrar tarea)
    actionTriggered = pyqtSignal(str, str)  # action_name, task_id

    def __init__(self, parent: Any = None) -> None:
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)

        self.presenter = InspectorPresenter()
        self.current_task_id: str | int | None = None
        self.current_task_data: dict[str, Any] | None = None
        self._init_ui()

    def _init_ui(self) -> None:
        """Inicializa la interfaz gráfica del inspector."""
        self.widgets, self.content_scroll, self.placeholder = build_inspector_ui(
            self,
            on_toggle_start_widgets=self._toggle_start_widgets,
            on_emit_change=self._emit_change,
            on_dependency_changed=self._on_dependency_changed,
            on_next_cyclic_changed=self._on_next_cyclic_changed,
            on_machine_changed=self._on_machine_changed,
            on_assign_worker=self._on_assign_worker,
            on_unassign_worker=self._on_unassign_worker,
            on_action_triggered=lambda action: self.actionTriggered.emit(
                action,
                str(self.current_task_id) if self.current_task_id is not None else "",
            ),
        )

    def _toggle_start_widgets(self) -> None:
        """Habilita/deshabilita widgets según el modo seleccionado."""
        w = self.widgets
        is_date = w.start_date_radio.isChecked()
        w.start_date_edit.setEnabled(is_date)

        is_dep = w.dependency_radio.isChecked()
        w.dependency_combo.setEnabled(is_dep)
        w.min_units_spin.setEnabled(is_dep)

    def _emit_change(self, key: str, value: Any) -> None:
        """Emite la señal de cambio si hay una tarea activa."""
        if self.current_task_id is not None:
            self.configChanged.emit(str(self.current_task_id), key, value)

    def _on_dependency_changed(self) -> None:
        w = self.widgets
        if w.dependency_combo.currentIndex() >= 0:
            val = w.dependency_combo.currentData()
            self._emit_change("previous_task_index", val)

    def _on_next_cyclic_changed(self) -> None:
        w = self.widgets
        if w.next_cyclic_combo.currentIndex() >= 0:
            val = w.next_cyclic_combo.currentData()
            self._emit_change("next_cyclic_task_index", val)

    def _on_machine_changed(self) -> None:
        w = self.widgets
        val = w.machine_combo.currentData()
        self._emit_change("machine_id", val)

    def _on_assign_worker(self) -> None:
        w = self.widgets
        selected_names = [i.text() for i in w.available_workers_list.selectedItems()]
        if not selected_names:
            return

        updated_workers = self.presenter.assign_workers(selected_names)
        self._emit_change("workers", updated_workers)

        self._sync_worker_lists()

    def _on_unassign_worker(self) -> None:
        w = self.widgets
        items_to_remove = [i.text() for i in w.assigned_workers_list.selectedItems()]
        if not items_to_remove:
            return

        updated_workers = self.presenter.unassign_workers(items_to_remove)
        self._emit_change("workers", updated_workers)

        self._sync_worker_lists()

    def _sync_worker_lists(self) -> None:
        w = self.widgets
        assigned_names, available_names = self.presenter.get_workers_lists()

        w.available_workers_list.clear()
        w.assigned_workers_list.clear()

        for name in assigned_names:
            w.assigned_workers_list.addItem(name)
        for name in available_names:
            w.available_workers_list.addItem(name)

    def get_selected_assigned_worker(self) -> str | None:
        """Devuelve el nombre del trabajador asignado seleccionado, o None."""
        w = self.widgets
        items = w.assigned_workers_list.selectedItems()
        if not items:
            return None
        return items[0].text()

    def set_task(self, task_data: dict[str, Any] | None, all_tasks: list[Any] | None = None, machines: list[Any] | None = None, available_workers: list[str] | None = None) -> None:
        """
        Carga una tarea en el inspector.

        Args:
            task_data (dict): Datos de la tarea (configuración).
            all_tasks (list): Lista de todas las tareas para llenar dependencias.
            machines (list): Lista de máquinas disponibles.
            available_workers (list): Lista de nombres de todos los trabajadores.
        """
        w = self.widgets

        if not task_data:
            self.current_task_id = None
            self.presenter.set_task(None, available_workers)
            self.content_scroll.setVisible(False)
            self.placeholder.setVisible(True)
            return

        # Bloquear señales para evitar rebotes durante la carga
        self.blockSignals(True)
        for f in fields(w):
            child = getattr(w, f.name)
            if hasattr(child, "blockSignals"):
                child.blockSignals(True)

        self.current_task_id, self.current_task_data = apply_task_to_widgets(
            task_data=task_data,
            widgets=w,
            presenter=self.presenter,
            all_tasks=all_tasks,
            machines=machines,
            available_workers=available_workers,
        )
        self._sync_worker_lists()

        # UI Logic Check
        self._toggle_start_widgets()

        for f in fields(w):
            child = getattr(w, f.name)
            if hasattr(child, "blockSignals"):
                child.blockSignals(False)
        self.blockSignals(False)

        self.content_scroll.setVisible(True)
        self.placeholder.setVisible(False)

    def clear(self) -> None:
        """Limpia el inspector ocultando el formulario y mostrando el placeholder."""
        self.set_task(None)
