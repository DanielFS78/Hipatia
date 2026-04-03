# -*- coding: utf-8 -*-
"""Tests unitarios Fase 5: wiring de servicios inyectados en controladores (sin pasar por AppModel donde aplica)."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import patch

import pytest

from controllers.calculation_controller import CalculationController
from controllers.worker.protocols import IWorkerService
from core.application_state import ApplicationState
from core.protocols import IFabricacionService, IMaterialService, IProductService


pytestmark = pytest.mark.unit


def _build_app_stub() -> Any:
    """Stub mínimo de AppController."""
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


def test_calculation_controller_uses_injected_pila_service() -> None:
    """CalculationController recibe pila_service por constructor."""
    app = _build_app_stub()
    injected = object()

    ctrl = CalculationController(app, injected)

    assert ctrl.pila_service is injected


@patch("controllers.simulation.controller.SimulationExecutionManager", autospec=True)
@patch("controllers.simulation.controller.SimulationEditorManager", autospec=True)
def test_simulation_controller_uses_injected_services(mock_editor, mock_execution) -> None:
    """SimulationController enlaza worker/machine/pila inyectados."""
    from controllers.simulation.controller import SimulationController

    app = _build_app_stub()
    w, m, p = object(), object(), object()

    with patch("core.di_container.DIContainer.get_instance", autospec=True) as get_instance:
        get_instance.return_value = SimpleNamespace(resolve=lambda _k: SimpleNamespace())

        ctrl = SimulationController(app, w, m, p)

    assert ctrl.worker_service is w
    assert ctrl.machine_service is m
    assert ctrl.pila_service is p
    assert mock_execution.call_count == 1
    assert mock_editor.call_count == 1


@patch("controllers.worker.controller.WorkerManagementManager", autospec=True)
@patch("controllers.worker.controller.WorkerAuthManager", autospec=True)
@patch("controllers.worker.controller.WorkerTaskManager", autospec=True)
def test_worker_controller_propagates_injected_services(mock_task, mock_auth, mock_management) -> None:
    """WorkerController pasa servicios explícitos a los managers."""
    from controllers.worker.controller import WorkerController

    app = _build_app_stub()
    injected_worker = object()
    injected_fabricacion = object()
    injected_product = object()
    sig = SimpleNamespace(connect=lambda *_a, **_k: None)

    ctrl = WorkerController(
        app_controller=app,
        view=app.view,
        worker_service=cast(IWorkerService, injected_worker),
        product_service=cast(IProductService, injected_product),
        fabricacion_service=cast(IFabricacionService | None, injected_fabricacion),
        workers_changed_signal=sig,
    )

    assert ctrl.worker_service is injected_worker
    assert mock_management.call_args.kwargs["worker_service"] is injected_worker
    assert mock_management.call_args.kwargs["fabricacion_service"] is injected_fabricacion
    assert mock_auth.call_args.kwargs["worker_service"] is injected_worker
    assert mock_task.call_args.kwargs["worker_service"] is injected_worker
    assert mock_task.call_args.kwargs["product_service"] is injected_product


@patch("controllers.product_controller_v2.ProductManager", autospec=True)
@patch("controllers.product_controller_v2.FabricacionManager", autospec=True)
@patch("controllers.product_controller_v2.PreprocesoManager", autospec=True)
@patch("controllers.product_controller_v2.MaterialManager", autospec=True)
def test_product_controller_uses_injected_services(_mm, _pm, _fm, _prm) -> None:
    """ProductController recibe facades y servicios por constructor."""
    from controllers.product_controller_v2 import ProductController

    app = _build_app_stub()
    ps, fs, ms, mac = object(), object(), object(), object()
    pf = SimpleNamespace(service=ps)
    plf = SimpleNamespace()
    st = SimpleNamespace()

    ctrl = ProductController(
        app_shell=app,
        db=app.db,
        product_model=app.model,
        view=app.view,
        product_facade=pf,
        fabricacion_service=cast(IFabricacionService, fs),
        planning_facade=plf,
        material_service=cast(IMaterialService, ms),
        machine_service=mac,
        state=cast(ApplicationState, st),
    )

    assert ctrl.model is app.model
    assert ctrl.product_facade.service is ps
    assert ctrl.product_service is ps
    assert ctrl.fabricacion_service is fs
    assert ctrl.material_service is ms


@patch("controllers.pila.controller.LoteManager", autospec=True)
@patch("controllers.pila.controller.PilaManager", autospec=True)
def test_pila_controller_propagates_injected_services(mock_pila_manager, mock_lote_manager) -> None:
    """PilaController reenvía servicios inyectados a LoteManager y PilaManager."""
    from controllers.pila.controller import PilaController

    app = _build_app_stub()
    ps, fs, pilas = object(), object(), object()
    si = app.model.system_integration

    ctrl = PilaController(
        app_controller=app,
        view=app.view,
        system_integration=si,
        product_service=ps,
        fabricacion_service=fs,
        pila_service=pilas,
        state=app.state,
        schedule_manager=app.schedule_manager,
    )

    assert ctrl.app is app
    assert mock_lote_manager.call_args.kwargs["product_service"] is ps
    assert mock_lote_manager.call_args.kwargs["fab_service"] is fs
    assert mock_lote_manager.call_args.kwargs["db"] is si
    assert mock_pila_manager.call_args.kwargs["pila_service"] is pilas
