from unittest.mock import MagicMock
import pytest
from PyQt6.QtWidgets import QApplication
from ui.widgets.production_flow.flow_toolbar import FlowToolbarWidget

@pytest.fixture
def toolbar(qtbot):
    widget = FlowToolbarWidget()
    qtbot.addWidget(widget)
    return widget

def test_toolbar_signals(toolbar, qtbot):
    """Verifica que los botones emiten las señales correctas con aserciones estrictas."""
    # Mocks para escuchar señales
    clear_spy = MagicMock(spec=[])
    load_spy = MagicMock(spec=[])
    save_spy = MagicMock(spec=[])
    calc_spy = MagicMock(spec=[])
    
    toolbar.clear_requested.connect(clear_spy)
    toolbar.load_requested.connect(load_spy)
    toolbar.save_requested.connect(save_spy)
    toolbar.calculate_requested.connect(calc_spy)
    
    # 1. Limpiar
    toolbar.clear_button.click()
    clear_spy.assert_called_once_with()
    
    # 2. Cargar
    toolbar.load_button.click()
    load_spy.assert_called_once_with()
    
    # 3. Guardar
    toolbar.save_button.click()
    save_spy.assert_called_once_with()
    
    # 4. Calcular
    toolbar.calc_button.click()
    calc_spy.assert_called_once_with()

def test_toolbar_enable_disable(toolbar):
    """Verifica el habilitado/deshabilitado de botones."""
    toolbar.set_buttons_enabled(False)
    assert not toolbar.clear_button.isEnabled()
    assert not toolbar.load_button.isEnabled()
    assert not toolbar.save_button.isEnabled()
    assert not toolbar.calc_button.isEnabled()
    
    toolbar.set_buttons_enabled(True)
    assert toolbar.clear_button.isEnabled()
    assert toolbar.load_button.isEnabled()
    assert toolbar.save_button.isEnabled()
    assert toolbar.calc_button.isEnabled()
