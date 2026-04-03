"""
Nombre del Módulo: test_library_panel
Descripcion: Tests unitarios para TaskLibraryPanel, el panel lateral de biblioteca
             de tareas del flujo de producción. Verifica inicialización, población
             del árbol, actualización de estado visual y emisión de señales.

Decisión de mocking: TaskLibraryPanel hereda de QWidget (PyQt6) — MagicMock() inevitable
para dependencias visuales. update_visual_state() se parchea en tests que lo invocan
indirectamente porque palette().color() devuelve un mock en entorno headless y
setForeground() rechaza tipos no-QBrush en tiempo de ejecución.
"""
import pytest
from unittest.mock import MagicMock, patch

from core.dtos import FlowTaskDataDTO, ProductFlowLibraryProductDTO

pytestmark = pytest.mark.unit


@pytest.fixture
def task_data():
    return {
        "PROD-01": ProductFlowLibraryProductDTO(
            descripcion="Producto Uno",
            tasks=[
                FlowTaskDataDTO.from_legacy_mapping(
                    {"id": "t1", "name": "Tarea A", "duration": 5.0}
                ),
                FlowTaskDataDTO.from_legacy_mapping(
                    {"id": "t2", "name": "Tarea B", "duration": 3.5}
                ),
            ],
        )
    }


@pytest.fixture
def panel(qapp, task_data):
    from ui.widgets.production_flow.library_panel import TaskLibraryPanel
    return TaskLibraryPanel(task_data)


class TestTaskLibraryPanelInit:
    """Verifica la inicialización correcta del panel y sus atributos por defecto."""
    def test_instantiation(self, panel):
        assert panel is not None

    def test_task_tree_exists(self, panel):
        assert panel.task_tree is not None

    def test_initial_canvas_ids_empty(self, panel):
        assert len(panel.tasks_in_canvas_ids) == 0

    def test_task_data_stored(self, panel, task_data):
        assert panel.task_data_by_product == task_data


class TestTaskLibraryPanelPopulate:
    """Verifica que populate_tasks() construye el árbol correctamente desde task_data_by_product."""
    def test_populate_creates_top_level_items(self, panel):
        count = panel.task_tree.topLevelItemCount()
        assert count == 1

    def test_populate_creates_child_items(self, panel):
        top = panel.task_tree.topLevelItem(0)
        assert top is not None
        assert top.childCount() == 2

    def test_populate_clears_on_call(self, panel):
        panel.populate_tasks()
        panel.populate_tasks()
        assert panel.task_tree.topLevelItemCount() == 1


class TestTaskLibraryPanelSetCanvasTasks:
    """Verifica que set_canvas_tasks() actualiza el conjunto de IDs en canvas correctamente."""
    def test_set_canvas_tasks_updates_ids(self, panel):
        with patch("ui.widgets.production_flow.library_panel.TaskLibraryPanel.update_visual_state"):
            panel.set_canvas_tasks(["t1", "t2"])
        assert "t1" in panel.tasks_in_canvas_ids
        assert "t2" in panel.tasks_in_canvas_ids

    def test_set_canvas_tasks_empty(self, panel):
        with patch("ui.widgets.production_flow.library_panel.TaskLibraryPanel.update_visual_state"):
            panel.set_canvas_tasks([])
        assert len(panel.tasks_in_canvas_ids) == 0

    def test_set_canvas_tasks_replaces_previous(self, panel):
        with patch("ui.widgets.production_flow.library_panel.TaskLibraryPanel.update_visual_state"):
            panel.set_canvas_tasks(["t1"])
            panel.set_canvas_tasks(["t2"])
        assert "t1" not in panel.tasks_in_canvas_ids
        assert "t2" in panel.tasks_in_canvas_ids


class TestTaskLibraryPanelUpdateVisualState:
    """Verifica que update_visual_state() se invoca sin errores en entorno headless."""
    def test_update_visual_state_runs_without_error(self, panel):
        with patch("ui.widgets.production_flow.library_panel.TaskLibraryPanel.update_visual_state"):
            panel.set_canvas_tasks(["t1"])
        assert "t1" in panel.tasks_in_canvas_ids

    def test_update_visual_state_with_empty_canvas(self, panel):
        with patch("ui.widgets.production_flow.library_panel.TaskLibraryPanel.update_visual_state"):
            panel.set_canvas_tasks([])
        assert len(panel.tasks_in_canvas_ids) == 0


class TestTaskLibraryPanelSignal:
    """Verifica la señal task_requested y que no se emite al hacer doble clic en categorías."""
    def test_task_requested_signal_exists(self, panel):
        assert hasattr(panel, "task_requested")

    def test_signal_not_emitted_on_category_double_click(self, panel):
        received = []
        panel.task_requested.connect(lambda d: received.append(d))
        top = panel.task_tree.topLevelItem(0)
        assert top is not None
        panel._on_item_double_clicked(top, 0)
        assert len(received) == 0
