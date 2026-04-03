# -*- coding: utf-8 -*-
"""Tests de orquestación y compatibilidad para AppController."""

from __future__ import annotations

from typing import Any, Dict, List, cast
from unittest.mock import MagicMock, patch, ANY

import pytest

from controllers.app_controller import AppController
from core.dtos import FlowTaskDataDTO, FlowTaskConfigDTO, ProductionFlowStepDTO


def _make_model() -> Any:
    model = MagicMock(spec=["db", "product_service"])
    model.db = MagicMock(spec=[])
    model.product_service = MagicMock(spec=["search_products"])
    model.product_service.search_products = MagicMock(return_value=["P1"])
    return model


def _make_view() -> Any:
    view = MagicMock(spec=["pages", "get_page"])
    view.pages = {}
    view.get_page = MagicMock(return_value=None)
    return view


@pytest.fixture
def controller() -> AppController:
    model = _make_model()
    view = _make_view()
    schedule_manager = MagicMock(spec=[])
    with patch("controllers.startup_controller.StartupController", autospec=True), patch(
        "controllers.ui_signals_controller.UISignalsController", autospec=True
    ):
        return AppController(model, view, schedule_manager)


@pytest.mark.unit
def test_initialize_infra_success(controller: AppController) -> None:
    controller.startup_controller.initialize_app = MagicMock(spec=[])
    controller.initialize_infra()
    controller.startup_controller.initialize_app.assert_called_once_with()


@pytest.mark.unit
def test_initialize_infra_error_reraises(controller: AppController) -> None:
    controller.startup_controller.initialize_app = MagicMock(side_effect=RuntimeError("infra fail"))
    with patch.object(controller, "handle_error") as mock_handle:
        with pytest.raises(RuntimeError, match="infra fail"):
            controller.initialize_infra()
        mock_handle.assert_called_once_with(ANY, "Inicialización de Infraestructura")


@pytest.mark.unit
def test_connect_all_signals_success_and_error(controller: AppController) -> None:
    controller.ui_signals_controller.connect_all_signals = MagicMock(spec=[])
    controller.connect_all_signals()
    controller.ui_signals_controller.connect_all_signals.assert_called_once_with()

    controller.ui_signals_controller.connect_all_signals = MagicMock(side_effect=RuntimeError("sig fail"))
    with patch.object(controller, "handle_error") as mock_handle:
        controller.connect_all_signals()
        mock_handle.assert_called_once_with(ANY, "Conexión de Señales")


@pytest.mark.unit
def test_initialize_calls_infra_then_signals(controller: AppController) -> None:
    with patch.object(controller, "initialize_infra") as mock_infra, patch.object(
        controller, "connect_all_signals"
    ) as mock_connect:
        controller.initialize()
        mock_infra.assert_called_once_with()
        mock_connect.assert_called_once_with()


@pytest.mark.unit
def test_cleanup_calls_subcontroller_cleanup(controller: AppController) -> None:
    controller.navigation_controller = MagicMock(spec=["cleanup"])
    controller.report_controller = MagicMock(spec=["cleanup"])
    controller.cleanup()
    controller.navigation_controller.cleanup.assert_called_once_with()
    controller.report_controller.cleanup.assert_called_once_with()


@pytest.mark.unit
def test_current_user_property_getter_setter(controller: AppController) -> None:
    controller.session_controller = MagicMock(spec=["current_user"])
    controller.session_controller.current_user = "userA"
    assert controller.current_user == "userA"
    controller.current_user = "userB"
    assert controller.session_controller.current_user == "userB"

    controller.session_controller = None
    assert controller.current_user is None
    controller.current_user = "ignored"


@pytest.mark.unit
def test_handle_save_flow_only_branches(controller: AppController) -> None:
    task_dto = FlowTaskDataDTO(id="T", name="T", duration=1.0, duration_per_unit=1.0, department="General")
    config_dto = FlowTaskConfigDTO(workers=[], machine_id=None, start_condition_type="date")
    step = ProductionFlowStepDTO(task=task_dto, config=config_dto)
    flow = [step]
    
    controller.simulation_controller = None
    with pytest.raises(RuntimeError, match="simulation_controller no inicializado"):
        controller.handle_save_flow_only("N", "D", flow)

    controller.simulation_controller = MagicMock(spec=["handle_save_flow_only"])
    controller.simulation_controller.handle_save_flow_only.return_value = 123
    
    res = controller.handle_save_flow_only("N", "D", flow)
    assert res == 123
    
    # Bonus calidad: DTO validation
    assert isinstance(flow[0], ProductionFlowStepDTO)
    controller.simulation_controller.handle_save_flow_only.assert_called_once_with("N", "D", flow)


