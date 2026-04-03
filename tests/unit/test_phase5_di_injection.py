# -*- coding: utf-8 -*-
"""Tests unitarios Fase 5: wiring de servicios vía AppModel (fuente única para los controladores)."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import patch

import pytest

from controllers.calculation_controller import CalculationController


pytestmark = pytest.mark.unit


def _build_app_stub() -> Any:
    """Stub mínimo de AppController con modelo que expone servicios."""
    system_integration = SimpleNamespace(
        lote_repo=SimpleNamespace(),
        preproceso_repo=SimpleNamespace(),
    )
    ps = object()
    model = SimpleNamespace(
        worker_service=object(),
        machine_service=object(),
        pila_service=object(),
        product_service=ps,
        product_facade=SimpleNamespace(service=ps),
        planning_facade=SimpleNamespace(),
        fabricacion_service=object(),
        material_service=object(),
        system_integration=system_integration,
    )
    return SimpleNamespace(
        db=SimpleNamespace(lote_repo=SimpleNamespace()),
        view=SimpleNamespace(),
        schedule_manager=SimpleNamespace(),
        state=SimpleNamespace(),
        model=model,
        ui_controller=SimpleNamespace(),
    )


def test_calculation_controller_uses_model_pila_service() -> None:
    """CalculationController toma pila_service desde app.model."""
    app = _build_app_stub()
    injected = object()
    app.model.pila_service = injected

    ctrl = CalculationController(app)

    assert ctrl.pila_service is injected


@patch("controllers.simulation.controller.SimulationExecutionManager", autospec=True)
@patch("controllers.simulation.controller.SimulationEditorManager", autospec=True)
def test_simulation_controller_uses_model_services(mock_editor, mock_execution) -> None:
    """SimulationController enlaza worker/machine/pila desde app.model."""
    from controllers.simulation.controller import SimulationController

    app = _build_app_stub()
    w, m, p = object(), object(), object()
    app.model.worker_service = w
    app.model.machine_service = m
    app.model.pila_service = p

    with patch("core.di_container.DIContainer.get_instance", autospec=True) as get_instance:
        get_instance.return_value = SimpleNamespace(resolve=lambda _k: SimpleNamespace())

        ctrl = SimulationController(app)

    assert ctrl.worker_service is w
    assert ctrl.machine_service is m
    assert ctrl.pila_service is p
    assert mock_execution.call_count == 1
    assert mock_editor.call_count == 1


@patch("controllers.worker.controller.WorkerManagementManager", autospec=True)
@patch("controllers.worker.controller.WorkerAuthManager", autospec=True)
@patch("controllers.worker.controller.WorkerTaskManager", autospec=True)
def test_worker_controller_propagates_model_services(mock_task, mock_auth, mock_management) -> None:
    """WorkerController pasa model.worker_service (y fabricación) a los managers."""
    from controllers.worker.controller import WorkerController

    app = _build_app_stub()
    injected_worker = object()
    injected_fabricacion = object()
    app.model.worker_service = injected_worker
    app.model.fabricacion_service = injected_fabricacion

    ctrl = WorkerController(app)

    assert cast(Any, ctrl).model is app.model
    assert mock_management.call_args.kwargs["worker_service"] is injected_worker
    assert mock_management.call_args.kwargs["fabricacion_service"] is injected_fabricacion
    assert mock_auth.call_args.kwargs["worker_service"] is injected_worker
    assert mock_task.call_args.kwargs["worker_service"] is injected_worker


@patch("controllers.product_controller_v2.ProductManager", autospec=True)
@patch("controllers.product_controller_v2.FabricacionManager", autospec=True)
@patch("controllers.product_controller_v2.PreprocesoManager", autospec=True)
@patch("controllers.product_controller_v2.MaterialManager", autospec=True)
def test_product_controller_uses_model_services(_mm, _pm, _fm, _prm) -> None:
    """ProductController lee product/fabricacion/material desde app.model."""
    from controllers.product_controller_v2 import ProductController

    app = _build_app_stub()
    ps, fs, ms = object(), object(), object()
    app.model.product_service = ps
    app.model.product_facade = SimpleNamespace(service=ps)
    app.model.fabricacion_service = fs
    app.model.material_service = ms

    with patch("core.di_container.DIContainer.get_instance", autospec=True) as get_instance:
        get_instance.return_value = SimpleNamespace(resolve=lambda _k: SimpleNamespace())

        ctrl = ProductController(app)

    assert ctrl.model is app.model
    assert ctrl.product_facade.service is ps
    assert ctrl.product_service is ps
    assert ctrl.fabricacion_service is fs
    assert ctrl.material_service is ms


@patch("controllers.pila.controller.LoteManager", autospec=True)
@patch("controllers.pila.controller.PilaManager", autospec=True)
def test_pila_controller_propagates_model_services(mock_pila_manager, mock_lote_manager) -> None:
    """PilaController reenvía servicios del modelo a LoteManager y PilaManager."""
    from controllers.pila.controller import PilaController

    app = _build_app_stub()
    ps, fs, pilas = object(), object(), object()
    app.model.product_service = ps
    app.model.fabricacion_service = fs
    app.model.pila_service = pilas

    ctrl = PilaController(app)

    assert ctrl.app is app
    assert mock_lote_manager.call_args.kwargs["product_service"] is ps
    assert mock_lote_manager.call_args.kwargs["fab_service"] is fs
    assert mock_lote_manager.call_args.kwargs["db"] is app.model.system_integration
    assert mock_pila_manager.call_args.kwargs["pila_service"] is pilas
