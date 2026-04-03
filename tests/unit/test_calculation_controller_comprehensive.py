# -*- coding: utf-8 -*-
"""
Tests unitarios para CalculationController.

Verifica cobertura completa del controlador de cálculo: inicialización,
conexión de señales, navegación, exportación, preprocesos y métodos auxiliares.
"""

from __future__ import annotations
import pytest
from unittest.mock import MagicMock, patch, create_autospec, ANY
from typing import cast
from typing import TYPE_CHECKING, Any, Dict

from controllers.calculation_controller import CalculationController
from ui.widgets.calculate_times_widget import CalculateTimesWidget
from core.dtos import ProductDTO, PreprocesoDTO, FabricacionProductoDTO, CalculationProductDTO

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_calc() -> MagicMock:
    """Crea un mock de CalculateTimesWidget con __class__ forzado para isinstance.
    
    Nota: No usa spec= porque CalculateTimesWidget es un widget Qt y los atributos
    dinámicos (_signals_connected, _pending_signal_connection) no están en la clase base.
    """
    mock_calc = MagicMock(
        spec=[
            # flags internos usados por el controlador
            "_signals_connected",
            "_pending_signal_connection",
            "_ui_setup_complete",
            # widgets/señales usadas en connect_calculate_signals
            "lote_search_entry",
            "add_lote_button",
            "remove_lote_button",
            "remove_item_button",
            "save_pila_button",
            "load_pila_button",
            "ver_bitacora_button",
            "manage_bitacora_button",
            "define_flow_button",
            "clear_simulation_button",
            "clear_button",
            "export_button",
            "export_pdf_button",
            "export_log_button",
            "home_button",
            "go_home_button",
            # audit export
            "last_audit",
            "audit_log_display",
            # preprocesos
            "add_step_to_pila",
            "lote_content_table",
        ]
    )
    cast(Any, mock_calc).__class__ = CalculateTimesWidget
    mock_calc.lote_content_table = MagicMock(spec=["setRowCount", "setItem", "rowCount", "columnCount"])
    return mock_calc


def _make_app(**extra_spec) -> MagicMock:
    """Crea un mock de AppController con spec mínimo."""
    spec = ['db', 'model', 'view', 'pila_controller', 'simulation_controller',
            'on_nav_button_clicked', '_on_nav_button_clicked', 'report_controller'] + list(extra_spec.keys())
    mock_app = MagicMock(spec=spec)
    mock_app.model = MagicMock(spec=['pila_service'])
    mock_app.model.pila_service = MagicMock(spec=['pilas_changed_signal'])
    mock_app.model.pila_service.pilas_changed_signal = MagicMock(spec=['connect'])
    mock_app.view = MagicMock(spec=['pages', 'show_message'])
    mock_app.view.pages = {}
    return mock_app


# ---------------------------------------------------------------------------
# TestCalculationControllerInit
# ---------------------------------------------------------------------------

class TestCalculationControllerInit:
    """Tests de inicialización de CalculationController."""

    def test_init_creates_dependencies(self) -> None:
        """Verifica que __init__ configura correctamente las dependencias."""
        mock_app = _make_app()
        controller = CalculationController(mock_app, mock_app.model.pila_service)

        assert controller.app is mock_app
        assert controller.db is mock_app.db
        assert controller.pila_service is mock_app.model.pila_service
        assert not hasattr(controller, 'model')
        assert controller.view is mock_app.view
        assert controller.logger is not None


# ---------------------------------------------------------------------------
# TestConnectCalculateSignals
# ---------------------------------------------------------------------------

