"""
Tests unitarios para AppController - Gestión de Preprocesos.

Cobertura objetivo: 100% de métodos relacionados con preprocesos.
Siguiendo la metodología de Fase 2: Happy Path, Empty State, Not Found, Edge Cases.
"""
import pytest
from unittest.mock import MagicMock, patch, PropertyMock, ANY
from PyQt6.QtWidgets import QDialog, QMessageBox

from controllers.app_controller import AppController
from ui.widgets import PreprocesosWidget


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def mock_view():
    """Mock de MainView con páginas configuradas."""
    view = MagicMock()
    view.pages = {}
    view.buttons = {}
    view.show_message = MagicMock()
    view.show_confirmation_dialog = MagicMock(return_value=True)
    return view


@pytest.fixture
def mock_model():
    """Mock de AppModel con repositorios simulados."""
    model = MagicMock()
    model.db = MagicMock()
    model.db.config_repo = MagicMock()
    model.db.tracking_repo = MagicMock()
    model.worker_repo = MagicMock()
    model.preproceso_repo = MagicMock()
    model.product_deleted_signal = MagicMock()
    model.pilas_changed_signal = MagicMock()
    return model


@pytest.fixture
def mock_schedule_config():
    """Mock de ScheduleConfig."""
    return MagicMock()


@pytest.fixture
def controller(mock_model, mock_view, mock_schedule_config):
    """Instancia de AppController con dependencias mockeadas."""
    with patch('controllers.app_controller.CameraManager'), \
         patch('controllers.app_controller.QrGenerator'), \
         patch('controllers.app_controller.LabelManager'), \
         patch('controllers.app_controller.LabelCounterRepository'):
        ctrl = AppController(mock_model, mock_view, mock_schedule_config)
        return ctrl


@pytest.fixture
def controller_with_preprocesos_widget(controller):
    """Controller con widget de preprocesos configurado."""
    mock_widget = MagicMock(spec=PreprocesosWidget)
    mock_widget.add_button = MagicMock()
    mock_widget.add_button.clicked = MagicMock()
    mock_widget.edit_button = MagicMock()
    mock_widget.edit_button.clicked = MagicMock()
    mock_widget.delete_button = MagicMock()
    mock_widget.delete_button.clicked = MagicMock()
    mock_widget.set_controller = MagicMock()
    mock_widget.load_preprocesos_data = MagicMock()
    mock_widget._on_edit_clicked = MagicMock()
    mock_widget._on_delete_clicked = MagicMock()
    
    controller.view.pages = {"preprocesos": mock_widget}
    return controller, mock_widget


# =============================================================================
# TESTS: _connect_preprocesos_signals
# =============================================================================

class TestConnectPreprocesosSignals:
    """Tests para _connect_preprocesos_signals."""

    def test_connect_preprocesos_signals_success(self, controller_with_preprocesos_widget):
        """Verifica que las señales se conectan correctamente cuando el widget existe."""
        controller, mock_widget = controller_with_preprocesos_widget
        
        controller._connect_preprocesos_signals()
        
        # Verificar que se estableció el controlador
        mock_widget.set_controller.assert_called_once_with(controller)
        
        # Verificar que se conectaron las señales de botones
        mock_widget.add_button.clicked.connect.assert_called()
        mock_widget.edit_button.clicked.connect.assert_called()
        mock_widget.delete_button.clicked.connect.assert_called()

    def test_connect_preprocesos_signals_loads_data(self, controller_with_preprocesos_widget):
        """Verifica que se cargan los datos iniciales al conectar señales."""
        controller, mock_widget = controller_with_preprocesos_widget
        
        controller.model.get_all_preprocesos_with_components.return_value = [
            {"id": 1, "nombre": "Preproceso 1"}
        ]
        
        controller._connect_preprocesos_signals()
        
        # Verificar que se llamó a cargar datos
        mock_widget.load_preprocesos_data.assert_called()

    def test_connect_preprocesos_signals_widget_not_found(self, controller):
        """Verifica manejo cuando el widget de preprocesos no existe."""
        controller.view.pages = {}
        
        # No debería lanzar excepción
        controller._connect_preprocesos_signals()

    def test_connect_preprocesos_signals_wrong_widget_type(self, controller):
        """Verifica manejo cuando el widget no es del tipo correcto."""
        controller.view.pages = {"preprocesos": MagicMock()}  # No es PreprocesosWidget
        
        # No debería lanzar excepción, solo hacer log de warning
        controller._connect_preprocesos_signals()

    def test_connect_preprocesos_signals_exception_handling(self, controller):
        """Verifica que las excepciones se manejan correctamente."""
        # Simular widget que lanza excepción
        mock_widget = MagicMock(spec=PreprocesosWidget)
        mock_widget.set_controller.side_effect = Exception("Test error")
        controller.view.pages = {"preprocesos": mock_widget}
        
        # No debería propagar la excepción
        controller._connect_preprocesos_signals()


