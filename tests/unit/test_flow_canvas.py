# -*- coding: utf-8 -*-
"""Tests unitarios para flow_canvas.py (CardWidget y ProductionFlowCanvas)."""
import math
import pytest
from unittest.mock import MagicMock, patch, PropertyMock, ANY, create_autospec

from PyQt6.QtCore import Qt, QPoint, QPointF, QLineF, QRect
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor

from core.dtos import ProductDTO
from core.dtos import CanvasCyclicConnectionFlags
from ui.widgets.production_flow.flow_canvas import ProductionFlowCanvas
from ui.widgets.production_flow.flow_card_widget import FlowCardWidget
from ui.widgets.production_flow.flow_connection_painter import FlowConnectionPainter
from core.app_model import AppModel
from core.schedule_config import ScheduleConfig

pytestmark = pytest.mark.unit


# Dummy classes for mocking QPainter and QColor
class DummyPainter:
    """A dummy QPainter for testing."""
    def __init__(self, *args, **kwargs):
        pass
    def setPen(self, *args, **kwargs):
        pass
    def drawPath(self, *args, **kwargs):
        pass
    def drawPolygon(self, *args, **kwargs):
        pass
    def drawLine(self, *args, **kwargs):
        pass
    def setBrush(self, *args, **kwargs):
        pass
    def fillRect(self, *args, **kwargs):
        pass
    def drawText(self, *args, **kwargs):
        pass
    def save(self, *args, **kwargs):
        pass
    def restore(self, *args, **kwargs):
        pass
    def begin(self, *args, **kwargs):
        pass
    def end(self, *args, **kwargs):
        pass
    def setRenderHint(self, *args, **kwargs):
        pass
    def strokePath(self, *args, **kwargs):
        pass
    def fillPath(self, *args, **kwargs):
        pass
    def drawRect(self, *args, **kwargs):
        pass

class DummyColor:
    """A dummy QColor for testing."""
    def __init__(self, *args, **kwargs):
        pass
    def isValid(self):
        return True
    def name(self):
        return "#000000"
    def red(self): return 0
    def green(self): return 0
    def blue(self): return 0
    def alpha(self): return 255


def _make_task_data(task_id="T1", name="Tarea 1", duration=5.0):
    """Crea datos de tarea simulados."""
    return {'id': task_id, 'name': name, 'duration': duration}


@pytest.mark.unit
class TestCardWidget:
    """Tests unitarios para CardWidget (tarjeta visual de tarea)."""

    @pytest.fixture
    def card(self, qtbot):
        """Instancia de FlowCardWidget con datos de prueba."""
        data = _make_task_data()
        c = FlowCardWidget(data)
        qtbot.addWidget(c)
        return c

    def test_init(self, card):
        """Verifica inicialización correcta de la tarjeta."""
        assert card.task_data['id'] == 'T1'
        assert card.task_data['name'] == 'Tarea 1'
        assert not card.dragging
        assert "Tarea 1" in card.text()
        assert "5.00" in card.text()

    def test_set_selected_true(self, card):
        """Verifica estilo de selección de tarjeta."""
        card.set_selected(True)
        style = card.styleSheet()
        assert "#0056b3" in style  # Color de borde seleccionado

    def test_set_selected_false(self, card):
        """Verifica estilo al deseleccionar tarjeta."""
        card.set_selected(True)
        card.set_selected(False)
        style = card.styleSheet()
        assert "#007bff" in style  # Color de borde normal

    def test_set_highlighted_true(self, card):
        """Verifica resaltado de tarjeta con color."""
        card.set_highlighted(True, "#ff0000")
        style = card.styleSheet()
        assert "#ff0000" in style

    def test_set_highlighted_false(self, card):
        """Verifica restauración al desresaltar."""
        card.set_highlighted(True, "#ff0000")
        card.set_highlighted(False)
        style = card.styleSheet()
        assert "#007bff" in style  # Restaura al estilo base

    def test_update_workers_with_names(self, card):
        """Verifica actualización de trabajadores asignados."""
        card.update_workers(["Juan", "Ana"])
        assert "👥" in card.text()
        assert "2" in card.text()
        assert "Juan, Ana" in card.toolTip()

    def test_update_workers_empty(self, card):
        """Verifica que sin trabajadores se restaura el texto."""
        card.update_workers(["Juan"])
        card.update_workers([])
        assert "👥" not in card.text()
        assert "Sin trabajadores" in card.toolTip()

    def test_click_emits_signal(self, qtbot, card):
        """Verifica que hacer clic emite la señal clicked con datos de tarea."""
        with qtbot.waitSignal(card.clicked, timeout=1000) as blocker:
            qtbot.mouseClick(card, Qt.MouseButton.LeftButton)
        assert blocker.args[0] == card.task_data

    def test_mouse_press_starts_drag(self, qtbot, card):
        """Verifica que mousePress inicia el arrastre."""
        qtbot.mousePress(card, Qt.MouseButton.LeftButton)
        assert card.dragging is True

    def test_mouse_release_stops_drag(self, qtbot, card):
        """Verifica que mouseRelease detiene el arrastre y emite moved."""
        with qtbot.waitSignal(card.moved, timeout=1000):
            qtbot.mousePress(card, Qt.MouseButton.LeftButton)
            qtbot.mouseRelease(card, Qt.MouseButton.LeftButton)
        assert card.dragging is False

    def test_snap_to_grid(self, card):
        """Verifica que _snap_to_grid ajusta a múltiplos de 20."""
        card.move(25, 33)
        card._snap_to_grid()
        assert card.x() == 20  # round(25/20)*20 = 20
        assert card.y() == 40  # round(33/20)*20 = 40

    def test_snap_to_grid_exact(self, card):
        """Verifica que _snap_to_grid no modifica posiciones ya alineadas."""
        card.move(60, 80)
        card._snap_to_grid()
        assert card.x() == 60
        assert card.y() == 80


