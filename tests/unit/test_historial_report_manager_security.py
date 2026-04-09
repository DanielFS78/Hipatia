# -*- coding: utf-8 -*-
"""RBAC: HistorialReportManager exige GENERATE_REPORTS para exportar PDF."""
from unittest.mock import MagicMock

import pytest

from controllers.historial.report_manager import HistorialReportManager
from core.security.access_control import set_security_service
from core.security.security_service import SecurityService

pytestmark = pytest.mark.unit


def test_on_print_report_clicked_permission_denied() -> None:
    mock_ss = MagicMock(spec=SecurityService)
    mock_ss.has_permission.return_value = False
    set_security_service(mock_ss)
    try:
        view = MagicMock(spec=["pages", "show_message"])
        view.pages = {}
        mgr = HistorialReportManager(
            db=MagicMock(spec=["iteration_repo"]),
            pila_service=MagicMock(spec=["load_pila", "get_diario_bitacora"]),
            worker_service=MagicMock(spec=[]),
            view=view,
        )
        mgr.on_print_report_clicked()
        view.show_message.assert_called_once_with(
            "Acceso Denegado",
            "No tienes permisos para realizar esta acción.",
            "warning",
        )
    finally:
        set_security_service(None)
