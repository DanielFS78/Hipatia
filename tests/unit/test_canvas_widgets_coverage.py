"""
Nombre del Módulo: test_canvas_widgets_coverage
Descripcion: Tests unitarios para el canvas de flujo de producción
             (``FlowCardWidget`` y ``ProductionFlowCanvas`` en ``ui/widgets/production_flow``).
             Verifica inicialización, snap-to-grid, señales, gestión de conexiones y ciclo de vida.

Decisión de mocking: Los widgets heredan de QWidget/QLabel (PyQt6) —
MagicMock() inevitable para dependencias visuales en conexiones.
``ProductionFlowCanvas`` es autónomo y no requiere mocks externos.
"""
import pytest
from unittest.mock import MagicMock

pytestmark = pytest.mark.unit


def make_task_data(name="Tarea A", task_id="t1", duration=5.0):
    return {"id": task_id, "name": name, "duration": duration}


# ─── FlowCardWidget ────────────────────────────────────────────────────────────


class TestFlowCanvasCardWidget:
    """Verifica FlowCardWidget: set_selected, set_highlighted, update_workers y snap-to-grid."""

    @pytest.fixture
    def card(self, qapp):
        from ui.widgets.production_flow.flow_card_widget import FlowCardWidget

        return FlowCardWidget(make_task_data())

    def test_instantiation(self, card):
        assert card is not None

    def test_task_data_stored(self, card):
        assert card.task_data["id"] == "t1"

    def test_text_contains_name(self, card):
        assert "Tarea A" in card.text()

    def test_fixed_size(self, card):
        assert card.width() == 180
        assert card.height() == 60

    def test_dragging_initially_false(self, card):
        assert card.dragging is False

    def test_set_selected_true(self, card):
        card.set_selected(True)
        assert "highlight" in card.styleSheet()

    def test_set_selected_false(self, card):
        card.set_selected(False)
        assert "#007bff" in card.styleSheet()

    def test_set_highlighted_true(self, card):
        card.set_highlighted(True, "#ff0000")
        assert "#ff0000" in card.styleSheet()

    def test_set_highlighted_false(self, card):
        card.set_highlighted(False)
        assert "#007bff" in card.styleSheet()

    def test_update_workers_with_names(self, card):
        card.update_workers(["Ana", "Luis"])
        assert "Ana" in card.toolTip() or "Luis" in card.toolTip()

    def test_update_workers_empty(self, card):
        card.update_workers([])
        assert "Sin trabajadores" in card.toolTip()

    def test_snap_to_grid(self, card):
        card.move(13, 27)
        card._snap_to_grid()
        assert card.x() % 20 == 0
        assert card.y() % 20 == 0


# ─── ProductionFlowCanvas ────────────────────────────────────────────────────


class TestProductionFlowCanvas:
    """Verifica ProductionFlowCanvas: add_task_widget, clear_widgets, set_connections y señales."""

    @pytest.fixture
    def canvas(self, qapp):
        from ui.widgets.production_flow.flow_canvas import ProductionFlowCanvas

        return ProductionFlowCanvas()

    def test_instantiation(self, canvas):
        assert canvas is not None

    def test_connections_initially_empty(self, canvas):
        assert canvas.connections == []

    def test_task_widgets_initially_empty(self, canvas):
        assert canvas.task_widgets == []

    def test_accepts_drops(self, canvas):
        assert canvas.acceptDrops() is True

    def test_set_connections_stores_list(self, canvas):
        canvas.set_connections(
            [{"start": MagicMock(spec=[]), "end": MagicMock(spec=[]), "type": "normal"}]
        )
        assert len(canvas.connections) == 1

    def test_set_connections_empty(self, canvas):
        canvas.set_connections([])
        assert canvas.connections == []

    def test_add_task_widget(self, qapp, canvas):
        from ui.widgets.production_flow.flow_card_widget import FlowCardWidget

        card = FlowCardWidget(make_task_data())
        canvas.add_task_widget(card)
        assert len(canvas.task_widgets) == 1

    def test_clear_widgets(self, qapp, canvas):
        from ui.widgets.production_flow.flow_card_widget import FlowCardWidget

        card = FlowCardWidget(make_task_data())
        canvas.add_task_widget(card)
        canvas.clear_widgets()
        assert len(canvas.task_widgets) == 0
        assert canvas.connections == []

    def test_signals_exist(self, canvas):
        assert hasattr(canvas, "taskDropped")
        assert hasattr(canvas, "cardSelected")
        assert hasattr(canvas, "cardMoved")
        assert hasattr(canvas, "backgroundClicked")