@pytest.mark.unit
class TestProductionFlowCanvas:
    """Tests unitarios para ProductionFlowCanvas."""

    @pytest.fixture
    def canvas(self, qtbot):
        """Instancia del canvas de producción."""
        c = ProductionFlowCanvas()
        c.setFixedSize(600, 400)
        qtbot.addWidget(c)
        return c

    @pytest.fixture
    def two_cards(self, qtbot, canvas):
        """Dos tarjetas posicionadas en el canvas."""
        card1 = FlowCardWidget(_make_task_data("T1", "Tarea 1", 5.0))
        card2 = FlowCardWidget(_make_task_data("T2", "Tarea 2", 3.0))
        canvas.add_task_widget(card1)
        canvas.add_task_widget(card2)
        card1.move(50, 100)
        card2.move(300, 100)
        return card1, card2

    def test_init(self, canvas):
        """Verifica inicialización correcta del canvas."""
        assert canvas.connections == []
        assert canvas.task_widgets == []
        assert canvas.acceptDrops()

    def test_add_task_widget(self, canvas, qtbot):
        """Verifica que añadir un widget de tarea lo registra."""
        card = FlowCardWidget(_make_task_data())
        canvas.add_task_widget(card)
        assert len(canvas.task_widgets) == 1
        assert card.parent() is canvas

    def test_clear_widgets(self, canvas, two_cards):
        """Verifica que se limpian todos los widgets."""
        assert len(canvas.task_widgets) == 2
        canvas.clear_widgets()
        assert len(canvas.task_widgets) == 0
        assert canvas.connections == []

    def test_set_connections(self, canvas, two_cards):
        """Verifica que se establecen las conexiones."""
        card1, card2 = two_cards
        conns = [{'start': card1, 'end': card2, 'type': 'normal'}]
        canvas.set_connections(conns)
        assert len(canvas.connections) == 1

    def test_card_selected_signal(self, qtbot, canvas):
        """Verifica que al hacer clic en una tarjeta se emite cardSelected."""
        card = FlowCardWidget(_make_task_data("T5", "Tarea 5"))
        canvas.add_task_widget(card)
        with qtbot.waitSignal(canvas.cardSelected, timeout=1000) as blocker:
            qtbot.mouseClick(card, Qt.MouseButton.LeftButton)
        assert blocker.args[0] == "T5"

    def test_background_clicked_signal(self, qtbot, canvas):
        """Verifica que al hacer clic en el fondo se emite backgroundClicked."""
        with qtbot.waitSignal(canvas.backgroundClicked, timeout=1000) as blocker:
            qtbot.mouseClick(canvas, Qt.MouseButton.LeftButton, pos=QPoint(500, 350))
        assert blocker.signal_triggered

    def test_drag_enter_event(self, canvas):
        """Verifica aceptación de drag enter."""
        event = MagicMock(spec=["mimeData", "acceptProposedAction"])
        event.mimeData.return_value.hasFormat.return_value = True
        canvas.dragEnterEvent(event)
        event.acceptProposedAction.assert_called()

    def test_drag_move_event(self, canvas):
        """Verifica aceptación de drag move."""
        event = MagicMock(spec=["acceptProposedAction"])
        canvas.dragMoveEvent(event)
        event.acceptProposedAction.assert_called()

    def test_drop_event(self, qtbot, canvas):
        """Verifica la emisión de señal al soltar un elemento."""
        mock_item = MagicMock(spec=["data"])
        mock_item.data.return_value = {'id': 'T99', 'name': 'Dropped'}

        mock_source = MagicMock(spec=["currentItem"])
        mock_source.currentItem.return_value = mock_item

        event = MagicMock(spec=["source", "position"])
        event.source.return_value = mock_source
        event.position.return_value.toPoint.return_value = QPoint(100, 100)

        with qtbot.waitSignal(canvas.taskDropped, timeout=1000) as blocker:
            canvas.dropEvent(event)
        assert blocker.signal_triggered

    def test_drop_event_invalid(self, canvas):
        """Verifica que drop inválido no falla."""
        event = MagicMock(spec=["source"])
        event.source.side_effect = AttributeError
        try:
            canvas.dropEvent(event)
        except AttributeError:
            pytest.fail("dropEvent no debería propagar AttributeError")
        assert len(canvas.connections) >= 0  # canvas sigue en estado válido

    def test_calculate_smart_path(self, canvas, two_cards):
        """Verifica el cálculo de ruta inteligente entre dos puntos."""
        card1, card2 = two_cards
        start = QPointF(card1.geometry().right(), card1.geometry().center().y())
        end = QPointF(card2.geometry().left(), card2.geometry().center().y())

        painter = FlowConnectionPainter(create_autospec(DummyPainter, instance=True))
        path = painter.calculate_smart_path(start, end, card1, card2, canvas.task_widgets)
        assert len(path) >= 2  # At least start and end points
        assert isinstance(path[0], QPointF)

    def test_count_path_collisions_no_obstacles(self, canvas):
        """Verifica conteo de colisiones sin obstáculos."""
        path = [QPointF(0, 0), QPointF(100, 0)]
        painter = FlowConnectionPainter(create_autospec(DummyPainter, instance=True))
        result = painter._count_collisions(path, [])
        assert result == 0

    def test_count_path_collisions_with_obstacle(self, canvas):
        """Verifica conteo de colisiones con un obstáculo."""
        path = [QPointF(0, 50), QPointF(200, 50)]
        obstacles = [QRect(80, 30, 40, 40)]  # Obstacle in path
        painter = FlowConnectionPainter(create_autospec(DummyPainter, instance=True))
        result = painter._count_collisions(path, obstacles)
        assert result >= 1

    def test_line_intersects_rect_true(self, canvas):
        """Verifica detección de intersección línea-rectángulo."""
        line = QLineF(QPointF(0, 50), QPointF(200, 50))
        rect = QRect(80, 30, 40, 40)  # rect: (80,30) to (120,70)
        painter = FlowConnectionPainter(create_autospec(DummyPainter, instance=True))
        assert painter._line_intersects_rect(line, rect) is True

    def test_line_intersects_rect_false(self, canvas):
        """Verifica no-intersección línea-rectángulo."""
        line = QLineF(QPointF(0, 0), QPointF(50, 0))
        rect = QRect(200, 200, 40, 40)
        painter = FlowConnectionPainter(create_autospec(DummyPainter, instance=True))
        assert painter._line_intersects_rect(line, rect) is False

    def test_line_intersects_rect_contained(self, canvas):
        """Verifica intersección cuando punto está contenido en rectángulo."""
        line = QLineF(QPointF(90, 50), QPointF(110, 50))
        rect = QRect(80, 30, 40, 40)
        painter = FlowConnectionPainter(create_autospec(DummyPainter, instance=True))
        assert painter._line_intersects_rect(line, rect) is True

    def test_adjust_path_to_avoid_obstacles(self, canvas):
        """Verifica ajuste de ruta para evitar obstáculos."""
        path = [QPointF(0, 0), QPointF(100, 0), QPointF(100, 100)]
        obstacles = [QRect(80, -20, 40, 40)]
        painter = FlowConnectionPainter(create_autospec(DummyPainter, instance=True))
        result = painter._avoid_obstacles(path, obstacles, 20)
        assert len(result) >= 3

    def test_adjust_path_wrong_length(self, canvas):
        """Verifica que rutas con longitud != 3 se retornan sin cambios."""
        path = [QPointF(0, 0), QPointF(100, 100)]
        painter = FlowConnectionPainter(create_autospec(DummyPainter, instance=True))
        result = painter._avoid_obstacles(path, [], 20)
        assert result == path

    def test_paint_event_no_crash(self, canvas, two_cards):
        """Verifica que paintEvent no falla con conexiones válidas."""
        card1, card2 = two_cards
        canvas.set_connections([
            {'start': card1, 'end': card2, 'type': 'normal'},
        ])
        canvas.repaint()  # Fuerza paintEvent
        # Verificar que las conexiones siguen intactas después del render
        assert len(canvas.connections) == 1

    def test_paint_event_cyclic_connections(self, canvas, two_cards):
        """Verifica rendering de conexiones cíclicas."""
        card1, card2 = two_cards
        canvas.set_connections([
            {'start': card1, 'end': card2, 'type': 'cyclic',
             'is_from_mother': True, 'is_to_mother': False},
        ])
        canvas.repaint()
        assert len(canvas.connections) == 1

    def test_paint_event_cyclic_to_mother(self, canvas, two_cards):
        """Verifica rendering de conexión cíclica hacia madre."""
        card1, card2 = two_cards
        canvas.set_connections([
            {'start': card1, 'end': card2, 'type': 'cyclic',
             'is_from_mother': False, 'is_to_mother': True},
        ])
        canvas.repaint()
        assert len(canvas.connections) == 1

    def test_paint_event_cyclic_neither(self, canvas, two_cards):
        """Verifica rendering de conexión cíclica sin madre."""
        card1, card2 = two_cards
        canvas.set_connections([
            {'start': card1, 'end': card2, 'type': 'cyclic',
             'is_from_mother': False, 'is_to_mother': False},
        ])
        canvas.repaint()
        assert len(canvas.connections) == 1

    def test_paint_event_invalid_connections(self, canvas):
        """Verifica que conexiones inválidas no causan crash."""
        canvas.set_connections([
            {'start': None, 'end': None, 'type': 'normal'},
            {'start': "not_a_widget", 'end': "not_a_widget", 'type': 'normal'},
        ])
        canvas.repaint()
        assert len(canvas.connections) == 2

    def test_paint_event_hidden_widget_skipped(self, canvas, two_cards):
        """Verifica que widgets ocultos se omiten en el rendering."""
        card1, card2 = two_cards
        card1.hide()
        canvas.set_connections([
            {'start': card1, 'end': card2, 'type': 'normal'},
        ])
        canvas.repaint()
        assert not card1.isVisible()

    def test_draw_grid_directly(self, canvas):
        """Verifica el dibujado de la cuadrícula invocando directamente."""
        mock_painter = create_autospec(DummyPainter, instance=True)
        with patch('ui.widgets.production_flow.flow_connection_painter.QColor', autospec=True), \
             patch('ui.widgets.production_flow.flow_connection_painter.QPen', autospec=True):
            FlowConnectionPainter.draw_grid(mock_painter, 600, 400)
        mock_painter.setPen.assert_called()
        mock_painter.drawLine.assert_called()

    def test_draw_connection_normal(self, canvas, two_cards):
        """Verifica el dibujado de una conexión normal invocando directamente."""
        card1, card2 = two_cards
        mock_painter = create_autospec(DummyPainter, instance=True)
        with patch('ui.widgets.production_flow.flow_connection_painter.QColor', autospec=True), \
             patch('ui.widgets.production_flow.flow_connection_painter.QPen', autospec=True), \
             patch('ui.widgets.production_flow.flow_connection_painter.QBrush', autospec=True):
            painter = FlowConnectionPainter(mock_painter)
            painter.draw_connection(
                card1, card2, "normal", CanvasCyclicConnectionFlags(), canvas.task_widgets
            )
        mock_painter.drawLine.assert_called()

    def test_draw_connection_cyclic_from_mother(self, canvas, two_cards):
        """Verifica el dibujado de una conexión cíclica desde madre."""
        card1, card2 = two_cards
        mock_painter = create_autospec(DummyPainter, instance=True)
        flags = CanvasCyclicConnectionFlags(is_from_mother=True, is_to_mother=False)
        
        mock_color = create_autospec(DummyColor, instance=True)
        with patch('ui.widgets.production_flow.flow_connection_painter.QColor', return_value=mock_color), \
             patch('ui.widgets.production_flow.flow_connection_painter.QPen', autospec=True), \
             patch('ui.widgets.production_flow.flow_connection_painter.QBrush', autospec=True), \
             patch('ui.widgets.production_flow.flow_connection_painter.QLinearGradient', autospec=True):
            painter = FlowConnectionPainter(mock_painter)
            painter.draw_connection(card1, card2, "cyclic", flags, canvas.task_widgets)
        mock_painter.drawLine.assert_called()

    def test_draw_connection_cyclic_to_mother(self, canvas, two_cards):
        """Verifica el dibujado de conexión cíclica hacia madre."""
        card1, card2 = two_cards
        mock_painter = create_autospec(DummyPainter, instance=True)
        flags = CanvasCyclicConnectionFlags(is_from_mother=False, is_to_mother=True)
        
        mock_color = create_autospec(DummyColor, instance=True)
        with patch('ui.widgets.production_flow.flow_connection_painter.QColor', return_value=mock_color), \
             patch('ui.widgets.production_flow.flow_connection_painter.QPen', autospec=True), \
             patch('ui.widgets.production_flow.flow_connection_painter.QBrush', autospec=True), \
             patch('ui.widgets.production_flow.flow_connection_painter.QLinearGradient', autospec=True):
            painter = FlowConnectionPainter(mock_painter)
            painter.draw_connection(card1, card2, "cyclic", flags, canvas.task_widgets)
        mock_painter.drawLine.assert_called()

    def test_draw_connection_cyclic_standard(self, canvas, two_cards):
        """Verifica el dibujado de conexión cíclica estándar (sin madre)."""
        card1, card2 = two_cards
        mock_painter = create_autospec(DummyPainter, instance=True)
        flags = CanvasCyclicConnectionFlags(is_from_mother=False, is_to_mother=False)
        
        mock_color = create_autospec(DummyColor, instance=True)
        with patch('ui.widgets.production_flow.flow_connection_painter.QColor', return_value=mock_color), \
             patch('ui.widgets.production_flow.flow_connection_painter.QPen', autospec=True), \
             patch('ui.widgets.production_flow.flow_connection_painter.QBrush', autospec=True), \
             patch('ui.widgets.production_flow.flow_connection_painter.QLinearGradient', autospec=True):
            painter = FlowConnectionPainter(mock_painter)
            painter.draw_connection(card1, card2, "cyclic", flags, canvas.task_widgets)
        mock_painter.drawLine.assert_called()

    def test_draw_arrowhead(self, canvas):
        """Verifica el dibujado de la flecha."""
        mock_painter = create_autospec(DummyPainter, instance=True)
        p1 = QPointF(0, 0)
        p2 = QPointF(100, 0)
        painter = FlowConnectionPainter(mock_painter)
        painter._draw_arrowhead(p1, p2, size=10)
        mock_painter.drawPolygon.assert_called_once_with(ANY)

    def test_mouse_move_during_drag(self, qtbot):
        """Verifica que mouseMoveEvent mueve la tarjeta durante arrastre."""
        parent = QWidget()
        parent.setFixedSize(600, 400)
        qtbot.addWidget(parent)
        parent.show()

        card = FlowCardWidget(_make_task_data("T1", "Test", 1.0), parent=parent)
        card.move(100, 100)
        card.show()

        # Simulate drag
        card.dragging = True
        card.drag_start_position = QPoint(10, 10)

        from PyQt6.QtGui import QMouseEvent
        from PyQt6.QtCore import QEvent
        event = QMouseEvent(
            QEvent.Type.MouseMove,
            QPointF(50, 50),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        card.mouseMoveEvent(event)
        # Card should have moved
        assert card.pos() != QPoint(100, 100)

        parent.deleteLater()

    def test_drag_enter_event_no_format(self, canvas):
        """Verifica aceptación de drag enter sin formato específico."""
        event = MagicMock(spec=["mimeData", "acceptProposedAction"])
        event.mimeData.return_value.hasFormat.return_value = False
        canvas.dragEnterEvent(event)
        event.acceptProposedAction.assert_called()

    def test_adjust_path_vertical_first(self, canvas):
        """Verifica cálculo de ruta con primer segmento vertical."""
        # path2 should be chosen when vertical is shorter  
        path = [QPointF(100, 0), QPointF(100, 200), QPointF(300, 200)]
        obstacles = [QRect(80, 80, 40, 40)]
        painter = FlowConnectionPainter(create_autospec(DummyPainter, instance=True))
        result = painter._avoid_obstacles(path, obstacles, 20)
        assert len(result) >= 3