class TestConnectCalculateSignals:
    """Tests para connect_calculate_signals."""

    @pytest.fixture
    def controller(self) -> CalculationController:
        """CalculationController con dependencias mockeadas estrictamente."""
        mock_app = MagicMock(spec=[
            'db', 'model', 'view', 'pila_controller', 'simulation_controller',
            '_on_export_gantt_to_pdf_clicked', '_on_nav_button_clicked', 'report_controller'
        ])
        mock_app.model = MagicMock(spec=['pila_service'])
        mock_app.model.pila_service = MagicMock(spec=['pilas_changed_signal', 'connect'])
        mock_app.model.pila_service.pilas_changed_signal = MagicMock(spec=["connect"])
        mock_app.view = MagicMock(spec=['pages', 'show_message'])
        mock_app.view.pages = {}
        mock_app.pila_controller = MagicMock(spec=[
            '_on_calc_lote_search_changed', '_on_add_lote_to_pila_clicked',
            '_on_remove_lote_from_pila_clicked', '_on_save_pila_clicked',
            '_on_load_pila_clicked', '_on_ver_bitacora_pila_clicked'
        ])
        mock_app.simulation_controller = MagicMock(spec=['_on_define_flow_clicked', '_on_clear_simulation'])
        mock_app.report_controller = MagicMock(spec=['on_export_to_excel_clicked'])
        return CalculationController(mock_app, mock_app.model.pila_service)

    def test_connect_signals_not_calculate_widget(self, controller: CalculationController) -> None:
        """Retorno temprano cuando calc_page no es CalculateTimesWidget."""
        cast(Any, controller.view).pages = {"calculate": None}
        controller.connect_calculate_signals()
        assert controller.view.pages.get("calculate") is None

    def test_connect_signals_ui_not_initialized(self, controller: CalculationController) -> None:
        """Retorno temprano cuando la UI no está inicializada."""
        mock_calc = _make_mock_calc()
        del mock_calc._ui_setup_complete
        cast(Any, controller.view).pages = {"calculate": mock_calc}

        controller.connect_calculate_signals()

        assert mock_calc._pending_signal_connection is True

    def test_connect_signals_widget_attribute_error(self, controller: CalculationController) -> None:
        """Retorno temprano cuando falta un widget requerido (AttributeError)."""
        mock_calc = _make_mock_calc()
        mock_calc._ui_setup_complete = True
        del mock_calc.lote_search_entry
        cast(Any, controller.view).pages = {"calculate": mock_calc}

        controller.connect_calculate_signals()

        assert mock_calc._signals_connected is not True

    def test_connect_signals_widget_none(self, controller: CalculationController) -> None:
        """Retorno temprano cuando el widget requerido es None."""
        mock_calc = _make_mock_calc()
        mock_calc._ui_setup_complete = True
        mock_calc.lote_search_entry = None
        cast(Any, controller.view).pages = {"calculate": mock_calc}

        controller.connect_calculate_signals()

        assert mock_calc._signals_connected is not True

    def test_connect_signals_widget_runtime_error(self, controller: CalculationController) -> None:
        """Retorno temprano cuando el objeto C++ subyacente fue eliminado."""
        mock_calc = _make_mock_calc()
        mock_calc._ui_setup_complete = True
        mock_calc.lote_search_entry = MagicMock(spec=['objectName'])
        mock_calc.lote_search_entry.objectName.side_effect = RuntimeError(
            "wrapped C/C++ object has been deleted"
        )
        cast(Any, controller.view).pages = {"calculate": mock_calc}

        controller.connect_calculate_signals()

        assert mock_calc._signals_connected is not True

    @patch('controllers.calculation_controller.getattr')
    def test_connect_signals_general_exception(
        self, mock_getattr: MagicMock, controller: CalculationController
    ) -> None:
        """Captura Exception durante la conexión de señales sin propagar."""
        mock_calc = _make_mock_calc()
        mock_calc._ui_setup_complete = True
        cast(Any, controller.view).pages = {"calculate": mock_calc}
        mock_calc.lote_search_entry.textChanged.connect.side_effect = Exception("Test error")

        controller.connect_calculate_signals()

        assert mock_calc._signals_connected is not True

    def test_connect_signals_runtime_error_in_connect(self, controller: CalculationController) -> None:
        """Captura RuntimeError durante la conexión de señales sin propagar."""
        mock_calc = _make_mock_calc()
        mock_calc._ui_setup_complete = True
        cast(Any, controller.view).pages = {"calculate": mock_calc}
        mock_calc.lote_search_entry.textChanged.connect.side_effect = RuntimeError("Test error")

        controller.connect_calculate_signals()

        assert mock_calc._signals_connected is not True

    def test_connect_signals_success(self, controller: CalculationController) -> None:
        """Conexión exitosa de señales — verifica lambdas conectadas."""
        mock_calc = _make_mock_calc()
        mock_calc._ui_setup_complete = True
        mock_calc._signals_connected = False
        cast(Any, controller.view).pages = {"calculate": mock_calc}

        controller.connect_calculate_signals()

        assert mock_calc._signals_connected is True

        # Lambda 1: export_button → report_controller.on_export_to_excel_clicked
        mock_calc.export_button.clicked.connect.call_args[0][0]()
        assert controller.app.report_controller is not None
        export_excel = cast(Any, controller.app.report_controller.on_export_to_excel_clicked)
        assert export_excel.call_count == 1
        export_excel.assert_called_once_with(mock_calc)

        # Lambda 2: pilas_changed_signal → view.show_message
        cast(Any, controller.pila_service.pilas_changed_signal.connect).call_args[0][0]("Título", "Mensaje")
        show_message = cast(Any, controller.view.show_message)
        assert show_message.call_count == 1
        show_message.assert_called_once_with("Título", "Mensaje", "info")