# =============================================================================
# TESTS: _load_preprocesos_data
# =============================================================================

class TestLoadPreprocesosData:
    """Tests para _load_preprocesos_data."""

    def test_load_preprocesos_data_success(self, controller_with_preprocesos_widget):
        """Verifica carga exitosa de datos de preprocesos."""
        controller, mock_widget = controller_with_preprocesos_widget
        
        test_data = [
            {"id": 1, "nombre": "Corte", "componentes": []},
            {"id": 2, "nombre": "Soldadura", "componentes": [{"material": "Hierro"}]}
        ]
        controller.model.get_all_preprocesos_with_components.return_value = test_data
        
        controller._load_preprocesos_data()
        
        mock_widget.load_preprocesos_data.assert_called_with(test_data)

    def test_load_preprocesos_data_empty_list(self, controller_with_preprocesos_widget):
        """Verifica comportamiento con lista vacía de preprocesos."""
        controller, mock_widget = controller_with_preprocesos_widget
        
        controller.model.get_all_preprocesos_with_components.return_value = []
        
        controller._load_preprocesos_data()
        
        mock_widget.load_preprocesos_data.assert_called_with([])

    def test_load_preprocesos_data_widget_not_found(self, controller):
        """Verifica comportamiento cuando el widget no existe."""
        controller.view.pages = {}
        
        # No debería lanzar excepción
        controller._load_preprocesos_data()

    def test_load_preprocesos_data_exception_loads_empty(self, controller_with_preprocesos_widget):
        """Verifica que en caso de error se carga lista vacía."""
        controller, mock_widget = controller_with_preprocesos_widget
        
        controller.model.get_all_preprocesos_with_components.side_effect = Exception("DB Error")
        
        controller._load_preprocesos_data()
        
        # Debe cargar lista vacía en caso de error
        mock_widget.load_preprocesos_data.assert_called_with([])


# =============================================================================
# TESTS: get_all_preprocesos_with_components
# =============================================================================

class TestGetAllPreprocesosWithComponents:
    """Tests para get_all_preprocesos_with_components."""

    def test_get_all_preprocesos_success(self, controller):
        """Verifica obtención exitosa de preprocesos."""
        test_data = [
            {"id": 1, "nombre": "Preproceso A"},
            {"id": 2, "nombre": "Preproceso B"}
        ]
        controller.model.preproceso_repo.get_all_preprocesos.return_value = test_data
        
        result = controller.get_all_preprocesos_with_components()
        
        assert result == test_data
        controller.model.preproceso_repo.get_all_preprocesos.assert_called_once()

    def test_get_all_preprocesos_empty(self, controller):
        """Verifica retorno de lista vacía cuando no hay preprocesos."""
        controller.model.preproceso_repo.get_all_preprocesos.return_value = []
        
        result = controller.get_all_preprocesos_with_components()
        
        assert result == []

    def test_get_all_preprocesos_exception(self, controller):
        """Verifica manejo de excepciones retornando lista vacía."""
        controller.model.preproceso_repo.get_all_preprocesos.side_effect = Exception("DB Error")
        
        result = controller.get_all_preprocesos_with_components()
        
        assert result == []


# =============================================================================
# TESTS: show_add_preproceso_dialog
# =============================================================================

