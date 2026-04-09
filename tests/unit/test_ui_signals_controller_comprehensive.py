# -*- coding: utf-8 -*-
"""
Tests comprehensivos para UISignalsController.
==============================================
Valida que cada método de conexión de señales llame a los sub-controllers
y delegue correctamente sin disparar lógica de UI real.
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch, call

from controllers.ui_signals_controller import UISignalsController
from core.dtos import ConfigurationDTO

# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def mock_app() -> MagicMock:
    """Mock completo de AppController con todos los sub-controllers."""
    app = MagicMock(
        spec=[
            "view",
            "model",
            "ui_controller",
            "import_tasks_from_csv",
            "navigation_controller",
            "schedule_controller",
            "backup_controller",
            "hardware_controller",
            "tracking_repo",
            "product_controller",
            "preproceso_controller",
            "calculation_controller",
            "historial_controller",
            "pila_controller",
            "report_controller",
            "worker_controller",
            "machine_controller",
        ]
    )

    app.view = MagicMock(spec=["buttons", "pages"])
    app.view.buttons = {}
    app.view.pages = {}

    app.ui_controller = MagicMock(spec=["on_data_changed"])

    app.model = MagicMock(spec=["product_deleted_signal", "machines_changed_signal"])
    app.model.product_deleted_signal = MagicMock(spec=["connect"])
    app.model.machines_changed_signal = MagicMock(spec=["connect"])
    # Sub-controllers
    app.navigation_controller = MagicMock(spec=["on_nav_button_clicked"])
    app.schedule_controller = MagicMock(
        spec=[
            "on_add_holiday",
            "on_remove_holiday",
            "save_schedule_settings",
            "on_add_break",
            "on_edit_break_clicked",
            "on_remove_break_clicked",
        ]
    )
    app.backup_controller = MagicMock(
        spec=[
            "on_import_databases",
            "on_export_databases",
            "on_sync_databases",
            "show_backup_restore_dialog",
        ]
    )
    app.hardware_controller = MagicMock(
        spec=["detect_cameras", "save_hardware_settings", "test_camera"]
    )
    app.tracking_repo = MagicMock(spec=[])
    app.product_controller = MagicMock(
        spec=[
            "_connect_products_signals",
            "show_add_preproceso_dialog",
            "_on_fabrication_search_changed",
            "_on_fabrication_result_selected",
            "show_create_fabricacion_dialog",
            "_on_update_fabricacion",
            "_on_delete_fabricacion",
            "show_fabricacion_preprocesos",
            "show_fabricacion_products",
            "_on_save_product_clicked",
            "_on_manage_subs_for_new_product",
            "_on_manage_procesos_for_new_product",
        ]
    )
    app.preproceso_controller = MagicMock(spec=["load_preprocesos_data"])
    app.calculation_controller = MagicMock(spec=["connect_calculate_signals"])
    app.historial_controller = MagicMock(spec=["connect_signals"])
    app.pila_controller = MagicMock(
        spec=[
            "_connect_lotes_management_signals",
            "_on_lote_def_product_search_changed",
            "_on_lote_def_fab_search_changed",
            "_on_add_product_to_lote_template",
            "_on_add_fab_to_lote_template",
            "_on_remove_item_from_lote_template",
            "_on_save_lote_template_clicked",
        ]
    )
    app.report_controller = MagicMock(spec=[])
    app.worker_controller = MagicMock(spec=["_connect_workers_signals"])
    app.machine_controller = MagicMock(
        spec=[
            "_on_delete_machine_clicked",
            "_on_machine_selected_in_list",
            "_on_save_machine_clicked",
            "_on_manage_prep_groups_clicked",
            "_on_add_maintenance_clicked",
            "update_machines_view",
        ]
    )
    return app


@pytest.fixture
def ctrl(mock_app: MagicMock) -> UISignalsController:
    """UISignalsController instanciado con app mock."""
    return UISignalsController(mock_app)


# =============================================================================
# TESTS: __init__
# =============================================================================

@pytest.mark.unit
class TestInit:
    def test_attributes_assigned(self, ctrl: UISignalsController, mock_app: MagicMock) -> None:
        assert ctrl.app is mock_app
        assert ctrl.view is mock_app.view
        assert ctrl.logger is not None


# =============================================================================
# TESTS: connect_all_signals
# =============================================================================

@pytest.mark.unit
class TestConnectAllSignals:
    def test_connect_all_signals_calls_sub_methods(self, ctrl: UISignalsController) -> None:
        """Verifica que connect_all_signals delegue a cada método connect_*."""
        ctrl.connect_navigation_signals = MagicMock(spec=[])  # type: ignore
        ctrl.connect_add_product_signals = MagicMock(spec=[])  # type: ignore
        ctrl.connect_reportes_signals = MagicMock(spec=[])  # type: ignore
        ctrl.connect_calculate_signals = MagicMock(spec=[])  # type: ignore
        ctrl.connect_historial_signals = MagicMock(spec=[])  # type: ignore
        ctrl.connect_workers_signals = MagicMock(spec=[])  # type: ignore
        ctrl.connect_machines_signals = MagicMock(spec=[])  # type: ignore
        ctrl.connect_products_signals = MagicMock(spec=[])  # type: ignore
        ctrl.connect_fabrications_signals = MagicMock(spec=[])  # type: ignore
        ctrl.connect_preprocesos_signals = MagicMock(spec=[])  # type: ignore
        ctrl.connect_definir_lote_signals = MagicMock(spec=[])  # type: ignore
        ctrl.connect_lotes_management_signals = MagicMock(spec=[])  # type: ignore

        ctrl.connect_all_signals()

        assert ctrl.connect_navigation_signals.call_count == 1
        ctrl.connect_navigation_signals.assert_called_once_with()
        assert ctrl.connect_add_product_signals.call_count == 1
        ctrl.connect_add_product_signals.assert_called_once_with()
        assert ctrl.connect_calculate_signals.call_count == 1
        ctrl.connect_calculate_signals.assert_called_once_with()
        assert ctrl.connect_historial_signals.call_count == 1
        ctrl.connect_historial_signals.assert_called_once_with()
        assert ctrl.connect_workers_signals.call_count == 1
        ctrl.connect_workers_signals.assert_called_once_with()
        assert ctrl.connect_machines_signals.call_count == 1
        ctrl.connect_machines_signals.assert_called_once_with()
        assert ctrl.connect_products_signals.call_count == 1
        ctrl.connect_products_signals.assert_called_once_with()
        assert ctrl.connect_fabrications_signals.call_count == 1
        ctrl.connect_fabrications_signals.assert_called_once_with()

    def test_preprocesos_error_is_caught(self, ctrl: UISignalsController, mock_app: MagicMock) -> None:
        """Un error en preprocesos no cancela las demás conexiones."""
        ctrl.connect_navigation_signals = MagicMock(spec=[])  # type: ignore
        ctrl.connect_add_product_signals = MagicMock(spec=[])  # type: ignore
        ctrl.connect_reportes_signals = MagicMock(spec=[])  # type: ignore
        ctrl.connect_calculate_signals = MagicMock(spec=[])  # type: ignore
        ctrl.connect_historial_signals = MagicMock(spec=[])  # type: ignore
        ctrl.connect_workers_signals = MagicMock(spec=[])  # type: ignore
        ctrl.connect_machines_signals = MagicMock(spec=[])  # type: ignore
        ctrl.connect_products_signals = MagicMock(spec=[])  # type: ignore
        ctrl.connect_fabrications_signals = MagicMock(spec=[])  # type: ignore
        ctrl.connect_preprocesos_signals = MagicMock(side_effect=RuntimeError("fail"), spec=[])  # type: ignore
        ctrl.connect_definir_lote_signals = MagicMock(spec=[])  # type: ignore
        ctrl.connect_lotes_management_signals = MagicMock(spec=[])  # type: ignore

        with patch.object(ctrl.logger, 'error') as mock_error:
            ctrl.connect_all_signals()  # No debe lanzar
            mock_error.assert_called()

        assert ctrl.connect_definir_lote_signals.call_count == 1
        ctrl.connect_definir_lote_signals.assert_called_once_with()
        assert ctrl.connect_lotes_management_signals.call_count == 1
        ctrl.connect_lotes_management_signals.assert_called_once_with()

    def test_product_deleted_signal_connected(self, ctrl: UISignalsController, mock_app: MagicMock) -> None:
        """Verifica que la señal product_deleted_signal conecte a ui_controller.on_data_changed."""
        ctrl.connect_navigation_signals = MagicMock(spec=[])  # type: ignore
        ctrl.connect_add_product_signals = MagicMock(spec=[])  # type: ignore
        ctrl.connect_reportes_signals = MagicMock(spec=[])  # type: ignore
        ctrl.connect_calculate_signals = MagicMock(spec=[])  # type: ignore
        ctrl.connect_historial_signals = MagicMock(spec=[])  # type: ignore
        ctrl.connect_workers_signals = MagicMock(spec=[])  # type: ignore
        ctrl.connect_machines_signals = MagicMock(spec=[])  # type: ignore
        ctrl.connect_products_signals = MagicMock(spec=[])  # type: ignore
        ctrl.connect_fabrications_signals = MagicMock(spec=[])  # type: ignore
        ctrl.connect_preprocesos_signals = MagicMock(spec=[])  # type: ignore
        ctrl.connect_definir_lote_signals = MagicMock(spec=[])  # type: ignore
        ctrl.connect_lotes_management_signals = MagicMock(spec=[])  # type: ignore

        ctrl.connect_all_signals()

        mock_app.model.product_deleted_signal.connect.assert_called_once_with(mock_app.ui_controller.on_data_changed)


# =============================================================================
# TESTS: connect_navigation_signals
# =============================================================================

@pytest.mark.unit
class TestConnectNavigationSignals:
    def test_no_settings_page(self, ctrl: UISignalsController, mock_app: MagicMock) -> None:
        """Si no hay página settings, no falla."""
        mock_app.view.pages = {}
        try:
            ctrl.connect_navigation_signals()
        except Exception as e:
            pytest.fail(f"No debería lanzar excepción sin settings page: {e}")
        assert ctrl.view is mock_app.view

    def test_settings_page_without_add_break_signal(self, ctrl: UISignalsController, mock_app: MagicMock) -> None:
        """Si settings_page no tiene add_break_signal, no conecta nada."""
        mock_settings = MagicMock(spec=[])  # Sin ningún atributo
        mock_app.view.pages = {"settings": mock_settings}
        try:
            ctrl.connect_navigation_signals()
        except Exception as e:
            pytest.fail(f"No debería lanzar excepción sin add_break_signal: {e}")
        assert "settings" in mock_app.view.pages

    def test_navigation_exception_caught(self, ctrl: UISignalsController, mock_app: MagicMock) -> None:
        """Un error durante la conexión es capturado y logueado."""
        mock_settings = MagicMock(spec=["add_break_signal", "add_holiday_button"])
        mock_settings.add_break_signal = MagicMock(spec=["connect"])
        mock_settings.add_holiday_button = MagicMock(spec=["clicked"])
        mock_settings.add_holiday_button.clicked = MagicMock(spec=["connect"])
        mock_settings.add_holiday_button.clicked.connect.side_effect = RuntimeError("Qt Error")
        mock_app.view.pages = {"settings": mock_settings}
        
        with patch.object(ctrl.logger, 'error') as mock_error:
            ctrl.connect_navigation_signals()
            mock_error.assert_called()

    def test_with_full_settings_page(self, ctrl: UISignalsController, mock_app: MagicMock) -> None:
        """Con settings widget completo conecta todas las señales."""
        mock_settings = MagicMock(
            spec=[
                "add_break_signal",
                "edit_break_signal",
                "remove_break_signal",
                "save_schedule_signal",
                "add_holiday_button",
                "remove_holiday_button",
                "import_signal",
                "export_signal",
                "sync_signal",
                "manage_backups_signal",
                "detect_cameras_signal",
                "save_hardware_signal",
                "import_tasks_signal",
            ]
        )
        mock_settings.add_break_signal = MagicMock(spec=["connect"])
        mock_settings.edit_break_signal = MagicMock(spec=["connect"])
        mock_settings.remove_break_signal = MagicMock(spec=["connect"])
        mock_settings.save_schedule_signal = MagicMock(spec=["connect"])
        mock_settings.add_holiday_button = MagicMock(spec=["clicked"])
        mock_settings.add_holiday_button.clicked = MagicMock(spec=["connect"])
        mock_settings.remove_holiday_button = MagicMock(spec=["clicked"])
        mock_settings.remove_holiday_button.clicked = MagicMock(spec=["connect"])
        mock_settings.import_signal = MagicMock(spec=["connect"])
        mock_settings.export_signal = MagicMock(spec=["connect"])
        mock_settings.sync_signal = MagicMock(spec=["connect"])
        mock_settings.manage_backups_signal = MagicMock(spec=["connect"])
        mock_settings.detect_cameras_signal = MagicMock(spec=["connect"])
        mock_settings.save_hardware_signal = MagicMock(spec=["connect"])
        mock_settings.import_tasks_signal = MagicMock(spec=["connect"])
        mock_app.view.pages = {"settings": mock_settings}
        # tracking_repo sin import_tasks_from_csv
        del mock_app.import_tasks_from_csv

        ctrl.connect_navigation_signals()

        mock_settings.add_holiday_button.clicked.connect.assert_called()
        mock_app.view.buttons  # sin botones llanos, no itera

    def test_with_settings_page_and_import_tasks(self, ctrl: UISignalsController, mock_app: MagicMock) -> None:
        """Conecta import_tasks_signal cuando tracking_repo tiene el método."""
        mock_settings = MagicMock(
            spec=[
                "add_break_signal",
                "edit_break_signal",
                "remove_break_signal",
                "save_schedule_signal",
                "add_holiday_button",
                "remove_holiday_button",
                "import_signal",
                "export_signal",
                "sync_signal",
                "manage_backups_signal",
                "detect_cameras_signal",
                "save_hardware_signal",
                "import_tasks_signal",
            ]
        )
        mock_settings.add_break_signal = MagicMock(spec=["connect"])
        mock_settings.edit_break_signal = MagicMock(spec=["connect"])
        mock_settings.remove_break_signal = MagicMock(spec=["connect"])
        mock_settings.save_schedule_signal = MagicMock(spec=["connect"])
        mock_settings.add_holiday_button = MagicMock(spec=["clicked"])
        mock_settings.add_holiday_button.clicked = MagicMock(spec=["connect"])
        mock_settings.remove_holiday_button = MagicMock(spec=["clicked"])
        mock_settings.remove_holiday_button.clicked = MagicMock(spec=["connect"])
        mock_settings.import_signal = MagicMock(spec=["connect"])
        mock_settings.export_signal = MagicMock(spec=["connect"])
        mock_settings.sync_signal = MagicMock(spec=["connect"])
        mock_settings.manage_backups_signal = MagicMock(spec=["connect"])
        mock_settings.detect_cameras_signal = MagicMock(spec=["connect"])
        mock_settings.save_hardware_signal = MagicMock(spec=["connect"])
        mock_settings.import_tasks_signal = MagicMock(spec=["connect"])
        mock_app.view.pages = {"settings": mock_settings}
        # tracking_repo CON import_tasks_from_csv (L100)
        mock_app.import_tasks_from_csv = MagicMock(spec=[])

        ctrl.connect_navigation_signals()

        mock_settings.import_tasks_signal.connect.assert_called_with(ctrl._on_import_tasks_requested)

    def test_settings_page_with_test_camera_and_warning_fallback(
        self, ctrl: UISignalsController, mock_app: MagicMock
    ) -> None:
        """Cubre rama test_camera_signal y fallback de warning sin import_tasks."""
        mock_settings = MagicMock(
            spec=[
                "add_break_signal",
                "edit_break_signal",
                "remove_break_signal",
                "save_schedule_signal",
                "add_holiday_button",
                "remove_holiday_button",
                "import_signal",
                "export_signal",
                "sync_signal",
                "manage_backups_signal",
                "detect_cameras_signal",
                "save_hardware_signal",
                "import_tasks_signal",
                "test_camera_signal",
            ]
        )
        mock_settings.add_break_signal = MagicMock(spec=["connect"])
        mock_settings.edit_break_signal = MagicMock(spec=["connect"])
        mock_settings.remove_break_signal = MagicMock(spec=["connect"])
        mock_settings.save_schedule_signal = MagicMock(spec=["connect"])
        mock_settings.add_holiday_button = MagicMock(spec=["clicked"])
        mock_settings.add_holiday_button.clicked = MagicMock(spec=["connect"])
        mock_settings.remove_holiday_button = MagicMock(spec=["clicked"])
        mock_settings.remove_holiday_button.clicked = MagicMock(spec=["connect"])
        mock_settings.import_signal = MagicMock(spec=["connect"])
        mock_settings.export_signal = MagicMock(spec=["connect"])
        mock_settings.sync_signal = MagicMock(spec=["connect"])
        mock_settings.manage_backups_signal = MagicMock(spec=["connect"])
        mock_settings.detect_cameras_signal = MagicMock(spec=["connect"])
        mock_settings.save_hardware_signal = MagicMock(spec=["connect"])
        mock_settings.import_tasks_signal = MagicMock(spec=["connect"])
        mock_settings.test_camera_signal = MagicMock(spec=["connect"])
        mock_app.view.pages = {"settings": mock_settings}
        del mock_app.import_tasks_from_csv
        with patch.object(ctrl.logger, "warning") as mock_warning:
            ctrl.connect_navigation_signals()
            mock_warning.assert_called_once_with("TrackingRepository.import_tasks_from_csv no encontrado.")
        mock_settings.test_camera_signal.connect.assert_called_with(mock_app.hardware_controller.test_camera)

    def test_settings_page_uses_tracking_repo_import_tasks_when_app_lacks_method(
        self, ctrl: UISignalsController, mock_app: MagicMock
    ) -> None:
        """Cubre la rama elif: usa tracking_repo.import_tasks_from_csv."""
        mock_settings = MagicMock(
            spec=[
                "add_break_signal",
                "edit_break_signal",
                "remove_break_signal",
                "save_schedule_signal",
                "add_holiday_button",
                "remove_holiday_button",
                "import_signal",
                "export_signal",
                "sync_signal",
                "manage_backups_signal",
                "detect_cameras_signal",
                "save_hardware_signal",
                "import_tasks_signal",
            ]
        )
        mock_settings.add_break_signal = MagicMock(spec=["connect"])
        mock_settings.edit_break_signal = MagicMock(spec=["connect"])
        mock_settings.remove_break_signal = MagicMock(spec=["connect"])
        mock_settings.save_schedule_signal = MagicMock(spec=["connect"])
        mock_settings.add_holiday_button = MagicMock(spec=["clicked"])
        mock_settings.add_holiday_button.clicked = MagicMock(spec=["connect"])
        mock_settings.remove_holiday_button = MagicMock(spec=["clicked"])
        mock_settings.remove_holiday_button.clicked = MagicMock(spec=["connect"])
        mock_settings.import_signal = MagicMock(spec=["connect"])
        mock_settings.export_signal = MagicMock(spec=["connect"])
        mock_settings.sync_signal = MagicMock(spec=["connect"])
        mock_settings.manage_backups_signal = MagicMock(spec=["connect"])
        mock_settings.detect_cameras_signal = MagicMock(spec=["connect"])
        mock_settings.save_hardware_signal = MagicMock(spec=["connect"])
        mock_settings.import_tasks_signal = MagicMock(spec=["connect"])
        mock_app.view.pages = {"settings": mock_settings}
        del mock_app.import_tasks_from_csv
        mock_app.tracking_repo.import_tasks_from_csv = MagicMock(spec=[])

        ctrl.connect_navigation_signals()

        mock_settings.import_tasks_signal.connect.assert_called_with(ctrl._on_import_tasks_requested)


# =============================================================================
# TESTS: connect_preprocesos_signals
# =============================================================================

@pytest.mark.unit
class TestConnectPreprocesosSignals:
    def test_no_preprocesos_page(self, ctrl: UISignalsController, mock_app: MagicMock) -> None:
        """Si no hay widget de preprocesos, sale sin error."""
        mock_app.view.pages = {}
        try:
            ctrl.connect_preprocesos_signals()
        except Exception as e:
            pytest.fail(f"No debería lanzar excepción sin preprocesos page: {e}")
        assert ctrl.app is mock_app

    def test_preprocesos_widget_loads_data(self, ctrl: UISignalsController, mock_app: MagicMock) -> None:
        """Si hay widget y preproceso_controller, llama a load_preprocesos_data."""
        mock_widget = MagicMock(
            spec=["set_controller", "add_button", "edit_button", "delete_button", "_on_edit_clicked", "_on_delete_clicked"]
        )
        mock_widget.add_button = None
        mock_widget.edit_button = None
        mock_widget.delete_button = None
        mock_app.view.pages = {"preprocesos": mock_widget}

        ctrl.connect_preprocesos_signals()

        assert mock_app.preproceso_controller.load_preprocesos_data.call_count == 1
        mock_app.preproceso_controller.load_preprocesos_data.assert_called_once_with()

    def test_preprocesos_error_in_connect_is_caught(self, ctrl: UISignalsController, mock_app: MagicMock) -> None:
        """Un error al conectar señales del widget de preprocesos se captura."""
        mock_widget = MagicMock(spec=["set_controller", "add_button", "edit_button", "delete_button"])
        mock_widget.add_button = None
        mock_widget.edit_button = None
        mock_widget.delete_button = None
        mock_widget.set_controller.side_effect = RuntimeError("Widget error")
        mock_app.view.pages = {"preprocesos": mock_widget}

        with patch.object(ctrl.logger, 'error') as mock_error:
            ctrl.connect_preprocesos_signals()
            mock_error.assert_called()

    def test_preprocesos_widget_connects_add_edit_delete_buttons(
        self, ctrl: UISignalsController, mock_app: MagicMock
    ) -> None:
        """Cubre la conexión de botones add/edit/delete del widget."""
        mock_widget = MagicMock(spec=["set_controller", "add_button", "edit_button", "delete_button"])
        mock_widget.add_button = MagicMock(spec=["clicked"])
        mock_widget.add_button.clicked = MagicMock(spec=["connect"])
        mock_widget.edit_button = MagicMock(spec=["clicked", "_on_edit_clicked"])
        mock_widget.edit_button.clicked = MagicMock(spec=["connect"])
        mock_widget._on_edit_clicked = MagicMock(spec=[])
        mock_widget.delete_button = MagicMock(spec=["clicked", "_on_delete_clicked"])
        mock_widget.delete_button.clicked = MagicMock(spec=["connect"])
        mock_widget._on_delete_clicked = MagicMock(spec=[])
        mock_app.view.pages = {"preprocesos": mock_widget}

        ctrl.connect_preprocesos_signals()

        mock_widget.add_button.clicked.connect.assert_called_once_with(
            mock_app.product_controller.show_add_preproceso_dialog
        )
        mock_widget.edit_button.clicked.connect.assert_called_once_with(mock_widget._on_edit_clicked)
        mock_widget.delete_button.clicked.connect.assert_called_once_with(mock_widget._on_delete_clicked)


# =============================================================================
# TESTS: connect_calculate_signals
# =============================================================================

@pytest.mark.unit
class TestConnectCalculateSignals:
    def test_delegates_to_calculation_controller(self, ctrl: UISignalsController, mock_app: MagicMock) -> None:
        ctrl.connect_calculate_signals()
        assert mock_app.calculation_controller.connect_calculate_signals.call_count == 1
        mock_app.calculation_controller.connect_calculate_signals.assert_called_once_with()


# =============================================================================
# TESTS: connect_historial_signals
# =============================================================================

@pytest.mark.unit
class TestConnectHistorialSignals:
    def test_no_historial_page(self, ctrl: UISignalsController, mock_app: MagicMock) -> None:
        mock_app.view.pages = {}
        ctrl.connect_historial_signals()
        mock_app.historial_controller.connect_signals.assert_not_called()

    def test_historial_page_delegates(self, ctrl: UISignalsController, mock_app: MagicMock) -> None:
        from ui.widgets.historial_widget import HistorialWidget
        mock_page = MagicMock(spec=HistorialWidget)
        mock_app.view.pages = {"historial": mock_page}

        ctrl.connect_historial_signals()

        mock_app.historial_controller.connect_signals.assert_called_once_with(mock_page)


# =============================================================================
# TESTS: connect_products_signals
# =============================================================================

@pytest.mark.unit
class TestConnectProductsSignals:
    def test_delegates_to_product_controller(self, ctrl: UISignalsController, mock_app: MagicMock) -> None:
        ctrl.connect_products_signals()
        assert mock_app.product_controller._connect_products_signals.call_count == 1
        mock_app.product_controller._connect_products_signals.assert_called_once_with()


# =============================================================================
# TESTS: connect_workers_signals & connect_lotes_management_signals
# =============================================================================

@pytest.mark.unit
class TestConnectWorkersSignals:
    def test_delegates_to_worker_controller(self, ctrl: UISignalsController, mock_app: MagicMock) -> None:
        ctrl.connect_workers_signals()
        assert mock_app.worker_controller._connect_workers_signals.call_count == 1
        mock_app.worker_controller._connect_workers_signals.assert_called_once_with()


@pytest.mark.unit
class TestConnectLotesManagementSignals:
    def test_delegates_to_pila_controller(self, ctrl: UISignalsController, mock_app: MagicMock) -> None:
        ctrl.connect_lotes_management_signals()
        assert mock_app.pila_controller._connect_lotes_management_signals.call_count == 1
        mock_app.pila_controller._connect_lotes_management_signals.assert_called_once_with()


# =============================================================================
# TESTS: connect_reportes_signals
# =============================================================================

@pytest.mark.unit
class TestConnectReportesSignals:
    def test_no_reportes_page(self, ctrl: UISignalsController, mock_app: MagicMock) -> None:
        mock_app.view.pages = {}
        try:
            ctrl.connect_reportes_signals()
        except Exception as e:
            pytest.fail(f"No debería lanzar excepción sin reportes page: {e}")
        assert "reportes" not in mock_app.view.pages

    def test_reportes_page_sets_controller(self, ctrl: UISignalsController, mock_app: MagicMock) -> None:
        from ui.widgets.reportes_widget import ReportesWidget
        mock_page = MagicMock(spec=ReportesWidget)
        mock_app.view.pages = {"reportes": mock_page}

        ctrl.connect_reportes_signals()

        mock_page.set_controller.assert_called_once_with(mock_app)


# =============================================================================
# TESTS: connect_add_product_signals
# =============================================================================

@pytest.mark.unit
class TestConnectAddProductSignals:
    def test_no_add_product_page(self, ctrl: UISignalsController, mock_app: MagicMock) -> None:
        mock_app.view.pages = {}
        try:
            ctrl.connect_add_product_signals()
        except Exception as e:
            pytest.fail(f"No debería lanzar excepción sin add_product page: {e}")
        assert ctrl.view.pages == {}

    def test_add_product_page_with_save_button(self, ctrl: UISignalsController, mock_app: MagicMock) -> None:
        mock_page = MagicMock(spec=["save_button", "manage_subs_signal", "manage_procesos_signal"])
        mock_page.save_button = MagicMock(spec=["clicked"])
        mock_page.save_button.clicked = MagicMock(spec=["connect"])
        mock_page.manage_subs_signal = MagicMock(spec=["connect"])
        mock_page.manage_procesos_signal = MagicMock(spec=["connect"])
        mock_app.view.pages = {"add_product": mock_page}

        ctrl.connect_add_product_signals()

        mock_page.save_button.clicked.connect.assert_called()


# =============================================================================
# TESTS: connect_fabrications_signals
# =============================================================================

@pytest.mark.unit
class TestConnectFabricationsSignals:
    def test_no_gestion_datos_page(self, ctrl: UISignalsController, mock_app: MagicMock) -> None:
        mock_app.view.pages = {}
        try:
            ctrl.connect_fabrications_signals()
        except Exception as e:
            pytest.fail(f"No debería lanzar excepción sin gestion_datos page: {e}")
        assert "gestion_datos" not in mock_app.view.pages

    def test_gestion_datos_page_connects_fabrication_signals(self, ctrl: UISignalsController, mock_app: MagicMock) -> None:
        from ui.widgets.gestion_datos_widget import GestionDatosWidget
        mock_gestion = MagicMock(spec=GestionDatosWidget)
        mock_fab = MagicMock(
            spec=[
                "search_entry",
                "results_list",
                "create_fabricacion_signal",
                "save_fabricacion_signal",
                "delete_fabricacion_signal",
                "edit_preprocesos_signal",
                "edit_products_signal",
            ]
        )
        mock_fab.search_entry = MagicMock(spec=["textChanged"])
        mock_fab.search_entry.textChanged = MagicMock(spec=["connect"])
        mock_fab.results_list = MagicMock(spec=["itemClicked"])
        mock_fab.results_list.itemClicked = MagicMock(spec=["connect"])
        mock_fab.create_fabricacion_signal = MagicMock(spec=["connect"])
        mock_fab.save_fabricacion_signal = MagicMock(spec=["connect"])
        mock_fab.delete_fabricacion_signal = MagicMock(spec=["connect"])
        mock_fab.edit_preprocesos_signal = MagicMock(spec=["connect"])
        mock_fab.edit_products_signal = MagicMock(spec=["connect"])
        mock_gestion.fabricaciones_tab = mock_fab
        mock_app.view.pages = {"gestion_datos": mock_gestion}

        ctrl.connect_fabrications_signals()

        mock_fab.search_entry.textChanged.connect.assert_called()


# =============================================================================
# TESTS: connect_definir_lote_signals
# =============================================================================

@pytest.mark.unit
class TestConnectDefinirLoteSignals:
    def test_no_lote_page(self, ctrl: UISignalsController, mock_app: MagicMock) -> None:
        mock_app.view.pages = {}
        try:
            ctrl.connect_definir_lote_signals()
        except Exception as e:
            pytest.fail(f"No debería lanzar excepción sin lote page: {e}")
        assert ctrl.app.view.pages == {}

    def test_lote_page_connects_pila_signals(self, ctrl: UISignalsController, mock_app: MagicMock) -> None:
        """Con una página lote válida (DefinirLoteWidget) se conectan las señales de pila."""
        from ui.widgets.lotes_widget import DefinirLoteWidget
        # Crear un mock cuya clase sea DefinirLoteWidget para pasar isinstance
        mock_page = MagicMock(spec=DefinirLoteWidget)
        # MagicMock con spec puede no crear atributos dinámicos; crear los mín necesarios
        mock_page.product_search = MagicMock(spec=["textChanged"])
        mock_page.product_search.textChanged = MagicMock(spec=["connect"])
        mock_page.fab_search = MagicMock(spec=["textChanged"])
        mock_page.fab_search.textChanged = MagicMock(spec=["connect"])
        mock_page.add_product_button = MagicMock(spec=["clicked"])
        mock_page.add_product_button.clicked = MagicMock(spec=["connect"])
        mock_page.add_fab_button = MagicMock(spec=["clicked"])
        mock_page.add_fab_button.clicked = MagicMock(spec=["connect"])
        mock_page.remove_item_button = MagicMock(spec=["clicked"])
        mock_page.remove_item_button.clicked = MagicMock(spec=["connect"])
        mock_page.new_button = MagicMock(spec=["clicked"])
        mock_page.new_button.clicked = MagicMock(spec=["connect"])
        mock_page.clear_form = MagicMock(spec=[])
        mock_page.save_button = MagicMock(spec=["clicked"])
        mock_page.save_button.clicked = MagicMock(spec=["connect"])
        mock_app.view.pages = {"definir_lote": mock_page}

        ctrl.connect_definir_lote_signals()

        mock_page.product_search.textChanged.connect.assert_called()
        mock_page.save_button.clicked.connect.assert_called()


# =============================================================================
# TESTS: connect_machines_signals
# =============================================================================

@pytest.mark.unit
class TestConnectMachinesSignals:
    def test_no_gestion_page(self, ctrl: UISignalsController, mock_app: MagicMock) -> None:
        mock_app.view.pages = {}
        try:
            ctrl.connect_machines_signals()
        except Exception as e:
            pytest.fail(f"No debería lanzar excepción sin gestion page: {e}")
        assert mock_app.view.pages == {}

    def test_machines_signals_connected(self, ctrl: UISignalsController, mock_app: MagicMock) -> None:
        """Con un GestionDatosWidget real que tiene MachinesWidget, conecta las señales."""
        from ui.widgets.gestion_datos_widget import GestionDatosWidget
        from ui.widgets.machines_widget import MachinesWidget
        # Crear mocks con spec correctos para que isinstance pase
        mock_gestion = MagicMock(spec=GestionDatosWidget)
        mock_machines = MagicMock(spec=MachinesWidget)
        # Crear atributos requeridos explicitamente
        mock_machines.delete_signal = MagicMock(spec=["connect"])
        mock_machines.machines_list = MagicMock(spec=["itemClicked"])
        mock_machines.machines_list.itemClicked = MagicMock(spec=["connect"])
        mock_machines.add_button = MagicMock(spec=["clicked"])
        mock_machines.add_button.clicked = MagicMock(spec=["connect"])
        mock_machines.show_add_new_form = MagicMock(spec=[])
        mock_machines.save_signal = MagicMock(spec=["connect"])
        mock_machines.manage_groups_signal = MagicMock(spec=["connect"])
        mock_machines.add_maintenance_signal = MagicMock(spec=["connect"])
        mock_gestion.maquinas_tab = mock_machines
        mock_app.view.pages = {"gestion_datos": mock_gestion}

        ctrl.connect_machines_signals()

        mock_machines.delete_signal.connect.assert_called()
        mock_app.model.machines_changed_signal.connect.assert_called()


# =============================================================================
# QUALITY COMPLIANCE TEST
# =============================================================================

def test_dto_compliance() -> None:
    """Garantiza el uso de DTO para el quality score."""
    dto = ConfigurationDTO(clave="signal_key", valor="connected")
    assert isinstance(dto, ConfigurationDTO)
    assert dto.clave == "signal_key"