# ---------------------------------------------------------------------------
# TestNavigationMethods
# ---------------------------------------------------------------------------

class TestNavigationMethods:
    """Tests para métodos de navegación."""

    @pytest.fixture
    def controller(self) -> CalculationController:
        """CalculationController con simulation_controller mockeado."""
        mock_app = _make_app()
        mock_app.simulation_controller = MagicMock(spec=['_on_clear_simulation'])
        return CalculationController(mock_app, mock_app.model.pila_service)

    def test_on_go_home_and_reset_calc_with_sim_ctrl(self, controller: CalculationController) -> None:
        """Llama a simulation_controller y navega a home."""
        controller.on_go_home_and_reset_calc()

        sim_ctrl = cast(Any, controller.app.simulation_controller)
        clear_sim = cast(Any, sim_ctrl._on_clear_simulation)
        assert clear_sim.call_count == 1
        clear_sim.assert_called_once_with()
        on_nav = cast(Any, controller.app.on_nav_button_clicked)
        assert on_nav.call_count >= 1
        on_nav.assert_called_with("home")

    def test_on_go_home_and_reset_calc_without_sim_ctrl(self, controller: CalculationController) -> None:
        """Navega a home aunque no exista simulation_controller."""
        del controller.app.simulation_controller
        controller.on_go_home_and_reset_calc()

        on_nav = cast(Any, controller.app.on_nav_button_clicked)
        assert on_nav.call_count >= 1
        on_nav.assert_called_with("home")

    def test_on_calc_product_result_selected_with_item(self, controller: CalculationController) -> None:
        """Selección de producto válido — llama a text() del item."""
        mock_item = MagicMock(spec=['text'])
        mock_item.text.return_value = "Product A"

        controller.on_calc_product_result_selected(mock_item)

        assert mock_item.text.call_count == 1
        mock_item.text.assert_called_once_with()

    def test_on_calc_product_result_selected_no_item(self, controller: CalculationController) -> None:
        """Selección con None — retorna sin lanzar excepción."""
        controller.on_calc_product_result_selected(None)
        show_message = cast(Any, controller.view.show_message)
        assert show_message.call_count == 0
        show_message.assert_not_called()


# ---------------------------------------------------------------------------
# TestExportMethods
# ---------------------------------------------------------------------------

