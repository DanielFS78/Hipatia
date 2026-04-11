# -*- coding: utf-8 -*-
"""
Nombre del Módulo: inspector_ui

Descripción: Construcción de la UI del inspector de tareas: factoría ``build_inspector_ui`` y
             dataclass ``InspectorWidgets`` con referencias a los controles Qt.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from PyQt6.QtCore import Qt, QDateTime
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDateTimeEdit,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


@dataclass
class InspectorWidgets:
    """Referencias tipadas a los controles del inspector de tarea."""

    title: QLabel
    duration_label: QLabel
    start_date_radio: QRadioButton
    start_date_edit: QDateTimeEdit
    dependency_radio: QRadioButton
    dependency_combo: QComboBox
    min_units_spin: QSpinBox
    start_condition_group: QGroupBox
    cycle_start_cb: QCheckBox
    units_spin: QSpinBox
    units_per_cycle_spin: QSpinBox
    next_cyclic_combo: QComboBox
    machine_combo: QComboBox
    available_workers_list: QListWidget
    assign_btn: QPushButton
    unassign_btn: QPushButton
    assigned_workers_list: QListWidget
    reassign_btn: QPushButton
    cycle_end_btn: QPushButton


def _create_list_widget() -> QListWidget:
    lw = QListWidget()
    lw.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
    return lw


def build_inspector_ui(
    parent: QWidget,
    *,
    on_toggle_start_widgets: Callable[[], None],
    on_emit_change: Callable[[str, Any], None],
    on_dependency_changed: Callable[[], None],
    on_next_cyclic_changed: Callable[[], None],
    on_machine_changed: Callable[[], None],
    on_assign_worker: Callable[[], None],
    on_unassign_worker: Callable[[], None],
    on_action_triggered: Callable[[str], None],
) -> tuple[InspectorWidgets, QScrollArea, QLabel]:
    """
    Construye la UI del inspector y devuelve `InspectorWidgets`, `content_scroll`, `placeholder`.
    """
    main_layout = QVBoxLayout(parent)
    main_layout.setContentsMargins(10, 10, 10, 10)
    main_layout.setSpacing(15)

    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.Shape.NoFrame)

    content_widget = QWidget()
    content_layout = QVBoxLayout(content_widget)
    content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

    scroll.setWidget(content_widget)
    main_layout.addWidget(scroll)

    title_lbl = QLabel("Propiedades de Tarea")
    font = title_lbl.font()
    font.setPointSize(14)
    font.setBold(True)
    title_lbl.setFont(font)
    title_lbl.setWordWrap(True)
    content_layout.addWidget(title_lbl)

    duration_label = QLabel()
    duration_label.setStyleSheet("font-style: italic; color: #888;")
    content_layout.addWidget(duration_label)

    group = QGroupBox("Condición de Inicio")
    layout = QVBoxLayout(group)

    start_date_radio = QRadioButton("Fecha y Hora Específica")
    layout.addWidget(start_date_radio)

    start_date_edit = QDateTimeEdit(QDateTime.currentDateTime())
    start_date_edit.setCalendarPopup(True)
    start_date_edit.setDisplayFormat("dd/MM/yyyy HH:mm")
    layout.addWidget(start_date_edit)

    dependency_radio = QRadioButton("Al finalizar otra tarea")
    layout.addWidget(dependency_radio)

    dep_layout = QHBoxLayout()
    dep_layout.addWidget(QLabel("Predecesora:"))
    dependency_combo = QComboBox()
    dep_layout.addWidget(dependency_combo)
    layout.addLayout(dep_layout)

    min_units_layout = QHBoxLayout()
    min_units_spin = QSpinBox()
    min_units_spin.setRange(1, 99999)
    min_units_spin.setSuffix(" uds")
    min_units_layout.addWidget(QLabel("Esperar:"))
    min_units_layout.addWidget(min_units_spin)
    layout.addLayout(min_units_layout)

    start_condition_group = group
    content_layout.addWidget(group)

    start_date_radio.toggled.connect(on_toggle_start_widgets)
    dependency_radio.toggled.connect(on_toggle_start_widgets)

    start_date_radio.toggled.connect(
        lambda: on_emit_change("start_condition_type", "date") if start_date_radio.isChecked() else None
    )
    start_date_edit.dateTimeChanged.connect(lambda dt: on_emit_change("start_date", dt.toPyDateTime()))
    dependency_radio.toggled.connect(
        lambda: on_emit_change("start_condition_type", "dependency")
        if dependency_radio.isChecked()
        else None
    )
    dependency_combo.currentIndexChanged.connect(on_dependency_changed)
    min_units_spin.valueChanged.connect(lambda v: on_emit_change("min_predecessor_units", v))

    group = QGroupBox("Marcador de Ciclo")
    layout = QVBoxLayout(group)
    cycle_start_cb = QCheckBox("⭐ Marcar Inicio de Ciclo")
    cycle_start_cb.setStyleSheet("font-weight: bold; color: #f39c12;")
    layout.addWidget(cycle_start_cb)
    content_layout.addWidget(group)
    cycle_start_cb.stateChanged.connect(lambda s: on_emit_change("is_cycle_start", bool(s)))

    group = QGroupBox("Objetivos")
    goals_layout = QFormLayout(group)
    units_spin = QSpinBox()
    units_spin.setRange(1, 999999)
    goals_layout.addRow("Unidades:", units_spin)
    units_per_cycle_spin = QSpinBox()
    units_per_cycle_spin.setRange(1, 99999)
    goals_layout.addRow("Uds/Ciclo:", units_per_cycle_spin)
    next_cyclic_combo = QComboBox()
    goals_layout.addRow("Sig. Tarea Cíclica:", next_cyclic_combo)
    content_layout.addWidget(group)
    units_spin.valueChanged.connect(lambda v: on_emit_change("total_units", v))
    units_per_cycle_spin.valueChanged.connect(lambda v: on_emit_change("units_per_cycle", v))
    next_cyclic_combo.currentIndexChanged.connect(on_next_cyclic_changed)

    group = QGroupBox("Recursos")
    resources_layout = QFormLayout(group)
    machine_combo = QComboBox()
    resources_layout.addRow("Máquina:", machine_combo)
    content_layout.addWidget(group)
    machine_combo.currentIndexChanged.connect(on_machine_changed)

    group = QGroupBox("Gestión de Trabajadores")
    main_layout_workers = QVBoxLayout(group)
    lists_layout = QHBoxLayout()

    avail_layout = QVBoxLayout()
    avail_layout.addWidget(QLabel("Disponibles"))
    available_workers_list = _create_list_widget()
    avail_layout.addWidget(available_workers_list)

    btns_layout = QVBoxLayout()
    btns_layout.addStretch()
    assign_btn = QPushButton(">>")
    unassign_btn = QPushButton("<<")
    btns_layout.addWidget(assign_btn)
    btns_layout.addWidget(unassign_btn)
    btns_layout.addStretch()

    assigned_layout = QVBoxLayout()
    assigned_layout.addWidget(QLabel("Asignados"))
    assigned_workers_list = _create_list_widget()
    assigned_layout.addWidget(assigned_workers_list)

    lists_layout.addLayout(avail_layout)
    lists_layout.addLayout(btns_layout)
    lists_layout.addLayout(assigned_layout)
    main_layout_workers.addLayout(lists_layout)
    content_layout.addWidget(group)

    assign_btn.clicked.connect(on_assign_worker)
    unassign_btn.clicked.connect(on_unassign_worker)

    adv_group = QGroupBox("Configuración Avanzada")
    adv_layout = QHBoxLayout(adv_group)
    reassign_btn = QPushButton("🔧 Reasignación")
    reassign_btn.setToolTip("Configurar reglas de reasignación")
    cycle_end_btn = QPushButton("🔄 Fin de Ciclo")
    cycle_end_btn.setToolTip("Configurar retorno de ciclo")
    adv_layout.addWidget(reassign_btn)
    adv_layout.addWidget(cycle_end_btn)
    content_layout.addWidget(adv_group)

    reassign_btn.clicked.connect(lambda: on_action_triggered("configure_reassignment"))
    cycle_end_btn.clicked.connect(lambda: on_action_triggered("configure_cycle_end"))

    del_group = QGroupBox("Acciones")
    del_layout = QVBoxLayout(del_group)
    btn_delete = QPushButton("🗑 Eliminar Tarea")
    btn_delete.setStyleSheet("background-color: #e74c3c; color: white; font-weight: bold;")
    del_layout.addWidget(btn_delete)
    content_layout.addWidget(del_group)
    btn_delete.clicked.connect(lambda: on_action_triggered("delete"))

    placeholder = QLabel(
        "PANEL INSPECTOR\n\n"
        "Selecciona una tarea en el canvas\n"
        "para configurar sus detalles."
    )
    placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
    placeholder.setStyleSheet("color: #777; font-size: 12px; margin-top: 50px;")
    main_layout.addWidget(placeholder)

    scroll.setVisible(False)

    widgets = InspectorWidgets(
        title=title_lbl,
        duration_label=duration_label,
        start_date_radio=start_date_radio,
        start_date_edit=start_date_edit,
        dependency_radio=dependency_radio,
        dependency_combo=dependency_combo,
        min_units_spin=min_units_spin,
        start_condition_group=start_condition_group,
        cycle_start_cb=cycle_start_cb,
        units_spin=units_spin,
        units_per_cycle_spin=units_per_cycle_spin,
        next_cyclic_combo=next_cyclic_combo,
        machine_combo=machine_combo,
        available_workers_list=available_workers_list,
        assign_btn=assign_btn,
        unassign_btn=unassign_btn,
        assigned_workers_list=assigned_workers_list,
        reassign_btn=reassign_btn,
        cycle_end_btn=cycle_end_btn,
    )
    return widgets, scroll, placeholder
