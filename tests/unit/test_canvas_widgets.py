# -*- coding: utf-8 -*-
"""Tests unitarios para CanvasWidget y CardWidget (diálogos de canvas)."""
import pytest
from unittest.mock import MagicMock, call
from PyQt6.QtCore import Qt, QPoint, QPointF, QLineF, QRect
from PyQt6.QtGui import QMouseEvent, QDropEvent, QDragEnterEvent, QDragMoveEvent, QPainter, QPolygonF
from PyQt6.QtWidgets import QWidget, QLabel

from core.dtos import FlowTaskDataDTO
from core.flow_canvas_io import CanvasVisualConnection
from ui.dialogs.canvas_widgets import CanvasWidget, CardWidget

pytestmark = pytest.mark.unit

class MockParentDialog(QWidget):
    def __init__(self):
        super().__init__()
        self.canvas_tasks = []
        self._add_task_to_canvas = MagicMock(spec=[])
        self._hide_inspector_panel = MagicMock(spec=[])
        self._update_canvas_connections = MagicMock(spec=[])

@pytest.fixture
def mock_parent_dialog(qtbot):
    dialog = MockParentDialog()
    qtbot.addWidget(dialog)
    return dialog

@pytest.fixture
def canvas_widget(qtbot, mock_parent_dialog):
    widget = CanvasWidget(mock_parent_dialog)
    qtbot.addWidget(widget)
    return widget

def test_canvas_widget_init(canvas_widget, mock_parent_dialog):
    assert canvas_widget.parent_dialog == mock_parent_dialog
    assert canvas_widget.acceptDrops() is True
    assert canvas_widget.connections == []

def test_set_connections(canvas_widget):
    # Use real widgets to avoid paintEvent exceptions in teardown
    w1 = QWidget()
    w2 = QWidget()
    canvas_widget.set_connections([{"start": w1, "end": w2, "type": "normal"}])
    assert len(canvas_widget.connections) == 1
    c = canvas_widget.connections[0]
    assert isinstance(c, CanvasVisualConnection)
    assert c.start is w1 and c.end is w2 and c.connection_type == "normal"

def test_drag_events(canvas_widget):
    # Pass a duck-typed object instead of speccing a Qt Event which sometimes fails
    class MockDragEvent:
        def __init__(self):
            self.accepted = False
        def acceptProposedAction(self):
            self.accepted = True
            
    event1 = MockDragEvent()
    canvas_widget.dragEnterEvent(event1)
    assert event1.accepted
    
    event2 = MockDragEvent()
    canvas_widget.dragMoveEvent(event2)
    assert event2.accepted

def test_drop_event(canvas_widget, mock_parent_dialog):
    class MockItem:
        def data(self, role, user_role):
            return {"id": 1, "name": "Task"}
            
    class MockSource:
        def currentItem(self):
            return MockItem()
            
    class MockDropEvent:
        def __init__(self):
            self.accepted = False
        def position(self):
            class Pos:
                def toPoint(self):
                    return QPoint(100, 100)
            return Pos()
        def source(self):
            return MockSource()
        def acceptProposedAction(self):
            self.accepted = True

    event = MockDropEvent()
    canvas_widget.dropEvent(event)
    mock_parent_dialog._add_task_to_canvas.assert_called_once_with(
        {"id": 1, "name": "Task"}, QPoint(100, 100), skip_confirmation=False
    )
    assert event.accepted

def test_get_task_index_by_widget(canvas_widget, mock_parent_dialog):
    w1 = QWidget()
    w2 = QWidget()
    mock_parent_dialog.canvas_tasks = [
        {"widget": w1},
        {"widget": w2}
    ]
    assert canvas_widget._get_task_index_by_widget(w1) == 0
    assert canvas_widget._get_task_index_by_widget(w2) == 1
    assert canvas_widget._get_task_index_by_widget(QWidget()) is None

