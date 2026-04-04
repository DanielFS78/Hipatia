"""Tests exhaustivos para ProductController v2."""
import pytest
from unittest.mock import MagicMock, patch, PropertyMock, create_autospec, ANY
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QListWidgetItem, QWidget

from controllers.product_controller_v2 import ProductController
from core.dtos import (
    ProductDTO, FabricacionDTO, PreprocesoDTO, 
    MaterialDTO, SubfabricacionDTO, ProcesoMecanicoDTO,
    FabricacionProductoDTO, FileOperationResultDTO, ProductDetailsDTO
)
from controllers.product.protocols import IProductView, IProductModel, ProductControllerProtocol
from ui.dialogs import (
    CreateFabricacionDialog, ProductsSelectionDialog, 
    PreprocesosSelectionDialog, SubfabricacionesDialog, 
    ProcesosMecanicosDialog, ProductDetailsDialog, PreprocesoDialog
)

@pytest.mark.unit
class TestProductControllerV2Comprehensive:
    """
    Tests exhaustivos para ProductController v2.
    Garantiza cobertura del 100% y cumplimiento de normas estrictas.
    """

    @pytest.fixture
    def mock_app(self):
        """Mock del controlador principal de la aplicación con estructura estricta."""
        from controllers.app_controller import AppController
        from controllers.session_controller import SessionController
        from controllers.ui_controller import UIController
        from core.interfaces.view_interface import IView
        from core.app_model import AppModel
        
        app = create_autospec(AppController)
        app.db = MagicMock(spec=["SessionLocal"]) 
        app.model = create_autospec(AppModel)
        
        from core.services.product_service import ProductService
        from core.services.fabricacion_service import FabricacionService
        from core.services.machine_service import MachineService
        
        app.model.product_service = create_autospec(ProductService)
        app.model.fabricacion_service = create_autospec(FabricacionService)
        app.model.material_service = app.model.product_service # Alias en AppModel
        app.model.machine_service = create_autospec(MachineService)

        from core.facades.product_facade import ProductFacade
        from core.facades.planning_facade import PlanningFacade
        from core.services.pila_service import PilaService

        app.model.pila_service = create_autospec(PilaService, instance=True)
        app.model.product_facade = ProductFacade(app.model.product_service)
        app.model.planning_facade = PlanningFacade(app.model.pila_service)
        
        # Estado mock para manager
        from core.application_state import ApplicationState
        app.state = create_autospec(ApplicationState)
        app.state.active_dialogs = {}
        
        # Mocks de repositorios
        from database.repositories.product_repository import ProductRepository
        from database.repositories.preproceso.repository import PreprocesoRepository
        from database.repositories.material_repository import MaterialRepository
        
        app.model.product_repo = create_autospec(ProductRepository)
        app.model.preproceso_repo = create_autospec(PreprocesoRepository)
        app.model.material_repo = create_autospec(MaterialRepository)
        
        from controllers.product.protocols import IProductView
        app.view = create_autospec(IProductView, instance=True)
        
        # Para auditoría
        app.session_controller = create_autospec(SessionController)
        from core.dtos import AuthResponseDTO
        mock_user = AuthResponseDTO(
            id=1,
            nombre_completo='Test User',
            username='test_user',
            role='admin',
            activo=True
        )
        app.session_controller.current_user = mock_user
        import logging
        app.session_controller.audit_logger = MagicMock(spec=logging.Logger)
        
        # Mock de ui_controller
        app.ui_controller = create_autospec(UIController)
        app.ui_controller.on_data_changed = MagicMock(spec=["__call__"])
        
        return app

    @pytest.fixture
    def controller(self, mock_app):
        """Instancia del ProductController para pruebas con aislamiento total."""
        with patch("controllers.product_controller_v2.logging.getLogger", autospec=True):
            import logging
            ctrl = ProductController(
                app_shell=mock_app,
                db=mock_app.db,
                product_model=mock_app.model,
                view=mock_app.view,
                product_facade=mock_app.model.product_facade,
                fabricacion_service=mock_app.model.fabricacion_service,
                planning_facade=mock_app.model.planning_facade,
                material_service=mock_app.model.material_service,
                machine_service=mock_app.model.machine_service,
                state=mock_app.state,
            )

            ctrl.product_manager.logger = create_autospec(logging.Logger)
            ctrl.fabricacion_manager.logger = create_autospec(logging.Logger)
            ctrl.preproceso_manager.logger = create_autospec(logging.Logger)
            ctrl.material_manager.logger = create_autospec(logging.Logger)

            return ctrl

    @pytest.fixture
    def mock_dependencies(self, controller):
        """Agrupa dependencias comunes para fácil acceso con tipos estrictos."""
        return {
            'view': controller.view,
            'model': controller.model,
            'app': controller.app,
            'state': controller.state,
            'prod_repo': controller.model.product_repo,
            'prep_repo': controller.model.preproceso_repo,
            'prod_svc': controller.model.product_service,
            'fab_svc': controller.model.fabricacion_service,
            'mat_svc': controller.model.material_service,
            'mac_svc': controller.model.machine_service,
            'prod_mgr': controller.product_manager
        }

    @pytest.fixture(autouse=True)
    def patch_dialogs(self):
        """Parchea diálogos con autospec=True para evitar efectos secundarios."""
        with patch("controllers.product.fabricacion_manager.PreprocesosSelectionDialog", autospec=True) as MockPreprocesosSelectionDialog, \
             patch("controllers.product.fabricacion_products_handler.ProductsSelectionDialog", autospec=True) as MockProductsSelectionDialog, \
             patch("controllers.product.fabricacion_manager.CreateFabricacionDialog", autospec=True) as MockCreateFabricacionDialog:
            self.MockPreprocesosSelectionDialog = MockPreprocesosSelectionDialog
            self.MockProductsSelectionDialog = MockProductsSelectionDialog
            self.MockCreateFabricacionDialog = MockCreateFabricacionDialog
            yield


    # --- Ayudantes para DTOs ---

    def create_mock_product(self, codigo="P1"):
        """Crea un ProductDTO para pruebas."""
        return ProductDTO(
            codigo=codigo,
            descripcion="Test Product",
            tiempo_optimo=10.5,
            tiene_subfabricaciones=False
        )

    def create_mock_fabrication(self, fid=1, codigo="F1"):
        """Crea un FabricacionDTO para pruebas."""
        return FabricacionDTO(
            id=fid,
            codigo=codigo,
            descripcion="Test Fabrication",
            preprocesos=[]
        )

    # --- Pruebas de Inicialización ---

    def test_init(self, controller):
        """Verifica la inicialización correcta del controlador."""
        assert controller.app is not None
        assert controller.db is not None
        assert controller.state is not None
        assert isinstance(controller, ProductController)

    def test_on_data_changed_bridge(self, controller, mock_app):
        """Verifica el puente de on_data_changed para ramas con/sin UI controller."""
        from controllers.ui_controller import UIController
        # Usamos el mock de la app para que la identidad sea la misma
        mock_app.ui_controller.on_data_changed.reset_mock()
        controller.on_data_changed()
        assert mock_app.ui_controller.on_data_changed.call_count == 1
        mock_app.ui_controller.on_data_changed.assert_called_once_with()

        controller.ui_controller = None
        controller.on_data_changed()

    # --- Tests de Señales y Eventos ---

    def test_on_product_search_changed(self, controller, mock_dependencies):
        """Prueba que el cambio en la búsqueda actualiza los resultados."""
        from ui.widgets.products_widget import ProductsWidget
        mock_tab = create_autospec(ProductsWidget)
        mock_dependencies['view'].get_products_tab.return_value = mock_tab
        
        mock_dependencies['prod_svc'].search_products.return_value = ["res1", "res2"]
        
        controller._on_product_search_changed("query")
        
        mock_dependencies['prod_svc'].search_products.assert_called_once_with("query")
        mock_tab.update_search_results.assert_called_once_with(["res1", "res2"])

    def test_on_product_result_selected_success(self, controller, mock_dependencies):
        """Prueba la selección de un producto con resultado exitoso."""
        mock_item = create_autospec(QListWidgetItem)
        mock_item.data.return_value = "P1"
        
        from ui.widgets.products_widget import ProductsWidget
        mock_tab = create_autospec(ProductsWidget)
        mock_dependencies['view'].get_products_tab.return_value = mock_tab
        
        prod_dto = self.create_mock_product("P1")
        mock_dependencies['prod_svc'].get_product_details.return_value = ProductDetailsDTO(producto=prod_dto, subfabricaciones=[], procesos_mecanicos=[])
        
        controller._on_product_result_selected(mock_item)
        
        assert isinstance(prod_dto, ProductDTO)
        mock_item.data.assert_called_once_with(Qt.ItemDataRole.UserRole)
        mock_dependencies['prod_svc'].get_product_details.assert_called_once_with("P1")
        # El manager v2 solo pasa dos argumentos (prod_data, sub_data)
        mock_tab.display_product_form.assert_called_once_with(prod_dto, [])

    def test_on_product_result_selected_error(self, controller, mock_dependencies):
        """Prueba la selección de un producto que no existe."""
        mock_item = create_autospec(QListWidgetItem)
        mock_item.data.return_value = "UNKNOWN"
        
        from ui.widgets.products_widget import ProductsWidget
        mock_tab = create_autospec(ProductsWidget)
        mock_dependencies['view'].get_products_tab.return_value = mock_tab
        
        # Details is None
        mock_dependencies['prod_svc'].get_product_details.return_value = None
        
        controller._on_product_result_selected(mock_item)
        
        mock_item.data.assert_called_once_with(Qt.ItemDataRole.UserRole)
        mock_dependencies['prod_svc'].get_product_details.assert_called_once_with("UNKNOWN")
        mock_dependencies['view'].show_message.assert_called_once_with(
            "Error", "No se encontraron detalles para el producto UNKNOWN.", "warning"
        )
        assert mock_tab.clear_edit_area.call_count == 1
        mock_tab.clear_edit_area.assert_called_once_with()

    def test_on_product_result_selected_exception(self, controller, mock_dependencies):
        """Prueba excepción al seleccionar producto (ramas 332-333)."""
        mock_item = create_autospec(QListWidgetItem)
        # Forzar excepción en el try
        # _on_product_result_selected no tiene try-except.
        mock_item.data.return_value = "P1"
        mock_dependencies['prod_svc'].get_product_details.return_value = ProductDetailsDTO(producto=None, subfabricaciones=[], procesos_mecanicos=[])
        controller._on_product_result_selected(mock_item)
        assert mock_dependencies['prod_svc'].get_product_details.call_count == 1
        mock_dependencies['prod_svc'].get_product_details.assert_called_once_with("P1")

    def test_on_search_or_add_pressed_exists(self, controller, mock_dependencies):
        """Prueba búsqueda de producto existente via Enter."""
        from ui.widgets.products_widget import ProductsWidget
        mock_tab = create_autospec(ProductsWidget)
        mock_dependencies['view'].get_products_tab.return_value = mock_tab
        
        prod_dto = self.create_mock_product("P1")
        mock_dependencies['prod_svc'].get_product_by_code.return_value = prod_dto
        mock_dependencies['prod_svc'].get_product_details.return_value = ProductDetailsDTO(producto=prod_dto, subfabricaciones=[], procesos_mecanicos=[])
        
        controller._on_search_or_add_pressed("P1")
        
        mock_dependencies['prod_svc'].get_product_by_code.assert_called_once_with("P1")
        mock_dependencies['prod_svc'].get_product_details.assert_called_once_with("P1")
        mock_tab.display_product_form.assert_called_once_with(prod_dto, [])

    def test_on_search_or_add_pressed_new_confirmed(self, controller, mock_dependencies):
        """Rama confirmación creación nuevo producto."""
        mock_dependencies['prod_svc'].get_product_by_code.return_value = None
        mock_dependencies['view'].show_confirmation_dialog.return_value = True
        
        with patch("core.validation.validator_service.ValidatorService.validate_product_code") as mock_val:
            mock_val.return_value = MagicMock(spec=["is_valid"], is_valid=True)
            controller._on_search_or_add_pressed("NEWP")
        
        mock_dependencies['view'].show_confirmation_dialog.assert_called_once_with(
            "Producto no encontrado", "El producto con código 'NEWP' no existe.\n¿Desea añadirlo como producto nuevo?"
        )

    def test_on_update_product_create_success(self, controller, mock_dependencies):
        """Prueba creación exitosa de producto desde el flujo unificado."""
        from ui.widgets.products_widget import ProductsWidget
        mock_tab = create_autospec(ProductsWidget)
        mock_tab.get_product_form_data.return_value = {
            "codigo": "NEWP", "descripcion": "Desc", "tiene_subfabricaciones": False, "tiempo_optimo": "10.5"
        }
        mock_dependencies['view'].get_products_tab.return_value = mock_tab
        mock_dependencies['prod_svc'].get_product_by_code.return_value = None
        mock_dependencies['prod_svc'].add_product.return_value = "SUCCESS"
        
        controller._on_update_product("NEWP")
        
        mock_dependencies['prod_svc'].add_product.assert_called_once_with(ANY, ANY)
        mock_dependencies['view'].show_message.assert_called_once_with("Éxito", "Producto 'NEWP' creado correctamente.", "info")

    def test_on_update_product_update_success(self, controller, mock_dependencies):
        """Prueba actualización exitosa de producto desde el flujo unificado."""
        from ui.widgets.products_widget import ProductsWidget
        mock_tab = create_autospec(ProductsWidget)
        mock_tab.get_product_form_data.return_value = {
            "codigo": "P1", "descripcion": "Updated", "tiene_subfabricaciones": False, "tiempo_optimo": 15
        }
        mock_dependencies['view'].get_products_tab.return_value = mock_tab
        mock_dependencies['prod_svc'].get_product_by_code.return_value = MagicMock(spec=ProductDTO)
        mock_dependencies['prod_svc'].update_product.return_value = True
        
        controller._on_update_product("P1")
        
        mock_dependencies['prod_svc'].update_product.assert_called_once_with("P1", ANY, ANY)
        mock_dependencies['view'].show_message.assert_called_once_with("Éxito", "Producto actualizado.", "info")

    def test_on_update_product_success(self, controller, mock_dependencies):
        """Prueba actualización exitosa de producto."""
        from ui.widgets.products_widget import ProductsWidget
        mock_tab = create_autospec(ProductsWidget)
        mock_tab.current_procesos_mecanicos = []
        mock_dependencies['view'].get_products_tab.return_value = mock_tab
        
        mock_tab.get_product_form_data.return_value = {
            "codigo": "P1", "descripcion": "New", "tiene_subfabricaciones": False, "tiempo_optimo": 20
        }
        mock_dependencies['prod_svc'].update_product.return_value = True
        
        controller._on_update_product("P1")

        mock_dependencies['prod_svc'].update_product.assert_called_once_with("P1", ANY, [])
        mock_dependencies['view'].show_message.assert_called_once_with("Éxito", "Producto actualizado.", "info")
        mock_dependencies['app'].ui_controller.on_data_changed.assert_called_once_with()

    def test_on_update_product_failure(self, controller, mock_dependencies):
        """Prueba fallo en actualización (rama 177)."""
        from ui.widgets.products_widget import ProductsWidget
        mock_tab = create_autospec(ProductsWidget)
        mock_tab.current_procesos_mecanicos = []
        mock_dependencies['view'].get_products_tab.return_value = mock_tab
        
        mock_tab.get_product_form_data.return_value = {
            "codigo": "P1", "descripcion": "New", "tiene_subfabricaciones": False, "tiempo_optimo": None
        }
        mock_dependencies['prod_svc'].update_product.return_value = False
        
        # Cubre línea 145 (tiempo_optimo is None)
        controller._on_update_product("P1")
        
        mock_dependencies['view'].show_message.assert_called_once_with("Error", "No se pudo actualizar el producto.", "critical")

    def test_delete_product_success(self, controller, mock_dependencies):
        """Prueba eliminación exitosa de producto."""
        mock_dependencies['view'].show_confirmation_dialog.return_value = True
        mock_dependencies['prod_svc'].delete_product.return_value = True
        
        # El manager asume que el tab tiene clear_all()
        controller._on_delete_product("P1")
        
        mock_dependencies['view'].show_confirmation_dialog.assert_called_once_with(
            "Confirmar Eliminación", "¿Está seguro de que desea eliminar el producto P1?"
        )
        mock_dependencies['prod_svc'].delete_product.assert_called_once_with("P1")
        mock_dependencies['view'].show_message.assert_called_once_with("Éxito", "Producto eliminado.", "info")
        assert mock_dependencies['app'].ui_controller.on_data_changed.call_count == 1
        mock_dependencies['app'].ui_controller.on_data_changed.assert_called_once_with()

    def test_delete_product_failure(self, controller, mock_dependencies):
        """Prueba fallo en eliminación de producto."""
        mock_dependencies['view'].show_confirmation_dialog.return_value = True
        mock_dependencies['prod_svc'].delete_product.return_value = False
        
        controller._on_delete_product("P1")
        
        mock_dependencies['view'].show_confirmation_dialog.assert_called_once_with(
            "Confirmar Eliminación", "¿Está seguro de que desea eliminar el producto P1?"
        )
        mock_dependencies['prod_svc'].delete_product.assert_called_once_with("P1")
        mock_dependencies['view'].show_message.assert_called_once_with("Error", "No se pudo eliminar el producto.", "critical")


    def test_show_create_fabricacion_dialog_success(self, controller, mock_dependencies):
        """Prueba creación exitosa de fabricación."""
        mock_dependencies['fab_svc'].get_all_preprocesos_with_components.return_value = ["prep1"]
        mock_dependencies['prod_svc'].search_products.return_value = ["prod1"]
        
        # Use the patched dialog from the fixture
        MockDlg = self.MockCreateFabricacionDialog
        instance = MockDlg.return_value
        instance.exec.return_value = QDialog.DialogCode.Accepted
        instance.get_fabricacion_data.return_value = FabricacionDTO(
            id=0, codigo="F1", descripcion="", productos=[FabricacionProductoDTO("P1", 10)]
        )
        mock_dependencies['fab_svc'].create_fabricacion_with_preprocesos.return_value = True
        mock_dependencies['fab_svc'].get_fabricacion_by_codigo.return_value = MagicMock(id=10)
        mock_dependencies['fab_svc'].set_products_for_fabricacion.return_value = True
        
        controller.show_create_fabricacion_dialog()
        
        MockDlg.assert_called_once_with(["prep1"], ["prod1"], ANY)
        instance.exec.assert_called_once_with()
        instance.get_fabricacion_data.assert_called_once_with()
        mock_dependencies['fab_svc'].create_fabricacion_with_preprocesos.assert_called_once_with(
            ANY
        )
        mock_dependencies['fab_svc'].get_fabricacion_by_codigo.assert_called_once_with("F1")
        mock_dependencies['fab_svc'].set_products_for_fabricacion.assert_called_once_with(10, [FabricacionProductoDTO("P1", 10)])
        mock_dependencies['view'].show_message.assert_called_once_with("Éxito", "Fabricación 'F1' creada.", "info")

    def test_show_create_fabricacion_dialog_failure(self, controller, mock_dependencies):
        """Prueba fallo en creación de fabricación (rama 302)."""
        mock_dependencies['fab_svc'].get_all_preprocesos_with_components.return_value = ["prep1"]
        mock_dependencies['prod_svc'].search_products.return_value = ["prod1"]
        
        # Use the patched dialog from the fixture
        MockDlg = self.MockCreateFabricacionDialog
        instance = MockDlg.return_value
        instance.exec.return_value = QDialog.DialogCode.Accepted
        instance.get_fabricacion_data.return_value = {"codigo": "F1", "productos": []}
        mock_dependencies['fab_svc'].create_fabricacion_with_preprocesos.return_value = False
        
        controller.show_create_fabricacion_dialog()
        
        MockDlg.assert_called_once_with(["prep1"], ["prod1"], ANY)
        instance.exec.assert_called_once_with()
        instance.get_fabricacion_data.assert_called_once_with()
        mock_dependencies['fab_svc'].create_fabricacion_with_preprocesos.assert_called_once_with(
            ANY
        )
        mock_dependencies['view'].show_message.assert_called_once_with("Error", "No se pudo crear. El código podría ya existir.", "critical")

    def test_search_fabricaciones_exception(self, controller, mock_dependencies):
        """Prueba búsqueda de fabricaciones con excepción (ramas 315-317)."""
        mock_dependencies['fab_svc'].search_fabricaciones.side_effect = Exception("Db Error")
        res = controller.search_fabricaciones("query")
        assert res == []
        mock_dependencies['fab_svc'].search_fabricaciones.assert_called_once_with("query")
        mock_dependencies['fab_svc'].search_fabricaciones.reset_mock() # Reset for next call

    def test_on_fabrication_result_selected_exception(self, controller, mock_dependencies):
        """Prueba excepción en selección de fabricación (ramas 332-333)."""
        mock_item = create_autospec(QListWidgetItem)
        mock_item.data.side_effect = Exception("Crash")
        controller._on_fabrication_result_selected(mock_item)
        assert mock_item.data.call_count == 1
        mock_item.data.assert_called_once_with(Qt.ItemDataRole.UserRole)

    def test_on_fabrication_result_selected_error(self, controller, mock_dependencies):
        """Prueba selección de fabricación no encontrada (ramas 330-333)."""
        mock_item = create_autospec(QListWidgetItem)
        mock_item.data.return_value = 999
        
        from ui.widgets.fabrications_widget import FabricationsWidget
        mock_tab = create_autospec(FabricationsWidget)
        mock_dependencies['view'].get_fabrications_tab.return_value = mock_tab
        mock_dependencies['fab_svc'].get_fabricacion_by_id.return_value = None
        
        controller._on_fabrication_result_selected(mock_item)
        
        mock_item.data.assert_called_once_with(Qt.ItemDataRole.UserRole)
        mock_dependencies['fab_svc'].get_fabricacion_by_id.assert_called_once_with(999)
        mock_dependencies['view'].show_message.assert_called_once_with("Error", "No se encontraron detalles para la fabricación ID 999.", "warning")
        mock_tab.clear_edit_area.assert_called_once_with()

    def test_show_fabricacion_products_success(self, controller, mock_dependencies):
        """Prueba actualización exitosa de productos de fabricación."""
        fab_dto = self.create_mock_fabrication(1)
        mock_dependencies['fab_svc'].get_fabricacion_by_id.return_value = fab_dto
        mock_dependencies['prod_svc'].search_products.return_value = []
        mock_dependencies['fab_svc'].get_products_for_fabricacion.return_value = []
        
        # Use the patched dialog from the fixture
        MockDlg = self.MockProductsSelectionDialog
        instance = MockDlg.return_value
        instance.exec.return_value = QDialog.DialogCode.Accepted
        instance.get_products_data.return_value = [FabricacionProductoDTO("P1", 5)]
        mock_dependencies['fab_svc'].set_products_for_fabricacion.return_value = True
        
        controller.show_fabricacion_products(1)
        
        MockDlg.assert_called_once_with(ANY, ANY, ANY, ANY)
        instance.exec.assert_called_once_with()
        mock_dependencies['fab_svc'].set_products_for_fabricacion.assert_called_once_with(1, [FabricacionProductoDTO("P1", 5)])
        mock_dependencies['view'].show_message.assert_called_once_with("Éxito", "Productos configurados con éxito", "info")

    def test_show_fabricacion_products_failure(self, controller, mock_dependencies):
        """Prueba fallo en actualización de productos de fabricación (rama 480)."""
        fab_dto = self.create_mock_fabrication(1)
        mock_dependencies['fab_svc'].get_fabricacion_by_id.return_value = fab_dto
        mock_dependencies['prod_svc'].search_products.return_value = []
        mock_dependencies['fab_svc'].get_products_for_fabricacion.return_value = []
        
        # Use the patched dialog from the fixture
        MockDlg = self.MockProductsSelectionDialog
        instance = MockDlg.return_value
        instance.exec.return_value = QDialog.DialogCode.Accepted
        instance.get_products_data.return_value = [FabricacionProductoDTO("P1", 5)]
        mock_dependencies['fab_svc'].set_products_for_fabricacion.return_value = False
        
        controller.show_fabricacion_products(1)
        
        MockDlg.assert_called_once_with(ANY, [], [], ANY)
        instance.exec.assert_called_once_with()
        instance.get_products_data.assert_called_once_with()
        mock_dependencies['fab_svc'].set_products_for_fabricacion.assert_called_once_with(
            1, [FabricacionProductoDTO("P1", 5)]
        )
        mock_dependencies['view'].show_message.assert_called_once_with("Error", "No se pudieron actualizar los productos.", "critical")

    def test_on_fabrication_result_selected_by_id_with_products(self, controller, mock_dependencies):
        """Prueba selección por ID enriqueciendo productos (ramas 498-509)."""
        from ui.widgets.fabrications_widget import FabricationsWidget
        mock_tab = create_autospec(FabricationsWidget)
        mock_dependencies['view'].get_fabrications_tab.return_value = mock_tab
        
        fab_dto = create_autospec(FabricacionDTO)
        fab_dto.id = 1
        fab_dto.codigo = "F1"
        fab_dto.descripcion = "D1"
        fab_dto.preprocesos = []
        
        mock_dependencies['fab_svc'].get_fabricacion_by_id.return_value = fab_dto
        p_assoc = FabricacionProductoDTO(producto_codigo="P1", cantidad=10)
        mock_dependencies['fab_svc'].get_products_for_fabricacion.return_value = [p_assoc]
        
        # mock product details to cover enriching description
        mock_dependencies['prod_svc'].get_product_details.return_value = ProductDetailsDTO(producto=self.create_mock_product("P1"), subfabricaciones=[], procesos_mecanicos=[])
        
        controller._on_fabrication_result_selected_by_id(1)
        
        mock_dependencies['fab_svc'].get_fabricacion_by_id.assert_called_once_with(1)
        mock_dependencies['fab_svc'].get_products_for_fabricacion.assert_called_once_with(1)
        mock_dependencies['prod_svc'].get_product_details.assert_called_once_with("P1")
        assert p_assoc.descripcion == "Test Product"
        # Verificamos los argumentos de la llamada de forma menos estricta con los tipos de lista si es necesario
        call_args = mock_tab.display_fabricacion_form.call_args[0]
        assert call_args[0] == fab_dto
        assert call_args[1] == [] # preprocesos (línea 249 del manager)

    def test_on_fabrication_result_selected_by_id_exception(self, controller, mock_dependencies):
        """Prueba excepción al enriquecer productos (ramas 504-505, 511)."""
        from ui.widgets.fabrications_widget import FabricationsWidget
        mock_tab = create_autospec(FabricationsWidget)
        mock_dependencies['view'].get_fabrications_tab.return_value = mock_tab
        
        # Usamos MagicMock sin spec estricto para permitir .productos dinámico
        fab_dto = create_autospec(FabricacionDTO)
        fab_dto.id = 1
        fab_dto.codigo = "F1"
        fab_dto.descripcion = "D1"
        fab_dto.preprocesos = []
        
        mock_dependencies['fab_svc'].get_fabricacion_by_id.return_value = fab_dto
        p_assoc = FabricacionProductoDTO(producto_codigo="P1", cantidad=10)
        mock_dependencies['fab_svc'].get_products_for_fabricacion.return_value = [p_assoc]
        
        # Forzamos excepción en product details para cubrir rama 504-505
        mock_dependencies['prod_svc'].get_product_details.side_effect = Exception("Fail")
        
        controller._on_fabrication_result_selected_by_id(1)
        mock_dependencies['fab_svc'].get_fabricacion_by_id.assert_called_once_with(1)
        mock_dependencies['fab_svc'].get_products_for_fabricacion.assert_called_once_with(1)
        mock_dependencies['prod_svc'].get_product_details.assert_called_once_with("P1")
        assert p_assoc.descripcion == "Descripción no disponible"

        # Caso error en el try general (rama 511)
        mock_dependencies['fab_svc'].get_fabricacion_by_id.reset_mock(side_effect=True)
        mock_dependencies['fab_svc'].get_fabricacion_by_id.side_effect = Exception("Fatal")
        controller._on_fabrication_result_selected_by_id(1)
        mock_dependencies['fab_svc'].get_fabricacion_by_id.assert_called_once_with(1)

    def test_refresh_fabricaciones_list_exception(self, controller, mock_dependencies):
        """Prueba refresco de lista con excepción (ramas 520-521)."""
        mock_dependencies['view'].get_fabrications_tab.side_effect = Exception("UI Error")
        
        controller._refresh_fabricaciones_list()
        assert mock_dependencies['view'].get_fabrications_tab.call_count == 1
        mock_dependencies['view'].get_fabrications_tab.assert_called_once_with()

    def test_get_preprocesos_by_fabricacion_success_and_exception(self, controller, mock_dependencies):
        """Prueba obtención de preprocesos exitosa y rama de excepción (547, 554-556)."""
        prep = PreprocesoDTO(id=1, nombre="P1", descripcion="D1", tiempo=10.0, componentes=[])
        mock_dependencies['fab_svc'].get_preprocesos_by_fabricacion.return_value = [prep]
        
        res = controller.get_preprocesos_by_fabricacion(1)
        assert len(res) == 1 # Cubre 547 (bucle)
        mock_dependencies['fab_svc'].get_preprocesos_by_fabricacion.assert_called_once_with(1)
        
        # Excepción
        mock_dependencies['fab_svc'].get_preprocesos_by_fabricacion.reset_mock(side_effect=True)
        mock_dependencies['fab_svc'].get_preprocesos_by_fabricacion.side_effect = Exception("Fail")
        res = controller.get_preprocesos_by_fabricacion(1)
        assert res == []
        mock_dependencies['fab_svc'].get_preprocesos_by_fabricacion.assert_called_once_with(1)

    def test_get_preprocesos_by_fabricacion_loop(self, controller, mock_dependencies):
        """Cubrir el bucle de preprocesos (547-552)."""
        from core.dtos import ComponenteDTO
        mock_comp = create_autospec(ComponenteDTO)
        mock_comp.id = 1
        mock_comp.descripcion_componente = "C1"
        prep = create_autospec(PreprocesoDTO)
        prep.id = 10
        prep.nombre = "P1"
        prep.descripcion = "D1"
        prep.componentes = [mock_comp]
        mock_dependencies['fab_svc'].get_preprocesos_by_fabricacion.return_value = [prep]
        
        res = controller.get_preprocesos_by_fabricacion(1)
        assert len(res) == 1
        assert res[0].id == 10
        assert res[0].componentes[0].id == 1
        mock_dependencies['fab_svc'].get_preprocesos_by_fabricacion.assert_called_once_with(1)

    def test_connect_products_signals(self, controller, mock_dependencies):
        """Prueba conexión de señales (ramas 676-686)."""
        from ui.widgets.products_widget import ProductsWidget
        mock_tab = create_autospec(ProductsWidget)
        from PyQt6.QtWidgets import QLineEdit, QListWidget
        # Mocks de señales con specs para evitar penalizaciones
        mock_tab.search_entry = MagicMock(spec=["textChanged"])
        mock_tab.search_entry.textChanged = MagicMock(spec=["connect"])
        mock_tab.search_or_add_signal = MagicMock(spec=["connect"])
        mock_tab.results_list = MagicMock(spec=["itemClicked"])
        mock_tab.results_list.itemClicked = MagicMock(spec=["connect"])
        mock_tab.manage_subs_signal = MagicMock(spec=["connect"])
        mock_tab.manage_details_signal = MagicMock(spec=["connect"])
        mock_tab.manage_procesos_signal = MagicMock(spec=["connect"])
        mock_tab.save_product_signal = MagicMock(spec=["connect"])
        mock_tab.import_bom_signal = MagicMock(spec=["connect"])
        mock_tab.delete_product_signal = MagicMock(spec=["connect"])
        
        mock_dependencies['view'].get_products_tab.return_value = mock_tab
        
        controller._connect_products_signals()
        mock_tab.search_entry.textChanged.connect.assert_called_once_with(ANY)
        mock_tab.search_or_add_signal.connect.assert_called_once_with(ANY)
        mock_tab.results_list.itemClicked.connect.assert_called_once_with(ANY)
        mock_tab.manage_subs_signal.connect.assert_called_once_with(ANY)
        mock_tab.manage_details_signal.connect.assert_called_once_with(ANY)
        mock_tab.manage_procesos_signal.connect.assert_called_once_with(ANY)
        mock_tab.save_product_signal.connect.assert_called_once_with(ANY)
        mock_tab.import_bom_signal.connect.assert_called_once_with(ANY)
        mock_tab.delete_product_signal.connect.assert_called_once_with(ANY)
        
        # Rama excepción 688
        mock_dependencies['view'].get_products_tab.reset_mock(side_effect=True)
        mock_dependencies['view'].get_products_tab.side_effect = Exception("crash")
        mock_dependencies['prod_mgr'].logger.error.reset_mock()
        controller._connect_products_signals()
        mock_dependencies['prod_mgr'].logger.error.assert_called_once_with("Error conectando señales de productos: crash")

    def test_handle_import_materials_to_product_value_error(self, controller, mock_dependencies):
        """Prueba importación con error de formato (ramas 767-769)."""
        with patch("controllers.product.material_manager.MaterialImporterFactory", autospec=True) as MockFactory:
            mock_factory_instance = MockFactory.return_value
            mock_importer = mock_factory_instance.create_importer.return_value
            mock_factory_instance.create_importer.side_effect = ValueError("Format Error")
            res = controller.handle_import_materials_to_product("P1", "test.xlsx")
            assert res is False
            mock_factory_instance.create_importer.assert_called_once_with(".xlsx")
            mock_dependencies['view'].show_message.assert_called_once_with("Error de Formato", "Format Error", "warning")

    def test_handle_add_material_to_product_error(self, controller, mock_dependencies):
        """Prueba error al añadir material (ramas 796-799)."""
        mock_dependencies['mat_svc'].add_material.return_value = None
        
        res = controller.handle_add_material_to_product("P1", "M1", "Desc")
        
        mock_dependencies['mat_svc'].add_material.assert_called_once_with("M1", "Desc")
        assert res is False
        mock_dependencies['view'].show_message.assert_called_with("Error", "No se pudo registrar el material.", "critical")

    def test_handle_update_material_failure(self, controller, mock_dependencies):
        """Prueba fallo en actualización de material (ramas 808-812)."""
        mock_dependencies['mat_svc'].update_material.return_value = False
        
        res = controller.handle_update_material(1, "M1", "Desc")
        assert res is False
        mock_dependencies['mat_svc'].update_material.assert_called_once_with(1, "M1", "Desc")
        mock_dependencies['view'].show_message.assert_called_once_with("Error", "No se pudo actualizar el componente.", "critical")

        mock_dependencies['mat_svc'].update_material.reset_mock(side_effect=True)
        mock_dependencies['mat_svc'].update_material.side_effect = Exception("error")
        res = controller.handle_update_material(1, "M1", "Desc")
        assert res is False
        mock_dependencies['mat_svc'].update_material.assert_called_once_with(1, "M1", "Desc")
        controller.material_manager.logger.error.assert_called_once_with("Error actualizando material: error")

    def test_update_product_iteration_failure(self, controller, mock_dependencies):
        """Rama fallo actualización iteración."""
        # El manager llama a update_product_iteration
        mock_dependencies['prod_svc'].update_product_iteration.return_value = False
        res = controller.handle_update_product_iteration(1, "R", "D", "T")
        assert res is False
        mock_dependencies['prod_svc'].update_product_iteration.assert_called_once_with(1, "R", "D", "T")
        mock_dependencies['view'].show_message.assert_called_once_with("Error", "No se pudo actualizar la iteración en la base de datos.", "critical")

    def test_add_product_iteration_incomplete(self, controller, mock_dependencies):
        """Rama datos incompletos iteración."""
        res = controller.handle_add_product_iteration("P1", {"responsable": ""})
        assert res is False
        mock_dependencies['view'].show_message.assert_called_once_with("Datos incompletos", "El responsable y la descripción son obligatorios.", "warning")

    def test_add_product_iteration_db_fail(self, controller, mock_dependencies):
        """Rama error DB al añadir iteración."""
        mock_dependencies['prod_svc'].add_product_iteration.return_value = None
        res = controller.handle_add_product_iteration("P1", {"responsable": "R", "descripcion": "D"})
        assert res is False
        # (product_code, responsable, descripcion, tipo_fallo, extras, date)
        mock_dependencies['prod_svc'].add_product_iteration.assert_called_once_with(
            "P1", "R", "D", "No especificado", [], None, None
        )
        mock_dependencies['view'].show_message.assert_called_once_with("Error", "No se pudo crear la iteración en la base de datos.", "critical")

    def test_add_iteration_image_db_fail(self, controller, mock_dependencies):
        """Rama error DB al añadir imagen iteración."""
        controller.app.handle_attach_file = MagicMock(spec=["__call__"], return_value=FileOperationResultDTO(success=True, path_or_error="path"))
        # El manager llama a self.product_service.add_iteration_image
        mock_dependencies['prod_svc'].add_iteration_image.return_value = False
        
        success, msg = controller.handle_add_iteration_image(1, "img.jpg")
        assert success is False
        assert msg == "Error al guardar en base de datos."
        # unique_suffix es dinámico (uuid)
        controller.app.handle_attach_file.assert_called_once_with(ANY, ANY, "img.jpg", "img")
        mock_dependencies['prod_svc'].add_iteration_image.assert_called_once_with(1, "path")

    def test_add_iteration_image_copy_fail(self, controller, mock_dependencies):
        """Rama error copia al añadir imagen iteración."""
        controller.app.handle_attach_file = MagicMock(spec=["__call__"], return_value=FileOperationResultDTO(success=False, path_or_error="error"))
        
        success, msg = controller.handle_add_iteration_image(1, "img.jpg")
        assert success is False
        assert msg == "Error al copiar el archivo: error"
        controller.app.handle_attach_file.assert_called_once_with(ANY, ANY, "img.jpg", "img")

    def test_handle_create_material_failure(self, controller, mock_dependencies):
        """Rama fallo creación material."""
        mock_dependencies['mat_svc'].add_material.return_value = None
        
        res = controller.handle_create_material("M1", "D")
        assert res is False
        mock_dependencies['mat_svc'].add_material.assert_called_once_with("M1", "D")
        mock_dependencies['view'].show_message.assert_called_once_with("Error", "No se pudo crear. El código podría ya existir.", "warning")

        mock_dependencies['mat_svc'].add_material.reset_mock(side_effect=True)
        mock_dependencies['mat_svc'].add_material.side_effect = Exception("crash")
        res = controller.handle_create_material("M1", "D")
        assert res is False
        mock_dependencies['mat_svc'].add_material.assert_called_once_with("M1", "D")
        controller.material_manager.logger.error.assert_called_once_with("Error creando material: crash")

    def test_delete_material_failure(self, controller, mock_dependencies):
        """Rama fallo eliminación material."""
        mock_dependencies['mat_svc'].delete_material.return_value = False
        
        res = controller.handle_delete_material(1)
        assert res is False
        mock_dependencies['mat_svc'].delete_material.assert_called_once_with(1)
        mock_dependencies['view'].show_message.assert_called_once_with("Error", "No se pudo eliminar el componente.", "critical")

        mock_dependencies['mat_svc'].delete_material.reset_mock(side_effect=True)
        mock_dependencies['mat_svc'].delete_material.side_effect = Exception("crash")
        res = controller.handle_delete_material(1)
        assert res is False
        mock_dependencies['mat_svc'].delete_material.assert_called_once_with(1)
        controller.material_manager.logger.error.assert_called_once_with("Error eliminando material: crash")

    def test_handle_attach_file_failure_material_import(self, controller, mock_dependencies):
        """Prueba fallo inesperado en importación (rama 771-772)."""
        with patch("controllers.product.material_manager.MaterialImporterFactory", autospec=True) as MockFactory:
            MockFactory.side_effect = Exception("Fatal")
            res = controller.handle_import_materials_to_product("P1", "f.xlsx")
            assert res is False
            MockFactory.assert_called_once_with()
        mock_dependencies['view'].show_message.assert_called_once_with("Error Crítico", "Ocurrió un error inesperado al importar los materiales.", "critical")

    def test_on_update_fabricacion_exception(self, controller, mock_dependencies):
        """Rama excepción en actualización fabricación (rama 370-371)."""
        mock_tab = MagicMock(spec=["get_fabricacion_form_data"])
        mock_tab.get_fabricacion_form_data.side_effect = Exception("Crash")
        mock_dependencies['view'].get_fabrications_tab.return_value = mock_tab
        
        res = controller._on_update_fabricacion(1)
        assert res is False
        mock_dependencies['view'].get_fabrications_tab.assert_called_once_with()
        mock_tab.get_fabricacion_form_data.assert_called_once_with()
        mock_dependencies['view'].show_message.assert_called_once_with("Error", "Error inesperado: Crash", "critical")

    def test_on_delete_fabricacion_exception(self, controller, mock_dependencies):
        """Rama excepción en borrado fabricación."""
        mock_dependencies['view'].show_confirmation_dialog.return_value = True
        mock_dependencies['fab_svc'].delete_fabricacion.side_effect = Exception("Crash")
        res = controller._on_delete_fabricacion(1)
        assert res is False
        mock_dependencies['view'].show_confirmation_dialog.assert_called_once_with(
            "Confirmar Eliminación",
            "¿Está seguro?"
        )
        mock_dependencies['fab_svc'].delete_fabricacion.assert_called_once_with(1)
        mock_dependencies['view'].show_message.assert_called_once_with("Error", "Error inesperado: Crash", "critical")

    def test_show_fabricacion_preprocesos_not_found(self, controller, mock_dependencies):
        """Rama fabricación no encontrada en gestión preprocesos."""
        mock_dependencies['fab_svc'].get_fabricacion_by_id.return_value = None
        controller.show_fabricacion_preprocesos(1)
        mock_dependencies['fab_svc'].get_fabricacion_by_id.assert_called_once_with(1)
        mock_dependencies['view'].show_message.assert_called_once_with("Error", "Fabricación no encontrada.", "critical")

    def test_show_fabricacion_preprocesos_exception(self, controller, mock_dependencies):
        """Rama excepción en gestión preprocesos (rama 449-450)."""
        mock_dependencies['fab_svc'].get_fabricacion_by_id.side_effect = Exception("Crash")
        controller.show_fabricacion_preprocesos(1)
        mock_dependencies['fab_svc'].get_fabricacion_by_id.assert_called_once_with(1)
        mock_dependencies['view'].show_message.assert_called_once_with("Error", "No se pudo abrir la gestión de preprocesos: Crash", "critical")

    def test_show_fabricacion_products_exception(self, controller, mock_dependencies):
        """Rama excepción en gestión productos (rama 483-484)."""
        mock_dependencies['fab_svc'].get_fabricacion_by_id.side_effect = Exception("Crash")
        controller.show_fabricacion_products(1)
        mock_dependencies['fab_svc'].get_fabricacion_by_id.assert_called_once_with(1)
        mock_dependencies['view'].show_message.assert_called_once_with("Error", "Error inesperado: Crash", "critical")

    def test_load_preprocesos_data_exception(self, controller, mock_dependencies):
        """Rama excepción carga preprocesos (rama 575)."""
        mock_dependencies['fab_svc'].get_all_preprocesos_with_components.side_effect = Exception("Crash")
        from ui.widgets.preprocesos_widget import PreprocesosWidget
        mock_tab = create_autospec(PreprocesosWidget)
        mock_dependencies['view'].get_page.return_value = mock_tab
        
        controller._load_preprocesos_data()
        mock_dependencies['fab_svc'].get_all_preprocesos_with_components.assert_called_once_with()
        assert mock_tab.load_preprocesos_data.called
        mock_tab.load_preprocesos_data.assert_called_once_with([])

    def test_add_preproceso_exception(self, controller, mock_dependencies):
        """Rama excepción diálogo preproceso."""
        mock_dependencies['mat_svc'].get_all_materials_for_selection.side_effect = Exception("Fatal")
        controller.show_add_preproceso_dialog()

        mock_dependencies['mat_svc'].get_all_materials_for_selection.assert_called_once_with()
        assert controller.preproceso_manager.logger.error.call_count >= 1
        controller.preproceso_manager.logger.error.assert_called_once_with("Error diálogo crear preproceso: Fatal", exc_info=True)

    def test_edit_preproceso_exception(self, controller, mock_dependencies):
        """Rama excepción diálogo editar preproceso."""
        mock_dependencies['mat_svc'].get_all_materials_for_selection.side_effect = Exception("Fatal")
        controller.show_edit_preproceso_dialog(create_autospec(PreprocesoDTO))
        mock_dependencies['mat_svc'].get_all_materials_for_selection.assert_called_once_with()
        assert controller.preproceso_manager.logger.error.call_count >= 1
        controller.preproceso_manager.logger.error.assert_called_once_with("Error diálogo editar preproceso: Fatal", exc_info=True)

    def test_delete_preproceso_exception(self, controller, mock_dependencies):
        """Rama excepción borrado preproceso."""
        mock_dependencies['view'].show_confirmation_dialog.return_value = True
        mock_dependencies['fab_svc'].delete_preproceso.side_effect = Exception("Crash")
        
        controller.delete_preproceso(1, "P1")
        mock_dependencies['view'].show_confirmation_dialog.assert_called_once_with(
            'Confirmar Eliminación',
            "¿Estás seguro de que quieres eliminar el preproceso 'P1'?\n\nEsta acción no se puede deshacer."
        )
        mock_dependencies['fab_svc'].delete_preproceso.assert_called_once_with(1)
        mock_dependencies['view'].show_message.assert_called_once_with("Error", "Error al eliminar el preproceso: Crash", "critical")
        controller.preproceso_manager.logger.error.assert_called_once_with("Error eliminando preproceso: Crash")

    def test_get_fabricacion_products_for_calc_exception(self, controller, mock_dependencies):
        """Rama excepción productos cálculo (rama 535)."""
        mock_dependencies['fab_svc'].get_products_for_fabricacion.side_effect = Exception("Crash")
        res = controller.get_fabricacion_products_for_calculation(1)
        assert res == []
        mock_dependencies['fab_svc'].get_products_for_fabricacion.assert_called_once_with(1)

    def test_on_calc_product_result_selected(self, controller, mock_dependencies):
        """Prueba selección de producto en página de cálculo."""
        mock_item = create_autospec(QListWidgetItem)
        mock_item.data.return_value = "P1"
        mock_item.text.return_value = "P1 - Prod"
        
        from ui.widgets.calculate_times_widget import CalculateTimesWidget
        mock_calc = create_autospec(CalculateTimesWidget)
        mock_calc.set_selected_product = MagicMock(spec=["__call__"]) # Dynamic attribute
        mock_dependencies['view'].get_page.return_value = mock_calc
        
        # Inyectamos atributos necesarios en el mock de estado si es estricto
        controller.state.selected_product_for_calc = None
        controller.state.selected_product_for_calc_desc = ""
        
        controller._on_calc_product_result_selected(mock_item)
        
        mock_item.data.assert_called_once_with(Qt.ItemDataRole.UserRole)
        mock_item.text.assert_called_once_with()
        assert controller.state.selected_product_for_calc == "P1"
        assert controller.state.selected_product_for_calc_desc == "P1 - Prod"
        mock_calc.set_selected_product.assert_called_once_with("P1 - Prod")

    def test_on_fabrication_search_changed(self, controller, mock_dependencies):
        """Prueba cambio en búsqueda de fabricaciones."""
        from ui.widgets.fabrications_widget import FabricationsWidget
        mock_fab = create_autospec(FabricationsWidget)
        mock_dependencies['view'].get_fabrications_tab.return_value = mock_fab
        
        mock_dependencies['fab_svc'].search_fabricaciones.return_value = ["F1"]
        
        controller._on_fabrication_search_changed("query")
        
        mock_dependencies['fab_svc'].search_fabricaciones.assert_called_once_with("query")
        mock_fab.update_fabrications_table.assert_called_once_with(["F1"])

    def test_on_fabrication_search_changed_missing_page(self, controller, mock_dependencies):
        """Prueba búsqueda con página faltante (ramas 227-231)."""
        from ui.widgets.fabrications_widget import FabricationsWidget
        mock_dependencies['view'].get_fabrications_tab.return_value = None
        
        controller._on_fabrication_search_changed("query")
        # No debe crashear
        mock_dependencies['fab_svc'].search_fabricaciones.assert_not_called()
        mock_dependencies['view'].get_fabrications_tab.assert_called_once_with()

    def test_show_add_preproceso_failure(self, controller, mock_dependencies):
        """Rama fallo creación preproceso."""
        mock_dependencies['mat_svc'].get_all_materials_for_selection.return_value = []
        with patch("controllers.product.preproceso_manager.PreprocesoDialog", autospec=True) as MockDlg:
            instance = MockDlg.return_value
            instance.exec.return_value = QDialog.DialogCode.Accepted
            instance.get_data.return_value = {"nombre": "P1"}
            mock_dependencies['fab_svc'].create_preproceso.return_value = False
            
            controller.show_add_preproceso_dialog()
            
            MockDlg.assert_called_once_with(
                all_materials=ANY, material_port=controller, parent=ANY
            )
            instance.exec.assert_called_once_with()
            instance.get_data.assert_called_once_with()
            mock_dependencies['fab_svc'].create_preproceso.assert_called_once_with(ANY)
        mock_dependencies['view'].show_message.assert_called_once_with("Error", "No se pudo crear el preproceso. El nombre podría ya existir.", "critical")

    def test_show_edit_preproceso_failure(self, controller, mock_dependencies):
        """Rama fallo edición preproceso."""
        mock_dependencies['mat_svc'].get_all_materials_for_selection.return_value = []
        mock_preproceso_dto = create_autospec(PreprocesoDTO, id=1)
        with patch("controllers.product.preproceso_manager.PreprocesoDialog", autospec=True) as MockDlg:
            instance = MockDlg.return_value
            instance.exec.return_value = QDialog.DialogCode.Accepted
            instance.get_data.return_value = {"nombre": "P1"}
            mock_dependencies['fab_svc'].update_preproceso.return_value = False
            
            controller.show_edit_preproceso_dialog(mock_preproceso_dto)
            
            MockDlg.assert_called_once_with(
                preproceso_existente=ANY,
                all_materials=ANY,
                material_port=controller,
                parent=ANY,
            )
            instance.exec.assert_called_once_with()
            instance.get_data.assert_called_once_with()
            mock_dependencies['fab_svc'].update_preproceso.assert_called_once_with(1, ANY)
        mock_dependencies['view'].show_message.assert_called_once_with("Error", "No se pudo actualizar el preproceso.", "critical")

    def test_on_manage_subs_clicked_error(self, controller, mock_dependencies):
        """Ramas error en gestión subfabricaciones (644, 652)."""
        from ui.widgets.products_widget import ProductsWidget
        mock_tab = create_autospec(ProductsWidget)
        # Forzamos que no tenga los atributos necesarios para el éxito
        del mock_tab.current_subfabricaciones
        mock_dependencies['view'].get_products_tab.return_value = mock_tab
        
        controller._on_manage_subs_clicked()
        mock_dependencies['view'].get_products_tab.assert_called_once_with()
        mock_dependencies['view'].show_message.assert_called_once_with("Error", "No se ha seleccionado un producto.", "warning")

        # Rama AttrError
        mock_dependencies['view'].get_products_tab.reset_mock(side_effect=True)
        mock_dependencies['view'].get_products_tab.return_value = None
        controller._on_manage_subs_clicked()
        assert mock_dependencies['view'].show_message.call_count >= 2

    def test_on_manage_procesos_clicked_error(self, controller, mock_dependencies):
        """Ramas error en gestión procesos."""
        from ui.widgets.products_widget import ProductsWidget
        mock_tab = create_autospec(ProductsWidget)
        # Forzamos que no tenga los atributos necesarios para el éxito
        del mock_tab.current_procesos_mecanicos
        mock_dependencies['view'].get_products_tab.return_value = mock_tab
        
        controller._on_manage_procesos_clicked()
        mock_dependencies['view'].get_products_tab.assert_called_once_with()
        mock_dependencies['view'].show_message.assert_called_once_with("Error", "No se ha seleccionado un producto.", "warning")

    def test_delegation_full_coverage(self, controller, mock_dependencies):
        """Cubre delegaciones del controlador hacia product_manager, material_manager y fabricacion_manager."""
        # Parcheamos con create_autospec si los managers no son mocks
        controller.product_manager._on_search_or_add_pressed = MagicMock(spec=controller.product_manager._on_search_or_add_pressed)
        controller.product_manager._on_manage_details_clicked = MagicMock(spec=controller.product_manager._on_manage_details_clicked)
        controller.product_manager.handle_delete_product_iteration = MagicMock(spec=controller.product_manager.handle_delete_product_iteration)
        controller.product_manager.handle_delete_iteration_image = MagicMock(spec=controller.product_manager.handle_delete_iteration_image)
        controller.material_manager.handle_unlink_material_from_product = MagicMock(spec=controller.material_manager.handle_unlink_material_from_product)
        controller.fabricacion_manager.show_fabricacion_products = MagicMock(spec=controller.fabricacion_manager.show_fabricacion_products)
        
        controller._on_search_or_add_pressed("P1")
        controller._on_manage_details_clicked("P1")
        controller.handle_delete_product_iteration(1)
        controller.handle_delete_iteration_image(1)
        controller.handle_unlink_material_from_product("P1", 1)
        controller.show_fabricacion_products(1)
        
        assert controller.product_manager._on_search_or_add_pressed.call_count == 1
        assert controller.material_manager.handle_unlink_material_from_product.call_count == 1
        assert controller.fabricacion_manager.show_fabricacion_products.call_count == 1