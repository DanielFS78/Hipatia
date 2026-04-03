"""Tests para diálogos comunes del flujo de producción."""
import pytest
from typing import Any
from PyQt6.QtWidgets import QDialogButtonBox
from ui.dialogs.production_flow.common_dialogs import (
    CycleEndConfigDialog, ReassignmentRuleDialog, DefinirCantidadesDialog
)

@pytest.fixture
def sample_tasks():
    return [
        {"data": {"id": "T0", "name": "Tarea 0"}, "config": {"is_cycle_start": True}},
        {"data": {"id": "T1", "name": "Tarea 1"}, "config": {"is_cycle_start": False}},
        {"data": {"id": "T2", "name": "Tarea 2"}, "config": {"is_cycle_start": False}}
    ]

@pytest.mark.unit
class TestCycleEndConfigDialog:
    def test_init_and_get_config(self, qtbot, sample_tasks):
        # Tareas en formato canvas (con data y config)
        canvas_tasks = [
            {"data": t["data"], "config": t["config"]} for t in sample_tasks
        ]
        dialog = CycleEndConfigDialog(current_task_index=1, all_canvas_tasks=canvas_tasks)
        qtbot.addWidget(dialog)
        
        assert dialog.windowTitle() == "Configurar Fin de Ciclo"
        assert dialog.tasks_list.count() == 3 # No regresar + T0 + T2 (T1 no está porque es la actual)
        
        # Seleccionar T0
        dialog.tasks_list.setCurrentRow(1)
        dialog.mark_as_end_checkbox.setChecked(True)
        
        config = dialog.get_configuration()
        assert config['is_cycle_end'] is True
        assert config['return_to_index'] == 0

    def test_init_with_existing_config(self, qtbot, sample_tasks):
        canvas_tasks = [
            {"data": t["data"], "config": {"is_cycle_end": True, "cycle_return_to_index": 0}} 
            if i == 1 else {"data": t["data"], "config": {}} 
            for i, t in enumerate(sample_tasks)
        ]
        dialog = CycleEndConfigDialog(current_task_index=1, all_canvas_tasks=canvas_tasks)
        qtbot.addWidget(dialog)
        
        from PyQt6.QtCore import Qt
        assert dialog.mark_as_end_checkbox.isChecked() is True
        item = dialog.tasks_list.currentItem()
        assert item is not None
        assert item.data(Qt.ItemDataRole.UserRole) == 0

@pytest.mark.unit
class TestReassignmentRuleDialog:
    def test_init_and_get_rule_parallel(self, qtbot, sample_tasks):
        current_task = sample_tasks[0]['data']
        dialog = ReassignmentRuleDialog(
            worker_name="W1",
            current_task=current_task,
            all_canvas_tasks=sample_tasks,
            current_rule=None
        )
        qtbot.addWidget(dialog)
        
        dialog.rb_after_units.setChecked(True)
        dialog.sb_units_value.setValue(10)
        dialog.cb_target_task.setCurrentIndex(1) # Tarea 1
        dialog.tipo_paralelo.setChecked(True)
        
        rule = dialog.get_rule()
        assert rule is not None
        assert rule['condition_type'] == 'AFTER_UNITS'
        assert rule['condition_value'] == 10
        assert rule['mode'] == 'PARALLEL_JOIN'

    def test_init_with_existing_rule(self, qtbot, sample_tasks):
        current_task = sample_tasks[0]['data']
        existing_rule = {
            "condition_type": "AFTER_UNITS",
            "condition_value": 5,
            "target_task_id": "T2",
            "mode": "PARALLEL_JOIN"
        }
        dialog = ReassignmentRuleDialog(
            worker_name="W1",
            current_task=current_task,
            all_canvas_tasks=sample_tasks,
            current_rule=existing_rule
        )
        qtbot.addWidget(dialog)
        
        assert dialog.rb_after_units.isChecked()
        assert dialog.sb_units_value.value() == 5
        assert dialog.tipo_paralelo.isChecked()

@pytest.mark.unit
class TestDefinirCantidadesDialog:
    def test_init_and_get_cantidades(self, qtbot):
        flow: list[dict[str, Any]] = [
            {"type": "task", "task": {"name": "T0"}},
            {"type": "sequential_group", "tasks": [{"task": {"name": "G1"}}, {"task": {"name": "G2"}}]}
        ]
        dialog = DefinirCantidadesDialog(production_flow=flow)
        qtbot.addWidget(dialog)
        
        assert dialog.table.rowCount() == 2
        dialog.spin_boxes[0].setValue(100)
        dialog.spin_boxes[1].setValue(200)
        
        cantidades = dialog.get_cantidades()
        assert cantidades[0] == 100
        assert cantidades[1] == 200
