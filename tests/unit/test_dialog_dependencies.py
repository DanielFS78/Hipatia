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


def _container_di_registered(svc_type, instance):
    c = MagicMock()
    c.is_registered.side_effect = lambda t: t is svc_type
    c.resolve.return_value = instance
    return c


def test_resolve_fabricacion_prefers_di() -> None:
    svc = create_autospec(FabricacionService, instance=True)
    container = _container_di_registered(FabricacionService, svc)
    ctrl = MagicMock()
    assert resolve_fabricacion_service(ctrl, container) is svc
    container.resolve.assert_called_once_with(FabricacionService)


def test_resolve_fabricacion_product_controller_before_model() -> None:
    container = MagicMock()
    container.is_registered.return_value = False
    pc_fs = MagicMock()
    mod_fs = MagicMock()
    pc = MagicMock(spec=["fabricacion_service"])
    pc.fabricacion_service = pc_fs
    mod = MagicMock(spec=["fabricacion_service"])
    mod.fabricacion_service = mod_fs
    ctrl = MagicMock(spec=["product_controller", "model"])
    ctrl.product_controller = pc
    ctrl.model = mod
    assert resolve_fabricacion_service(ctrl, container) is pc_fs


def test_resolve_fabricacion_model_when_no_pc() -> None:
    container = MagicMock()
    container.is_registered.return_value = False
    mod_fs = MagicMock()
    mod = MagicMock(spec=["fabricacion_service"])
    mod.fabricacion_service = mod_fs
    ctrl = MagicMock(spec=["product_controller", "model"])
    ctrl.product_controller = None
    ctrl.model = mod
    assert resolve_fabricacion_service(ctrl, container) is mod_fs


def test_resolve_fabricacion_returns_none_when_missing() -> None:
    container = MagicMock()
    container.is_registered.return_value = False
    ctrl = MagicMock(spec=["product_controller", "model"])
    ctrl.product_controller = MagicMock(spec=["fabricacion_service"])
    ctrl.product_controller.fabricacion_service = None
    ctrl.model = MagicMock(spec=["fabricacion_service"])
    ctrl.model.fabricacion_service = None
    assert resolve_fabricacion_service(ctrl, container) is None


def test_resolve_pila_prefers_di() -> None:
    svc = create_autospec(PilaService, instance=True)
    container = _container_di_registered(PilaService, svc)
    ctrl = MagicMock()
    assert resolve_pila_service(ctrl, container) is svc
    container.resolve.assert_called_once_with(PilaService)


def test_resolve_pila_model_fallback() -> None:
    container = MagicMock()
    container.is_registered.return_value = False
    ps = MagicMock()
    mod = MagicMock(spec=["pila_service"])
    mod.pila_service = ps
    ctrl = MagicMock(spec=["model"])
    ctrl.model = mod
    assert resolve_pila_service(ctrl, container) is ps


def test_resolve_pila_returns_none_when_missing() -> None:
    container = MagicMock()
    container.is_registered.return_value = False
    ctrl = MagicMock(spec=["model"])
    ctrl.model = MagicMock(spec=["pila_service"])
    ctrl.model.pila_service = None
    assert resolve_pila_service(ctrl, container) is None
