"""
Interfaz PyQt6 (`define_control_panel`): widgets, diálogos o recursos visuales conectados al flujo de usuario.
"""

import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QLabel, QCheckBox,
    QScrollArea, QComboBox, QTreeWidget,
    QTreeWidgetItem, QDateEdit, QRadioButton, QFrame
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from typing import Any, Dict, List, TYPE_CHECKING, Optional, cast
from core.dtos import FlowTaskDataDTO, ProductionFlowStepDTO, ProductFlowLibraryProductDTO

if TYPE_CHECKING:
    from core.dtos import FlowTaskDataDTO, ProductionFlowStepDTO

class DefineControlPanel(QFrame):
    """
    Panel de control lateral para añadir y editar pasos en el flujo de producción.
    Encapsula la interfaz de configuración de tareas, condiciones de inicio y recursos.
    """
    
    # Señales para notificar al diálogo/presenter sobre interacciones del usuario
    task_selected_signal = pyqtSignal(object) # Emitirá FlowTaskDataDTO
    add_update_clicked = pyqtSignal()
    cancel_edit_clicked = pyqtSignal()
    machine_changed_signal = pyqtSignal()
    start_condition_changed = pyqtSignal()

    def __init__(
        self,
        task_data_by_product: Dict[str, ProductFlowLibraryProductDTO],
        workers: List[str],
        units: int,
        parent: Any = None,
    ) -> None:
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.task_data_by_product = task_data_by_product
        self.workers = workers
        self.units = units
        self.start_date_radio: QRadioButton
        
        self.prep_steps_checkboxes: list[Any] = []
        self.worker_checkboxes: dict[str, Any] = {}
        
        self._setup_ui()
        self._connect_internal_signals()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.edit_info_label = QLabel("<b>Añadir Nuevo Paso a la Pila</b>")
        font = self.edit_info_label.font()
        font.setPointSize(12)
        self.edit_info_label.setFont(font)
        layout.addWidget(self.edit_info_label)

        # --- SECCIÓN 1: Selección de Tarea ---
        layout.addWidget(QLabel("<b>1. Tarea Base</b>"))
        self.task_tree = QTreeWidget()
        self.task_tree.setHeaderLabel("Productos y Tareas de la Fabricación")
        for product_code, product_info in self.task_data_by_product.items():
            product_item = QTreeWidgetItem(
                self.task_tree, [f"{product_info.descripcion} ({product_code})"]
            )
            product_font = product_item.font(0)
            product_font.setBold(True)
            product_item.setFont(0, product_font)
            product_item.setFlags(product_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            for task in product_info.tasks:
                task_item = QTreeWidgetItem(product_item, [f"({task.department}) {task.name}"])
                task_item.setData(0, Qt.ItemDataRole.UserRole, task)
            product_item.setExpanded(True)
        layout.addWidget(self.task_tree, 1)

        # --- SECCIÓN 2: Condiciones ---
        layout.addWidget(QLabel("<b>2. Condición de Inicio</b>"))

        self.start_date_radio = QRadioButton("Iniciar en fecha específica")
        self.start_date_radio.setChecked(True)
        layout.addWidget(self.start_date_radio)
        self.start_date_entry = QDateEdit(QDate.currentDate())
        layout.addWidget(self.start_date_entry)

        self.dependency_radio = QRadioButton("Depende de tarea previa")
        layout.addWidget(self.dependency_radio)

        dep_task_layout = QHBoxLayout()
        dep_task_layout.addWidget(QLabel("Tarea predecesora:"))
        self.previous_task_menu = QComboBox()
        dep_task_layout.addWidget(self.previous_task_menu)
        layout.addLayout(dep_task_layout)

        min_pred_layout = QHBoxLayout()
        min_pred_label = QLabel("Esperar a que complete (unidades):")
        self.min_predecessor_units_entry = QLineEdit("1")
        self.min_predecessor_units_entry.setMaximumWidth(80)
        min_pred_layout.addWidget(min_pred_label)
        min_pred_layout.addWidget(self.min_predecessor_units_entry)
        min_pred_layout.addStretch()
        layout.addLayout(min_pred_layout)

        units_layout = QHBoxLayout()
        units_label = QLabel("Unidades a producir de ESTA tarea:")
        self.trigger_units_entry = QLineEdit(str(self.units))
        self.trigger_units_entry.setMaximumWidth(80)
        units_layout.addWidget(units_label)
        units_layout.addWidget(self.trigger_units_entry)
        units_layout.addStretch()
        layout.addLayout(units_layout)

        self.worker_dependency_radio = QRadioButton("Depende de trabajador disponible")
        layout.addWidget(self.worker_dependency_radio)
        self.worker_dependency_menu = QComboBox()
        self.worker_dependency_menu.addItems(self.workers)
        layout.addWidget(self.worker_dependency_menu)

        # --- SECCIÓN 3: Recursos ---
        layout.addWidget(QLabel("<b>3. Recursos Asignados</b>"))
        self.resource_layout = QFormLayout()
        self.machine_menu = QComboBox()
        self.resource_layout.addRow("Máquina:", self.machine_menu)
        layout.addLayout(self.resource_layout)

        self.prep_steps_label = QLabel("Fases de Preparación para esta Tarea:")
        self.prep_steps_scroll = QScrollArea()
        self.prep_steps_scroll.setWidgetResizable(True)
        self.prep_steps_container = QWidget()
        self.prep_steps_layout = QVBoxLayout(self.prep_steps_container)
        self.prep_steps_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.prep_steps_scroll.setWidget(self.prep_steps_container)
        layout.addWidget(self.prep_steps_label)
        layout.addWidget(self.prep_steps_scroll, 1)

        layout.addWidget(QLabel("Trabajadores:"))
        worker_scroll = QScrollArea()
        worker_scroll.setWidgetResizable(True)
        worker_widget = QWidget()
        worker_layout = QVBoxLayout(worker_widget)
        worker_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        for worker in self.workers:
            cb = QCheckBox(worker)
            self.worker_checkboxes[worker] = cb
            worker_layout.addWidget(cb)
        worker_scroll.setWidget(worker_widget)
        layout.addWidget(worker_scroll)

        # --- SECCIÓN 4: Botones ---
        self.add_update_button = QPushButton("Añadir a la Pila ▼")
        self.cancel_edit_button = QPushButton("Cancelar Edición")
        self.cancel_edit_button.setVisible(False)

        action_button_layout = QHBoxLayout()
        action_button_layout.addWidget(self.cancel_edit_button)
        action_button_layout.addStretch()
        action_button_layout.addWidget(self.add_update_button)
        layout.addLayout(action_button_layout)

    def _connect_internal_signals(self) -> None:
        self.task_tree.currentItemChanged.connect(self._emit_task_selected)
        self.start_date_radio.toggled.connect(lambda: self.start_condition_changed.emit())
        self.dependency_radio.toggled.connect(lambda: self.start_condition_changed.emit())
        self.worker_dependency_radio.toggled.connect(lambda: self.start_condition_changed.emit())
        self.machine_menu.currentIndexChanged.connect(lambda: self.machine_changed_signal.emit())
        self.add_update_button.clicked.connect(self.add_update_clicked.emit)
        self.cancel_edit_button.clicked.connect(self.cancel_edit_clicked.emit)

    def _emit_task_selected(self, current: Any, previous: Any) -> None:
        if current and current.parent():
            task_info = current.data(0, Qt.ItemDataRole.UserRole)
            self.task_selected_signal.emit(task_info)
        else:
            self.task_selected_signal.emit(None)

    def get_selected_task(self) -> Optional[FlowTaskDataDTO]:
        item = self.task_tree.currentItem()
        if item and item.parent():
            return cast(FlowTaskDataDTO, item.data(0, Qt.ItemDataRole.UserRole))
        return None

    def set_editing_mode(self, is_editing: bool, task_name: str | None = None, index: int | None = None) -> None:
        if is_editing:
            idx_str = str((index or 0) + 1)
            self.edit_info_label.setText(f"<b>Editando Paso {idx_str}: {task_name}</b>")
            self.add_update_button.setText("✓ Actualizar Paso")
            self.cancel_edit_button.setVisible(True)
            self.task_tree.setEnabled(False)
        else:
            self.edit_info_label.setText("<b>Añadir Nuevo Paso a la Pila</b>")
            self.add_update_button.setText("Añadir a la Pila ▼")
            self.cancel_edit_button.setVisible(False)
            self.task_tree.setEnabled(True)
            self.task_tree.clearSelection()

    def clear_form(self) -> None:
        self.start_date_radio.setChecked(True)
        self.trigger_units_entry.setText(str(self.units))
        for cb in self.worker_checkboxes.values():
            cb.setChecked(False)
        self.machine_menu.clear()
        self.clear_prep_steps()
        self.set_editing_mode(False)

    def clear_prep_steps(self) -> None:
        while self.prep_steps_layout.count():
            child = self.prep_steps_layout.takeAt(0)
            if not child:
                continue
            w = child.widget()
            if w is not None:
                w.deleteLater()
        self.prep_steps_checkboxes.clear()

    def get_form_data(self) -> Dict[str, Any]:
        """Recoge todos los datos configurados en el panel."""
        selected_workers = [worker for worker, cb in self.worker_checkboxes.items() if cb.isChecked()]
        
        data = {
            "workers": selected_workers,
            "machine_id": self.machine_menu.currentData(),
            "start_condition_type": "dependency" if self.dependency_radio.isChecked() else "worker" if self.worker_dependency_radio.isChecked() else "date",
            "start_condition_date": self.start_date_entry.date().toPyDate(),
            "previous_task_index": self.previous_task_menu.currentData(),
            "min_predecessor_units": int(self.min_predecessor_units_entry.text()) if self.min_predecessor_units_entry.text().isdigit() else 1,
            "depends_on_worker": self.worker_dependency_menu.currentText() if self.worker_dependency_radio.isChecked() else None,
            "selected_prep_steps": [cb.property("step_id") for cb in self.prep_steps_checkboxes if cb.isChecked()]
        }
        return data

    def populate_form(self, step: ProductionFlowStepDTO) -> None:
        """Puebla el formulario con datos de un paso existente (Fase 12C)."""
        config = step.config
        if config.start_condition_type == "date":
            self.start_date_radio.setChecked(True)
            if config.start_condition_date:
                self.start_date_entry.setDate(config.start_condition_date)
        elif config.previous_task_index is not None:
            self.dependency_radio.setChecked(True)
            idx = self.previous_task_menu.findData(config.previous_task_index)
            if idx != -1:
                self.previous_task_menu.setCurrentIndex(idx)
            self.min_predecessor_units_entry.setText(str(config.min_predecessor_units))
        elif config.depends_on_worker:
            self.worker_dependency_radio.setChecked(True)
            self.worker_dependency_menu.setCurrentText(config.depends_on_worker)
        
        for worker, cb in self.worker_checkboxes.items():
            cb.setChecked(worker in config.workers)
