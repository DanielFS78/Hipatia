# -*- coding: utf-8 -*-
"""Prioridad de resolución en `ui.dialogs.fabrication.dialog_dependencies`."""

from unittest.mock import MagicMock, create_autospec

import pytest

from core.services.fabricacion_service import FabricacionService
from core.services.pila_service import PilaService
from ui.dialogs.fabrication.dialog_dependencies import (
    resolve_fabricacion_service,
    resolve_pila_service,
)

pytestmark = pytest.mark.unit


def _container_registered(svc_type: type, instance: object) -> MagicMock:
    c = MagicMock(spec=["is_registered", "resolve"])
    c.is_registered.side_effect = lambda t: t is svc_type
    c.resolve.return_value = instance
    return c


def _container_not_registered() -> MagicMock:
    c = MagicMock(spec=["is_registered", "resolve"])
    c.is_registered.return_value = False
    return c


def _ctrl_minimal() -> MagicMock:
    return MagicMock(spec=["product_controller", "model"])


def test_resolve_fabricacion_prefers_di() -> None:
    svc = create_autospec(FabricacionService, instance=True)
    container = _container_registered(FabricacionService, svc)
    ctrl = _ctrl_minimal()
    ctrl.product_controller = None
    ctrl.model = None
    assert resolve_fabricacion_service(ctrl, container) is svc
    container.is_registered.assert_called()
    container.resolve.assert_called_once_with(FabricacionService)


def test_resolve_fabricacion_product_controller_before_model() -> None:
    container = _container_not_registered()
    pc_fs = create_autospec(FabricacionService, instance=True)
    mod_fs = create_autospec(FabricacionService, instance=True)
    pc = MagicMock(spec=["fabricacion_service"])
    pc.fabricacion_service = pc_fs
    mod = MagicMock(spec=["fabricacion_service"])
    mod.fabricacion_service = mod_fs
    ctrl = MagicMock(spec=["product_controller", "model"])
    ctrl.product_controller = pc
    ctrl.model = mod
    assert resolve_fabricacion_service(ctrl, container) is pc_fs
    container.is_registered.assert_called_with(FabricacionService)


def test_resolve_fabricacion_model_when_no_pc() -> None:
    container = _container_not_registered()
    mod_fs = create_autospec(FabricacionService, instance=True)
    mod = MagicMock(spec=["fabricacion_service"])
    mod.fabricacion_service = mod_fs
    ctrl = MagicMock(spec=["product_controller", "model"])
    ctrl.product_controller = None
    ctrl.model = mod
    assert resolve_fabricacion_service(ctrl, container) is mod_fs


def test_resolve_fabricacion_returns_none_when_missing() -> None:
    container = _container_not_registered()
    ctrl = MagicMock(spec=["product_controller", "model"])
    ctrl.product_controller = MagicMock(spec=["fabricacion_service"])
    ctrl.product_controller.fabricacion_service = None
    ctrl.model = MagicMock(spec=["fabricacion_service"])
    ctrl.model.fabricacion_service = None
    assert resolve_fabricacion_service(ctrl, container) is None


def test_resolve_pila_prefers_di() -> None:
    svc = create_autospec(PilaService, instance=True)
    container = _container_registered(PilaService, svc)
    ctrl = MagicMock(spec=["model"])
    ctrl.model = None
    assert resolve_pila_service(ctrl, container) is svc
    container.resolve.assert_called_once_with(PilaService)


def test_resolve_pila_model_fallback() -> None:
    container = _container_not_registered()
    ps = create_autospec(PilaService, instance=True)
    mod = MagicMock(spec=["pila_service"])
    mod.pila_service = ps
    ctrl = MagicMock(spec=["model"])
    ctrl.model = mod
    assert resolve_pila_service(ctrl, container) is ps


def test_resolve_pila_returns_none_when_missing() -> None:
    container = _container_not_registered()
    ctrl = MagicMock(spec=["model"])
    ctrl.model = MagicMock(spec=["pila_service"])
    ctrl.model.pila_service = None
    assert resolve_pila_service(ctrl, container) is None
