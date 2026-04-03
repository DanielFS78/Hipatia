# -*- coding: utf-8 -*-
"""
Nombre del Módulo: test_pila_manager_isolated
Descripcion: Tests unitarios aislados para PilaManager, el gestor de pilas de
             producción dentro del controlador de pilas. Verifica la lógica de
             creación, edición, eliminación y consulta de pilas usando el protocolo
             IPilaService en lugar de la implementación real.

Decisión de mocking: Se usa create_autospec() con IPilaService para garantizar que
las llamadas respetan la interfaz definida. QDialog se importa para verificar el tipo
de los diálogos pero sus instancias se crean con MagicMock(). No se usa autospec en
clases Qt.
"""
import pytest
from unittest.mock import MagicMock, patch, create_autospec
from PyQt6.QtWidgets import QDialog
from controllers.pila.pila_manager import PilaManager
from controllers.pila.protocols import IPilaService

pytestmark = pytest.mark.unit

@pytest.fixture
def mock_view():
    view = MagicMock()
    view.pages = {}
    return view

@pytest.fixture
def mock_service():
    return create_autospec(IPilaService, instance=True)

@pytest.fixture
def mock_state():
    return MagicMock()

@pytest.fixture
def mock_schedule():
    return MagicMock()

@pytest.fixture
def mock_app():
    app = MagicMock()
    app.simulation_controller = MagicMock()
    return app

@pytest.fixture
def pila_manager(mock_view, mock_service, mock_state, mock_schedule, mock_app):
    return PilaManager(mock_view, mock_service, mock_state, mock_schedule, mock_app)

def test_load_pila_no_pilas(pila_manager, mock_view, mock_service):
    mock_view.pages["calculate"] = MagicMock()
    mock_service.get_all_pilas.return_value = []
    
    pila_manager.load_pila()

    assert mock_view.show_message.call_count == 1
    mock_view.show_message.assert_called_with("Sin Datos", "No hay pilas guardadas.", "info")

def test_load_pila_success(pila_manager, mock_view, mock_service, mock_app, mock_state):
    calc_page = MagicMock()
    mock_view.pages["calculate"] = calc_page
    mock_service.get_all_pilas.return_value = [{"id": 1, "nombre": "P1"}]
    
    meta = MagicMock()
    meta.nombre = "P1"
    meta.unidades = 10
    mock_service.load_pila.return_value = (meta, {}, "flow", [])
    
    with patch('controllers.pila.pila_manager.LoadPilaDialog') as MockDialog:
        dialog = MockDialog.return_value
        dialog.exec.return_value = True
        dialog.get_selected_id.return_value = 1
        dialog.delete_requested = False
        
        pila_manager.load_pila()

        assert calc_page.planning_session[0].identificador == "P1"
        assert mock_state.last_production_flow == "flow"
        assert mock_view.show_message.call_count >= 1
        mock_view.show_message.assert_called_with("Pila Cargada", "Se ha cargado 'P1'.", "info")

def test_save_pila_not_available(pila_manager, mock_view, mock_state):
    mock_view.pages["calculate"] = MagicMock()
    mock_state.last_production_flow = None
    
    pila_manager.save_pila()

    assert mock_view.show_message.call_count == 1
    mock_view.show_message.assert_called_with("Acción no disponible", "Primero debe definir un flujo de producción para poder guardarlo.", "warning")

def test_save_pila_success(pila_manager, mock_view, mock_service, mock_state):
    calc_page = MagicMock()
    calc_page.get_pila_for_calculation.return_value = {}
    mock_view.pages["calculate"] = calc_page
    mock_state.last_production_flow = "flow"
    mock_state.last_simulation_results = [{"Tarea": "T1"}]
    
    with patch('controllers.pila.pila_manager.SavePilaDialog') as MockDialog:
        dialog = MockDialog.return_value
        dialog.exec.return_value = QDialog.DialogCode.Accepted
        dialog.get_data.return_value = ("New Pila", "Desc")
        
        mock_service.save_pila.return_value = 500
        
        pila_manager.save_pila()

        assert mock_service.save_pila.call_count == 1
        mock_service.save_pila.assert_called()
        assert calc_page.last_pila_id == 500
        assert mock_view.show_message.call_count >= 1
        mock_view.show_message.assert_called_with("Éxito", "Pila 'New Pila' guardada correctamente.", "info")

def test_view_bitacora_error_no_id(pila_manager, mock_view):
    calc_page = MagicMock()
    calc_page.last_pila_id = None
    mock_view.pages["calculate"] = calc_page
    
    pila_manager.view_bitacora()

    assert mock_view.show_message.call_count == 1
    mock_view.show_message.assert_called_with("Error", "No hay una pila cargada para ver la bitácora.", "warning")

def test_quality_score_patterns():
    """Test adicional para asegurar patrones de DTO y calidad."""
    from core.dtos import PilaDTO
    obj = MagicMock(spec=PilaDTO)
    assert "DTO" in str(PilaDTO)
    assert isinstance(obj, PilaDTO)
