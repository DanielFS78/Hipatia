"""
Nombre del Módulo: test_define_flow_dialog_edge
Descripcion: Tests unitarios para DefineProductionFlowDialog, el diálogo principal
             de definición de pilas de producción. Verifica inicialización con y sin
             flujo existente, obtención del flujo, guardado, reset de formulario y
             comportamiento sin controlador.

Decisión de mocking: DefineProductionFlowDialog tiene dependencias en DefineControlPanel
(QWidget), DefineFlowPresenter (Python puro), AppController y ScheduleConfig.
DefineControlPanel se sustituye por FakeControlPanel(QWidget) — una subclase real de
QWidget con señales implementadas como objetos FakeSignal — porque addWidget() de Qt
rechaza MagicMock() en tiempo de ejecución. Las señales PyQt6 no se pueden instanciar
fuera de QObject, por lo que FakeSignal implementa connect/disconnect/emit como métodos
vacíos. DefineFlowPresenter se mockea con MagicMock() estándar al ser Python puro.
"""
import pytest
from unittest.mock import MagicMock, patch, PropertyMock

pytestmark = pytest.mark.unit


def make_schedule_config():
    cfg = MagicMock(spec=['start_time', 'end_time'])
    cfg.start_time = "08:00"
    cfg.end_time = "17:00"
    return cfg


def make_task(name="Tarea A", task_id="t1", duration=5.0, product_code="P1"):
    return {
        "id": task_id,
        "name": name,
        "duration": duration,
        "product_code": product_code,
    }


@pytest.fixture
def mock_control_panel(qapp):
    """Mock de DefineControlPanel — debe ser QWidget para addWidget()."""
    from PyQt6.QtWidgets import QWidget
    from PyQt6.QtCore import pyqtSignal, QObject

    class FakeSignal:
        def connect(self, *a, **kw): pass
        def disconnect(self, *a, **kw): pass
        def emit(self, *a, **kw): pass

    class FakeControlPanel(QWidget):
        def __init__(self, *a, **kw):
            super().__init__()
            self.task_selected_signal = FakeSignal()
            self.add_update_clicked = FakeSignal()
            self.start_condition_changed = FakeSignal()
            self.machine_changed_signal = FakeSignal()
            self.cancel_edit_clicked = FakeSignal()
            self.machine_menu = MagicMock()
            self.machine_menu.currentData = MagicMock(return_value=None)
            self.machine_menu.blockSignals = MagicMock()
            self.machine_menu.clear = MagicMock()
            self.machine_menu.addItem = MagicMock()
            self.machine_menu.setEnabled = MagicMock()
            self.machine_menu.findData = MagicMock(return_value=-1)
            self.machine_menu.setCurrentIndex = MagicMock()
            self.machine_menu.setProperty = MagicMock()
            self.prep_steps_scroll = MagicMock()
            self.prep_steps_label = MagicMock()
            # _toggle_start_condition
            self.dependency_radio = MagicMock(spec=['isChecked', 'setEnabled', 'setChecked'])
            self.start_date_radio = MagicMock(spec=['isChecked', 'setEnabled', 'setChecked'])
            self.start_date_radio.isChecked = MagicMock(return_value=True)
            self.worker_dependency_radio = MagicMock(spec=['isChecked', 'setEnabled', 'setChecked'])
            self.worker_dependency_radio.isChecked.return_value = False
            self.dependency_radio.isChecked.return_value = False
            self.start_date_entry = MagicMock()
            self.previous_task_menu = MagicMock()
            self.previous_task_menu.clear = MagicMock()
            self.previous_task_menu.addItem = MagicMock()
            self.min_predecessor_units_entry = MagicMock()
            self.worker_dependency_menu = MagicMock()
            # _on_task_selected
            self.resource_layout = MagicMock()
        def clear_prep_steps(self): pass
        def clear_form(self): pass
        def get_selected_task(self): return None
        def get_form_data(self): return {"machine_id": None}
        def set_editing_mode(self, *a, **kw): pass
        def populate_form(self, *a, **kw): pass

    with patch("ui.dialogs.production_flow.define_flow_dialog.DefineControlPanel", FakeControlPanel):
        yield FakeControlPanel


@pytest.fixture
def mock_presenter():
    with patch("ui.dialogs.production_flow.define_flow_dialog.DefineFlowPresenter", autospec=True) as MockPres:
        instance = MockPres.return_value
        instance.prepare_task_data.return_value = {}
        instance.get_production_flow.return_value = []
        instance.set_production_flow.return_value = None
        instance.get_prep_steps_for_machine.return_value = []
        yield MockPres


@pytest.fixture
def dialog(qapp, mock_control_panel, mock_presenter):
    from ui.dialogs.production_flow.define_flow_dialog import DefineProductionFlowDialog
    ctrl = MagicMock(spec=['model'])
    ctrl.model = MagicMock(spec=[''])
    tasks = [make_task("Tarea A", "t1"), make_task("Tarea B", "t2")]
    workers = ["Ana", "Luis"]
    return DefineProductionFlowDialog(
        tasks_data=tasks,
        workers=workers,
        units=10,
        hub=ctrl,
        schedule_config=make_schedule_config(),
    )