class TestShowAddPreprocesoDialog:
    """Tests para show_add_preproceso_dialog."""

    def test_add_preproceso_dialog_success(self, controller):
        """Verifica creación exitosa de preproceso vía diálogo."""
        materials = [{"id": 1, "nombre": "Material A"}]
        controller.model.get_all_materials_for_selection.return_value = materials
        
        dialog_data = {"nombre": "Nuevo Preproceso", "descripcion": "Test"}
        
        with patch('controllers.app_controller.PreprocesoDialog') as MockDialog:
            dialog_instance = MockDialog.return_value
            dialog_instance.exec.return_value = True
            dialog_instance.get_data.return_value = dialog_data
            
            controller.model.create_preproceso.return_value = True
            
            # Mock widget para evitar errores en _load_preprocesos_data
            mock_widget = MagicMock()
            controller.view.pages = {"preprocesos": mock_widget}
            controller.model.get_all_preprocesos_with_components.return_value = []
            
            controller.show_add_preproceso_dialog()
            
            # Verificar que se obtuvo los materiales
            controller.model.get_all_materials_for_selection.assert_called_once()
            
            # Verificar que se mostró el diálogo
            MockDialog.assert_called_once_with(all_materials=materials, controller=ANY, parent=controller.view)
            
            # Verificar que se creó el preproceso
            controller.model.create_preproceso.assert_called_once_with(dialog_data)
            
            # Verificar mensaje de éxito
            controller.view.show_message.assert_called_with(
                ANY, ANY, "info"
            )

    def test_add_preproceso_dialog_cancelled(self, controller):
        """Verifica comportamiento cuando el usuario cancela el diálogo."""
        controller.model.get_all_materials_for_selection.return_value = []
        
        with patch('controllers.app_controller.PreprocesoDialog') as MockDialog:
            dialog_instance = MockDialog.return_value
            dialog_instance.exec.return_value = False  # Usuario canceló
            
            controller.show_add_preproceso_dialog()
            
            # No debería crear preproceso
            controller.model.create_preproceso.assert_not_called()

    def test_add_preproceso_dialog_creation_fails(self, controller):
        """Verifica manejo cuando la creación del preproceso falla."""
        controller.model.get_all_materials_for_selection.return_value = []
        
        dialog_data = {"nombre": "Preproceso Fallido"}
        
        with patch('controllers.app_controller.PreprocesoDialog') as MockDialog:
            dialog_instance = MockDialog.return_value
            dialog_instance.exec.return_value = True
            dialog_instance.get_data.return_value = dialog_data
            
            controller.model.create_preproceso.return_value = False  # Fallo
            
            controller.show_add_preproceso_dialog()
            
            # Verificar mensaje de error
            controller.view.show_message.assert_called_with(
                "Error", "No se pudo crear el preproceso. El nombre podría ya existir.", "critical"
            )

    def test_add_preproceso_dialog_empty_data(self, controller):
        """Verifica manejo cuando el diálogo retorna datos vacíos."""
        controller.model.get_all_materials_for_selection.return_value = []
        
        with patch('controllers.app_controller.PreprocesoDialog') as MockDialog:
            dialog_instance = MockDialog.return_value
            dialog_instance.exec.return_value = True
            dialog_instance.get_data.return_value = None  # Sin datos
            
            controller.show_add_preproceso_dialog()
            
            # No debería intentar crear
            controller.model.create_preproceso.assert_not_called()

    def test_add_preproceso_dialog_exception(self, controller):
        """Verifica manejo de excepciones durante el proceso."""
        controller.model.get_all_materials_for_selection.side_effect = Exception("Error")
        
        # No debería propagar la excepción
        controller.show_add_preproceso_dialog()


# =============================================================================
# TESTS: show_edit_preproceso_dialog
# =============================================================================

