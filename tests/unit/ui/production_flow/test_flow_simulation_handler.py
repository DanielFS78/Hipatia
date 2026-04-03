import pytest
from unittest.mock import MagicMock, create_autospec
from PyQt6.QtWidgets import QLabel, QWidget
from ui.dialogs.production_flow.flow_simulation_handler import FlowSimulationHandler

# Imports para specs
from ui.dialogs.production_flow.enhanced_flow_presenter import EnhancedFlowPresenter
from ui.widgets.production_flow.flow_graph_manager import FlowGraphManager
from core.services.flow_simulation_service import FlowSimulationService

@pytest.fixture
def simulation_deps(qtbot):
    presenter = create_autospec(EnhancedFlowPresenter, instance=True)
    graph_manager = create_autospec(FlowGraphManager, instance=True)
    label = QLabel()
    qtbot.addWidget(label)
    return presenter, graph_manager, label

def test_simulation_lifecycle(qtbot, simulation_deps):
    presenter, graph_manager, label = simulation_deps
    handler = FlowSimulationHandler(presenter, graph_manager, label)
    mock_service = create_autospec(FlowSimulationService, instance=True)
    
    # Mock de inicio exitoso
    presenter.start_simulation_preview.return_value = True
    presenter.get_simulation_progress_text.return_value = "Progreso"
    
    # Simular pasos
    presenter.get_next_simulation_step.side_effect = [0, -1]
    
    finished_spy = MagicMock(spec=[])
    handler.finished.connect(finished_spy)
    
    # Iniciar con un intervalo largo para control manual en el test
    assert handler.start(mock_service, interval_ms=1000)
    assert handler.timer.isActive()
    
    # Simular tick manualmente para evitar race conditions en entornos CI
    handler._on_tick()
    
    graph_manager.highlight_processing_task.assert_called_once_with(0)
    presenter.get_simulation_progress_text.assert_called_once_with(0)
    assert label.text() == "Progreso"
    assert not label.isHidden()
    
    # Segundo tick (fin)
    handler._on_tick()
    
    assert not handler.timer.isActive()
    assert label.isHidden()
    graph_manager.clear_simulation_effects.assert_called_once_with()
    finished_spy.assert_called_once_with()
    
    # Limpieza final
    handler.stop()

def test_simulation_start_failure(simulation_deps):
    presenter, graph_manager, label = simulation_deps
    handler = FlowSimulationHandler(presenter, graph_manager, label)
    mock_service = create_autospec(FlowSimulationService, instance=True)
    
    presenter.start_simulation_preview.return_value = False
    assert not handler.start(mock_service)
    assert not handler.timer.isActive()
    presenter.start_simulation_preview.assert_called_once_with(mock_service)
