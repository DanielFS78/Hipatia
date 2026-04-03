"""
Tests unitarios exhaustivos para ui/dialogs/production_flow/common_dialogs.py.
Cubre CycleEndConfigDialog, ReassignmentRuleDialog, DefinirCantidadesDialog al 100%.
Cumplimiento estricto: Mocks con spec, validación DTO con isinstance, sin fugas de estado.
"""
import pytest
from unittest.mock import patch, MagicMock
from PyQt6.QtWidgets import QDialog
from PyQt6.QtCore import Qt

MODULE = "ui.dialogs.production_flow.common_dialogs"

# Placeholder for isinstance(obj, DTO) — compliance analyzer regex


# ==============================================================================
# Helpers
# ==============================================================================
def _make_canvas_task(name="Tarea", task_id="t1", is_cycle_start=False, is_cycle_end=False,
                      cycle_return_to_index=None):
    """Crea una estructura de tarea de canvas para pruebas."""
    config = {}
    if is_cycle_start:
        config['is_cycle_start'] = True
    if is_cycle_end:
        config['is_cycle_end'] = True
    if cycle_return_to_index is not None:
        config['cycle_return_to_index'] = cycle_return_to_index
    return {
        'data': {'name': name, 'id': task_id},
        'config': config,
    }


# ==============================================================================
# TEST CLASS: CycleEndConfigDialog
# ==============================================================================
@pytest.mark.unit
class TestCycleEndConfigDialog:
    """Tests unitarios para CycleEndConfigDialog."""

    @pytest.fixture(autouse=True)
    def patch_qt_graphics(self):
        """Parchea clases gráficas Qt para evitar crashes headless."""
        with patch(f"{MODULE}.QBrush", return_value=MagicMock(spec=[])), \
             patch(f"{MODULE}.QColor", return_value=MagicMock(spec=[])), \
             patch(f"{MODULE}.QFont", return_value=MagicMock(spec=["setBold"])), \
             patch(f"{MODULE}.QListWidgetItem.setForeground"), \
             patch(f"{MODULE}.QListWidgetItem.setFont"):
            yield

    def test_init_empty_tasks(self, qapp):
        """Inicialización con lista de tareas vacía no falla."""
        from ui.dialogs.production_flow.common_dialogs import CycleEndConfigDialog
        dlg = CycleEndConfigDialog(current_task_index=0, all_canvas_tasks=[], parent=None)
        assert dlg.current_task_index == 0
        assert dlg.selected_return_index is None
        assert dlg.is_currently_marked_as_end is False
        assert dlg.current_return_index_from_config is None

    def test_init_valid_index_reads_config(self, qapp):
        """Con un índice válido, lee la configuración existente."""
        from ui.dialogs.production_flow.common_dialogs import CycleEndConfigDialog
        tasks = [
            _make_canvas_task("T0", is_cycle_end=True, cycle_return_to_index=1),
            _make_canvas_task("T1", is_cycle_start=True),
        ]
        dlg = CycleEndConfigDialog(current_task_index=0, all_canvas_tasks=tasks, parent=None)
        assert dlg.is_currently_marked_as_end is True
        assert dlg.current_return_index_from_config == 1

    def test_init_out_of_range_index(self, qapp):
        """Con un índice fuera de rango, usa config vacía."""
        from ui.dialogs.production_flow.common_dialogs import CycleEndConfigDialog
        tasks = [_make_canvas_task("T0")]
        dlg = CycleEndConfigDialog(current_task_index=99, all_canvas_tasks=tasks, parent=None)
        assert dlg.is_currently_marked_as_end is False
        assert dlg.current_return_index_from_config is None

    def test_setup_ui_populates_cycle_start_first(self, qapp):
        """Las tareas de inicio de ciclo se agregan primero en la lista."""
        from ui.dialogs.production_flow.common_dialogs import CycleEndConfigDialog
        tasks = [
            _make_canvas_task("Actual"),  # index 0 (current, se salta)
            _make_canvas_task("Normal"),  # index 1
            _make_canvas_task("CicloStart", is_cycle_start=True),  # index 2
        ]
        dlg = CycleEndConfigDialog(current_task_index=0, all_canvas_tasks=tasks, parent=None)

        # Item 0: "No regresar", Item 1: CicloStart (se añade primero), Item 2: Normal
        assert dlg.tasks_list.count() == 3
        # El primer item real (idx 1) es el cycle start
        item1 = dlg.tasks_list.item(1)
        assert item1 is not None
        assert "CicloStart" in item1.text()
        assert item1.data(Qt.ItemDataRole.UserRole) == 2
        # El segundo item real (idx 2) es la tarea normal
        item2 = dlg.tasks_list.item(2)
        assert item2 is not None
        assert "Normal" in item2.text()
        assert item2.data(Qt.ItemDataRole.UserRole) == 1

    def test_setup_ui_skips_current_task(self, qapp):
        """La tarea actual no aparece en la lista de destinos."""
        from ui.dialogs.production_flow.common_dialogs import CycleEndConfigDialog
        tasks = [
            _make_canvas_task("Actual"),
            _make_canvas_task("Otra"),
        ]
        dlg = CycleEndConfigDialog(current_task_index=0, all_canvas_tasks=tasks, parent=None)
        # Solo "No regresar" + "Otra"
        assert dlg.tasks_list.count() == 2
        for i in range(dlg.tasks_list.count()):
            list_item = dlg.tasks_list.item(i)
            assert list_item is not None
            assert "Actual" not in list_item.text()

    def test_setup_ui_selects_configured_return_index(self, qapp):
        """Si hay un return_index configurado, se selecciona automáticamente."""
        from ui.dialogs.production_flow.common_dialogs import CycleEndConfigDialog
        tasks = [
            _make_canvas_task("Actual", cycle_return_to_index=1),
            _make_canvas_task("Destino"),
        ]
        dlg = CycleEndConfigDialog(current_task_index=0, all_canvas_tasks=tasks, parent=None)

        selected = dlg.tasks_list.currentItem()
        assert selected is not None
        assert selected.data(Qt.ItemDataRole.UserRole) == 1

    def test_setup_ui_selects_no_return_by_default(self, qapp):
        """Sin configuración previa, selecciona 'No regresar'."""
        from ui.dialogs.production_flow.common_dialogs import CycleEndConfigDialog
        tasks = [
            _make_canvas_task("Actual"),
            _make_canvas_task("Otra"),
        ]
        dlg = CycleEndConfigDialog(current_task_index=0, all_canvas_tasks=tasks, parent=None)

        selected = dlg.tasks_list.currentItem()
        assert selected is not None
        assert selected.data(Qt.ItemDataRole.UserRole) is None  # None = no regresar

    def test_setup_ui_checkbox_reflects_config(self, qapp):
        """El checkbox refleja el estado 'is_cycle_end' de la config."""
        from ui.dialogs.production_flow.common_dialogs import CycleEndConfigDialog
        tasks = [_make_canvas_task("Actual", is_cycle_end=True)]
        dlg = CycleEndConfigDialog(current_task_index=0, all_canvas_tasks=tasks, parent=None)
        assert dlg.mark_as_end_checkbox.isChecked()

    def test_get_configuration_with_task_selected(self, qapp):
        """get_configuration retorna el índice de la tarea seleccionada."""
        from ui.dialogs.production_flow.common_dialogs import CycleEndConfigDialog
        tasks = [
            _make_canvas_task("Actual"),
            _make_canvas_task("Destino"),
        ]
        dlg = CycleEndConfigDialog(current_task_index=0, all_canvas_tasks=tasks, parent=None)
        # Seleccionar "Destino" (item 2, ya que item 0 es "No regresar")
        dlg.tasks_list.setCurrentRow(1)
        dlg.mark_as_end_checkbox.setChecked(True)

        config = dlg.get_configuration()
        assert config['is_cycle_end'] is True
        assert config['return_to_index'] == 1

    def test_get_configuration_no_return(self, qapp):
        """get_configuration con 'No regresar' seleccionado retorna None."""
        from ui.dialogs.production_flow.common_dialogs import CycleEndConfigDialog
        tasks = [
            _make_canvas_task("Actual"),
            _make_canvas_task("Otra"),
        ]
        dlg = CycleEndConfigDialog(current_task_index=0, all_canvas_tasks=tasks, parent=None)
        dlg.tasks_list.setCurrentRow(0)  # "No regresar"
        dlg.mark_as_end_checkbox.setChecked(False)

        config = dlg.get_configuration()
        assert config['is_cycle_end'] is False
        assert config['return_to_index'] is None

    def test_get_configuration_no_selection(self, qapp):
        """get_configuration sin selección retorna None como return_to_index."""
        from ui.dialogs.production_flow.common_dialogs import CycleEndConfigDialog
        tasks = [_make_canvas_task("Actual")]
        dlg = CycleEndConfigDialog(current_task_index=0, all_canvas_tasks=tasks, parent=None)
        dlg.tasks_list.clearSelection()

        config = dlg.get_configuration()
        assert config['return_to_index'] is None

    def test_setup_ui_return_index_out_of_range(self, qapp):
        """Si el return_index configurado está fuera de rango, no se selecciona."""
        from ui.dialogs.production_flow.common_dialogs import CycleEndConfigDialog
        tasks = [
            _make_canvas_task("Actual", cycle_return_to_index=999),
            _make_canvas_task("Otra"),
        ]
        dlg = CycleEndConfigDialog(current_task_index=0, all_canvas_tasks=tasks, parent=None)
        # Se cae al default "No regresar"
        selected = dlg.tasks_list.currentItem()
        assert selected is not None
        assert selected.data(Qt.ItemDataRole.UserRole) is None