def test_mouse_press_event(canvas_widget, mock_parent_dialog):
    event = QMouseEvent(QMouseEvent.Type.MouseButtonPress, QPointF(10, 10), QPointF(10, 10), Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
    canvas_widget.mousePressEvent(event)
    assert mock_parent_dialog._hide_inspector_panel.call_count == 1
    mock_parent_dialog._hide_inspector_panel.assert_called_once_with()

def test_card_widget_basic(qtbot, mock_parent_dialog):
    canvas = CanvasWidget(mock_parent_dialog)
    qtbot.addWidget(canvas)
    
    task_data = {"id": 1, "name": "Task1", "duration": 4.5}
    card = CardWidget(task_data, canvas)
    qtbot.addWidget(card)
    
    assert isinstance(card.task_data, FlowTaskDataDTO)
    assert card.task_data.id == "1"
    assert card.task_data.name == "Task1"
    assert card.task_data.duration == 4.5
    assert card.parent_dialog == mock_parent_dialog
    assert "Task1" in card.text()
    assert "4.50 min" in card.text()

def test_card_widget_mouse_events(qtbot, mock_parent_dialog):
    canvas = CanvasWidget(mock_parent_dialog)
    qtbot.addWidget(canvas)
    
    card = CardWidget({"id": 1, "name": "Task1", "duration": 4.5}, canvas)
    qtbot.addWidget(card)
    
    # Test press
    with qtbot.waitSignal(card.clicked) as blocker:
        event = QMouseEvent(QMouseEvent.Type.MouseButtonPress, QPointF(10, 10), QPointF(10, 10), Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
        card.mousePressEvent(event)
    assert blocker.args[0] == card.task_data
    assert card.dragging is True
    assert card.drag_start_position == QPoint(10, 10)
    
    # Test move
    event2 = QMouseEvent(QMouseEvent.Type.MouseMove, QPointF(20, 20), QPointF(20, 20), Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
    card.mouseMoveEvent(event2)
    assert mock_parent_dialog._update_canvas_connections.call_count == 1
    mock_parent_dialog._update_canvas_connections.assert_called_once_with()
    
    # Test release
    with qtbot.waitSignal(card.moved):
        event3 = QMouseEvent(QMouseEvent.Type.MouseButtonRelease, QPointF(20, 20), QPointF(20, 20), Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
        card.mouseReleaseEvent(event3)
    assert card.dragging is False

def test_canvas_path_finding(canvas_widget):
    # simulate grid smart path
    w1 = QWidget()
    w1.setGeometry(0, 0, 100, 100)
    w2 = QWidget()
    w2.setGeometry(200, 0, 100, 100)
    
    p1 = QPointF(100, 50)
    p2 = QPointF(200, 50)
    path = canvas_widget._calculate_smart_path(p1, p2, w1, w2)
    assert len(path) >= 2
    
    # mock obstacle
    rect = QRect(120, 20, 60, 60)
    line = QLineF(QPointF(100, 50), QPointF(200, 50))
    assert canvas_widget._line_intersects_rect(line, rect) is True
    
    line2 = QLineF(QPointF(100, 150), QPointF(200, 150))
    assert canvas_widget._line_intersects_rect(line2, rect) is False
    
    # hit path collisions
    path_with_coll = [QPointF(100, 50), QPointF(200, 50)]
    assert canvas_widget._count_path_collisions(path_with_coll, [rect]) == 1

def test_paint_event_full(canvas_widget, qtbot):
    w1 = CardWidget({"id": 1, "name": "A", "duration": 1}, canvas_widget)
    w2 = CardWidget({"id": 2, "name": "B", "duration": 1}, canvas_widget)
    w3 = CardWidget({"id": 3, "name": "C", "duration": 1}, canvas_widget)
    
    w1.setGeometry(10, 10, 50, 50)
    w2.setGeometry(100, 10, 50, 50)
    w3.setGeometry(10, 100, 50, 50)
    
    # Cover the _get_task_index logic fully
    canvas_widget.parent_dialog.canvas_tasks = [
        {"widget": w1, "config": {"is_cycle_start": True}},
        {"widget": w2, "config": {"is_cycle_start": False}},
        {"widget": w3, "config": {}}
    ]
    
    # Add multiple types of connections to hit all branches in paintEvent
    canvas_widget.set_connections([
        {"start": w1, "end": w2, "type": "normal"},
        {"start": w2, "end": w1, "type": "cyclic"},
        {"start": w1, "end": w3, "type": "normal"},
    ])
    
    # Render to pixmap to force a full paintEvent call
    pixmap = canvas_widget.grab()
    assert not pixmap.isNull()  # El render se completó sin crash
    from PyQt6.QtGui import QImage, QPainter
    image = QImage(1000, 1000, QImage.Format.Format_ARGB32)
    painter = QPainter(image)
    try:
        # Cover _draw_cyclic_arrow_with_glow explicitly
        canvas_widget._draw_cyclic_arrow_with_glow(painter, QPointF(10, 10), QPointF(50, 50), w1, w2, True, False)
        canvas_widget._draw_cyclic_arrow_with_glow(painter, QPointF(10, 10), QPointF(50, 50), w1, w2, False, True)
    finally:
        painter.end()

def test_card_widget_snap_to_grid(qtbot, mock_parent_dialog):
    canvas = CanvasWidget(mock_parent_dialog)
    qtbot.addWidget(canvas)
    card = CardWidget({"id": 1, "name": "Task1", "duration": 4.5}, canvas)
    qtbot.addWidget(card)
    card.move(17, 33)
    card._snap_to_grid()
    # 17 should snap to 20, 33 should snap to 40 (assuming grid is 20)
    assert card.pos().x() % 20 == 0
    assert card.pos().y() % 20 == 0

def test_canvas_path_edge_cases(canvas_widget):
    # 1. 145-146: _draw_cyclic_arrow_with_glow with False, False
    from PyQt6.QtGui import QImage, QPainter
    image = QImage(100, 100, QImage.Format.Format_ARGB32)
    painter = QPainter(image)
    w1 = QWidget()
    w1.setGeometry(0, 0, 10, 10)
    w2 = QWidget()
    w2.setGeometry(20, 20, 10, 10)
    try:
        canvas_widget._draw_cyclic_arrow_with_glow(painter, QPointF(0,0), QPointF(10,10), w1, w2, False, False)
    finally:
        painter.end()

    # 2. 271-273: path2 preferred (vertical first)
    p1 = QPointF(0, 0)
    p2 = QPointF(100, 100)
    obs1 = QWidget()
    obs1.setGeometry(80, 0, 20, 20) # Blocks path1 horizontal segment (0,0)->(100,0)
    
    obs2 = QWidget()
    obs2.setGeometry(0, 80, 20, 20) # Blocks path2 vertical segment
    
    canvas_widget.parent_dialog.canvas_tasks = [{'widget': obs1}]
    # path1 has collision, path2 has 0 -> returns path2
    path = canvas_widget._calculate_smart_path(p1, p2, w1, w2)
    
    # Force collisions1 > collisions2 AND collisions2 > 0
    obs3 = QWidget()
    obs3.setGeometry(80, 80, 40, 40) # Intersects path1 segment 2 and path2 segment 2
    canvas_widget.parent_dialog.canvas_tasks = [{'widget': obs1}, {'widget': obs3}]
    # path1 has 2 collisions (obs1, obs3) 
    # path2 has 1 collision (obs3)
    # This hits line 272
    path = canvas_widget._calculate_smart_path(p1, p2, w1, w2)
    
    # 3. 331: _adjust_path_to_avoid_obstacles with len(path) != 3
    assert canvas_widget._adjust_path_to_avoid_obstacles([p1, p2], [], 20) == [p1, p2]
    
    # 4. 353-369: _adjust_path_to_avoid_obstacles 
    # vertical first (hit >= 369)
    path_vert = [QPointF(0,0), QPointF(0, 100), QPointF(100, 100)]
    adj_path = canvas_widget._adjust_path_to_avoid_obstacles(path_vert, [QRect(-10, 50, 20, 20)], 20)
    assert len(adj_path) == 4
    
    # horizontal first (hit 353)
    path_horiz = [QPointF(0,0), QPointF(100, 0), QPointF(100, 100)]
    adj_path_horiz = canvas_widget._adjust_path_to_avoid_obstacles(path_horiz, [QRect(50, -10, 20, 20)], 20)
    assert len(adj_path_horiz) == 4
    
    # force it when adjustment still fails
    fail_path = canvas_widget._adjust_path_to_avoid_obstacles(path_vert, [QRect(-100, -100, 500, 500)], 20)
    assert len(fail_path) == 3
    
    # 5. 322: _line_intersects_rect point inside rect but no edge intersection
    res = canvas_widget._line_intersects_rect(QLineF(QPointF(5,5), QPointF(6,6)), QRect(0,0,10,10))
    assert res is True
