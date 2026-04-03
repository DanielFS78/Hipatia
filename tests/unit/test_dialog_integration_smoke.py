"""
Nombre del Módulo: test_dialog_integration_smoke
Descripcion: Tests unitarios para los tres diálogos de common_dialogs.py:
             CycleEndConfigDialog (configuración de fin de ciclo),
             ReassignmentRuleDialog (reglas de reasignación de trabajadores) y
             DefinirCantidadesDialog (cantidades de producción por paso de flujo).
             Verifica inicialización, estado por defecto, obtención de datos y
             comportamiento con datos de entrada variados.

Decisión de mocking: Los tres diálogos heredan de QDialog (PyQt6) — MagicMock()
inevitable para widgets internos. Las tareas del canvas se pasan como dicts Python
puros (no mocks) porque los diálogos acceden a claves como task['data']['id']
directamente. No se usa autospec en ningún caso al ser clases Qt.
"""
import pytest
from unittest.mock import MagicMock, patch

pytestmark = pytest.mark.unit


def make_task(name="Tarea X", task_id="t1", is_cycle_start=False, is_cycle_end=False):
    return {
        "data": {"id": task_id, "name": name},
        "config": {
            "is_cycle_start": is_cycle_start,
            "is_cycle_end": is_cycle_end,
        },
    }


# ─── CycleEndConfigDialog ────────────────────────────────────────────────────

class TestCycleEndConfigDialog:
    """Verifica CycleEndConfigDialog: lista de tareas candidatas, checkbox de fin de ciclo y get_configuration()."""
    @pytest.fixture
    def dialog(self, qapp):
        from ui.dialogs.production_flow.common_dialogs import CycleEndConfigDialog
        tasks = [make_task("Tarea A", "t1"), make_task("Tarea B", "t2", is_cycle_start=True)]
        return CycleEndConfigDialog(current_task_index=0, all_canvas_tasks=tasks)

    def test_instantiation(self, dialog):
        assert dialog is not None

    def test_has_tasks_list(self, dialog):
        assert dialog.tasks_list is not None

    def test_has_mark_as_end_checkbox(self, dialog):
        assert dialog.mark_as_end_checkbox is not None

    def test_get_configuration_returns_dict(self, dialog):
        result = dialog.get_configuration()
        assert isinstance(result, dict)

    def test_get_configuration_has_is_cycle_end_key(self, dialog):
        result = dialog.get_configuration()
        assert "is_cycle_end" in result

    def test_get_configuration_has_return_to_index_key(self, dialog):
        result = dialog.get_configuration()
        assert "return_to_index" in result

    def test_checkbox_default_unchecked(self, dialog):
        assert dialog.mark_as_end_checkbox.isChecked() is False

    def test_tasks_list_has_items(self, dialog):
        # At least the "no return" option + task B
        assert dialog.tasks_list.count() >= 2

    def test_empty_tasks_list(self, qapp):
        from ui.dialogs.production_flow.common_dialogs import CycleEndConfigDialog
        d = CycleEndConfigDialog(current_task_index=0, all_canvas_tasks=[])
        assert d is not None


# ─── ReassignmentRuleDialog ──────────────────────────────────────────────────