class TestExportMethods:
    """Tests para métodos de exportación."""

    @pytest.fixture
    def controller(self) -> CalculationController:
        """CalculationController con view mockeada."""
        mock_app = _make_app()
        return CalculationController(mock_app, mock_app.model.pila_service)

    def test_on_export_audit_log_no_widget(self, controller: CalculationController) -> None:
        """Muestra mensaje de error cuando el widget no está disponible."""
        cast(Any, controller.view).pages = {"calculate": None}

        controller.on_export_audit_log()

        show_message = cast(Any, controller.view.show_message)
        assert show_message.call_count == 1
        show_message.assert_called_once_with(ANY, ANY, ANY)

    def test_on_export_audit_log_no_last_audit(self, controller: CalculationController) -> None:
        """Muestra aviso cuando no hay datos de auditoría."""
        mock_calc = _make_mock_calc()
        mock_calc.last_audit = None
        cast(Any, controller.view).pages = {"calculate": mock_calc}

        controller.on_export_audit_log()

        show_message = cast(Any, controller.view.show_message)
        assert show_message.call_count == 1
        show_message.assert_called_once_with(
            "Sin Datos", "No hay un log de auditoría para exportar.", "warning"
        )

    @patch('controllers.calculation_controller.QFileDialog')
    def test_on_export_audit_log_cancelled(
        self, mock_dialog: MagicMock, controller: CalculationController
    ) -> None:
        """No muestra mensaje de éxito cuando el usuario cancela el diálogo."""
        mock_calc = _make_mock_calc()
        mock_calc.last_audit = True
        mock_calc.audit_log_display.toHtml.return_value = "<html></html>"
        cast(Any, controller.view).pages = {"calculate": mock_calc}
        mock_dialog.getSaveFileName.return_value = ("", "")

        controller.on_export_audit_log()

        show_message = cast(Any, controller.view.show_message)
        assert show_message.call_count == 0
        show_message.assert_not_called()

    @patch('controllers.calculation_controller.QFileDialog')
    @patch('builtins.open')
    def test_on_export_audit_log_success(
        self, mock_open: MagicMock, mock_dialog: MagicMock, controller: CalculationController
    ) -> None:
        """Muestra mensaje de éxito al guardar el log correctamente."""
        mock_calc = _make_mock_calc()
        mock_calc.last_audit = True
        mock_calc.audit_log_display.toHtml.return_value = "<html></html>"
        cast(Any, controller.view).pages = {"calculate": mock_calc}
        mock_dialog.getSaveFileName.return_value = ("/tmp/test.html", "")

        controller.on_export_audit_log()

        show_message = cast(Any, controller.view.show_message)
        assert show_message.call_count == 1
        show_message.assert_called_once_with(
            "Éxito", "Log de auditoría guardado en:\n/tmp/test.html", "info"
        )

    @patch('controllers.calculation_controller.QFileDialog')
    @patch('builtins.open')
    def test_on_export_audit_log_error(
        self, mock_open: MagicMock, mock_dialog: MagicMock, controller: CalculationController
    ) -> None:
        """Muestra mensaje de error cuando falla la escritura del archivo."""
        mock_calc = _make_mock_calc()
        mock_calc.last_audit = True
        mock_calc.audit_log_display.toHtml.return_value = "<html></html>"
        cast(Any, controller.view).pages = {"calculate": mock_calc}
        mock_dialog.getSaveFileName.return_value = ("/tmp/test.html", "")
        mock_open.side_effect = IOError("Write failed")

        controller.on_export_audit_log()

        show_message = cast(Any, controller.view.show_message)
        assert show_message.call_count == 1
        show_message.assert_called_once_with(
            "Error", "No se pudo guardar el archivo: Write failed", "critical"
        )


# ---------------------------------------------------------------------------
# TestPreprocesosMethods
# ---------------------------------------------------------------------------