class TestShowEditPreprocesoDialog:
    """Tests para show_edit_preproceso_dialog."""

    def test_edit_preproceso_dialog_success(self, controller):
        """Verifica edición exitosa de preproceso vía diálogo."""
        preproceso_data = MagicMock()
        preproceso_data.id = 1
        preproceso_data.nombre = "Preproceso Original"
        
        materials = [{"id": 1, "nombre": "Material X"}]
        controller.model.get_all_materials_for_selection.return_value = materials
        
        new_data = {"nombre": "Preproceso Actualizado", "descripcion": "Nueva desc"}
        
        with patch('controllers.app_controller.PreprocesoDialog') as MockDialog:
            dialog_instance = MockDialog.return_value
            dialog_instance.exec.return_value = True
            dialog_instance.get_data.return_value = new_data
            
            controller.model.update_preproceso.return_value = True
            
            # Mock widget
            mock_widget = MagicMock()
            controller.view.pages = {"preprocesos": mock_widget}
            controller.model.get_all_preprocesos_with_components.return_value = []
            
            controller.show_edit_preproceso_dialog(preproceso_data)
            
            # Verificar que se pasó el preproceso existente al diálogo
            MockDialog.assert_called_once_with(
                preproceso_existente=preproceso_data,
                all_materials=materials,
                controller=ANY,
                parent=controller.view
            )
            
            # Verificar actualización
            controller.model.update_preproceso.assert_called_once_with(1, new_data)
            
            # Verificar mensaje de éxito
            controller.view.show_message.assert_called_with(
                ANY, ANY, "info"
            )

    def test_edit_preproceso_dialog_cancelled(self, controller):
        """Verifica comportamiento cuando el usuario cancela la edición."""
        preproceso_data = MagicMock()
        preproceso_data.id = 1
        
        controller.model.get_all_materials_for_selection.return_value = []
        
        with patch('controllers.app_controller.PreprocesoDialog') as MockDialog:
            dialog_instance = MockDialog.return_value
            dialog_instance.exec.return_value = False
            
            controller.show_edit_preproceso_dialog(preproceso_data)
            
            controller.model.update_preproceso.assert_not_called()

    def test_edit_preproceso_dialog_update_fails(self, controller):
        """Verifica manejo cuando la actualización falla."""
        preproceso_data = MagicMock()
        preproceso_data.id = 1
        
        controller.model.get_all_materials_for_selection.return_value = []
        
        with patch('controllers.app_controller.PreprocesoDialog') as MockDialog:
            dialog_instance = MockDialog.return_value
            dialog_instance.exec.return_value = True
            dialog_instance.get_data.return_value = {"nombre": "Test"}
            
            controller.model.update_preproceso.return_value = False
            
            controller.show_edit_preproceso_dialog(preproceso_data)
            
            controller.view.show_message.assert_called_with(
                "Error", "No se pudo actualizar el preproceso.", "critical"
            )

    def test_edit_preproceso_dialog_exception(self, controller):
        """Verifica manejo de excepciones durante la edición."""
        preproceso_data = MagicMock()
        preproceso_data.id = 1
        
        controller.model.get_all_materials_for_selection.side_effect = Exception("Error")
        
        # No debería propagar la excepción
        controller.show_edit_preproceso_dialog(preproceso_data)


# =============================================================================
# TESTS: delete_preproceso
# =============================================================================

class TestDeletePreproceso:
    """Tests para delete_preproceso.
    
    Nota: Los tests de QMessageBox requieren patching especial debido a cómo
    PyQt6 importa las clases. Estos tests verifican la lógica básica.
    """

    def test_delete_preproceso_calls_model_on_confirm(self, controller):
        """Verifica que delete_preproceso llama al modelo cuando se confirma."""
        mock_widget = MagicMock()
        controller.view.pages = {"preprocesos": mock_widget}
        controller.model.get_all_preprocesos_with_components.return_value = []
        controller.model.delete_preproceso.return_value = True
        
        # Simular QMessageBox devolviendo Yes usando monkeypatch en el módulo
        import controllers.app_controller as app_ctrl_module
        original_qmb = app_ctrl_module.QMessageBox
        
        mock_qmb = MagicMock()
        mock_qmb.StandardButton = original_qmb.StandardButton
        mock_qmb.question.return_value = original_qmb.StandardButton.Yes
        mock_qmb.information = MagicMock()
        
        app_ctrl_module.QMessageBox = mock_qmb
        try:
            controller.delete_preproceso(1, "Preproceso Test")
            controller.model.delete_preproceso.assert_called_once_with(1)
        finally:
            app_ctrl_module.QMessageBox = original_qmb


# =============================================================================
# TESTS: Métodos de preprocesos para fabricaciones
# =============================================================================