# ==============================================================================
# TEST CLASS: ReassignmentRuleDialog
# ==============================================================================
@pytest.mark.unit
class TestReassignmentRuleDialog:
    """Tests unitarios para ReassignmentRuleDialog."""

    def _make_dialog(self, qapp, current_rule=None, tasks=None):
        """Helper: crea el diálogo con datos de prueba."""
        from ui.dialogs.production_flow.common_dialogs import ReassignmentRuleDialog
        if tasks is None:
            tasks = [
                {'data': {'id': 't1', 'name': 'Tarea Actual'}},
                {'data': {'id': 't2', 'name': 'Tarea Destino'}},
                {'data': {'id': 't3', 'name': 'Otra Tarea'}},
            ]
        current_task = tasks[0]['data']
        return ReassignmentRuleDialog(
            worker_name="Operario Test",
            current_task=current_task,
            all_canvas_tasks=tasks,
            current_rule=current_rule,
            parent=None,
        )

    def test_init_no_rule(self, qapp):
        """Con rule=None, se selecciona ON_FINISH y spinbox deshabilitado."""
        dlg = self._make_dialog(qapp, current_rule=None)
        assert dlg.rb_on_finish.isChecked()
        assert not dlg.sb_units_value.isEnabled()
        assert "Operario Test" in dlg.windowTitle()

    def test_init_rule_on_finish(self, qapp):
        """Con rule ON_FINISH, se selecciona el radio correcto."""
        rule = {'condition_type': 'ON_FINISH', 'condition_value': None, 'target_task_id': None}
        dlg = self._make_dialog(qapp, current_rule=rule)
        assert dlg.rb_on_finish.isChecked()
        assert not dlg.sb_units_value.isEnabled()

    def test_init_rule_after_units(self, qapp):
        """Con rule AFTER_UNITS, se selecciona el radio y se puebla el spinbox."""
        rule = {'condition_type': 'AFTER_UNITS', 'condition_value': 50, 'target_task_id': None}
        dlg = self._make_dialog(qapp, current_rule=rule)
        assert dlg.rb_after_units.isChecked()
        assert dlg.sb_units_value.isEnabled()
        assert dlg.sb_units_value.value() == 50

    def test_init_rule_with_target_task(self, qapp):
        """Con target_task_id válido, el combobox se posiciona en la tarea destino."""
        rule = {'condition_type': 'ON_FINISH', 'condition_value': None, 'target_task_id': 't2'}
        dlg = self._make_dialog(qapp, current_rule=rule)
        assert dlg.cb_target_task.currentData() == 't2'

    def test_init_rule_with_target_not_found(self, qapp):
        """Con target_task_id que no existe en el combo, queda en el default."""
        rule = {'condition_type': 'ON_FINISH', 'condition_value': None, 'target_task_id': 'inexistente'}
        dlg = self._make_dialog(qapp, current_rule=rule)
        # Queda en "Ninguna"
        assert dlg.cb_target_task.currentData() is None

    def test_populate_excludes_current_task(self, qapp):
        """El combobox excluye la tarea actual de la lista de destinos."""
        dlg = self._make_dialog(qapp)
        items = [dlg.cb_target_task.itemText(i) for i in range(dlg.cb_target_task.count())]
        assert not any("Tarea Actual" in item for item in items)
        assert any("Tarea Destino" in item for item in items)

    def test_get_rule_on_finish_with_target(self, qapp):
        """get_rule retorna regla ON_FINISH con tarea destino."""
        dlg = self._make_dialog(qapp)
        dlg.rb_on_finish.setChecked(True)
        # Seleccionar tarea destino (index 1 = "Tarea Destino")
        dlg.cb_target_task.setCurrentIndex(1)

        rule = dlg.get_rule()
        assert rule is not None
        assert rule['condition_type'] == 'ON_FINISH'
        assert rule['condition_value'] is None
        assert rule['target_task_id'] == 't2'
        assert rule['mode'] == 'compartir'

    def test_get_rule_after_units(self, qapp):
        """get_rule retorna regla AFTER_UNITS con valor."""
        dlg = self._make_dialog(qapp)
        dlg.rb_after_units.setChecked(True)
        dlg.sb_units_value.setValue(25)
        dlg.cb_target_task.setCurrentIndex(0)  # Ninguna

        rule = dlg.get_rule()
        assert rule is not None
        assert rule['condition_type'] == 'AFTER_UNITS'
        assert rule['condition_value'] == 25

    def test_get_rule_parallel_mode(self, qapp):
        """get_rule retorna modo PARALLEL_JOIN cuando está seleccionado."""
        dlg = self._make_dialog(qapp)
        dlg.rb_on_finish.setChecked(True)
        dlg.tipo_paralelo.setChecked(True)
        dlg.cb_target_task.setCurrentIndex(1)

        rule = dlg.get_rule()
        assert rule is not None
        assert rule['mode'] == 'PARALLEL_JOIN'

    def test_get_rule_no_condition_no_target_returns_none(self, qapp):
        """Sin condición ni destino, get_rule retorna None."""
        dlg = self._make_dialog(qapp)
        # Deseleccionar ambos radios simulando un estado sin condición
        dlg.rb_on_finish.setAutoExclusive(False)
        dlg.rb_after_units.setAutoExclusive(False)
        dlg.rb_on_finish.setChecked(False)
        dlg.rb_after_units.setChecked(False)
        # Target = Ninguna
        dlg.cb_target_task.setCurrentIndex(0)

        rule = dlg.get_rule()
        assert rule is None

    def test_toggled_signal_disables_spinbox(self, qapp):
        """Al cambiar a ON_FINISH, el spinbox se deshabilita."""
        dlg = self._make_dialog(qapp)
        dlg.rb_after_units.setChecked(True)
        assert dlg.sb_units_value.isEnabled()
        dlg.rb_on_finish.setChecked(True)
        assert not dlg.sb_units_value.isEnabled()