@pytest.mark.unit
def test_search_fabricaciones_branches(controller: AppController) -> None:
    controller.fabricacion_controller = MagicMock(spec=["search_fabricaciones"])
    controller.fabricacion_controller.search_fabricaciones.return_value = ["F1"]
    assert controller.search_fabricaciones("q") == ["F1"]

    controller.fabricacion_controller = None
    controller.product_controller = MagicMock(spec=["search_fabricaciones"])
    controller.product_controller.search_fabricaciones.return_value = ["F2"]
    assert controller.search_fabricaciones("q") == ["F2"]

    controller.product_controller = None
    assert controller.search_fabricaciones("q") == []


@pytest.mark.unit
def test_show_fabricacion_preprocesos_branches(controller: AppController) -> None:
    controller.fabricacion_controller = MagicMock(spec=["show_fabricacion_preprocesos"])
    controller.show_fabricacion_preprocesos(1)
    controller.fabricacion_controller.show_fabricacion_preprocesos.assert_called_once_with(1)

    controller.fabricacion_controller = None
    controller.product_controller = MagicMock(spec=["show_fabricacion_preprocesos"])
    controller.show_fabricacion_preprocesos(2)
    controller.product_controller.show_fabricacion_preprocesos.assert_called_once_with(2)

    controller.product_controller = None
    with pytest.raises(RuntimeError, match="No hay controlador de fabricación inicializado"):
        controller.show_fabricacion_preprocesos(3)


@pytest.mark.unit
def test_misc_delegations(controller: AppController) -> None:
    controller.session_controller = MagicMock(spec=["logout", "handle_login"])
    controller.session_controller.handle_login.return_value = True
    assert controller.handle_login() is True
    controller.logout_user()
    controller.session_controller.logout.assert_called_once_with()

    controller.session_controller = None
    assert controller.handle_login() is False
    controller.logout_user()

    controller.report_controller = MagicMock(spec=["on_export_gantt_to_pdf_clicked"])
    calc_page = MagicMock(spec=[])
    cast(Any, controller.view).pages = {"calculate": calc_page}
    controller._on_export_gantt_to_pdf_clicked()
    controller.report_controller.on_export_gantt_to_pdf_clicked.assert_called_once_with(calc_page)

    controller.schedule_controller = MagicMock(spec=["load_schedule_settings"])
    controller.load_schedule_settings()
    controller.schedule_controller.load_schedule_settings.assert_called_once_with()

    controller.navigation_controller = MagicMock(spec=["on_nav_button_clicked"])
    controller.on_nav_button_clicked("home")
    controller.navigation_controller.on_nav_button_clicked.assert_called_once_with("home")


@pytest.mark.unit
def test_on_data_changed_branches(controller: AppController) -> None:
    controller.ui_controller = MagicMock(spec=["on_data_changed"])

    prod_tab = MagicMock(spec=["clear_all", "update_search_results"])
    gestion = MagicMock(spec=["productos_tab"])
    gestion.productos_tab = prod_tab
    cast(Any, controller.view).get_page.return_value = gestion
    cast(Any, controller.model).product_service.search_products.return_value = ["P1", "P2"]

    controller.on_data_changed()
    controller.ui_controller.on_data_changed.assert_called_once_with()
    prod_tab.clear_all.assert_called_once_with()
    prod_tab.update_search_results.assert_called_once_with(["P1", "P2"])

    controller.ui_controller.on_data_changed.reset_mock()
    prod_tab.update_search_results.reset_mock()
    controller.product_controller = MagicMock(spec=["product_service"])
    cast(Any, controller.product_controller).product_service.search_products.return_value = ["via_pc"]
    controller.on_data_changed()
    controller.ui_controller.on_data_changed.assert_called_once_with()
    prod_tab.update_search_results.assert_called_once_with(["via_pc"])

    # Sin ui_controller ni gestión, no debe fallar
    controller.ui_controller = None
    cast(Any, controller.view).get_page.return_value = None
    controller.on_data_changed()