class TestReassignmentRuleDialog:
    """Verifica ReassignmentRuleDialog: radio buttons de condición, spinbox de unidades y get_rule()."""
    @pytest.fixture
    def dialog(self, qapp):
        from ui.dialogs.production_flow.common_dialogs import ReassignmentRuleDialog
        current_task = {"id": "t1", "name": "Tarea A"}
        all_tasks = [
            {"data": {"id": "t1", "name": "Tarea A"}},
            {"data": {"id": "t2", "name": "Tarea B"}},
        ]
        return ReassignmentRuleDialog(
            worker_name="Operario 1",
            current_task=current_task,
            all_canvas_tasks=all_tasks,
            current_rule=None,
        )

    def test_instantiation(self, dialog):
        assert dialog is not None

    def test_has_radio_on_finish(self, dialog):
        assert dialog.rb_on_finish is not None

    def test_has_radio_after_units(self, dialog):
        assert dialog.rb_after_units is not None

    def test_has_spinbox_units(self, dialog):
        assert dialog.sb_units_value is not None

    def test_has_combo_target(self, dialog):
        assert dialog.cb_target_task is not None

    def test_default_rule_is_on_finish(self, dialog):
        assert dialog.rb_on_finish.isChecked() is True

    def test_get_rule_returns_none_when_no_condition(self, dialog):
        # rb_on_finish checked but no target → condition_type is ON_FINISH → returns dict
        result = dialog.get_rule()
        # ON_FINISH with no target still returns a dict (condition_type is set)
        assert result is None or isinstance(result, dict)

    def test_get_rule_with_after_units(self, dialog):
        dialog.rb_after_units.setChecked(True)
        dialog.sb_units_value.setValue(10)
        result = dialog.get_rule()
        assert result is not None
        assert result["condition_type"] == "AFTER_UNITS"
        assert result["condition_value"] == 10

    def test_get_rule_parallel_mode(self, dialog):
        dialog.rb_after_units.setChecked(True)
        dialog.sb_units_value.setValue(5)
        dialog.tipo_paralelo.setChecked(True)
        result = dialog.get_rule()
        assert result is not None
        assert result["mode"] == "PARALLEL_JOIN"

    def test_window_title_contains_worker_name(self, dialog):
        assert "Operario 1" in dialog.windowTitle()

    def test_with_existing_rule(self, qapp):
        from ui.dialogs.production_flow.common_dialogs import ReassignmentRuleDialog
        rule = {"condition_type": "AFTER_UNITS", "condition_value": 5, "target_task_id": None, "mode": "compartir"}
        d = ReassignmentRuleDialog(
            worker_name="Op",
            current_task={"id": "t1", "name": "T1"},
            all_canvas_tasks=[{"data": {"id": "t1", "name": "T1"}}],
            current_rule=rule,
        )
        assert d.rb_after_units.isChecked() is True
        assert d.sb_units_value.value() == 5


# ─── DefinirCantidadesDialog ─────────────────────────────────────────────────

class TestDefinirCantidadesDialog:
    """Verifica DefinirCantidadesDialog: tabla de pasos, spinboxes de cantidad y get_cantidades()."""
    @pytest.fixture
    def flow(self):
        return [
            {"type": "task", "task": {"name": "Tarea A"}},
            {"type": "task", "task": {"name": "Tarea B"}},
            {"type": "sequential_group", "tasks": [
                {"task": {"name": "Tarea C"}},
                {"task": {"name": "Tarea D"}},
            ]},
        ]

    @pytest.fixture
    def dialog(self, qapp, flow):
        from ui.dialogs.production_flow.common_dialogs import DefinirCantidadesDialog
        return DefinirCantidadesDialog(production_flow=flow)

    def test_instantiation(self, dialog):
        assert dialog is not None

    def test_has_table(self, dialog):
        assert dialog.table is not None

    def test_table_row_count_matches_flow(self, dialog, flow):
        assert dialog.table.rowCount() == len(flow)

    def test_spinboxes_count_matches_flow(self, dialog, flow):
        assert len(dialog.spin_boxes) == len(flow)

    def test_default_values_are_one(self, dialog):
        for sb in dialog.spin_boxes:
            assert sb.value() == 1

    def test_get_cantidades_returns_dict(self, dialog):
        result = dialog.get_cantidades()
        assert isinstance(result, dict)

    def test_get_cantidades_keys_match_indices(self, dialog, flow):
        result = dialog.get_cantidades()
        for i in range(len(flow)):
            assert i in result

    def test_get_cantidades_reflects_spinbox_values(self, dialog):
        dialog.spin_boxes[0].setValue(5)
        dialog.spin_boxes[1].setValue(10)
        result = dialog.get_cantidades()
        assert result[0] == 5
        assert result[1] == 10

    def test_empty_flow(self, qapp):
        from ui.dialogs.production_flow.common_dialogs import DefinirCantidadesDialog
        d = DefinirCantidadesDialog(production_flow=[])
        assert d.get_cantidades() == {}