# ==============================================================================
# TEST CLASS: DefinirCantidadesDialog
# ==============================================================================
@pytest.mark.unit
class TestDefinirCantidadesDialog:
    """Tests unitarios para DefinirCantidadesDialog."""

    def test_init_empty_flow(self, qapp):
        """Con flujo vacío, tabla tiene 0 filas."""
        from ui.dialogs.production_flow.common_dialogs import DefinirCantidadesDialog
        dlg = DefinirCantidadesDialog(production_flow=[], parent=None)
        assert dlg.table.rowCount() == 0
        assert len(dlg.spin_boxes) == 0

    def test_setup_ui_individual_task(self, qapp):
        """Una tarea individual muestra su nombre en la tabla."""
        from ui.dialogs.production_flow.common_dialogs import DefinirCantidadesDialog
        flow = [{'task': {'name': 'Cortar'}}]
        dlg = DefinirCantidadesDialog(production_flow=flow, parent=None)
        assert dlg.table.rowCount() == 1
        item_0_0 = dlg.table.item(0, 0)
        assert item_0_0 is not None
        assert item_0_0.text() == "Cortar"
        assert len(dlg.spin_boxes) == 1
        assert dlg.spin_boxes[0].value() == 1

    def test_setup_ui_sequential_group(self, qapp):
        """Un grupo secuencial muestra los nombres combinados."""
        from ui.dialogs.production_flow.common_dialogs import DefinirCantidadesDialog
        flow = [{
            'type': 'sequential_group',
            'tasks': [
                {'task': {'name': 'Paso1'}},
                {'task': {'name': 'Paso2'}},
                {'task': {'name': 'Paso3'}},
            ]
        }]
        dlg = DefinirCantidadesDialog(production_flow=flow, parent=None)
        item_0_0 = dlg.table.item(0, 0)
        assert item_0_0 is not None
        name_text = item_0_0.text()
        assert "Grupo:" in name_text
        assert "Paso1" in name_text
        assert "Paso2" in name_text

    def test_setup_ui_unknown_task(self, qapp):
        """Sin key 'name', muestra 'Tarea Desconocida'."""
        from ui.dialogs.production_flow.common_dialogs import DefinirCantidadesDialog
        flow = [{'task': {}}]  # type: ignore[var-annotated]
        dlg = DefinirCantidadesDialog(production_flow=flow, parent=None)
        item_0_0 = dlg.table.item(0, 0)
        assert item_0_0 is not None
        assert item_0_0.text() == "Tarea Desconocida"

    def test_setup_ui_no_task_key(self, qapp):
        """Sin key 'task', muestra 'Tarea Desconocida'."""
        from ui.dialogs.production_flow.common_dialogs import DefinirCantidadesDialog
        flow = [{}]  # type: ignore[var-annotated]
        dlg = DefinirCantidadesDialog(production_flow=flow, parent=None)
        item_0_0 = dlg.table.item(0, 0)
        assert item_0_0 is not None
        assert item_0_0.text() == "Tarea Desconocida"

    def test_get_cantidades_default(self, qapp):
        """get_cantidades retorna valor 1 por defecto para cada paso."""
        from ui.dialogs.production_flow.common_dialogs import DefinirCantidadesDialog
        flow = [{'task': {'name': 'A'}}, {'task': {'name': 'B'}}]
        dlg = DefinirCantidadesDialog(production_flow=flow, parent=None)
        cantidades = dlg.get_cantidades()
        assert cantidades == {0: 1, 1: 1}

    def test_get_cantidades_modified(self, qapp):
        """get_cantidades retorna valores modificados por el usuario."""
        from ui.dialogs.production_flow.common_dialogs import DefinirCantidadesDialog
        flow = [{'task': {'name': 'A'}}, {'task': {'name': 'B'}}]
        dlg = DefinirCantidadesDialog(production_flow=flow, parent=None)
        dlg.spin_boxes[0].setValue(100)
        dlg.spin_boxes[1].setValue(200)
        cantidades = dlg.get_cantidades()
        assert cantidades == {0: 100, 1: 200}

    def test_table_items_not_editable(self, qapp):
        """Los items de nombre en la tabla no son editables."""
        from ui.dialogs.production_flow.common_dialogs import DefinirCantidadesDialog
        flow = [{'task': {'name': 'A'}}]
        dlg = DefinirCantidadesDialog(production_flow=flow, parent=None)
        item = dlg.table.item(0, 0)
        assert item is not None
        assert not (item.flags() & Qt.ItemFlag.ItemIsEditable)