class TestPreprocesosFabricacionMethods:
    """Tests para métodos de preprocesos relacionados con fabricaciones."""

    def test_get_preprocesos_by_fabricacion_success(self, controller):
        """Verifica obtención de preprocesos por fabricación."""
        # Setup preproceso_repo en el controller directamente
        # Since this method is delegated to ProductController, we must mock it there
        mock_preproceso_repo = MagicMock()
        controller.product_controller.preproceso_repo = mock_preproceso_repo
        
        # Crear mock de preprocesos con atributos correctos
        mock_prep1 = MagicMock()
        mock_prep1.id = 1
        mock_prep1.nombre = "Prep 1"
        mock_prep1.descripcion = "Descripción 1"
        mock_prep1.componentes = []
        
        mock_prep2 = MagicMock()
        mock_prep2.id = 2
        mock_prep2.nombre = "Prep 2"
        mock_prep2.descripcion = "Descripción 2"
        mock_prep2.componentes = []
        
        mock_preproceso_repo.get_preprocesos_by_fabricacion.return_value = [mock_prep1, mock_prep2]
        
        result = controller.get_preprocesos_by_fabricacion(10)
        
        mock_preproceso_repo.get_preprocesos_by_fabricacion.assert_called_once_with(10)
        assert len(result) == 2
        assert result[0]['id'] == 1
        assert result[0]['nombre'] == "Prep 1"

    def test_get_preprocesos_by_fabricacion_empty(self, controller):
        """Verifica retorno vacío cuando no hay preprocesos asignados."""
        mock_preproceso_repo = MagicMock()
        controller.product_controller.preproceso_repo = mock_preproceso_repo
        mock_preproceso_repo.get_preprocesos_by_fabricacion.return_value = []
        
        result = controller.get_preprocesos_by_fabricacion(999)
        
        assert result == []

    def test_get_preprocesos_by_fabricacion_exception(self, controller):
        """Verifica manejo de excepción retornando lista vacía."""
        mock_preproceso_repo = MagicMock()
        controller.product_controller.preproceso_repo = mock_preproceso_repo
        mock_preproceso_repo.get_preprocesos_by_fabricacion.side_effect = Exception("DB Error")
        
        result = controller.get_preprocesos_by_fabricacion(10)
        
        assert result == []

    def test_add_preprocesos_to_current_pila_success(self, controller):
        """Verifica añadir preprocesos a la pila de cálculo actual."""
        mock_calc = MagicMock()
        mock_calc.planning_session = []
        controller.view.pages = {"calculate": mock_calc}
        
        preprocesos = [
            {"id": 1, "nombre": "Prep 1", "componentes": []}
        ]
        
        # Mock del método de conversión
        with patch.object(controller, '_convert_preproceso_to_pila_step') as mock_convert:
            mock_convert.return_value = {"tipo": "preproceso", "id": 1}
            
            count = controller.add_preprocesos_to_current_pila(preprocesos)
            
            assert count == 1

    def test_convert_preproceso_to_pila_step_success(self, controller):
        """Verifica conversión de preproceso a formato de paso de pila."""
        preproceso = {
            "id": 5,
            "nombre": "Preproceso Prueba",
            "componentes": [(1, "Hierro"), (2, "Acero")]
        }
        
        result = controller._convert_preproceso_to_pila_step(preproceso)
        
        assert result is not None
        assert result['tipo'] == 'preproceso'
        assert result['preproceso_id'] == 5
        assert result['preproceso_nombre'] == "Preproceso Prueba"
        assert result['es_preproceso'] is True
        assert "PREPROCESO" in result['descripcion']

    def test_convert_preproceso_to_pila_step_empty_components(self, controller):
        """Verifica conversión cuando no hay componentes."""
        preproceso = {
            "id": 3,
            "nombre": "Preproceso Sin Componentes",
            "componentes": []
        }
        
        result = controller._convert_preproceso_to_pila_step(preproceso)
        
        assert result is not None
        assert result['tiempo'] >= 10  # Mínimo 10 minutos

    def test_convert_preproceso_to_pila_step_exception(self, controller):
        """Verifica manejo de excepción durante conversión."""
        # Preproceso malformado sin key 'nombre'
        preproceso = {"id": 1}  
        
        result = controller._convert_preproceso_to_pila_step(preproceso)
        
        # Debe retornar None en caso de error
        assert result is None