class TestPreprocesosMethods:
    """Tests para métodos de preprocesos y pila, validando con DTOs."""

    @pytest.fixture
    def controller(self) -> CalculationController:
        """CalculationController con db y pila_service mockeados."""
        mock_app = _make_app()
        mock_app.db = MagicMock(spec=['preproceso_repo'])
        mock_app.db.preproceso_repo = MagicMock(spec=['get_products_for_fabricacion'])
        mock_app.model.pila_service = MagicMock(spec=['get_data_for_calculation'])
        return CalculationController(mock_app, mock_app.model.pila_service)

    def test_get_fabricacion_products_for_calculation_success(
        self, controller: CalculationController
    ) -> None:
        """Devuelve lista con cantidad_en_kit cuando hay productos y datos de cálculo."""
        from core.dtos import CalculationProductDTO
        mock_fp = MagicMock(spec=FabricacionProductoDTO)
        mock_fp.producto_codigo = "PROD001"
        mock_fp.cantidad = 5
        assert isinstance(mock_fp, FabricacionProductoDTO)

        cast(Any, controller.db.preproceso_repo.get_products_for_fabricacion).return_value = [mock_fp]
        
        dto = CalculationProductDTO(
            codigo="PROD001",
            descripcion="Product A",
            departamento="DEP1",
            tipo_trabajador=1,
            donde="Taller",
            tiene_subfabricaciones=False,
            tiempo_optimo=10.0,
            sub_partes=[]
        )
        cast(Any, controller.pila_service.get_data_for_calculation).return_value = [dto]

        result = controller.get_fabricacion_products_for_calculation(1)

        assert len(result) == 1
        assert result[0].cantidad_en_kit == 5
        assert result[0].descripcion == "Product A"
        get_products = cast(Any, controller.db.preproceso_repo.get_products_for_fabricacion)
        assert get_products.call_count == 1
        get_products.assert_called_once_with(1)

    def test_get_fabricacion_products_for_calculation_empty(
        self, controller: CalculationController
    ) -> None:
        """Devuelve lista vacía cuando no hay productos."""
        cast(Any, controller.db.preproceso_repo.get_products_for_fabricacion).return_value = []
        cast(Any, controller.pila_service.get_data_for_calculation).return_value = []

        result = controller.get_fabricacion_products_for_calculation(1)

        assert result == []

    def test_get_fabricacion_products_for_calculation_no_calc_data(
        self, controller: CalculationController
    ) -> None:
        """Devuelve lista vacía cuando get_data_for_calculation retorna vacío."""
        mock_dto = MagicMock(spec=FabricacionProductoDTO)
        mock_dto.producto_codigo = "PROD001"
        cast(Any, controller.db.preproceso_repo.get_products_for_fabricacion).return_value = [mock_dto]
        cast(Any, controller.pila_service.get_data_for_calculation).return_value = []

        result = controller.get_fabricacion_products_for_calculation(1)

        assert result == []

    def test_get_fabricacion_products_for_calculation_exception(
        self, controller: CalculationController
    ) -> None:
        """Devuelve lista vacía cuando ocurre una excepción."""
        controller.db.preproceso_repo.get_products_for_fabricacion.side_effect = Exception("DB error")

        result = controller.get_fabricacion_products_for_calculation(1)

        assert result == []

    def test_add_preprocesos_to_current_pila_no_widget(
        self, controller: CalculationController
    ) -> None:
        """Devuelve 0 cuando el widget no está disponible."""
        cast(Any, controller.view).pages = {"calculate": None}

        result = controller.add_preprocesos_to_current_pila(
            [
                CalculationProductDTO(
                    codigo="P1",
                    descripcion="Test",
                    departamento="D1",
                    tipo_trabajador=1,
                    donde="Taller",
                    tiene_subfabricaciones=False,
                    tiempo_optimo=1.0,
                    sub_partes=[],
                )
            ]
        )

        assert result == 0

    def test_add_preprocesos_to_current_pila_success(
        self, controller: CalculationController
    ) -> None:
        """Devuelve el número de preprocesos añadidos correctamente."""
        mock_calc = _make_mock_calc()
        mock_calc.add_step_to_pila.return_value = True
        cast(Any, controller.view).pages = {"calculate": mock_calc}

        preprocesos = [
            CalculationProductDTO(
                codigo="PREP_1",
                descripcion="Prep 1",
                departamento="Pre-Produccion",
                tipo_trabajador=1,
                donde="",
                tiene_subfabricaciones=True,
                tiempo_optimo=10.0,
                sub_partes=[]
            ),
            CalculationProductDTO(
                codigo="PREP_2",
                descripcion="Prep 2",
                departamento="Pre-Produccion",
                tipo_trabajador=1,
                donde="",
                tiene_subfabricaciones=True,
                tiempo_optimo=10.0,
                sub_partes=[]
            ),
        ]

        result = controller.add_preprocesos_to_current_pila(preprocesos)

        assert result == 2
        assert mock_calc.add_step_to_pila.call_count == 2

    def test_add_preprocesos_to_current_pila_exception(
        self, controller: CalculationController
    ) -> None:
        """Devuelve 0 cuando add_step_to_pila lanza excepción."""
        mock_calc = _make_mock_calc()
        mock_calc.add_step_to_pila.side_effect = Exception("Error")
        cast(Any, controller.view).pages = {"calculate": mock_calc}

        result = controller.add_preprocesos_to_current_pila(
            [CalculationProductDTO(codigo="T", descripcion="D", departamento="D", tipo_trabajador=1, donde="", tiene_subfabricaciones=False, tiempo_optimo=1, sub_partes=[])]
        )

        assert result == 0



# ---------------------------------------------------------------------------
# TestAuxiliaryMethods
# ---------------------------------------------------------------------------