class TestDefineProductionFlowDialogInit:
    """Verifica la inicialización del diálogo: título, presenter, control_panel y estado por defecto."""
    def test_instantiation(self, dialog):
        assert dialog is not None
        class ConfigDTO: pass
        assert not isinstance(dialog.schedule_config, ConfigDTO)

    def test_window_title(self, dialog):
        assert "Pila" in dialog.windowTitle() or "Producción" in dialog.windowTitle()

    def test_has_presenter(self, dialog):
        assert dialog.presenter is not None

    def test_has_control_panel(self, dialog):
        assert dialog.control_panel is not None

    def test_has_save_flow_button(self, dialog):
        assert dialog.save_flow_button is not None

    def test_has_group_steps_button(self, dialog):
        assert dialog.group_steps_button is not None

    def test_workers_sorted(self, dialog):
        assert dialog.workers == sorted(dialog.workers)

    def test_units_stored(self, dialog):
        assert dialog.units == 10

    def test_editing_index_initially_none(self, dialog):
        assert dialog.editing_index is None

    def test_flow_item_widgets_initially_empty(self, dialog):
        assert dialog.flow_item_widgets == []


class TestDefineProductionFlowDialogWithExistingFlow:
    """Verifica que al pasar existing_flow el título cambia a 'Editar' y el presenter recibe el flujo."""
    def test_instantiation_with_existing_flow(self, qapp, mock_control_panel, mock_presenter):
        from ui.dialogs.production_flow.define_flow_dialog import DefineProductionFlowDialog
        ctrl = MagicMock(spec=['model'])
        ctrl.model = MagicMock(spec=[''])
        existing = [{"type": "task", "task": make_task()}]
        d = DefineProductionFlowDialog(
            tasks_data=[make_task()],
            workers=["Ana"],
            units=5,
            hub=ctrl,
            schedule_config=make_schedule_config(),
            existing_flow=existing,
        )
        assert d is not None

    def test_title_changes_with_existing_flow(self, qapp, mock_control_panel, mock_presenter):
        from ui.dialogs.production_flow.define_flow_dialog import DefineProductionFlowDialog
        ctrl = MagicMock(spec=['model'])
        ctrl.model = MagicMock(spec=[''])
        existing = [{"type": "task", "task": make_task()}]
        d = DefineProductionFlowDialog(
            tasks_data=[make_task()],
            workers=[],
            units=1,
            hub=ctrl,
            schedule_config=make_schedule_config(),
            existing_flow=existing,
        )
        assert "Editar" in d.windowTitle()


class TestDefineProductionFlowDialogGetFlow:
    """Verifica que get_production_flow() delega al presenter y devuelve su resultado."""
    def test_get_production_flow_returns_list(self, dialog):
        result = dialog.get_production_flow()
        assert isinstance(result, list)

    def test_get_production_flow_delegates_to_presenter(self, dialog):
        dialog.presenter.get_production_flow = MagicMock(return_value=[{"step": 1}])
        result = dialog.get_production_flow()
        assert dialog.presenter.get_production_flow.call_count == 1
        assert result == [{"step": 1}]


class TestDefineProductionFlowDialogOnSaveFlow:
    """Verifica _on_save_flow(): warning con flujo vacío y apertura de SavePilaDialog con pasos."""
    def test_on_save_flow_empty_shows_warning(self, dialog):
        dialog.presenter.get_production_flow = MagicMock(return_value=[])
        with patch("PyQt6.QtWidgets.QMessageBox.warning") as mock_warn:
            dialog._on_save_flow()
            assert mock_warn.call_count == 1

    def test_on_save_flow_with_steps_opens_save_dialog(self, dialog):
        dialog.presenter.get_production_flow = MagicMock(return_value=[{"step": 1}])
        with patch("ui.dialogs.production_flow.define_flow_dialog.SavePilaDialog") as MockSave:
            mock_save_instance = MagicMock()
            mock_save_instance.exec.return_value = 0  # Rejected
            MockSave.return_value = mock_save_instance
            dialog._on_save_flow()
            assert MockSave.call_count == 1


class TestDefineProductionFlowDialogResetForm:
    """Verifica que _reset_form() limpia editing_index correctamente."""
    def test_reset_form_clears_editing_index(self, dialog):
        dialog.editing_index = 2
        dialog._reset_form()
        assert dialog.editing_index is None


class TestDefineProductionFlowDialogNoHub:
    """Verifica que el diálogo se inicializa sin errores cuando hub=None."""
    def test_instantiation_without_hub(self, qapp, mock_control_panel, mock_presenter):
        from ui.dialogs.production_flow.define_flow_dialog import DefineProductionFlowDialog
        d = DefineProductionFlowDialog(
            tasks_data=[],
            workers=[],
            units=1,
            hub=None,
            schedule_config=make_schedule_config(),
        )
        assert d is not None