# =============================================================================
# TESTS: Edge Cases y Valores Límite
# =============================================================================

class TestPreprocesosEdgeCases:
    """Tests para casos límite y edge cases de preprocesos."""

    def test_preproceso_with_special_characters_name(self, controller):
        """Verifica manejo de nombres con caracteres especiales."""
        controller.model.get_all_materials_for_selection.return_value = []
        
        dialog_data = {"nombre": "Preproceso (Especial) #1 - Test/V2"}
        
        with patch('controllers.app_controller.PreprocesoDialog') as MockDialog:
            dialog_instance = MockDialog.return_value
            dialog_instance.exec.return_value = True
            dialog_instance.get_data.return_value = dialog_data
            
            controller.model.create_preproceso.return_value = True
            mock_widget = MagicMock()
            controller.view.pages = {"preprocesos": mock_widget}
            controller.model.get_all_preprocesos_with_components.return_value = []
            
            controller.show_add_preproceso_dialog()
            
            controller.model.create_preproceso.assert_called_once_with(dialog_data)

    def test_preproceso_with_empty_name(self, controller):
        """Verifica manejo de nombre vacío."""
        controller.model.get_all_materials_for_selection.return_value = []
        
        dialog_data = {"nombre": ""}
        
        with patch('controllers.app_controller.PreprocesoDialog') as MockDialog:
            dialog_instance = MockDialog.return_value
            dialog_instance.exec.return_value = True
            dialog_instance.get_data.return_value = dialog_data
            
            controller.model.create_preproceso.return_value = False
            
            controller.show_add_preproceso_dialog()
            
            # Debe intentar crear y manejar el fallo
            controller.model.create_preproceso.assert_called_once()

    def test_preproceso_with_very_long_name(self, controller):
        """Verifica manejo de nombres muy largos."""
        controller.model.get_all_materials_for_selection.return_value = []
        
        long_name = "A" * 500  # Nombre extremadamente largo
        dialog_data = {"nombre": long_name}
        
        with patch('controllers.app_controller.PreprocesoDialog') as MockDialog:
            dialog_instance = MockDialog.return_value
            dialog_instance.exec.return_value = True
            dialog_instance.get_data.return_value = dialog_data
            
            controller.model.create_preproceso.return_value = True
            mock_widget = MagicMock()
            controller.view.pages = {"preprocesos": mock_widget}
            controller.model.get_all_preprocesos_with_components.return_value = []
            
            controller.show_add_preproceso_dialog()
            
            controller.model.create_preproceso.assert_called_once_with(dialog_data)

    def test_load_preprocesos_with_many_items(self, controller_with_preprocesos_widget):
        """Verifica carga de gran cantidad de preprocesos."""
        controller, mock_widget = controller_with_preprocesos_widget
        
        # Lista grande de preprocesos
        large_data_set = [{"id": i, "nombre": f"Preproceso {i}"} for i in range(1000)]
        controller.model.get_all_preprocesos_with_components.return_value = large_data_set
        
        controller._load_preprocesos_data()
        
        mock_widget.load_preprocesos_data.assert_called_with(large_data_set)

    def test_delete_preproceso_with_zero_id(self, controller):
        """Verifica comportamiento con ID 0."""
        with patch.object(QMessageBox, 'question', return_value=QMessageBox.StandardButton.Yes):
            controller.model.delete_preproceso.return_value = False
            
            controller.delete_preproceso(0, "Zero ID Preproceso")
            
            controller.model.delete_preproceso.assert_called_once_with(0)

    def test_delete_preproceso_with_negative_id(self, controller):
        """Verifica comportamiento con ID negativo."""
        with patch.object(QMessageBox, 'question', return_value=QMessageBox.StandardButton.Yes):
            controller.model.delete_preproceso.return_value = False
            
            controller.delete_preproceso(-1, "Negative ID Preproceso")
            
            controller.model.delete_preproceso.assert_called_once_with(-1)