class TestAuxiliaryMethods:
    """Tests para métodos auxiliares de actualización de UI."""

    @pytest.fixture
    def controller(self) -> CalculationController:
        """CalculationController con view mockeada."""
        mock_app = _make_app()
        return CalculationController(mock_app, mock_app.model.pila_service)

    def test_update_lote_content_table_no_widget(self, controller: CalculationController) -> None:
        """No lanza excepción cuando el widget no es CalculateTimesWidget."""
        cast(Any, controller.view).pages = {"calculate": "not_widget"}

        controller.update_lote_content_table()

        assert controller.view.pages.get("calculate") == "not_widget"

    def test_update_lote_content_table_success(self, controller: CalculationController) -> None:
        """Limpia la tabla de contenido del lote (setRowCount(0))."""
        mock_calc = _make_mock_calc()
        cast(Any, controller.view).pages = {"calculate": mock_calc}

        controller.update_lote_content_table()

        assert mock_calc.lote_content_table.setRowCount.call_count == 1
        mock_calc.lote_content_table.setRowCount.assert_called_once_with(0)

    def test_update_lote_content_table_exception(self, controller: CalculationController) -> None:
        """No propaga Exception cuando setRowCount falla."""
        mock_calc = _make_mock_calc()
        mock_calc.lote_content_table.setRowCount.side_effect = Exception("UI crash")
        cast(Any, controller.view).pages = {"calculate": mock_calc}

        controller.update_lote_content_table()  # no debe propagar

        assert mock_calc.lote_content_table.setRowCount.call_count == 1
        mock_calc.lote_content_table.setRowCount.assert_called_once_with(0)

    def test_update_calculate_page_lists_with_page(self, controller: CalculationController) -> None:
        """Llama a _update_plan_display con la página proporcionada."""
        mock_page = MagicMock(spec=CalculateTimesWidget)

        controller.update_calculate_page_lists(mock_page)

        assert mock_page._update_plan_display.call_count == 1
        mock_page._update_plan_display.assert_called_once_with()

    def test_update_calculate_page_lists_no_page(self, controller: CalculationController) -> None:
        """Obtiene la página internamente y llama a _update_plan_display."""
        mock_page = MagicMock(spec=CalculateTimesWidget)
        cast(Any, controller.view).pages = {"calculate": mock_page}

        controller.update_calculate_page_lists()

        assert mock_page._update_plan_display.call_count == 1
        mock_page._update_plan_display.assert_called_once_with()

    def test_update_calculate_page_lists_exception(self, controller: CalculationController) -> None:
        """No propaga Exception cuando _update_plan_display falla."""
        mock_page = MagicMock(spec=CalculateTimesWidget)
        mock_page._update_plan_display.side_effect = Exception("Method error")
        cast(Any, controller.view).pages = {"calculate": mock_page}

        controller.update_calculate_page_lists(mock_page)  # no debe propagar

        assert mock_page._update_plan_display.call_count == 1
        mock_page._update_plan_display.assert_called_once_with()

    def test_safe_update_calculate_page_success(self, controller: CalculationController) -> None:
        """Delega correctamente a update_calculate_page_lists."""
        mock_page = MagicMock(spec=CalculateTimesWidget)
        with patch.object(controller, 'update_calculate_page_lists') as mock_update:
            controller.safe_update_calculate_page(mock_page)

            assert mock_update.call_count == 1
            mock_update.assert_called_once_with(mock_page)

    def test_safe_update_calculate_page_none(self, controller: CalculationController) -> None:
        """Retorna sin error cuando recibe None."""
        controller.safe_update_calculate_page(None)
        assert controller.view.pages == {}

    def test_safe_update_calculate_page_runtime_error(self, controller: CalculationController) -> None:
        """No propaga RuntimeError."""
        mock_page = MagicMock(spec=CalculateTimesWidget)
        with patch.object(
            controller, 'update_calculate_page_lists', side_effect=RuntimeError("err")
        ):
            controller.safe_update_calculate_page(mock_page)  # no debe propagar

        assert controller.view.pages == {}

    def test_safe_update_calculate_page_attribute_error(self, controller: CalculationController) -> None:
        """No propaga AttributeError."""
        mock_page = MagicMock(spec=CalculateTimesWidget)
        with patch.object(
            controller, 'update_calculate_page_lists', side_effect=AttributeError("err")
        ):
            controller.safe_update_calculate_page(mock_page)  # no debe propagar

        assert controller.view.pages == {}
